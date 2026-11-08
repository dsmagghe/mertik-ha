"""Mertik Maxitrol fireplace integration."""

import logging
import socket

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .discovery import async_discover, async_find_moved_host
from .mertik import Mertik
from .mertikdatacoordinator import MertikDataCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = ["binary_sensor", "light", "number", "sensor", "switch"]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up Mertik from a config entry."""
    try:
        mertik = await hass.async_add_executor_job(Mertik, entry.data[CONF_HOST])
    except (OSError, socket.timeout) as err:
        # The module may have been given a new IP address: look for it.
        new_host = await async_find_moved_host(hass, entry)
        if new_host is None:
            raise ConfigEntryNotReady(
                f"Cannot connect to Mertik device at {entry.data[CONF_HOST]}"
            ) from err
        _LOGGER.warning(
            "Mertik module moved from %s to %s", entry.data[CONF_HOST], new_host
        )
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_HOST: new_host}
        )
        try:
            mertik = await hass.async_add_executor_job(Mertik, new_host)
        except (OSError, socket.timeout) as err2:
            raise ConfigEntryNotReady(
                f"Cannot connect to Mertik device at {new_host}"
            ) from err2

    coordinator = MertikDataCoordinator(hass, mertik, entry)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if entry.unique_id is None:
        entry.async_create_background_task(
            hass, _async_learn_mac(hass, entry), "mertik_learn_mac"
        )

    return True


async def _async_learn_mac(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> None:
    """Remember the module's MAC address, so it is found again after an IP change."""
    for module in await async_discover(hass):
        if module["host"] != entry.data[CONF_HOST]:
            continue
        if any(
            other.unique_id == module["mac"]
            for other in hass.config_entries.async_entries(DOMAIN)
        ):
            return
        hass.config_entries.async_update_entry(entry, unique_id=module["mac"])
        # reload once, so the device shows its MAC address
        hass.config_entries.async_schedule_reload(entry.entry_id)
        return


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a Mertik config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.async_add_executor_job(entry.runtime_data.mertik.close)
    return unload_ok


async def async_remove_config_entry_device(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow deleting a device this entry no longer provides.

    Earlier versions created their devices under other identifiers (the IP
    address of the module); those stay behind, unavailable, after an update or
    an IP change. The fireplace's current device cannot be deleted.
    """
    return (DOMAIN, entry.entry_id) not in device_entry.identifiers


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Mertik component."""
    return True
