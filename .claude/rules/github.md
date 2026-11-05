---
paths:
  - ".github/**"
---

# GitHub configuration and workflows

- **Least privilege**: every workflow sets `permissions:` explicitly, at the minimum needed.
- **Pin third-party actions** to a release tag at least, and prefer a full commit SHA for actions that
  receive secrets. Dependabot (`github-actions` ecosystem) keeps them current.
- **Never** use `pull_request_target` together with a checkout of PR code. Never echo secrets, and never
  pass untrusted input (issue titles, branch names, comment bodies) straight into `run:` shell; go
  through `env:`.
- **Claude workflows** are gated by repository variables (`CLAUDE_ENABLED`, `CLAUDE_AUTO_REVIEW`,
  `CLAUDE_AUTO_TRIAGE`), so they stay dormant until configured. Keep `--max-turns` and job timeouts.
- **CI calls the stable scripts** (`scripts/check`, `scripts/check --full`), never ad-hoc commands, so
  local and CI behavior stay the same.
- **Labels** live in `.github/labels.yml`. Sync them with `scripts/github/sync-labels.sh` after editing.
  Skills (`/triage`, `/breakdown`) rely on the label names.
- Validate with `actionlint` (part of `scripts/lint` when installed; always in CI).
