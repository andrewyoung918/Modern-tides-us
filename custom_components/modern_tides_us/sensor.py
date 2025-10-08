"""Sensor platform for Modern Tides integration."""
import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, cast

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    INTERVALS,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Modern Tides sensors based on a config entry."""
    stations = entry.data.get(CONF_STATIONS, [])
    
    if not stations:
        return

    entities = []
    
    # Get coordinators from the hass.data structure
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinators = entry_data["coordinators"]
    
    _LOGGER.debug("Setting up sensors for %d stations", len(stations))
    _LOGGER.debug("Available coordinators: %s", list(coordinators.keys()))
    
    # Create entities for each station using the existing coordinators
    for station in stations:
        station_id = station[CONF_STATION_ID]
        station_name = station[CONF_STATION_NAME]
        
        if station_id not in coordinators:
            _LOGGER.error("No coordinator found for station %s (%s)", station_id, station_name)
            continue
            
        _LOGGER.debug("Creating sensors for station %s (%s)", station_id, station_name)
        coordinator = coordinators[station_id]
        
        # Add entities for this station
        entities.extend([
            TideStationInfoSensor(coordinator),
            TideCurrentHeightSensor(coordinator),
            TideNextHighSensor(coordinator),
            TideNextLowSensor(coordinator)
        ])
    
    if entities:
        async_add_entities(entities)

class ModernTidesEntity(CoordinatorEntity):
    """Base entity for Modern Tides sensors."""

    def __init__(
        self,
        coordinator,
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

    def __init__(self, coordinator):
        """Initialize the sensor."""
        description = SensorEntityDescription(
            key="tide_station_info",
            name=f"{coordinator.station_name} Tide Station Info",
            icon="mdi:waves",
        )
        
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.coordinator.station_name

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

    def __init__(self, coordinator):
        """Initialize the sensor."""
        description = SensorEntityDescription(
            key="current_tide_height",
            name=f"{coordinator.station_name} Current Tide Height",
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

    def __init__(self, coordinator):
        """Initialize the sensor."""
        description = SensorEntityDescription(
            key="next_high_tide_time",
            name=f"{coordinator.station_name} Next High Tide Time",
            icon="mdi:arrow-up-bold",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        
        super().__init__(coordinator, description)
        
        # Create additional entity for height
        self._height_entity_id = f"{self.entity_id}_height".replace("next_high_tide_time", "next_high_tide_height")
        # Ensure we always have a valid state even if no data is available
        self._attr_available = True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Ensure we're always available even if no tide data
        if not self.coordinator.last_update_success:
            return False
        return True

    @property
    def native_value(self) -> Optional[datetime.datetime]:
        """Return the time of the next high tide."""
        try:
            if (
                self.coordinator.data
                and "next_high_tide" in self.coordinator.data
                and self.coordinator.data["next_high_tide"] is not None
                and "time" in self.coordinator.data["next_high_tide"]
            ):
                return self.coordinator.data["next_high_tide"]["time"]
        except Exception as e:
            _LOGGER.error("Error getting next high tide time: %s", e)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        try:
            if (
                self.coordinator.data
                and "next_high_tide" in self.coordinator.data
                and self.coordinator.data["next_high_tide"] is not None
                and "height" in self.coordinator.data["next_high_tide"]
            ):
                high_tide = self.coordinator.data["next_high_tide"]
                attrs["height"] = round(high_tide["height"], 2)
                attrs["height_m"] = round(high_tide["height"], 2)  # For backwards compatibility
        except Exception as e:
            _LOGGER.error("Error getting next high tide attributes: %s", e)
            
        return attrs

class TideNextLowSensor(ModernTidesEntity, SensorEntity):
    """Sensor for next low tide."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        description = SensorEntityDescription(
            key="next_low_tide_time",
            name=f"{coordinator.station_name} Next Low Tide Time",
            icon="mdi:arrow-down-bold",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        
        super().__init__(coordinator, description)
        
        # Create additional entity for height
        self._height_entity_id = f"{self.entity_id}_height".replace("next_low_tide_time", "next_low_tide_height")
        # Ensure we always have a valid state even if no data is available
        self._attr_available = True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Ensure we're always available even if no tide data
        if not self.coordinator.last_update_success:
            return False
        return True

    @property
    def native_value(self) -> Optional[datetime.datetime]:
        """Return the time of the next low tide."""
        try:
            if (
                self.coordinator.data
                and "next_low_tide" in self.coordinator.data
                and self.coordinator.data["next_low_tide"] is not None
                and "time" in self.coordinator.data["next_low_tide"]
            ):
                return self.coordinator.data["next_low_tide"]["time"]
        except Exception as e:
            _LOGGER.error("Error getting next low tide time: %s", e)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        try:
            if (
                self.coordinator.data
                and "next_low_tide" in self.coordinator.data
                and self.coordinator.data["next_low_tide"] is not None
                and "height" in self.coordinator.data["next_low_tide"]
            ):
                low_tide = self.coordinator.data["next_low_tide"]
                attrs["height"] = round(low_tide["height"], 2)
                attrs["height_m"] = round(low_tide["height"], 2)  # For backwards compatibility
        except Exception as e:
            _LOGGER.error("Error getting next low tide attributes: %s", e)
            
        return attrs
