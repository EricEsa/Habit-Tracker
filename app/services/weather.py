import time

import requests
from flask import current_app

_cache = {"weather": None, "expires_at": 0.0}


def is_configured():
    return bool(current_app.config.get("WEATHER_LAT") and current_app.config.get("WEATHER_LON"))


def _fetch_from_api(lat, lon, timeout):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,weather_code",
            "timezone": "auto",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    current = response.json()["current"]
    return {
        "temperature": current["temperature_2m"],
        "precipitation": current["precipitation"],
        "weather_code": current["weather_code"],
    }


def get_current_weather():
    """Aktuelles Wetter am konfigurierten Ort. None ohne Konfiguration oder bei Fehlern."""
    if not is_configured():
        return None

    now = time.time()
    if _cache["weather"] is not None and _cache["expires_at"] > now:
        return _cache["weather"]

    lat = current_app.config["WEATHER_LAT"]
    lon = current_app.config["WEATHER_LON"]
    timeout = current_app.config.get("WEATHER_API_TIMEOUT", 5)
    ttl = current_app.config.get("WEATHER_CACHE_SECONDS", 30 * 60)

    try:
        weather = _fetch_from_api(lat, lon, timeout)
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None

    weather["outdoor_friendly"] = weather["precipitation"] < 0.5
    weather["location_name"] = current_app.config.get("WEATHER_LOCATION_NAME", "")
    _cache["weather"] = weather
    _cache["expires_at"] = now + ttl
    return weather


def reset_cache():
    """Nur für Tests: leert den Cache."""
    _cache["weather"] = None
    _cache["expires_at"] = 0.0
