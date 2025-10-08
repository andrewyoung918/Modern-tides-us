"""
Custom component for Modern Tides integration with Home Assistant.
For more details about this component, please refer to the documentation at
https://github.com/ALArvi019/moderntides
"""
import logging
from datetime import timedelta
import os
import sys
import async_timeout
import datetime
import traceback

from homeassistant.util import dt as dt_util

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
    from homeassistant.helpers.update_coordinator import (
        DataUpdateCoordinator,
        UpdateFailed,
    )
    from homeassistant.util import dt as dt_util
    import homeassistant.helpers.config_validation as cv
except ImportError:
    ConfigEntry = object
    HomeAssistant = object
    ConfigType = dict
    DataUpdateCoordinator = object
    UpdateFailed = Exception
    dt_util = None
    cv = None

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    INTERVALS,
    PLATFORMS,
    PLOT_DAYS_TO_GENERATE
)
from .tide_api import TideApiClient
from .plot_manager import TidePlotManager

_LOGGER = logging.getLogger(__name__)

# Configuration schema - this integration only uses config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

def _install_dependencies():
    try:
        import requests
    except ImportError:
        _LOGGER.warning("Installing missing dependency: requests")
        os.system(f"{sys.executable} -m pip install requests")

_install_dependencies()

class TideDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching tide data."""

    def __init__(
        self,
        hass: HomeAssistant,
        station: dict,
    ):
        """Initialize coordinator."""
        self.station_id = station[CONF_STATION_ID]
        self.station_name = station[CONF_STATION_NAME]
        self.api_client = TideApiClient()
        
        # Convert update interval string to minutes
        update_interval_str = station.get(CONF_UPDATE_INTERVAL, "1h")
        update_interval_min = INTERVALS.get(update_interval_str, 60)
        update_interval = datetime.timedelta(minutes=update_interval_min)

        _LOGGER.debug("Creating coordinator for station %s (%s) with update interval %s",
                      self.station_name, self.station_id, update_interval)

        # Initialize plot managers for tide charts (light and dark mode) for multiple days
        safe_name = self.station_name.lower().replace(" ", "_").replace("-", "_")
        
        # Create plot managers for each day configuration
        self.plot_managers = {}
        
        for days in PLOT_DAYS_TO_GENERATE:
            # Generate filename suffix based on plot days (maintain compatibility)
            if days == 1:
                # For 1 day, keep the original naming for backwards compatibility
                filename_suffix = ""
            else:
                filename_suffix = f"_{days}d"
            
            # Light mode plot manager
            plot_filename_light = hass.config.path("www", f"{DOMAIN}_{safe_name}_plot{filename_suffix}.svg")
            light_manager = TidePlotManager(
                name=self.station_name,
                filename=plot_filename_light,
                transparent_background=False,
                dark_mode=False,
                plot_days=days
            )
            
            # Dark mode plot manager
            plot_filename_dark = hass.config.path("www", f"{DOMAIN}_{safe_name}_plot{filename_suffix}_dark.svg")
            dark_manager = TidePlotManager(
                name=self.station_name,
                filename=plot_filename_dark,
                transparent_background=False,
                dark_mode=True,
                plot_days=days
            )
            
            self.plot_managers[days] = {
                'light': light_manager,
                'dark': dark_manager
            }

        super().__init__(
            hass,
            _LOGGER,
            name=f"Modern Tides {self.station_name}",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(60):
                # Get data for the maximum number of days (7 days)
                max_days = max(PLOT_DAYS_TO_GENERATE)
                all_daily_data = []
                base_date = datetime.datetime.now()
                
                # Get data for each day
                for day_offset in range(max_days):
                    current_date = base_date + datetime.timedelta(days=day_offset)
                    date_str = current_date.strftime("%Y%m%d")
                    
                    daily_data = await self.hass.async_add_executor_job(
                        self.api_client.get_daily_tides, self.station_id, date_str
                    )
                    
                    if daily_data:
                        all_daily_data.append({
                            'date': date_str,
                            'data': daily_data
                        })
                        _LOGGER.debug("Got data for station %s, date %s", self.station_id, date_str)
                
                # For backwards compatibility, use the first day as "daily_data"
                daily_data = all_daily_data[0]['data'] if all_daily_data else {}
                
                # Log the data structure for debugging
                _LOGGER.debug("Daily data for station %s: %s", self.station_id, daily_data)
                
                # Get current month data for trend analysis
                current_month = datetime.datetime.now().strftime("%Y%m")
                monthly_data = await self.hass.async_add_executor_job(
                    self.api_client.get_monthly_tides, self.station_id, current_month
                )
                
                # Combine data
                data = {
                    "daily": daily_data,
                    "monthly": monthly_data,
                    "all_daily_data": all_daily_data,  # Include all days for multi-day plots
                    "station_id": self.station_id,
                    "station_name": self.station_name
                }
                
                # Process data to extract current tide height and next events
                if daily_data and "mareas" in daily_data and "datos" in daily_data["mareas"]:
                    if "marea" in daily_data["mareas"]["datos"]:
                        # Current API format has data in 'datos.marea'
                        data.update(self._process_tide_data(daily_data["mareas"]["datos"]["marea"]))
                    else:
                        _LOGGER.error("Unexpected data format: 'marea' key not found in 'datos'")
                else:
                    _LOGGER.error("No valid tide data found for station %s", self.station_id)
                
                # Generate tide plots for all day configurations
                # Each plot is generated independently to prevent one failure from breaking all plots
                if daily_data:
                    for days in PLOT_DAYS_TO_GENERATE:
                        try:
                            # Create data subset for this day range
                            days_data = {
                                **data,
                                "plot_days": days,
                                "all_daily_data": all_daily_data[:days]  # Only include days up to this range
                            }

                            # Generate light mode plot
                            try:
                                await self.hass.async_add_executor_job(
                                    self.plot_managers[days]['light'].generate_tide_plot, days_data
                                )
                                _LOGGER.debug("Generated %d-day light plot for station %s", days, self.station_id)
                            except Exception as light_err:
                                _LOGGER.warning("Failed to generate %d-day light plot for station %s: %s",
                                              days, self.station_id, light_err)

                            # Generate dark mode plot
                            try:
                                await self.hass.async_add_executor_job(
                                    self.plot_managers[days]['dark'].generate_tide_plot, days_data
                                )
                                _LOGGER.debug("Generated %d-day dark plot for station %s", days, self.station_id)
                            except Exception as dark_err:
                                _LOGGER.warning("Failed to generate %d-day dark plot for station %s: %s",
                                              days, self.station_id, dark_err)

                        except Exception as plot_err:
                            _LOGGER.warning("Failed to generate %d-day plots for station %s: %s",
                                           days, self.station_id, plot_err)

                    _LOGGER.debug("Tide plot generation completed for station %s", self.station_id)
                
                return data
        except Exception as err:
            _LOGGER.error("Error updating data for station %s: %s", self.station_id, err)
            import traceback
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _process_tide_data(self, tide_data):
        """Process tide data to extract current and next tide information."""
        now = dt_util.now()  # Use Home Assistant's dt_util for timezone-aware datetime
        today = now.strftime("%Y-%m-%d")
        current_height = None
        next_high = None
        next_low = None
        
        # Log the tide data for debugging
        _LOGGER.debug("Processing tide data for station %s: %s", self.station_id, tide_data)
        
        # Find current tide height (interpolate between points if needed)
        tide_points = []
        processed_tide_points = []  # For plot manager
        for point in tide_data:
            # Log each point for debugging
            _LOGGER.debug("Processing tide point: %s", point)
            
            if "hora" in point and "altura" in point:
                time_str = point["hora"]  # Format is "HH:MM"
                height = float(point["altura"])
                
                try:
                    # Parse the time (format: "HH:MM")
                    # API returns local time (lst_ldt parameter)
                    time_parts = time_str.split(":")
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])

                    # Create a naive datetime with today's date and the time from API
                    local_time = datetime.datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=hours,
                        minute=minutes
                    )

                    # Make it timezone-aware using Home Assistant's timezone
                    tide_time = dt_util.as_local(local_time)

                    # Handle case when tide time is past midnight but still part of today's data
                    if tide_time > now + datetime.timedelta(hours=12):
                        prev_day_time = local_time - datetime.timedelta(days=1)
                        tide_time = dt_util.as_local(prev_day_time)
                    elif tide_time < now - datetime.timedelta(hours=12):
                        next_day_time = local_time + datetime.timedelta(days=1)
                        tide_time = dt_util.as_local(next_day_time)
                        
                    tide_points.append((tide_time, height))
                    processed_tide_points.append({
                        'time': tide_time,
                        'height': height
                    })
                    _LOGGER.debug("Added tide point for station %s: time=%s, height=%s", 
                                 self.station_id, tide_time, height)
                except ValueError as e:
                    _LOGGER.error("Error parsing tide time: %s - %s", time_str, e)
                    continue
        
        # Sort by time
        tide_points.sort(key=lambda x: x[0])
        
        # Find current height through linear interpolation
        for i in range(len(tide_points) - 1):
            if tide_points[i][0] <= now <= tide_points[i+1][0]:
                t1, h1 = tide_points[i]
                t2, h2 = tide_points[i+1]
                
                # Linear interpolation
                time_diff = (t2 - t1).total_seconds()
                height_diff = h2 - h1
                now_diff = (now - t1).total_seconds()
                
                if time_diff > 0:
                    current_height = h1 + (height_diff * now_diff / time_diff)
                else:
                    current_height = h1
                break
        
        # If we couldn't interpolate, use the closest data point
        if current_height is None and tide_points:
            tide_points.sort(key=lambda x: abs((x[0] - now).total_seconds()))
            current_height = tide_points[0][1]
        
        # Identify tide type points (high/low)
        high_tides = []
        low_tides = []
        
        for point in tide_data:
            if "hora" in point and "altura" in point and "tipo" in point:
                time_str = point["hora"]  # Format is "HH:MM"
                height = float(point["altura"])
                tide_type = point["tipo"]
                
                try:
                    # Parse the time (format: "HH:MM")
                    # API returns local time (lst_ldt parameter)
                    time_parts = time_str.split(":")
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])

                    # Create a naive datetime with today's date and the time from API
                    local_time = datetime.datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        hour=hours,
                        minute=minutes
                    )

                    # Make it timezone-aware using Home Assistant's timezone
                    tide_time = dt_util.as_local(local_time)

                    # Handle case when tide time is past midnight but still part of today's data
                    if tide_time > now + datetime.timedelta(hours=12):
                        prev_day_time = local_time - datetime.timedelta(days=1)
                        tide_time = dt_util.as_local(prev_day_time)
                    elif tide_time < now - datetime.timedelta(hours=12):
                        next_day_time = local_time + datetime.timedelta(days=1)
                        tide_time = dt_util.as_local(next_day_time)
                    
                    if tide_type == "pleamar" and tide_time >= now:
                        high_tides.append((tide_time, height))
                        _LOGGER.debug("Added high tide for station %s: time=%s, height=%s", 
                                     self.station_id, tide_time, height)
                    elif tide_type == "bajamar" and tide_time >= now:
                        low_tides.append((tide_time, height))
                        _LOGGER.debug("Added low tide for station %s: time=%s, height=%s", 
                                     self.station_id, tide_time, height)
                except ValueError as e:
                    _LOGGER.error("Error parsing tide type time: %s - %s", time_str, e)
                    continue
        
        # Sort by time to get next events
        high_tides.sort(key=lambda x: x[0])
        low_tides.sort(key=lambda x: x[0])
        
        # Extract next high and low tide info
        if high_tides:
            next_high = {
                "time": high_tides[0][0],
                "height": high_tides[0][1]
            }
            
        if low_tides:
            next_low = {
                "time": low_tides[0][0],
                "height": low_tides[0][1]
            }
            
        return {
            "current_height": current_height,
            "next_high_tide": next_high,
            "next_low_tide": next_low,
            "tide_points": processed_tide_points
        }

async def async_setup(hass, config):
    """Set up the Modern Tides component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry):
    """Set up Modern Tides from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize entry data structure
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "coordinators": {}
    }
    
    # Create a coordinator for each station
    stations = entry.data.get(CONF_STATIONS, [])
    _LOGGER.debug("Setting up %d stations: %s", len(stations), stations)
    
    for station in stations:
        station_id = station[CONF_STATION_ID]
        station_name = station[CONF_STATION_NAME]
        _LOGGER.debug("Creating coordinator for station %s (%s)", station_id, station_name)
        
        coordinator = TideDataCoordinator(hass, station)
        
        # Do initial data update
        try:
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("Initial data update successful for station %s", station_id)
        except Exception as err:
            _LOGGER.error("Error during initial data update for station %s: %s", station_id, err)
            import traceback
            _LOGGER.error("Traceback: %s", traceback.format_exc())
        
        # Store the coordinator
        hass.data[DOMAIN][entry.entry_id]["coordinators"][station_id] = coordinator
        _LOGGER.debug("Added coordinator for station %s to data structure", station_id)

    # Set up all platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True

async def async_update_options(hass, entry):
    """Update options for the entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    # Unload entities for this entry/device
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove entry from data
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
