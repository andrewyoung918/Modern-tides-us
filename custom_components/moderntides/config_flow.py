"""Config flow for Modern Tides integration."""
import logging
from typing import Any, Dict, Optional

try:
    import voluptuous as vol
except ImportError:
    # Handle import failure
    vol = None

try:
    from homeassistant import config_entries
    from homeassistant.core import callback
    from homeassistant.data_entry_flow import FlowResult
    import homeassistant.helpers.config_validation as cv
except ImportError:
    # Fallback definitions in case of import failure
    callback = lambda func: func
    FlowResult = Dict[str, Any]
    cv = None
    config_entries = None

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    INTERVALS,
)
from .tide_api import TideApiClient

_LOGGER = logging.getLogger(__name__)

class ModernTidesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Modern Tides."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._entry_data = {CONF_STATIONS: []}
        self._current_stations = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Go directly to station addition step
            return await self.async_step_station()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("setup_message", default="Click Submit to continue"): str,
            }),
        )

    async def async_step_station(
        self, user_input: Optional[Dict[str, Any]] = None
    ):
        """Handle adding a tide station."""
        errors = {}

        if user_input is not None:
            # Get the list of stations
            api_client = TideApiClient()
            stations = await self.hass.async_add_executor_job(api_client.get_stations)

            # Check if the station ID exists
            station_id = user_input[CONF_STATION_ID]
            valid_station_ids = [str(station["id"]) for station in stations]
            
            if station_id not in valid_station_ids:
                errors[CONF_STATION_ID] = "invalid_station"
            else:
                # Find the station name
                station_name = None
                for station in stations:
                    if str(station["id"]) == station_id:
                        # Use puerto or name field depending on what's available
                        station_name = station.get("puerto", station.get("name", f"Station {station_id}"))
                        break
                
                if not station_name:
                    station_name = f"Station {station_id}"
                
                # Check if station already exists in current config
                if any(station[CONF_STATION_ID] == station_id for station in self._entry_data[CONF_STATIONS]):
                    errors[CONF_STATION_ID] = "station_exists"
                else:
                    # Add the new station
                    self._entry_data[CONF_STATIONS].append({
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: user_input.get(CONF_STATION_NAME, station_name),
                        CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    })
                    
                    # Preguntar si desea añadir otra estación o finalizar
                    return await self.async_step_add_another()

        # Get available stations for dropdown
        stations_list = {}
        try:
            api_client = TideApiClient()
            stations = await self.hass.async_add_executor_job(api_client.get_stations)
            
            # Process each station safely
            for station in stations:
                try:
                    station_id = str(station["id"])
                    # Use puerto or name field depending on what's available
                    station_name = station.get("puerto", station.get("name", f"Station {station_id}"))
                    stations_list[station_id] = f"{station_name} ({station_id})"
                except Exception as e:
                    _LOGGER.error("Error processing station: %s - %s", station, e)
        except Exception as e:
            _LOGGER.error("Error fetching stations: %s", e)
            import traceback
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            errors["base"] = "cannot_connect"

        # Prepare the schema for the form
        schema = vol.Schema({
            vol.Required(CONF_STATION_ID): vol.In(stations_list) if stations_list else str,
            vol.Optional(CONF_STATION_NAME): cv.string,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.In(
                {k: f"{k} ({v} min)" for k, v in INTERVALS.items()}
            ),
        })

        return self.async_show_form(
            step_id="station",
            data_schema=schema,
            errors=errors,
        )
    
    async def async_step_add_another(
        self, user_input: Optional[Dict[str, Any]] = None
    ):
        """Ask if user wants to add another station."""
        if user_input is not None:
            if user_input.get("add_another", True):
                return await self.async_step_station()
            else:
                # Crear la entrada de configuración final
                return self.async_create_entry(
                    title="Modern Tides", 
                    data=self._entry_data
                )

        schema = vol.Schema({
            vol.Required("add_another", default=True): bool,
        })

        return self.async_show_form(
            step_id="add_another",
            data_schema=schema,
            description_placeholders={
                "station_count": str(len(self._entry_data[CONF_STATIONS]))
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ModernTidesOptionsFlow(config_entry)


class ModernTidesOptionsFlow(config_entries.OptionsFlow):
    """Handle options for the Modern Tides integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self.data = dict(config_entry.data)
        self.current_station_id = None

    async def async_step_init(self, user_input=None):
        """Manage basic options."""
        if user_input is not None:
            if user_input.get("add_station", False):
                return await self.async_step_add_station()
            elif user_input.get("remove_station", False):
                return await self.async_step_remove_station()
            else:
                # Verificar si se seleccionó modificar alguna estación
                for key, value in user_input.items():
                    if key.startswith("modify_station_") and value:
                        self.current_station_id = key.replace("modify_station_", "")
                        return await self.async_step_modify_station()
                
                # Si no se seleccionó ninguna acción, simplemente guardar las opciones
                return self.async_create_entry(title="", data=user_input)

        current_stations = self.data.get(CONF_STATIONS, [])
        
        options = {
            vol.Optional("add_station", default=False): bool,
            vol.Optional("remove_station", default=False): bool,
        }
        
        # Add options to modify each station
        for i, station in enumerate(current_stations):
            station_id = station[CONF_STATION_ID]
            station_name = station[CONF_STATION_NAME]
            key = f"modify_station_{station_id}"
            options[vol.Optional(key, default=False)] = bool

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        )

    async def async_step_add_station(self, user_input=None):
        """Add a new station."""
        errors = {}

        if user_input is not None:
            # Get the list of stations
            api_client = TideApiClient()
            stations = await self.hass.async_add_executor_job(api_client.get_stations)

            # Check if the station ID exists
            station_id = user_input[CONF_STATION_ID]
            valid_station_ids = [str(station["id"]) for station in stations]
            
            if station_id not in valid_station_ids:
                errors[CONF_STATION_ID] = "invalid_station"
            else:
                # Find the station name
                station_name = None
                for station in stations:
                    if str(station["id"]) == station_id:
                        # Use puerto or name field depending on what's available
                        station_name = station.get("puerto", station.get("name", f"Station {station_id}"))
                        break
                
                if not station_name:
                    station_name = f"Station {station_id}"
                
                # Actualizar la configuración actual
                current_data = self.config_entry.data.copy()
                stations_list = list(current_data.get(CONF_STATIONS, []))
                
                # Check if station already exists
                # Log current stations for debugging
                _LOGGER.debug("Current stations: %s", stations_list)
                
                # Check if station already exists
                existing_station_ids = [s.get(CONF_STATION_ID) for s in stations_list]
                _LOGGER.debug("Existing station IDs: %s", existing_station_ids)
                
                if station_id in existing_station_ids:
                    _LOGGER.warning("Attempted to add station %s (%s) that already exists", station_id, station_name)
                    errors[CONF_STATION_ID] = "station_exists"
                    _LOGGER.warning("Station %s already exists in config", station_id)
                else:
                    _LOGGER.info("Adding new station: %s - %s", station_id, station_name)
                    stations_list.append({
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: user_input.get(CONF_STATION_NAME, station_name),
                        CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    })
                    
                    current_data[CONF_STATIONS] = stations_list
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=current_data
                    )
                    return self.async_abort(reason="station_added")

        # Get available stations for dropdown
        stations_list = {}
        try:
            api_client = TideApiClient()
            stations = await self.hass.async_add_executor_job(api_client.get_stations)
            
            # Process each station safely
            for station in stations:
                try:
                    station_id = str(station["id"])
                    # Use puerto or name field depending on what's available
                    station_name = station.get("puerto", station.get("name", f"Station {station_id}"))
                    stations_list[station_id] = f"{station_name} ({station_id})"
                except Exception as e:
                    _LOGGER.error("Error processing station: %s - %s", station, e)
        except Exception as e:
            _LOGGER.error("Error fetching stations: %s", e)
            import traceback
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            errors["base"] = "cannot_connect"

        # Prepare the schema for the form
        schema = vol.Schema({
            vol.Required(CONF_STATION_ID): vol.In(stations_list) if stations_list else str,
            vol.Optional(CONF_STATION_NAME): cv.string,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.In(
                {k: f"{k} ({v} min)" for k, v in INTERVALS.items()}
            ),
        })

        return self.async_show_form(
            step_id="add_station",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_remove_station(self, user_input=None):
        """Remove a station."""
        if user_input is not None:
            station_id = user_input["station_to_remove"]
            current_data = self.config_entry.data.copy()
            stations = list(current_data.get(CONF_STATIONS, []))
            
            # Remove the selected station
            stations = [s for s in stations if s[CONF_STATION_ID] != station_id]
            
            current_data[CONF_STATIONS] = stations
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=current_data
            )
            return self.async_abort(reason="station_removed")

        # Get current stations for the dropdown
        current_stations = self.data.get(CONF_STATIONS, [])
        station_options = {
            station[CONF_STATION_ID]: f"{station[CONF_STATION_NAME]} ({station[CONF_STATION_ID]})"
            for station in current_stations
        }

        return self.async_show_form(
            step_id="remove_station",
            data_schema=vol.Schema({
                vol.Required("station_to_remove"): vol.In(station_options)
            }),
        )

    async def async_step_modify_station(self, user_input=None):
        """Modify an existing station."""
        station_id = self.current_station_id
        
        if user_input is not None:
            current_data = self.config_entry.data.copy()
            stations = list(current_data.get(CONF_STATIONS, []))
            
            # Find and update the selected station
            for i, station in enumerate(stations):
                if station[CONF_STATION_ID] == station_id:
                    stations[i] = {
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: user_input.get(CONF_STATION_NAME),
                        CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL),
                    }
                    break
            
            current_data[CONF_STATIONS] = stations
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=current_data
            )
            return self.async_abort(reason="station_modified")

        # Get current station settings
        current_stations = self.data.get(CONF_STATIONS, [])
        station = next((s for s in current_stations if s[CONF_STATION_ID] == station_id), None)
        
        if not station:
            return self.async_abort(reason="station_not_found")

        return self.async_show_form(
            step_id="modify_station",
            data_schema=vol.Schema({
                vol.Required(CONF_STATION_NAME, default=station[CONF_STATION_NAME]): cv.string,
                vol.Required(CONF_UPDATE_INTERVAL, default=station[CONF_UPDATE_INTERVAL]): vol.In(
                    {k: f"{k} ({v} min)" for k, v in INTERVALS.items()}
                ),
            }),
        )
