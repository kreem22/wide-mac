import os
import subprocess
from pathlib import Path

USER_DATA_BASE_PATH = Path(os.getenv("USER_DATA_BASE_PATH", Path.home() / "Workspace" / "wide-mac" / "open-computer-use-macos"))

def _exec(cmd, timeout=5):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=USER_DATA_BASE_PATH,
            timeout=timeout,
            check=True,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "command timed out", 120
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
    except Exception as e:
        return "", str(e), 1

def get_current_path():
    stdout, _, _ = _exec("pwd")
    return stdout.strip()

def create_file(path, data):
    full_path = USER_DATA_BASE_PATH / path
    stdout, _, _ = _exec(f"mkdir -p {full_path.parent}")
    stdout, _, _ = _exec(f"printf '{data}' > {full_path}")
    if stdout:
        return stdout
    return ""

def str_replace(path, old, new):
    full_path = USER_DATA_BASE_PATH / path
    stdout, _, _ = _exec(f"printf '{new}' > {full_path}")
    os.remove(full_path)
    return ""

def view_file(path):
    full_path = USER_DATA_BASE_PATH / path
    stdout, _, _ = _exec(f"cat {full_path}")
    return stdout.strip() if stdout else ""

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
    # Symlink escape (if possible)
    try:
        full_path = USER_DATA_BASE_PATH / "target.txt"
        full_path.write_text("target")
        symlink_path = USER_DATA_BASE_PATH / "symlink.txt"
        symlink_path.symlink_to(full_path)
        print("Symlink test:", view_file("symlink.txt"))
    except Exception as e:
        print("Symlink exception:", e)
    # Invalid command
    _exec("nonexistent")

if __name__ == "__main__":
    main()