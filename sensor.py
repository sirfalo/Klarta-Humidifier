"""Sensor platform - v5.0 CORRECTED - With proper error handling"""

import logging
import asyncio
from typing import Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"

DP_CURRENT_HUMIDITY = "14"
DP_TEMPERATURE = "10"
DP_WATER_LEVEL = "102"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensors."""
    from .device_manager_v5_7_FINAL import PersistentDeviceManager

    data = hass.data[DOMAIN][config_entry.entry_id]
    device_manager = PersistentDeviceManager(
        data["device_id"],
        data["local_key"],
        data.get("ip_address"),
        data.get("protocol_version", "3.4")
    )

    _LOGGER.info(f"Sensor setup for {data['device_id']}")
    name = data["name"]

    async_add_entities([
        HumiditySensor(device_manager, f"{name} Current Humidity"),
        TemperatureSensor(device_manager, f"{name} Temperature"),
        WaterLevelSensor(device_manager, f"{name} Water Level"),
    ])


class BaseKlartaSensor(SensorEntity):
    """Base sensor with error handling"""

    _attr_should_poll = True

    def __init__(self, device_manager, name: str, dp: str):
        self._device_manager = device_manager
        self._name = name
        self._dp = dp
        self._native_value = None
        self._available = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f"klarta_humea_{self._device_manager.device_id}_{self._dp}"

    @property
    def native_value(self):
        return self._native_value

    @property
    def available(self) -> bool:
        return self._available

    async def async_update(self) -> None:
        try:
            data = await asyncio.wait_for(
                self._device_manager.get_status(),
                timeout=5.0
            )

            if not data or "dps" not in data:
                _LOGGER.warning(f"⚠️ {self._name} received invalid data: {data}")
                self._available = False
                return

            if self._dp in data["dps"]:
                self._native_value = self._process_value(data["dps"][self._dp])
                self._available = True
            else:
                _LOGGER.warning(f"⚠️ {self._name} DP {self._dp} not in response")
                self._available = False

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ {self._name} update timeout")
            self._available = False
        except Exception as e:
            _LOGGER.error(f"❌ {self._name} update failed: {e}")
            self._available = False

    def _process_value(self, value):
        """Process raw value - override in subclasses."""
        return value


class HumiditySensor(BaseKlartaSensor):
    """Humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    def __init__(self, device_manager, name: str):
        super().__init__(device_manager, name, DP_CURRENT_HUMIDITY)

    def _process_value(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class TemperatureSensor(BaseKlartaSensor):
    """Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, device_manager, name: str):
        super().__init__(device_manager, name, DP_TEMPERATURE)

    def _process_value(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class WaterLevelSensor(BaseKlartaSensor):
    """Water level sensor."""

    def __init__(self, device_manager, name: str):
        super().__init__(device_manager, name, DP_WATER_LEVEL)

    def _process_value(self, value):
        return str(value)
