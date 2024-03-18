import logging
from datetime import timedelta, datetime
import json

from homeassistant.core import HomeAssistant
from homeassistant.components import mqtt

from .const import CONF_GOE_TOPIC_PREFIX, CONF_SERIAL_NUMBER, CONST_VICTRON_CHARGE_PRIOS, DOMAIN

from .definitions import GoEChargerStatusCodes

from .sensor_data import SensorData, GoESensorData, VictronSensorData, InternalSensorData, stateChargePrio, stateUsedPhases, stateFrc

_LOGGER = logging.getLogger(__name__)


class GoESurplusService():
    __name__ = "GoESurplusService"

    hass: HomeAssistant

    # mandatory
    chargePrio: VictronSensorData
    globalGrid: VictronSensorData # (W) global used power
    batteryPower: VictronSensorData # (W) current power the battery is charged with
    batterySoc: VictronSensorData # (%) battery chargelevel in %
    oldTargetCarChargePower: VictronSensorData # (W) old targetCarChargePower
    carChargePower: GoESensorData # (W) current power the car is charged with
    oldFrcVal: GoESensorData # value of GoE key FRC
    oldPsmVal: GoESensorData # value of GoE key PSM
    usedPhases: VictronSensorData # (0-3) for every phase used for charging the car 
    oldAmpVal: GoESensorData # value of GoE key AMP
    ledBrightness: GoESensorData # color of LEDs when charging
    colorCharging: GoESensorData # color of LEDs when charging
    colorIdle: GoESensorData # color of LEDs when idle (not charging, but not finished)
    frcUpdateTimer: VictronSensorData # a timer showing when frc will be updated
    psmUpdateTimer: VictronSensorData # a timer showing when psm will be updated
    # conditional
    maxBatteryChargePower: VictronSensorData # (W) maximal allowed power the battery may be charged with
    batterySocMin: VictronSensorData # (%) discharge battery to this soc in Prio 4
    manualCarChargePower: VictronSensorData # (W) targetCarChargePower will be set to this in Prio 6 & 8
    targetCarPowerAmount: VictronSensorData # (Wh) power amount that should be charged in prio 8
    targetCarPowerAmountFulfilled: VictronSensorData # (Wh) power already charged in prio 8
    totalEnergy: GoESensorData # (Wh) total power ever charged with the wallbox

    # ------------AUTOMATIC MODE----------
    automaticPercFrom0: VictronSensorData # (%) charge Percentage from 0 upwards 
    automaticPercFrom10: VictronSensorData # (%) charge Percentage from 10 upwards 
    automaticPercFrom20: VictronSensorData # (%) charge Percentage from 20 upwards 
    automaticPercFrom30: VictronSensorData # (%) charge Percentage from 30 upwards 
    automaticPercFrom40: VictronSensorData # (%) charge Percentage from 40 upwards 
    automaticPercFrom50: VictronSensorData # (%) charge Percentage from 50 upwards 
    automaticPercFrom60: VictronSensorData # (%) charge Percentage from 60 upwards 
    automaticPercFrom70: VictronSensorData # (%) charge Percentage from 70 upwards 
    automaticPercFrom80: VictronSensorData # (%) charge Percentage from 80 upwards 
    automaticPercFrom90: VictronSensorData # (%) charge Percentage from 90 upwards 
    automaticPercFrom100: VictronSensorData # (%) charge Percentage at 100 
    allAutomaticPercRangeList: list
    automaticLoadingPercentage: float # (%) charge Percentage actually used to not always load every range 
    # ------------AUTOMATIC MODE----------

    powerAmountStart: float # (Wh) power at start of prio where car gets charged with a given amount of Wh

    instantUpdatePower: bool = False # (bool) if chargePrio changes or some prios are selected the chargePower should change instantly
    batteryHasReachedDischargeSOC = False
    mandatorySensorList:list[SensorData]
    valueChangeAllower = {} # here fields which may not be changed instantly can be entered and the time they are allowed to change. see changeOfValueAllowed for more info
    lastButtonPress = datetime.now()

    def __init__(
        self,
        hass : HomeAssistant,
    ) -> None:
        """Initialize the Service."""
        self.hass = hass

        configEntry = self.hass.config_entries.async_entries(DOMAIN)[0]
        serialNumber = configEntry.data[CONF_SERIAL_NUMBER]
        goeTopicPrefix = f"{configEntry.data[CONF_GOE_TOPIC_PREFIX]}/{serialNumber}/"

        usedPhasesAdditionalData = { "powerPhaseList": [GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_nrg_7", dataType=float), 
                                    GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_nrg_8", dataType=float),
                                    GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_nrg_9", dataType=float)]}

        self.chargePrio = VictronSensorData(hass=hass, entityId="select.custom_chargeprio", dataType=int, defaultData=-1, stateMethod=stateChargePrio)
        self.globalGrid = VictronSensorData(hass=hass, entityId="sensor.custom_globalGrid", dataType=float)
        self.batteryPower = VictronSensorData(hass=hass, entityId="sensor.custom_batteryPower", dataType=float)
        self.batterySoc = VictronSensorData(hass=hass, entityId="sensor.custom_batterySOC", dataType=float)
        self.oldTargetCarChargePower = VictronSensorData(hass=hass, entityId="sensor.custom_targetCarChargePower", dataType=float, defaultData=1)
        self.oldAmpVal = GoESensorData(hass=hass, entityId=f"number.go_echarger_{serialNumber}_amp", mqttTopic=f"{goeTopicPrefix}amp", dataType=int, defaultData=0)
        self.ledBrightness = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_lbr", mqttTopic=f"{goeTopicPrefix}lbr", dataType=int, defaultData=0)
        self.colorCharging = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_cch", mqttTopic=f"{goeTopicPrefix}cch", defaultData=65793)
        self.colorIdle = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_cid", mqttTopic=f"{goeTopicPrefix}cid", defaultData=65793)

        # TODO calculate maxBatteryChargePower interally
        self.maxBatteryChargePower = VictronSensorData(hass=hass, entityId="sensor.custom_maxBatteryChargePower", dataType=float)
        self.targetCarPowerAmount = VictronSensorData(hass=hass, entityId="number.custom_targetCarPowerAmount", dataType=float)
        self.batterySocMin = VictronSensorData(hass=hass, entityId="number.custom_batterySOCMin", dataType=float)
        self.manualCarChargePower = VictronSensorData(hass=hass, entityId="number.custom_manualCarChargePower", dataType=float)
        self.targetCarPowerAmountFulfilled = VictronSensorData(hass=hass, entityId="sensor.custom_targetCarPowerAmountFulfilled", dataType=float, defaultData=0)
        self.frcUpdateTimer = VictronSensorData(hass=hass, entityId="sensor.custom_frcUpdateTimer", dataType=int)
        self.psmUpdateTimer = VictronSensorData(hass=hass, entityId="sensor.custom_psmUpdateTimer", dataType=int)
        self.usedPhases = VictronSensorData(hass=hass, entityId="sensor.custom_usedPhases", stateMethod=stateUsedPhases, additionalData=usedPhasesAdditionalData)

        self.carChargePower = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_nrg_12", dataType=float)
        self.oldFrcVal = GoESensorData(hass=hass, entityId=f"select.go_echarger_{serialNumber}_frc", mqttTopic=f"{goeTopicPrefix}frc", dataType=int, stateMethod=stateFrc)
        self.oldPsmVal = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_psm", mqttTopic=f"{goeTopicPrefix}psm", dataType=int)
        self.totalEnergy = GoESensorData(hass=hass, entityId=f"sensor.go_echarger_{serialNumber}_eto", dataType=float)
        

        self.automaticPercFrom0 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage0_10", dataType=float)
        self.automaticPercFrom10 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage10_20", dataType=float)
        self.automaticPercFrom20 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage20_30", dataType=float)
        self.automaticPercFrom30 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage30_40", dataType=float)
        self.automaticPercFrom40 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage40_50", dataType=float)
        self.automaticPercFrom50 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage50_60", dataType=float)
        self.automaticPercFrom60 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage60_70", dataType=float)
        self.automaticPercFrom70 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage70_80", dataType=float)
        self.automaticPercFrom80 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage80_90", dataType=float)
        self.automaticPercFrom90 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage90_100", dataType=float)
        self.automaticPerc100 = VictronSensorData(hass=hass, entityId="number.custom_automaticpercentage100", dataType=float)
        self.allAutomaticPercRangeList = [self.automaticPercFrom0, self.automaticPercFrom10, self.automaticPercFrom20, self.automaticPercFrom30, self.automaticPercFrom40, 
                                self.automaticPercFrom50, self.automaticPercFrom60, self.automaticPercFrom70, self.automaticPercFrom80, self.automaticPercFrom90, self.automaticPerc100]

        # these sensors are always needes,  so should always be loaded
        self.mandatorySensorList = [self.chargePrio, self.globalGrid, self.batteryPower, self.batterySoc, self.oldTargetCarChargePower, 
                                        self.carChargePower, self.oldFrcVal, self.oldPsmVal, self.usedPhases, self.oldAmpVal, 
                                        self.colorCharging, self.colorIdle, self.ledBrightness, self.frcUpdateTimer, self.psmUpdateTimer]


    def initData(self, triggerId) -> bool:
        """returns True if data initialization was successful, otherwise False"""
        self.instantUpdatePower = False
        unavailableSensorList = []

        for sensor in self.mandatorySensorList:
            sensor.retrieveData()
            if (sensor.state == None):
                unavailableSensorList.append(sensor.entityId)

        # stop any further data gathering or calculation if a mandatory field is missing
        if unavailableSensorList:
            _LOGGER.warn(f"Following MANDATORY fields couldn't be retrieved {unavailableSensorList}!\nCanceling charger calculations!")
            return False

        # look at the triggerId to find out how the service was called
        if triggerId == "prioChanged":
            self.instantUpdatePower = True
            self.updateLedColor(self.chargePrio.state)
            
            # reset targetCarPowerAmountFulfilled for Prio 8
            if self.chargePrio.state == 8:
                self.targetCarPowerAmountFulfilled.setData(0)
        elif triggerId == "buttonPressed":
            # on first button press, it should only be activated and shown to the user, which priority is active
            # if pressed within a certain time it will cycle through priorities

            # only react to button press when the last button press is at least 1 sec ago, fixes problem of button activating twice on single press
            if datetime.now() < self.lastButtonPress+timedelta(seconds=1):
                return False

            # if ledBrightness is max, we consider the button active
            if self.ledBrightness.state == 255:
                # cycle through priorities
                newPrio = "0" # 0 equals OFF, so turn off if cycled through all priorities
                for key, priority in CONST_VICTRON_CHARGE_PRIOS.items():
                    # try to get prio with higher key
                    if int(key) <= self.chargePrio.state:
                        continue
                    # if it is possible to select this priority using the button, do so
                    if priority["buttonAccess"]:
                        newPrio = key
                        break
                self.chargePrio.setData(CONST_VICTRON_CHARGE_PRIOS[newPrio]["name"])
                self.chargePrio.state = int(newPrio)

            self.updateLedColor(self.chargePrio.state)
            return False
        elif triggerId == "timeTrigger":
            # TODO change brightness to configurable default brightness instead of 100
            # reset ledBrightness when button isn't active anymore
            if datetime.now() >= self.lastButtonPress+timedelta(seconds=10):
                self.ledBrightness.setData(100)
            

        
        conditionalSensorList:list[SensorData] = []

        if self.chargePrio.state == 1:
            conditionalSensorList.append(self.maxBatteryChargePower)
        elif self.chargePrio.state == 4:
            conditionalSensorList.append(self.batterySocMin)
            conditionalSensorList.append(self.manualCarChargePower)
        elif self.chargePrio.state == 6:
            conditionalSensorList.append(self.manualCarChargePower)
        elif self.chargePrio.state == 7: # automatic
            automaticPercRangeList = []

            # to only load 2 of the automatic ranges look here at the batterySOC already, subtract 0.01 to avoid 100%
            automaticPercIndex = int((self.batterySoc.state-0.01) / 10)
            
            automaticPercRangeList.append(self.allAutomaticPercRangeList[automaticPercIndex])
            automaticPercRangeList.append(self.allAutomaticPercRangeList[automaticPercIndex+1])

            conditionalSensorList.append(self.allAutomaticPercRangeList[automaticPercIndex])
            conditionalSensorList.append(self.allAutomaticPercRangeList[automaticPercIndex+1])
        elif self.chargePrio.state == 8:
            conditionalSensorList.append(self.manualCarChargePower)
            conditionalSensorList.append(self.targetCarPowerAmount)
            conditionalSensorList.append(self.targetCarPowerAmountFulfilled)
            conditionalSensorList.append(self.totalEnergy)
            conditionalSensorList.append(self.maxBatteryChargePower)

        for sensor in conditionalSensorList:
            sensor.retrieveData()
            if (sensor.state == None):
                unavailableSensorList.append(sensor.entityId)

        # stop any further data gathering or calculation if a conditional field is missing
        if unavailableSensorList:
            _LOGGER.warn(f"Following CONDITIONAL fields couldn't be retrieved {unavailableSensorList}!\nCanceling charger calculations!")
            return False

        if self.chargePrio.state == 7: # automatic
            # calculate automaticLoadingPercentage
            loadingPercentage = 0


            # calculate weighting of the two ranges
            weighting = ((self.batterySoc.state-0.01) % 10) / 10
            # lower range weighting
            loadingPercentage += (automaticPercRangeList[0].state/100) * (1-weighting)
            # higher range weighting
            loadingPercentage += (automaticPercRangeList[1].state/100) * weighting
            
            self.automaticLoadingPercentage = round(loadingPercentage, 2)

        return True

    def executeService(self, triggerId):
        if not self.initData(triggerId):
            # if button was pressed, the priority will change so the service will be called again in a few ms
            if triggerId == "buttonPressed":
                return
            _LOGGER.warn("Data initialization failed! Controller won't be executed!")
            return
        
        targetCarChargePower = round(self.calcTargetCarChargePower(), 0)

        # decide between single phase and multiphase
        if targetCarChargePower <= 4140:
            # if charging via two phases check with 3680 (2*230V*8A) 
            # to avoid often switching between single and multiphase charging
            # -> the lowest possible power would be 2760W, but I used 3680W to be able to make smaller power changes in a lower power region
            if self.usedPhases.state == 2 and targetCarChargePower >= 3680:
                psmNewVal = 2
            else:
                psmNewVal = 1
        else:
            psmNewVal = 2

        # use timer to decide wheter psm should be updated or not, to prevent switching psm to often
        psmUpdateTimer, psmNewVal = self.updateValueTimer("psm", self.oldPsmVal.state, psmNewVal, 30)
        self.psmUpdateTimer.setData(psmUpdateTimer)
    
        ampNewVal, targetCarChargePower = self.calcAmpNewVal(targetCarChargePower, psmNewVal)       
       
        # check if charging is allowed
        if targetCarChargePower < 1380:
            # charging disabled
            frcNewVal = 1
        else:
            # charging enabled
            frcNewVal = 2

        # use timer to decide wheter frc should be updated or not, to prevent switching frc to often
        frcUpdateTimer, frcNewVal = self.updateValueTimer("frc", self.oldFrcVal.state, frcNewVal, 15)
        self.frcUpdateTimer.setData(frcUpdateTimer)

        # update amp
        self.oldAmpVal.setData(ampNewVal)

        # update targetCarChargePower
        self.oldTargetCarChargePower.setData(targetCarChargePower)

        # update frc if needed
        if (frcUpdateTimer == 0):
            self.oldFrcVal.setData(frcNewVal)
        
        # update psm if needed
        if (psmUpdateTimer == 0):
            self.oldPsmVal.setData(psmNewVal)
            

    def calcTargetCarChargePower(self) -> int:
        availablePower = self.batteryPower.state - self.globalGrid.state + self.carChargePower.state
        targetCarChargePower = 0
        
        if self.chargePrio.state == 1: # prioritize battery
            targetCarChargePower = availablePower - self.maxBatteryChargePower.state
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300) and bigger than the allowed battery charge power
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower.state - self.globalGrid.state > self.maxBatteryChargePower.state:
                targetCarChargePower = 1380
        elif self.chargePrio.state == 2: # prioritize wallbox
            targetCarChargePower = availablePower
        elif self.chargePrio.state == 3: # split available power between battery and wallbox
            targetCarChargePower = availablePower/2
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300)
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower.state - self.globalGrid.state:
                targetCarChargePower = 1380   
        elif self.chargePrio.state == 4: # discharge battery until SOC is below the configured confSOCMin
            # check if batterySocMin was already reached 
            if self.batterySoc.state <= self.batterySocMin.state:
                targetCarChargePower = 0
                self.instantUpdatePower = True
            else:
                # otherwise charge with eihter configured power or availablePower, considering which is bigger
                targetCarChargePower = max(self.manualCarChargePower.state, availablePower)

        elif self.chargePrio.state == 5: # use power from the grid to fast charge the car
            targetCarChargePower = availablePower + 27000
            self.instantUpdatePower = True
        elif self.chargePrio.state == 6: # charge with the configured power from manualCarChargePower
            targetCarChargePower = self.manualCarChargePower.state
            self.instantUpdatePower = True
        elif self.chargePrio.state == 7: # automatically update the partition used for charging the car based on a configured curve
            targetCarChargePower = availablePower * self.automaticLoadingPercentage
        elif self.chargePrio.state == 8: # charge car with a given amount of Wh
            # when the chargePrio is changed set current totalEnergy for targetCarPowerAmountFulfilled
            if self.instantUpdatePower:
                self.powerAmountStart = self.totalEnergy.state

            newTargetCarPowerAmountFulfilled = abs(round(self.totalEnergy.state - self.powerAmountStart))
            # check if targetCarPowerAmount was already reached 
            if newTargetCarPowerAmountFulfilled >= self.targetCarPowerAmount.state:
                targetCarChargePower = 0
                self.instantUpdatePower = True
            else:
                # otherwise charge with either configured power or availablePower - maxBatteryChargePower, considering which is bigger
                targetCarChargePower = max(self.manualCarChargePower.state, availablePower - self.maxBatteryChargePower.state)

            # update targetcarpoweramountfulfilled
            self.targetCarPowerAmountFulfilled.setData(newTargetCarPowerAmountFulfilled)

        else: # either OFF or unknown chargePrio
            targetCarChargePower = 0
            self.instantUpdatePower = True


        # smoothen out targetCarChargePower for it not to flicker around, but only if difference to old targetCarChargePower is greater than 200
        if not self.instantUpdatePower and not self.oldTargetCarChargePower.state == 0 and targetCarChargePower >= 1380 and abs(targetCarChargePower-self.oldTargetCarChargePower.state) > 200:
            targetCarChargePower = round((targetCarChargePower + 5*self.oldTargetCarChargePower.state)/6)

        # avoid a negativ targetCarChargePower
        return targetCarChargePower if targetCarChargePower > 0 else 0

    def updateValueTimer(self, valName:str, oldVal, newVal, timeout: int) -> int:
        """This method is responsible for values that change after a certain time.
        If oldVal and newVal become the same the change timer is stopped and resets"""
        # by default return -1, in case of error, the value gets not updated
        updateTimer = -1
        if oldVal == newVal or self.instantUpdatePower:
            # values are equal or instantUpdatePower is set, so reset timer
            self.valueChangeAllower.pop(valName, None)
            updateTimer = 0
        else:
            now = datetime.now()
            if valName not in self.valueChangeAllower:
                # first occurance of the values differing: register the valueChangeRequest
                self.valueChangeAllower[valName] = now+timedelta(seconds=timeout)
                updateTimer = timeout
            else:
                # check if time of valueChangeRequest was reached
                changeAllowedTime = self.valueChangeAllower[valName]
                if now >= changeAllowedTime:
                    updateTimer = 0
                else:
                    delta: timedelta = changeAllowedTime-now
                    updateTimer = int(round(delta.total_seconds()))
        
        # keep working with the oldVal, since no update is allowed
        if updateTimer != 0:
            newVal = oldVal
        
        return updateTimer, newVal

    def calcAmpNewVal(self, targetCarChargePower, psm):
        """calculate charging AMPs"""
        if psm == 1:
            ampNewVal = targetCarChargePower/230
        else:
            # calculate two phase charging
            ampNewVal = targetCarChargePower/230/2
            if self.usedPhases.state == 3:
                ampNewVal = targetCarChargePower/400/1.73

        ampNewVal = int(ampNewVal)
    
        # enable discharging battery for priority 2 & 3 (prioritize battery & 50/50) 
        # IF (battery is already charged up to 97% OR has reached it before and is still above 95%) AND feeding the grid with more than 300W
        if self.chargePrio.state in [2,3,4,6,7,8] and (self.batterySoc.state >= 97 or self.batteryHasReachedDischargeSOC) and self.globalGrid.state < -300:
            if ampNewVal < 6:
                ampNewVal = 6
            else:
                ampNewVal += 1

            # calculate new targetCarChargePower, since the amp value has increased
            if psm == 1:
                targetCarChargePower = ampNewVal*230
            else:
            # calculate two phase charging
                targetCarChargePower = ampNewVal*230*2
                if self.usedPhases.state == 3:
                    targetCarChargePower = ampNewVal*400*1.73


            # set batteryHasReachedDischargeSOC to True if SOC has reached 97 and is between 97 and 95
            # set it to False if it has dropped to 95
            self.batteryHasReachedDischargeSOC = False if self.batterySoc.state <= 95 else True

        if ampNewVal < 6:
            ampNewVal = 6
        elif psm == 1 and ampNewVal > 18:
            # single and two phase charging allows max 18A
            ampNewVal = 18
        elif ampNewVal > 32:
            # multi phase charging allowes max 32A
            ampNewVal = 32

        return ampNewVal, targetCarChargePower
    
    def updateLedColor(self, chargePrio:int):
        # max brightness for 10 sec for better viewing
        self.ledBrightness.setData(255)
        self.lastButtonPress = datetime.now()
        # update colors
        self.colorCharging.setData(json.dumps(CONST_VICTRON_CHARGE_PRIOS[str(chargePrio)]["defaultColor"]))
        self.colorIdle.setData(json.dumps(CONST_VICTRON_CHARGE_PRIOS[str(chargePrio)]["defaultColor"]))
