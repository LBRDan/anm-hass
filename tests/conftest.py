"""pytest configuration for ANM integration tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(scope="session", autouse=True)
def auto_load_custom_components():
    """Automatically load custom components for testing."""
    # Add custom_components to Python path so pytest-homeassistant-custom-component can find our integration
    custom_components_path = Path(__file__).parent.parent / "custom_components"
    if str(custom_components_path) not in sys.path:
        sys.path.insert(0, str(custom_components_path))

    # Also add to help with integration discovery
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    if enable_custom_integrations is not None:
        enable_custom_integrations()


@pytest.fixture
def api_response_fixture():
    """Fixture to load API response files."""

    def _load_response(file_name: str) -> str:
        base_path = os.path.join(os.path.dirname(__file__), "fixtures", "api_responses")
        file_path = os.path.join(base_path, file_name)
        with open(file_path, encoding="utf-8") as file:
            return file.read()

    return _load_response
