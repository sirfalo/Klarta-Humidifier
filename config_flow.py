"""Klarta Humea Integration - Config Flow - v4.0 FINAL"""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "klarta_humea"


class KlartaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Klarta Humea."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input["device_id"])
            self._abort_if_unique_id_configured()
            
            _LOGGER.info(f"Creating config entry for {user_input['name']}")
            
            return self.async_create_entry(
                title=user_input["name"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Klarta Humea"): cv.string,
                    vol.Required("device_id"): cv.string,
                    vol.Required("local_key"): cv.string,
                    vol.Required("ip_address"): cv.string,
                    vol.Optional("protocol_version", default="3.4"): cv.string,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return KlartaOptionsFlow(config_entry)


class KlartaOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Initialize options flow."""
        return self.async_show_form(step_id="init")
