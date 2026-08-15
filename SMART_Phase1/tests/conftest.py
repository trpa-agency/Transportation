import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "network: hits maps.trpa.org; deselect with -m 'not network'"
    )


@pytest.fixture(scope="session")
def settings():
    from smart_config import load_settings

    return load_settings()


@pytest.fixture
def vehicle_cfg(settings):
    return settings.dataset("vehicle_counts")


@pytest.fixture
def vru_cfg(settings):
    return settings.dataset("vru_counts")


@pytest.fixture
def safety_cfg(settings):
    return settings.dataset("safety_insights")


@pytest.fixture
def speed_cfg(settings):
    return settings.dataset("speed")


@pytest.fixture
def daily_cfg(settings):
    return settings.dataset("daily_counts")
