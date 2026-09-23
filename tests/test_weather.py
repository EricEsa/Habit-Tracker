import pytest
import requests

from app.services import weather


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("Fehler")

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def reset_weather_cache():
    weather.reset_cache()
    yield
    weather.reset_cache()


def test_returns_none_when_not_configured(app):
    app.config["WEATHER_LAT"] = None
    app.config["WEATHER_LON"] = None
    with app.app_context():
        assert weather.get_current_weather() is None


def test_uses_stuttgart_by_default(app):
    with app.app_context():
        assert weather.is_configured()
        assert app.config["WEATHER_LOCATION_NAME"] == "Stuttgart"


def test_returns_weather_when_configured(app, monkeypatch):
    app.config["WEATHER_LAT"] = "52.5"
    app.config["WEATHER_LON"] = "13.4"

    def fake_get(url, params, timeout):
        return FakeResponse({"current": {"temperature_2m": 18.5, "precipitation": 0.0, "weather_code": 1}})

    monkeypatch.setattr(weather.requests, "get", fake_get)
    with app.app_context():
        data = weather.get_current_weather()
    assert data["temperature"] == 18.5
    assert data["outdoor_friendly"] is True


def test_returns_none_on_error(app, monkeypatch):
    app.config["WEATHER_LAT"] = "52.5"
    app.config["WEATHER_LON"] = "13.4"

    def fake_get(url, params, timeout):
        raise requests.ConnectionError("kein Netz")

    monkeypatch.setattr(weather.requests, "get", fake_get)
    with app.app_context():
        assert weather.get_current_weather() is None
