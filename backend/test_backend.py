#!/usr/bin/env python3
"""
Test the backend manager interface
"""

import os
import sys

# Add backend directory to path
sys.path.append("/Users/creemac/Workspace/wide-mac/open-computer-use-macos/backend")

from backend.manager import BackendManager, MacOSBackend, DockerBackend

def test_backend_interface():
    print("Testing backend interface...")
    
    # Test MacOSBackend
    print("Creating MacOSBackend...")
    backend = MacOSBackend()
    print(f"  Workspace: {backend.get_workspace()}")
    
    # Test environment variables
    print(f"  Env vars: {backend.get_environment_variable_names()}")
    
    # Test workspace setting
    new_ws = "/Users/creemac/Workspace/project-test"
    backend.set_workspace(new_ws)
    print(f"  New workspace: {backend.get_workspace()}")
    
    # Test DockerBackend as fallback
    print("Creating DockerBackend...")
    docker_backend = DockerBackend()
    print(f"  Docker workspace: {docker_backend.get_workspace()}")
    
    print("Backend interface test passed!")

if __name__ == "__main__":
    test_backend_interface()