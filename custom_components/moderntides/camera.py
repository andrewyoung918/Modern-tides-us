"""Camera platform for Modern Tides integration."""
import base64
import io
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from homeassistant.components.camera import Camera
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.util import dt as dt_util
except ImportError:
    # Fallback definitions to avoid import errors
    Camera = object
    ConfigEntry = object
    HomeAssistant = object
    AddEntitiesCallback = object
    dt_util = None

from .const import CONF_STATION_ID, CONF_STATION_NAME, CONF_STATIONS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Static image to use when chart generation is not possible
PLACEHOLDER_SVG = """
<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="400" fill="#1D1E1F"/>
  <text x="400" y="100" font-family="Arial" font-size="24" fill="white" text-anchor="middle">Tide Data</text>
  <text x="400" y="140" font-family="Arial" font-size="18" fill="#0066cc" text-anchor="middle">Station: {station_name}</text>
  
  <!-- Decorative waves -->
  <path d="M 50,250 C 100,230 150,270 200,250 C 250,230 300,270 350,250 C 400,230 450,270 500,250 C 550,230 600,270 650,250 C 700,230 750,270 800,250" 
        stroke="white" stroke-width="3" fill="none" opacity="0.6"/>
  <path d="M 50,280 C 100,260 150,300 200,280 C 250,260 300,300 350,280 C 400,260 450,300 500,280 C 550,260 600,300 650,280 C 700,260 750,300 800,280" 
        stroke="white" stroke-width="2" fill="none" opacity="0.4"/>
  <path d="M 50,310 C 100,290 150,330 200,310 C 250,290 300,330 350,310 C 400,290 450,330 500,310 C 550,290 600,330 650,310 C 700,290 750,330 800,310" 
        stroke="white" stroke-width="2" fill="none" opacity="0.2"/>
        
  <!-- Tide information -->
  <text x="400" y="200" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Next high tide: {high_time}</text>
  <text x="400" y="230" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Height: {high_height} m</text>
  
  <text x="400" y="280" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Next low tide: {low_time}</text>
  <text x="400" y="310" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Height: {low_height} m</text>
  
  <text x="400" y="360" font-family="Arial" font-size="12" fill="#cccccc" text-anchor="middle">Data provided by Instituto Hidrográfico de la Marina</text>
  <text x="750" y="380" font-family="Arial" font-size="10" fill="#cccccc" text-anchor="end">Updated: {updated_time}</text>
</svg>
"""


async def async_setup_entry(
    hass, entry, async_add_entities
) -> None:
    """Set up Modern Tides camera based on a config entry."""
    stations = entry.data.get(CONF_STATIONS, [])
    
    if not stations:
        return

    # Get coordinators from hass.data
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinators = entry_data["coordinators"]
    
    _LOGGER.debug("Setting up cameras for %d stations", len(stations))
    _LOGGER.debug("Available coordinators: %s", list(coordinators.keys()))
    
    entities = []
    for station in stations:
        station_id = station[CONF_STATION_ID]
        station_name = station[CONF_STATION_NAME]
        if station_id in coordinators:
            _LOGGER.debug("Creating camera for station %s (%s)", station_id, station_name)
            entities.append(TideCurveCamera(hass, coordinators[station_id]))
        else:
            _LOGGER.error("No coordinator found for camera of station %s (%s)", station_id, station_name)
    
    if entities:
        async_add_entities(entities)

class TideCurveCamera(Camera):
    """Camera that generates tide curve images."""

    def __init__(
        self,
        hass,
        coordinator,
    ):
        """Initialize tide curve camera."""
        super().__init__()
        
        self.coordinator = coordinator
        self.station_id = coordinator.station_id
        self.station_name = coordinator.station_name
        self.hass = hass
        
        self._attr_unique_id = f"{self.station_id}_curve_picture"
        self._attr_name = f"{self.station_name} Curve Picture"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.station_id)},
            "name": f"Tide Station {self.station_name}",
            "manufacturer": "IHM - Instituto Hidrográfico de la Marina",
            "model": "Tide Station",
        }
        
        self._image = None
        self._last_image = None

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return a tide curve image."""
        await self.coordinator.async_request_refresh()
        
        if not self.coordinator.data:
            return self._create_error_image("No data available")
        
        # Generate image with tide information
        image_bytes = await self.hass.async_add_executor_job(self._generate_tide_info)
        return image_bytes
        
    @property
    def content_type(self) -> str:
        """Return the content type of the camera."""
        return "image/svg+xml"

    def _generate_tide_info(self) -> bytes:
        """Generate an image with tide information."""
        try:
            high_time = "Not available"
            high_height = "N/A"
            low_time = "Not available"
            low_height = "N/A"
            
            # Extract tide data if available
            if self.coordinator.data:
                if "next_high_tide" in self.coordinator.data and self.coordinator.data["next_high_tide"]:
                    high_tide = self.coordinator.data["next_high_tide"]
                    high_time = high_tide["time"].strftime("%H:%M") if "time" in high_tide else "Not available"
                    high_height = f"{high_tide['height']:.2f}" if "height" in high_tide else "N/A"
                
                if "next_low_tide" in self.coordinator.data and self.coordinator.data["next_low_tide"]:
                    low_tide = self.coordinator.data["next_low_tide"]
                    low_time = low_tide["time"].strftime("%H:%M") if "time" in low_tide else "Not available"
                    low_height = f"{low_tide['height']:.2f}" if "height" in low_tide else "N/A"
            
            # Fill the SVG template with data
            svg_content = PLACEHOLDER_SVG.format(
                station_name=self.station_name,
                high_time=high_time,
                high_height=high_height,
                low_time=low_time,
                low_height=low_height,
                updated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Return SVG directly as bytes
            _LOGGER.debug("Using SVG format")
            return svg_content.encode("utf-8")
            
        except Exception as err:
            _LOGGER.error("Error generating tide info: %s", err)
            return self._create_error_image(f"Error: {err}")

    def _create_error_image(self, message: str) -> bytes:
        """Create a simple error image."""
        error_svg = f"""
        <svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
          <rect width="800" height="400" fill="#1D1E1F"/>
          <text x="400" y="200" font-family="Arial" font-size="24" fill="red" text-anchor="middle">{message}</text>
          <text x="400" y="240" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Please check the logs for more information</text>
        </svg>
        """
        
        # Return SVG directly
        return error_svg.encode("utf-8")
