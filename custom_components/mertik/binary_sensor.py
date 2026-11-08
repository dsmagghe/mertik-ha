"""Mertik Maxitrol binary sensor platform."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .entity import mertik_device_info
from .mertikdatacoordinator import MertikDataCoordinator

# (name suffix, unique id suffix, coordinator property, icon)
STATUS_SENSORS = (
    (" Igniting", "-Igniting", "is_igniting", "mdi:fire-alert"),
    (" Shutting Down", "-ShuttingDown", "is_shutting_down", "mdi:fire-off"),
    (" Guard Flame", "-GuardFlame", "is_guard_flame_on", "mdi:fire-circle"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mertik binary sensors from a config entry."""
    dataservice: MertikDataCoordinator = entry.runtime_data
    device_info = mertik_device_info(entry)

    async_add_entities(
        MertikStatusBinarySensorEntity(
            dataservice,
            entry.entry_id + unique_suffix,
            entry.data["name"] + name_suffix,
            status,
            icon,
            device_info,
        )
        for name_suffix, unique_suffix, status, icon in STATUS_SENSORS
    )


class MertikStatusBinarySensorEntity(
    CoordinatorEntity[MertikDataCoordinator], BinarySensorEntity
):
    """A status bit of the fireplace: igniting, shutting down or guard flame."""

    def __init__(
        self,
        dataservice: MertikDataCoordinator,
        unique_id: str,
        name: str,
        status: str,
        icon: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(dataservice)
        self._dataservice = dataservice
        self._status = status
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = icon
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        """Return true if the status bit is set."""
        return bool(getattr(self._dataservice, self._status))
