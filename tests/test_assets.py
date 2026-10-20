"""Offline tests for the pure helpers (no Home Assistant needed): python tests/test_assets.py"""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("assets", ROOT / "custom_components" / "custom_branding" / "assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)

LOGIN = (ROOT / "tests" / "fixtures" / "login.html").read_bytes()
INDEX = (ROOT / "tests" / "fixtures" / "index.html").read_bytes()

FULL = {"name": "My Home", "logo": "/local/b/logo.png", "icon": "/local/b/icon.png", "icon_maskable": "/local/b/m.png",
        "background_color": "#0b1220", "accent_color": "#38bdf8", "loading_text": "Hold on"}


def test_normalize_rejects_bad_values():
    s = assets.normalize({"name": "X" * 200, "logo": "javascript:alert(1)", "accent_color": "red;} body{display:none", "icon": "/ok/icon.png"})
    assert len(s["name"]) == 60
    assert s["logo"] is None and s["icon"] == "/ok/icon.png"
    assert s["accent_color"] == assets.DEFAULTS["accent_color"]


def test_login_page_is_branded():
    s = assets.normalize(FULL)
    out = assets.rewrite_html(LOGIN, s)
    assert assets.MARK in out and b"/custom_branding/branding.css?v=" + s["version"].encode() in out
    assert b"<title>My Home</title>" in out
    assert b'src="/local/b/logo.png" alt="My Home"' in out
    assert b'alt="Home Assistant"' not in out
    assert b'content="#0b1220"' in out or b"theme-color" not in out


def test_index_page_is_branded_and_manifest_swapped():
    s = assets.normalize(FULL)
    out = assets.rewrite_html(INDEX, s)
    assert b'href="/custom_branding/manifest.json?v=' in out and b'href="/manifest.json"' not in out
    assert b'<meta name="apple-mobile-web-app-title" content="My Home">' in out
    assert b'href="/local/b/icon.png"' in out
    assert b'name="theme-color" content="#0b1220"' in out


def test_idempotent_and_ignores_other_html():
    s = assets.normalize(FULL)
    once = assets.rewrite_html(INDEX, s)
    assert assets.rewrite_html(once, s) == once
    other = b"<html><head></head><body>hello</body></html>"
    assert assets.rewrite_html(other, s) == other


def test_only_what_is_configured_changes():
    s = assets.normalize({"accent_color": "#ff0000"})  # nothing but colors
    out = assets.rewrite_html(INDEX, s)
    assert b"<title>Home Assistant</title>" in out and b'href="/manifest.json"' in out
    assert b"/custom_branding/branding.css" in out


def test_css_js_manifest():
    s = assets.normalize(FULL)
    css = assets.build_css(s)
    assert "#38bdf8" in css and "/local/b/logo.png" in css and ".ohf-logo" in css and "var(--" not in css.split("{")[0]
    js = assets.build_js(s)
    assert json.loads(js.split("var C = ")[1].split(";\n")[0])["name"] == "My Home"
    man = assets.build_manifest(s)
    assert man["name"] == "My Home" and {i["purpose"] for i in man["icons"]} == {"any", "maskable"}
    assert "icons" not in assets.build_manifest(assets.normalize({}))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
