---
paths:
  - "fixtures/email/**"
---

# Email fixture corpus

- **Byte-exact data.** `.eml` files are CRLF (`.gitattributes` has `*.eml -text`). Never reformat, trim
  or re-save them in an editor. The guard hook asks before an existing fixture is edited.
- **Synthetic fixtures** are produced by `generate_synthetic.py`. To change or add one, edit the
  generator and run `python3 fixtures/email/generate_synthetic.py`; the test suite runs `--check`.
- **Real-world fixtures** are only allowed after `scripts/email/anonymize_eml.py` plus a manual review
  (`inspect_eml.py --body`), with `"origin": "anonymized"` in `manifest.json`. No real names, addresses,
  phone numbers, prices or attachment contents.
- **Expectations**: every fixture has an `expect` block (keys documented in
  `manifest.json → expect_keys`), and the reference parser must pass it (`scripts/test -k fixture`).
  The app must pass the same suite.
- **Naming**: `NNN-short-slug.eml`, numbered sequentially, with the slug describing the edge case, not
  the bug.
- Use `/email-fixture` for the full workflow.
