#!/usr/bin/env python3
"""
GetProgressTemplate.py

Public interface:
    Prints the progress template through stdout.

The template is intentionally defined here as an immutable interface
contract. The persisted progress state is handled separately.
"""

import sys


_PROGRESS_TEMPLATE = """# PROGRESS SUMMARY

---

## Progress Bar

This section tracks progress toward the main goal.

### 🚦 Progress Bar (Current Status)

Status: <Current plan pointer>

Next Target: <Next plan pointer>

### Completed Milestones:

✅ <Completed milestone>

---
"""


def main() -> int:
    try:
        sys.stdout.write(_PROGRESS_TEMPLATE)
        return 0
    except Exception:
        sys.stderr.write("Unable to retrieve the progress template.\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())