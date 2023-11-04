import logging
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.components import mqtt

from .const import CONST_VICTRON_CHARGE_PRIOS
from .definitions import GoEChargerStatusCodes

_LOGGER = logging.getLogger(__name__)

class SensorData():
    hass: HomeAssistant
    entityId: str
    dataType: type
    defaultData: Any | None
    stateMethod: Callable | None # Method that is called when gathering the state of this entity
    state: Any | None = None
    additionalData: dict | None = None

    def __init__(self, hass:HomeAssistant, entityId:str, dataType:type=str, defaultData=None, stateMethod=None) -> None:
        self.hass = hass
        self.entityId = entityId
        self.dataType = dataType
        self.defaultData = defaultData
        self.stateMethod = stateMethod
        self.additionalData = {}

    def retrieveData(self):
        try:
            curState = self.hass.states.get(self.entityId)
            # get state, but use stateMethod if one exists
            self.state = self.dataType(curState.state) if self.stateMethod == None else self.stateMethod(self, curState)
        except ValueError:
            self.state = self.defaultData
        
    def setData(self, newState):
        if self.state != newState:
            self.state = newState
            # TODO maybe change custom sensors to not use MQTT
            # for now kept the custom sensors in MQTT even if not needed
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"custom/{self.entityId.split('_',1)[1]}", newState)
            
    
class VictronSensorData(SensorData):
    pass

class GoESensorData(SensorData):
    
    mqttTopic:str=None

    def __init__(self, hass:HomeAssistant, entityId:str, mqttTopic:str=None, dataType:type=str, defaultData=None, stateMethod=None) -> None:
        super().__init__(hass, entityId, dataType, defaultData, stateMethod)
        self.mqttTopic = mqttTopic

    def setData(self, newState):
        # only mqtt needed since the sensor should get data of that message too
        if self.mqttTopic == None:
            _LOGGER.warn(f"{self.entityId} cannot be set via MQTT. This method should not becalled for this object!")
            return
        if self.state != newState:
            self.state = newState
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{self.mqttTopic}/set", newState)

class InternalSensorData(SensorData):

    def __init__(self, hass:HomeAssistant, entityId:str, additionalData:dict, dataType:type=str, defaultData=None, stateMethod=None) -> None:
        super().__init__(hass, entityId, dataType, defaultData, stateMethod)
        self.additionalData = additionalData

    def retrieveData(self):
        # stateMethod should return a list, containing a bool for wasSuccessful and the actual value
        # e.g. [True, 3]
        stateMethodReturn = self.stateMethod(self)
        if stateMethodReturn[0]:
            self.state = stateMethodReturn[1]
        else:
            self.state = self.defaultData


def stateChargePrio(self: SensorData, chargePrioState: State) -> int:
    # get charge priority
    returnVal = -1
    for key, description in CONST_VICTRON_CHARGE_PRIOS.items():
        if chargePrioState.state == description:
            returnVal = self.dataType(key)
            break
    if returnVal == -1:
        returnVal = 0
        _LOGGER.warn(f"Charger was turned off! Reason: Configured chargePrio is not know to the controller, but is: {chargePrioState.state}")
    # last_changed is needed for instantUpdate in goe_surplus_service
    self.additionalData["last_changed"] = chargePrioState.last_changed
    return returnVal

def stateFrc(self: SensorData, frcState: State) -> int:
    """Get frc data since it is mapped to strings"""
    frcPossibleStateDict: dict[int, str] = getattr(GoEChargerStatusCodes, "frc")
    frcValue = None

    for code, description in frcPossibleStateDict.items():
        if description == frcState.state:
            frcValue = code
    
    return frcValue

def stateUsedPhases(self: SensorData):
    wasSuccessful = True
    usedPhases = 0
    powerPhaseList:list[GoESensorData] = self.additionalData["powerPhaseList"]
    
    for powerPhase in powerPhaseList:
        powerPhase.retrieveData()
        if powerPhase.state == None:
            # if state is None, data couldn't be retrieved, so cancel
            wasSuccessful
            break
        else:
            # add one used phase if there is power on the phase (above 500W since some minor power may always be existant)
            usedPhases += 1 if powerPhase.state > 500 else 0

    return wasSuccessful, usedPhases
