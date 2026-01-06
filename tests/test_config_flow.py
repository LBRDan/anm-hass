"""Tests for ANM config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.anm.const import (
    CONF_API_BASE_URL,
    CONF_LINE_FILTER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    CONF_STOPS,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.anm.config_flow import (
    ANMConfigFlow,
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


async def test_form_user(hass: HomeAssistant):
    """Test the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == STEP_USER


async def test_form_stops(hass: HomeAssistant):
    """Test the stops form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Proceed with user input
    with patch(
        "custom_components.anm.config_flow.validate_input",
        return_value={"title": "ANM"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=VALID_USER_INPUT
        )

    assert result2["type"] == "form"
    assert result2["step_id"] == STEP_STOPS


async def test_form_abort(hass: HomeAssistant):
    """Test abort when already configured."""
    entry = await hass.config_entries.async_add(
        config_entries.ConfigEntry(
            version=1,
            domain=DOMAIN,
            title="ANM",
            data=VALID_USER_INPUT,
            source=config_entries.SOURCE_USER,
            entry_id="test",
        )
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    await hass.config_entries.async_remove(entry.entry_id)
