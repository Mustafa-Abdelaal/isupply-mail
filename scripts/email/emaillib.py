"""Reference email-parsing helpers for repo tooling (Python 3.9+ standard library only).

This module is the *oracle* for the fixture conformance suite: `summarize()` defines the
expected, client-facing interpretation of a message (decoded headers, body choice,
attachments vs inline parts, calendar data, risky HTML). Whatever stack the app uses must
produce the same answers for every fixture in fixtures/email/manifest.json.

It is deliberately lenient (like a real client): malformed input yields defects/warnings,
never exceptions.
"""

from __future__ import annotations

import email
import email.policy
import re
import unicodedata
from email.message import EmailMessage, Message
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_bytes(path: "str | Path") -> bytes:
    return Path(path).read_bytes()


def parse_bytes(raw: bytes) -> EmailMessage:
    """Parse with the modern policy (RFC 2047/2231/6532 aware header decoding)."""
    return email.message_from_bytes(raw, policy=email.policy.default)  # type: ignore[return-value]


def load_message(path: "str | Path") -> EmailMessage:
    return parse_bytes(load_bytes(path))


def line_endings(raw: bytes) -> str:
    """'crlf', 'lf' or 'mixed' — fixtures must declare which one they are."""
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and not lf:
        return "crlf"
    if lf and not crlf:
        return "lf"
    return "mixed" if crlf and lf else "none"


# ---------------------------------------------------------------------------
# Headers
# ---------------------------------------------------------------------------


def fix_surrogates(text: str) -> str:
    """Raw 8-bit (RFC 6532 UTF-8) header bytes surface as surrogate escapes; decode them as UTF-8."""
    if any("\udc80" <= ch <= "\udcff" for ch in text):
        return text.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
    return text


def header_text(msg: Message, name: str) -> Optional[str]:
    """Decoded, unfolded header value (first occurrence), or None."""
    try:
        value = msg.get(name)
    except Exception:  # noqa: BLE001 - header parsing defects must not crash tooling
        raw = msg.get_all(name, failobj=[None])[0] if hasattr(msg, "get_all") else None
        value = raw
    if value is None:
        return None
    text = fix_surrogates(str(value))
    text = re.sub(r"\r?\n[ \t]+", " ", text)  # unfold
    return text.strip()


def addresses(msg: Message, name: str) -> List[Dict[str, str]]:
    """Mailbox list for an address header. Groups are flattened; empty groups yield []."""
    out: List[Dict[str, str]] = []
    try:
        header = msg.get(name)
        if header is None:
            return out
        if hasattr(header, "addresses"):
            for a in header.addresses:  # type: ignore[attr-defined]
                if a.addr_spec and a.addr_spec != "<>":
                    out.append({"name": fix_surrogates(a.display_name or ""), "address": a.addr_spec.lower()})
            return out
        pairs = getaddresses([str(header)])
    except Exception:  # noqa: BLE001
        pairs = getaddresses(msg.get_all(name, []))
    for display, addr in pairs:
        if addr:
            out.append({"name": display or "", "address": addr.lower()})
    return out


MSGID_RE = re.compile(r"<[^<>\s]+>")


def message_ids(value: Optional[str]) -> List[str]:
    return MSGID_RE.findall(value or "")


def iso_date(msg: Message) -> Optional[str]:
    raw = header_text(msg, "Date")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat()
    from datetime import timezone

    return dt.astimezone(timezone.utc).isoformat()


# Reply/forward prefixes seen in the wild, including Arabic Outlook ("رد:" / "إعادة توجيه:").
SUBJECT_PREFIX_RE = re.compile(
    r"^\s*(?:(?:re|aw|sv|antw|vs|ref|rif|fw|fwd|tr|wg|enc|rv|رد|إعادة توجيه|توجيه)\s*(?:\[\d+\])?\s*[:：]\s*)+",
    re.IGNORECASE,
)


