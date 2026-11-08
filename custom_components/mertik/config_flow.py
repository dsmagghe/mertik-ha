"""Config flow for the Mertik Maxitrol integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN
from .discovery import async_discover
from .mertik import Mertik


def _probe(host: str) -> None:
    """Connect to the module and read its status once; raise OSError if it fails."""
    Mertik(host).close()


class MertikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Mertik config flow: set up a fireplace or change its IP address."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._modules: list[dict[str, str]] = []

    def _host_field(self, default: str | None) -> dict[Any, Any]:
        """The IP address field: modules found on the network, or any typed address."""
        key = vol.Required(CONF_HOST, default=default) if default else vol.Required(CONF_HOST)
        options = [
            SelectOptionDict(
                value=module["host"],
                label=f"{module['host']} ({module['name']}, {module['mac']})",
            )
            for module in self._modules
        ]
        return {
            key: SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }

    def _found(self) -> str:
        """The modules found, for the form description."""
        if not self._modules:
            return "-"
        return ", ".join(f"{module['host']} ({module['mac']})" for module in self._modules)

    def _mac_of(self, host: str) -> str | None:
        return next((m["mac"] for m in self._modules if m["host"] == host), None)

    async def _async_reachable(self, host: str) -> bool:
        try:
            await self.hass.async_add_executor_job(_probe, host)
        except OSError:
            return False
        return True

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up a fireplace: pick a module found on the network or type its IP address."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if not await self._async_reachable(host):
                errors["base"] = "cannot_connect"
            else:
                if mac := self._mac_of(host):
                    await self.async_set_unique_id(mac)
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                else:
                    self._async_abort_entries_match({CONF_HOST: host})
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={CONF_NAME: user_input[CONF_NAME], CONF_HOST: host},
                )

        if not self._modules:
            self._modules = await async_discover(self.hass)
        default_host = (user_input or {}).get(CONF_HOST) or (
            self._modules[0]["host"] if self._modules else None
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED)): str,
                **self._host_field(default_host),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"found": self._found()},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and change the IP address of the module."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            mac = self._mac_of(host)
            if entry.unique_id and mac and mac != entry.unique_id:
                errors["base"] = "wrong_device"
            elif not await self._async_reachable(host):
                errors["base"] = "cannot_connect"
            else:
                unique_id = entry.unique_id
                if unique_id is None and mac and not any(
                    other.unique_id == mac for other in self._async_current_entries()
                ):
                    unique_id = mac
                return self.async_update_reload_and_abort(
                    entry, unique_id=unique_id, data_updates={CONF_HOST: host}
                )

        self._modules = await async_discover(self.hass)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(self._host_field(entry.data[CONF_HOST])),
            errors=errors,
            description_placeholders={
                "current": entry.data[CONF_HOST],
                "found": self._found(),
            },
        )
