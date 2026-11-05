---
name: cut-release
description: Prepare a release — derive the semantic version from Conventional Commits, update CHANGELOG.md, bump every platform's version and build numbers, tag, draft GitHub release notes for staff, and walk the per-platform release checklist (web deploy, desktop signing/notarization/auto-update, App Store and Play submission). Use only when the user asks to release.
disable-model-invocation: true
argument-hint: "[version | major | minor | patch]"
---

# Cut a release

Last tag (empty = first release): !`git describe --tags --abbrev=0 2>/dev/null || true`
Recent commits:
!`git log --oneline -60 2>/dev/null || true`

Use `git log --oneline <last-tag>..HEAD` to get the exact set of commits since the last release.

## 1. Readiness

- You are on an up-to-date `main` with green CI on the release commit (`gh run list --branch main --limit 3`).
- There are no open `priority:p0` or `type:bug` issues with the milestone label
  (`gh issue list --label priority:p0`).

## 2. Version

Apply SemVer from the commits since the last tag: any breaking change → major (or minor while we're in
0.x), any `feat` → minor, otherwise patch. Use `$ARGUMENTS` instead if it's given. Mobile stores also
need a monotonically increasing **build number**, which is separate from the version.

## 3. Changelog and notes

- Update `CHANGELOG.md` (Keep a Changelog format): move "Unreleased" items under `## [x.y.z] — YYYY-MM-DD`,
  grouped as Added, Changed, Fixed or Security, and written in user language.
- Draft the **staff-facing release notes** in plain English plus an Arabic summary: what's new, what's
  fixed, any action needed (for example "sign in again"). Avoid jargon.

## 4. Bump versions everywhere

STACK: list every manifest after `/bootstrap-stack`, for example the web package version, desktop
bundle version (Windows/macOS/Linux), Android `versionName`/`versionCode`, iOS
`CFBundleShortVersionString`/`CFBundleVersion`, and the backend image tag. One commit:
`chore(release): vX.Y.Z`.

## 5. Tag and release (each step needs the user's go-ahead)

`git tag -a vX.Y.Z -m "vX.Y.Z"` → push the tag (after confirmation) → `gh release create vX.Y.Z --notes-file <notes> --draft`.
The guard asks before publishing. Release workflows (added at bootstrap) build the signed artifacts
from the tag.

## 6. Per-platform checklist

Run through [checklist.md](checklist.md) and report each item as done, skipped (with a reason) or blocked.
