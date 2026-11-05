---
name: verify-ui
description: Launch the iSupply Mail app and visually verify a UI change — screenshots in LTR and RTL (Arabic), light and dark, phone and desktop widths, against seeded dev mail — plus keyboard-only and screen-reader checks, with evidence attached to the PR. Use after any UI change, or when asked to run, see or screenshot the app.
argument-hint: "[screen or flow to check]"
---

# Verify the UI in the running app

Flow to check: `$ARGUMENTS`

## 1. Prepare data and the app

1. Run `scripts/dev-mail up && scripts/dev-mail reset` so the mailbox holds the whole fixture corpus:
   Arabic, HTML, attachments, threads, hostile mail. Add `--bulk 2000` when checking scrolling and
   performance.
2. Start the target with `scripts/dev web` (or `desktop`, `android`, `ios`). Read the URL or device from
   its output, and sign in as `alice@isupply.test` / `alice-dev-pw` against `127.0.0.1:3143` / `:3025`.
   - **STACK**: the launch commands, the dev-server account wiring and the E2E tool are set up by
     `/bootstrap-stack`. Until then, report that there is no app to verify.

## 2. Capture the matrix

For web, use Playwright (`require('playwright')`; in cloud sessions Chromium is preinstalled, so don't
run `playwright install`). Capture each relevant screen at:

| Variant | Settings |
|---|---|
| Phone | 390×844, touch |
| Desktop | 1440×900 |
| RTL | Arabic locale (`ar-EG`), `dir=rtl` |
| Dark | `prefers-color-scheme: dark` |

Screens to cover when relevant: the message list (unread/flagged/attachment indicators, long Arabic
subjects); the reader with the HTML newsletter (remote images blocked plus the banner to load them),
the XSS fixture (nothing executes, no layout escape) and the inline-image fixture; compose (RTL typing,
attachments, send progress, offline outbox); and settings. Save the images in the scratchpad or
`.scratch/`, never committed.

## 3. Behavior checks

- Keyboard only: tab order, visible focus, shortcuts, and no traps in dialogs or the reader iframe.
- Screen reader: names and roles on list rows, buttons and toggles. Use axe-core for web if available.
- States: empty folder, loading, server error, offline, and a 100k-message folder (virtualized, no jank).
- Text: 200% OS font scaling, long names, mixed bidi (`PO-2026-0117` inside Arabic sentences).

## 4. Report

Attach the before/after screenshots to the PR description or a comment (`gh pr comment`), list what
you checked per variant, and file issues for problems that are out of scope. Spawn `ux-a11y-reviewer`
on the screenshots and diff for a second look.
