---
name: email-fixture
description: Add a message to the email conformance corpus — synthesize an edge case in fixtures/email/generate_synthetic.py or anonymize a real message — with manifest.json expectations, then prove the reference parser passes. Use when a bug, feature or review involves a specific email shape (charset, MIME structure, HTML, attachment, header quirk).
argument-hint: "[edge case description | path to .eml]"
---

# Add an email fixture

Corpus: `fixtures/email/` · answer key: `manifest.json` · rules: `.claude/rules/email-fixtures.md`
Existing fixtures: !`ls fixtures/email/ 2>/dev/null | grep -c '\.eml$' || true` .eml files

## Choose the path

**A. Synthetic** (preferred, since no privacy risk):

1. Run `jq -r '.fixtures[] | .file + " — " + (.tags|join(","))' fixtures/email/manifest.json` and check
   the shape isn't already covered.
2. In `fixtures/email/generate_synthetic.py`, add a `fixture("NNN-slug.eml", """...""", ...)` call
   after the last one. Keep it deterministic: fixed Date, Message-ID and boundaries, and the
   `b64`/`b64_text`/`qp`/`encoded_words`/`rfc2231` helpers. Use invented people and companies only
   (`@isupply.test`, `@example.com`).
3. Put any bidi or invisible characters in Python source as `\u` escapes, never as literal characters.
4. Run `python3 fixtures/email/generate_synthetic.py`.

**B. Real message** (only when the bug can't be synthesized):

1. Get the `.eml` from the user, kept outside the repo (real mail is git-ignored outside `fixtures/email/`).
2. Run `python3 scripts/email/anonymize_eml.py /path/in.eml -o fixtures/email/NNN-slug.eml --redact-text`
   (drop `--redact-text` only if the text itself triggers the bug and contains nothing sensitive).
3. Review it: `python3 scripts/email/inspect_eml.py fixtures/email/NNN-slug.eml --body`. There must be
   no real names, addresses, phone numbers, prices or attachment contents. Show the user the summary
   and get explicit OK.
4. Confirm the bug still reproduces with the anonymized file.
5. Add a manifest entry by hand: `"origin": "anonymized"` plus `line_endings`, `description`, `tags`,
   `seed` and `expect`. The generator preserves non-synthetic entries.

## Write expectations (the answer key)

- Run `python3 scripts/email/inspect_eml.py fixtures/email/NNN-slug.eml --json` to see what the
  reference parser produces.
- Write `expect` with **only the keys that matter** for this edge case (documented in
  `manifest.json → expect_keys`). For a bug fixture, the expectation is the *correct* behavior, even
  if the app currently fails it.
- Security fixtures list `html_dangerous_at_least` or `warnings_include`; privacy fixtures list
  `remote_resources` and `tracking_pixels`.
- Choose `seed.folder` and `seed.flags` so `scripts/dev-mail seed` places it realistically.

## Prove it

`scripts/test -k fixture` must pass, and the generator's `--check` must be clean. If the reference
parser itself is wrong for the new shape, fix `scripts/email/emaillib.py` (with a unit test) in the
same change. Then commit with `test(fixtures): add NNN-slug (<edge case>)`.
