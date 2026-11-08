"""Mertik Maxitrol fireplace integration."""

import socket

from homeassistant import config_entries, core
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .mertik import Mertik
from .mertikdatacoordinator import MertikDataCoordinator

PLATFORMS = ["binary_sensor", "light", "number", "sensor", "switch"]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up Mertik from a config entry."""
    try:
        mertik = await hass.async_add_executor_job(Mertik, entry.data["host"])
    except (OSError, socket.timeout) as err:
        raise ConfigEntryNotReady(
            f"Cannot connect to Mertik device at {entry.data['host']}"
        ) from err

    coordinator = MertikDataCoordinator(hass, mertik, entry)
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


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
