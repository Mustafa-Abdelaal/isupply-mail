# Security policy

iSupply Mail handles staff email and credentials, so we treat security issues as top priority.

## Reporting a vulnerability

- **Do not** open a public issue or PR describing the vulnerability.
- Report it privately to the repository owner (GitHub: @Mustafa-Abdelaal) or through GitHub's
  **"Report a vulnerability"** (private security advisory) on this repository.
- Include the affected version or commit, the platform, reproduction steps, and the impact. If the
  issue involves a malicious email, attach an **anonymized** `.eml` (`scripts/email/anonymize_eml.py`).

## Our commitments

- We acknowledge reports within 2 business days and agree a fix timeline based on severity.
- Fixes ship with a regression test (a hostile fixture where applicable) and a CHANGELOG `Security`
  entry.

## Scope and design

See the [threat model](docs/security/threat-model.md) for assets, trust boundaries and required
controls.
