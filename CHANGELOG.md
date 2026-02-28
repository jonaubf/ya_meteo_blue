# Changelog

All notable changes to this integration are documented here. The version in the repo matches `custom_components/meteoblue/manifest.json`.

## [1.0.0] – 2026-02-28

### Added

- Initial release
- Weather entity with current conditions and daily/hourly forecast
- Config flow: API key, optional coordinates, “Use Home Assistant location”
- Options flow to change location without re-entering API key
- Single API request for `basic-1h` and `basic-day` data
- Timezone support: API uses HA timezone; current conditions use the hourly slot for “now” (not midnight)
- Entity attributes: `latitude`, `longitude`, `current_conditions_time` for debugging

### Fixed

- Current temperature now matches the Meteoblue website (same hour slot used for “current”)
