"""Camera platform for Modern Tides integration."""
import io
import logging
import os
from typing import Any, Dict, List, Optional

import matplotlib.dates as mdates
import matplotlib.figure as mplfig
import matplotlib.pyplot as plt
import numpy as np
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from PIL import Image

from .const import CONF_STATION_ID, CONF_STATION_NAME, CONF_STATIONS, DOMAIN
from .sensor import TideBaseCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Modern Tides camera based on a config entry."""
    stations = entry.data.get(CONF_STATIONS, [])
    
    if not stations:
        return

    async_add_entities(
        [
            TideCurveCamera(hass, entry, station)
            for station in stations
        ]
    )

class TideCurveCamera(Camera):
    """Camera that generates tide curve images."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        station: Dict[str, Any],
    ):
        """Initialize tide curve camera."""
        super().__init__()
        
        self.station_id = station[CONF_STATION_ID]
        self.station_name = station[CONF_STATION_NAME]
        self.coordinator = TideBaseCoordinator(hass, station)
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
            return None
        
        # Generate a curve image based on the tide data
        image_bytes = await self.hass.async_add_executor_job(self._generate_tide_curve)
        return image_bytes

    def _generate_tide_curve(self) -> bytes:
        """Generate a tide curve image based on the coordinator data."""
        try:
            daily_data = self.coordinator.data.get("daily", {})
            
            if (
                not daily_data
                or "mareas" not in daily_data
                or "datos" not in daily_data["mareas"]
                or not daily_data["mareas"]["datos"]
            ):
                if self._last_image:
                    return self._last_image
                return self._create_error_image("No tide data available")
            
            # Extract tide data
            tide_points = []
            high_points = []
            low_points = []
            
            for point in daily_data["mareas"]["datos"]:
                if "fecha" in point and "altura" in point:
                    time_str = point["fecha"]
                    height = float(point["altura"])
                    tide_type = point.get("tipo")
                    
                    try:
                        # Convert to datetime object
                        tide_time = dt_util.parse_datetime(time_str)
                        if tide_time:
                            tide_points.append((tide_time, height))
                            
                            # Categorize as high or low tide
                            if tide_type == "pleamar":
                                high_points.append((tide_time, height))
                            elif tide_type == "bajamar":
                                low_points.append((tide_time, height))
                    except ValueError:
                        continue
            
            # Sort all points by time
            tide_points.sort(key=lambda x: x[0])
            
            if not tide_points:
                if self._last_image:
                    return self._last_image
                return self._create_error_image("No valid tide points found")
            
            # Create the plot
            fig = plt.figure(figsize=(10, 5))
            ax = fig.add_subplot(111)
            
            # Plot the tide curve
            times, heights = zip(*tide_points)
            ax.plot(times, heights, 'b-', linewidth=2, label='Tide')
            
            # Highlight high tides
            if high_points:
                high_times, high_heights = zip(*high_points)
                ax.scatter(high_times, high_heights, c='red', marker='^', s=100, label='High Tide')
            
            # Highlight low tides
            if low_points:
                low_times, low_heights = zip(*low_points)
                ax.scatter(low_times, low_heights, c='green', marker='v', s=100, label='Low Tide')
            
            # Add current time marker
            now = dt_util.now()
            if times[0] <= now <= times[-1]:
                # Find current height by interpolating
                ax.axvline(x=now, color='orange', linestyle='--', linewidth=2, label='Current Time')
            
            # Format the plot
            ax.set_title(f'Tide Chart: {self.station_name}', fontsize=14)
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Height (m)', fontsize=12)
            
            # Format the x-axis to show hours
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            
            # Add grid and legend
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(loc='best')
            
            # Add water level fill
            min_height = min(heights)
            ax.fill_between(times, min_height, heights, color='lightblue', alpha=0.5)
            
            # Set dark style background for Home Assistant integration
            fig.set_facecolor('#121212')
            ax.set_facecolor('#1D1E1F')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            
            # Adjust layout
            fig.tight_layout()
            
            # Convert to image bytes
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            
            # Clean up plot
            plt.close(fig)
            
            # Save image for future use if data fails to load
            self._last_image = buf.getvalue()
            return self._last_image
            
        except Exception as err:
            _LOGGER.error("Error generating tide curve: %s", err)
            if self._last_image:
                return self._last_image
            return self._create_error_image(f"Error: {err}")

    def _create_error_image(self, message: str) -> bytes:
        """Create an image showing an error message."""
        # Create a simple image with text
        fig = plt.figure(figsize=(10, 5))
        ax = fig.add_subplot(111)
        
        ax.text(0.5, 0.5, message, 
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=14, color='red',
                transform=ax.transAxes)
        
        # Set dark style background
        fig.set_facecolor('#121212')
        ax.set_facecolor('#1D1E1F')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Convert to image bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        
        # Clean up plot
        plt.close(fig)
        
        return buf.getvalue()
