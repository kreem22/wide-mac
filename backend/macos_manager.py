#!/usr/bin/env python3

"""
Native macOS Backend for Open Computer Use

Provides native macOS subprocess execution and filesystem operations.
Preserves all existing MCP contracts and API.
"""

import os
import sys
import subprocess
import json
from typing import Tuple, Dict, Any, Optional, List
from pathlib import Path
import time
import signal


class MacOSBackend:
    """
    Native macOS backend implementation for Open Computer Use.
    
    Preserves all MCP contracts and API:
    - BackendManager interface
    - MCP tool compatibility
    - Service endpoints
    - Resource management
    """
    
    # Default process name for macOS
    PROCESS_NAME = "zsh"
    DEFAULT_TIMEOUT = 120
    
    def __init__(self, backend_type: str = "macos", cwd: str = "/tmp/computer-use-data"):
        """
        Initialize macOS backend.
        
        Args:
            backend_type: "macos" (default)
            cwd: Working directory (used for worker processes)
        """
        self.backend_type = backend_type.lower()
        self.process = None
        self.worker_process = None
        self.cwd = cwd
        self._termination_requested = False
        self._signal_handled = False
    
    def get_workspace(self) -> str:
        """Get current workspace path"""
        return self.cwd
    
    def set_workspace(self, path: str) -> None:
        """Set workspace path and cwd"""
        self.cwd = path
        # Ensure directory exists
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    def get_current_workspace(self) -> str:
        """Get current workspace path"""
        return self.cwd
    
    def create_process(self, name: str = None) -> None:
        """Create a new macOS process for tool execution"""
        if name is None:
            name = self.PROCESS_NAME
        
        # Create new zsh process
        try:
            result = subprocess.Popen(
                ["zsh", "-i", "-c", f"set -euo pipefail; {name}"], 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd
            )
            self.process = result
            self.worker_process = result
            self.process_name = self.PROCESS_NAME
            self.process_id = self.process.pid
        except Exception as e:
            self.process = None
            self.process_id = None
            raise RuntimeError(f"Failed to create process {name}: {e}")
    
    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        """Execute command with input, return exit code, stdout, stderr"""
        if self.process is None:
            raise RuntimeError("No process to execute")
        
        # Prepare command
        cmd_full = [sys.executable, "script", "-q", "-c"]
        if input:
            cmd_full.append("-r")
            cmd_full.extend(["-", input])
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd_full,
                input=input.encode(),
                text=True,
                timeout=timeout,
                capture_output=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            return timeout, "", ""
        except Exception as e:
            os.killpg(self.process.pid, signal.SIGKILL)
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
            # Check if process is alive
            if not os.kill(self.process.pid, 0):
                return {
                    "process": self.PROCESS_NAME,
                    "state": "idle",
                    "cwd": self.cwd,
                    "working_directory": self.cwd
                }
            
            # Get process information
            output = subprocess.check_output(
                ["ps", "-p", str(self.process.pid), "-o", "pid,ppid,stat,cmd"],
                universal_newlines=True,
                timeout=2
            )
            # Extract current command
            cmd_line = output.strip()
            if cmd_line:
                # Simple parsing to extract working directory
                cmd_parts = cmd_line.split()
                if len(cmd_parts) >= 1:
                    cmd_parts[0] = "zsh"
                working_dir = cmd_parts[0]  # zsh directory is current cwd
                
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
        if name in os.environ:
            return os.environ[name]
        return ""
    
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
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get all environment variables"""
        return os.environ.copy()
    
    def get_environment_variable_names(self) -> List[str]:
        """Get all environment variable names"""
        return list(os.environ.keys())
    
    def get_env(self, name: str) -> str:
        """Get environment variable"""
        return self.get_environment(name)
    
    def shutdown(self) -> None:
        """Shutdown all processes"""
        if self.process:
            os.killpg(self.process.pid, 9)
        if self.worker_process:
            os.killpg(self.worker_process.pid, 9)
        self.process = None
        self.process_id = None
    
    def shutdown_all(self) -> None:
        """Shutdown all related processes"""
        self.shutdown()
        # Clean up worker process too
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
                os.killpg(self.process.pid, 0)
                return False  # Still running
            except:
                return True  # Terminated
        return True
    
    def cleanup(self) -> None:
        """Clean up and ensure no resources leaked"""
        self.shutdown()
        self._process = None
        self._worker_process = None
        self._termination_requested = False
    
    def get_process_id(self) -> int:
        """Get current process ID"""
        return self.process_id if self.process else 0
    
    def get_process_name(self) -> str:
        """Get current process name"""
        return self.process_name
    
    def get_cwd(self) -> str:
        """Get current working directory"""
        return self.cwd
    
    def set_cwd(self, path: str) -> None:
        """Set current working directory"""
        self.cwd = path
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    def list_dir(self, path: str = ".") -> List[str]:
        """List directory contents"""
        if os.path.exists(path):
            return os.listdir(path)
        return []
    
    def read_file(self, path: str) -> str:
        """Read file content"""
        path = str(Path(path).resolve())
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def write_file(self, path: str, content: str) -> bool:
        """Write file content"""
        path = str(Path(path).resolve())
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            return False
    
    def touch_file(self, path: str) -> bool:
        """Create empty file"""
        path = str(Path(path).resolve())
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write('\n')
            return True
        except Exception as e:
            return False

    def ls(self, path: str = ".") -> List[str]:
        """List directory contents"""
        return self.ls(path)

    def cat(self, path: str) -> str:
        """Display file content"""
        content = self.read_file(path)
        return content