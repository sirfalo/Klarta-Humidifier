"""Klarta Humea Integration - v4.0 FINAL - With SELECT for Fan Speed"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"

PLATFORMS = [
    Platform.SWITCH,
    Platform.HUMIDIFIER,
    Platform.SENSOR,
    Platform.SELECT,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up klarta_humea from configuration.yaml."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup entry."""

    _LOGGER.info("=" * 60)
    _LOGGER.info("Klarta Humea v4.0 FINAL - Persistent Device Manager")
    _LOGGER.info("=" * 60)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    _LOGGER.info(f"Setting up: {entry.data.get('name', 'Klarta Humea')}")
    _LOGGER.info(f"Device ID: {entry.data.get('device_id')}")
    _LOGGER.info(f"IP Address: {entry.data.get('ip_address')}")
    _LOGGER.info(f"Protocol: {entry.data.get('protocol_version', '3.4')}")
    _LOGGER.info("-" * 60)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""

    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if result:
        hass.data[DOMAIN].pop(entry.entry_id)

    return result
