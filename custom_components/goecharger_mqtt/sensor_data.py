import logging
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.components import mqtt

from .const import CONF_GOE_TOPIC_PREFIX, CONF_SERIAL_NUMBER, CONST_VICTRON_CHARGE_PRIOS, DOMAIN

_LOGGER = logging.getLogger(__name__)

class SensorData():
    hass: HomeAssistant
    entityId: str
    dataType: type
    mandatory: bool
    defaultData: Any | None
    stateMethod: Callable | None # Method that is called when gathering the state of this entity
    state: Any | None = None
    additionalData: dict | None = None

    def __init__(self, hass:HomeAssistant, entityId:str, dataType:type=str, mandatory=False, defaultData=None, stateMethod=None) -> None:
        self.hass = hass
        self.entityId = entityId
        self.dataType = dataType
        self.mandatory = mandatory
        self.defaultData = defaultData
        self.stateMethod = stateMethod
        self.additionalData = {}

    def getData(self):
        try:
            curState = self.hass.states.get(self.entityId)
            # get state, but use stateMethod if one exists
            self.state = self.dataType(curState.state if self.stateMethod == None else self.stateMethod(self, curState))
        except ValueError:
            self.state = None
        
    def setData(self, newState):
        self.hass.states.set(self.entityId, str(newState))
            
    
class VictronSensorData(SensorData):
    pass

class GoESensorData(SensorData):

    def setData(self, newState):
        # only mqtt needed since the sensor should get data of that message too
        self.hass.async_add_job(mqtt.async_publish, self.hass, f"{self.entityId}/set", newState)


def stateChargePrio(self: SensorData, chargePrioState: State) -> str:
    # get charge priority
    returnVal = "-1"
    for key, description in CONST_VICTRON_CHARGE_PRIOS.items():
        if chargePrioState.state == description:
            returnVal = key
            break
    if returnVal == "-1":
        returnVal = "0"
        _LOGGER.warn(f"Charger was turned off! Reason: Configured chargePrio is not know to the controller, but is: {chargePrioState.state}")
    # last_changed is needed for instantUpdate in goe_surplus_service
    self.additionalData["last_changed"] = chargePrioState.last_changed
    return returnVal