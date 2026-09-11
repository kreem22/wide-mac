#!/usr/bin/env python3

"""
Native macOS Backend for Open Computer Use

Provides native macOS subprocess execution and filesystem operations.
Preserves all existing MCP contracts and API.
"""

import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

from filesystem import get_resource_path


class MacOSBackend:
    """
    Native macOS backend implementation for Open Computer Use.
    Preserves all existing MCP contracts and API.
    """

    PROCESS_NAME = "zsh"
    DEFAULT_TIMEOUT = 120

    def __init__(self, backend_type: str = "macos", cwd: str = "/tmp/computer-use-data"):
        """
        Initialize macOS backend.

        Args:
            backend_type: "macos" (default)
            cwd: Working directory for subprocess execution
        """
        self.backend_type = backend_type.lower()
        self.process = None
        self.worker_process = None
        self.process_name = None
        self.process_id = None
        self.cwd = cwd
        self._termination_requested = False
        self._signal_handled = False

    def get_workspace(self) -> str:
        """Get current workspace path"""
        return self.cwd

    def set_workspace(self, path: str) -> None:
        """Set workspace path and cwd"""
        self.cwd = path
        os.makedirs(path, exist_ok=True)

    def get_current_workspace(self) -> str:
        """Get current workspace path"""
        return self.cwd

    def create_process(self, name: str = None) -> None:
        """Create a new macOS process for tool execution"""
        if name is None:
            name = self.PROCESS_NAME

        try:
            self.process = subprocess.Popen(
                [name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd
            )
            self.worker_process = self.process
            self.process_name = name
            self.process_id = self.process.pid
        except Exception as e:
            self.process = None
            self.worker_process = None
            self.process_id = None
            raise RuntimeError(f"Failed to create process {name}: {e}")

    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        """Execute command with input, return exit code, stdout, stderr"""
        command_line = " ".join(shlex.quote(str(c)) for c in cmd)
        try:
            result = subprocess.run(
                [self.PROCESS_NAME, "-c", command_line],
                input=input if input else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.cwd
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def get_process_status(self) -> Dict[str, Any]:
        """Get status of current macOS process"""
        if self.process is None:
            return {
                "process": self.PROCESS_NAME,
                "state": "idle",
                "cwd": self.cwd,
                "working_directory": self.cwd
            }

        try:
            if not os.kill(self.process.pid, 0):
                return {
                    "process": self.PROCESS_NAME,
                    "state": "idle",
                    "cwd": self.cwd,
                    "working_directory": self.cwd
                }

            output = subprocess.check_output(
                ["ps", "-p", str(self.process.pid), "-o", "pid,ppid,stat,cmd"],
                universal_newlines=True,
                timeout=2
            )
            cmd_line = output.strip()
            working_dir = self.cwd
            if cmd_line:
                cmd_parts = cmd_line.split()
                if len(cmd_parts) > 1:
                    working_dir = cmd_parts[-1]

            return {
                "process": self.PROCESS_NAME,
                "state": "running",
                "cwd": self.cwd,
                "working_directory": working_dir,
                "pid": self.process_id
            }
        except Exception as e:
            return {
                "process": self.PROCESS_NAME,
                "state": "error",
                "cwd": self.cwd,
                "error": str(e)
            }

    def get_environment(self, name: str) -> str:
        """Get environment variable"""
        return os.environ.get(name, "")

    def get_env(self, name: str) -> str:
        """Get environment variable"""
        return self.get_environment(name)

    def get_env_names(self) -> List[str]:
        """Get all environment variable names"""
        return list(os.environ.keys())

    def get_environment_variable_names(self) -> List[str]:
        """Get all environment variable names"""
        return self.get_env_names()

    def get_environment_variables(self) -> Dict[str, str]:
        """Get all environment variables"""
        return os.environ.copy()

    def get_ports(self) -> List[int]:
        """Get service ports (currently macOS doesn't have Docker ports)"""
        return []

    def shutdown(self) -> None:
        """Shutdown all processes"""
        if self.process:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception:
                pass
        if self.worker_process and self.worker_process is not self.process:
            try:
                os.killpg(self.worker_process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception:
                pass
        self.process = None
        self.worker_process = None
        self.process_id = None

    def shutdown_all(self) -> None:
        """Shutdown all related processes"""
        self.shutdown()
        self._termination_requested = True

    def is_termination_requested(self) -> bool:
        """Check if termination has been requested"""
        return self._termination_requested

    def wait_for_termination(self, timeout: int = 120) -> bool:
        """Wait for processes to terminate"""
        if self._termination_requested:
            return True

        if self.process:
            try:
                os.kill(self.process.pid, 0)
                return False
            except ProcessLookupError:
                return True
            except Exception:
                return True
        return True

    def cleanup(self) -> None:
        """Clean up and ensure no resources leaked"""
        self.shutdown()
        self._termination_requested = False

    def get_process_id(self) -> int:
        """Get current process ID"""
        return self.process_id if self.process else 0

    def get_process_name(self) -> str:
        """Get current process name"""
        return self.process_name or self.PROCESS_NAME

    def get_cwd(self) -> str:
        """Get current working directory"""
        return self.cwd

    def set_cwd(self, path: str) -> None:
        """Set current working directory"""
        self.cwd = path
        os.makedirs(path, exist_ok=True)

    def list_dir(self, path: str = ".") -> List[str]:
        """List directory contents"""
        if os.path.exists(path):
            return os.listdir(path)
        return []

    def read_file(self, path: str) -> str:
        """Read file content"""
        resolved = str(Path(path).resolve())
        if os.path.exists(resolved):
            with open(resolved, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def write_file(self, path: str, content: str) -> bool:
        """Write file content"""
        resolved = str(Path(path).resolve())
        try:
            with open(resolved, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def touch_file(self, path: str) -> bool:
        """Create empty file"""
        resolved = str(Path(path).resolve())
        try:
            with open(resolved, 'a', encoding='utf-8') as f:
                pass
            return True
        except Exception:
            return False

    def ls(self, path: str = ".") -> List[str]:
        """List directory contents"""
        return self.list_dir(path)

    def cat(self, path: str) -> str:
        """Display file content"""
        return self.read_file(path)

    def get_resource_path(self, path: str) -> str:
        """Get resource path for a given path within workspace."""
        return get_resource_path(path)
