#!/usr/bin/env python3

"""
UpdateStatus.py

Public interface:
    Receives new progress content through stdin and persists it.

The persistence mechanism is intentionally encapsulated here.
"""

from pathlib import Path
import os
import sys
import tempfile


PROPERTIES_FILE = Path(__file__).with_name("STATUS_BAR.properties")
STATUS_PROPERTY = "progressStatusFileLoc"

_MAX_CONTENT_LENGTH = 4000

_REQUIRED_MARKERS = (
    "# PROGRESS SUMMARY",
    "## Progress Bar",
    "### 🚦 Progress Bar (Current Status)",
    "Status:",
    "Next Target:",
    "### Completed Milestones:",
)


def _load_properties(path: Path) -> dict[str, str]:
    properties = {}

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()

    return properties


def _get_status_path() -> Path:
    properties = _load_properties(PROPERTIES_FILE)

    status_location = properties.get(STATUS_PROPERTY)

    if not status_location:
        raise ValueError(
            f"Missing required property: {STATUS_PROPERTY}"
        )

    path = Path(status_location).expanduser()

    if not path.is_absolute():
        path = PROPERTIES_FILE.parent / path

    return path


def _validate(content: str) -> None:
    if not content.strip():
        raise ValueError("Progress content cannot be empty.")

    if len(content) > _MAX_CONTENT_LENGTH:
        raise ValueError("Progress content exceeds the permitted boundary.")

    for marker in _REQUIRED_MARKERS:
        if marker not in content:
            raise ValueError(
                "Progress content does not conform to the required template."
            )


def _persist(content: str) -> None:
    state_file = _get_status_path()
    state_dir = state_file.parent

    state_dir.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{state_file.name}.",
        dir=state_dir,
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content.rstrip() + "\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_name, state_file)

    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass

        raise


def main() -> int:
    try:
        content = sys.stdin.read()

        _validate(content)
        _persist(content)

        sys.stdout.write("Progress updated successfully.\n")
        return 0

    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 3

    except Exception:
        sys.stderr.write("Unable to persist progress.\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())