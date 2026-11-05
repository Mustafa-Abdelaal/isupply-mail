# Release checklist (per platform)

STACK: refine these items after `/bootstrap-stack`, and replace generic steps with exact commands and
workflow names.

## All platforms

- [ ] `scripts/check --full` green on the release commit
- [ ] Fixture conformance suite green in the app (not just the reference parser)
- [ ] Smoke test against the dev server **and** a real `@isupply.com` test account: sign-in, sync,
      read HTML, send with attachment, search, notifications
- [ ] No debug logging, test endpoints or dev credentials in release builds
- [ ] Crash and analytics reporting strips PII (no addresses, subjects or bodies)
- [ ] Minimum supported OS versions unchanged, or announced

## Web

- [ ] Gateway or backend migrations applied, with a rollback plan
- [ ] CSP and security headers verified; the HTML reader iframe is sandboxed
- [ ] Service worker update path tested (no stale clients stuck on the old version)

## Desktop (Windows, macOS, Linux)

- [ ] Windows: installer signed (Authenticode), SmartScreen reputation considered, `mailto:` registration works
- [ ] macOS: signed with Developer ID, **notarized**, stapled; the Keychain access group is correct
- [ ] Linux: packages (AppImage/deb/rpm/Flatpak as decided) install, and the libsecret keyring works
- [ ] The auto-update feed is signed and the previous version updates to this one

## Android

- [ ] `versionCode` incremented; signed App Bundle; Play target API level meets the current requirement
- [ ] Data safety form still accurate; the notification permission flow (Android 13+) works
- [ ] Staged rollout configured (for example 10%), with crash-rate thresholds watched

## iOS

- [ ] Build number incremented; TestFlight build tested on the oldest supported device and OS
- [ ] Privacy manifest and App Store privacy labels accurate; push entitlement present
- [ ] App Review notes include a **demo account** (a test mailbox, never a staff one)

## After release

- [ ] GitHub release published; CHANGELOG on main
- [ ] Staff announcement sent (English and Arabic), with known issues listed
- [ ] Monitor crash and error dashboards for 48 hours. A hotfix goes through `/fix-bug` plus a patch release.
