"""API client for ANM public transport."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from .const import DEFAULT_API_BASE_URL, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# Legacy page for API key renewal
LEGACY_INFO_URL = "https://www2.anm.it/infoclick/infoclick.php"

# API endpoints
PREDICTIONS_ENDPOINT = "/ServiceInfoAnmLinee.asmx/CaricaPrevisioniNuova"
STOPS_ENDPOINT = "/ServiceInfoAnmLinee.asmx/CaricaElencoPaline"


class ANMArrival:
    """Represents an arrival prediction for a line at a stop."""

    def __init__(
        self,
        line: str,
        destination: str,
        arrival_time: str,
        time_minutes: int,
        stop_id: str,
    ) -> None:
        self.line = line
        self.destination = destination
        self.arrival_time = arrival_time
        self.time_minutes = time_minutes
        self.stop_id = stop_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "line": self.line,
            "destination": self.destination,
            "arrival_time": self.arrival_time,
            "time_minutes": self.time_minutes,
            "stop_id": self.stop_id,
        }


class ANMAPIClientError(Exception):
    """Exception raised for ANM API errors."""


class ANMAPIClient:
    """API client for ANM (Azienda Napoletana Mobilità)."""

    def __init__(
        self,
        api_base_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the ANM API client.

        Args:
            api_base_url: The base URL for the ANM API
            timeout: Request timeout in seconds
            session: Optional aiohttp session
        """
        self._api_base_url = api_base_url or DEFAULT_API_BASE_URL
        self._timeout = ClientTimeout(total=timeout)
        self._session = session
        self._own_session = session is None
        self._api_key: str | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Close the API client."""
        if self._own_session and self._session is not None:
            await self._session.close()

    async def _renew_api_key(self) -> str:
        """Renew API key by scraping the legacy page.

        Returns:
            The API key

        Raises:
            ANMAPIClientError: If the API key cannot be renewed
        """
        session = await self._get_session()

        try:
            async with session.get(LEGACY_INFO_URL) as response:
                if response.status != 200:
                    raise ANMAPIClientError(
                        f"Failed to fetch legacy page: {response.status}"
                    )

                text = await response.text()

                # Find API key in format: var key_anm='XXXXXXXX'
                match = re.search(r"var key_anm='([a-zA-Z0-9]+)'", text)
                if not match:
                    raise ANMAPIClientError("Could not find API key in legacy page")

                api_key = match.group(1)
                _LOGGER.debug("Renewed ANM API key: %s", api_key)
                return api_key

        except aiohttp.ClientError as err:
            _LOGGER.error("Error renewing API key: %s", err)
            raise ANMAPIClientError(f"Failed to renew API key: {err}") from err

    async def _get_api_key(self) -> str:
        """Get or renew the API key.

        Returns:
            The current API key
        """
        if self._api_key is None:
            self._api_key = await self._renew_api_key()
        return self._api_key

    def _parse_anm_time(self, time_str: str) -> datetime | None:
        """Parse ANM time format (HH:mm).

        Args:
            time_str: Time string in ANM format

        Returns:
            Parsed datetime or None if parsing fails
        """
        try:
            now = datetime.now()
            time_parsed = datetime.strptime(time_str, "%H:%M")
            return now.replace(
                hour=time_parsed.hour,
                minute=time_parsed.minute,
                second=0,
                microsecond=0,
            )
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse time: %s", time_str)
            return None

    def _parse_anm_date(self, date_str: str) -> datetime | None:
        """Parse ANM date format (DD/MM/YYYY HH:mm:ss).

        Args:
            date_str: Date string in ANM format

        Returns:
            Parsed datetime or None if parsing fails
        """
        try:
            return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse date: %s", date_str)
            return None

    async def get_stops(self) -> list[dict[str, Any]]:
        """Fetch all stops from the ANM API for autocomplete.

        Returns:
            List of stops with id, name, lat, lon

        Raises:
            ANMAPIClientError: If the API request fails
        """
        session = await self._get_session()

        url = f"{self._api_base_url}{STOPS_ENDPOINT}"

        headers = {
            "accept": "application/xml",
            "accept-language": "it-IT,it;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            # "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.anm.it",
            "pragma": "no-cache",
            "referer": "https://www.anm.it/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        api_key = await self._get_api_key()

        # Send payload as form data
        data = aiohttp.FormData()
        data.add_field("key", api_key)

        try:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    raise ANMAPIClientError(f"API returned status {response.status}")

                text = await response.text()

                # Parse XML response
                root = ET.fromstring(text)
                stops = []

                # Find all Palina elements
                for palina in root.findall(".//Palina"):
                    stop_id = palina.findtext("id", "")
                    name = palina.findtext("nome", "")
                    lat = float(palina.findtext("lat", 0))
                    lon = float(palina.findtext("lon", 0))
                    status = palina.findtext("stato", "")

                    if stop_id:
                        stops.append(
                            {
                                "id": stop_id,
                                "name": name,
                                "lat": lat,
                                "lon": lon,
                                "status": status,
                            }
                        )

                return stops

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching stops: %s", err)
            raise ANMAPIClientError(f"Failed to fetch stops: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise ANMAPIClientError(f"Unexpected error: {err}") from err

    def _get_predictions_headers(self) -> dict[str, str]:
        """Get headers for predictions API request."""
        return {
            "accept": "application/json",
            "accept-language": "it-IT,it;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "origin": "https://www.anm.it",
            "pragma": "no-cache",
            "referer": "https://www.anm.it/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

    def _parse_line_filter(self, line_filter: str | None) -> list[str] | None:
        """Parse comma-separated line filter into list of lines."""
        if not line_filter:
            return None
        allowed_lines = [line.strip() for line in line_filter.split(",")]
        _LOGGER.debug("Filtering by lines: %s", allowed_lines)
        return allowed_lines

    def _create_arrival_from_item(
        self, item: dict[str, Any], allowed_lines: list[str] | None
    ) -> ANMArrival | None:
        """Create ANMArrival object from API response item."""
        # Skip error messages
        if item.get("stato") == "Nessuna informazione alla palina.":
            return None

        line = item.get("linea", "").strip()

        # Apply line filter if specified
        if allowed_lines and line not in allowed_lines:
            _LOGGER.debug("Skipping line %s due to filter", line)
            return None

        time_str = item.get("time", "")  # e.g. "09:46"
        time_min = item.get("timeMin", "")  # e.g. "7" like minutes to arrival
        destination = item.get(
            "nome", ""
        )  # e.g. "GIULIO CESARE - San Vitale" , Stop name
        stop_id = item.get("id", "")  # e.g. "2103" , Stop ID

        # Parse time to get actual arrival time
        arrival_time = self._parse_anm_time(time_str)

        return ANMArrival(
            line=line,
            destination=destination,
            arrival_time=(
                arrival_time.isoformat(sep="T", timespec="minutes")
                if arrival_time
                else time_str
            ),
            time_minutes=int(time_min) if time_min.isdigit() else time_min,
            stop_id=stop_id,
        )

    async def _handle_invalid_api_key(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Handle invalid API key by renewing and retrying the request."""
        _LOGGER.info("API key invalid, renewing...")
        self._api_key = None
        api_key = await self._get_api_key()
        payload["key"] = api_key
        async with session.post(url, json=payload, headers=headers) as retry_response:
            return await retry_response.json()  # type: ignore

    async def _fetch_predictions_data(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Fetch and handle predictions API data."""
        async with session.post(url, json=payload, headers=headers) as response:
            text = await response.text()

            if response.status != 200:
                raise ANMAPIClientError(
                    f"API returned status {response.status}: {text}"
                )

            data = await response.json()
            _LOGGER.debug("Received data: %s", data)
            return data  # type: ignore

    def _extract_arrivals_from_data(
        self, data: dict[str, Any], allowed_lines: list[str] | None
    ) -> list[ANMArrival]:
        """Extract arrival objects from API response data."""
        arrivals = list[ANMArrival]()
        raw_arrivals = data.get("d", [])

        if isinstance(raw_arrivals, list):
            for item in raw_arrivals:
                arrival = self._create_arrival_from_item(item, allowed_lines)
                if arrival:
                    arrivals.append(arrival)

        # Sort by arrival time
        arrivals.sort(key=lambda x: x.time_minutes)
        return arrivals

    def _should_return_empty(self, data: dict[str, Any]) -> bool:
        """Check if API response indicates no information at the stop."""
        return (
            "d" in data
            and isinstance(data["d"], list)
            and len(data["d"]) > 0
            and data["d"][0].get("stato") == "Nessuna informazione alla palina."
        )

    def _should_renew_api_key(self, data: dict[str, Any]) -> bool:
        """Check if API response indicates invalid API key."""
        return (
            "d" in data
            and isinstance(data["d"], list)
            and len(data["d"]) > 0
            and data["d"][0].get("stato") == "Chiave non valida"
        )

    async def async_get_stop_arrivals(
        self, stop_id: str, line_filter: str | None = None
    ) -> list[ANMArrival]:
        """Get arrival information for a specific stop.

        Args:
            stop_id: The stop identifier (Palina ID)
            line_filter: Optional filter for specific lines (comma-separated for multiple)

        Returns:
            List of ANMArrival objects

        Raises:
            ANMAPIClientError: If the API request fails
        """
        session = await self._get_session()
        url = f"{self._api_base_url}{PREDICTIONS_ENDPOINT}"
        headers = self._get_predictions_headers()
        api_key = await self._get_api_key()
        payload = {"Palina": stop_id, "key": api_key}
        allowed_lines = self._parse_line_filter(line_filter)

        _LOGGER.debug("Fetching arrivals for stop %s", stop_id)
        _LOGGER.debug("Using line filter: %s", line_filter)
        _LOGGER.debug("API URL: %s", url)

        try:
            data = await self._fetch_predictions_data(session, url, payload, headers)

            # Handle invalid API key
            if self._should_renew_api_key(data):
                data = await self._handle_invalid_api_key(
                    session, url, payload, headers
                )

            # Check for no information at the stop
            if self._should_return_empty(data):
                return []

            return self._extract_arrivals_from_data(data, allowed_lines)

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching stop arrivals: %s", err)
            raise ANMAPIClientError(f"Failed to fetch data: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise ANMAPIClientError(f"Unexpected error: {err}") from err
