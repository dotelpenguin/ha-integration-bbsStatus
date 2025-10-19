"""Sensor platform for BBS Status integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BBS Status sensor based on a config entry."""
    coordinator = BBSStatusDataUpdateCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([BBSStatusSensor(coordinator)])


class BBSStatusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the BBS Status API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = config_entry
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.scan_interval = config_entry.data[CONF_SCAN_INTERVAL]
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        url = f"http://{self.host}:{self.port}/status"
        
        # Retry up to 10 times with exponential backoff
        last_error = None
        for attempt in range(10):
            try:
                _LOGGER.debug(f"Fetching BBS Status data (attempt {attempt + 1}/10): {url}")
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                if "status" in data:
                                    _LOGGER.debug(f"Successfully fetched BBS Status data from: {url}")
                                    return data["status"]
                                else:
                                    last_error = f"Invalid response format: missing 'status' key in response from {url}"
                                    _LOGGER.warning(f"Invalid response format on attempt {attempt + 1} for {url}: {last_error}")
                                    if attempt == 9:  # Last attempt
                                        raise UpdateFailed(last_error)
                                    continue  # Retry on invalid format
                            else:
                                last_error = f"HTTP {response.status}: {response.reason} from {url}"
                                _LOGGER.warning(f"HTTP error on attempt {attempt + 1} for {url}: {last_error}")
                                if attempt == 9:  # Last attempt
                                    raise UpdateFailed(last_error)
                                continue  # Retry on HTTP error
            except aiohttp.ClientError as err:
                last_error = f"Connection error to {url}: {err}"
                _LOGGER.warning(f"Connection error on attempt {attempt + 1} for {url}: {last_error}")
                if attempt == 9:  # Last attempt
                    raise UpdateFailed(f"Connection failed after 10 attempts to {url}. Last error: {last_error}")
                continue  # Retry on connection error
            except Exception as err:
                last_error = f"Unexpected error accessing {url}: {err}"
                _LOGGER.warning(f"Unexpected error on attempt {attempt + 1} for {url}: {last_error}")
                if attempt == 9:  # Last attempt
                    raise UpdateFailed(f"Unexpected error after 10 attempts accessing {url}. Last error: {last_error}")
                continue  # Retry on other errors
            
            # Wait before retry (exponential backoff)
            if attempt < 9:
                wait_time = 2 ** attempt
                _LOGGER.debug(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        raise UpdateFailed(f"Failed to fetch data after 10 attempts. Last error: {last_error}")


class BBSStatusSensor(SensorEntity):
    """Representation of a BBS Status sensor."""

    def __init__(self, coordinator: BBSStatusDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"BBS Status - {self.coordinator.host}:{self.coordinator.port}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"bbs_status_{self.coordinator.host}_{self.coordinator.port}"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "Unknown"
        
        used_instances = self.coordinator.data.get("used_instances", 0)
        num_instances = self.coordinator.data.get("num_instances", 0)
        
        if used_instances == 0:
            return "All Available"
        elif used_instances < num_instances:
            return f"{used_instances}/{num_instances} Used"
        else:
            return "All Busy"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        
        return {
            "num_instances": self.coordinator.data.get("num_instances", 0),
            "used_instances": self.coordinator.data.get("used_instances", 0),
            "available_instances": self.coordinator.data.get("num_instances", 0) - self.coordinator.data.get("used_instances", 0),
            "lines": self.coordinator.data.get("lines", []),
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if not self.coordinator.data:
            return "mdi:help-circle"
        
        used_instances = self.coordinator.data.get("used_instances", 0)
        num_instances = self.coordinator.data.get("num_instances", 0)
        
        if used_instances == 0:
            return "mdi:check-circle"
        elif used_instances < num_instances:
            return "mdi:alert-circle"
        else:
            return "mdi:close-circle"

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    async def async_update(self) -> None:
        """Update the sensor."""
        await self.coordinator.async_request_refresh()
