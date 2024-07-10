"""Constants for the go-eCharger (MQTT) integration."""

DOMAIN = "goecharger_mqtt"

ATTR_SERIAL_NUMBER = "serial_number"
ATTR_KEY = "key"
ATTR_VALUE = "value"

CONF_SERIAL_NUMBER = "serial_number"
CONF_GOE_TOPIC_PREFIX = "topic_prefix"

DEFAULT_GOE_TOPIC_PREFIX = "/go-eCharger"

ATTR_VICTRON_TRIGGER_ID = "triggerId"

DEVICE_INFO_MANUFACTURER = "go-e"
DEVICE_INFO_MODEL = "go-eCharger HOME"

# color a hex color, buttonAccess decides if this prio can be selected by the physical GO-E button
CONST_VICTRON_CHARGE_PRIOS = {
    # <unique identifier>: {<friendly name>, <default color of LED ring>, <boolean describing wether this prio can be set by button or not>}
    "0": {"name":"OFF", "color":"#000000", "buttonAccess":True}, # OFF, color BLACK
    "1": {"name":"Prio Battery", "color":"#911EB4", "buttonAccess":True}, # prioritize battery, color PURPLE
    "2": {"name":"Prio Wallbox", "color":"#FFE119", "buttonAccess":True}, # prioritize wallbox, color YELLOW
    "3": {"name":"50/50", "color":"#9A6324", "buttonAccess":True}, # split available power between battery and wallbox, color BROWN
    "4": {"name":"Discharge to SOC", "color":"#FFD8B1", "buttonAccess":False}, # discharge battery until SOC is below the configured batterySOCMin, color LIGHT ORANGE
    "5": {"name":"Use Grid", "color":"#E6194B", "buttonAccess":True}, # use power from the grid to fast charge the car, color RED
    "6": {"name":"Manual", "color":"#FFD8B1", "buttonAccess":False}, # charge with the configured power from manualCarChargePower, color LIGHT ORANGE
    "7": {"name":"Automatic", "color":"#42D4F4", "buttonAccess":True}, # automatically decide to either charge the car or home battery, color CYAN
    "8": {"name":"Manual Amount", "color":"#FFD8B1", "buttonAccess":False}, # charge car with a given amount of Wh, color LIGHT ORANGE
}
