"""Sensor platform for Modern Tides integration."""
import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, cast

import async_timeout
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    INTERVALS,
)
from .tide_api import TideApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Modern Tides sensors based on a config entry."""
    stations = entry.data.get(CONF_STATIONS, [])
    
    if not stations:
        return

    async_add_entities(
        [
            TideStationInfoSensor(hass, entry, station)
            for station in stations
        ]
        +
        [
            TideCurrentHeightSensor(hass, entry, station)
            for station in stations
        ]
        +
        [
            TideNextHighSensor(hass, entry, station)
            for station in stations
        ]
        +
        [
            TideNextLowSensor(hass, entry, station)
            for station in stations
        ]
    )

class TideBaseCoordinator(DataUpdateCoordinator):
    """Class to manage fetching tide data."""

    def __init__(
        self,
        hass: HomeAssistant,
        station: Dict[str, Any],
    ):
        """Initialize coordinator."""
        self.station_id = station[CONF_STATION_ID]
        self.station_name = station[CONF_STATION_NAME]
        self.api_client = TideApiClient()
        
        # Convert update interval string to minutes
        update_interval_str = station.get(CONF_UPDATE_INTERVAL, "1h")
        update_interval_min = INTERVALS.get(update_interval_str, 60)
        update_interval = datetime.timedelta(minutes=update_interval_min)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Modern Tides {self.station_name}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                # Get current day data
                today = datetime.datetime.now().strftime("%Y%m%d")
                daily_data = await self.hass.async_add_executor_job(
                    self.api_client.get_daily_tides, self.station_id, today
                )
                
                # Get current month data for trend analysis
                current_month = datetime.datetime.now().strftime("%Y%m")
                monthly_data = await self.hass.async_add_executor_job(
                    self.api_client.get_monthly_tides, self.station_id, current_month
                )
                
                # Combine data
                data = {
                    "daily": daily_data,
                    "monthly": monthly_data,
                    "station_id": self.station_id,
                    "station_name": self.station_name
                }
                
                # Process data to extract current tide height and next events
                if daily_data and "mareas" in daily_data and "datos" in daily_data["mareas"]:
                    data.update(self._process_tide_data(daily_data["mareas"]["datos"]))
                
                return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _process_tide_data(self, tide_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process tide data to extract current and next tide information."""
        now = datetime.datetime.now()
        current_height = None
        next_high = None
        next_low = None
        
        # Find current tide height (interpolate between points if needed)
        tide_points = []
        for point in tide_data:
            if "fecha" in point and "altura" in point:
                time_str = point["fecha"]
                height = float(point["altura"])
                
                try:
                    # Parse the date time (format: "2025-07-03 12:34:00")
                    tide_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    tide_points.append((tide_time, height))
                except ValueError:
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
            if "fecha" in point and "altura" in point and "tipo" in point:
                time_str = point["fecha"]
                height = float(point["altura"])
                tide_type = point["tipo"]
                
                try:
                    tide_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    
                    if tide_type == "pleamar" and tide_time >= now:
                        high_tides.append((tide_time, height))
                    elif tide_type == "bajamar" and tide_time >= now:
                        low_tides.append((tide_time, height))
                except ValueError:
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
            "next_low_tide": next_low
        }

class ModernTidesEntity(CoordinatorEntity):
    """Base entity for Modern Tides sensors."""

    def __init__(
        self,
        coordinator: TideBaseCoordinator,
        description: SensorEntityDescription,
    ):
        """Initialize entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.station_id)},
            "name": f"Tide Station {coordinator.station_name}",
            "manufacturer": "IHM - Instituto Hidrográfico de la Marina",
            "model": "Tide Station",
        }

class TideStationInfoSensor(ModernTidesEntity, SensorEntity):
    """Sensor representing tide station information."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        station: Dict[str, Any],
    ):
        """Initialize the sensor."""
        coordinator = TideBaseCoordinator(hass, station)
        self.station_name = station[CONF_STATION_NAME]
        
        description = SensorEntityDescription(
            key="tide_station_info",
            name=f"{self.station_name} Tide Station Info",
            icon="mdi:waves",
        )
        
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.station_name

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        if self.coordinator.data:
            attrs["station_id"] = self.coordinator.data.get("station_id")
            
            # Include any metadata from the API response
            if (
                "daily" in self.coordinator.data
                and "mareas" in self.coordinator.data["daily"]
                and "metadatos" in self.coordinator.data["daily"]["mareas"]
            ):
                metadata = self.coordinator.data["daily"]["mareas"]["metadatos"]
                attrs.update(metadata)
        
        return attrs

