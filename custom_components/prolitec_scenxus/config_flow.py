"""Config flow for Prolitec ScenXus."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ScenXusApi, ScenXusApiError, ScenXusAuthError
from .const import CONF_DSN, CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
        vol.Required(CONF_DSN): str,
    }
)

_REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class ScenXusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the ScenXus config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect email/password/DSN, verify, and create the entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            dsn = user_input[CONF_DSN].strip().upper()
            await self.async_set_unique_id(dsn)
            self._abort_if_unique_id_configured()

            session = async_create_clientsession(self.hass)
            api = ScenXusApi(
                session,
                email=user_input[CONF_EMAIL].strip(),
                password=user_input[CONF_PASSWORD],
            )
            try:
                await api.async_login()
                device = await api.async_get_device(dsn)
                if not device or not device.get("dsn"):
                    errors["base"] = "unknown_device"
            except ScenXusAuthError:
                errors["base"] = "invalid_auth"
            except ScenXusApiError:
                errors["base"] = "cannot_connect"
            else:
                if not errors:
                    name = device.get("product_name") or f"ScenXus {dsn}"
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_EMAIL: user_input[CONF_EMAIL].strip(),
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_DSN: dsn,
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the stored password stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt for a new password and validate it."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = ScenXusApi(
                session,
                email=user_input[CONF_EMAIL].strip(),
                password=user_input[CONF_PASSWORD],
            )
            try:
                await api.async_login()
            except ScenXusAuthError:
                errors["base"] = "invalid_auth"
            except ScenXusApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                _REAUTH_SCHEMA, {CONF_EMAIL: reauth_entry.data.get(CONF_EMAIL)}
            ),
            errors=errors,
        )
