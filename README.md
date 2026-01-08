# ANM Integration for Home Assistant

Custom Home Assistant integration for monitoring ANM (Azienda Napoletana Mobilita) public transport stops.

## AI Assisted Notice

This project has been developed with a huge amount of assistance from AI tools (GLM 4.7, GPT-4.1 etc...)
While every effort has been made to ensure the accuracy and reliability of the code, users should be aware that AI-generated content may contain errors or omissions. Users are advised to review and test the code thoroughly before deploying it in a production environment.
The author assumes no responsibility for any issues arising from the use of this code.

## Features

- Monitor multiple bus/tram stops in Naples
- Optional line filtering to track specific routes (supports multiple lines like "R1,R2,R3")
- Real-time arrival information
- UI-based configuration via Home Assistant's config flow
- Automatic periodic updates

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click "+" and search for "ANM"
4. Click Download and follow the setup instructions

### Manual Installation

1. Copy the `custom_components/anm` directory to your Home Assistant configuration
2. Restart Home Assistant
3. Go to Settings -> Devices & Services -> Add Integration
4. Search for "ANM" and follow the setup wizard

## Configuration

### Initial Setup (Optional)

- **API Base URL**: The ANM API endpoint (default: https://srv.anm.it)
- **Update Interval**: How often to refresh data (default: 60 seconds, min: 10, max: 3600)
- **Timeout**: API request timeout (default: 10 seconds, min: 5, max: 60)

### Add Stops

- **Stop ID**: The numeric identifier for the bus/tram stop (required)
- **Stop Name**: A human-readable name for display (required)
- **Line Filter**: Optional filter for specific routes (e.g., "R1" or "R1,R2,R3" for multiple lines)

You can add multiple stops during configuration. At least one stop is required.

## Sensors

Each monitored stop creates a sensor entity with:

### State

- **Next arrival time**: ISO timestamp of the first upcoming arrival

### Attributes

- `stop_id`: The stop identifier
- `stop_name`: Human-readable stop name
- `line_filter`: Configured line filter (if any)
- `next_arrivals`: List of upcoming arrivals
  - `line`: Route line (e.g., "R1")
  - `destination`: Destination of the vehicle
  - `arrival_time`: Predicted arrival time (ISO format)
  - `time_minutes`: Time until arrival in minutes
  - `vehicle_id`: Unique vehicle identifier
- `last_updated`: Last successful API fetch timestamp

## Finding Stop IDs

Stop IDs are numeric codes assigned to each bus/tram stop. You can find them:

- Through the official ANM website
- Via the ANM mobile app
- At physical stops (typically displayed on signage)

## Troubleshooting

If sensors show unavailable or stale data:

- Verify the stop ID is correct
- Check your network connection to ANM servers
- Review Home Assistant logs for error messages
- Try increasing the update interval if API rate limits are encountered

## Development

### Setting Up Development Environment

#### Using UV (Recommended)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install test dependencies
make install-deps

# Run tests
make test

# Or run specific tests
make test-api    # API tests only
make test-unit   # Config flow and coordinator tests
```

#### Manual Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v
```

### Testing with local Home Assistant using Docker

- Add a `config` directory
- (Optional) Enable extensions logs for the anm integration in configuration.yaml:

```yaml
logger:
  default: warning
  logs:
    custom_components.anm: debug
```

- Run Home Assistant container using Docker Compose:

```bash
docker compose up -d
```

- Access Home Assistant at `http://localhost:8123`

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Full check (format + lint + type-check + test)
make check
```

## Testing

This project includes comprehensive test coverage using pytest and aioresponses.

### Test Structure

- `tests/test_api.py`: Tests for ANM API client
- `tests/test_config_flow.py`: Tests for configuration flow
- `tests/test_coordinator.py`: Tests for data update coordinator

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=custom_components/anm --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### CI/CD

GitHub Actions automatically runs tests on push and pull requests with Python 3.13.

## License

MIT License

## Support

For issues, feature requests, or contributions, please use the GitHub issue tracker.

---

**Note**: This is an unofficial integration for ANM public transport services in Naples, Italy.
