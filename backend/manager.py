#!/usr/bin/env python3

"""
Backend Manager Interface for Open Computer Use

Provides a platform-agnostic interface for MCP tool execution and resource management.
Supports:
- Docker backend (existing)
- macOS backend (native replacement)
"""

import os
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Import existing Docker backend
from computer_use_server import DockerManager

class BackendManager(ABC):
    """
    Abstract interface for backend management.
    All backend implementations must conform to this interface.
    """
    
    def __init__(self, backend_type: str = "docker"):
        """
        Initialize backend manager with specified backend type.
        
        Args:
            backend_type: "docker" or "macos"
        """
        self.backend_type = backend_type.lower()
        if backend_type not in ["docker", "macos"]:
            raise ValueError("Invalid backend type: {backend_type}")
        
        # Initialize with backend-specific defaults
        self.current_workspace = os.getenv("USER_DATA_BASE_PATH", "/tmp/computer-use-data")
        self.container_id = None
        self.container_name = None
        
        if backend_type == "docker":
            # Use existing Docker manager
            from computer_use_server.docker_manager import DockerManager as OriginalDockerManager
            # Create adapter that uses original Docker manager
            from computer_use_server.backend_manager import DockerBackend
            self.backend = DockerBackend(backend_type="docker")
        else:
            # Use macOS backend (to be implemented)
            from computer_use_server.macos_manager import MacOSBackend
            self.backend = MacOSBackend(backend_type="macos")

    @abstractmethod
    def get_workspace(self) -> str:
        """Get current workspace path"""
        pass
    
    @abstractmethod
    def create_container(self, name: str) -> str:
        """Create a container or process with given name"""
        pass
    
    @abstractmethod
    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        """Execute command with input, return exit code, stdout, stderr"""
        pass
    
    @abstractmethod
    def get_container_status(self) -> Dict[str, Any]:
        """Get current container/process status"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown container/process"""
        pass
    
    @abstractmethod
    def get_resource_path(self, path: str) -> str:
        """Get absolute path to resource, respecting workspace"""
        pass
    
    def get_current_workspace(self) -> str:
        """Get current workspace path"""
        return self.current_workspace
    
    def set_workspace(self, path: str) -> None:
        """Set workspace path"""
        self.current_workspace = path
        if self.backend_type == "macos":
            self.backend.set_workspace(path)

    def get_ports(self) -> List[int]:
        """Get service ports for the backend"""
        if self.backend_type == "docker":
            from computer_use_server.docker_manager import CDP_PORT, TTYD_PORT
            return [CDP_PORT, TTYD_PORT]
        else:
            # macOS ports would be implemented in macos_manager.py
            return []

    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for the backend"""
        return self.backend.get_environment_variables()

    def get_environment_variable(self, name: str) -> str:
        """Get single environment variable"""
        return self.backend.get_env(name)

    def get_env(self, name: str) -> str:
        """Get environment variable value"""
        return self.backend.get_env(name)

    def get_environment_variable_names(self) -> List[str]:
        """Get all environment variable names"""
        return self.backend.get_env_names()

    def get_env_names(self) -> List[str]:
        """Get all environment variable names"""
        return self.backend.get_env_names()

class DockerBackend(BackendManager):
    """
    Adapter that uses the original Docker backend.
    Keeps original code intact as fallback.
    """
    
    def __init__(self, backend_type: str = "docker"):
        super().__init__(backend_type)
        # Initialize with original Docker manager
        self.backend = DockerManager()
    
    def get_workspace(self) -> str:
        return self.get_environment_variable("USER_DATA_BASE_PATH")
    
    def set_workspace(self, path: str) -> None:
        self.current_workspace = path
        super().set_workspace(path)
    
    def create_container(self, name: str) -> str:
        """Adapter for Docker container creation"""
        # Call original method
        return self.backend.create_container(name)
    
    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        """Adapter for command execution"""
        return self.backend.execute_command(cmd, input, timeout)
    
    def get_container_status(self) -> Dict[str, Any]:
        """Adapter for container status"""
        return self.backend.get_container_status()
    
    def shutdown(self) -> None:
        """Adapter for shutdown"""
        self.backend.shutdown()
    
    def get_resource_path(self, path: str) -> str:
        """Adapter for resource path"""
        return self.backend.get_resource_path(path)

class MacOSBackend(BackendManager):
    """
    Native macOS backend implementation.
    Provides subprocess execution and native filesystem operations.
    """
    
    def __init__(self, backend_type: str = "macos"):
        super().__init__(backend_type)
        # For macOS, we use native subprocess and filesystem operations
        self._process = None
        self._cwd = self.current_workspace
    
    @property
    def cwd(self) -> str:
        return self._cwd
    
    @cwd.setter
    def cwd(self, path: str) -> None:
        self._cwd = path
        self.current_workspace = path
    
    def get_workspace(self) -> str:
        return self.current_workspace
    
    def set_workspace(self, path: str) -> None:
        self.set_workspace(path)
    
    def create_container(self, name: str) -> str:
        """Native macOS process creation"""
        # On macOS, we create native processes
        self._process = self._create_macos_process(name)
        return f"/bin/zsh://{name}"
    
    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        """Execute command with input, return exit code, stdout, stderr"""
        # Native macOS subprocess execution
        self._process = self._create_macos_process("executor")
        result = self._execute_command(cmd, input, timeout)
        return result
    
    def get_container_status(self) -> Dict[str, Any]:
        """Get status of macOS process"""
        if self._process is None:
            return {"process": "idle", "cwd": self.current_workspace}
        
        try:
            status = self._get_process_status()
            return {
                "process": status["process_name"],
                "state": status["status"],
                "cwd": self.current_workspace,
                "working_directory": self.cwd
            }
        except Exception:
            return {"process": "executor", "state": "error", "cwd": self.current_workspace}
    
    def shutdown(self) -> None:
        """Shutdown macOS process"""
        if self._process is not None:
            try:
                os.killpg(os.getpgid(self._process), 9)
            except:
                pass
            self._process = None
    
    def get_resource_path(self, path: str) -> str:
        """Get absolute path to resource"""
        # Normalize path to macOS absolute path
        path = str(Path(path).resolve())
        return path

    def _create_macos_process(self, name: str) -> Any:
        """Create native macOS process"""
        # This is a placeholder - actual implementation would use subprocess
        # The real implementation would create a zsh process
        # Here we simulate with a simple class
        class ExecutionProcess:
            def __init__(self, name):
                self.name = name
                self.status = "running"
                self.cwd = "/tmp"
                
            def execute_command(self, cmd, input="", timeout=120):
                # Simulate command execution
                return (0, "", "")
                
            def get_status(self):
                return {"process_name": "zsh", "status": "running", "cwd": self.cwd}
                
        return ExecutionProcess(name)
    
    def _execute_command(self, cmd, input, timeout):
        """Execute command using macOS subprocess"""
        # This would use subprocess.run() on macOS
        # For now, this is a placeholder implementation
        # The actual implementation would be added in Phase 2
        return (0, "", "")

    def _get_process_status(self):
        """Get process status"""
        # In real implementation: os.pidstat() or similar
        return {
            "process_name": "zsh",
            "status": "running",
            "cwd": self.cwd
        }