class TideCurrentHeightSensor(ModernTidesEntity, SensorEntity):
    """Sensor for current tide height."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        station: Dict[str, Any],
    ):
        """Initialize the sensor."""
        coordinator = TideBaseCoordinator(hass, station)
        self.station_name = station[CONF_STATION_NAME]
        
        description = SensorEntityDescription(
            key="current_tide_height",
            name=f"{self.station_name} Current Tide Height",
            icon="mdi:wave",
            native_unit_of_measurement=UnitOfLength.METERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
        )
        
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        if (
            self.coordinator.data
            and "current_height" in self.coordinator.data
            and self.coordinator.data["current_height"] is not None
        ):
            # Round to 2 decimal places
            return round(self.coordinator.data["current_height"], 2)
        return None

class TideNextHighSensor(ModernTidesEntity, SensorEntity):
    """Sensor for next high tide."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        station: Dict[str, Any],
    ):
        """Initialize the sensor."""
        coordinator = TideBaseCoordinator(hass, station)
        self.station_name = station[CONF_STATION_NAME]
        
        description = SensorEntityDescription(
            key="next_high_tide_time",
            name=f"{self.station_name} Next High Tide Time",
            icon="mdi:arrow-up-bold",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        
        super().__init__(coordinator, description)
        
        # Create additional entity for height
        self._height_entity_id = f"{self.entity_id}_height".replace("next_high_tide_time", "next_high_tide_height")

    @property
    def native_value(self) -> Optional[datetime.datetime]:
        """Return the time of the next high tide."""
        if (
            self.coordinator.data
            and "next_high_tide" in self.coordinator.data
            and self.coordinator.data["next_high_tide"] is not None
        ):
            return self.coordinator.data["next_high_tide"]["time"]
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        if (
            self.coordinator.data
            and "next_high_tide" in self.coordinator.data
            and self.coordinator.data["next_high_tide"] is not None
        ):
            high_tide = self.coordinator.data["next_high_tide"]
            attrs["height"] = round(high_tide["height"], 2)
            attrs["height_m"] = round(high_tide["height"], 2)  # For backwards compatibility
            
        return attrs

class TideNextLowSensor(ModernTidesEntity, SensorEntity):
    """Sensor for next low tide."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        station: Dict[str, Any],
    ):
        """Initialize the sensor."""
        coordinator = TideBaseCoordinator(hass, station)
        self.station_name = station[CONF_STATION_NAME]
        
        description = SensorEntityDescription(
            key="next_low_tide_time",
            name=f"{self.station_name} Next Low Tide Time",
            icon="mdi:arrow-down-bold",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        
        super().__init__(coordinator, description)
        
        # Create additional entity for height
        self._height_entity_id = f"{self.entity_id}_height".replace("next_low_tide_time", "next_low_tide_height")

    @property
    def native_value(self) -> Optional[datetime.datetime]:
        """Return the time of the next low tide."""
        if (
            self.coordinator.data
            and "next_low_tide" in self.coordinator.data
            and self.coordinator.data["next_low_tide"] is not None
        ):
            return self.coordinator.data["next_low_tide"]["time"]
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        if (
            self.coordinator.data
            and "next_low_tide" in self.coordinator.data
            and self.coordinator.data["next_low_tide"] is not None
        ):
            low_tide = self.coordinator.data["next_low_tide"]
            attrs["height"] = round(low_tide["height"], 2)
            attrs["height_m"] = round(low_tide["height"], 2)  # For backwards compatibility
            
        return attrs
