"""Pure helpers for Custom Branding (no Home Assistant imports, so they can be tested anywhere).

Builds the CSS, JavaScript and PWA manifest from the user's settings, and rewrites the HTML of the
login page and of the main page so they carry the custom name, logo and colors.
"""
from __future__ import annotations

import hashlib
import html
import json
import re

MARK = b"<!--custom_branding-->"
BASE_URL = "/custom_branding"

_COLOR = re.compile(r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20}|(rgb|hsl)a?\([0-9.,%\s/]+\))$")
_PATH = re.compile(r"^[\w./%:@+~=&?\-]+$")

DEFAULTS = {
    "name": None,
    "short_name": None,
    "logo": None,
    "icon": None,
    "icon_maskable": None,
    "background_color": "#04060a",
    "accent_color": "#00d9ff",
    "text_color": "#eef7ff",
    "loading_text": "Loading",
    "welcome_text": None,
    "hide_ha_logo": True,
    "hide_open_home_foundation": True,
    "sidebar_title": True,
    "tab_title": True,
}


ALLOWED_KEYS = tuple(DEFAULTS)
MAX_UPLOAD = 6 * 1024 * 1024


def clean_settings(raw: dict | None, defaults: dict = DEFAULTS) -> dict:
    """Keep only known keys with sane types (used before storing settings coming from the UI or YAML)."""
    out = {}
    for key in ALLOWED_KEYS:
        if raw is None or key not in raw or raw[key] in (None, ""):
            continue
        value = raw[key]
        if isinstance(defaults.get(key), bool):
            out[key] = bool(value)
        else:
            out[key] = str(value).strip()
    return out


