---
name: new-skill
description: Create or improve a project skill in .claude/skills following this repo's conventions — trigger-first description, numbered procedure with exact commands, supporting files for detail, safe dynamic context, validator-clean — and register it in CLAUDE.md and docs/agentic. Use when a workflow repeats, a procedure keeps being re-explained, or the user asks for a new command.
argument-hint: "[skill name and purpose]"
---

# Create a project skill

Request: `$ARGUMENTS`. Existing skills: !`ls .claude/skills 2>/dev/null | tr '\n' ' ' || true`

## 1. Is a skill the right tool?

- A repeatable **procedure** with judgment calls → **skill**.
- A rule that applies while editing certain files → `.claude/rules/` with `paths:`.
- Something that must happen every time, or be blocked → **hook** or test (see `/codify-lesson`).
- Domain knowledge → `docs/domain/`, linked from a skill.
- Check there's no overlap with an existing skill. Prefer extending one.

## 2. Write `.claude/skills/<name>/SKILL.md`

- **Name**: lowercase kebab-case, verb-first where natural (`fix-ci`). It must match the folder and
  must not collide with built-ins (review, security-review, init, doctor, plan, run, loop…).
- **Description**: what it does, then "Use when …" with the words users actually say, in under 600
  characters, with no angle brackets (use `[arg]`). Claude picks skills by description, so it is the
  most important line.
- **Frontmatter options**:
  - `argument-hint`
  - `disable-model-invocation: true` for side-effectful or one-off skills (releases, bootstrap)
  - `allowed-tools: Bash(cmd:*), ...` only for safe, read-only commands the skill always runs
  - `context: fork` plus `agent:` for self-contained research that doesn't need the conversation
- **Body**: put the most important steps first (after compaction only the start of a skill may
  survive). Use numbered steps with exact commands from `scripts/` and expected outputs, include the
  guardrails ("never …") and say where artifacts go. Keep it under ~150 lines; anything longer goes
  in sibling files (`reference.md`, `checklist.md`) linked with relative links.
- **Dynamic context** (`` !`cmd` ``): only read-only commands that are allowed by settings or
  `allowed-tools`, always with `|| true`, because a failure aborts the skill. Never interpolate
  `$ARGUMENTS` into a shell command.
- **Arguments**: `$ARGUMENTS`, or `$0`/`$1` for positional ones.

## 3. Register and validate

1. Add it to the skills table in `CLAUDE.md` and to the catalog in `docs/agentic/README.md`.
2. Run `python3 scripts/agent/validate_config.py`. It must report no errors.
3. Dry-run it: invoke `/<name>` on a realistic case, check that it triggers from a natural request, and
   tighten the description if it triggers wrongly.
4. Commit with `chore(agent): add /<name> skill`.
