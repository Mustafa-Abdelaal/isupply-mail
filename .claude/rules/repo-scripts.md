---
paths:
  - "scripts/**"
  - ".githooks/**"
  - "infra/**"
---

# Repo scripts, git hooks and dev infrastructure

- **Stable interface**: `scripts/{check,lint,test,fmt,dev,dev-mail,setup,doctor}` are the contract that
  CI, hooks, skills and humans call. Keep their flags backward compatible, and update `--help` text and
  `scripts/README.md` together.
- **Portability**: bash 3.2 (macOS) and Git Bash (Windows). No associative arrays, `mapfile`,
  `${var,,}`, GNU-only flags (`sed -i` without a suffix, `readlink -f`) or `timeout`. Source
  `scripts/lib/common.sh` for helpers.
- **Step functions** run inside `if`, where errexit is off. Collect status explicitly
  (`rc=0; cmd || rc=1; return "$rc"`).
- **Python tooling**: 3.9+ standard library only, deterministic output, and `--help` from the module
  docstring. Tests go in `scripts/tests/test_*.py` (unittest).
- **Safety**: dev tools refuse non-local mail hosts by default and take passwords from environment
  variables, never CLI arguments. Never add network calls to the default `scripts/check` path, except
  through the opt-in `--full` integration tier.
- `STACK:` comments mark placeholders that `/bootstrap-stack` replaces. Don't remove them without wiring
  the real command.
- `shellcheck` must pass (CI runs it). Add a test for new behavior.
