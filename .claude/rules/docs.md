---
paths:
  - "docs/**"
  - "README.md"
  - "CONTRIBUTING.md"
---

# Documentation

- **Audience**: humans and agents. Lead with the answer, use tables and checklists over prose, and cut
  marketing tone.
- **ADRs** (`docs/decisions/`): numbered `NNNN-kebab-title.md` from `template.md`, with a
  `- **Status:**` line (Proposed / Accepted / Rejected / Deprecated / Superseded) and a row in the
  `README.md` index. Accepted ADRs are immutable: write a new one that supersedes them (`/adr`).
- **Specs** (`docs/specs/NNNN-slug.md`) say *what* and *why*, with numbered, testable acceptance
  criteria. **Plans** (`docs/plans/NNNN-slug.md`, numbered by issue) say *how*, with checkbox progress
  that the SessionStart hook surfaces.
- **Domain notes** (`docs/domain/`) are the canonical email knowledge. When you learn a protocol fact
  or a server quirk, add it there with a source (RFC section or observed server plus version).
- **Links** are relative and must resolve; `scripts/lint` validates them. Mention a path without
  linking it by putting it in backticks.
- When behavior, commands or structure change, update the affected doc in the same PR (`/sync-docs`
  finds drift).
