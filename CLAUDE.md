@AGENTS.md

# Claude Code in this repository

The rules above bind every agent. This section covers Claude Code specifics: the **skills** that encode
our workflows, the **subagents** that review work, and the **hooks** that run automatically. The full
guide is [docs/agentic/README.md](docs/agentic/README.md).

## Golden path

`/spec` → `/adr` (when a decision is needed) → `/breakdown` → `/implement <issue>` → `/review-pr` →
`/open-pr` → `/address-review` · `/fix-ci` → a human merges → `/cut-release`

## Skills (`.claude/skills/`)

| Stage | Skill | Use it to |
|---|---|---|
| Plan | `/spec` | Turn an idea or staff request into a spec with acceptance criteria |
| Plan | `/adr` | Record or supersede an architecture decision |
| Plan | `/breakdown` | Split a spec into small, agent-ready GitHub issues |
| Plan | `/threat-model` | Run a design-time STRIDE analysis for a feature |
| Build | `/implement` | Take an issue to a tested PR (the golden path) |
| Build | `/tdd` · `/fix-bug` · `/refactor` | Red-green-refactor · reproduce-first bug fixing · safe restructuring |
| Build | `/bootstrap-stack` | One-time wiring of the chosen stack (after ADR-0002 is Accepted) |
| Email | `email-protocols` | Load IMAP/SMTP/MIME/HTML/auth knowledge (auto-loads for protocol work) |
| Email | `/email-fixture` · `/dev-mail` · `/discover-mail-server` | Add a corpus message · run the local mail server · find and verify server settings |
| Verify | `/review-pr` · `/verify-ui` | Parallel multi-agent review · screenshot the app in LTR/RTL, light/dark |
| Ship | `/commit` · `/open-pr` · `/address-review` · `/fix-ci` · `/cut-release` | Commit, open PRs, answer review, fix CI, release |
| Maintain | `/triage` · `/handoff` · `/sync-docs` · `/codify-lesson` · `/new-skill` | Triage issues · save progress · fix doc drift · turn mistakes into safeguards · add skills |

## Subagents (`.claude/agents/`)

| Agent | Use for |
|---|---|
| `code-reviewer` | Correctness, design and test quality of a diff (always part of a review) |
| `security-reviewer` | Hostile HTML/MIME, credentials, TLS, injection, storage, CI |
| `email-protocol-expert` | RFC compliance, sync correctness, real-server quirks |
| `platform-reviewer` | Web, desktop and mobile differences: background limits, push, secure storage, packaging |
| `ux-a11y-reviewer` | Usability for non-technical staff, WCAG, Arabic/RTL, localization |
| `test-engineer` | Writing missing tests and turning bug reports into failing tests (can edit) |
| `tech-researcher` | Cited comparisons of libraries, frameworks and services (ADR input) |

Launch independent reviewers **in parallel in one message**. Give each one the file list, the
acceptance criteria and the relevant `docs/domain/` pages. Subagents report; the main session verifies
their findings and makes the edits.

## Hooks (automatic — `.claude/settings.json`)

- **SessionStart** prints the branch, active plan and stack status. In cloud sessions it also runs `scripts/setup`.
- **PreToolUse** blocks force-pushes, pushes to `main`, `--no-verify`, catastrophic `rm`, `curl | sh` and
  secret dumps. It protects lockfiles, generated code, accepted ADRs and existing fixtures, and asks
  before guardrail or CI edits.
- **PostToolUse** formats each edited file with the stack's formatter, when one is installed.
- **Stop** runs `scripts/check --fast --changed` when there are uncommitted changes, and blocks once on
  failure. Fix the failure, or tell the user why it is unrelated.

When a hook blocks you, read its reason and take the safe alternative it names. Never work around a
guard (by rephrasing a command, say). If a guard is wrong, say so and propose a hook change plus a test
in `scripts/tests/test_hooks.py`.

## Working agreements

- **Explore before editing.** Read the relevant `docs/domain/` page and the existing code. Plan
  multi-file work first (plan mode, or the plan step of `/implement`) and keep `docs/plans/` updated.
- **Verify, don't assume.** Run the scripts and put evidence (test output, screenshots) in your final message.
- **Keep context lean.** Send broad searches to `Explore` and reviews to subagents, then summarize.
- **Make lessons stick.** When the user corrects you, or a mistake escapes, run `/codify-lesson`.
- **Leave a trail.** Before stopping mid-task, or when context gets large, run `/handoff`.
- **Personal preferences** go in `CLAUDE.local.md` (git-ignored), not here.
