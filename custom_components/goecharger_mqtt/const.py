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

# color a hex color, buttonAccess decides if this prio can be selected by the physical GO-E button
CONST_VICTRON_CHARGE_PRIOS = {
    # <unique identifier>: {<friendly name>, <default color of LED ring>, <custom configurable color for LED ring>, <boolean, describes wether this prio can be set by button or not>}
    "0": {"name":"OFF", "defaultColor":"#000000", "colorEntity":"ledColorOff", "buttonAccess":True}, # OFF, color BLACK
    "1": {"name":"Prio Battery", "defaultColor":"#911EB4", "colorEntity":"ledColorPrioBattery", "buttonAccess":True}, # prioritize battery, color PURPLE
    "2": {"name":"Prio Wallbox", "defaultColor":"#FFE119", "colorEntity":"ledColorPrioWallbox", "buttonAccess":True}, # prioritize wallbox, color YELLOW
    "3": {"name":"50/50", "defaultColor":"#9A6324", "colorEntity":"ledColor50_50", "buttonAccess":True}, # split available power between battery and wallbox, color BROWN
    "4": {"name":"Discharge to SOC", "defaultColor":"#FFD8B1", "colorEntity":"ledColorManualToSOC", "buttonAccess":False}, # discharge battery until SOC is below the configured batterySOCMin, color LIGHT ORANGE
    "5": {"name":"Use Grid", "defaultColor":"#E6194B", "colorEntity":"ledColorGrid", "buttonAccess":True}, # use power from the grid to fast charge the car, color RED
    "6": {"name":"Manual", "defaultColor":"#FFD8B1", "colorEntity":"ledColorManual", "buttonAccess":False}, # charge with the configured power from manualCarChargePower, color LIGHT ORANGE
    "7": {"name":"Automatic", "defaultColor":"#42D4F4", "colorEntity":"ledColorAutomatic", "buttonAccess":True}, # automatically decide to either charge the car or home battery, color CYAN
    "8": {"name":"Manual Amount", "defaultColor":"#FFD8B1", "colorEntity":"ledColorManualAmount", "buttonAccess":False}, # charge car with a given amount of Wh, color LIGHT ORANGE
}
