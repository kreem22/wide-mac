import os
import sys
from backend.native_shell import cmd_pwd, cmd_echo, run_cmd

def test_pwd():
    print("pwd:", cmd_pwd())

def test_echo():
    print("echo test:", cmd_echo("hello"))

def test_command_inside_wd():
    os.environ["USER_DATA_BASE_PATH"] = "/tmp/other"
    result = run_cmd("pwd")
    print("command inside other WD:", result)

def test_invalid_command():
    print("invalid command:", run_cmd("nonexistent"))

def test_timeout():
    print("timeout test:", run_cmd("sleep 10"))

if __name__ == "__main__":
    test_pwd()
    test_echo()
    test_command_inside_wd()
    test_invalid_command()
    test_timeout()