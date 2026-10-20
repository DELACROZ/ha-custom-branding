"""Custom Branding: your name, logo and colors on Home Assistant's login page, loading screen and PWA."""
from __future__ import annotations

import json
import logging

from aiohttp import web
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .assets import BASE_URL, DEFAULTS, build_css, build_js, build_manifest, normalize, rewrite_html

DOMAIN = "custom_branding"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("name"): cv.string,
                vol.Optional("short_name"): cv.string,
                vol.Optional("logo"): cv.string,
                vol.Optional("icon"): cv.string,
                vol.Optional("icon_maskable"): cv.string,
                vol.Optional("background_color", default=DEFAULTS["background_color"]): cv.string,
                vol.Optional("accent_color", default=DEFAULTS["accent_color"]): cv.string,
                vol.Optional("text_color", default=DEFAULTS["text_color"]): cv.string,
                vol.Optional("loading_text", default=DEFAULTS["loading_text"]): cv.string,
                vol.Optional("hide_ha_logo", default=True): cv.boolean,
                vol.Optional("hide_open_home_foundation", default=True): cv.boolean,
                vol.Optional("sidebar_title", default=True): cv.boolean,
                vol.Optional("tab_title", default=True): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_CACHE = {"Cache-Control": "public, max-age=86400"}  # URLs carry ?v=<hash of the settings>


class _AssetView(HomeAssistantView):
    """Serves one generated asset. Public on purpose: the login page needs it before anyone is signed in."""

    requires_auth = False
    cors_allowed = False

    def __init__(self, url: str, name: str, body: str, content_type: str) -> None:
        self.url = url
        self.name = name
        self._body = body
        self._type = content_type

    async def get(self, request: web.Request) -> web.Response:
        return web.Response(text=self._body, content_type=self._type, headers=_CACHE)


def _wrap(hass: HomeAssistant, orig, settings):
    """Wrap a route handler so its HTML response gets the branding; fall back to the original on any problem."""
    cache: dict[str, bytes] = {}  # branded static pages (they only change when Home Assistant itself is updated)

    async def handler(request, *args, **kwargs):
        resp = await orig(request, *args, **kwargs)
        try:
            if request.method != "GET":
                return resp
            if isinstance(resp, web.FileResponse):
                path = getattr(resp, "_path", None)  # FileResponse has no content type until it is prepared
                if path is None or not str(path).lower().endswith(".html"):
                    return resp
                key = str(path)
                if key not in cache:
                    body = await hass.async_add_executor_job(path.read_bytes)  # never block the event loop
                    cache[key] = rewrite_html(body, settings)
                    if cache[key] == body:
                        return resp
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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Custom Branding from YAML."""
    if DOMAIN not in config:
        return True
    settings = normalize(config[DOMAIN])

    hass.http.register_view(_AssetView(f"{BASE_URL}/branding.css", "custom_branding:css", build_css(settings), "text/css"))
    hass.http.register_view(_AssetView(f"{BASE_URL}/branding.js", "custom_branding:js", build_js(settings), "text/javascript"))
    hass.http.register_view(
        _AssetView(f"{BASE_URL}/manifest.json", "custom_branding:manifest", json.dumps(build_manifest(settings)), "application/manifest+json")
    )

    # The server freezes its middleware list very early, so the existing routes are wrapped instead.
    found = {"index": False, "login": False}
    try:
        for res in hass.http.app.router.resources():
            if type(res).__name__ == "IndexView":  # main page; its route is created once and cached
                route = res._route
                route._handler = _wrap(hass, route._handler, settings)
                found["index"] = True
            elif getattr(res, "canonical", None) == "/auth/authorize":  # login page (a static file route)
                for route in res:
                    route._handler = _wrap(hass, route._handler, settings)
                found["login"] = True
    except Exception:
        _LOGGER.exception("custom_branding: could not hook into the web server")
    if not all(found.values()):
        _LOGGER.warning("custom_branding: some pages could not be branded (main page: %s, login page: %s)", found["index"], found["login"])
    else:
        _LOGGER.info("custom_branding active (main page and login page)")
    return True
