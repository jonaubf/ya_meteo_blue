"""Meteoblue Weather entity."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_CONDITION,
    PICTOCODE_TO_CONDITION_DAILY,
    PICTOCODE_TO_CONDITION_HOURLY,
)
from .coordinator import MeteoblueCoordinator

_LOGGER = logging.getLogger(__name__)


def _condition_from_pictocode_hourly(pictocode: int | None) -> str:
    """Map hourly pictocode (1-35) to HA condition."""
    if pictocode is None:
        return DEFAULT_CONDITION
    return PICTOCODE_TO_CONDITION_HOURLY.get(int(pictocode), DEFAULT_CONDITION)


def _condition_from_pictocode_daily(pictocode: int | None) -> str:
    """Map daily (iday) pictocode (1-17) to HA condition."""
    if pictocode is None:
        return DEFAULT_CONDITION
    return PICTOCODE_TO_CONDITION_DAILY.get(int(pictocode), DEFAULT_CONDITION)


def _safe_index(lst: list[Any] | None, index: int, default: Any = None) -> Any:
    """Return list[index] or default if missing or out of range."""
    if lst is None or index < 0 or index >= len(lst):
        return default
    val = lst[index]
    return default if val is None else val


def _parse_iso_datetime(s: str | None) -> datetime | None:
    """Parse API time string to datetime (UTC or naive)."""
    if not s:
        return None
    try:
        if " " in str(s):
            return datetime.strptime(str(s).strip(), "%Y-%m-%d %H:%M")
        return datetime.strptime(str(s).strip(), "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meteoblue weather from config entry."""
    coordinator: MeteoblueCoordinator = hass.data["meteoblue"][config_entry.entry_id]
    async_add_entities([MeteoblueWeatherEntity(coordinator, config_entry)])


class MeteoblueWeatherEntity(
    CoordinatorEntity[MeteoblueCoordinator], WeatherEntity
):
    """Meteoblue weather entity using coordinator data."""

    _attr_attribution = "Data provided by Meteoblue"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self, coordinator: MeteoblueCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Meteoblue"
        self._attr_unique_id = f"{entry.entry_id}-weather"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_current_from_coordinator()
        super()._handle_coordinator_update()

    def _update_current_from_coordinator(self) -> None:
        """Set current state from coordinator data."""
        data = self.coordinator.data
        if not data:
            return
        h = data.get("data_1h") or {}
        times = h.get("time") or []
        if not times:
            return
        idx = 0
        pictocode = _safe_index(h.get("pictocode"), idx)
        is_daylight = _safe_index(h.get("isdaylight"), idx, 1)
        self._attr_native_temperature = _safe_index(h.get("temperature"), idx)
        self._attr_humidity = _safe_index(h.get("relativehumidity"), idx)
        self._attr_native_pressure = _safe_index(h.get("sealevelpressure"), idx)
        self._attr_native_wind_speed = _safe_index(h.get("windspeed"), idx)
        self._attr_native_wind_gust_speed = _safe_index(h.get("windgusts"), idx)
        self._attr_native_wind_bearing = _safe_index(h.get("winddirection"), idx)
        self._attr_condition = _condition_from_pictocode_hourly(pictocode)
        if pictocode == 1 and not is_daylight:
            self._attr_condition = "clear-night"
        self._attr_uv_index = None
        day_data = data.get("data_day") or {}
        if day_data and (day_data.get("time") or []) and (day_data.get("uvindex") or []):
            self._attr_uv_index = _safe_index(day_data["uvindex"], 0)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and bool(self.coordinator.data)
            and bool((self.coordinator.data or {}).get("data_1h"))
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._update_current_from_coordinator()

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data = self.coordinator.data
        if not data:
            return None
        day_data = data.get("data_day") or {}
        times = day_data.get("time") or []
        if not times:
            return None
        forecasts: list[Forecast] = []
        n = len(times)
        for i in range(n):
            dt = _parse_iso_datetime(_safe_index(times, i))
            if not dt:
                continue
            condition = _condition_from_pictocode_daily(
                _safe_index(day_data.get("pictocode"), i)
            )
            temp_high = _safe_index(day_data.get("temperature_max"), i)
            temp_low = _safe_index(day_data.get("temperature_min"), i)
            precip = _safe_index(
                day_data.get("precipitation_sum") or day_data.get("precipitation"), i, 0.0
            )
            precip_prob = _safe_index(day_data.get("precipitationprobability_mean"), i)
            wind_speed = _safe_index(day_data.get("windspeed_mean"), i)
            wind_bearing = _safe_index(day_data.get("winddirection_dominant"), i)
            humidity = _safe_index(day_data.get("relativehumidity_mean"), i)
            forecasts.append({
                "datetime": dt.isoformat() if dt else None,
                "condition": condition,
                "temperature": temp_high,
                "templow": temp_low,
                "precipitation": precip,
                "precipitation_probability": precip_prob,
                "wind_speed": wind_speed,
                "wind_bearing": wind_bearing,
                "humidity": humidity,
            })
        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        data = self.coordinator.data
        if not data:
            return None
        h = data.get("data_1h") or {}
        times = h.get("time") or []
        if not times:
            return None
        forecasts: list[Forecast] = []
        n = len(times)
        for i in range(n):
            dt = _parse_iso_datetime(_safe_index(times, i))
            if not dt:
                continue
            condition = _condition_from_pictocode_hourly(
                _safe_index(h.get("pictocode"), i)
            )
            temp = _safe_index(h.get("temperature"), i)
            precip = _safe_index(h.get("precipitation"), i, 0.0)
            precip_prob = _safe_index(h.get("precipitationprobability"), i)
            wind_speed = _safe_index(h.get("windspeed"), i)
            wind_bearing = _safe_index(h.get("winddirection"), i)
            humidity = _safe_index(h.get("relativehumidity"), i)
            forecasts.append({
                "datetime": dt.isoformat() if dt else None,
                "condition": condition,
                "temperature": temp,
                "templow": None,
                "precipitation": precip,
                "precipitation_probability": precip_prob,
                "wind_speed": wind_speed,
                "wind_bearing": wind_bearing,
                "humidity": humidity,
            })
        return forecasts
