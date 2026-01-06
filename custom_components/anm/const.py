"""Constants for the ANM integration."""

from typing import Final

DOMAIN: Final = "anm"
DEFAULT_NAME: Final = "ANM"

DEFAULT_API_BASE_URL: Final = "https://srv.anm.it"  # ANM API base URL
DEFAULT_UPDATE_INTERVAL: Final = 60
DEFAULT_TIMEOUT: Final = 10

CONF_STOPS: Final = "stops"
CONF_STOP_ID: Final = "stop_id"
CONF_STOP_NAME: Final = "stop_name"
CONF_LINE_FILTER: Final = "line_filter"
CONF_API_BASE_URL: Final = "api_base_url"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_TIMEOUT: Final = "timeout"

STEP_USER: Final = "user"
STEP_STOPS: Final = "stops"
STEP_ADD_STOP: Final = "add_stop"
STEP_REMOVE_STOP: Final = "remove_stop"
STEP_FINISH: Final = "finish"

CONF_ADD_ANOTHER: Final = "add_another"
CONF_FINISH: Final = "finish"
CONF_REMOVE_STOP: Final = "remove_stop"

SENSOR_TYPE_STOP: Final = "stop"

ATTR_STOP_ID: Final = "stop_id"
ATTR_STOP_NAME: Final = "stop_name"
ATTR_LINE_FILTER: Final = "line_filter"
ATTR_NEXT_ARRIVALS: Final = "next_arrivals"
ATTR_LAST_UPDATED: Final = "last_updated"
ATTR_LINE: Final = "line"
ATTR_DESTINATION: Final = "destination"
ATTR_ARRIVAL_TIME: Final = "arrival_time"
ATTR_TIME_MINUTES: Final = "time_minutes"

DATA_COORDINATOR: Final = "coordinator"
DATA_API_CLIENT: Final = "api_client"
