import os
import subprocess
from pathlib import Path

USER_DATA_BASE_PATH = os.getenv("USER_DATA_BASE_PATH", Path.home() / "Workspace" / "wide-mac" / "open-computer-use-macos")

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

def cmd_pwd():
    stdout, _, _ = _exec("pwd")
    return stdout.strip()

def cmd_echo(text):
    stdout, _, _ = _exec(f"echo '{text}'")
    return stdout.strip()

def run_cmd(cmd):
    stdout, stderr, rc = _exec(f"{cmd}")
    return stdout, stderr, rc