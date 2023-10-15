import logging
from datetime import timedelta, datetime
import pytz

from homeassistant.core import HomeAssistant
from homeassistant.components import mqtt

from .const import CONF_GOE_TOPIC_PREFIX, CONF_SERIAL_NUMBER, CONST_VICTRON_CHARGE_PRIOS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoESurplusService():
    __name__ = "GoESurplusService"

    hass: HomeAssistant
    chargePrio: str = "-1"
    globalGrid: float # global used power
    batteryPower: float
    batteryCurrent: float
    batteryVoltage: float
    batterySoc: float # battery chargelevel in %
    chargePower: float # current power the battery is charged with
    maxBatteryChargePower: float # maximal allowed power the battery may be charged with
    usedPhases: int = 0 # 0-3 for every phase used for charging the car 
    instantUpdatePower: bool = False # if chargePrio changes or some prios are selected the chargePower should change instantly

    def __init__(
        self,
        hass : HomeAssistant,
    ) -> None:
        """Initialize the Service."""
        
        self.hass = hass
    
    # returns True if data initialization was successful, otherwise False
    def initData(self) -> bool:
        # key=variableName, value=hass sensor name
        sensorData = {
            "globalGrid" : "sensor.custom_globalGrid",
            "batteryPower" : "sensor.custom_batteryPower",
            "batteryCurrent" : "sensor.custom_batteryCurrent",
            "batteryVoltage" : "sensor.custom_batteryVoltage",
            "batterySoc" : "sensor.custom_batterySOC",
            "carChargePower" : "sensor.go_echarger_217953_nrg_12",
            "maxBatteryChargePower" : "sensor.custom_maxBatteryChargePower",
            "powerPhaseOne" : "sensor.go_echarger_217953_nrg_5",
            "powerPhaseTwo" : "sensor.go_echarger_217953_nrg_6",
            "powerPhaseThree" : "sensor.go_echarger_217953_nrg_7",
        }
        unavailableSensorData = []

        # check if all sensor data is available
        for varName, sensor in sensorData.items():
            try:
                sensorData[varName] = float(self.hass.states.get(sensor).state)
            except ValueError:
                unavailableSensorData.append(sensor)
        
        if unavailableSensorData:
            _LOGGER.info(f"Following fields couldn't be retrieved {unavailableSensorData}!\nCanceling charger calculations!")
            return False


        chargePrioSelect = self.hass.states.get('select.custom_chargeprio')
        for key, description in CONST_VICTRON_CHARGE_PRIOS.items():
            if chargePrioSelect.state == description:
                self.chargePrio = key
                break
        if self.chargePrio == "-1":
            self.chargePrio = "0"
            _LOGGER.warn(f"Configured chargePrio is not know to the controller, but: {chargePrioSelect.state}\nCharger was turned off!")
        
        # if new prio was selected always instat update all fields
        if chargePrioSelect.last_changed > datetime.now(pytz.UTC)-timedelta(seconds=1):
            self.instantUpdatePower = True

        self.globalGrid = sensorData["globalGrid"]
        self.batteryPower = sensorData["batteryPower"]
        self.batteryCurrent = sensorData["batteryCurrent"]
        self.batteryVoltage = sensorData["batteryVoltage"]
        self.batterySoc = sensorData["batterySoc"]
        self.carChargePower = sensorData["carChargePower"]
        # TODO calculate maxBatteryChargePower here or in a own service
        self.maxBatteryChargePower = sensorData["maxBatteryChargePower"]
        
        # regoster everey used phase
        self.usedPhases += 1 if sensorData["powerPhaseOne"] > 0 else 0
        self.usedPhases += 1 if sensorData["powerPhaseTwo"] > 0 else 0
        self.usedPhases += 1 if sensorData["powerPhaseThree"] > 0 else 0

        return True

    def executeService(self):

        if not self.initData():
            return
        
        targetCarChargePower = self.calcTargetCarChargePower()

        # check if charging is allowed
        if targetCarChargePower < 1380:
            frcNewVal = 1
        else:
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

        ampNewVal = self.calcAmpNewVal(targetCarChargePower, psmNewVal)

        # TODO replace the mqtt calls with the actual update of the sensor e.g.:
        # self.hass.async_add_job(GoEChargerSelect.async_select_option, "OFF")
        configEntry = self.hass.config_entries.async_entries(DOMAIN)[0]
        serialNumber = configEntry.data[CONF_SERIAL_NUMBER]
        goeTopicPrefix = f"{configEntry.data[CONF_GOE_TOPIC_PREFIX]}/{serialNumber}"
        
        # set new amp if needed
        if (ampNewVal != self.hass.states.get(f"number.go_echarger_{serialNumber}_amp")):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/amp/set", ampNewVal)

        # set new frc if needed
        if (frcNewVal != self.hass.states.get(f"number.go_echarger_{serialNumber}_frc")):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/frc/set", frcNewVal)
        
        # set new psm if needed
        if (psmNewVal != self.hass.states.get(f"number.go_echarger_{serialNumber}_psm")):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"{goeTopicPrefix}/psm/set", psmNewVal)
        
        # set new targetCarChargePower if needed
        if (targetCarChargePower != self.hass.states.get(f"sensor.custom_targetCarChargePower")):
            self.hass.async_add_job(mqtt.async_publish, self.hass, f"custom/targetCarChargePower", targetCarChargePower)



    def calcTargetCarChargePower(self) -> int:
        availablePower = self.batteryPower - self.globalGrid + self.carChargePower
        targetCarChargePower = 0
        
        if self.chargePrio == "1": # prioritize battery
            targetCarChargePower = availablePower - self.maxBatteryChargePower
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300) and bigger than the allowed battery charge power
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower - self.globalGrid > self.maxBatteryChargePower:
                targetCarChargePower = 1380
        elif self.chargePrio == "2": # prioritize wallbox
            targetCarChargePower = availablePower
        elif self.chargePrio == "3": # split available power between battery and wallbox
            targetCarChargePower = availablePower/2
            # try not to feed the grid with more than 300W but also not drain energy from battery
            # IF targetCarChargePower between 300 (an allowed grid feed value) and 1380 (minimal possible charge for go-e wallbox)
            # AND PV produced energy is bigger than 1680 (1380 + 300)
            # SET targetCarChargePower to the minimal of 1380
            if 300 < targetCarChargePower < 1380 and 1680 < self.batteryPower - self.globalGrid:
                targetCarChargePower = 1380   
        elif self.chargePrio == "5": # use power from the grid to fast charge the car
            targetCarChargePower = availablePower + 27000
            self.instantUpdatePower = True
        else: # either OFF or unknown chargePrio
            targetCarChargePower = 0
            self.instantUpdatePower = True

        # TODO funky aufrundung um netzeinspeisung zu verhindern

        # TODO Glättung von targetCarChargePower

        # avoid a negativ targetCarChargePower
        return targetCarChargePower if targetCarChargePower > 0 else 0

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