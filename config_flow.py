"""Config flow for BBS Status integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    
    url = f"http://{host}:{port}/status"
    
    # Retry up to 10 times with exponential backoff
    for attempt in range(10):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "status" in result:
                            return {"title": f"BBS Status - {host}:{port}"}
                        else:
                            raise CannotConnect("Invalid response format")
                    else:
                        if attempt == 9:  # Last attempt
                            raise CannotConnect(f"HTTP {response.status}")
                        continue  # Retry on HTTP error
        except aiohttp.ClientError as err:
            if attempt == 9:  # Last attempt
                raise CannotConnect(f"Connection error after 10 attempts: {err}")
            continue  # Retry on connection error
        except Exception as err:
            if attempt == 9:  # Last attempt
                raise CannotConnect(f"Unexpected error after 10 attempts: {err}")
            continue  # Retry on other errors
        
        # Wait before retry (exponential backoff)
        if attempt < 9:
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, etc.
    
    raise CannotConnect("Failed to connect after 10 attempts")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BBS Status."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if not errors:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
