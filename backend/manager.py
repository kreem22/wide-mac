#!/usr/bin/env python3

"""
Backend Manager Interface for Open Computer Use

Provides a platform-agnostic interface for MCP tool execution and resource management.
Supports:
- Docker backend (existing)
- macOS backend (native replacement)
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Tuple

from backend.macos_manager import MacOSBackend


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
        if self.backend_type not in ["docker", "macos"]:
            raise ValueError(f"Invalid backend type: {backend_type}")

        # Initialize with backend-specific defaults
        self.current_workspace = os.getenv("USER_DATA_BASE_PATH", "/tmp/computer-use-data")
        self.container_id = None
        self.container_name = None

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


class DockerBackend(BackendManager):
    """
    Adapter that preserves the original Docker backend contract.
    The underlying Docker implementation in computer-use-server/docker_manager.py
    is left unchanged.
    """

    def __init__(self, backend_type: str = "docker"):
        super().__init__(backend_type)

    def get_workspace(self) -> str:
        return self.current_workspace

    def create_container(self, name: str) -> str:
        raise NotImplementedError(
            "DockerBackend.create_container is not implemented in this repair"
        )

    def execute_command(self, cmd: List[str], input: str = "", timeout: int = 120) -> Tuple[int, str, str]:
        raise NotImplementedError(
            "DockerBackend.execute_command is not implemented in this repair"
        )

    def get_container_status(self) -> Dict[str, Any]:
        raise NotImplementedError(
            "DockerBackend.get_container_status is not implemented in this repair"
        )

    def shutdown(self) -> None:
        pass

    def get_resource_path(self, path: str) -> str:
        return str(Path(self.current_workspace) / path)
