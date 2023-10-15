import logging
from datetime import timedelta, datetime
import pytz

from homeassistant.core import HomeAssistant
from homeassistant.components import mqtt

from .const import CONF_GOE_TOPIC_PREFIX, CONF_SERIAL_NUMBER, CONST_VICTRON_CHARGE_PRIOS, DOMAIN

from .definitions import GoEChargerStatusCodes

_LOGGER = logging.getLogger(__name__)


class GoESurplusService():
    __name__ = "GoESurplusService"

    hass: HomeAssistant
    chargePrio: int = -1
    globalGrid: float # global used power
    batteryPower: float # current power the battery is charged with
    batteryCurrent: float
    batteryVoltage: float
    batterySoc: float # battery chargelevel in %
    maxBatteryChargePower: float # maximal allowed power the battery may be charged with
    usedPhases: int = 0 # 0-3 for every phase used for charging the car 
    instantUpdatePower: bool = False # if chargePrio changes or some prios are selected the chargePower should change instantly
    carChargePower: float # current power the car is charged with
    oldTargetCarChargePower: float # old targetCarChargePower
    oldAmpVal: float
    oldFrcVal: float
    oldPsmVal: float

    valueChangeAllower = {} # here fields which may not be changed instantly can be entered and the time they are allowed to change. see changeOfValueAllowed for more info

    def __init__(
        self,
        hass : HomeAssistant,
    ) -> None:
        """Initialize the Service."""
        
        self.hass = hass
    
    # returns True if data initialization was successful, otherwise False
    def initData(self, serialNumber:str) -> bool:
        # key=variableName, value=hass sensor name
        mandatorySensorData = {
            "globalGrid" : "sensor.custom_globalGrid",
            "batteryPower" : "sensor.custom_batteryPower",
            "batteryCurrent" : "sensor.custom_batteryCurrent",
            "batteryVoltage" : "sensor.custom_batteryVoltage",
            "batterySoc" : "sensor.custom_batterySOC",
            "carChargePower" : f"sensor.go_echarger_{serialNumber}_nrg_12",
            "maxBatteryChargePower" : "sensor.custom_maxBatteryChargePower",
            "powerPhaseOne" : f"sensor.go_echarger_{serialNumber}_nrg_5",
            "powerPhaseTwo" : f"sensor.go_echarger_{serialNumber}_nrg_6",
            "powerPhaseThree" : f"sensor.go_echarger_{serialNumber}_nrg_7",
            "oldAmpVal" : f"number.go_echarger_{serialNumber}_amp",
            "oldPsmVal" : f"sensor.go_echarger_{serialNumber}_psm",
        }
        unavailableSensorData = []

        # check if all mandatory sensor data is available
        for varName, sensor in mandatorySensorData.items():
            try:
                mandatorySensorData[varName] = float(self.hass.states.get(sensor).state)
            except ValueError:
                unavailableSensorData.append(sensor)
        
        # get frc data since it is mapped to strings
        frcPossibleStateDict: dict[int, str] = getattr(GoEChargerStatusCodes, "frc")
        oldFrcState = self.hass.states.get(f"select.go_echarger_{serialNumber}_frc").state
        oldFrcVal = -1

        for code, description in frcPossibleStateDict.items():
            if description == oldFrcState:
                oldFrcVal = code
        if oldFrcVal == -1:
            # sensor data not available
            unavailableSensorData.append(f"select.go_echarger_{serialNumber}_frc")
        else:
            self.oldFrcVal = oldFrcVal

        # log all unavailable sensors
        if unavailableSensorData:
            _LOGGER.warn(f"Following fields couldn't be retrieved {unavailableSensorData}!\nCanceling charger calculations!")
            return False

        self.globalGrid = mandatorySensorData["globalGrid"]
        self.batteryPower = mandatorySensorData["batteryPower"]
        self.batteryCurrent = mandatorySensorData["batteryCurrent"]
        self.batteryVoltage = mandatorySensorData["batteryVoltage"]
        self.batterySoc = mandatorySensorData["batterySoc"]
        self.carChargePower = mandatorySensorData["carChargePower"]
        # TODO calculate maxBatteryChargePower here or in a own service
        self.maxBatteryChargePower = mandatorySensorData["maxBatteryChargePower"]
        
        # regoster everey used phase
        self.usedPhases += 1 if mandatorySensorData["powerPhaseOne"] > 0 else 0
        self.usedPhases += 1 if mandatorySensorData["powerPhaseTwo"] > 0 else 0
        self.usedPhases += 1 if mandatorySensorData["powerPhaseThree"] > 0 else 0

        # set old values

        # get old targetCarChargePower, if none fount use 0
        self.oldAmpVal = mandatorySensorData["oldAmpVal"]
        self.oldPsmVal = mandatorySensorData["oldPsmVal"]
        try:
            self.oldTargetCarChargePower = float(self.hass.states.get("sensor.custom_targetCarChargePower").state)
        except ValueError:
            self.oldTargetCarChargePower = 0
        
        # get charge priority
        chargePrioSelect = self.hass.states.get('select.custom_chargeprio')
        for key, description in CONST_VICTRON_CHARGE_PRIOS.items():
            if chargePrioSelect.state == description:
                self.chargePrio = int(key)
                break
        if self.chargePrio == -1:
            self.chargePrio = 0
            _LOGGER.warn(f"Configured chargePrio is not know to the controller, but: {chargePrioSelect.state}\nCharger was turned off!")
        
        # if new prio was selected always instat update all fields
        if chargePrioSelect.last_changed > datetime.now(pytz.UTC)-timedelta(seconds=1):
            self.instantUpdatePower = True

        return True

    def executeService(self):
        configEntry = self.hass.config_entries.async_entries(DOMAIN)[0]
        serialNumber = configEntry.data[CONF_SERIAL_NUMBER]
        goeTopicPrefix = f"{configEntry.data[CONF_GOE_TOPIC_PREFIX]}/{serialNumber}"

        if not self.initData(serialNumber):
            _LOGGER.warn("Data initialization failed! Controller won't be executed!")
            return
        
        targetCarChargePower = self.calcTargetCarChargePower()

        # check if charging is allowed
        if targetCarChargePower < 1380:
            # charging disabled
            frcNewVal = 1
        else:
            # charging enabled
            frcNewVal = 2
        
        # decide between single phase and multiphase
        if targetCarChargePower <= 4140:
            # if charging via two phases check with 3680 (2*230V*8A) 
            # to avoid often switching between single and multiphase charging
            # -> the lowest possible power would be 2760W, but I used 3680W to be able to make smaller power changes in a lower power region
            if self.usedPhases == 2 and targetCarChargePower >= 3680:
                psmNewVal = 2
            else:
                psmNewVal = 1
        else:
            psmNewVal = 2

        # wait for some fields for a certain time not to swap them to often. e.g. psm, since changing phase modes takes a little time and might jump arround
        frcUpdateTimer = 0
        psmUpdateTimer = 0
        if not self.instantUpdatePower:
            frcUpdateTimer = self.updateValueTimer("frc", self.oldFrcVal, frcNewVal, 30)
            psmUpdateTimer = self.updateValueTimer("psm", self.oldPsmVal, psmNewVal, 30)

            self.hass.async_add_job(mqtt.async_publish, self.hass, f"custom/frcUpdateTimer", frcUpdateTimer)
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"custom/psmUpdateTimer", psmUpdateTimer)

        ampNewVal = self.calcAmpNewVal(targetCarChargePower, psmNewVal)

        # TODO replace the mqtt calls with the actual update of the sensor e.g.:
        # self.hass.async_add_job(GoEChargerSelect.async_select_option, "OFF")
        
        # update amp if needed
        if (ampNewVal != self.hass.states.get(f"number.go_echarger_{serialNumber}_amp").state):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/amp/set", ampNewVal)

        # update targetCarChargePower if needed
        if (targetCarChargePower != self.oldTargetCarChargePower):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"custom/targetCarChargePower", targetCarChargePower)

        # update frc if needed
        if (frcNewVal != self.oldFrcVal and frcUpdateTimer == 0):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/frc/set", frcNewVal)
        
        # update psm if needed
        if (psmNewVal != self.oldPsmVal and psmUpdateTimer == 0):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/psm/set", psmNewVal)
            

    def calcTargetCarChargePower(self) -> int:
        availablePower = self.batteryPower - self.globalGrid + self.carChargePower
        targetCarChargePower = 0
        
        if self.chargePrio == 1: # prioritize battery
            targetCarChargePower = availablePower - self.maxBatteryChargePower
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300) and bigger than the allowed battery charge power
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower - self.globalGrid > self.maxBatteryChargePower:
                targetCarChargePower = 1380
        elif self.chargePrio == 2: # prioritize wallbox
            targetCarChargePower = availablePower
        elif self.chargePrio == 3: # split available power between battery and wallbox
            targetCarChargePower = availablePower/2
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300)
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower - self.globalGrid:
                targetCarChargePower = 1380   
        elif self.chargePrio == 5: # use power from the grid to fast charge the car
            targetCarChargePower = availablePower + 27000
            self.instantUpdatePower = True
        else: # either OFF or unknown chargePrio
            targetCarChargePower = 0
            self.instantUpdatePower = True

        # smoothen out targetCarChargePower for it not to flicker around
        if not self.instantUpdatePower and not self.oldTargetCarChargePower == 0 and targetCarChargePower > 0:
            targetCarChargePower = (targetCarChargePower+4*self.oldTargetCarChargePower)/5
            
        # avoid feeding the grid with more power than is being charged
        if self.chargePrio > 0:
            if self.batterySoc > 95 and targetCarChargePower < self.carChargePower - self.globalGrid:
                targetCarChargePower = self.carChargePower - self.globalGrid
            elif targetCarChargePower < self.globalGrid *-1:
                targetCarChargePower = self.globalGrid*-1

        # avoid a negativ targetCarChargePower
        return targetCarChargePower if targetCarChargePower > 0 else 0

    def updateValueTimer(self, valName:str, oldVal, newVal, timeout: int) -> int:
        """This method is responsible for values that change after a certain time.
        If oldVal and newVal become the same the change timer is stopped and resets"""
        if oldVal == newVal:
            # values are equal, so reset timer
            self.valueChangeAllower[valName] = None
        else:
            now = datetime.now()
            if self.valueChangeAllower[valName] == None:
                # first occurance of the values differing: register the valueChangeRequest
                self.valueChangeAllower[valName] = now+timedelta(seconds=timeout)
                now-(now-timedelta(seconds=100))

                delta = now-(now-timedelta(seconds=100))
                delta.total_seconds()

                return timeout
            else:
                # check if time of valueChangeRequest was reached
                changeAllowedTime = self.valueChangeAllower[valName]
                if now >= changeAllowedTime:
                    return 0
                else:
                    delta: timedelta = changeAllowedTime-now
                    return int(round(delta.total_seconds()))
        
        return -1


    def calcAmpNewVal(self, targetCarChargePower, psm):
        """calculate charging AMPs"""
        if psm == 1:
            ampNewVal = targetCarChargePower/230
        else:
            # calculate two phase charging
            ampNewVal = targetCarChargePower/230/2
            if self.usedPhases == 3:
                ampNewVal = targetCarChargePower/400/1.73

        ampNewVal = int(ampNewVal)

        # enable discharging battery for priority 2 (prioritize battery) 
        # IF battery is already charged up to 95% AND feeding the grid with more than 300W
        if self.chargePrio == 2 and self.batterySoc >= 95 and self.globalGrid < -300:
            if ampNewVal < 6:
                ampNewVal = 6
            else:
                ampNewVal += 1


        if ampNewVal < 6:
            ampNewVal = 6
        elif psm == 1 and ampNewVal > 18:
            # single and two phase charging allows max 18A
            ampNewVal = 18
        elif ampNewVal > 32:
            # multi phase charging allowes max 32A
            ampNewVal = 32

        return ampNewVal