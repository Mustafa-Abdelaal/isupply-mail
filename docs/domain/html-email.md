# Rendering HTML email safely

HTML email is attacker-controlled content displayed inside our app. The goal is **useful fidelity with
zero active content**. Security wins over fidelity whenever they conflict.

## Pipeline (every platform)

1. **Decode** the HTML part with its charset (see [mime.md](mime.md)).
2. **Sanitize** with an **allowlist** sanitizer: a maintained library, never a regex.
   - Remove `script`, `iframe`/`frame`, `object`/`embed`/`applet`, `form`/inputs, `base`,
     `meta http-equiv`, `link`, `svg`/`math` (or a strictly sanitized subset), and every `on*` attribute.
   - URLs: allow `https:`, `http:` and `mailto:` in links, and `cid:` plus `data:image/*` in images. Drop
     `javascript:`, `vbscript:`, `data:text/html` and anything unknown. Normalize case, whitespace and
     entities **before** checking, because `jav&#x09;ascript:` is a classic bypass.
   - CSS: keep presentational properties. Drop `expression()`, `behavior`, `-moz-binding`, `@import`
     and `url()` pointing to remote hosts (or rewrite them through the remote-content gate). Drop
     `position: fixed` and absolute overlays that could spoof our UI.
   - Watch for **mutation XSS**: sanitize the parsed DOM and serialize once. Don't sanitize, re-parse
     and insert.
3. **Rewrite**: `cid:` references go to local blob URLs of this message's own parts. Remote images are
   replaced by placeholders until allowed. Links get `target=_blank rel="noopener noreferrer"`, and our
   click handler opens them in the system browser.
4. **Render in a sandbox**:
   - **Web**: `<iframe sandbox>` with **no** `allow-scripts` and no `allow-same-origin`, plus a CSP such
     as `default-src 'none'; img-src cid: data: blob: [https: only after opt-in]; style-src 'unsafe-inline'`.
   - **Desktop and mobile**: a webview with JavaScript **disabled**, no file access, and navigation
     intercepted (every navigation becomes "open externally").
5. **Wrap** the content in our container with `dir="auto"`, a dark-mode adaptation (invert carefully,
   or offer an "original colors" toggle), responsive scaling for fixed-width (600 px) newsletters, and
   quoted-text collapsing.

## Remote content and privacy (R-12)

- Block remote images, fonts and CSS by default. Tracking pixels (1×1 images, fixture 012) reveal when
  and where (IP address) a message was opened.
- Show a banner: "Images from this sender were blocked to protect your privacy. [Load once] [Always
  for sender]". The per-sender allowlist is stored locally (or synced).
- When loading is allowed, prefer a **proxy** (if we have a backend) to hide user IPs and strip
  tracking parameters.
- Never auto-fetch link previews of URLs in messages (SSRF and tracking risk).

## Phishing signals (R-13)

- Show the real link target on hover or long-press, and warn when the link text shows a different
  host than the href (fixture 011). Check against the Public Suffix List.
- Show an external-sender banner when `From` isn't `@isupply.com.eg` but the display name, signature or
  reply-to imitates an internal sender.
- Flag lookalike domains (`isupp1y.com`, IDN homographs) and `Reply-To` that differs from `From` on
  first contact.

## Test oracles

| Fixture | Must hold after sanitization |
|---|---|
| `011-html-xss-payloads.eml` | none of `html_dangerous_at_least` remain; nothing executes; the link-mismatch warning is shown |
| `012-remote-images-tracking-pixel.eml` | 0 remote requests before opt-in; the banner is shown |
| `005-inline-image-cid.eml`, `007-outlook-nested-structure.eml` | inline images render from cid: |
| `002-multipart-alternative-qp.eml` | formatting (bold, links) preserved |

Run `scripts/email/emaillib.py::html_findings` on the **sanitizer output** in tests: the `dangerous`
dict must be empty, and `remote_resources` must be 0 unless remote content is allowed.
