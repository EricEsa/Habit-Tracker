import pytest
import requests

from app.services import quotes


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
def reset_quote_cache():
    quotes.reset_cache()
    yield
    quotes.reset_cache()


def test_returns_quote_from_api(app, monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse([{"q": "Testzitat", "a": "Test Autor"}])

    monkeypatch.setattr(quotes.requests, "get", fake_get)
    with app.app_context():
        quote = quotes.get_daily_quote()
    assert quote == {"text": "Testzitat", "author": "Test Autor"}


def test_falls_back_on_timeout(app, monkeypatch):
    def fake_get(url, timeout):
        raise requests.Timeout("zu langsam")

    monkeypatch.setattr(quotes.requests, "get", fake_get)
    with app.app_context():
        quote = quotes.get_daily_quote()
    assert quote in quotes.FALLBACK_QUOTES


def test_falls_back_on_bad_status(app, monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse({}, status=500)

    monkeypatch.setattr(quotes.requests, "get", fake_get)
    with app.app_context():
        quote = quotes.get_daily_quote()
    assert quote in quotes.FALLBACK_QUOTES


def test_falls_back_on_malformed_json(app, monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse([{"q": "", "a": ""}])

    monkeypatch.setattr(quotes.requests, "get", fake_get)
    with app.app_context():
        quote = quotes.get_daily_quote()
    assert quote in quotes.FALLBACK_QUOTES


def test_caches_result_between_calls(app, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return FakeResponse([{"q": "Erstes Zitat", "a": "A"}])

    monkeypatch.setattr(quotes.requests, "get", fake_get)
    with app.app_context():
        first = quotes.get_daily_quote()
        second = quotes.get_daily_quote()
    assert first == second
    assert len(calls) == 1


def test_dashboard_shows_a_quote(client, make_user, login):
    make_user()
    login()
    html = client.get("/heute").get_data(as_text=True)
    assert "quote-card" in html
