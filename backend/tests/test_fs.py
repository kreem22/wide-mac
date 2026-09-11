#!/usr/bin/env python3
"""
Test the filesystem operations and backend contract for the native macOS backend.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project directory to Python path
sys.path.append('/Users/creemac/Workspace/wide-mac/open-computer-use-macos')

# Add backend directory to path
sys.path.append("/Users/creemac/Workspace/wide-mac/open-computer-use-macos/backend")

import filesystem
from backend.macos_manager import MacOSBackend


class TestMacOSBackendAndFilesystem(unittest.TestCase):
    def setUp(self):
        self.original_base = filesystem.USER_DATA_BASE_PATH
        self.temp_dir = tempfile.mkdtemp()
        os.environ['USER_DATA_BASE_PATH'] = self.temp_dir
        filesystem.USER_DATA_BASE_PATH = Path(self.temp_dir)

    def tearDown(self):
        filesystem.USER_DATA_BASE_PATH = self.original_base
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
        backend = MacOSBackend()
        resource = backend.get_resource_path('test.txt')
        self.assertEqual(resource, str(Path(self.temp_dir) / 'test.txt'))

    def test_resource_path_nested(self):
        backend = MacOSBackend()
        resource = backend.get_resource_path('nested/path.txt')
        self.assertEqual(resource, str(Path(self.temp_dir) / 'nested/path.txt'))

    def test_resource_path_absolute_inside(self):
        inside = os.path.join(self.temp_dir, 'inside.txt')
        backend = MacOSBackend()
        resource = backend.get_resource_path(inside)
        self.assertEqual(resource, inside)

    def test_resource_path_absolute_outside_resolves_to_root(self):
        backend = MacOSBackend()
        resource = backend.get_resource_path('/tmp/outside.txt')
        self.assertEqual(resource, self.temp_dir)

    def test_filesystem_create_and_view(self):
        filesystem.create_file("nested/file.txt", "hello")
        self.assertEqual(filesystem.view_file("nested/file.txt"), "hello")

    def test_filesystem_str_replace(self):
        filesystem.create_file("replace.txt", "hello world")
        result = filesystem.str_replace("replace.txt", "world", "goodbye")
        self.assertEqual(result, "hello goodbye")
        self.assertEqual(filesystem.view_file("replace.txt"), "hello goodbye")

    def test_filesystem_view_missing_returns_empty(self):
        self.assertEqual(filesystem.view_file("missing.txt"), "")

    def test_filesystem_str_replace_missing_returns_empty(self):
        self.assertEqual(filesystem.str_replace("missing.txt", "a", "b"), "")

    def test_path_traversal_blocked(self):
        with self.assertRaises(ValueError):
            filesystem.create_file("../outside.txt", "escape")
        with self.assertRaises(ValueError):
            filesystem.view_file("../outside.txt")
        with self.assertRaises(ValueError):
            filesystem.str_replace("../outside.txt", "a", "b")


if __name__ == '__main__':
    unittest.main()
