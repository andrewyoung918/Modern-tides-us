"""Tide API client for Modern Tides integration using NOAA CO-OPS API."""
import datetime
import logging
import traceback
from typing import Any, Dict, List, Optional

import requests

from .const import (
    API_PREDICTIONS, 
    API_HILO_PREDICTIONS, 
    API_STATION_LIST_URL,
    DEFAULT_STATION_ID,
    DEFAULT_STATION_NAME
)

_LOGGER = logging.getLogger(__name__)

class TideApiClient:
    """Client to interact with the NOAA CO-OPS API."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.session = requests.Session()

    def get_stations(self) -> List[Dict[str, Any]]:
        """Get list of available NOAA tide stations."""
        try:
            response = self.session.get(API_STATION_LIST_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            _LOGGER.debug("NOAA stations API response structure: %s", data)
            
            # NOAA API returns stations in 'stations' array
            if "stations" in data:
                # Filter for US stations only and format for compatibility
                us_stations = []
                for station in data["stations"]:
                    if station.get("state") in ["MA", "ME", "NH", "RI", "CT", "NY", "NJ", "DE", "MD", "VA", "NC", "SC", "GA", "FL", "AL", "MS", "LA", "TX", "CA", "OR", "WA", "AK", "HI"]:
                        us_stations.append({
                            "id": station["id"],
                            "name": station["name"],
                            "state": station.get("state", ""),
                            "puerto": f"{station['name']}, {station.get('state', '')}"  # For compatibility
                        })
                return us_stations
            
            _LOGGER.error("Invalid stations data format received from NOAA API: %s", data)
            return []
        except Exception as err:
            _LOGGER.error("Error fetching NOAA tide stations: %s", err)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            
            # Return default Provincetown station if API fails
            return [{
                "id": DEFAULT_STATION_ID,
                "name": DEFAULT_STATION_NAME,
                "state": "MA",
                "puerto": DEFAULT_STATION_NAME
            }]

    def get_daily_tides(self, station_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get tide predictions for a specific day from NOAA."""
        if date is None:
            target_date = datetime.datetime.now()
        else:
            target_date = datetime.datetime.strptime(date, "%Y%m%d")
        
        begin_date = target_date.strftime("%Y%m%d")
        end_date = (target_date + datetime.timedelta(days=1)).strftime("%Y%m%d")
        
        # Get 6-minute interval predictions for detailed tide curve
        predictions_url = API_PREDICTIONS.format(
            station_id=station_id,
            begin_date=begin_date,
            end_date=end_date
        )
        
        # Get high/low tide times
        hilo_url = API_HILO_PREDICTIONS.format(
            station_id=station_id,
            begin_date=begin_date,
            end_date=end_date
        )
        
        try:
            # Get detailed predictions
            _LOGGER.debug("Fetching NOAA predictions for station %s, date %s", station_id, begin_date)
            predictions_response = self.session.get(predictions_url, timeout=15)
            predictions_response.raise_for_status()
            predictions_data = predictions_response.json()
            
            # Get high/low tides
            _LOGGER.debug("Fetching NOAA high/low tides for station %s, date %s", station_id, begin_date)
            hilo_response = self.session.get(hilo_url, timeout=15)
            hilo_response.raise_for_status()
            hilo_data = hilo_response.json()
            
            # Log response sizes for debugging
            predictions_count = len(predictions_data.get("predictions", []))
            hilo_count = len(hilo_data.get("predictions", []))
            _LOGGER.debug("NOAA API returned %d predictions and %d high/low points for station %s", 
                         predictions_count, hilo_count, station_id)
            
            # Convert NOAA format to format expected by existing code
            converted_data = self._convert_noaa_to_legacy_format(
                predictions_data, hilo_data, station_id, target_date
            )
            
            return converted_data
            
        except requests.RequestException as err:
            _LOGGER.error("Error fetching daily tides from NOAA for station %s: %s", station_id, err)
            # Log the URLs for debugging
            _LOGGER.debug("Failed predictions URL: %s", predictions_url)
            _LOGGER.debug("Failed hilo URL: %s", hilo_url)
            return {}

    def get_monthly_tides(self, station_id: str, month: Optional[str] = None) -> Dict[str, Any]:
        """Get tide predictions for a month from NOAA."""
        if month is None:
            target_month = datetime.datetime.now()
        else:
            target_month = datetime.datetime.strptime(month + "01", "%Y%m%d")
        
        # Get start and end dates for the month
        import calendar
        begin_date = target_month.replace(day=1).strftime("%Y%m%d")
        last_day = calendar.monthrange(target_month.year, target_month.month)[1]
        end_date = target_month.replace(day=last_day).strftime("%Y%m%d")
        
        # Get high/low tides for the entire month
        hilo_url = API_HILO_PREDICTIONS.format(
            station_id=station_id,
            begin_date=begin_date,
            end_date=end_date
        )
        
        try:
            _LOGGER.debug("Fetching NOAA monthly tides for station %s, month %s", station_id, target_month.strftime("%Y-%m"))
            response = self.session.get(hilo_url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            # Log response size for debugging
            monthly_count = len(data.get("predictions", []))
            _LOGGER.debug("NOAA API returned %d monthly high/low points for station %s", monthly_count, station_id)
            
            # Convert to format expected by existing code
            return self._convert_monthly_noaa_format(data, station_id, target_month)
            
        except requests.RequestException as err:
            _LOGGER.error("Error fetching monthly tides from NOAA for station %s: %s", station_id, err)
            _LOGGER.debug("Failed monthly URL: %s", hilo_url)
            return {}
    
    def _convert_noaa_to_legacy_format(self, predictions_data: Dict, hilo_data: Dict, station_id: str, date: datetime.datetime) -> Dict[str, Any]:
        """Convert NOAA API response to format expected by existing Modern Tides code."""
        try:
            # Extract predictions from NOAA response
            marea_points = []
            if "predictions" in predictions_data:
                for pred in predictions_data["predictions"]:
                    # NOAA format: {"t": "2024-01-01 00:00", "v": "2.45"}
                    time_str = pred["t"].split()[1]  # Extract time part (HH:MM)
                    marea_points.append({
                        "hora": time_str,
                        "altura": pred["v"]
                    })
            
            # Extract high/low tides and add them to marea points with tipo
            combined_points = marea_points.copy()
            high_low_events = []
            
            if "predictions" in hilo_data:
                for pred in hilo_data["predictions"]:
                    tide_type = pred.get("type", "").upper()
                    time_str = pred["t"].split()[1]
                    # Use lowercase for compatibility with existing code
                    tipo = "pleamar" if tide_type == "H" else "bajamar"
                    
                    # Add to combined points with type info
                    combined_points.append({
                        "hora": time_str,
                        "altura": pred["v"],
                        "tipo": tipo
                    })
                    
                    high_low_events.append({
                        "hora": time_str,
                        "altura": pred["v"],
                        "tipo": tipo
                    })
            
            # Sort combined points by time for consistency
            def sort_key(point):
                try:
                    hour, minute = point["hora"].split(":")
                    return int(hour) * 60 + int(minute)
                except:
                    return 0
            
            combined_points.sort(key=sort_key)
            
            # Create structure compatible with existing code
            converted = {
                "mareas": {
                    "datos": {
                        "marea": combined_points  # Include both regular points and high/low with tipo
                    },
                    "puerto": {
                        "nombre": f"NOAA Station {station_id}",
                        "id": station_id
                    },
                    "pleamares": [event for event in high_low_events if event.get("tipo") == "pleamar"],
                    "bajamares": [event for event in high_low_events if event.get("tipo") == "bajamar"]
                }
            }
            
            return converted
            
        except Exception as err:
            _LOGGER.error("Error converting NOAA data format: %s", err)
            _LOGGER.error("Traceback: %s", traceback.format_exc())
            return {}
    
    def _convert_monthly_noaa_format(self, hilo_data: Dict, station_id: str, month: datetime.datetime) -> Dict[str, Any]:
        """Convert monthly NOAA API response to legacy format."""
        try:
            high_low_events = []
            if "predictions" in hilo_data:
                for pred in hilo_data["predictions"]:
                    tide_type = pred.get("type", "").upper()
                    date_time = pred["t"]  # Full datetime string
                    high_low_events.append({
                        "datetime": date_time,
                        "altura": pred["v"],
                        "tipo": "PLEAMAR" if tide_type == "H" else "BAJAMAR"
                    })
            
            return {
                "monthly_events": high_low_events,
                "station_id": station_id,
                "month": month.strftime("%Y-%m")
            }
            
        except Exception as err:
            _LOGGER.error("Error converting monthly NOAA data: %s", err)
            return {}
