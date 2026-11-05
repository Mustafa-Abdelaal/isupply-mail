# Implementation plans

A plan describes **how** one issue gets built, and doubles as the hand-off log between sessions. Files
are named by issue number, `NNNN-slug.md` (`feat/12-thread-view` → `0012-thread-view.md`), and start
from [template.md](template.md).

- `/implement` creates the plan, `/handoff` updates it, and the SessionStart hook shows the plan's open
  checkboxes whenever you're on its branch.
- Plans stay in the repo after merge as a lightweight design history (status `Done`). `/sync-docs`
  corrects stale statuses.
