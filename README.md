# Meteoblue Weather for Home Assistant

Home Assistant integration that adds a weather entity using the [Meteoblue](https://www.meteoblue.com) Forecast API. Current conditions and daily/hourly forecasts are fetched in a single API call.

## Features

- **Single API request** – Fetches current weather plus hourly and daily forecast using the `basic-1h_basic-day` package
- **Config flow** – Set up via UI: API key and optional coordinates
- **Home or custom location** – Use your Home Assistant home coordinates or enter latitude/longitude
- **Options** – Change location later without re-entering the API key
- **Forecasts** – Daily and hourly forecast support for the weather entity

## Installation

### HACS (recommended)

1. Open **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Add: `https://github.com/jonaubf/ya_meteo_blue`
3. Choose category **Integration** and add
4. Find **Meteoblue** in the list and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/meteoblue` folder into your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. **Settings** → **Devices & services** → **Add integration**
2. Search for **Meteoblue** and select it
3. Enter your **API key** (get a free key from [meteoblue.com](https://www.meteoblue.com) or contact support@meteoblue.com; free tier includes 100,000 requests/year)
4. Choose **Use Home Assistant location** or enter custom **Latitude** and **Longitude**
5. Submit

After setup, a **Meteoblue** weather entity appears. You can change the location later via the integration’s **Configure** option.

## Requirements

- Home Assistant 2024.x or newer
- Meteoblue API key

## License

MIT License – see [LICENSE](LICENSE).
