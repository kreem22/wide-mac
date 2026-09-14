# Security Bug Fix: Invalid Mode Bypass

**Issue Found:** Mode `= junk` (or any invalid mode) allowed ALL paths - security bypass!

**Root Cause:** The `_validate_path()` function had no `else` clause for invalid modes:

```python
# BEFORE (VULNERABLE):
def _validate_path(path: Path) -> None:
    if FILESYSTEM_SECURITY_MODE == "unrestricted":
        return
    
    if FILESYSTEM_SECURITY_MODE == "strict":
        if not _is_inside(...):
            raise ValueError(...)
    
    # If mode is 'elevated' or anything else, we allow external paths.
    # ^^^ BUG: Invalid modes silently default to unrestricted!
```

**Fix:** Added explicit validation with fail-safe behavior:

```python
# AFTER (SECURE):
def _validate_path(path: Path) -> None:
    if FILESYSTEM_SECURITY_MODE == "unrestricted":
        return
    
    if FILESYSTEM_SECURITY_MODE == "strict":
        if not _is_inside(USER_DATA_BASE_PATH, path):
            raise ValueError(...)
        return
    
    if FILESYSTEM_SECURITY_MODE == "elevated":
        # Allow with validation
        return
    
    # INVALID MODE - FAIL SAFE TO STRICT
    raise ValueError(
        f"Invalid filesystem security mode: '{FILESYSTEM_SECURITY_MODE}'. "
        f"Valid modes: 'strict', 'unrestricted', 'elevated'. "
        f"Denying path access for safety: {path}"
    )
```

---

## What Changed

1. **`backend/filesystem.py`**
   - Fixed `_validate_path()` to reject invalid modes
   - Now raises `ValueError` for unknown modes instead of silently allowing them
   - Explicit `return` statements for valid modes

2. **`backend/tests/test_fs.py`**
   - Added test: `test_invalid_mode_fails_safe_to_strict`
   - Verifies that invalid modes raise `ValueError`
   - Confirms error message mentions the invalid mode

---

## Test Results

**Before Fix:**
```
Mode "junk" → Allowed access to /tmp/outside.txt ❌ SECURITY BUG
```

**After Fix:**
```
17 passed in 0.08s ✅
```

Including new test:
```python
def test_invalid_mode_fails_safe_to_strict(self):
    filesystem.FILESYSTEM_SECURITY_MODE = "invalid_mode_junk"
    with self.assertRaises(ValueError) as context:
        backend.get_resource_path('/tmp/outside.txt')
    self.assertIn("Invalid filesystem security mode", str(context.exception))
```

---

## Security Modes (Now Explicit)

| Mode | Outside Paths | Result |
|------|---------------|--------|
| `strict` | ❌ Blocked | `ValueError` |
| `unrestricted` | ✅ Allowed | Path returned |
| `elevated` | ✅ Allowed | Path returned |
| **Invalid (e.g., "junk")** | ❌ **Blocked** | **`ValueError` (FIXED)** |

---

## Lesson

**Never have a silent fallback for invalid configurations.** Always fail fast and loudly.

- ❌ Bad: Invalid mode → silently defaults to permissive
- ✅ Good: Invalid mode → explicitly raises error

This prevents typos or misconfiguration from becoming security holes.
