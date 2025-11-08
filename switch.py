"""Switch platform - v5.0 CORRECTED - With proper error handling - NO Constant Mode"""

import logging

import asyncio

from typing import Any

from homeassistant.components.switch import SwitchEntity

from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant

from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"

DP_POWER = "1"

DP_NIGHT_MODE = "16"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,

) -> None:

    """Setup switch platform."""

    from .device_manager_v5_7_FINAL import PersistentDeviceManager

    data = hass.data[DOMAIN][config_entry.entry_id]

    device_id = data["device_id"]

    local_key = data["local_key"]

    ip_address = data.get("ip_address")

    protocol_version = data.get("protocol_version", "3.4")

    name = data["name"]

    device_manager = PersistentDeviceManager(device_id, local_key, ip_address, protocol_version)

    _LOGGER.info(f"Switch setup for {device_id}")

    switches = [
        KlartaHumeaPowerSwitch(hass, device_manager, f"{name} Power", DP_POWER),
        KlartaHueaNightModeSwitch(hass, device_manager, f"{name} Night Mode", DP_NIGHT_MODE),
    ]

    async_add_entities(switches)


class KlartaHueaBaseSwitch(SwitchEntity):

    """Base switch with error handling"""

    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, device_manager, name: str, dp: str):

        self._hass = hass

        self._name = name

        self._dp = dp

        self._device_manager = device_manager

        self._is_on = False

        self._available = True

    @property

    def name(self) -> str:

        return self._name

    @property

    def is_on(self) -> bool:

        return self._is_on

    @property

    def available(self) -> bool:

        return self._available

    async def async_turn_on(self, **kwargs: Any) -> None:

        try:

            result = await asyncio.wait_for(

                self._device_manager.set_value(self._dp, True),

                timeout=5.0

            )

            if result:

                self._is_on = True

                self._available = True

                self.async_write_ha_state()

            else:

                _LOGGER.warning(f"⚠️ {self._name} set_value returned False")

                self._available = False

        except asyncio.TimeoutError:

            _LOGGER.error(f"❌ {self._name} turn on timeout")

            self._available = False

        except Exception as e:

            _LOGGER.error(f"❌ {self._name} turn on failed: {e}")

            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:

        try:

            result = await asyncio.wait_for(

                self._device_manager.set_value(self._dp, False),

                timeout=5.0

            )

            if result:

                self._is_on = False

                self._available = True

                self.async_write_ha_state()

            else:

                _LOGGER.warning(f"⚠️ {self._name} set_value returned False")

                self._available = False

        except asyncio.TimeoutError:

            _LOGGER.error(f"❌ {self._name} turn off timeout")

            self._available = False

        except Exception as e:

            _LOGGER.error(f"❌ {self._name} turn off failed: {e}")

            self._available = False

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

                self._is_on = bool(data["dps"][self._dp])

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


class KlartaHumeaPowerSwitch(KlartaHueaBaseSwitch):

    """Power switch."""

    @property

    def unique_id(self) -> str:

        return f"klarta_humea_{self._device_manager.device_id}_power"


class KlartaHueaNightModeSwitch(KlartaHueaBaseSwitch):

    """Night Mode switch."""

    @property

    def unique_id(self) -> str:

        return f"klarta_humea_{self._device_manager.device_id}_night_mode"
