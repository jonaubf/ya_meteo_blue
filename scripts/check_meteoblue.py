#!/usr/bin/env python3
"""
Local check for Meteoblue API and response structure.
Run from project root: python scripts/check_meteoblue.py [--api-key KEY] [--lat 47.56] [--lon 7.57]

Use your own API key (from support@meteoblue.com). DEMOKEY may return 403.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    import aiohttp
except ImportError:
    print("Install aiohttp: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

API_BASE_URL = "https://my.meteoblue.com/packages/basic-1h_basic-day"
API_TIMEOUT = 30

PICTOCODE_HOURLY = {
    1: "sunny", 2: "sunny", 3: "sunny", 4: "partlycloudy", 5: "partlycloudy",
    6: "partlycloudy", 7: "partlycloudy", 8: "partlycloudy", 9: "partlycloudy",
    10: "lightning-rainy", 11: "lightning-rainy", 12: "lightning-rainy",
    13: "partlycloudy", 14: "partlycloudy", 15: "partlycloudy",
    16: "fog", 17: "fog", 18: "fog", 19: "cloudy", 20: "cloudy", 21: "cloudy",
    22: "cloudy", 23: "rainy", 24: "snowy", 25: "pouring", 26: "snowy",
    27: "lightning-rainy", 28: "lightning-rainy", 29: "snowy", 30: "lightning-rainy",
    31: "rainy", 32: "snowy", 33: "rainy", 34: "snowy", 35: "snowy-rainy",
}

PICTOCODE_DAILY = {
    1: "sunny", 2: "partlycloudy", 3: "partlycloudy", 4: "cloudy", 5: "fog",
    6: "rainy", 7: "rainy", 8: "lightning-rainy", 9: "snowy", 10: "snowy",
    11: "snowy-rainy", 12: "rainy", 13: "snowy", 14: "rainy", 15: "snowy",
    16: "rainy", 17: "snowy",
}


def normalize(data: dict) -> dict:
    """Same normalization as coordinator: ensure data_1h / data_day."""
    if "data_1h" in data or "data_day" in data:
        return data
    if "time" in data:
        return {"data_1h": data, "data_day": {}}
    return data


def safe(lst: list | None, i: int, default=None):
    if lst is None or i < 0 or i >= len(lst):
        return default
    v = lst[i]
    return default if v is None else v


async def run(api_key: str, lat: float, lon: float) -> None:
    url = f"{API_BASE_URL}?lat={lat}&lon={lon}&apikey={api_key}&format=json"
    print(f"Fetching: {url.replace(api_key, '***')}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as resp:
            if resp.status != 200:
                print(f"HTTP {resp.status}: {await resp.text()}")
                sys.exit(1)
            data = await resp.json()

    data = normalize(data)
    if "data_1h" not in data:
        print("Unexpected response (no data_1h after normalize):", list(data.keys()))
        sys.exit(1)

    h = data.get("data_1h") or {}
    d = data.get("data_day") or {}
    times_1h = h.get("time") or []
    times_day = d.get("time") or []

    print("\n--- Response structure ---")
    print("data_1h keys:", list(h.keys()))
    print("data_day keys:", list(d.keys()))
    print("Hourly intervals:", len(times_1h))
    print("Daily intervals:", len(times_day))

    if times_1h:
        i = 0
        cond = PICTOCODE_HOURLY.get(safe(h.get("pictocode"), i) or 0, "cloudy")
        print("\n--- Current (first hour) ---")
        print("  time:", safe(times_1h, i))
        print("  condition:", cond)
        print("  temperature:", safe(h.get("temperature"), i))
        print("  humidity:", safe(h.get("relativehumidity"), i))
        print("  pressure:", safe(h.get("sealevelpressure"), i))
        print("  windspeed:", safe(h.get("windspeed"), i))
        print("  precipitation:", safe(h.get("precipitation"), i))

    if times_day and len(times_day) >= 2:
        print("\n--- Daily forecast (first 2 days) ---")
        for i in range(min(2, len(times_day))):
            cond = PICTOCODE_DAILY.get(safe(d.get("pictocode"), i) or 0, "cloudy")
            print(f"  {safe(times_day, i)}: {cond}, max={safe(d.get('temperature_max'), i)}, min={safe(d.get('temperature_min'), i)}")

    print("\nOK – API and parsing work as expected.")


def main() -> None:
    p = argparse.ArgumentParser(description="Check Meteoblue API locally")
    p.add_argument("--api-key", default="DEMOKEY", help="API key (default: DEMOKEY; use your own if you get 403)")
    p.add_argument("--lat", type=float, default=47.56, help="Latitude")
    p.add_argument("--lon", type=float, default=7.57, help="Longitude")
    args = p.parse_args()
    asyncio.run(run(args.api_key, args.lat, args.lon))


if __name__ == "__main__":
    main()
