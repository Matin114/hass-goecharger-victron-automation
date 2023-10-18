"""Definitions for go-eCharger numbers exposed via MQTT."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription
from homeassistant.const import ELECTRIC_CURRENT_AMPERE, ENERGY_WATT_HOUR, TIME_SECONDS, POWER_WATT
from homeassistant.helpers.entity import EntityCategory

from . import GoEChargerEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass
class GoEChargerNumberEntityDescription(
    GoEChargerEntityDescription, NumberEntityDescription
):
    """Number entity description for go-eCharger."""

    domain: str = "number"

VICTRON_NUMBERS: tuple[GoEChargerNumberEntityDescription, ...] = (
    GoEChargerNumberEntityDescription(
        key="targetCarPowerAmount",
        name="Wh to charge the car with",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.ENERGY,
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=50000,
        native_min_value=0,
        native_step=100,
        isVictron=True
    ),
    GoEChargerNumberEntityDescription(
        key="manualCarChargePower",
        name="Manual Power for car charging",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=POWER_WATT,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=22000,
        native_min_value=1380,
        native_step=230,
        isVictron=True
    ),
)

GOE_NUMBERS: tuple[GoEChargerNumberEntityDescription, ...] = (
    GoEChargerNumberEntityDescription(
        key="ama",
        name="Maximum current limit",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
    ),
    GoEChargerNumberEntityDescription(
        key="amp",
        name="Requested current",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=32,
        native_min_value=6,
        native_step=1,
    ),
    GoEChargerNumberEntityDescription(
        key="ate",
        name="Automatic stop energy",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.ENERGY,
        native_unit_of_measurement=ENERGY_WATT_HOUR,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=100000,
        native_min_value=1,
        native_step=1,
    ),
    GoEChargerNumberEntityDescription(
        key="att",
        name="Automatic stop time",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        native_unit_of_measurement=TIME_SECONDS,
        entity_registry_enabled_default=True,
        disabled=False,
        native_max_value=86400,
        native_min_value=60,
        native_step=1,
    ),
)
