# Contributing

Humans and agents follow the same process. The rules are in [AGENTS.md](AGENTS.md), and the agent
workflow is in [docs/agentic/README.md](docs/agentic/README.md).

## Setup

```bash
scripts/setup     # enables git hooks (.githooks), checks your toolchain
scripts/doctor    # re-check tools any time
```

Required: git, bash (Git Bash on Windows), Python 3.9+. Recommended: jq, gh, shellcheck, Docker.

## Flow

1. **Issue first.** Every change has an issue (use the templates, or `/spec` → `/breakdown`).
2. **Branch** `<type>/<issue>-<slug>` from `main` (types: feat, fix, refactor, perf, test, docs, build, ci, chore).
3. **Commits** use [Conventional Commits](https://www.conventionalcommits.org): `feat(sync): add QRESYNC path`.
   The `commit-msg` hook enforces the format.
4. **Gate**: `scripts/check` must be green, plus `scripts/check --full` for protocol and sync work.
5. **PR** into `main` using the template: link the issue, list platforms, show how you verified.
6. **Review**: at least one human approval. Agents can pre-review with `/review-pr`.
7. **Merge**: squash or rebase (linear history). Delete the branch.

## Ground rules

- Never commit secrets or real email. `.eml` files belong only in `fixtures/email/`, synthetic or
  anonymized. The pre-commit hook scans for secrets.
- Tests come with every behavior change; bug fixes start with a failing test.
- Architecture decisions go in an ADR (`/adr`).
- Keep docs true in the same PR.
