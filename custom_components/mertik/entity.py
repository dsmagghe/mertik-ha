"""Shared helpers for Mertik entities."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from .const import DOMAIN


def mertik_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device that all entities of one fireplace belong to."""
    info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="Mertik Maxitrol",
        model="WiFi fireplace module",
    )
    if entry.unique_id:
        # the unique id is the module's MAC address, learnt by discovery
        info["connections"] = {(CONNECTION_NETWORK_MAC, entry.unique_id)}
    return info
