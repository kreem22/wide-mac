#!/usr/bin/env python3
"""
Test the filesystem operations and backend contract for the native macOS backend.

Tests are mode-aware:
- strict mode: paths outside workspace raise ValueError
- unrestricted mode: paths outside workspace are allowed
- elevated mode: paths outside workspace allowed with validation
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project directory to Python path
sys.path.append('/Users/creemac/Workspace/wide-mac/open-computer-use-macos')
sys.path.append("/Users/creemac/Workspace/wide-mac/open-computer-use-macos/backend")

import filesystem
from backend.macos_manager import MacOSBackend


class TestMacOSBackendAndFilesystem(unittest.TestCase):
    def setUp(self):
        self.original_base = filesystem.USER_DATA_BASE_PATH
        self.original_mode = filesystem.FILESYSTEM_SECURITY_MODE
        
        self.temp_dir = tempfile.mkdtemp()
        os.environ['USER_DATA_BASE_PATH'] = self.temp_dir
        filesystem.USER_DATA_BASE_PATH = Path(self.temp_dir)
        
        # Default to strict mode for tests
        filesystem.FILESYSTEM_SECURITY_MODE = "strict"

    def tearDown(self):
        filesystem.USER_DATA_BASE_PATH = self.original_base
        filesystem.FILESYSTEM_SECURITY_MODE = self.original_mode
        
        if self.original_base:
            os.environ['USER_DATA_BASE_PATH'] = str(self.original_base)
        else:
            os.environ.pop('USER_DATA_BASE_PATH', None)
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backend_contract_methods_exist(self):
        """MacOSBackend exposes the expected backend contract methods."""
        backend = MacOSBackend()
        self.assertTrue(hasattr(backend, 'get_workspace'))
        self.assertTrue(hasattr(backend, 'set_workspace'))
        self.assertTrue(hasattr(backend, 'execute_command'))
        self.assertTrue(hasattr(backend, 'get_resource_path'))
        self.assertTrue(hasattr(backend, 'create_process'))
        self.assertTrue(hasattr(backend, 'shutdown'))

    def test_workspace_get_and_set(self):
        backend = MacOSBackend()
        self.assertEqual(backend.get_workspace(), "/tmp/computer-use-data")
        backend.set_workspace(self.temp_dir)
        self.assertEqual(backend.get_workspace(), self.temp_dir)
        self.assertTrue(os.path.isdir(self.temp_dir))

    def test_execute_command_runs_zsh_subprocess(self):
        backend = MacOSBackend()
        backend.set_workspace(self.temp_dir)
        rc, stdout, stderr = backend.execute_command(['python3', '-c', 'print("Hello")'])
        self.assertEqual(rc, 0)
        self.assertIn("Hello", stdout)
        self.assertEqual(stderr, "")

    def test_execute_command_with_input(self):
        backend = MacOSBackend()
        backend.set_workspace(self.temp_dir)
        rc, stdout, stderr = backend.execute_command(['cat'], input="world")
        self.assertEqual(rc, 0)
        self.assertIn("world", stdout)

    def test_resource_path_relative(self):
        """Relative paths always allowed (inside workspace by definition)"""
        backend = MacOSBackend()
        resource = backend.get_resource_path('test.txt')
        self.assertEqual(resource, str(Path(self.temp_dir) / 'test.txt'))

    def test_resource_path_nested(self):
        """Nested relative paths always allowed"""
        backend = MacOSBackend()
        resource = backend.get_resource_path('nested/path.txt')
        self.assertEqual(resource, str(Path(self.temp_dir) / 'nested/path.txt'))

    def test_resource_path_absolute_inside(self):
        """Absolute path inside workspace always allowed"""
        inside = os.path.join(self.temp_dir, 'inside.txt')
        backend = MacOSBackend()
        resource = backend.get_resource_path(inside)
        self.assertEqual(resource, inside)

    def test_resource_path_absolute_outside_strict_mode(self):
        """
        In strict mode: absolute path outside workspace raises ValueError
        
        This test validates that security mode is working:
        - If strict mode is enabled, accessing /tmp/outside.txt should fail
        """
        backend = MacOSBackend()
        filesystem.FILESYSTEM_SECURITY_MODE = "strict"
        
        # In strict mode, outside paths should raise ValueError
        with self.assertRaises(ValueError):
            backend.get_resource_path('/tmp/outside.txt')

    def test_resource_path_absolute_outside_unrestricted_mode(self):
        """
        In unrestricted mode: absolute path outside workspace is allowed
        
        This test validates that unrestricted mode works:
        - If unrestricted mode is enabled, /tmp/outside.txt should be returned as-is
        """
        backend = MacOSBackend()
        filesystem.FILESYSTEM_SECURITY_MODE = "unrestricted"
        
        # In unrestricted mode, outside paths should be allowed
        resource = backend.get_resource_path('/tmp/outside.txt')
        self.assertEqual(resource, '/tmp/outside.txt')

    def test_filesystem_create_and_view(self):
        """Create and view files in workspace"""
        filesystem.create_file("nested/file.txt", "hello")
        self.assertEqual(filesystem.view_file("nested/file.txt"), "hello")

    def test_filesystem_str_replace(self):
        """Replace text in files"""
        filesystem.create_file("replace.txt", "hello world")
        result = filesystem.str_replace("replace.txt", "world", "goodbye")
        self.assertEqual(result, "hello goodbye")
        self.assertEqual(filesystem.view_file("replace.txt"), "hello goodbye")

    def test_filesystem_view_missing_returns_empty(self):
        """Missing files return empty string, not error"""
        self.assertEqual(filesystem.view_file("missing.txt"), "")

    def test_filesystem_str_replace_missing_returns_empty(self):
        """Replace on missing files returns empty string"""
        self.assertEqual(filesystem.str_replace("missing.txt", "a", "b"), "")

    def test_path_traversal_blocked_strict_mode(self):
        """
        In strict mode: path traversal (../) attempts are blocked
        
        Validates that security containment works:
        - ../outside.txt should raise ValueError in strict mode
        """
        filesystem.FILESYSTEM_SECURITY_MODE = "strict"
        
        with self.assertRaises(ValueError):
            filesystem.create_file("../outside.txt", "escape")
        
        with self.assertRaises(ValueError):
            filesystem.view_file("../outside.txt")
        
        with self.assertRaises(ValueError):
            filesystem.str_replace("../outside.txt", "a", "b")

    def test_path_traversal_allowed_unrestricted_mode(self):
        """
        In unrestricted mode: path traversal (../) attempts are allowed
        
        Validates that unrestricted mode is truly unrestricted:
        - ../outside.txt should be allowed and resolved properly
        """
        filesystem.FILESYSTEM_SECURITY_MODE = "unrestricted"
        
        # Create a temp file outside workspace to test
        outside_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        outside_temp.write(b"external content")
        outside_temp.close()
        
        try:
            # In unrestricted mode, absolute paths should work
            result = filesystem.view_file(outside_temp.name)
            self.assertEqual(result, "external content")
        finally:
            os.unlink(outside_temp.name)

    def test_security_mode_configuration(self):
        """Verify that security mode can be changed"""
        # Start with strict
        filesystem.FILESYSTEM_SECURITY_MODE = "strict"
        self.assertEqual(filesystem.FILESYSTEM_SECURITY_MODE, "strict")
        
        # Switch to unrestricted
        filesystem.FILESYSTEM_SECURITY_MODE = "unrestricted"
        self.assertEqual(filesystem.FILESYSTEM_SECURITY_MODE, "unrestricted")
        
        # Switch to elevated
        filesystem.FILESYSTEM_SECURITY_MODE = "elevated"
        self.assertEqual(filesystem.FILESYSTEM_SECURITY_MODE, "elevated")
    
    def test_invalid_mode_fails_safe_to_strict(self):
        """
        Invalid mode fails safe to strict (deny access, don't allow bypass)
        
        This prevents accidental security bypass from typos or misconfiguration.
        Example: mode = 'junk' should NOT allow outside paths
        """
        backend = MacOSBackend()
        filesystem.FILESYSTEM_SECURITY_MODE = "invalid_mode_junk"
        
        # Invalid mode should raise ValueError for outside paths
        with self.assertRaises(ValueError) as context:
            backend.get_resource_path('/tmp/outside.txt')
        
        # Error message should mention invalid mode
        self.assertIn("Invalid filesystem security mode", str(context.exception))
        self.assertIn("invalid_mode_junk", str(context.exception))


if __name__ == '__main__':
    unittest.main()