def detect_image(data: bytes) -> str | None:
    """Return 'png', 'jpg' or 'webp' from the file signature (never trust the file name)."""
    if data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
        return "png"
    if data[:3] == bytes([0xFF, 0xD8, 0xFF]):
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def normalize(cfg: dict | None) -> dict:
    """Return clean settings (invalid colors/paths fall back to defaults) plus a short `version` hash."""
    s = dict(DEFAULTS)
    for key, value in (cfg or {}).items():
        if key in s and value is not None:
            s[key] = value
    for key in ("background_color", "accent_color", "text_color"):
        if not isinstance(s[key], str) or not _COLOR.match(s[key].strip()):
            s[key] = DEFAULTS[key]
        s[key] = s[key].strip()
    for key in ("logo", "icon", "icon_maskable"):
        v = s[key]
        if v is not None and (not isinstance(v, str) or not _PATH.match(v.strip())):
            s[key] = None
        elif v is not None:
            s[key] = v.strip()
    for key in ("name", "short_name", "loading_text", "welcome_text"):
        if s[key] is not None:
            s[key] = str(s[key]).strip()[:60] or None
    if s["name"] and not s["short_name"]:
        s["short_name"] = s["name"][:20]
    s["version"] = hashlib.sha1(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()[:8]
    return s


# --------------------------------------------------------------------------- CSS
_CSS = """/* Custom Branding: loading screen and login page */
body:has(ha-authorize),body:has(#ha-launch-screen){background:radial-gradient(75vw 60vh at 50% 18%,color-mix(in srgb,__AC__ 20%,transparent),transparent 70%),radial-gradient(60vw 50vh at 85% 95%,color-mix(in srgb,__AC__ 10%,transparent),transparent 70%),__BG__ !important}
html:has(ha-authorize),html:has(#ha-launch-screen){background:__BG__ !important}
ha-authorize{--primary-color:__AC__;--mdc-theme-primary:__AC__;--mdc-text-field-ink-color:__TX__;--primary-text-color:__TX__;--secondary-text-color:color-mix(in srgb,__TX__ 62%,transparent);--card-background-color:color-mix(in srgb,__BG__ 86%,#fff 6%);--ha-card-background:color-mix(in srgb,__BG__ 86%,#fff 6%);--ha-card-border-color:color-mix(in srgb,__AC__ 35%,transparent);--divider-color:color-mix(in srgb,__AC__ 25%,transparent);--mdc-theme-on-primary:__BG__;--ha-card-box-shadow:0 0 30px color-mix(in srgb,__AC__ 14%,transparent)}
#ha-launch-screen{background:radial-gradient(60vw 46vh at 50% 44%,color-mix(in srgb,__AC__ 18%,transparent),transparent 72%),__BG__ !important}
#cb-splash{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:38px}
#cb-splash img{width:min(64vw,440px);height:auto;filter:drop-shadow(0 0 20px color-mix(in srgb,__AC__ 55%,transparent));animation:cbPulse 2.6s ease-in-out infinite}
#cb-splash .cb-ring{width:48px;height:48px;border-radius:50%;border:3px solid color-mix(in srgb,__AC__ 16%,transparent);border-top-color:__AC__;border-right-color:__AC__;box-shadow:0 0 18px color-mix(in srgb,__AC__ 50%,transparent);animation:cbSpin 1s linear infinite}
#cb-splash small{font:600 13px/1 Roboto,Arial,sans-serif;letter-spacing:.32em;text-transform:uppercase;color:__AC__;opacity:.85}
@keyframes cbSpin{to{transform:rotate(360deg)}}
@keyframes cbPulse{50%{opacity:.82;transform:scale(1.025)}}
"""


def build_css(s: dict) -> str:
    css = _CSS.replace("__BG__", s["background_color"]).replace("__AC__", s["accent_color"]).replace("__TX__", s["text_color"])
    extra = []
    if s["hide_ha_logo"] and s["logo"]:
        extra.append("#ha-launch-screen .ha-lockup{display:none !important}")
    if s["hide_open_home_foundation"]:
        extra.append("#ha-launch-screen .ohf-logo,#ha-launch-screen-info-box{display:none !important}")
    if s["logo"]:
        extra.append(
            ".content .header img{content:url('%s');width:min(72vw,380px) !important;height:auto !important;max-width:100%%;"
            "filter:drop-shadow(0 0 20px color-mix(in srgb,%s 55%%,transparent))}" % (s["logo"], s["accent_color"])
        )
        extra.append(".content .header{padding-top:6vh}")
    return css + "\n".join(extra) + "\n"


# --------------------------------------------------------------------------- JS
_JS = """/* Custom Branding: loading screen content, sidebar title and tab title */
(function () {
  var C = __CFG__;
  function splash() {
    var screen = document.getElementById("ha-launch-screen");
    if (!screen || document.getElementById("cb-splash") || (!C.logo && !C.loading_text)) return;
    var box = document.createElement("div");
    box.id = "cb-splash";
    if (C.logo) { var img = document.createElement("img"); img.src = C.logo; img.alt = C.name || ""; box.appendChild(img); }
    var ring = document.createElement("div"); ring.className = "cb-ring"; box.appendChild(ring);
    if (C.loading_text) { var t = document.createElement("small"); t.textContent = C.loading_text; box.appendChild(t); }
    screen.appendChild(box);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", splash); else splash();
  if (C.name && C.sidebar_title) {
    var side = function () {
      try {
        var ha = document.querySelector("home-assistant");
        var main = ha && ha.shadowRoot && ha.shadowRoot.querySelector("home-assistant-main");
        var sb = main && main.shadowRoot && main.shadowRoot.querySelector("ha-sidebar");
        var t = sb && sb.shadowRoot && sb.shadowRoot.querySelector(".title");
        if (t && t.textContent.trim() !== C.name) t.textContent = C.name;
      } catch (e) {}
    };
    setInterval(side, 1000); side();
  }
  if (C.name && C.tab_title) {
    var title = function () { if (/Home Assistant/.test(document.title)) document.title = document.title.replace(/Home Assistant/g, C.name); };
    title();
    var node = document.querySelector("title");
    if (node) new MutationObserver(title).observe(node, { childList: true, characterData: true, subtree: true });
    else setInterval(title, 1500);
  }
  if (C.welcome_text) {
    var KNOWN_WELCOME = ["Welcome Home!", "Bem-vindo ao lar!"];
    var fixWelcome = function (node) {
      if (node.nodeType === 3) {
        if (KNOWN_WELCOME.indexOf(node.nodeValue.trim()) !== -1) node.nodeValue = C.welcome_text;
        return;
      }
      var kids = node.childNodes || [];
      for (var i = 0; i < kids.length; i++) fixWelcome(kids[i]);
      if (node.shadowRoot) fixWelcome(node.shadowRoot);
    };
    var run = function () { try { fixWelcome(document.body); } catch (e) {} };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
    setInterval(run, 500);
  }
})();
"""


def build_js(s: dict) -> str:
    cfg = {k: s[k] for k in ("name", "logo", "loading_text", "welcome_text", "sidebar_title", "tab_title")}
    return _JS.replace("__CFG__", json.dumps(cfg, ensure_ascii=False))


# --------------------------------------------------------------------------- manifest
def build_manifest(s: dict) -> dict:
    name = s["name"] or "Home Assistant"
    icons = []
    if s["icon"]:
        icons.append({"src": s["icon"], "sizes": "192x192", "type": "image/png", "purpose": "any"})
        icons.append({"src": s["icon"], "sizes": "512x512", "type": "image/png", "purpose": "any"})
    if s["icon_maskable"]:
        icons.append({"src": s["icon_maskable"], "sizes": "512x512", "type": "image/png", "purpose": "maskable"})
    man = {
        "id": "/",
        "name": name,
        "short_name": s["short_name"] or name[:20],
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": s["background_color"],
        "theme_color": s["background_color"],
        "lang": "en",
    }
    if icons:
        man["icons"] = icons
    return man


# --------------------------------------------------------------------------- HTML
def rewrite_html(body: bytes, s: dict) -> bytes:
    """Inject the branding into the login page and the main page. Anything else is returned unchanged."""
    if b"</head>" not in body or not (b"ha-launch-screen" in body or b"ha-authorize" in body):
        return body
    if MARK in body:
        return body
    v = s["version"]
    esc = lambda text: html.escape(text, quote=True).encode()  # noqa: E731
    subs: list[tuple[bytes, bytes]] = []
    if s["logo"]:
        subs.append((b'src="/static/icons/favicon-192x192.png" alt="Home Assistant"',
                     b'src="' + esc(s["logo"]) + b'" alt="' + esc(s["name"] or "") + b'"'))
    if s["name"]:
        subs += [
            (b"<title>Home Assistant</title>", b"<title>" + esc(s["name"]) + b"</title>"),
            (b'content="Home Assistant"', b'content="' + esc(s["name"]) + b'"'),
            (b'alt="Home Assistant"', b'alt="' + esc(s["name"]) + b'"'),
        ]
    if s["name"] or s["icon"]:
        subs.append((b'href="/manifest.json"', f'href="{BASE_URL}/manifest.json?v={v}"'.encode()))
    if s["icon"]:
        subs += [
            (b'href="/static/icons/favicon-apple-180x180.png"', b'href="' + esc(s["icon"]) + b'"'),
            (b'href="/static/icons/favicon.ico"', b'href="' + esc(s["icon"]) + b'"'),
        ]
    for old, new in subs:
        body = body.replace(old, new)
    body = re.sub(rb'(name="theme-color"\s+content=")[^"]*(")', b"\\g<1>" + s["background_color"].encode() + b"\\g<2>", body)
    tags = (
        MARK
        + f'<link rel="stylesheet" href="{BASE_URL}/branding.css?v={v}">'.encode()
        + f'<script defer src="{BASE_URL}/branding.js?v={v}"></script>'.encode()
    )
    return body.replace(b"</head>", tags + b"</head>", 1)
