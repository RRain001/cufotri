from pathlib import Path

import pytest

from era5.download_era5_timeseries import load_credentials


def test_credentials_can_come_from_environment(monkeypatch):
    monkeypatch.setenv("CDSAPI_URL", "https://example.invalid/api")
    monkeypatch.setenv("CDSAPI_KEY", "placeholder")
    assert load_credentials(Path("missing")) == (
        "https://example.invalid/api",
        "placeholder",
    )


def test_partial_environment_credentials_fail(monkeypatch):
    monkeypatch.setenv("CDSAPI_URL", "https://example.invalid/api")
    monkeypatch.delenv("CDSAPI_KEY", raising=False)
    with pytest.raises(ValueError, match="must be set together"):
        load_credentials(Path("missing"))
