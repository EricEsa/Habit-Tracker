import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///habit_tracker.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") == "1"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    WTF_CSRF_TIME_LIMIT = 8 * 60 * 60
    RATELIMIT_STORAGE_URI = "memory://"
    ITEMS_PER_PAGE = 10
    TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")

    QUOTE_API_TIMEOUT = int(os.environ.get("QUOTE_API_TIMEOUT", 5))
    QUOTE_CACHE_SECONDS = int(os.environ.get("QUOTE_CACHE_SECONDS", 6 * 60 * 60))

    WEATHER_LAT = os.environ.get("WEATHER_LAT") or "48.7758"
    WEATHER_LON = os.environ.get("WEATHER_LON") or "9.1829"
    WEATHER_LOCATION_NAME = os.environ.get("WEATHER_LOCATION_NAME") or "Stuttgart"
    WEATHER_API_TIMEOUT = int(os.environ.get("WEATHER_API_TIMEOUT", 5))
    WEATHER_CACHE_SECONDS = int(os.environ.get("WEATHER_CACHE_SECONDS", 30 * 60))


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
