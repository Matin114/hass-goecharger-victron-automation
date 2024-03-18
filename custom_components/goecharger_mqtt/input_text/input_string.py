"""The go-eCharger (MQTT) input_text."""
import logging
import dataclasses

from typing import Any, Self
from homeassistant import config_entries, core
from homeassistant.components.text import TextEntity
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.core import callback

from ..definitions.input_text import VICTRON_RESTORE_INPUT_TEXT, GoEChargerInputTextEntityDescription
from ..entity import GoEChargerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Config entry setup."""    
    async_add_entities(
        VictronRestoreInputText(config_entry, description)
        for description in VICTRON_RESTORE_INPUT_TEXT
        if not description.disabled
    )


@dataclasses.dataclass
class InputTextExtraStoredData(ExtraStoredData):
    """Object to hold extra stored data."""

    native_value: str | None

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the input_text data."""
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self | None:
        """Initialize a stored input_text state from a dict."""
        try:
            return cls(
                restored["native_value"],
            )
        except KeyError:
            return None

class VictronRestoreInputText(GoEChargerEntity, TextEntity, RestoreEntity):
    """Representation of a go-eCharger switch that is updated via MQTT."""

    entity_description: GoEChargerInputTextEntityDescription

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
        description: GoEChargerInputTextEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry, description)

        self.entity_description = description

        self._attr_available = True

    def set_value(self, value: str) -> None:
        self.native_value = value
        self._attr_native_value = value

    @property
    def extra_restore_state_data(self) -> InputTextExtraStoredData:
        """Return input_text specific state data to be restored."""
        return InputTextExtraStoredData(
            self.native_value,
        )

    async def async_get_last_input_text_data(self) -> InputTextExtraStoredData | None:
        """Restore native_*."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None
        return InputTextExtraStoredData.from_dict(restored_last_extra_data.as_dict())