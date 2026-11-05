---
paths:
  - ".claude/**"
  - "CLAUDE.md"
  - "AGENTS.md"
---

# Agent configuration (skills, subagents, rules, hooks, memory)

- **Validate**: `python3 scripts/agent/validate_config.py` (part of `scripts/lint`) must pass. It checks
  frontmatter, names, description budgets, links, imports and hook wiring.
- **Skills** (`.claude/skills/<name>/SKILL.md`): the name is kebab-case and matches the folder, and must
  not collide with built-in commands. The description puts the use case first, in under 600
  characters, with no `<`/`>`. The body stays under 500 lines with the most important steps at the top;
  move detail into sibling files. Set `disable-model-invocation: true` for side-effectful one-offs. List
  every skill in `CLAUDE.md` and `docs/agentic/README.md`. Use `/new-skill`.
- **Subagents** (`.claude/agents/<name>.md`): give them the narrowest tools that work. Reviewers are
  read-only and their descriptions say when to use them proactively. They report findings in a fixed
  format; the main session decides and edits.
- **Rules** (`.claude/rules/`): one topic per file, path-scoped via `paths:` (the only key Claude Code
  reads). Global rules belong in `AGENTS.md`.
- **Hooks** (`.claude/hooks/`): fast, portable (bash 3.2, Git Bash), and fail-open on internal errors.
  Every rule has a test in `scripts/tests/test_hooks.py`. Changing them needs human confirmation (the
  guard asks).
- **Memory budget**: `CLAUDE.md` + `AGENTS.md` load every session, so keep them under ~300 lines.
  Procedures go in skills, area rules in `rules/`, knowledge in `docs/`.
- `AGENTS.md` is tool-neutral (other agents read it). Claude-only material goes in `CLAUDE.md`.
