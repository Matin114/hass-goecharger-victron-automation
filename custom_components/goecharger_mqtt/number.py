"""The go-eCharger (MQTT) switch."""
import logging

from homeassistant import config_entries, core
from homeassistant.components import mqtt
from homeassistant.components.number import NumberEntity, RestoreNumber
from homeassistant.core import callback

from .definitions.number import GOE_NUMBERS, VICTRON_NUMBERS, VICTRON_RESTORE_NUMBERS, GoEChargerNumberEntityDescription
from .entity import GoEChargerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Config entry setup."""
    async_add_entities(
        GoEChargerNumber(config_entry, description)
        for description in GOE_NUMBERS + VICTRON_NUMBERS
        if not description.disabled
    )
    
    async_add_entities(
        VictronRestoreNumber(config_entry, description)
        for description in VICTRON_RESTORE_NUMBERS
        if not description.disabled
    )


class GoEChargerNumber(GoEChargerEntity, NumberEntity):
    """Representation of a go-eCharger switch that is updated via MQTT."""

    entity_description: GoEChargerNumberEntityDescription

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
        description: GoEChargerNumberEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry, description)

        self.entity_description = description
        # by default goe numbers are not available, but victron numbers should be
        self._attr_available = description.isVictron
        if description.isVictron:
            self._attr_native_value = self.native_min_value

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        setterTopic = f"{self._topic}"
        if not self.entity_description.isVictron:
            setterTopic += "/set"
        await mqtt.async_publish(
            self.hass, setterTopic, int(value)
        )

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""

        @callback
        def message_received(message):
            """Handle new MQTT messages."""
            self._attr_available = True
            if self.entity_description.state is not None:
                self._attr_native_value = self.entity_description.state(
                    message.payload, self.entity_description.attribute
                )
            else:
                if message.payload == "null":
                    self._attr_native_value = None
                else:
                    self._attr_native_value = message.payload

            self.async_write_ha_state()

        await mqtt.async_subscribe(self.hass, self._topic, message_received, 1)


class VictronRestoreNumber(GoEChargerEntity, RestoreNumber):
    """Representation of a go-eCharger switch that is updated via MQTT."""

    entity_description: GoEChargerNumberEntityDescription

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
        description: GoEChargerNumberEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(config_entry, description)

        self.entity_description = description
        # by default goe numbers are not available, but victron numbers should be
        self._attr_available = description.isVictron
        if description.isVictron:
            self._attr_native_value = self.native_min_value

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self._state = value

    async def async_added_to_hass(self):
        """Restore a value from before stopping HASS"""
        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_native_value = last_state.state
            self._state = last_state.state
