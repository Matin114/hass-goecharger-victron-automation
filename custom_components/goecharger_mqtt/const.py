"""Constants for the go-eCharger (MQTT) integration."""

DOMAIN = "goecharger_mqtt"

ATTR_SERIAL_NUMBER = "serial_number"
ATTR_KEY = "key"
ATTR_VALUE = "value"

CONF_SERIAL_NUMBER = "serial_number"
CONF_GOE_TOPIC_PREFIX = "topic_prefix"

DEFAULT_GOE_TOPIC_PREFIX = "/go-eCharger"

DEFAULT_VICTRON_TOPIC_PREFIX = "custom"

ATTR_VICTRON_GLOBAL_GRID = "globalGrid"
ATTR_VICTRON_BATTERY_POWER = "batteryPower"
ATTR_VICTRON_BATTERY_CURRENT = "batteryCurrent"
ATTR_VICTRON_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_VICTRON_BATTERY_SOC = "batterySOC"

DEVICE_INFO_MANUFACTURER = "go-e"
DEVICE_INFO_MODEL = "go-eCharger HOME"
