"""Tests for ANM API client."""

import pytest
from aioresponses import aioresponses

from custom_components.anm.api import ANMAPIClient, ANMAPIClientError, LEGACY_INFO_URL

import os
import json


@pytest.fixture
def api_response_fixture():
    """Fixture to load API response XML files."""
    def _load_response(file_name: str) -> str:
        base_path = os.path.join(os.path.dirname(__file__), "fixtures", "api_responses")
        file_path = os.path.join(base_path, file_name)
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    return _load_response    

@pytest.mark.asyncio
async def test_async_get_stop_arrivals_success(api_response_fixture):
    """Test successful fetch of stop arrivals."""
    stop_id = "2103"
    ## Parse json from file
    mock_response = json.loads(api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json"))


    with aioresponses() as m:

        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )
        

        client = ANMAPIClient()
        result = await client.async_get_stop_arrivals(stop_id)
        await client.close()

        
        # Verify the first request to get the API key
        m.assert_any_call(LEGACY_INFO_URL, method="GET")
        # Verify the second request to get stop arrivals
        m.assert_any_call("https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova", method="POST")

        assert len(result) == 3


@pytest.mark.asyncio
async def test_async_get_stop_arrivals_with_line_filter(api_response_fixture):
    """Test fetching stop arrivals with single line filter."""
    stop_id = "2103"
    line_filter = "151"
    mock_response = json.loads(api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json"))


    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        client = ANMAPIClient()
        await client.close()
        result = await client.async_get_stop_arrivals(stop_id, line_filter)

        assert len(result) == 2
        assert result[0]["line"] == line_filter
        assert result[1]["line"] == line_filter
    


@pytest.mark.asyncio
async def test_async_get_stop_arrivals_with_multiline_filter(api_response_fixture):
    """Test fetching stop arrivals with multiple line filter (comma-separated)."""
    stop_id = "2103"
    line_filter = "181"
    mock_response = json.loads(api_response_fixture(f"CaricaPrevisioniNuova_{stop_id}.json"))


    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            payload=mock_response,
            status=200,
        )

        client = ANMAPIClient()
        await client.close()
        result = await client.async_get_stop_arrivals(stop_id, line_filter)

        assert len(result) == 0


@pytest.mark.asyncio
async def test_async_get_stop_arrivals_error():
    """Test error handling when API returns error."""
    stop_id = "1234"

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post("https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova", status=404)

        client = ANMAPIClient()

        with pytest.raises(ANMAPIClientError):
            await client.async_get_stop_arrivals(stop_id)

        await client.close()


@pytest.mark.asyncio
async def test_async_get_stop_arrivals_connection_error():
    """Test error handling when connection fails."""
    stop_id = "1234"

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova",
            exception=Exception()
        )

        client = ANMAPIClient()

        with pytest.raises(ANMAPIClientError):
            await client.async_get_stop_arrivals(stop_id)

        await client.close()


@pytest.mark.asyncio
async def test_get_stops_success(api_response_fixture):
    """Test successful fetch of all stops."""
    xml_response = """<?xml version="1.0" encoding="UTF-8"?>
    <ArrayOfPalina>
        	<Palina>
                <id>6337</id>
                <nome>S.ROSA</nome>
                <stato>OK</stato>
                <lat>40.8517149865804</lat>
                <lon>14.23561247637</lon>
            </Palina>
            <Palina>
                <id>6338</id>
                <nome>QUATTRO GIORNATE</nome>
                <stato>OK</stato>
                <lat>40.8463404239426</lat>
                <lon>14.2248254606282</lon>
            </Palina>
    </ArrayOfPalina>
    """

    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaElencoPaline",
            body=xml_response,
            content_type="application/xml",
            status=200,
        )

        client = ANMAPIClient()
        result = await client.get_stops()
        await client.close()

        assert len(result) == 2
        assert result[0]["id"] == "6337"
        assert result[0]["name"] == "S.ROSA"
        assert result[1]["name"] == "QUATTRO GIORNATE"


@pytest.mark.asyncio
async def test_get_stops_error():
    """Test error handling when fetching stops fails."""
    with aioresponses() as m:
        m.get(LEGACY_INFO_URL, status=200, body="var key_anm='testkey'")
        m.post(
            "https://srv.anm.it/ServiceInfoAnmLinee.asmx/CaricaElencoPaline",
            status=500,
        )

        client = ANMAPIClient()

        with pytest.raises(ANMAPIClientError):
            await client.get_stops()

        await client.close()
