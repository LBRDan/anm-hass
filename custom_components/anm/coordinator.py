"""Data update coordinator for ANM integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import ANMAPIClient, ANMAPIClientError

_LOGGER = logging.getLogger(__name__)


class ANMDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Data update coordinator for ANM."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: ANMAPIClient,
        stops: list[dict[str, str]],
        update_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: The Home Assistant instance
            api_client: The ANM API client
            stops: List of stops to monitor
            update_interval: Update interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            name="ANM",
            update_interval=timedelta(seconds=update_interval),
        )
        self._api_client = api_client
        self._stops = stops

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch data from ANM API for all monitored stops.

        Returns:
            Dictionary with stop_id as key and arrival data as value
        """
        data: dict[str, dict] = {}
        errors: dict[str, str] = {}

        for stop in self._stops:
            stop_id = stop["stop_id"]
            stop_name = stop.get("stop_name", stop_id)
            line_filter = stop.get("line_filter")

            try:
                arrival_data = await self._api_client.async_get_stop_arrivals(
                    stop_id, line_filter
                )
                data[stop_id] = {
                    "stop_id": stop_id,
                    "stop_name": stop_name,
                    "line_filter": line_filter,
                    "arrivals": arrival_data or [],
                    "last_updated": datetime.now().isoformat(
                        sep="T", timespec="seconds"
                    ),
                }
            except ANMAPIClientError as err:
                _LOGGER.error(
                    "Error updating stop %s (%s): %s", stop_id, stop_name, err
                )
                errors[stop_id] = str(err)
                # Keep existing data if update fails, just update error status
                if self.data and stop_id in self.data:
                    data[stop_id] = self.data[stop_id]
                    data[stop_id]["error"] = str(err)
                else:
                    data[stop_id] = {
                        "stop_id": stop_id,
                        "stop_name": stop_name,
                        "line_filter": line_filter,
                        "error": str(err),
                        "arrivals": [],
                        "last_updated": None,
                    }

        if errors:
            _LOGGER.warning("Errors occurred during update for stops: %s", errors)

        return data
