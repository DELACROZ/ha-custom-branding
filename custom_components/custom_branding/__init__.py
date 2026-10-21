"""Custom Branding: your name, logo and colors on Home Assistant's login page, loading screen and PWA.

Version 2: configured from a "Branding" panel in the sidebar (upload images, pick colors, save). A `custom_branding:`
block in configuration.yaml (version 1.x) is still read once and imported.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from aiohttp import web
import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .assets import (
    BASE_URL,
    DEFAULTS,
    MAX_UPLOAD,
    build_css,
    build_js,
    build_manifest,
    clean_settings,
    detect_image,
    normalize,
    rewrite_html,
)

DOMAIN = "custom_branding"
PANEL_PATH = "custom-branding"
KINDS = ("logo", "icon", "icon_maskable")
_LOGGER = logging.getLogger(__name__)
_CACHE_SHORT = {"Cache-Control": "public, max-age=86400"}  # URLs carry ?v=<hash of the settings>
_EXT_TYPE = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("name"): cv.string,
                vol.Optional("short_name"): cv.string,
                vol.Optional("logo"): cv.string,
                vol.Optional("icon"): cv.string,
                vol.Optional("icon_maskable"): cv.string,
                vol.Optional("background_color"): cv.string,
                vol.Optional("accent_color"): cv.string,
                vol.Optional("text_color"): cv.string,
                vol.Optional("loading_text"): cv.string,
                vol.Optional("welcome_text"): cv.string,
                vol.Optional("footer_link"): cv.string,
                vol.Optional("footer_link_value"): cv.string,
                vol.Optional("hide_ha_logo"): cv.boolean,
                vol.Optional("hide_open_home_foundation"): cv.boolean,
                vol.Optional("sidebar_title"): cv.boolean,
                vol.Optional("tab_title"): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# --------------------------------------------------------------------------- state helpers
def _state(hass: HomeAssistant) -> dict:
    return hass.data.setdefault(DOMAIN, {"entry": None, "yaml": None, "hooks": []})


def _entry(hass: HomeAssistant) -> ConfigEntry | None:
    return _state(hass)["entry"]


def _settings(hass: HomeAssistant) -> dict:
    """Current effective settings (stored in the config entry; YAML only until it is imported)."""
    st = _state(hass)
    raw = dict(st["entry"].data) if st["entry"] else dict(st["yaml"] or {})
    return normalize(raw)


def _files_dir(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("custom_branding"))


def _find_file(folder: Path, kind: str) -> Path | None:
    for ext in _EXT_TYPE:
        candidate = folder / f"{kind}.{ext}"
        if candidate.is_file():
            return candidate
    return None


def _save_file(folder: Path, kind: str, ext: str, data: bytes) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for old in _EXT_TYPE:
        (folder / f"{kind}.{old}").unlink(missing_ok=True)
    (folder / f"{kind}.{ext}").write_bytes(data)


def _delete_files(folder: Path) -> None:
    for kind in KINDS:
        for ext in _EXT_TYPE:
            (folder / f"{kind}.{ext}").unlink(missing_ok=True)


# --------------------------------------------------------------------------- HTTP views
class _DynamicAsset(HomeAssistantView):
    """CSS / JS / manifest generated from the current settings. Public: the login page needs it before sign-in."""

    requires_auth = False
    cors_allowed = False

    def __init__(self, hass: HomeAssistant, url: str, name: str, builder, content_type: str) -> None:
        self.url = url
        self.name = name
        self._hass = hass
        self._builder = builder
        self._type = content_type

    async def get(self, request: web.Request) -> web.Response:
        return web.Response(text=self._builder(_settings(self._hass)), content_type=self._type, headers=_CACHE_SHORT)


class _PanelJs(HomeAssistantView):
    requires_auth = False
    cors_allowed = False
    url = f"{BASE_URL}/panel.js"
    name = "custom_branding:panel_js"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._text: str | None = None

    async def get(self, request: web.Request) -> web.Response:
        if self._text is None:
            path = Path(__file__).parent / "frontend" / "panel.js"
            self._text = await self._hass.async_add_executor_job(path.read_text, "utf-8")
        return web.Response(text=self._text, content_type="text/javascript", headers={"Cache-Control": "no-cache"})


class _Files(HomeAssistantView):
    """The images uploaded in the panel (public, versioned with ?v=<hash>)."""

    requires_auth = False
    cors_allowed = False
    url = BASE_URL + "/files/{kind}"
    name = "custom_branding:files"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request, kind: str) -> web.StreamResponse:
        if kind not in KINDS:
            return web.Response(status=404)
        path = await self._hass.async_add_executor_job(_find_file, _files_dir(self._hass), kind)
        if path is None:
            return web.Response(status=404)
        return web.FileResponse(path, headers={"Cache-Control": "public, max-age=31536000"})


class _Upload(HomeAssistantView):
    """Upload one image (admin only). The body is the raw image file."""

    requires_auth = True
    url = "/api/custom_branding/upload/{kind}"
    name = "api:custom_branding:upload"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def post(self, request: web.Request, kind: str) -> web.Response:
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            return self.json_message("Admin access required", 403)
        entry = _entry(self._hass)
        if kind not in KINDS or entry is None:
            return self.json_message("Unknown image kind or integration not set up", 400)
        if request.content_length and request.content_length > MAX_UPLOAD:
            return self.json_message("File too large (max 6 MB)", 413)
        data = await request.read()
        if len(data) > MAX_UPLOAD:
            return self.json_message("File too large (max 6 MB)", 413)
        ext = detect_image(data)
        if ext is None:
            return self.json_message("Use a PNG, JPEG or WebP image", 400)
        await self._hass.async_add_executor_job(_save_file, _files_dir(self._hass), kind, ext, data)
        url = f"{BASE_URL}/files/{kind}?v={hashlib.sha1(data).hexdigest()[:8]}"
        self._hass.config_entries.async_update_entry(entry, data={**entry.data, kind: url})
        return self.json({"url": url})


# --------------------------------------------------------------------------- websocket API (admin)
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get"})
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "Custom Branding is not set up")
        return
    connection.send_result(msg["id"], {"settings": dict(entry.data), "defaults": dict(DEFAULTS), "kinds": list(KINDS)})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/save", vol.Required("settings"): dict})
@callback
def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "Custom Branding is not set up")
        return
    clean = clean_settings(msg["settings"])
    hass.config_entries.async_update_entry(entry, data=clean)
    connection.send_result(msg["id"], {"settings": clean, "version": _settings(hass)["version"]})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/reset"})
@websocket_api.async_response
async def ws_reset(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "Custom Branding is not set up")
        return
    await hass.async_add_executor_job(_delete_files, _files_dir(hass))
    hass.config_entries.async_update_entry(entry, data={})
    connection.send_result(msg["id"], {"settings": {}})


# --------------------------------------------------------------------------- page hooks
def _wrap(hass: HomeAssistant, orig):
    """Wrap a route handler so its HTML response gets the branding; fall back to the original on any problem."""
    cache: dict[tuple[str, str], bytes] = {}  # branded static pages, per settings version

    async def handler(request, *args, **kwargs):
        resp = await orig(request, *args, **kwargs)
        try:
            if request.method != "GET":
                return resp
            settings = _settings(hass)
            if isinstance(resp, web.FileResponse):
                path = getattr(resp, "_path", None)  # FileResponse has no content type until it is prepared
                if path is None or not str(path).lower().endswith(".html"):
                    return resp
                key = (str(path), settings["version"])
                if key not in cache:
                    body = await hass.async_add_executor_job(path.read_bytes)  # never block the event loop
                    cache.clear()
                    cache[key] = rewrite_html(body, settings)
                return web.Response(body=cache[key], content_type="text/html", charset="utf-8", headers={"Cache-Control": "no-cache"})
            if "text/html" not in (getattr(resp, "content_type", "") or ""):
                return resp
            body = getattr(resp, "body", None)
            if isinstance(body, (bytes, bytearray)):
                new = rewrite_html(bytes(body), settings)
                if new != body:
                    resp.body = new
        except Exception:  # never break the original page
            _LOGGER.exception("custom_branding: could not brand the page, serving the original")
        return resp

    return handler


def _install_hooks(hass: HomeAssistant) -> None:
    """The server freezes its middleware list very early, so the existing routes are wrapped instead."""
    st = _state(hass)
    if st["hooks"]:
        return
    found = {"index": False, "login": False}
    try:
        for res in hass.http.app.router.resources():
            if type(res).__name__ == "IndexView":  # main page; its route is created once and cached
                routes, key = [res._route], "index"
            elif getattr(res, "canonical", None) == "/auth/authorize":  # login page (a static file route)
                routes, key = list(res), "login"
            else:
                continue
            for route in routes:
                orig = route._handler
                route._handler = _wrap(hass, orig)
                st["hooks"].append((route, orig))
            found[key] = True
    except Exception:
        _LOGGER.exception("custom_branding: could not hook into the web server")
    if not all(found.values()):
        _LOGGER.warning(
            "custom_branding: some pages could not be branded (main page: %s, login page: %s). "
            "This Home Assistant version may have changed; please open an issue with your version.",
            found["index"], found["login"],
        )
    else:
        _LOGGER.info("custom_branding active (main page and login page)")


# --------------------------------------------------------------------------- setup
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    st = _state(hass)
    st["yaml"] = config.get(DOMAIN)

    hass.http.register_view(_DynamicAsset(hass, f"{BASE_URL}/branding.css", "custom_branding:css", build_css, "text/css"))
    hass.http.register_view(_DynamicAsset(hass, f"{BASE_URL}/branding.js", "custom_branding:js", build_js, "text/javascript"))
    hass.http.register_view(
        _DynamicAsset(hass, f"{BASE_URL}/manifest.json", "custom_branding:manifest",
                      lambda s: json.dumps(build_manifest(s)), "application/manifest+json")
    )
    hass.http.register_view(_PanelJs(hass))
    hass.http.register_view(_Files(hass))
    hass.http.register_view(_Upload(hass))
    websocket_api.async_register_command(hass, ws_get)
    websocket_api.async_register_command(hass, ws_save)
    websocket_api.async_register_command(hass, ws_reset)

    # Version 1.x was configured in YAML: import it once into the UI settings.
    if st["yaml"] is not None and not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(st["yaml"]))
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _state(hass)["entry"] = entry
    _install_hooks(hass)
    try:
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_PATH,
            webcomponent_name="custom-branding-panel",
            sidebar_title="Branding",
            sidebar_icon="mdi:palette-outline",
            module_url=f"{BASE_URL}/panel.js",
            require_admin=True,
            config={},
        )
    except ValueError:  # already registered (reload)
        pass
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    st = _state(hass)
    for route, orig in st["hooks"]:
        route._handler = orig
    st["hooks"] = []
    st["entry"] = None
    frontend.async_remove_panel(hass, PANEL_PATH)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete the uploaded images when the integration is removed."""
    await hass.async_add_executor_job(_delete_files, _files_dir(hass))
