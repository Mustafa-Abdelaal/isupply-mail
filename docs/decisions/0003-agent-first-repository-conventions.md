# ADR-0003: Agent-first repository conventions

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner
- **Related:** [agentic workflow guide](../agentic/README.md) · [ADR-0001](0001-record-architecture-decisions.md)

## Context

Most code will be written by AI agents (Claude Code locally, in the cloud and in GitHub Actions, and
possibly other tools), reviewed by a small team. Agents are fast but forgetful and literal. Without
structure they drift from conventions, re-learn the same lessons, and skip verification.

## Decision

1. **A stable command interface**: `scripts/{check,lint,test,fmt,dev,dev-mail,setup,doctor}`. Agents,
   hooks, skills and CI call only these. Stack-specific commands sit behind them (`STACK:` markers),
   so the stack can be chosen later without rewriting the workflow.
2. **Layered agent memory**: `AGENTS.md` (tool-neutral rules) imported by `CLAUDE.md` (Claude
   workflow); path-scoped `.claude/rules/`; procedures as skills; knowledge in `docs/`. The always-loaded
   part stays small.
3. **Enforcement over instruction**: guard hooks (destructive git, secrets, protected paths), a Stop
   hook that runs the fast gate, git hooks (secret scan, Conventional Commits), and a config validator
   in CI.
4. **An email conformance corpus**: `fixtures/email/` plus `manifest.json` is the stack-independent
   answer key for parsing and rendering. A reference oracle (`scripts/email/emaillib.py`) keeps the
   corpus honest, and the app must pass the same suite.
5. **A real local mail server** (GreenMail via Docker) for integration tests instead of mocks.
6. **Spec → plan → issue → PR traceability**: specs and plans in `docs/`, agent-ready issue forms,
   with plans surfaced automatically at session start.
7. **Specialist subagents** for review (code, security, protocol, platform, UX/a11y), run in parallel.

## Consequences

- Positive: consistent agent behavior across sessions and tools; mistakes get codified
  (`/codify-lesson`); the stack decision stays reversible until bootstrap.
- Negative: some upfront structure to maintain. The validator and `/sync-docs` keep it from rotting.
- Revisit if: agent tooling changes substantially, or the team finds a convention adds friction
  without catching problems.
