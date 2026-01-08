"""The ANM integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ANMAPIClient
from .const import (
    CONF_API_BASE_URL,
    CONF_STOPS,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DATA_API_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .coordinator import ANMDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up ANM from a config entry.

    Args:
        hass: Home Assistant instance
        config_entry: The config entry for ANM

    Returns:
        True if setup was successful
    """
    session = async_get_clientsession(hass)

    api_client = ANMAPIClient(
        api_base_url=config_entry.data.get(CONF_API_BASE_URL),
        timeout=config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        session=session,
    )

    coordinator = ANMDataUpdateCoordinator(
        hass,
        api_client=api_client,
        stops=config_entry.data.get(CONF_STOPS, []),
        update_interval=config_entry.data.get(CONF_UPDATE_INTERVAL, 60),
    )

    # Fetch initial data
    if config_entry.state is ConfigEntryState.LOADED:
        await coordinator.async_refresh()
    else:
        await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        DATA_API_CLIENT: api_client,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        config_entry: The config entry to unload

    Returns:
        True if unload was successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        data = hass.data[DOMAIN].pop(config_entry.entry_id)
        await data[DATA_API_CLIENT].close()

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Args:
        hass: Home Assistant instance
        entry: The config entry to update
    """
    await hass.config_entries.async_reload(entry.entry_id)
