"""Tests for ANM coordinator."""

from __future__ import annotations

import json

import pytest
from aioresponses import aioresponses

from custom_components.anm.api import LEGACY_INFO_URL, ANMAPIClient
from custom_components.anm.coordinator import ANMDataUpdateCoordinator


@pytest.mark.asyncio
async def test_coordinator_update(hass, api_response_fixture):
    """Test coordinator update."""
    stop_id = "2103"
    stop_name = "Giulio Cesare"
    mock_response = json.loads(
        api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json")
    )

    stops = [{"stop_id": stop_id, "stop_name": stop_name}]

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass,
            api_client=api_client,
            stops=stops,
            update_interval=60,
        )

        await coordinator.async_refresh()

        data = coordinator.data

        assert stop_id in data
        assert data[stop_id]["stop_id"] == stop_id
        assert data[stop_id]["stop_name"] == stop_name
        assert len(data[stop_id]["arrivals"]) == 3
        assert data[stop_id]["last_updated"] is not None

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_error(hass):
    """Test coordinator update with API error."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    stops = [{"stop_id": stop_id, "stop_name": stop_name}]

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            status=404,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_refresh()

        data = coordinator.data

        assert stop_id in data
        assert "error" in data[stop_id]
        assert data[stop_id]["arrivals"] == []

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_multiple_stops(hass, api_response_fixture):
    """Test coordinator update with multiple stops."""
    stops = [
        {"stop_id": "1234", "stop_name": "Piazza Cavour"},
        {"stop_id": "5678", "stop_name": "Via Toledo"},
    ]

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=json.loads(api_response_fixture("CaricaPrevisioniNuova_1234.json")),
            status=200,
        )
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=json.loads(api_response_fixture("CaricaPrevisioniNuova_5678.json")),
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_refresh()

        data = coordinator.data

        assert "1234" in data
        assert "5678" in data
        assert len(data) == 2

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_line_filter(hass, api_response_fixture):
    """Test coordinator update with line filter."""
    stop_id = "2103"
    stop_name = "Giulio Cesare"
    line_filter = "R7"

    stops = [{"stop_id": stop_id, "stop_name": stop_name, "line_filter": line_filter}]

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=json.loads(
                api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json")
            ),
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_refresh()

        data = coordinator.data
        # Should only include R7, not other lines
        assert stop_id in data
        assert len(data[stop_id]["arrivals"]) == 1
        assert data[stop_id]["arrivals"][0].line == "R7"

        await api_client.close()


@pytest.mark.asyncio
async def test_coordinator_update_with_multiline_filter(hass, api_response_fixture):
    """Test coordinator update with multiple line filter."""
    stop_id = "1234"
    stop_name = "Piazza Cavour"
    line_filter = "X1,X2"
    mock_response = json.loads(
        api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json")
    )

    stops = [{"stop_id": stop_id, "stop_name": stop_name, "line_filter": line_filter}]

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        api_client = ANMAPIClient()
        coordinator = ANMDataUpdateCoordinator(
            hass, api_client=api_client, stops=stops, update_interval=60
        )

        await coordinator.async_refresh()

        data = coordinator.data

        # Should include only X1 and X2, not R7
        assert stop_id in data
        assert len(data[stop_id]["arrivals"]) == 2
        assert all(a.line in ["X1", "X2"] for a in data[stop_id]["arrivals"])

        await api_client.close()
