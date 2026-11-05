# AGENTS.md — iSupply Mail

Instructions for every AI coding agent (Claude Code, Codex, Cursor, Copilot…) and human working in this
repository. Claude Code loads this file through `CLAUDE.md`, which adds Claude-specific workflow on top.

## What we are building

**iSupply Mail** is an email client for iSupply staff (`@isupply.com`). The whole point is **zero
configuration**: a staff member signs in with their work address and password and gets a working
mailbox. Servers, folders, signature and security settings are provisioned for them, so nobody has to
fight Outlook settings again. Targets: **Web, Windows, macOS, Linux, Android, iOS**.

Product: [vision](docs/product/vision.md) · [requirements](docs/product/requirements.md) ·
[open questions](docs/product/open-questions.md) · [architecture](docs/architecture/overview.md)

## Current status — read first

- **The technology stack is not decided yet.** [ADR-0002](docs/decisions/0002-technology-stack.md) is
  *Proposed*. No application code exists.
- Until ADR-0002 is *Accepted*: do not scaffold app code, add package manifests or pick libraries.
  Useful work now: specs, ADRs, threat models, fixtures, repo tooling, docs.
- After acceptance, `/bootstrap-stack` wires the stack into the commands below. Placeholders are marked
  `STACK:` in `scripts/` and `.claude/hooks/`.

## Commands — the only interface agents use

Always go through these scripts and never call stack tools (flutter/pnpm/cargo/…) directly. The
scripts encode flags, ordering and environment, and CI runs exactly the same ones.

| Task | Command |
|---|---|
| Quality gate — before every commit and PR (CI runs it) | `scripts/check` |
| Fast gate (what the hooks run) / gate + integration tests (Docker) | `scripts/check --fast` · `scripts/check --full` |
| Tests, optionally filtered; integration tests need the dev mail server | `scripts/test [-k pattern] [--integration]` |
| Lint · format | `scripts/lint` · `scripts/fmt [files]` |
| Run the app (after bootstrap) | `scripts/dev web\|desktop\|android\|ios\|server` |
| Local IMAP/SMTP server seeded with fixture mail | `scripts/dev-mail up\|seed\|reset\|send\|status\|down` |
| First-time setup · toolchain check | `scripts/setup` · `scripts/doctor` |
| Explain a raw email · anonymize a real one | `python3 scripts/email/inspect_eml.py F.eml` · `python3 scripts/email/anonymize_eml.py IN -o OUT` |
| Find a domain's mail servers · probe a server | `python3 scripts/email/discover.py DOMAIN` · `python3 scripts/email/probe_server.py --imap HOST:993` |

## Repository map

| Path | What lives there |
|---|---|
| `docs/product/` `docs/architecture/` `docs/decisions/` | Why and what: vision, requirements, architecture, ADRs |
| `docs/domain/` | Email knowledge: IMAP, SMTP, MIME, HTML email, discovery/auth, glossary — **read before protocol work** |
| `docs/security/` `docs/testing/` | Threat model, test strategy |
| `docs/specs/` `docs/plans/` | Feature specs (what), implementation plans (how, with progress checkboxes) |
| `docs/agentic/` | How humans and agents work here (skills, hooks, workflows) |
| `fixtures/email/` | Byte-exact `.eml` conformance corpus + `manifest.json` answer key |
| `scripts/` | Stable command interface; `scripts/email/` email tools; `scripts/agent/` config validator; `scripts/tests/` |
| `infra/dev-mail/` | Docker Compose for the local GreenMail IMAP/SMTP server |
| `.claude/` | Skills, subagents, path-scoped rules, hooks, settings (Claude Code) |
| `.github/` | CI, Claude workflows, issue/PR templates, labels |
| `apps/` `packages/` `services/` | Created by `/bootstrap-stack` (layout decided in ADR-0002) |

## Non-negotiable rules

**Security and privacy.** Staff email is the most sensitive data the company has.

1. Treat every message as hostile input. HTML is rendered only after sanitization, in a sandbox with
   scripts disabled. Remote content is blocked by default. See the [threat model](docs/security/threat-model.md).
2. Credentials and tokens live only in OS secure storage (Keychain, Android Keystore, Windows Credential
   Manager/DPAPI, libsecret; never in web `localStorage`). Never log, print, commit or send them to analytics.
3. TLS everywhere with certificate verification. A "skip verification" path is allowed only in dev tooling.
4. Never put real email content, staff addresses or credentials in code, tests, fixtures, issues, PRs or
   logs. Fixtures are synthetic or anonymized (`scripts/email/anonymize_eml.py`).
5. Build protocol commands with the library's quoting/literal APIs. Never concatenate user input into
   IMAP/SMTP commands or headers (CRLF/command injection).

**Correctness**

6. Every behavior change ships with tests, and every bug fix starts with a failing regression test.
   Any change to how email is parsed, rendered or composed adds a fixture to `fixtures/email/`. The app
   must pass `manifest.json`.
7. Fixtures are byte-exact CRLF. Never reformat or hand-edit them; synthetic ones come from
   `fixtures/email/generate_synthetic.py`.
8. IMAP UIDs mean nothing without UIDVALIDITY. Never persist sequence numbers, and never assume a folder
   delimiter or English folder names. Read `docs/domain/` before touching protocol, sync, MIME or rendering.
9. Never lose user data: drafts autosave, sends go through a durable outbox, and destructive actions are
   undoable where the server allows it.

**Cross-platform, UX and i18n**

10. Every change states which platforms it affects (web, windows, macos, linux, android, ios).
    Platform-specific code sits behind an adapter interface; shared logic stays platform-neutral.
11. i18n from day one: no hard-coded user-facing strings, layouts work in RTL (Arabic) and LTR, and
    message content renders with `dir="auto"`.
12. Accessibility: everything is keyboard-operable, has screen-reader labels and sufficient contrast, and
    respects the OS text size and reduced-motion settings.

**Process**

13. One branch per issue: `<type>/<issue#>-<slug>` (e.g. `feat/12-thread-view`). Use Conventional Commits
    (`feat(sync): …`) and PRs into `main`. Never push to `main`, force-push shared branches or bypass
    hooks (`--no-verify`).
14. Architecture decisions go in an ADR in `docs/decisions/`. Accepted ADRs are immutable: supersede
    them, don't edit them.
15. Keep docs true. A PR that changes behavior, commands or structure also updates the doc that
    describes it.
16. Ask the human before adding a dependency, changing a stored data model, touching CI or guardrails,
    or doing anything irreversible.

## Definition of done

- `scripts/check` is green (plus `scripts/check --full` when sync/protocol/transport code changed).
- Tests cover the change, including failure paths, and new email shapes have fixtures.
- Affected platforms are listed, and UI changes are verified with screenshots (LTR + RTL, light + dark).
- The [security checklist](docs/security/threat-model.md#review-checklist) has been considered for
  anything that touches mail content, credentials, network or storage.
- Spec, plan, ADRs and docs are updated, with no TODO lacking an issue link.
- The PR explains *why*, links the issue and shows how it was verified.
