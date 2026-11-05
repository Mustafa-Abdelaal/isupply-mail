---
paths:
  - "**/{auth,account,accounts,credentials,keychain,secure_storage,securestorage,crypto,security,sanitize,sanitizer,render,renderer,webview,attachments,storage,db,database}/**"
  - "**/*{auth,Auth,credential,Credential,sanitiz,Sanitiz,keychain,Keychain,token,Token,webview,WebView,Webview,crypto,Crypto}*"
---

# Security-sensitive code (credentials, rendering, storage, attachments)

This code is in scope of the [threat model](../../docs/security/threat-model.md). Re-read its
"Review checklist" before you finish, and request the `security-reviewer` subagent on the diff.

- **Credentials and tokens**: store them only through the platform secure-storage adapter. Never put
  them in preferences files, SQLite, logs, crash reports, URLs or analytics. Wipe them on sign-out.
- **HTML email**: sanitize with an allowlist (never a denylist), then render in a sandbox with no
  script execution and no same-origin access. Block remote loads until the user opts in (per message or
  per sender). Resolve `cid:` locally. Open links externally and show the real target.
- **Attachments**: never auto-open them. Neutralize filenames (bidi controls, path separators, reserved
  names, double extensions) and warn on executable types. Save only to user-chosen or app-sandboxed
  locations.
- **Local data**: use OS-level encryption where available. The cache must be wipeable remotely or on
  sign-out once an admin policy exists. Keep secrets out of backups (iOS/Android backup flags).
- **Network**: verify TLS with the system trust store. No custom "accept all" trust managers, and no
  HTTP fallbacks.
- **Inputs**: treat every header, MIME part, filename, URL and server response as hostile. Bound sizes
  and nesting depth (zip-bomb style MIME).
- **Tests**: cover the hostile fixtures (`011-html-xss-payloads.eml`,
  `012-remote-images-tracking-pixel.eml`, `019-attachment-filename-spoofing.eml`). After
  sanitization, no `html_dangerous_at_least` construct may remain.