def normalize_subject(subject: Optional[str]) -> str:
    """Subject used for thread grouping: reply/forward prefixes and list tags removed."""
    s = subject or ""
    prev = None
    while prev != s:
        prev = s
        s = SUBJECT_PREFIX_RE.sub("", s)
        s = re.sub(r"^\s*\[[^\]]{1,40}\]\s*", "", s)  # [list-tag]
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# MIME structure
# ---------------------------------------------------------------------------


def walk_with_paths(msg: Message, prefix: str = "") -> Iterator[Tuple[str, Message, List[Message]]]:
    """Yield (IMAP-style part path, part, ancestors). Root multipart has path ''."""

    def rec(part: Message, path: str, ancestors: List[Message]) -> Iterator[Tuple[str, Message, List[Message]]]:
        yield path, part, ancestors
        if part.is_multipart():
            for i, sub in enumerate(part.get_payload() or [], start=1):  # type: ignore[arg-type]
                if isinstance(sub, Message):
                    child = f"{path}.{i}" if path else str(i)
                    yield from rec(sub, child, ancestors + [part])

    yield from rec(msg, prefix, [])


def part_bytes(part: Message) -> bytes:
    try:
        payload = part.get_payload(decode=True)
    except Exception:  # noqa: BLE001
        payload = None
    if isinstance(payload, bytes):
        return payload
    raw = part.get_payload()
    return raw.encode("utf-8", "replace") if isinstance(raw, str) else b""


def part_text(part: Message, warnings: List[str]) -> str:
    """Decode a text part, tolerating wrong/unknown charsets (fallback chain documented in docs/domain/mime.md)."""
    data = part_bytes(part)
    declared = (part.get_content_charset() or "us-ascii").lower()
    for charset in (declared, "utf-8", "windows-1256", "latin-1"):
        try:
            text = data.decode(charset)
        except (LookupError, UnicodeDecodeError):
            if charset == declared:
                warnings.append(f"charset {declared!r} failed to decode part; used fallback")
            continue
        return text
    return data.decode("utf-8", "replace")


def filename_of(part: Message) -> Optional[str]:
    try:
        name = part.get_filename()
    except Exception:  # noqa: BLE001
        name = None
    if not name:
        name = part.get_param("name") if hasattr(part, "get_param") else None
        if isinstance(name, tuple):  # RFC 2231 tuple from compat32 parts
            name = email.utils.collapse_rfc2231_value(name)
    if name:
        # Outlook-style RFC 2047 inside parameters (non-standard but common)
        if "=?" in name:
            try:
                from email.header import decode_header, make_header

                name = str(make_header(decode_header(name)))
            except Exception:  # noqa: BLE001
                pass
        return str(name)
    return None


def disposition_of(part: Message) -> Optional[str]:
    value = part.get("Content-Disposition")
    if not value:
        return None
    return str(value).split(";", 1)[0].strip().lower() or None


def content_id_of(part: Message) -> Optional[str]:
    cid = part.get("Content-ID")
    if not cid:
        return None
    return str(cid).strip().strip("<>").strip() or None


# ---------------------------------------------------------------------------
# HTML risk analysis (oracle for sanitizer tests — NOT a sanitizer)
# ---------------------------------------------------------------------------

URL_ATTRS = {"href", "src", "action", "formaction", "background", "poster", "xlink:href", "data", "lowsrc", "dynsrc", "srcset"}
REMOTE_RE = re.compile(r"^\s*(?:https?:)?//", re.IGNORECASE)
CSS_URL_RE = re.compile(r"url\(\s*['\"]?\s*((?:https?:)?//[^'\")\s]+)", re.IGNORECASE)
CSS_DANGER_RE = re.compile(r"expression\s*\(|javascript\s*:|behavior\s*:|-moz-binding", re.IGNORECASE)


