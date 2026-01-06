"""Config flow for ANM integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from . import api
from .const import (
    CONF_API_BASE_URL,
    CONF_LINE_FILTER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_STOPS,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_API_BASE_URL,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Schema for step 1 - API configuration
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_API_BASE_URL, default=DEFAULT_API_BASE_URL
        ): str,
        vol.Optional(
            CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=60)
        ),
    }
)

# Schema for adding a stop
STEP_STOPS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_STOP_ID): str,
        vol.Optional(CONF_STOP_NAME): str,
        vol.Optional(CONF_LINE_FILTER): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect.

    Args:
        hass: Home Assistant instance
        data: User input data

    Returns:
        Info to be stored in the config entry
    """
    api_client = api.ANMAPIClient(
        api_base_url=data.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL),
        timeout=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
    )

    try:
        # Try to connect and validate API by fetching stops
        await api_client.get_stops()
    except Exception as err:
        _LOGGER.error("Error connecting to ANM API: %s", err)
        raise ValueError("cannot_connect") from err
    finally:
        await api_client.close()

    return {"title": DEFAULT_NAME}


class ANMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ANM."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_config: dict | None = None
        self._stops: list[dict] = []
        self._available_stops: list[dict] = []

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step - API configuration.

        Args:
            user_input: User input from the form

        Returns:
            FlowResult indicating next action
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)

                # Fetch stops for autocomplete
                api_client = api.ANMAPIClient(
                    api_base_url=user_input.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL),
                    timeout=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                )
                self._available_stops = await api_client.get_stops()
                await api_client.close()

                self._api_config = user_input

                # Store the config and move to stops step
                return await self.async_step_stops()

            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_stops(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle adding stops with autocomplete from available stops."""
        errors: dict[str, str] = {}

        # Build autocomplete lists
        stop_id_options = [stop.get("id", "") for stop in self._available_stops]
        stop_name_options = [stop.get("name", "") for stop in self._available_stops]

        # Dynamic schema with autocomplete
        stops_schema = vol.Schema(
            {
                vol.Optional(CONF_STOP_ID): vol.In(stop_id_options) if stop_id_options else str,
                vol.Optional(CONF_STOP_NAME): vol.In(stop_name_options) if stop_name_options else str,
                vol.Optional(CONF_LINE_FILTER): str,
            }
        )

        if user_input is not None:
            _LOGGER.debug("User input for stops: %s", user_input)
            stop_id = user_input.get(CONF_STOP_ID, "").strip()
            stop_name = user_input.get(CONF_STOP_NAME, "").strip()
            line_filter = user_input.get(CONF_LINE_FILTER, "").strip()

            if not stop_id:
                errors[CONF_STOP_ID] = "required"
            if not stop_name:
                errors[CONF_STOP_NAME] = "required"
            if stop_id and any(stop[CONF_STOP_ID] == stop_id for stop in self._stops):
                errors[CONF_STOP_ID] = "stop_already_configured"
            if not errors:
                self._stops.append(
                    {
                        CONF_STOP_ID: stop_id,
                        CONF_STOP_NAME: stop_name,
                        CONF_LINE_FILTER: line_filter if line_filter else None,
                    }
                )
            elif len(self._stops) > 0:
                return await self.async_step_finish()

        return self.async_show_form(
            step_id="stops",
            data_schema=stops_schema,
            errors=errors,
            last_step=len(self._stops) > 0,
            description_placeholders={
                "stops_list": "\n".join(
                    f"- {stop[CONF_STOP_NAME]} ({stop[CONF_STOP_ID]})"
                    for stop in self._stops
                ),
            },
        )

    async def async_step_finish(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Finish the config flow and create the entry.

        Args:
            user_input: Not used, kept for signature compatibility

        Returns:
            FlowResult creating the config entry
        """
        # Require at least one stop to be configured
        if not self._stops:
            return self.async_abort(reason="no_stops_configured")

        # Combine API config with stops
        data = {
            **self._api_config,
            CONF_STOPS: self._stops,
        }

        _LOGGER.debug("Finalizing config flow with stops: %s", self._stops)
        return self.async_create_entry(title=DEFAULT_NAME, data=data)
