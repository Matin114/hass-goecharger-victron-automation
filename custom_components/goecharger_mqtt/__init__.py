"""The go-eCharger (MQTT) integration."""
from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    ATTR_KEY,
    ATTR_SERIAL_NUMBER,
    ATTR_VALUE,
    DEFAULT_GOE_TOPIC_PREFIX,
    DOMAIN,
    ATTR_VICTRON_CHARGE_PRIO,
    ATTR_VICTRON_GLOBAL_GRID,
    ATTR_VICTRON_BATTERY_CURRENT,
    ATTR_VICTRON_BATTERY_POWER,
    ATTR_VICTRON_BATTERY_VOLTAGE,
    ATTR_VICTRON_BATTERY_SOC,
)

PLATFORMS: list[str] = [
    "binary_sensor",
    "button",
    "number",
    "sensor",
    "select",
    "switch",
]

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA_SET_CONFIG_KEY = vol.Schema(
    {
        vol.Required(ATTR_SERIAL_NUMBER): cv.string,
        vol.Required(ATTR_KEY): cv.string,
        vol.Required(ATTR_VALUE): cv.string,
    }
)
SERVICE_SCHEMA_GOE_SURPLUS_CONTROLLER = vol.Schema(
    {
        vol.Required(ATTR_VICTRON_CHARGE_PRIO): cv.string,
        vol.Required(ATTR_VICTRON_GLOBAL_GRID): cv.string,
        vol.Required(ATTR_VICTRON_BATTERY_CURRENT): cv.string,
        vol.Required(ATTR_VICTRON_BATTERY_POWER): cv.string,
        vol.Required(ATTR_VICTRON_BATTERY_VOLTAGE): cv.string,
        vol.Required(ATTR_VICTRON_BATTERY_SOC): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up go-eCharger (MQTT) from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration."""

    @callback
    async def set_config_key_service(call: ServiceCall) -> None:
        serial_number = call.data.get("serial_number")
        key = call.data.get("key")
        # @FIXME: Retrieve the topic_prefix from config_entry
        topic = f"{DEFAULT_GOE_TOPIC_PREFIX}/{serial_number}/{key}/set"
        value = call.data.get("value")

        if not value.isnumeric():
            if value in ["true", "True"]:
                value = "true"
            elif value in ["false", "False"]:
                value = "false"
            else:
                value = f'"{value}"'

        await mqtt.async_publish(hass, topic, value)
    
    @callback
    async def goe_surplus_controller_service(call: ServiceCall) -> None:
        chargePrio = call.data.get("chargePrio")
        globalGrid = call.data.get("globalGrid")
        batteryPower = call.data.get("batteryPower")
        batteryCurrent = call.data.get("batteryCurrent")
        batteryVoltage = call.data.get("batteryVoltage")
        batterySoc = call.data.get("batterySoc")
        _LOGGER.warn(f"GlobalGrid:{globalGrid}\nBatteryPower:{batteryPower}\nBatteryCurrent:{batteryCurrent}\nBatteryVoltage:{batteryVoltage}\nBatterySOC:{batterySoc}")

    hass.services.async_register(
        DOMAIN,
        "set_config_key",
        set_config_key_service,
        schema=SERVICE_SCHEMA_SET_CONFIG_KEY,
    )
    hass.services.async_register(
        DOMAIN,
        "goe_surplus_controller",
        goe_surplus_controller_service,
        schema=SERVICE_SCHEMA_GOE_SURPLUS_CONTROLLER,
    )

    return True
