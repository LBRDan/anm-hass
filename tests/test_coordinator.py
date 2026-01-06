"""Tests for ANM coordinator."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses

from custom_components.anm.api import ANMAPIClient
from custom_components.anm.coordinator import ANMDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_update(hass):
    """Test coordinator update."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    mock_response = {
        "arrivals": [
            {
                "line": "R1",
                "destination": "Piazza Cavour",
                "arrival_time": "2025-12-29T12:30:00",
                "time_minutes": "5",
                "vehicle_id": "12345",
            }
        ]
    }

    stops = [{"stop_id": stop_id, "stop_name": stop_name}]

    with aioresponses() as m:
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_config_entry_first_refresh()

        data = coordinator.data

        assert stop_id in data
        assert data[stop_id]["stop_id"] == stop_id
        assert data[stop_id]["stop_name"] == stop_name
        assert len(data[stop_id]["arrivals"]) == 1
        assert data[stop_id]["last_updated"] is not None

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_error(hass):
    """Test coordinator update with API error."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    stops = [{"stop_id": stop_id, "stop_name": stop_name}]

    with aioresponses() as m:
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova", status=404
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_config_entry_first_refresh()

        data = coordinator.data

        assert stop_id in data
        assert "error" in data[stop_id]
        assert data[stop_id]["arrivals"] == []

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_multiple_stops(hass):
    """Test coordinator update with multiple stops."""
    stops = [
        {"stop_id": "1234", "stop_name": "Piazza Cavour"},
        {"stop_id": "5678", "stop_name": "Via Toledo"},
    ]

    mock_response = {
        "arrivals": [
            {
                "line": "R1",
                "destination": "Piazza Cavour",
                "arrival_time": "2025-12-29T12:30:00",
                "time_minutes": "5",
                "vehicle_id": "12345",
            }
        ]
    }

    with aioresponses() as m:
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_config_entry_first_refresh()

        data = coordinator.data

        assert "1234" in data
        assert "5678" in data
        assert len(data) == 2

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_line_filter(hass):
    """Test coordinator update with line filter."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    line_filter = "R1"
    mock_response = {
        "arrivals": [
            {
                "line": "R1",
                "destination": "Piazza Cavour",
                "arrival_time": "2025-12-29T12:30:00",
                "time_minutes": "5",
                "vehicle_id": "12345",
            },
            {
                "line": "R2",
                "destination": "Via Toledo",
                "arrival_time": "2025-12-29T12:35:00",
                "time_minutes": "10",
                "vehicle_id": "12346",
            },
        ]
    }

    stops = [
        {"stop_id": stop_id, "stop_name": stop_name, "line_filter": line_filter}
    ]

    with aioresponses() as m:
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_config_entry_first_refresh()

        data = coordinator.data

        # Should only include R1, not R2
        assert stop_id in data
        assert len(data[stop_id]["arrivals"]) == 1
        assert data[stop_id]["arrivals"][0]["line"] == "R1"

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_multiline_filter(hass):
    """Test coordinator update with multiple line filter."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    line_filter = "R1,R2"
    mock_response = {
        "arrivals": [
            {
                "line": "R1",
                "destination": "Piazza Cavour",
                "arrival_time": "2025-12-29T12:30:00",
                "time_minutes": "5",
                "vehicle_id": "12345",
            },
            {
                "line": "R2",
                "destination": "Via Toledo",
                "arrival_time": "2025-12-29T12:35:00",
                "time_minutes": "10",
                "vehicle_id": "12346",
            },
            {
                "line": "R3",
                "destination": "Piazza Garibaldi",
                "arrival_time": "2025-12-29T12:40:00",
                "time_minutes": "15",
                "vehicle_id": "12347",
            },
        ]
    }

    stops = [
        {"stop_id": stop_id, "stop_name": stop_name, "line_filter": line_filter}
    ]

    with aioresponses() as m:
        m.post(
            "https://srv.anm.it/api/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_config_entry_first_refresh()

        data = coordinator.data

        # Should include only R1 and R2, not R3
        assert stop_id in data
        assert len(data[stop_id]["arrivals"]) == 2
        assert all(a["line"] in ["R1", "R2"] for a in data[stop_id]["arrivals"])

        await api_client.close()
