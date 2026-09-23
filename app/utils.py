from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import abort, current_app
from flask_login import current_user

from app.extensions import db


def owned_or_404(model, object_id):
    obj = db.session.get(model, object_id)
    if obj is None or obj.user_id != current_user.id:
        abort(404)
    return obj


def today_local() -> date:
    """Heutiges Datum in der App-Zeitzone (Standard: Europe/Berlin)."""
    name = current_app.config.get("TIMEZONE", "Europe/Berlin")
    try:
        return datetime.now(ZoneInfo(name)).date()
    except ZoneInfoNotFoundError:
        return date.today()
