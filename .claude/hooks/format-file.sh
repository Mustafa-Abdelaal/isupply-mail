#!/usr/bin/env bash
# PostToolUse(Edit|Write): format the file Claude just wrote, using the project's formatter for
# that language when it is installed. Silent no-op otherwise. Never fails the tool call.
# STACK: /bootstrap-stack adjusts this mapping to the chosen stack's formatters.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

file="$(json_get .tool_input.file_path)"
[ -n "$file" ] && [ -f "$file" ] || exit 0
rel="$(repo_relative "$file")"
[ -n "$rel" ] || exit 0

case "$rel" in
  fixtures/* | *.eml | *.lock | *-lock.* | *.min.* | docs/*) exit 0 ;;
esac

fmt() { "$@" >/dev/null 2>&1 || true; }
have() { command -v "$1" >/dev/null 2>&1; }

case "$file" in
  *.dart) have dart && fmt dart format "$file" ;;
  *.ts | *.tsx | *.js | *.jsx | *.mjs | *.cjs | *.css | *.scss | *.html | *.vue | *.svelte)
    [ -x "$PROJECT_DIR/node_modules/.bin/prettier" ] && fmt "$PROJECT_DIR/node_modules/.bin/prettier" --write --log-level warn "$file"
    ;;
  *.rs) have rustfmt && fmt rustfmt --edition 2021 "$file" ;;
  *.go) have gofmt && fmt gofmt -w "$file" ;;
  *.php) [ -x "$PROJECT_DIR/vendor/bin/pint" ] && fmt "$PROJECT_DIR/vendor/bin/pint" "$file" ;;
  *.kt | *.kts) have ktlint && fmt ktlint -F "$file" ;;
  *.swift) have swift-format && fmt swift-format -i "$file" ;;
  *.py) have ruff && fmt ruff format --quiet "$file" ;;
esac
exit 0
