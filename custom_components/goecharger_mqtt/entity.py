"""MQTT component mixins and helpers."""
from homeassistant import config_entries
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.util import slugify

from .const import (
    CONF_SERIAL_NUMBER,
    CONF_GOE_TOPIC_PREFIX,
    DEVICE_INFO_MANUFACTURER,
    DEVICE_INFO_MODEL,
    DOMAIN,
    DEFAULT_VICTRON_TOPIC_PREFIX,
)
from .definitions import GoEChargerEntityDescription


class GoEChargerEntity(Entity):
    """Common go-eCharger entity."""

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
        description: GoEChargerEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        serial_number = config_entry.data[CONF_SERIAL_NUMBER]

        if description.isVictron:            
            topic_prefix = DEFAULT_VICTRON_TOPIC_PREFIX
            self._topic = f"{topic_prefix}/{description.key}"
        else:
            topic_prefix = config_entry.data[CONF_GOE_TOPIC_PREFIX]
            self._topic = f"{topic_prefix}/{serial_number}/{description.key}"

        slug = slugify(self._topic.replace("/", "_"))
        self.entity_id = f"{description.domain}.{slug}"

        self._attr_unique_id = "-".join(
            [serial_number, description.domain, description.key, description.attribute]
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            name=config_entry.title,
            manufacturer=DEVICE_INFO_MANUFACTURER,
            model=DEVICE_INFO_MODEL,
        )
