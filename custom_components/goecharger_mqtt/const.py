"""Constants for the go-eCharger (MQTT) integration."""

DOMAIN = "goecharger_mqtt"

ATTR_SERIAL_NUMBER = "serial_number"
ATTR_KEY = "key"
ATTR_VALUE = "value"

CONF_SERIAL_NUMBER = "serial_number"
CONF_GOE_TOPIC_PREFIX = "topic_prefix"

DEFAULT_GOE_TOPIC_PREFIX = "/go-eCharger"

DEFAULT_VICTRON_TOPIC_PREFIX = "custom"

ATTR_VICTRON_CHARGE_PRIO = "chargePrio"
ATTR_VICTRON_GLOBAL_GRID = "globalGrid"
ATTR_VICTRON_BATTERY_POWER = "batteryPower"
ATTR_VICTRON_BATTERY_CURRENT = "batteryCurrent"
ATTR_VICTRON_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_VICTRON_BATTERY_SOC = "batterySOC"

DEVICE_INFO_MANUFACTURER = "go-e"
DEVICE_INFO_MODEL = "go-eCharger HOME"

CONST_VICTRON_CHARGE_PRIOS = {
    "0": "AUS", # OFF 
    "1": "Prio Hausakku", # prioritize battery
    "2": "Prio Wallbox", # prioritize wallbox
    "3": "50/50", # split available power between battery and wallbox
    "4": "Hausakku entladen bis SOC", # discharge battery until SOC is below the configured confSOCMin
    "5": "Netzstrom", # use power from the grid to fast charge the car
    "6": "Manuel", # charge with the configured power from confDischargePower
    "7": "Automatik", # automatically decide to either charge the car or home battery
    "8": "Manuelle Menge" # charge car with a given amount of Wh
}
