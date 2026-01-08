# ANM Home Assistant Integration - Development Guidelines

This document contains guidelines for AI agents working on the ANM (Azienda Napoletana Mobilita) Home Assistant integration.

## Development Commands

Note: This repository uses [UV](https://uv.dev/) for dependency management and virtual environments.
Always activate the virtual environment before running commands.

Use uv install to install the appropriate Python version and `uv sync` to install dependencies.

Alternatively, you can use the provided Makefile commands for common tasks.

### Environment Setup

```bash
# Install dependencies (requires UV)
make install-deps

# Manual setup (alternative)
python -m venv .venv
source .venv/bin/activate
uv sync
```

### Testing Commands

```bash
# Run all tests
make test
pytest tests/ -v

# Run specific test files
pytest tests/test_api.py -v
pytest tests/test_config_flow.py -v
pytest tests/test_coordinator.py -v

# Run tests with coverage
make test-coverage
pytest tests/ --cov=custom_components/anm --cov-report=html

# Run tests for specific functionality
pytest tests/ -k "test_async_get_stop_arrivals" -v
pytest tests/ -m "asyncio" -v
```

### Code Quality Commands

```bash
# Format code
make format
ruff format custom_components/ tests/

# Sort imports
make sort-imports
ruff check --select I --fix custom_components/ tests/

# Lint code
make lint
ruff check custom_components/ tests/

# Type checking
make type-check
mypy custom_components/ tests/

# Full quality check
make check  # Runs format + lint + type-check + test
```

### Docker Development

```bash
# Start Home Assistant with integration
docker compose up -d

# Access at http://localhost:8123
```

## Code Style Guidelines

### Import Organization

- Use ruff for import sorting (configured in pyproject.toml)
- Use `from __future__ import annotations` for type hints compatibility
- Example structure:

```python
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import ANMDataUpdateCoordinator
```

### Type Hints

- All functions and methods must have type hints
- Use `|` union syntax (Python 3.13+) instead of `Union`
- Use `dict[str, Any]` instead of `Dict[str, Any]`
- Use `list[Type]` instead of `List[Type]`
- Always return `None` explicitly for void functions

### Naming Conventions

- **Constants**: `UPPER_SNAKE_CASE` (use `Final` typing)
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Private methods**: `_snake_case`
- **Configuration keys**: `UPPER_SNAKE_CASE` with `CONF_` prefix
- **Data keys**: `UPPER_SNAKE_CASE` with `DATA_` prefix
- **Attribute keys**: `UPPER_SNAKE_CASE` with `ATTR_` prefix

### Error Handling

- Create custom exception classes that inherit from `Exception`
- Use `from err` to chain exceptions
- Log errors with appropriate level (error for failures, warning for recoverable issues)
- Always raise domain-specific exceptions from API/client modules
- Example:

```python
class ANMAPIClientError(Exception):
    """Exception raised for ANM API errors."""

try:
    await session.get(url)
except aiohttp.ClientError as err:
    _LOGGER.error("API request failed: %s", err)
    raise ANMAPIClientError(f"Failed to fetch data: {err}") from err
```

### Async/Await Patterns

- All API calls must be async
- Use `async with` for aiohttp sessions and context managers
- Properly close resources in `finally` or `async def close()` methods
- Mark async test functions with `@pytest.mark.asyncio`

### Home Assistant Integration Patterns

- **Constants**: Define in `const.py` with `Final` typing
- **Config Flow**: Inherit from `ConfigFlow` and use `vol.Schema`
- **Coordinators**: Inherit from `DataUpdateCoordinator`
- **Sensors**: Inherit from `CoordinatorEntity` and `SensorEntity`
- **API Clients**: Use aiohttp for HTTP requests
- **Logging**: Use module-level `_LOGGER = logging.getLogger(__name__)`

### Documentation Standards

- All modules must have module docstrings
- All public functions/methods must have docstrings following Google/NumPy style
- Use Args, Returns, and Raises sections in docstrings
- Include type information in docstrings when not obvious

### Testing Guidelines

- Use pytest with asyncio mode
- Mock external HTTP calls with aioresponses
- Load test fixtures from `tests/fixtures/api_responses/`
- Each test function should test a single behavior
- Use descriptive test names starting with `test_`
- Use fixtures for common test data
- Test both success and error cases

### Code Structure

- **api.py**: External API client and data models
- **coordinator.py**: DataUpdateCoordinator implementation
- **config_flow.py**: Configuration flow handling
- **sensor.py**: Sensor entity definitions
- **const.py**: Integration constants and configuration keys
- \***\*init**.py\*\*: Integration setup and entry point
- **strings.json**: Localization strings
- **manifest.json**: Integration metadata

### Configuration Management

- Store configuration in ConfigEntry data
- Use constants for all configuration keys
- Validate configuration in config flow
- Support optional configuration with sensible defaults

### Data Models

- Use dataclasses or simple classes for complex data
- Implement `to_dict()` methods for serialization
- Keep data models immutable where possible
- Use type hints for all model properties

## Best Practices

- Make sure to use uv and activate the virtual environment before running commands
- Always handle network timeouts and connection errors
- Implement proper resource cleanup (async close methods)
- Use Home Assistant's built-in constants where available
- Follow Home Assistant's integration patterns and conventions
- Test with multiple Python versions (3.13+)
- Ensure async code doesn't block event loop
- Use appropriate logging levels (debug for detailed info, error for failures)
- Validate external data before using it
- Implement retry logic for transient failures where appropriate

## Integration-Specific Notes

- ANM API requires dynamic API key renewal via web scraping
- XML parsing for stops endpoint, JSON for predictions
- Line filtering supports comma-separated values (e.g., "R1,R2,R3")
- Time parsing requires handling HH:mm format
- Default update interval is 60 seconds (minimum 10, maximum 3600)
- All HTTP requests must include specific headers for ANM API compatibility
