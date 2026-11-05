---
name: handoff
description: Save the state of in-progress work so another session, agent or person can resume without re-discovery — update the plan file (done, next steps, decisions, open questions, gotchas), commit and push WIP to the branch, and print a ready-to-paste resume prompt. Use before stopping, when context is getting large, or when switching tasks.
---

# Hand off in-progress work

Branch: !`git branch --show-current 2>/dev/null || true`
Uncommitted: !`git status --short 2>/dev/null | head -30 || true`

Cloud sessions run in ephemeral containers. Anything that isn't committed and pushed is lost.

## Steps

1. **Find the plan**: `docs/plans/<issue>-*.md` for this branch. If there isn't one, create it from the
   template, with the issue number taken from the branch name.
2. **Update its "Progress log"** with a dated entry:
   - **Done**: what's finished and verified, with evidence (commands and results).
   - **In progress**: the exact state (for example "test X written and failing as expected; implementation
     not started").
   - **Next steps**: ordered and concrete, naming files and functions, ticked off the checkbox list.
   - **Decisions made** and why (anything ADR-worthy becomes an `/adr`).
   - **Open questions** for the user, and blockers.
   - **Gotchas** discovered: things the next agent would otherwise re-learn (and consider
     `/codify-lesson` for them).
3. **Commit WIP**, even if it's red: `git add -A && git commit -m "wip(<scope>): <state> [skip ci]"`,
   unless the user prefers stashing. The pre-commit hook still runs. If the gate fails on WIP code,
   commit only the plan file and say so. Then push with `git push -u origin <branch>`.
4. **Print a resume prompt** for the next session:

   ```
   Resume work on <branch> (issue #<n>). Read docs/plans/<file> — progress log and next steps — then continue
   with step <k>: <short description>. Run scripts/check before opening the PR.
   ```

   The SessionStart hook will also surface the plan's open checkboxes automatically on this branch.
