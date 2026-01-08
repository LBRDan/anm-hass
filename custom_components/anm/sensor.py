"""Sensor platform for ANM integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ARRIVAL_TIME,
    ATTR_DESTINATION,
    ATTR_LAST_UPDATED,
    ATTR_LINE,
    ATTR_LINE_FILTER,
    ATTR_NEXT_ARRIVALS,
    ATTR_STOP_ID,
    ATTR_STOP_NAME,
    ATTR_TIME_MINUTES,
    CONF_STOPS,
    DATA_COORDINATOR,
    DOMAIN,
)
from .coordinator import ANMDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTION = SensorEntityDescription(
    key="anm_stop",
    translation_key="anm_stop",
    has_entity_name=True,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ANM sensor entities from a config entry."""
    coordinator: ANMDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    stops = entry.data.get(CONF_STOPS, [])

    entities: list[ANMStopSensor] = []
    for stop in stops:
        entities.append(ANMStopSensor(coordinator, stop, SENSOR_DESCRIPTION))

    async_add_entities(entities)


class ANMStopSensor(CoordinatorEntity[ANMDataUpdateCoordinator], SensorEntity):
    """Sensor representing an ANM stop."""

    def __init__(
        self,
        coordinator: ANMDataUpdateCoordinator,
        stop: dict[str, str],
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._stop_id = stop["stop_id"]
        self._stop_name = stop.get("stop_name", stop["stop_id"])
        self._line_filter = stop.get("line_filter")

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_{self._stop_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._stop_name

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the device class of the sensor."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor (next arrival time)."""
        stop_data = self.coordinator.data.get(self._stop_id)
        if not stop_data:
            return None

        arrivals = stop_data.get("arrivals", [])

        _LOGGER.debug("Arrivals data for stop %s: %s", self._stop_id, stop_data)
        if not arrivals:
            return None

        if len(arrivals) == 0:
            return None

        _LOGGER.info("Next arrivals for stop %s: %s", self._stop_id, arrivals)
        # Return the first arrival time
        first_arrival = arrivals[0].to_dict()
        arrival_time_str = first_arrival.get(ATTR_ARRIVAL_TIME)
        if arrival_time_str:
            try:
                # Try to parse as ISO format
                return datetime.fromisoformat(arrival_time_str).replace(
                    tzinfo=ZoneInfo("Europe/Rome")
                )
            except (ValueError, TypeError):
                _LOGGER.error(
                    "Error parsing arrival time '%s' for stop %s",
                    arrival_time_str,
                    self._stop_id,
                )
                pass

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        stop_data = self.coordinator.data.get(self._stop_id)
        if not stop_data:
            return None

        attrs = {
            ATTR_STOP_ID: self._stop_id,
            ATTR_STOP_NAME: self._stop_name,
            ATTR_LINE_FILTER: self._line_filter,
            ATTR_LAST_UPDATED: stop_data.get("last_updated"),
        }

        # Format next arrivals for attributes
        arrivals = stop_data.get("arrivals", [])
        formatted_arrivals = []
        for arrival in arrivals:
            arrival_dict = arrival.to_dict()
            formatted_arrivals.append(
                {
                    ATTR_LINE: arrival_dict.get(ATTR_LINE),
                    ATTR_DESTINATION: arrival_dict.get(ATTR_DESTINATION),
                    ATTR_ARRIVAL_TIME: arrival_dict.get(ATTR_ARRIVAL_TIME),
                    ATTR_TIME_MINUTES: arrival_dict.get(ATTR_TIME_MINUTES),
                }
            )
        attrs[ATTR_NEXT_ARRIVALS] = formatted_arrivals

        if stop_data.get("error"):
            attrs["error"] = stop_data["error"]

        return attrs
