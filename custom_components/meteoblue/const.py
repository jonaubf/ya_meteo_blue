"""Constants for the Meteoblue integration."""

DOMAIN = "meteoblue"

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_USE_HOME_COORDINATES = "use_home_coordinates"

DEFAULT_UPDATE_INTERVAL_MINUTES = 30
API_BASE_URL = "https://my.meteoblue.com/packages/basic-1h_basic-day"
API_TIMEOUT_SECONDS = 30

# Meteoblue hourly pictocode (1-35) to Home Assistant condition
# https://content.meteoblue.com/en/research-education/specifications/standards/symbols-and-pictograms
PICTOCODE_TO_CONDITION_HOURLY = {
    1: "sunny",  # Clear, cloudless
    2: "sunny",
    3: "sunny",
    4: "partlycloudy",
    5: "partlycloudy",
    6: "partlycloudy",
    7: "partlycloudy",
    8: "partlycloudy",
    9: "partlycloudy",
    10: "lightning-rainy",
    11: "lightning-rainy",
    12: "lightning-rainy",
    13: "partlycloudy",  # Clear but hazy
    14: "partlycloudy",
    15: "partlycloudy",
    16: "fog",
    17: "fog",
    18: "fog",
    19: "cloudy",
    20: "cloudy",
    21: "cloudy",
    22: "cloudy",  # Overcast
    23: "rainy",
    24: "snowy",
    25: "pouring",
    26: "snowy",
    27: "lightning-rainy",
    28: "lightning-rainy",
    29: "snowy",
    30: "lightning-rainy",
    31: "rainy",
    32: "snowy",
    33: "rainy",
    34: "snowy",
    35: "snowy-rainy",
}

# Meteoblue daily (iday) pictocode (1-17) to Home Assistant condition
PICTOCODE_TO_CONDITION_DAILY = {
    1: "sunny",
    2: "partlycloudy",
    3: "partlycloudy",
    4: "cloudy",
    5: "fog",
    6: "rainy",
    7: "rainy",
    8: "lightning-rainy",
    9: "snowy",
    10: "snowy",
    11: "snowy-rainy",
    12: "rainy",
    13: "snowy",
    14: "rainy",
    15: "snowy",
    16: "rainy",
    17: "snowy",
}

DEFAULT_CONDITION = "cloudy"
