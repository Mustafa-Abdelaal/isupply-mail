---
name: codify-lesson
description: Turn a mistake, correction or hard-won insight into a durable safeguard so no future session repeats it — pick the strongest cheap mechanism (test, lint, hook guard, protected path, skill step, path-scoped rule, domain note, AGENTS.md line) and implement it. Use whenever the user corrects you, a bug escapes review, or you learn a non-obvious fact.
argument-hint: "[what went wrong or what was learned]"
---

# Codify a lesson

Lesson: `$ARGUMENTS`. If it's empty, take it from the recent conversation: what was corrected, and why?

## 1. State it precisely

Write one sentence each:

- **Trigger**: the situation where it applies ("when parsing filenames in Content-Disposition…").
- **Rule**: what to do or never do.
- **Why**: the consequence of getting it wrong, plus a source (RFC section, incident, server observed).

## 2. Choose the strongest mechanism that's cheap enough

| Rank | Mechanism | Use when | Where |
|---|---|---|---|
| 1 | Automated test or fixture | The behavior can be asserted | `scripts/tests/`, app tests, `/email-fixture` |
| 2 | Lint, type or validator check | The pattern is detectable statically | `scripts/lint`, `validate_config.py`, analyzer config |
| 3 | Hook guard or protected path | An agent *action* must be blocked or confirmed | `.claude/hooks/`, `protected-paths.txt` (plus a test) |
| 4 | Skill step | It's part of a procedure | the relevant `.claude/skills/*/SKILL.md` |
| 5 | Path-scoped rule | It applies when touching certain files | `.claude/rules/*.md` with `paths:` |
| 6 | Domain note | It's knowledge (protocol fact, server quirk) | `docs/domain/*.md`, with a source |
| 7 | AGENTS.md line | It's global, short and critical | `AGENTS.md` (keep it small) |

Prefer ranks 1–3: instructions can be forgotten, checks can't. It's often worth doing two (a test plus
a domain note). Don't add an AGENTS.md line for something a test already enforces.

## 3. Implement and prove it

- Add the safeguard and show it catching the original mistake. A new test must fail on the old
  behavior; a new hook rule needs a case in `scripts/tests/test_hooks.py`.
- Run `scripts/check`. For hook or settings changes, expect the guard to ask for human confirmation;
  explain to the user why the change is needed.
- Commit with `chore(agent): codify <lesson>` (or `test:` / `docs:` as appropriate), and tell the user
  what was added and where.
