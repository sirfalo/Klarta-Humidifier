"""Humidifier platform - v5.0 CORRECTED - With proper error handling"""

import logging
import asyncio
import re
from typing import Optional

from homeassistant.components.humidifier import HumidifierEntity, HumidifierDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"

DP_POWER = "1"
DP_CURRENT_HUMIDITY = "14"
DP_TARGET_HUMIDITY = "101"

MIN_TARGET_HUMIDITY = 40
MAX_TARGET_HUMIDITY = 75


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Setup humidifier."""
    from .device_manager_v5_7_FINAL import PersistentDeviceManager

    data = hass.data[DOMAIN][config_entry.entry_id]
    device_manager = PersistentDeviceManager(
        data["device_id"],
        data["local_key"],
        data.get("ip_address"),
        data.get("protocol_version", "3.4")
    )

    _LOGGER.info(f"Humidifier setup for {data['device_id']}")
    async_add_entities([KlartaHumeaHumidifier(hass, device_manager, data["name"])])


class KlartaHumeaHumidifier(HumidifierEntity):
    """Humidifier with error handling"""

    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_min_humidity = MIN_TARGET_HUMIDITY
    _attr_max_humidity = MAX_TARGET_HUMIDITY
    _attr_target_humidity = 50
    _attr_available_modes = ["normal"]
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, device_manager, name: str):
        self._hass = hass
        self._name = name
        self._device_manager = device_manager
        self._is_on = False
        self._current_humidity = 50
        self._target_humidity = 50
        self._available = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f"klarta_humea_{self._device_manager.device_id}"

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def current_humidity(self) -> Optional[int]:
        return self._current_humidity

    @property
    def target_humidity(self) -> Optional[int]:
        return self._target_humidity

    @property
    def available(self) -> bool:
        return self._available

    async def async_turn_on(self, **kwargs) -> None:
        try:
            result = await asyncio.wait_for(
                self._device_manager.set_value(DP_POWER, True),
                timeout=5.0
            )

            if result:
                self._is_on = True
                self._available = True
                self.async_write_ha_state()
            else:
                _LOGGER.warning(f"⚠️ Humidifier turn on returned False")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Humidifier turn on timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Humidifier turn on failed: {e}")
            self._available = False

    async def async_turn_off(self, **kwargs) -> None:
        try:
            result = await asyncio.wait_for(
                self._device_manager.set_value(DP_POWER, False),
                timeout=5.0
            )

            if result:
                self._is_on = False
                self._available = True
                self.async_write_ha_state()
            else:
                _LOGGER.warning(f"⚠️ Humidifier turn off returned False")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Humidifier turn off timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Humidifier turn off failed: {e}")
            self._available = False

    async def async_set_humidity(self, humidity: int) -> None:
        humidity = max(MIN_TARGET_HUMIDITY, min(MAX_TARGET_HUMIDITY, humidity))

        try:
            target_value = f"{humidity}RH"
            result = await asyncio.wait_for(
                self._device_manager.set_value(DP_TARGET_HUMIDITY, target_value),
                timeout=5.0
            )

            if result:
                self._target_humidity = humidity
                self._available = True
                self.async_write_ha_state()
            else:
                _LOGGER.warning(f"⚠️ Set humidity returned False")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Set humidity timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Set humidity failed: {e}")
            self._available = False

    async def async_update(self) -> None:
        try:
            data = await asyncio.wait_for(
                self._device_manager.get_status(),
                timeout=5.0
            )

            if not data or "dps" not in data:
                _LOGGER.warning(f"⚠️ Humidifier received invalid data: {data}")
                self._available = False
                return

            dps = data["dps"]
            self._available = True

            if DP_POWER in dps:
                self._is_on = bool(dps[DP_POWER])

            if DP_CURRENT_HUMIDITY in dps:
                self._current_humidity = int(dps[DP_CURRENT_HUMIDITY])

            if DP_TARGET_HUMIDITY in dps:
                match = re.search(r'(\d+)', str(dps[DP_TARGET_HUMIDITY]))
                if match:
                    self._target_humidity = int(match.group(1))

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ Humidifier update timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ Humidifier update failed: {e}")
            self._available = False
