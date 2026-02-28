"""DataUpdateCoordinator for Meteoblue."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from urllib.parse import quote

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    API_TIMEOUT_SECONDS,
    CONF_API_KEY,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_coordinates(entry: ConfigEntry) -> tuple[float, float]:
    """Return (lat, lon) from config entry data or options."""
    opts = entry.options or {}
    data = entry.data or {}
    lat = opts.get(CONF_LATITUDE) or data.get(CONF_LATITUDE)
    lon = opts.get(CONF_LONGITUDE) or data.get(CONF_LONGITUDE)
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    return 0.0, 0.0


async def _fetch_meteoblue(
    api_key: str,
    lat: float,
    lon: float,
    session: aiohttp.ClientSession,
    time_zone: str | None = None,
) -> dict[str, Any]:
    """Fetch basic-1h and basic-day data in one request."""
    url = f"{API_BASE_URL}?lat={lat}&lon={lon}&apikey={api_key}&format=json"
    if time_zone:
        url += f"&tz={quote(time_zone, safe='')}"
    async with session.get(
        url, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT_SECONDS)
    ) as resp:
        resp.raise_for_status()
        return await resp.json()


class MeteoblueCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that fetches Meteoblue data once and provides it to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES),
            always_update=False,
        )
        self._entry = entry
        self._api_key = entry.data.get(CONF_API_KEY, "")

    def _lat_lon(self) -> tuple[float, float]:
        """Return current coordinates (from options or config)."""
        return _get_coordinates(self._entry)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meteoblue API."""
        lat, lon = self._lat_lon()
        if not self._api_key or (lat == 0.0 and lon == 0.0):
            raise UpdateFailed("Meteoblue not configured (missing API key or coordinates)")

        try:
            time_zone = self.hass.config.time_zone
            async with aiohttp.ClientSession() as session:
                data = await _fetch_meteoblue(
                    self._api_key, lat, lon, session, time_zone=time_zone
                )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"API request failed: {err}") from err

        # Normalize: API can return data_1h / data_day when both packages requested
        if "data_1h" not in data and "data_day" not in data:
            # Single-resolution response may be at top level
            if "time" in data:
                data = {"data_1h": data, "data_day": {}}
            else:
                raise UpdateFailed("Unexpected API response format")

        return data
