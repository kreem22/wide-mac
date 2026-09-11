# FULL_DIAG_OCU.md

## Purpose

Perform a **forensic, restartable diagnostic** of the Wide-Moat `open-computer-use-macos` port.

This is a diagnostic task, not an implementation task. Do not make speculative fixes. Every finding must be backed by exact repository evidence: file path, symbol/line where practical, command output, and test result.

Repository:
`/Users/creemac/Workspace/wide-mac/open-computer-use-macos`

Persistent checkpoint:
`/Users/creemac/Workspace/wide-mac/open-computer-use-macos/OCU.progress.md`

## 0. Restart / Resume Protocol

At startup:

1. Read this file completely.
2. Read `OCU.progress.md` if it exists.
3. Inspect `git status`, `git log --oneline --decorate -10`, and the current repository root.
4. Resume from the first incomplete diagnostic section.
5. Do not repeat completed sections unless their recorded evidence is stale or contradictory.
6. Update `OCU.progress.md` after every completed section and whenever a new issue is found.
7. If context is flushed, `OCU.progress.md` is the source of truth for the diagnostic checkpoint.
8. Never claim a section is complete without recording concrete evidence.

If `OCU.progress.md` does not exist, create it with the template in Section 1.

## 1. Progress File

Maintain:

`/Users/creemac/Workspace/wide-mac/open-computer-use-macos/OCU.progress.md`

Use this structure:

```md
# OCU Diagnostic Progress

Status: NOT STARTED

Current section:
Last completed section:
Last updated:

## Completed
- [ ] 0 Restart/bootstrap
- [ ] 1 Repository/Git integrity
- [ ] 2 Environment/prerequisites
- [ ] 3 Phase 1 backend boundary
- [ ] 4 Phase 2 native shell
- [ ] 5 Phase 3 filesystem
- [ ] 6 Filesystem security
- [ ] 7 Tool/MCP wiring
- [ ] 8 Docker preservation
- [ ] 9 Runtime/ports/processes
- [ ] 10 Tests/regression
- [ ] 11 Final diagnosis

## Issues
- 

## Evidence
- 

## Next action
-
```

Do not replace previous evidence. Append/update it carefully.

## 2. Prerequisites — CHECK FIRST

Before diagnosing implementation behavior, determine whether the required diagnostic software exists.

Check and record:

- macOS version
- architecture (`arm64` expected for this machine)
- Python version
- active Python executable
- `pip` availability
- `pytest` availability
- Git version
- Docker availability
- Docker Desktop/runtime status if safely observable
- any project dependency/requirements files
- any project-supported test command
- any virtual environment or package manager already provided by the repository

Use existing project tooling first.

### Important environment rule

Do **not** randomly install software.

Do not use `pip --user`, `pip --force`, or bypass externally-managed Python restrictions.

Do not modify the system Python.

If pytest is unavailable:

1. Inspect the repository for its intended environment/test setup.
2. Check whether a project virtual environment or documented dependency mechanism exists.
3. Record the exact failure.
4. If a dependency installation is genuinely required, STOP and report the prerequisite rather than improvising.

Do not confuse an unavailable test dependency with an implementation failure.

Do not modify, create, commit any files or start MCP or any server during diagnosis unless explicitly required to create `OCU.progress.md`.

## 3. Repository and Git Integrity

Inspect:

- repository root
- nested Git repositories
- `git status --short`
- `git log --oneline --decorate -10`
- `git diff --stat`
- `git diff --check`
- tracked/untracked files relevant to the port
- unexpected generated/test artifacts

Specifically investigate:

- `backend/filesystem.py`
- `backend/native_filesystem.py`
- `backend/tests/`
- `backend/manager.py`
- `backend/macos_manager.py`
- `backend/native_shell.py`
- `backend/test_backend.py`
- `test_native_shell.py`
- `nested/`
- `outside`
- `symlink.txt`
- `target.txt`
- `test.txt`
- `4B_PHASE_3_NATIVE_MACOS_FILESYSTEM.md`

Determine whether each is intentional, generated, test data, duplicated, or accidental.

Do not delete anything.

Record whether the working tree is clean and which changes belong to which phase.

## 4. Phase 1 — Backend Boundary

Verify the actual implementation against commit/history and current files.

Inspect:

- `backend/manager.py`
- `backend/macos_manager.py`
- `backend/test_backend.py`

Determine:

- Does `BackendManager` define a stable backend contract?
- Does `DockerBackend` preserve existing Docker behavior?
- Does `MacOSBackend` exist and actually implement the expected interface?
- Is backend selection/wiring correct?
- Were unrelated Docker behaviors changed?

Compare the current tree with the Phase 1 commit where useful.

Do not fix anything.

## 5. Phase 2 — Native Shell

Inspect:

- `backend/native_shell.py`
- `test_native_shell.py`
- any wiring that calls the native shell

Verify:

- native subprocess execution
- zsh/shell behavior
- configurable `USER_DATA_BASE_PATH`
- arbitrary working directories
- timeout/lifecycle behavior
- error handling
- tests actually test the implementation rather than merely printing
- Docker shell path remains intact

Check the Phase 2 commit:

`47c579f Implement native macOS shell backend`

