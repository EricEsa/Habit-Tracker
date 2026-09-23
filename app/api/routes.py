from datetime import date
from functools import wraps

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user

from app.models import FREQ_WEEKLY, Habit
from app.services.search import run_search
from app.services.streaks import current_streak, streak_unit, week_progress
from app.services.tracking import KEEP, completed_dates_by_habit, set_completion
from app.utils import owned_or_404, today_local

from datetime import timedelta

from app.extensions import db
from app.models import Category, Habit
from app.services.streaks import MILESTONES, longest_streak, milestones_reached, success_rate, week_start
from app.services.tracking import completed_dates_by_habit
from sqlalchemy import select

bp = Blueprint("api", __name__, url_prefix="/api")


def api_login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(error="Bitte melde dich an."), 401
        return view(*args, **kwargs)

    return wrapper


@bp.get("/habits/suche")
@api_login_required
def search():
    filters, page, cards = run_search(
        current_user.id, request.args, today_local(), current_app.config["ITEMS_PER_PAGE"]
    )
    html = render_template("habits/_results.html", filters=filters, page=page, cards=cards)
    return jsonify(html=html, total=page.total, page=page.page, pages=page.pages)


@bp.post("/habits/<int:habit_id>/log")
@api_login_required
def log_habit(habit_id):
    habit = owned_or_404(Habit, habit_id)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    today = today_local()

    try:
        day = date.fromisoformat(data["date"]) if data.get("date") else today
    except (TypeError, ValueError):
        return jsonify(error="Ungültiges Datum."), 400
    if day > today:
        return jsonify(error="Das Datum liegt in der Zukunft."), 400
    if day < habit.start_date:
        return jsonify(error="Das Datum liegt vor dem Startdatum."), 400

    completed = data.get("completed")
    if completed is not None and not isinstance(completed, bool):
        return jsonify(error="Ungültiger Wert für „completed“."), 400

    note = KEEP
    if "note" in data:
        raw = data["note"]
        if raw is not None and (not isinstance(raw, str) or len(raw) > 500):
            return jsonify(error="Die Notiz ist ungültig oder länger als 500 Zeichen."), 400
        note = (raw or "").strip() or None

    log = set_completion(habit, day, completed, note)
    dates = completed_dates_by_habit([habit.id])[habit.id]
    return jsonify(
        date=day.isoformat(),
        completed=log.completed,
        note=log.note,
        streak=current_streak(habit, dates, today),
        streak_unit=streak_unit(habit),
        week_count=week_progress(habit, dates, today) if habit.frequency == FREQ_WEEKLY else None,
    )

@bp.get("/stats/uebersicht")
@api_login_required
def stats_overview():
    today = today_local()
    habits = db.session.scalars(
        select(Habit).where(Habit.user_id == current_user.id, Habit.is_archived.is_(False))
    ).all()
    completed = completed_dates_by_habit([habit.id for habit in habits])

    weeks = [week_start(today) - timedelta(weeks=i) for i in range(11, -1, -1)]
    weekly_counts = []
    for week in weeks:
        count = sum(1 for dates in completed.values() for day in dates if week_start(day) == week)
        weekly_counts.append(count)

    success = []
    for habit in habits:
        rate = success_rate(habit, completed[habit.id], today, 30)
        success.append({"title": habit.title, "rate": round(rate * 100) if rate is not None else 0})
    success.sort(key=lambda item: item["rate"], reverse=True)

    category_counts = {}
    for habit in habits:
        name = habit.category.name if habit.category else "Ohne Kategorie"
        category_counts[name] = category_counts.get(name, 0) + 1

    heatmap_start = today - timedelta(weeks=26)
    heatmap = {}
    for habit in habits:
        heatmap[habit.id] = sorted(
            day.isoformat() for day in completed[habit.id] if day >= heatmap_start
        )
    combined = sorted({day.isoformat() for dates in completed.values() for day in dates if day >= heatmap_start})

    milestones = []
    for habit in habits:
        reached = milestones_reached(habit, completed[habit.id], today)
        if reached:
            milestones.append({"title": habit.title, "milestones": reached, "best": longest_streak(habit, completed[habit.id], today)})

    return jsonify(
        weekly_labels=[week.strftime("%d.%m.") for week in weeks],
        weekly_counts=weekly_counts,
        success_rates=success,
        category_labels=list(category_counts.keys()),
        category_counts=list(category_counts.values()),
        heatmap_start=heatmap_start.isoformat(),
        heatmap_today=today.isoformat(),
        heatmap_combined=combined,
        heatmap_by_habit=heatmap,
        habits=[{"id": h.id, "title": h.title} for h in habits],
        all_milestones=list(MILESTONES),
        milestones=milestones,
    )
