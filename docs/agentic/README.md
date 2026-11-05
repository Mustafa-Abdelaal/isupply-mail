# Working with AI agents in this repository

This repo is set up so that Claude Code (and other agents through `AGENTS.md`) can carry features from
idea to release with humans steering and reviewing. This page explains the system: what runs
automatically, which skills to use when, and how the setup improves over time.

## The layers

| Layer | Files | Loaded |
|---|---|---|
| Rules for every agent | `AGENTS.md` | Every session (Claude Code imports it through `CLAUDE.md`) |
| Claude workflow | `CLAUDE.md` | Every session |
| Area rules | `.claude/rules/*.md` (`paths:` frontmatter) | When matching files are read or edited |
| Procedures | `.claude/skills/*/SKILL.md` | On `/name`, or automatically when the description matches the task |
| Specialists | `.claude/agents/*.md` | When delegated (reviews run in parallel) |
| Enforcement | `.claude/hooks/*` + `.claude/settings.json`, `.githooks/`, CI | Always; agents can't skip them |
| Knowledge | `docs/domain/`, `docs/security/`, ADRs | On demand (skills point to them) |
| Ground truth | `fixtures/email/` + `manifest.json`, `scripts/dev-mail` | In tests |

## The golden path

```text
idea ──/spec──▶ spec (AC-1..n) ──/adr──▶ decision ──/breakdown──▶ issues (agent:ready)
   ──/implement N──▶ branch + plan + tests + code ──/review-pr──▶ verified findings
   ──/open-pr──▶ PR ──/address-review · /fix-ci──▶ green, approved ──human merge──▶ /cut-release
```

Each step leaves an artifact (spec, ADR, issue, plan, PR), so any session can pick up where another
left off. `/handoff` records progress in the plan, and the SessionStart hook surfaces it on the branch.

## Skill catalog

| Skill | When to use it | Output |
|---|---|---|
| `/spec [idea\|#]` | A new feature or a significant change | `docs/specs/NNNN-*.md` |
| `/adr [title]` | A costly-to-reverse or cross-cutting choice | `docs/decisions/NNNN-*.md` |
| `/breakdown [spec]` | A spec is approved | GitHub issues + epic |
| `/threat-model [feature]` | The feature touches content, credentials, storage, network | threat-model section + SEC criteria |
| `/implement [#]` | Building an issue | branch, plan, tests, commits |
| `/tdd [behavior]` | Logic-heavy work | tests + code, red-green-refactor |
| `/fix-bug [#]` | Any defect | regression test + fix + root-cause note |
| `/refactor [goal]` | A structural change without behavior change | small green commits |
| `/bootstrap-stack` | Once, after ADR-0002 is Accepted | wired scripts, CI, scaffold |
| `email-protocols` | Auto-loads for protocol, sync, MIME or rendering work | routes to `docs/domain/` |
| `/email-fixture [case]` | A specific email shape matters | fixture + manifest expectations |
| `/dev-mail [cmd]` | Anything needing a mail server | running, seeded GreenMail |
| `/discover-mail-server [domain]` | Provisioning or connection issues | `docs/domain/server-profiles/<domain>.md` |
| `/review-pr [#] [--post]` | Before a PR, or reviewing one | verified, ranked findings |
| `/verify-ui [flow]` | Any UI change | screenshots in LTR/RTL, light/dark, phone/desktop |
| `/commit` | Committing | Conventional Commits |
| `/open-pr [#]` | Ready for review | PR following the template |
| `/address-review [#]` | Review comments exist | fixes + threaded replies |
| `/fix-ci [#]` | Checks are red | root-cause fix + green run |
| `/cut-release [ver]` | Releasing | changelog, tag, checklist |
| `/triage [#\|--all]` | New issues | labels, info requests, agent:ready |
| `/handoff` | Pausing work, or context is large | updated plan + pushed WIP + resume prompt |
| `/sync-docs` | After structural changes, before releases | docs that match reality |
| `/codify-lesson [what]` | A correction or an escaped bug | a test, hook, rule or doc that prevents a repeat |
| `/new-skill [name]` | A procedure keeps repeating | new validated skill |

## Subagents

`code-reviewer`, `security-reviewer`, `email-protocol-expert`, `platform-reviewer`, `ux-a11y-reviewer`
and `test-engineer` (which can edit tests), plus `tech-researcher` (cited research). Reviewers are
read-only and return findings in a fixed format (severity, file:line, evidence, fix, confidence), and
the main session verifies each finding before acting on it. `/review-pr` picks reviewers from the
changed paths.

## Guardrails (hooks)

| Hook | Does | Bypass |
|---|---|---|
| SessionStart | Context snapshot (branch, plan, stack status); `scripts/setup` in cloud sessions | none needed |
| PreToolUse: Bash | Denies force-push, pushes to main, `--no-verify`, catastrophic `rm`, `curl\|sh`, secret printing; asks before work-destroying git and remote deletes | a human runs the command themselves |
| PreToolUse: edits | Denies lockfiles and generated code; asks before editing guardrails, CI, accepted ADRs, existing fixtures | human confirmation |
| PostToolUse | Formats the edited file (stack formatter, when installed) | none |
| Stop | Runs `scripts/check --fast --changed`; blocks once on failure | `ISUPPLY_SKIP_STOP_CHECK=1` |
| git pre-commit / commit-msg | Secret scan, no real `.eml` outside fixtures, file-size limit, Conventional Commits | none (`--no-verify` is blocked for agents) |

Every hook rule has a test in `scripts/tests/test_hooks.py`.

## Running agents in parallel

- **Worktrees**: one issue per worktree and session (`claude --worktree`, or `git worktree add ../isupply-mail-12 -b feat/12-x`).
  Pick issues that `/breakdown` marked as parallelizable.
- **Cloud sessions** (claude.ai/code): the SessionStart hook runs `scripts/setup`. Commit and push
  often, because containers are ephemeral (`/handoff`).
- **GitHub CLI in cloud sessions**: GraphQL is blocked, so use the REST forms in [github-cli.md](github-cli.md).
- **GitHub**: `@claude` in issues and PRs (`.github/workflows/claude.yml`), automatic PR review
  (`claude-review.yml`), automatic triage (`claude-triage.yml`).

## Enabling the GitHub workflows

1. Install the Claude GitHub App on the repo (`/install-github-app` in Claude Code, or
   https://github.com/apps/claude). If it offers to add workflow files, skip that step, because
   ours are already committed.
2. Add the secret `ANTHROPIC_API_KEY` (Console API key) **or** `CLAUDE_CODE_OAUTH_TOKEN` (from
   `claude setup-token`, uses your subscription).
3. Add the repository variables (Settings → Secrets and variables → Actions → Variables):
   `CLAUDE_ENABLED=true` (@claude mentions), and optionally `CLAUDE_AUTO_REVIEW=true` and
   `CLAUDE_AUTO_TRIAGE=true`.
4. Recommended: protect `main` (require PRs, the `check` status, linear history), and enable
   Dependabot alerts and secret scanning.

## How the system improves

- **`/codify-lesson`** after every correction turns lessons into tests, hooks, rules or docs.
- **`/sync-docs`** keeps docs truthful, and `scripts/agent/validate_config.py` (part of `scripts/lint`)
  keeps the agent config valid.
- New repeated procedures become skills (`/new-skill`). Recurring review findings become rules or lint
  checks.
- The stack-specific skills (`scaffold-module`, `upgrade-deps`, platform build and signing) are created
  by `/bootstrap-stack` once the stack is known.
