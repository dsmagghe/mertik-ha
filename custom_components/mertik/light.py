"""Mertik light platform."""

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .entity import mertik_device_info
from .mertikdatacoordinator import MertikDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mertik light from a config entry."""
    dataservice: MertikDataCoordinator = entry.runtime_data
    device_info = mertik_device_info(entry)

    async_add_entities(
        [
            MertikLightEntity(
                dataservice, entry.entry_id, entry.data["name"], device_info
            )
        ]
    )


class MertikLightEntity(CoordinatorEntity[MertikDataCoordinator], LightEntity):
    """Representation of a Mertik light entity."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        dataservice: MertikDataCoordinator,
        entry_id: str,
        name: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the Mertik light entity."""
        super().__init__(dataservice)
        self._dataservice = dataservice
        self._attr_name = name + " Light"
        self._attr_unique_id = entry_id + "-Light"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._dataservice.is_light_on

    @property
    def brightness(self) -> int:
        """Return the current brightness as a 0–255 value."""
        return round(self._dataservice.dim_level * 255)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the light on, optionally at a given brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        dim_level = int(brightness) / 255  # type: ignore[arg-type]
        await self.hass.async_add_executor_job(
            self._dataservice.set_light_dim, dim_level
        )
        self._dataservice.async_set_updated_data(None)

    async def async_turn_off(self, **_kwargs: object) -> None:
        """Turn the light off."""
        await self.hass.async_add_executor_job(
            self._dataservice.set_light_dim, 0.0
        )
        self._dataservice.async_set_updated_data(None)
