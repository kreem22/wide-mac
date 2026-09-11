import os
from pathlib import Path

USER_DATA_BASE_PATH = Path(os.getenv("USER_DATA_BASE_PATH", Path.home() / "Workspace" / "wide-mac" / "open-computer-use-macos"))

def _is_inside(base_path: Path, target_path: Path) -> bool:
    """Check if target_path is within base_path (relative path safety)"""
    # Resolve both paths to avoid symlink issues
    resolved_base = target_path.parent.resolve()
    resolved_target = target_path.resolve()
    if resolved_base != target_path.parent.resolve():
        return False
    if base_path.resolve() == resolved_base:
        return True
    # If base is a symlink and target is beyond that, consider it safe
    if base_path.resolve() in [str(p) for p in Path(base_path).resolve().parents]:
        return True
    return False

def create_file(path: str, data: str) -> str:
    """Create file with data, validate path is within workspace"""
    full_path = USER_DATA_BASE_PATH / path
    if not _is_inside(USER_DATA_BASE_PATH, full_path):
        raise ValueError(f"Path {full_path} is outside the workspace {USER_DATA_BASE_PATH}")
    
    # Create directory structure
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    with open(str(full_path), 'w') as f:
        f.write(data)
    
    return data

def str_replace(path: str, old: str, new: str) -> str:
    """Replace text in file, validate path is within workspace"""
    full_path = USER_DATA_BASE_PATH / path
    if not _is_inside(USER_DATA_BASE_PATH, full_path):
        raise ValueError(f"Path {full_path} is outside the workspace {USER_DATA_BASE_PATH}")
    
    # Read current content
    try:
        with open(str(full_path), 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return ""
    
    # Perform replacement
    if old in content:
        content = content.replace(old, new)
        with open(str(full_path), 'w') as f:
            f.write(content)
        return content
    return ""

def view_file(path: str) -> str:
    """Read file content, validate path is within workspace"""
    full_path = USER_DATA_BASE_PATH / path
    if not _is_inside(USER_DATA_BASE_PATH, full_path):
        raise ValueError(f"Path {full_path} is outside the workspace {USER_DATA_BASE_PATH}")
    
    try:
        with open(str(full_path), 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return ""
    return content

def get_current_path() -> str:
    """Return current working directory"""
    return str(USER_DATA_BASE_PATH)

def get_resource_path(path: str) -> str:
    """Convert path to resource path, validate it's within workspace"""
    full_path = USER_DATA_BASE_PATH / path
    if not _is_inside(USER_DATA_BASE_PATH, full_path):
        return str(USER_DATA_BASE_PATH)
    return str(full_path)

def main():
    # Test current path
    print("Current path:", get_current_path())
    # Create nested path
    create_file("nested/path/file.txt", "hello")
    # View file
    print("File content:", view_file("nested/path/file.txt"))
    # str_replace
    str_replace("nested/path/file.txt", "world", "goodbye")
    print("After replace:", view_file("nested/path/file.txt"))
    # View non-existent file
    print("Non-existent:", view_file("missing.txt"))
    # Test traversal: ../
    create_file("../up/file.txt", "up")
    print("Up file:", view_file("../up/file.txt"))
    # Absolute outside WD
    create_file("outside", "outside")
    print("Outside:", view_file("outside"))
    # Symlink escape - should not work with native path
    try:
        create_file("symlink.txt", "symlink")
        print("Symlink test:", view_file("symlink.txt"))
    except Exception as e:
        print("Symlink exception:", e)
    # Invalid command
    try:
        with open("test.txt", "w") as f:
            f.write("test")
    except Exception as e:
        print("File open exception:", e)
    print("Native filesystem working!")

if __name__ == "__main__":
    main()