class _HtmlRisk(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.dangerous: Dict[str, int] = {}
        self.remote: List[str] = []
        self.tracking_pixels = 0
        self.links: List[Tuple[str, str]] = []
        self._in_style = False
        self._link_href: Optional[str] = None
        self._link_text: List[str] = []

    def _flag(self, kind: str) -> None:
        self.dangerous[kind] = self.dangerous.get(kind, 0) + 1

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            self._flag("script")
        elif tag in ("iframe", "frame", "frameset"):
            self._flag("iframe")
        elif tag in ("object", "embed", "applet"):
            self._flag("object_embed")
        elif tag == "form" or tag in ("input", "button", "textarea", "select"):
            self._flag("form")
        elif tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            self._flag("meta_refresh")
        elif tag == "base":
            self._flag("base_tag")
        elif tag == "link" and "stylesheet" in a.get("rel", "").lower() and REMOTE_RE.match(a.get("href", "")):
            self.remote.append(a["href"])
        elif tag == "style":
            self._in_style = True
        elif tag == "svg":
            self._flag("svg")
        for name, value in a.items():
            if name.startswith("on"):
                self._flag("event_handler")
            if name == "srcdoc":
                self._flag("srcdoc")
            if name in URL_ATTRS or name.endswith(":href"):
                v = re.sub(r"[\x00-\x20]", "", value).lower()
                if v.startswith(("javascript:", "vbscript:")):
                    self._flag("javascript_url")
                elif v.startswith("data:text/html"):
                    self._flag("data_html_url")
                if name in ("src", "background", "poster", "srcset", "lowsrc", "dynsrc") and REMOTE_RE.match(value):
                    self.remote.append(value.strip())
            if name == "style":
                self._css(value)
        if tag == "img" and REMOTE_RE.match(a.get("src", "")):
            w, h = a.get("width", "").strip(), a.get("height", "").strip()
            style = a.get("style", "").replace(" ", "").lower()
            if (w in ("0", "1") and h in ("0", "1")) or ("width:1px" in style and "height:1px" in style):
                self.tracking_pixels += 1
        if tag == "a":
            self._link_href = a.get("href", "")
            self._link_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style":
            self._in_style = False
        if tag == "a" and self._link_href is not None:
            self.links.append((self._link_href, "".join(self._link_text).strip()))
            self._link_href = None

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._css(data)
        if self._link_href is not None:
            self._link_text.append(data)

    def _css(self, css: str) -> None:
        if CSS_DANGER_RE.search(css):
            self._flag("css_expression")
        self.remote.extend(CSS_URL_RE.findall(css))
        if re.search(r"@import", css, re.IGNORECASE):
            self._flag("css_import")


def html_findings(html: str) -> Dict[str, Any]:
    parser = _HtmlRisk()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001
        pass
    mismatched = []
    for href, text in parser.links:
        host = _host(href)
        shown = _host(text) if re.match(r"^\s*(https?://|www\.)", text, re.IGNORECASE) else None
        if host and shown and host != shown:
            mismatched.append({"href_host": host, "text_host": shown})
    return {
        "dangerous": dict(sorted(parser.dangerous.items())),
        "remote_resources": len(parser.remote),
        "tracking_pixels": parser.tracking_pixels,
        "mismatched_links": mismatched,
    }


def _host(url: str) -> Optional[str]:
    m = re.match(r"^\s*(?:[a-z][a-z0-9+.-]*:)?//([^/:?#\s]+)", url, re.IGNORECASE)
    if not m and url.lower().startswith("www."):
        m = re.match(r"^([^/:?#\s]+)", url)
    return m.group(1).lower() if m else None


# ---------------------------------------------------------------------------
# Attachment filename safety
# ---------------------------------------------------------------------------

BIDI_CONTROLS = {"\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069", "\u200e", "\u200f"}
WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}
EXECUTABLE_EXT = {
    "exe", "bat", "cmd", "com", "scr", "pif", "msi", "msp", "js", "jse", "vbs", "vbe", "wsf", "wsh",
    "ps1", "hta", "cpl", "jar", "lnk", "reg", "iso", "img", "dmg", "app", "apk", "sh", "docm", "xlsm",
}


