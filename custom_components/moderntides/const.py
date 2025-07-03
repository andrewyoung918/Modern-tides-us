"""Constants for the Modern Tides integration."""

DOMAIN = "moderntides"
PLATFORMS = ["sensor", "camera"]

# Configuration options
CONF_STATIONS = "stations"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_UPDATE_INTERVAL = "update_interval"

# Update intervals in minutes
DEFAULT_UPDATE_INTERVAL = 360
INTERVALS = {
    "30min": 30,
    "1h": 60,
    "3h": 180,
    "6h": 360,
    "12h": 720,
    "24h": 1440
}

# API endpoints
API_BASE_URL = "https://ideihm.covam.es/api-ihm/getmarea"
API_STATION_LIST = f"{API_BASE_URL}?request=getlist&format=json"
API_DAY_TIDES = f"{API_BASE_URL}?request=gettide&format=json&id={{station_id}}&date={{date}}"
API_MONTH_TIDES = f"{API_BASE_URL}?request=gettide&format=json&id={{station_id}}&month={{month}}"
