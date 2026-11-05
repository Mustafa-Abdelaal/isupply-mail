#!/usr/bin/env python3
"""Validate the repository's agent configuration and documentation wiring.

Usage: python3 scripts/agent/validate_config.py [--strict] [--quiet]

Checks (errors fail CI; warnings are printed, and fail too with --strict):
  settings    .claude/settings.json is valid JSON; hook commands point at existing scripts
  skills      .claude/skills/*/SKILL.md: frontmatter parses, name == folder, description present and
              within budget, no angle brackets in description, body <= 500 lines, no collisions with
              built-in commands, relative links resolve
  agents      .claude/agents/*.md: name/description present, name == filename, known tools/model values
  rules       .claude/rules/**/*.md: only `paths` frontmatter, paths is a list of globs
  memory      CLAUDE.md @imports resolve; CLAUDE.md + AGENTS.md stay small; AGENTS.md exists
  links       relative Markdown links in docs/, skills, agents, rules and root *.md resolve
  adrs        docs/decisions/NNNN-*.md have a valid Status line and are listed in the index
  fixtures    .gitattributes protects *.eml; no stray .eml files outside fixtures/email/
  stack       reports remaining STACK: placeholders (warning once ADR-0002 is Accepted)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
BUILTIN_COMMANDS = {
    "add-dir", "agents", "bug", "clear", "compact", "config", "context", "cost", "doctor", "exit", "export", "help",
    "hooks", "ide", "init", "install-github-app", "login", "logout", "mcp", "memory", "model", "permissions",
    "plugin", "pr-comments", "release-notes", "resume", "review", "rewind", "sandbox", "security-review", "status",
    "statusline", "terminal-setup", "todos", "upgrade", "usage", "vim", "code-review", "simplify", "loop", "run",
    "batch", "fork", "plan", "skills", "output-style", "privacy-settings", "feedback", "cd", "effort", "fast",
}
KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch", "Agent", "Task",
    "TodoWrite", "NotebookEdit", "Skill", "AskUserQuestion", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet",
}
MODELS = {"sonnet", "opus", "haiku", "fable", "inherit"}
ADR_STATUSES = {"Proposed", "Accepted", "Rejected", "Deprecated", "Superseded"}
DESCRIPTION_SOFT_LIMIT = 600  # listing budget is shared by every skill; keep entries tight
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


class Report:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def rel(p: Path) -> str:
    return p.relative_to(REPO).as_posix()


def parse_frontmatter(text: str) -> Tuple[Optional[Dict[str, object]], str]:
    """Minimal YAML subset: `key: value`, `key: >`/`|` blocks, and `- item` lists. Returns (data, body)."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, text
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    data: Dict[str, object] = {}
    key: Optional[str] = None
    mode = ""
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith((" ", "\t")) and key:
            stripped = raw.strip()
            if stripped.startswith("- ") and mode == "list":
                data.setdefault(key, [])
                data[key].append(stripped[2:].strip().strip('"').strip("'"))  # type: ignore[union-attr]
            elif mode == "block":
                data[key] = (str(data.get(key, "")) + " " + stripped).strip()
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            raise ValueError(f"cannot parse frontmatter line: {raw!r}")
        key, value = m.group(1), m.group(2).strip()
        if value in (">", "|", ">-", "|-"):
            mode, data[key] = "block", ""
        elif value == "":
            mode, data[key] = "list", []
        else:
            mode = ""
            data[key] = value.strip('"').strip("'")
    return data, "\n".join(lines[end + 1:])


def check_links(path: Path, text: str, report: Report) -> None:
    in_code = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for target in LINK_RE.findall(re.sub(r"`[^`]*`", "", line)):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (path.parent / target_path).resolve()
            if not resolved.exists():
                report.error(f"{rel(path)}:{n}", f"broken link -> {target}")