def filename_warnings(name: str) -> List[str]:
    out = []
    if any(ch in BIDI_CONTROLS for ch in name):
        out.append("bidi_control_chars")
    if "/" in name or "\\" in name or name.startswith("..") or "/.." in name or "\\.." in name:
        out.append("path_traversal")
    if any(unicodedata.category(ch) == "Cc" for ch in name):
        out.append("control_chars")
    visible = "".join(ch for ch in name if ch not in BIDI_CONTROLS)
    base = re.split(r"[\\/]", visible)[-1]
    stem = base.split(".", 1)[0].strip().lower()
    if stem in WINDOWS_RESERVED:
        out.append("windows_reserved_name")
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
    if ext in EXECUTABLE_EXT:
        out.append("executable_extension")
    return out


# ---------------------------------------------------------------------------
# Summary (the conformance "answer key")
# ---------------------------------------------------------------------------


def _classify(msg: EmailMessage) -> Dict[str, Any]:
    warnings: List[str] = []
    parts: List[Dict[str, Any]] = []
    attachments: List[Dict[str, Any]] = []
    inline: List[Dict[str, Any]] = []
    attached_messages: List[Dict[str, Any]] = []
    calendar: Optional[Dict[str, Any]] = None
    text_bodies: List[Tuple[str, Message]] = []
    html_bodies: List[Tuple[str, Message]] = []
    referenced_cids: set = set()

    for path, part, ancestors in walk_with_paths(msg):
        ctype = part.get_content_type()
        if ancestors and any(a.get_content_type() == "message/rfc822" for a in ancestors):
            continue  # parts of an attached message belong to that message, not this one
        if part.is_multipart() and ctype != "message/rfc822":
            parts.append({"path": path or "root", "content_type": ctype})
            continue
        disp = disposition_of(part)
        fname = filename_of(part)
        cid = content_id_of(part)
        parent = ancestors[-1].get_content_type() if ancestors else None
        info = {
            "path": path or "1",
            "content_type": ctype,
            "charset": part.get_content_charset(),
            "transfer_encoding": (part.get("Content-Transfer-Encoding") or "7bit").strip().lower(),
            "disposition": disp,
            "filename": fname,
            "content_id": cid,
            "size": len(part_bytes(part)) if ctype != "message/rfc822" else 0,
        }
        parts.append(info)

        if ctype == "message/rfc822":
            inner = part.get_payload()
            inner_msg = inner[0] if isinstance(inner, list) and inner else None
            attached_messages.append(
                {"subject": header_text(inner_msg, "Subject") if inner_msg is not None else None, "filename": fname}
            )
            attachments.append({"filename": fname, "content_type": ctype, "size": len(inner_msg.as_bytes()) if inner_msg is not None else 0})
            continue
        if ctype == "text/calendar":
            body = part_text(part, warnings)
            m = re.search(r"^METHOD:(\S+)", body, re.MULTILINE)
            s = re.search(r"^SUMMARY[^:]*:(.+)$", body, re.MULTILINE)
            calendar = {
                "method": (part.get_param("method") or (m.group(1) if m else None) or "").upper() or None,
                "summary": s.group(1).strip() if s else None,
            }
            if disp == "attachment":
                attachments.append({"filename": fname, "content_type": ctype, "size": info["size"]})
            continue

        is_body_type = ctype in ("text/plain", "text/html")
        if disp == "attachment" or (fname and not (is_body_type and disp == "inline")):
            if cid and parent == "multipart/related" and disp != "attachment":
                inline.append({"content_id": cid, "content_type": ctype})
            else:
                attachments.append({"filename": fname, "content_type": ctype, "size": info["size"]})
                if fname:
                    for w in filename_warnings(fname):
                        warnings.append(f"attachment filename: {w}")
            continue
        if cid and ctype.startswith("image/"):
            inline.append({"content_id": cid, "content_type": ctype})
            continue
        if ctype == "text/plain":
            text_bodies.append((path, part))
        elif ctype == "text/html":
            html_bodies.append((path, part))
        else:
            attachments.append({"filename": fname, "content_type": ctype, "size": info["size"]})

    text = part_text(text_bodies[0][1], warnings) if text_bodies else None
    html = part_text(html_bodies[0][1], warnings) if html_bodies else None
    if html:
        referenced_cids = set(re.findall(r"cid:([^\"'\s>)]+)", html, re.IGNORECASE))
        known = {p["content_id"] for p in inline}
        for missing in sorted(referenced_cids - known):
            warnings.append(f"html references missing inline part cid:{missing}")
    preferred = "text/html" if html else ("text/plain" if text is not None else None)
    return {
        "parts": parts,
        "attachments": attachments,
        "inline_parts": inline,
        "attached_messages": attached_messages,
        "calendar": calendar,
        "text": text,
        "html": html,
        "preferred": preferred,
        "warnings": warnings,
    }


