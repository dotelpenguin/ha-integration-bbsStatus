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
        for attempt in range(10):
            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                if "status" in data:
                                    return data["status"]
                                else:
                                    if attempt == 9:  # Last attempt
                                        raise UpdateFailed("Invalid response format")
                                    continue  # Retry on invalid format
                            else:
                                if attempt == 9:  # Last attempt
                                    raise UpdateFailed(f"HTTP {response.status}")
                                continue  # Retry on HTTP error
            except aiohttp.ClientError as err:
                if attempt == 9:  # Last attempt
                    raise UpdateFailed(f"Connection error after 10 attempts: {err}")
                continue  # Retry on connection error
            except Exception as err:
                if attempt == 9:  # Last attempt
                    raise UpdateFailed(f"Unexpected error after 10 attempts: {err}")
                continue  # Retry on other errors
            
            # Wait before retry (exponential backoff)
            if attempt < 9:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, etc.
        
        raise UpdateFailed("Failed to connect after 10 attempts")


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
