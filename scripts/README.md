# scripts/: the stable command interface

Agents, git hooks, Claude Code hooks, skills, CI and humans all call these scripts and nothing else.
That keeps behavior identical everywhere, and lets the technology stack be wired in later without
changing the workflow (`STACK:` comments mark the placeholders that `/bootstrap-stack` replaces).

| Script | Purpose | Flags |
|---|---|---|
| `check` | Quality gate: `fmt --check` + `lint` + `test` | `--fast`, `--changed`, `--full` (+ integration) |
| `lint` | Agent-config validator, shellcheck, Python syntax, actionlint, app linters | `--changed` |
| `test` | Repo tooling, hook and fixture tests; app tests | `-k PATTERN`, `--integration`, `--integration-only`, `--fast` |
| `fmt` | App formatters (fixtures are never formatted) | `--check`, `--changed`, `[files]` |
| `dev` | Run the app (`web`, `desktop`, `android`, `ios`, `server`) | |
| `dev-mail` | Local GreenMail server: `up`, `seed`, `reset`, `send`, `status`, `logs`, `down` | |
| `setup` | Idempotent setup: git hooks path, permissions, dependencies, doctor | `--quiet` |
| `doctor` | Toolchain check with install hints | `--quiet` |

Every script supports `--help`.

## Email tools (`scripts/email/`, Python stdlib)

| Tool | Use |
|---|---|
| `inspect_eml.py FILE [--json] [--body]` | Explain a message: headers, MIME tree, body choice, attachments, risky HTML |
| `anonymize_eml.py IN -o OUT [--redact-text]` | Make a real message safe to commit as a fixture |
| `discover.py DOMAIN [--json]` | Candidate IMAP/SMTP settings via autoconfig, ISPDB, SRV, MX |
| `probe_server.py --imap H:P --smtp H:P` | TLS, certificate, capabilities, auth mechanisms, folders |
| `seed_mailbox.py seed\|send\|status` | Dev-server data (used by `dev-mail`; refuses non-local hosts) |
| `emaillib.py` | Reference parser: the conformance oracle |

## Other

- `agent/validate_config.py` validates skills, agents, rules, settings, memory imports, doc links,
  ADRs and fixture hygiene.
- `github/sync-labels.sh` creates or updates the repository labels from `.github/labels.yml`.
- `tests/` holds the unittest suites for everything above (`scripts/test`).
- `lib/common.sh` holds shared bash helpers (bash 3.2 compatible).
