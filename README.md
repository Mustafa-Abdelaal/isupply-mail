# iSupply Mail

A zero-configuration email app for iSupply staff (`@isupply.com.eg`) on **Web, Windows, macOS, Linux,
Android and iOS**. Staff sign in with their work address and password, and everything else is set up
for them.

> **Status: foundation.** The repository is fully set up for agent-driven development (skills,
> subagents, guardrail hooks, an email conformance corpus, a local mail server, CI). The technology
> stack is the next decision, recorded in [ADR-0002](docs/decisions/0002-technology-stack.md).
> Application code starts after it's accepted.

## Quick start

```bash
git clone https://github.com/Mustafa-Abdelaal/isupply-mail.git && cd isupply-mail
scripts/setup          # git hooks + toolchain check (idempotent)
scripts/check          # the quality gate (CI runs the same thing)
scripts/dev-mail up && scripts/dev-mail seed   # local IMAP/SMTP server with test mail (needs Docker)
claude                 # start Claude Code; CLAUDE.md, skills and hooks load automatically
```

Then try `/spec "unified inbox for shared mailboxes"`, `/implement 12` or `/review-pr`. The full
workflow is in [docs/agentic/README.md](docs/agentic/README.md).

## What's here

| | |
|---|---|
| [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) | Rules and workflow for AI agents (and humans) |
| [docs/](docs/README.md) | Product, architecture, ADRs, email-protocol knowledge, threat model, testing |
| [fixtures/email/](fixtures/email/README.md) | Byte-exact test emails + the expected interpretation (conformance suite) |
| [scripts/](scripts/README.md) | Stable command interface (`check`, `test`, `lint`, `fmt`, `dev`, `dev-mail`, …) and email tools |
| [infra/dev-mail/](infra/dev-mail/README.md) | Local GreenMail server for development and integration tests |
| `.claude/` | 25 skills, 7 specialist subagents, path-scoped rules, guardrail hooks |
| `.github/` | CI, `@claude` workflows, issue/PR templates, labels |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: one issue per branch, Conventional Commits, PRs
into `main`, and `scripts/check` green before review.

Proprietary and internal to iSupply. Not for redistribution.