def check_settings(report: Report) -> None:
    p = REPO / ".claude" / "settings.json"
    try:
        settings = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        report.error(rel(p), f"invalid JSON: {e}")
        return
    for event, groups in settings.get("hooks", {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                for script in re.findall(r"\.claude/hooks/([A-Za-z0-9_.-]+)", cmd):
                    if not (REPO / ".claude" / "hooks" / script).is_file():
                        report.error(rel(p), f"{event} hook references missing script .claude/hooks/{script}")
    for kind in ("allow", "ask", "deny"):
        for rule in settings.get("permissions", {}).get(kind, []):
            if re.match(r"^Bash\(.*:\*.+\)$", rule):
                report.error(rel(p), f"{kind} rule {rule!r}: ':*' is only valid at the end of a pattern")


def check_skills(report: Report) -> List[str]:
    names = []
    root = REPO / ".claude" / "skills"
    for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        f = skill_dir / "SKILL.md"
        where = rel(f)
        if not f.is_file():
            report.error(rel(skill_dir), "missing SKILL.md")
            continue
        text = f.read_text(encoding="utf-8")
        try:
            fm, body = parse_frontmatter(text)
        except ValueError as e:
            report.error(where, str(e))
            continue
        if fm is None:
            report.error(where, "missing YAML frontmatter (must start at line 1 with ---)")
            continue
        name = str(fm.get("name", skill_dir.name))
        names.append(name)
        if name != skill_dir.name:
            report.error(where, f"name {name!r} must equal folder name {skill_dir.name!r}")
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", name):
            report.error(where, f"name {name!r} must be lowercase kebab-case")
        if name in BUILTIN_COMMANDS:
            report.error(where, f"name {name!r} collides with a built-in Claude Code command/skill")
        desc = str(fm.get("description", "")) + " " + str(fm.get("when_to_use", ""))
        desc = desc.strip()
        if not desc:
            report.error(where, "description is required (Claude uses it to decide when to load the skill)")
        if len(desc) > 1536:
            report.error(where, f"description+when_to_use is {len(desc)} chars (> 1536 is truncated)")
        elif len(desc) > DESCRIPTION_SOFT_LIMIT:
            report.warn(where, f"description is {len(desc)} chars; keep under {DESCRIPTION_SOFT_LIMIT} (shared listing budget)")
        if "<" in desc or ">" in desc:
            report.error(where, "description contains < or > (rendered as &lt;/&gt;); use [square brackets]")
        for b in ("disable-model-invocation", "user-invocable"):
            if b in fm and str(fm[b]).lower() not in ("true", "false", "yes", "no", "on", "off", "1", "0"):
                report.error(where, f"{b} must be a boolean")
        if fm.get("context") not in (None, "fork"):
            report.error(where, "context must be 'fork' when set")
        n_lines = len(body.splitlines())
        if n_lines > 500:
            report.error(where, f"SKILL.md body has {n_lines} lines (> 500); move detail into supporting files")
        check_links(f, body, report)
        for extra in skill_dir.rglob("*.md"):
            if extra != f:
                check_links(extra, extra.read_text(encoding="utf-8"), report)
    dupes = {n for n in names if names.count(n) > 1}
    for d in sorted(dupes):
        report.error(".claude/skills", f"duplicate skill name {d!r}")
    return names


def check_agents(report: Report) -> None:
    root = REPO / ".claude" / "agents"
    for f in sorted(root.glob("*.md")) if root.is_dir() else []:
        where = rel(f)
        try:
            fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError as e:
            report.error(where, str(e))
            continue
        if not fm or not fm.get("name") or not fm.get("description"):
            report.error(where, "agents need name and description frontmatter (otherwise they are skipped)")
            continue
        if fm["name"] != f.stem:
            report.error(where, f"name {fm['name']!r} must equal filename {f.stem!r}")
        if ":" in str(fm["name"]):
            report.error(where, "agent names cannot contain ':'")
        tools = fm.get("tools")
        tool_list = tools if isinstance(tools, list) else [t.strip() for t in str(tools or "").split(",") if t.strip()]
        for t in tool_list:
            base = t.split("(")[0]
            if base not in KNOWN_TOOLS and not base.startswith("mcp__"):
                report.warn(where, f"unknown tool {t!r}")
        if "model" in fm and str(fm["model"]) not in MODELS and not str(fm["model"]).startswith("claude-"):
            report.error(where, f"model {fm['model']!r} is not one of {sorted(MODELS)} or a full model id")
        check_links(f, body, report)


def check_rules(report: Report) -> None:
    root = REPO / ".claude" / "rules"
    for f in sorted(root.rglob("*.md")) if root.is_dir() else []:
        where = rel(f)
        try:
            fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError as e:
            report.error(where, str(e))
            continue
        if fm:
            for k in fm:
                if k != "paths":
                    report.warn(where, f"rule frontmatter key {k!r} is ignored by Claude Code (only 'paths' is read)")
            if "paths" in fm and not isinstance(fm["paths"], list):
                report.error(where, "paths must be a YAML list of glob strings")
        check_links(f, body, report)


def check_memory(report: Report) -> None:
    claude = REPO / "CLAUDE.md"
    agents = REPO / "AGENTS.md"
    if not agents.is_file():
        report.error("AGENTS.md", "missing (tool-neutral agent guide imported by CLAUDE.md)")
    if not claude.is_file():
        report.error("CLAUDE.md", "missing")
        return
    total = 0
    for f in (claude, agents):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            total += len(text.splitlines())
            in_code = False
            for line in text.splitlines():
                if line.lstrip().startswith("```"):
                    in_code = not in_code
                if in_code:
                    continue
                for imp in re.findall(r"(?:^|\s)@([A-Za-z0-9_./-]+\.md)\b", re.sub(r"`[^`]*`", "", line)):
                    if not (f.parent / imp).is_file():
                        report.error(rel(f), f"@import {imp} does not exist")
            check_links(f, text, report)
    if total > 300:
        report.warn("CLAUDE.md+AGENTS.md", f"{total} lines are loaded every session; keep under ~300 (move detail to skills/rules/docs)")


def check_adrs(report: Report) -> None:
    root = REPO / "docs" / "decisions"
    if not root.is_dir():
        return
    index = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    for f in sorted(root.glob("[0-9][0-9][0-9][0-9]-*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"^- \*\*Status:\*\* *([A-Za-z]+)", text, re.MULTILINE)
        if not m:
            report.error(rel(f), "missing '- **Status:** <Proposed|Accepted|...>' line")
        elif m.group(1) not in ADR_STATUSES:
            report.error(rel(f), f"status {m.group(1)!r} not in {sorted(ADR_STATUSES)}")
        if f.name not in index:
            report.error(rel(f), "not listed in docs/decisions/README.md")


def check_fixture_hygiene(report: Report) -> None:
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8") if (REPO / ".gitattributes").is_file() else ""
    if not re.search(r"^\*\.eml\s+-text", attrs, re.MULTILINE):
        report.error(".gitattributes", "must contain '*.eml -text' so fixtures keep CRLF bytes")
    try:
        tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "--cached", "--others", "--exclude-standard", "*.eml"],
                                 capture_output=True, text=True, check=False).stdout.split()
    except OSError:
        tracked = []
    for f in tracked:
        if not f.startswith("fixtures/email/"):
            report.error(f, ".eml files are only allowed under fixtures/email/ (real mail must never be committed)")


def check_stack_markers(report: Report) -> None:
    adr = REPO / "docs" / "decisions" / "0002-technology-stack.md"
    accepted = adr.is_file() and re.search(r"^- \*\*Status:\*\* *Accepted", adr.read_text(encoding="utf-8"), re.MULTILINE)
    count = 0
    for f in list((REPO / "scripts").glob("*")) + list((REPO / ".claude" / "hooks").glob("*.sh")):
        if f.is_file() and "STACK:" in f.read_text(encoding="utf-8", errors="replace"):
            count += 1
    if accepted and count:
        report.warn("stack", f"ADR-0002 is Accepted but {count} script(s) still contain STACK: placeholders — run /bootstrap-stack")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    report = Report()
    check_settings(report)
    skills = check_skills(report)
    check_agents(report)
    check_rules(report)
    check_memory(report)
    for md in list(REPO.glob("*.md")) + list((REPO / "docs").rglob("*.md")) + list((REPO / "fixtures").rglob("*.md")) + list((REPO / "infra").rglob("*.md")) + list((REPO / "scripts").rglob("*.md")) + list((REPO / ".github").rglob("*.md")):
        if md.name not in ("CLAUDE.md", "AGENTS.md"):
            check_links(md, md.read_text(encoding="utf-8"), report)
    check_adrs(report)
    check_fixture_hygiene(report)
    check_stack_markers(report)
    for w in report.warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in report.errors:
        print(f"error: {e}", file=sys.stderr)
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    if not args.quiet:
        status = "FAILED" if failed else "OK"
        print(f"agent config {status}: {len(skills)} skills, {len(report.errors)} errors, {len(report.warnings)} warnings", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
