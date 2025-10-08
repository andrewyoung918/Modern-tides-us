"""Constants for the Modern Tides integration."""

DOMAIN = "modern_tides_us"
PLATFORMS = ["sensor", "camera"]

# Metadata to ensure Home Assistant finds the integration
INTEGRATION_TITLE = "Modern Tides"
INTEGRATION_DOMAIN = DOMAIN

# Configuration options
CONF_STATIONS = "stations"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_UPDATE_INTERVAL = "update_interval"

# Plot generation settings
PLOT_DAYS_TO_GENERATE = [1, 2, 3, 4, 5, 6, 7]  # Generate plots for these day ranges

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

# NOAA CO-OPS API endpoints
API_BASE_URL = "https://tidesandcurrents.noaa.gov/api/datagetter"
API_STATION_LIST_URL = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions"
API_PREDICTIONS = f"{API_BASE_URL}?product=predictions&application=NOS.COOPS.TAC.WL&datum=MLLW&station={{station_id}}&time_zone=lst_ldt&units=english&format=json&begin_date={{begin_date}}&end_date={{end_date}}&interval=6"
API_HILO_PREDICTIONS = f"{API_BASE_URL}?product=predictions&application=NOS.COOPS.TAC.WL&datum=MLLW&station={{station_id}}&time_zone=lst_ldt&units=english&format=json&begin_date={{begin_date}}&end_date={{end_date}}&interval=hilo"

# Default station - Provincetown, MA
DEFAULT_STATION_ID = "8443970"
DEFAULT_STATION_NAME = "Provincetown, MA"
