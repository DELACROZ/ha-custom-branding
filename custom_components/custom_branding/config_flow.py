"""Config flow for Custom Branding (UI setup; settings are edited in the "Branding" sidebar panel)."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries

from .assets import DEFAULTS, clean_settings

DOMAIN = "custom_branding"


class CustomBrandingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Single-instance config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="Custom Branding", data={})
        return self.async_show_form(step_id="user")

    async def async_step_import(self, import_data: dict[str, Any]):
        """Import the settings of an existing YAML block (versions 1.x)."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Custom Branding", data=clean_settings(import_data, DEFAULTS))
