"""Constants for the go-eCharger (MQTT) integration."""

DOMAIN = "goecharger_mqtt"

ATTR_SERIAL_NUMBER = "serial_number"
ATTR_KEY = "key"
ATTR_VALUE = "value"

CONF_SERIAL_NUMBER = "serial_number"
CONF_GOE_TOPIC_PREFIX = "topic_prefix"

DEFAULT_GOE_TOPIC_PREFIX = "/go-eCharger"

DEFAULT_VICTRON_TOPIC_PREFIX = "custom"

ATTR_VICTRON_TRIGGER_ID = "triggerId"

DEVICE_INFO_MANUFACTURER = "go-e"
DEVICE_INFO_MODEL = "go-eCharger HOME"

# color is the int value of in hex color, buttonAccess decides if this prio can be selected by the physical GO-E button
CONST_VICTRON_CHARGE_PRIOS = {
    "0": {"name":"AUS", "color":0, "buttonAccess":True}, # OFF, color BLACK
    "1": {"name":"Prio Hausakku", "color":9510580, "buttonAccess":True}, # prioritize battery, color PURPLE
    "2": {"name":"Prio Wallbox", "color":16769305, "buttonAccess":True}, # prioritize wallbox, color YELLOW
    "3": {"name":"50/50", "color":10117924, "buttonAccess":True}, # split available power between battery and wallbox, color BROWN
    "4": {"name":"Hausakku entladen bis SOC", "color":16767153, "buttonAccess":False}, # discharge battery until SOC is below the configured batterySOCMin, color LIGHT ORANGE
    "5": {"name":"Netzstrom", "color":15079755, "buttonAccess":True}, # use power from the grid to fast charge the car, color RED
    "6": {"name":"Manuel", "color":16767153, "buttonAccess":False}, # charge with the configured power from manualCarChargePower, color LIGHT ORANGE
    "7": {"name":"Automatik", "color":4379892, "buttonAccess":True}, # automatically decide to either charge the car or home battery, color CYAN
    "8": {"name":"Manuelle Menge", "color":16767153, "buttonAccess":False}, # charge car with a given amount of Wh, color LIGHT ORANGE
}
