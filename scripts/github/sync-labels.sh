#!/usr/bin/env bash
# Create or update GitHub labels from .github/labels.yml (idempotent). Requires an authenticated gh.
# Usage: scripts/github/sync-labels.sh [--dry-run]
#
# Existing labels that are not in the file are left alone (GitHub's defaults such as "bug" stay usable).

# shellcheck source=../lib/common.sh
source "$(dirname "$0")/../lib/common.sh"

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
cd "$REPO_ROOT"
require_python
have gh || die "gh (GitHub CLI) is required: https://cli.github.com"

"$PY" - .github/labels.yml <<'PY' | while IFS=$'\t' read -r name color desc; do
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
for block in re.split(r"^- ", text, flags=re.MULTILINE)[1:]:
    fields = dict(re.findall(r'^\s*(name|color|description):\s*"([^"]*)"', block, flags=re.MULTILINE))
    if "name" in fields:
        print("\t".join([fields["name"], fields.get("color", "ededed"), fields.get("description", "")]))
PY
  if [ "$DRY" = 1 ]; then
    printf 'would sync: %-22s #%s  %s\n' "$name" "$color" "$desc"
  else
    gh label create "$name" --color "$color" --description "$desc" --force >/dev/null && log_ok "$name"
  fi
done
