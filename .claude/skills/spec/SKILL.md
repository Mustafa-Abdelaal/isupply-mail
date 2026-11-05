---
name: spec
description: Turn a feature idea, staff request or GitHub issue into a written spec in docs/specs/ — user stories, numbered testable acceptance criteria, platform matrix, email edge cases, security/privacy, a11y/i18n and a test plan. Use before building anything non-trivial.
argument-hint: "[idea | issue number]"
---

# Write a feature spec

> **Cloud sessions:** GitHub GraphQL is blocked there, so the `gh issue`/`gh pr`/`gh label list` commands below need their REST forms. See [github-cli.md](../../../docs/agentic/github-cli.md).

Input: `$ARGUMENTS` (an idea, a staff complaint, or a GitHub issue number).
A spec states **what** and **why**. **How** goes in a plan (`/implement`), and decisions go in ADRs (`/adr`).

## 1. Gather context before writing anything

- For an issue number, run `gh issue view <n> --comments`.
- Read [vision](../../../docs/product/vision.md), [requirements](../../../docs/product/requirements.md)
  and [open questions](../../../docs/product/open-questions.md), and note which requirement IDs (R-xx)
  this touches.
- Read the `docs/domain/` pages relevant to the feature (threading needs imap.md and mime.md; compose
  needs smtp.md and mime.md).
- Run `ls docs/specs/`. If a spec already covers this, extend it instead of creating a duplicate.

## 2. Interview the user (AskUserQuestion, at most 4 questions per round)

Ask only what changes the design: who needs it and when, how success is measured, where the scope
ends, which platforms come first, offline expectations, and what IT/admins need. Offer a recommended
default for each question. Never ask anything the docs already answer.

## 3. Write `docs/specs/NNNN-slug.md` from [the template](../../../docs/specs/template.md)

NNNN is the next free 4-digit number. Fill every section; write "None" rather than deleting one.

- **Acceptance criteria**: Given/When/Then, numbered `AC-1…`, each verifiable by a test or a screenshot.
- **Platform matrix**: list behavior differences and OS integrations (notifications, `mailto:`,
  share sheet, background limits) for each of web, windows, macos, linux, android, ios.
- **Email edge cases**: work through [edge-cases.md](edge-cases.md) and keep every item that applies.
- **Security and privacy**: data touched, trust boundaries. If anything non-trivial comes up, run
  `/threat-model` next.
- **Test plan**: unit tests, fixture conformance (existing and new fixtures), dev-mail integration,
  E2E and manual checks.

## 4. Review the draft

- Check yourself: is every AC testable? Are non-goals explicit? Are the edge cases considered?
  Did you introduce any new jargon (if so, add it to `docs/domain/glossary.md`)?
- For user-facing or sensitive features, spawn `ux-a11y-reviewer` and `security-reviewer` **in
  parallel** on the spec file and fold their findings in.

## 5. Finish

- Set `Status: Draft`, show the user a summary, and on approval set `Status: Approved`.
- Next steps: `/adr` if the spec forces an architectural decision, then `/breakdown docs/specs/NNNN-slug.md`.
