---
name: sync-docs
description: Find and fix drift between documentation and reality — commands or paths in AGENTS.md/CLAUDE.md/README that no longer exist, stale repo maps, architecture/testing docs that contradict the code, spec/plan/ADR statuses that are wrong, skills or rules referencing removed files, broken links. Use after structural changes, before releases, or periodically.
---

# Sync docs with reality

## 1. Mechanical checks

- Run `python3 scripts/agent/validate_config.py` for links, imports, skill and agent frontmatter, ADR
  index and stack markers. Fix every error.
- For every command in the AGENTS.md command table, confirm the script exists and its `--help` matches
  what the docs claim.
- For every path in the AGENTS.md repo map, `docs/architecture/overview.md` and `scripts/README.md`,
  confirm it exists (`ls`).
- For every skill named in `CLAUDE.md` and `docs/agentic/README.md`, confirm the folder exists, and
  vice versa (`ls .claude/skills`).

## 2. Semantic checks (read and compare)

- **Architecture**: do the components and data flows in `docs/architecture/overview.md` match the code
  (after bootstrap)? Use the `Explore` subagent to map the actual modules.
- **Testing**: does `docs/testing/strategy.md` describe the real tiers, tools and commands?
- **Specs and plans**: specs marked Approved but fully shipped become `Implemented`. Plans for merged
  branches become `Done`. Check with `gh pr list --state merged --search "<issue>"`.
- **ADRs**: is any accepted decision contradicted by the code? Either the code is wrong (file an
  issue) or the decision changed (write a superseding ADR). Never silently edit an accepted ADR.
- **Open questions**: move answered items into the requirements or an ADR.
- **CHANGELOG**: does "Unreleased" cover the merged user-visible changes?

## 3. Fix and report

Make the doc fixes in one `docs: sync …` commit, or several if they're unrelated. List anything that
needs a human decision (contradictions between code and ADRs) as issues, not edits.
