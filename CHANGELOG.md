# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). Entries are written for users, while commits follow
Conventional Commits.

## [Unreleased]

### Added

- Repository foundation for agent-driven development: AGENTS.md/CLAUDE.md, 25 workflow skills,
  7 specialist subagents, path-scoped rules, guardrail hooks, stable `scripts/` interface, git hooks.
- Email conformance corpus (19 synthetic fixtures + manifest) with a reference parser and tests.
- Local IMAP/SMTP dev server (GreenMail) with fixture seeding, bulk data and integration tests.
- Email tools: inspect, anonymize, server discovery, server probe.
- Product, architecture, email-domain, security and testing documentation; ADR-0001..0003.
- CI (quality gate, integration, workflow lint) and Claude GitHub workflows (mentions, review, triage).
