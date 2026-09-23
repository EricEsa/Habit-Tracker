import pytest

from app import create_app
from app.extensions import db
from config import TestingConfig


class RateLimitedConfig(TestingConfig):
    RATELIMIT_ENABLED = True


@pytest.fixture()
def limited_client():
    app = create_app(RateLimitedConfig)
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_login_is_rate_limited(limited_client):
    data = {"identifier": "nobody", "password": "wrong"}
    for _ in range(10):
        response = limited_client.post("/login", data=data)
        assert response.status_code == 200
    response = limited_client.post("/login", data=data)
    assert response.status_code == 429


def test_register_is_rate_limited(limited_client):
    data = {"username": "x", "email": "x", "password": "x", "password2": "y"}
    for _ in range(5):
        response = limited_client.post("/registrieren", data=data)
        assert response.status_code == 200
    response = limited_client.post("/registrieren", data=data)
    assert response.status_code == 429
