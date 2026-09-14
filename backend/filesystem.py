import os
import configparser
from pathlib import Path

USER_DATA_BASE_PATH = Path(
    os.getenv(
        "USER_DATA_BASE_PATH",
        Path.cwd(),
    )
)

# Load security mode from config file or environment
def _load_security_mode() -> str:
    """
    Load filesystem security mode from:
    1. Environment variable FILESYSTEM_SECURITY_MODE
    2. Config file backend/filesystem_config.ini
    3. Default to 'strict'
    """
    # Check environment variable first (override)
    env_mode = os.getenv("FILESYSTEM_SECURITY_MODE")
    if env_mode:
        return env_mode
    
    # Check config file
    config_path = Path(__file__).parent / "filesystem_config.ini"
    if config_path.exists():
        config = configparser.ConfigParser()
        try:
            config.read(config_path)
            if "security" in config and "mode" in config["security"]:
                return config["security"]["mode"].strip()
        except Exception:
            pass
    
    # Default to strict
    return "strict"

# Security mode:
#   strict     -> paths must remain inside USER_DATA_BASE_PATH (raises error on escape)
#   unrestricted -> absolute paths outside the workspace are allowed
#   elevated    -> paths outside the workspace are allowed, but validated
#
FILESYSTEM_SECURITY_MODE = _load_security_mode()


def _is_inside(base_path: Path, target_path: Path) -> bool:
    """Check if target_path is within base_path."""
    try:
        resolved_base = base_path.resolve()
        resolved_target = target_path.resolve()

        if FILESYSTEM_SECURITY_MODE == "strict":
            # In strict mode, target must be relative or resolvable inside the base path.
            return resolved_target.is_relative_to(resolved_base)

        # For 'elevated' or 'unrestricted', we allow checks on absolute paths outside.
        return (
            resolved_target == resolved_base
            or resolved_target.is_relative_to(resolved_base)
        )
    except (OSError, RuntimeError):
        return False


def _validate_path(path: Path) -> None:
    """Validate path according to the active filesystem security mode.
    
    Raises:
        ValueError: If mode is strict and path is outside workspace
        ValueError: If mode is invalid/unknown (fail-safe to strict)
    """

    if FILESYSTEM_SECURITY_MODE == "unrestricted":
        return

    if FILESYSTEM_SECURITY_MODE == "strict":
        if not _is_inside(USER_DATA_BASE_PATH, path):
            raise ValueError(
                f"Path {path} is outside the workspace "
                f"{USER_DATA_BASE_PATH}"
            )
        return
    
    if FILESYSTEM_SECURITY_MODE == "elevated":
        # elevated mode: allow outside paths but with validation
        # (implementation can be added later)
        return
    
    # Invalid/unknown mode - fail safe to strict (deny external paths)
    raise ValueError(
        f"Invalid filesystem security mode: '{FILESYSTEM_SECURITY_MODE}'. "
        f"Valid modes: 'strict', 'unrestricted', 'elevated'. "
        f"Denying path access for safety: {path}"
    )


def create_file(path: str, data: str) -> str:
    """Create file with data."""
    full_path = USER_DATA_BASE_PATH / path

    _validate_path(full_path)

    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "w") as f:
        f.write(data)

    return data


def str_replace(path: str, old: str, new: str) -> str:
    """Replace text in file."""
    full_path = Path(get_resource_path(path))

    _validate_path(full_path)

    try:
        with open(full_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return ""

    if old in content:
        content = content.replace(old, new)

        with open(full_path, "w") as f:
            f.write(content)

        return content

    return ""


def view_file(path: str) -> str:
    """Read file content."""
    full_path = USER_DATA_BASE_PATH / path

    _validate_path(full_path)

    try:
        with open(full_path, "rt") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def get_current_path() -> str:
    """Return current workspace path."""
    return str(USER_DATA_BASE_PATH)


def get_resource_path(path: str) -> str:
    """Resolve a filesystem path according to the active security mode."""

    supplied_path = Path(path)

    if supplied_path.is_absolute():
        full_path = supplied_path
    else:
        full_path = USER_DATA_BASE_PATH / supplied_path

    _validate_path(full_path)

    return str(full_path)