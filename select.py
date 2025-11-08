"""Select platform - Fan Speed selector"""

import logging
import asyncio
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"

DP_FAN_SPEED = "103"

FAN_SPEED_OPTIONS = ["Low_speed", "Medium_speed", "High_speed", "Turbo_speed"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup select platform."""

    from .device_manager_v5_7_FINAL import PersistentDeviceManager

    data = hass.data[DOMAIN][config_entry.entry_id]
    device_manager = PersistentDeviceManager(
        data["device_id"],
        data["local_key"],
        data.get("ip_address"),
        data.get("protocol_version", "3.4")
    )

    name = data["name"]
    _LOGGER.info(f"Select setup for {data['device_id']}")

    async_add_entities([
        KlartaHueaFanSpeed(hass, device_manager, f"{name} Fan Speed", DP_FAN_SPEED),
    ])


class KlartaHueaFanSpeed(SelectEntity):
    """Fan Speed selector"""

    _attr_should_poll = True
    _attr_options = FAN_SPEED_OPTIONS

    def __init__(self, hass: HomeAssistant, device_manager, name: str, dp: str):
        self._hass = hass
        self._name = name
        self._dp = dp
        self._device_manager = device_manager
        self._current_option = "Low_speed"
        self._available = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f"klarta_humea_{self._device_manager.device_id}_fan_speed"

    @property
    def current_option(self) -> Optional[str]:
        return self._current_option

    @property
    def available(self) -> bool:
        return self._available

    async def async_select_option(self, option: str) -> None:
        if option not in FAN_SPEED_OPTIONS:
            _LOGGER.error(f"❌ Invalid fan speed: {option}")
            return

        try:
            result = await asyncio.wait_for(
                self._device_manager.set_value(self._dp, option),
                timeout=5.0
            )

            if result:
                self._current_option = option
                self._available = True
                self.async_write_ha_state()
                _LOGGER.info(f"✅ Fan speed set to {option}")
            else:
                _LOGGER.warning(f"⚠️ Fan speed set_value returned False")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Fan speed set timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Fan speed set failed: {e}")
            self._available = False

    async def async_update(self) -> None:
        try:
            data = await asyncio.wait_for(
                self._device_manager.get_status(),
                timeout=5.0
            )

            if not data or "dps" not in data:
                _LOGGER.warning(f"⚠️ Fan Speed received invalid data")
                self._available = False
                return

            if self._dp in data["dps"]:
                current_value = str(data["dps"][self._dp])
                if current_value in FAN_SPEED_OPTIONS:
                    self._current_option = current_value
                    self._available = True
                else:
                    _LOGGER.warning(f"⚠️ Fan Speed unknown value: {current_value}")
                    self._available = False
            else:
                _LOGGER.warning(f"⚠️ Fan Speed DP not in response")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Fan Speed update timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Fan Speed update failed: {e}")
            self._available = False
