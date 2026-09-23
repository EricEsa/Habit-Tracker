import random
import time

import requests
from flask import current_app

FALLBACK_QUOTES = [
    {"text": "Der Weg entsteht beim Gehen.", "author": "Sprichwort"},
    {"text": "Kleine Schritte führen zu großen Veränderungen.", "author": "Unbekannt"},
    {"text": "Disziplin ist die Brücke zwischen Zielen und Erfolg.", "author": "Jim Rohn"},
    {"text": "Eine Gewohnheit ist ein Seil. Wir weben jeden Tag einen Faden hinzu.", "author": "Horace Mann"},
    {"text": "Man muss das Unmögliche versuchen, um das Mögliche zu erreichen.", "author": "Hermann Hesse"},
    {"text": "Erfolg ist die Summe kleiner Anstrengungen, jeden Tag wiederholt.", "author": "Robert Collier"},
    {"text": "Beginne dort, wo du stehst, mit dem, was du hast.", "author": "Arthur Ashe"},
    {"text": "Was du heute übst, wirst du morgen können.", "author": "Sprichwort"},
]

_cache = {"quote": None, "expires_at": 0.0}


def _fetch_from_api(timeout):
    response = requests.get("https://zenquotes.io/api/today", timeout=timeout)
    response.raise_for_status()
    item = response.json()[0]
    text, author = item["q"], item["a"]
    if not text or not author:
        raise ValueError("Leere Antwort der Zitat-API.")
    return {"text": text, "author": author}


def get_daily_quote():
    """Tageszitat mit Cache. Bei jedem Fehler wird ein lokales Zitat verwendet."""
    now = time.time()
    if _cache["quote"] is not None and _cache["expires_at"] > now:
        return _cache["quote"]

    timeout = current_app.config.get("QUOTE_API_TIMEOUT", 5)
    ttl = current_app.config.get("QUOTE_CACHE_SECONDS", 6 * 60 * 60)

    try:
        quote = _fetch_from_api(timeout)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        quote = random.choice(FALLBACK_QUOTES)

    _cache["quote"] = quote
    _cache["expires_at"] = now + ttl
    return quote


def reset_cache():
    """Nur für Tests: leert den Cache."""
    _cache["quote"] = None
    _cache["expires_at"] = 0.0
