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
    }
)


class ScenXusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the ScenXus config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._auth: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect email/password and sign in."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = ScenXusApi(
                session,
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
            )
            try:
                await api.async_login()
                self._devices = await api.async_get_devices()
            except ScenXusAuthError:
                errors["base"] = "invalid_auth"
            except ScenXusApiError:
                errors["base"] = "cannot_connect"
            else:
                self._auth = dict(user_input)
                if not self._devices:
                    return self.async_abort(reason="no_devices")
                if len(self._devices) == 1:
                    return await self._create_entry(self._devices[0].get("dsn"))
                return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the stored password stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt for a new password (and email) and validate it."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = ScenXusApi(
                session,
                email=user_input[CONF_EMAIL],
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
                _USER_SCHEMA, {CONF_EMAIL: reauth_entry.data.get(CONF_EMAIL)}
            ),
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a device when the account has more than one."""
        if user_input is not None:
            return await self._create_entry(user_input[CONF_DSN])

        choices = {
            d["dsn"]: f"{d.get('product_name', 'ScenXus')} ({d['dsn']})"
            for d in self._devices
            if d.get("dsn")
        }
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_DSN): vol.In(choices)}),
        )

    async def _create_entry(self, dsn: str) -> ConfigFlowResult:
        await self.async_set_unique_id(str(dsn).upper())
        self._abort_if_unique_id_configured()
        name = next(
            (
                d.get("product_name")
                for d in self._devices
                if d.get("dsn") == dsn and d.get("product_name")
            ),
            f"ScenXus {dsn}",
        )
        return self.async_create_entry(
            title=name, data={**self._auth, CONF_DSN: dsn}
        )
