---
name: bootstrap-stack
description: One-time wiring of the chosen technology stack after ADR-0002 is Accepted — scaffold the monorepo, replace every STACK placeholder in scripts and hooks, wire the fixture conformance suite, update CI, ignores, permissions, docs and AGENTS.md, and add stack-specific skills. Use only when the user confirms the stack decision is final.
disable-model-invocation: true
---

# Bootstrap the application stack

ADR-0002 status: !`grep -m1 -E '^- \*\*Status:\*\*' docs/decisions/0002-technology-stack.md 2>/dev/null || true`
Placeholders to resolve:
!`grep -rn "STACK:" scripts .claude/hooks .gitignore .github 2>/dev/null | cut -c1-160 || true`

## 0. Gate

ADR-0002 must be `Accepted` and name concrete choices **with versions**: languages, UI framework per
platform, shared core, local storage, HTML rendering approach, backend (gateway, push relay,
provisioning), package manager, test frameworks and minimum OS versions. If anything is vague, stop and
resolve it with the user first (`/adr` can amend through a new ADR).

## 1. Plan (get approval)

Turn every `STACK:` marker above into a checklist item in `docs/plans/0000-bootstrap-stack.md`, plus
the sections below. Show the plan to the user before scaffolding.

## 2. Scaffold

- Create the monorepo layout from the ADR (for example `apps/{web,desktop,mobile}`, `packages/{core,ui}`,
  `services/{gateway,push}`). Each target gets a minimal hello-world that builds and runs.
- Pin toolchain versions (`.tool-versions`, `.nvmrc`, `fvm`, `rust-toolchain.toml`… whatever the stack uses).
- Use the official generators where they exist. Commit generator output separately from hand edits.

## 3. Wire the stable command interface (never change the CLI contract)

| Script | Wire |
|---|---|
| `scripts/setup` | idempotent, non-interactive dependency install |
| `scripts/fmt` | formatters, with `--check` mode |
| `scripts/lint` (`lint_app`) | analyzers, linters and type checkers, warnings as errors |
| `scripts/test` (`test_app`) | unit/widget tests honoring `-k` and `--fast`, plus a **fixture conformance test** that iterates `fixtures/email/manifest.json` through the app's MIME layer with the same semantics as `scripts/tests/_support.py::conformance_errors` |
| `scripts/dev` | each target (web, desktop, android, ios, server) |
| `scripts/doctor` | toolchain checks with install hints |

## 4. Agent guardrails

- `.claude/hooks/format-file.sh`: map the stack's file types to its formatter.
- `.claude/hooks/protected-paths.txt`: add generated-code patterns and this stack's lockfile, with a
  test case in `scripts/tests/test_hooks.py` for each.
- `.claude/settings.json`: allow the stack's safe read-only and test commands, and ask or deny
  dangerous ones (publish, deploy).
- `.gitignore` build outputs. `.gitattributes`: `linguist-generated` for codegen.
- Add MCP servers to `.mcp.json` if they materially help (for example the Dart/Flutter MCP server, or
  Playwright for web E2E), and document them in `docs/agentic/README.md`.

## 5. CI

Extend `.github/workflows/ci.yml` with build and test jobs per platform: Linux for web, desktop and
backend; Windows desktop; macOS desktop and the iOS simulator; an Android emulator or build. Add
caching. Keep `scripts/check` as the single gate job. Add Dependabot ecosystems for the stack.

## 6. Docs and memory

Update the AGENTS.md status, repo map and commands; `docs/architecture/overview.md` (actual
components); `docs/testing/strategy.md` (frameworks per tier); `scripts/README.md`; and `README.md`
quick start.

## 7. Stack-specific skills

Create them with `/new-skill`, for example `scaffold-module` (a new package or feature following
conventions), `upgrade-deps`, `add-migration` (if there is a local database), and platform build or
signing skills. Add each to the `CLAUDE.md` table.

## 8. Verify and ship

`scripts/doctor` → `scripts/check` → `scripts/check --full` → `scripts/dev web` smoke test. The
validator must show no remaining `STACK:` markers. Use logical commits (`build: scaffold …`,
`build: wire scripts …`, `ci: …`), then `/open-pr` titled `build: bootstrap <stack>`.
