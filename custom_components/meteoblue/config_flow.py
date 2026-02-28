"""Config flow for the Meteoblue integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    API_BASE_URL,
    API_TIMEOUT_SECONDS,
    CONF_API_KEY,
    CONF_USE_HOME_COORDINATES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _async_validate_api_key(
    hass: HomeAssistant, api_key: str, lat: float, lon: float
) -> str | None:
    """Validate API key by making a test request. Returns error message or None."""
    import aiohttp

    url = f"{API_BASE_URL}?lat={lat}&lon={lon}&apikey={api_key}&format=json"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT_SECONDS)
            ) as resp:
                if resp.status == 401:
                    return "invalid_api_key"
                if resp.status != 200:
                    return "cannot_connect"
                return None
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("API validation failed: %s", exc)
        return "cannot_connect"


class MeteoblueConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteoblue."""

    VERSION = 1

    @staticmethod
    async def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "MeteoblueOptionsFlowHandler":
        """Return the options flow handler."""
        return MeteoblueOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            use_home = user_input.get(CONF_USE_HOME_COORDINATES, True)

            if not api_key:
                errors["base"] = "invalid_api_key"
            else:
                if use_home:
                    lat = self.hass.config.latitude
                    lon = self.hass.config.longitude
                else:
                    try:
                        lat = float(user_input.get(CONF_LATITUDE))
                        lon = float(user_input.get(CONF_LONGITUDE))
                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            errors["base"] = "invalid_coordinates"
                    except (TypeError, ValueError):
                        errors["base"] = "invalid_coordinates"
                        lat = self.hass.config.latitude
                        lon = self.hass.config.longitude

                if not errors:
                    err = await _async_validate_api_key(self.hass, api_key, lat, lon)
                    if err:
                        errors["base"] = err
                    else:
                        self._data = {
                            CONF_API_KEY: api_key,
                            CONF_LATITUDE: lat,
                            CONF_LONGITUDE: lon,
                        }
                        return self.async_create_entry(title="Meteoblue", data=self._data)

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_USE_HOME_COORDINATES, default=True): bool,
                vol.Optional(CONF_LATITUDE): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class MeteoblueOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Meteoblue options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    @callback
    def _current_lat_lon(self) -> tuple[float, float]:
        """Return current config latitude and longitude."""
        return (
            self.config_entry.data.get(
                CONF_LATITUDE, self.config_entry.options.get(CONF_LATITUDE)
            ) or self.hass.config.latitude,
            self.config_entry.data.get(
                CONF_LONGITUDE, self.config_entry.options.get(CONF_LONGITUDE)
            ) or self.hass.config.longitude,
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            use_home = user_input.get(CONF_USE_HOME_COORDINATES, True)
            if use_home:
                lat = self.hass.config.latitude
                lon = self.hass.config.longitude
            else:
                lat = user_input.get(CONF_LATITUDE)
                lon = user_input.get(CONF_LONGITUDE)
            return self.async_create_entry(
                title="",
                data={
                    CONF_USE_HOME_COORDINATES: use_home,
                    CONF_LATITUDE: lat,
                    CONF_LONGITUDE: lon,
                },
            )

        lat, lon = self._current_lat_lon()
        use_home = (
            lat == self.hass.config.latitude and lon == self.hass.config.longitude
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USE_HOME_COORDINATES, default=use_home): bool,
                    vol.Optional(CONF_LATITUDE, default=lat): vol.Coerce(float),
                    vol.Optional(CONF_LONGITUDE, default=lon): vol.Coerce(float),
                }
            ),
        )
