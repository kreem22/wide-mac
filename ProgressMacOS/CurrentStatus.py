#!/usr/bin/env python3

"""
CurrentStatus.py

Public interface:
    Prints the currently persisted progress state.

The persistence implementation is intentionally encapsulated here.
Callers should treat stdout as the authoritative current status.
"""

from pathlib import Path
import sys


PROPERTIES_FILE = Path(__file__).with_name("STATUS_BAR.properties")
STATUS_PROPERTY = "progressStatusFileLoc"


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


def _read_state() -> str:
    state_file = _get_status_path()

    if not state_file.exists():
        return ""

    return state_file.read_text(encoding="utf-8")


def main() -> int:
    try:
        state = _read_state()

        if state:
            sys.stdout.write(state.rstrip() + "\n")
        else:
            sys.stdout.write("No progress has been persisted yet.\n")

        return 0

    except Exception:
        sys.stderr.write("Unable to retrieve current progress.\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())