Do not modify anything.

## 6. Phase 3 — Filesystem Implementation

Inspect these files first:

- `backend/filesystem.py`
- `backend/native_filesystem.py`
- `backend/tests/test_fs.py`
- any imports/callers/wiring for these modules

Determine exactly:

### A. Existing Docker implementation

- What does the original Docker filesystem path do?
- Is it still intact?
- Does native code accidentally replace or mutate Docker behavior?

### B. Native implementation

Verify actual code, not claims, for:

- `view`
- `create_file`
- `str_replace`
- current workspace/path behavior
- native local filesystem operations
- configurable `USER_DATA_BASE_PATH`
- arbitrary working directories
- nested relative paths
- missing-file behavior
- write/read/replace behavior
- return values/errors expected by callers

### C. Hard-coded paths

Search the repository for:

`/Users/creemac/Workspace`

and specifically determine whether any implementation logic incorrectly depends on the repository's absolute path.

Test/diagnose with at least two different workspace roots where feasible.

### D. Tool-contract compatibility

Trace each filesystem operation from its exposed tool/function entry point to the native implementation.

Do not accept "compatible" unless the call path proves it.

## 7. Filesystem Security

This section is diagnostic only.

Inspect the actual path-resolution implementation.

Check separately:

1. normal relative path
2. nested relative path
3. `../` traversal
4. repeated traversal such as `../../`
5. absolute path inside workspace
6. absolute path outside workspace
7. symlink pointing inside workspace
8. symlink pointing outside workspace
9. nonexistent target through a symlink
10. path normalization edge cases

Pay particular attention to:

`backend/filesystem.py`

and any `_is_inside` / path containment helper.

If code appears to return `True` unconditionally or otherwise defeats containment, record it as a critical finding.

Do not repair it during this diagnostic.

Important distinction:

- Phase 3B may provide basic filesystem behavior.
- Security hardening may be a later task.
- Do not mark security as complete merely because a helper exists.

## 8. MCP / Tool Wiring

Trace the real execution path.

Determine:

- Which module exposes `view`, `create_file`, `str_replace`
- Which backend is selected
- Whether native filesystem code is actually reachable
- Whether MCP still calls the Docker implementation
- Whether any imports are stale/broken
- Whether there are duplicate implementations with only one actually being used

Do not start MCP.

Use static code inspection and existing tests only unless a server is already running and observation is explicitly safe.

## 9. Docker Preservation

This is a hard requirement.

Verify that the following remain intact:

- Docker manager
- Docker filesystem behavior
- Dockerfile
- `docker-compose.yml`
- existing Docker MCP path
- existing Docker tool contracts

Do not accept claims such as "Docker is preserved" without inspecting diffs/current code.

Explicitly identify any Docker file changed by Phase 3.

## 10. Runtime / Ports / Processes

Do not start or restart anything.

Inspect only what can be safely observed.

Confirm that diagnostic work has not changed:

- `8081`
- `8082`
- `9000`

Do not kill processes.

Do not restart NemoClaw/OpenShell/OpenClaw/llama.cpp.

Record any existing process/service evidence only if it can be obtained safely.

## 11. Tests and Regression

First identify the repository's intended test runner.

Then determine whether tests are:

- executable
- real assertions
- correctly discovered
- testing the actual implementation
- dependent on unavailable software
- using hard-coded paths
- leaving generated artifacts

Relevant tests include:

- backend boundary tests
- native shell tests
- filesystem tests
- any existing project tests affected by backend changes

Do not fabricate passing results.

If a test cannot run, record:

- exact command
- exact error
- why it failed
- whether failure is environmental or implementation-related

Do not install dependencies unless the repository explicitly documents how to do so; otherwise stop and report the prerequisite.

## 12. Phase 3 Git Commit Verification

Inspect:

`142e889 Implement native macOS filesystem backend`

Determine:

- exact files changed by the commit
- whether those files actually implement Phase 3
- whether unrelated files were included
- whether the commit matches the current working tree
- whether later uncommitted changes alter the conclusion

Do not create a new commit.

## 13. Final Diagnosis

Produce a concise but complete report with:

### Verdict

One of:

- `PHASE 3 VERIFIED`
- `PHASE 3 INCOMPLETE`
- `PHASE 3 BLOCKED BY ENVIRONMENT`
- `PHASE 3 HAS CRITICAL DEFECTS`

### Findings

For every issue:

- severity: CRITICAL / HIGH / MEDIUM / LOW
- exact file
- exact symbol/function/class where possible
- what is wrong
- evidence
- affected requirement
- recommended next action

### Verified items

List requirements that are actually proven.

### Unverified items

List anything that could not be tested or traced.

### Environment blockers

Separate missing software/test dependencies from code defects.

### Recommended next task

Give ONE small next implementation task only. Do not write an implementation plan for all remaining phases.

## 14. Final Stop Rule

After completing the diagnostic:

1. Update `OCU.progress.md`.
2. Do not modify implementation code.
3. Do not commit.
4. Do not start MCP or any server.
5. Do not proceed to Phase 4.
6. Report the final diagnosis and stop.

The objective is **truthful diagnosis from repository evidence**, not confirmation of previous reports.
