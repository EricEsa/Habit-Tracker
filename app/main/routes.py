from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models import FREQ_WEEKLY
from app.services.quotes import get_daily_quote
from app.services.streaks import current_streak, streak_unit, week_progress
from app.services.tracking import completed_dates_by_habit, habits_due_on
from app.services.weather import get_current_weather
from app.utils import today_local

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@bp.route("/heute")
@login_required
def dashboard():
    today = today_local()
    habits = habits_due_on(current_user.id, today)
    completed = completed_dates_by_habit([habit.id for habit in habits])

    items = []
    for habit in habits:
        dates = completed[habit.id]
        items.append({
            "habit": habit,
            "done": today in dates,
            "streak": current_streak(habit, dates, today),
            "unit": streak_unit(habit),
            "week_count": week_progress(habit, dates, today) if habit.frequency == FREQ_WEEKLY else None,
        })

    done = sum(1 for item in items if item["done"])
    percent = round(done / len(items) * 100) if items else 0
    return render_template(
        "dashboard.html",
        today=today,
        items=items,
        done=done,
        percent=percent,
        quote=get_daily_quote(),
        weather=get_current_weather(),
    )
