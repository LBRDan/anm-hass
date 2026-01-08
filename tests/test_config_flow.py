"""Tests for ANM config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.anm.const import (
    CONF_API_BASE_URL,
    CONF_LINE_FILTER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    STEP_STOPS,
    STEP_USER,
)

# Test data
VALID_USER_INPUT = {
    CONF_API_BASE_URL: "https://srv.anm.it/api",
    CONF_UPDATE_INTERVAL: 60,
    CONF_TIMEOUT: 10,
}

VALID_STOP_INPUT = {
    CONF_STOP_ID: "1234",
    CONF_STOP_NAME: "Piazza Cavour",
    CONF_LINE_FILTER: "R1",
}

VALID_STOPS_API_RESPONSE = [
    {"id": "1234", "name": "Piazza Cavour"},
    {"id": "2103", "name": "Via Toledo"},
]


async def test_form_user(hass: HomeAssistant):
    """Test the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == STEP_USER


async def test_form_stops(hass: HomeAssistant):
    """Test the stops form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Mock the API client to avoid network calls
    mock_client = AsyncMock()
    mock_client.get_stops.return_value = VALID_STOPS_API_RESPONSE
    mock_client._renew_api_key.return_value = "testkey"
    mock_client._get_api_key.return_value = "testkey"

    with patch("custom_components.anm.api.ANMAPIClient", return_value=mock_client):
        with patch(
            "custom_components.anm.config_flow.validate_input",
            return_value={"title": "ANM"},
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input=VALID_USER_INPUT
            )
            result_menu = await hass.config_entries.flow.async_configure(
                result2["flow_id"], user_input=VALID_STOP_INPUT
            )
            # Test we are getting the menu with async_show_menu
            result_final = await hass.config_entries.flow.async_configure(
                result_menu["flow_id"], user_input={"next_step_id": "finish"}
            )

    assert result2.get("type") == FlowResultType.FORM
    assert result2.get("step_id") == STEP_STOPS
    assert result_menu.get("type") == FlowResultType.MENU
    assert result_menu.get("step_id") == "choice"
    assert result_final.get("type") == FlowResultType.CREATE_ENTRY
    assert result_final.get("title") == "ANM"