def summarize(msg: EmailMessage, raw: Optional[bytes] = None) -> Dict[str, Any]:
    """Client-facing interpretation of a message. Stable keys; used by tests and inspect_eml."""
    c = _classify(msg)
    defects = sorted({type(d).__name__ for _, part, _ in walk_with_paths(msg) for d in getattr(part, "defects", [])})
    subject = header_text(msg, "Subject")
    summary: Dict[str, Any] = {
        "subject": subject,
        "normalized_subject": normalize_subject(subject),
        "from": addresses(msg, "From"),
        "to": addresses(msg, "To"),
        "cc": addresses(msg, "Cc"),
        "reply_to": addresses(msg, "Reply-To"),
        "date": iso_date(msg),
        "message_id": (message_ids(header_text(msg, "Message-ID")) or [None])[0],
        "in_reply_to": (message_ids(header_text(msg, "In-Reply-To")) or [None])[0],
        "references": message_ids(header_text(msg, "References")),
        "body": {
            "preferred": c["preferred"],
            "text": c["text"],
            "html": c["html"],
        },
        "parts": c["parts"],
        "attachments": c["attachments"],
        "inline_parts": c["inline_parts"],
        "attached_messages": c["attached_messages"],
        "calendar": c["calendar"],
        "html_findings": html_findings(c["html"]) if c["html"] else None,
        "defects": defects,
        "warnings": c["warnings"],
    }
    if raw is not None:
        summary["line_endings"] = line_endings(raw)
        summary["size"] = len(raw)
    return summary


# ---------------------------------------------------------------------------
# IMAP modified UTF-7 (RFC 3501 §5.1.3) — mailbox names on the wire
# ---------------------------------------------------------------------------


def imap_utf7_encode(name: str) -> str:
    import base64

    out: List[str] = []
    buf: List[str] = []

    def flush() -> None:
        if buf:
            b = "".join(buf).encode("utf-16-be")
            out.append("&" + base64.b64encode(b).decode("ascii").rstrip("=").replace("/", ",") + "-")
            buf.clear()

    for ch in name:
        if 0x20 <= ord(ch) <= 0x7E:
            flush()
            out.append("&-" if ch == "&" else ch)
        else:
            buf.append(ch)
    flush()
    return "".join(out)


def imap_utf7_decode(name: str) -> str:
    import base64

    def repl(m: "re.Match[str]") -> str:
        body = m.group(1)
        if body == "":
            return "&"
        b64 = body.replace(",", "/")
        b64 += "=" * (-len(b64) % 4)
        return base64.b64decode(b64).decode("utf-16-be")

    return re.sub(r"&([A-Za-z0-9+,]*)-", repl, name)
