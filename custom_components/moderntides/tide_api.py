"""Tide API client for Modern Tides integration."""
import datetime
import logging
from typing import Any, Dict, List, Optional

import requests

from .const import API_DAY_TIDES, API_MONTH_TIDES, API_STATION_LIST

_LOGGER = logging.getLogger(__name__)

class TideApiClient:
    """Client to interact with the tide API."""

    def __init__(self) -> None:
        """Initialize the API client."""
        self.session = requests.Session()

    def get_stations(self) -> List[Dict[str, Any]]:
        """Get list of available tide stations."""
        try:
            response = self.session.get(API_STATION_LIST, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "mareas" in data and "puertos" in data["mareas"]:
                return data["mareas"]["puertos"]
            
            _LOGGER.error("Invalid data format received from API")
            return []
        except requests.RequestException as err:
            _LOGGER.error("Error fetching tide stations: %s", err)
            return []

    def get_daily_tides(self, station_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get tides for a specific day."""
        if date is None:
            date = datetime.datetime.now().strftime("%Y%m%d")
        
        url = API_DAY_TIDES.format(station_id=station_id, date=date)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            _LOGGER.error("Error fetching daily tides: %s", err)
            return {}

    def get_monthly_tides(self, station_id: str, month: Optional[str] = None) -> Dict[str, Any]:
        """Get tides for a specific month."""
        if month is None:
            month = datetime.datetime.now().strftime("%Y%m")
        
        url = API_MONTH_TIDES.format(station_id=station_id, month=month)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            _LOGGER.error("Error fetching monthly tides: %s", err)
            return {}
