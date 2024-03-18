"""Definitions for go-eCharger / victron input_text."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.text import TextEntityDescription
from homeassistant.helpers.entity import EntityCategory

from . import GoEChargerEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass
class GoEChargerInputTextEntityDescription(
    GoEChargerEntityDescription, TextEntityDescription
):
    """input_text entity description for go-eCharger."""

    domain: str = "input_text"

VICTRON_RESTORE_INPUT_TEXT: tuple[GoEChargerInputTextEntityDescription, ...] = (
    GoEChargerInputTextEntityDescription(
        key="ledColorOff",
        name="Color OFF",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorPrioBattery",
        name="Color Prio Battery",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorPrioWallbox",
        name="Color Prio Wallbox",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColor50_50",
        name="Color 50/50",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorManualToSOC",
        name="Color Manual to SOC",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorGrid",
        name="Color From Grid",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorManual",
        name="Color Manual",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorAutomatic",
        name="Color Automatic",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
    GoEChargerInputTextEntityDescription(
        key="ledColorManualAmount",
        name="Color Manual Amount",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        entity_registry_enabled_default=True,
        disabled=False,
        pattern="^#([A-Fa-f0-9]{6})$",
        isVictron=True,
    ),
)