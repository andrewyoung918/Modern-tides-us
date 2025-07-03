"""
Custom component for Modern Tides integration with Home Assistant.
For more details about this component, please refer to the documentation at
https://github.com/ALArvi019/moderntides
"""
import logging
from datetime import timedelta
import os
import sys

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
except ImportError:
    ConfigEntry = object
    HomeAssistant = object
    ConfigType = dict

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

def _install_dependencies():
    try:
        import requests
    except ImportError:
        _LOGGER.warning("Installing missing dependency: requests")
        os.system(f"{sys.executable} -m pip install requests")
    
    try:
        import matplotlib
    except ImportError:
        _LOGGER.warning("Installing missing dependency: matplotlib")
        os.system(f"{sys.executable} -m pip install matplotlib")
        
    try:
        import numpy
    except ImportError:
        _LOGGER.warning("Installing missing dependency: numpy")
        os.system(f"{sys.executable} -m pip install numpy")
        
    try:
        import PIL
    except ImportError:
        _LOGGER.warning("Installing missing dependency: Pillow")
        os.system(f"{sys.executable} -m pip install Pillow")

_install_dependencies()

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Modern Tides component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Modern Tides from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Set up all platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for the entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload entities for this entry/device
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove entry from data
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
