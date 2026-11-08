"""Shared helpers for Mertik entities."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def mertik_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device that all entities of one fireplace belong to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="Mertik Maxitrol",
        model="WiFi fireplace module",
    )
