from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import Habit, HabitLog
from app.services.streaks import current_streak, longest_streak, success_rate
from app.utils import today_local

TODAY = date(2026, 9, 21)


def days(*numbers):
    return {date(2026, 9, n) for n in numbers}


def daily_habit(start=date(2026, 9, 1)):
    return Habit(frequency="daily", start_date=start, target_per_period=1, weekdays="")


def weekly_habit(target=2):
    return Habit(frequency="weekly", start_date=date(2026, 9, 1), target_per_period=target, weekdays="")


def test_current_streak_counts_consecutive_days():
    assert current_streak(daily_habit(), days(19, 20, 21), TODAY) == 3


def test_current_streak_survives_open_today():
    assert current_streak(daily_habit(), days(18, 19, 20), TODAY) == 3


def test_current_streak_breaks_after_missed_day():
    assert current_streak(daily_habit(), days(17, 18, 20, 21), TODAY) == 2


def test_current_streak_is_zero_when_yesterday_was_missed():
    assert current_streak(daily_habit(), days(15, 16, 17), TODAY) == 0


def test_longest_streak():
    assert longest_streak(daily_habit(), days(1, 2, 3, 4, 5, 10, 11, 20, 21), TODAY) == 5


def test_longest_streak_open_today_does_not_reset():
    assert longest_streak(daily_habit(), days(19, 20), TODAY) == 2


def test_streak_skips_days_that_are_not_due():
    habit = Habit(frequency="weekdays", weekdays="0,2,4", start_date=date(2026, 9, 1), target_per_period=1)
    completed = {date(2026, 9, 21), date(2026, 9, 18), date(2026, 9, 16)}
    assert current_streak(habit, completed, TODAY) == 3


def test_weekly_streak_counts_weeks():
    completed = days(8, 10, 14, 16, 21)
    assert current_streak(weekly_habit(), completed, TODAY) == 2
    assert longest_streak(weekly_habit(), completed, TODAY) == 2


def test_weekly_streak_includes_current_week_once_target_is_reached():
    assert current_streak(weekly_habit(), days(8, 10, 14, 16, 21, 22), TODAY) == 3


def test_success_rate_daily():
    habit = daily_habit()
    assert success_rate(habit, days(15, 16, 17, 18, 19, 20, 21), TODAY, 7) == 1.0
    assert success_rate(habit, days(15, 16, 17, 18), TODAY, 7) == pytest.approx(4 / 7)


def test_success_rate_is_limited_by_start_date():
    habit = daily_habit(start=date(2026, 9, 19))
    assert success_rate(habit, days(19, 20), TODAY, 30) == pytest.approx(2 / 3)


def test_success_rate_is_none_before_start():
    assert success_rate(daily_habit(start=date(2026, 9, 22)), set(), TODAY, 7) is None


@pytest.fixture()
def today(app):
    with app.app_context():
        return today_local()


def log_url(habit_id):
    return f"/api/habits/{habit_id}/log"


def load_logs(app):
    with app.app_context():
        logs = db.session.scalars(select(HabitLog).order_by(HabitLog.date)).all()
        return [{"date": log.date, "completed": log.completed, "note": log.note} for log in logs]


def test_api_requires_login(client, make_user, make_habit):
    habit_id = make_habit(make_user())
    response = client.post(log_url(habit_id), json={})
    assert response.status_code == 401
    assert response.get_json()["error"]


def test_log_marks_today_as_done(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today - timedelta(days=5))
    login()
    response = client.post(log_url(habit_id), json={"completed": True})
    data = response.get_json()
    assert response.status_code == 200
    assert data["completed"] is True
    assert data["date"] == today.isoformat()
    assert data["streak"] == 1
    assert data["streak_unit"] == "Tage"
    assert data["week_count"] is None
    assert len(load_logs(app)) == 1


def test_log_without_completed_toggles(client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    first = client.post(log_url(habit_id), json={}).get_json()
    second = client.post(log_url(habit_id), json={}).get_json()
    assert first["completed"] is True
    assert second["completed"] is False
    assert second["streak"] == 0


def test_log_past_day_with_note(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today - timedelta(days=10))
    login()
    day = today - timedelta(days=2)
    response = client.post(
        log_url(habit_id), json={"date": day.isoformat(), "completed": True, "note": "  Lief gut  "}
    )
    assert response.get_json()["note"] == "Lief gut"
    assert load_logs(app) == [{"date": day, "completed": True, "note": "Lief gut"}]


def test_log_keeps_note_when_it_is_not_sent(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    client.post(log_url(habit_id), json={"completed": True, "note": "Wichtig"})
    client.post(log_url(habit_id), json={"completed": False})
    assert load_logs(app)[0]["note"] == "Wichtig"
    client.post(log_url(habit_id), json={"note": ""})
    assert load_logs(app)[0]["note"] is None


def test_log_rejects_future_date(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    tomorrow = today + timedelta(days=1)
    response = client.post(log_url(habit_id), json={"date": tomorrow.isoformat()})
    assert response.status_code == 400
    assert load_logs(app) == []


def test_log_rejects_date_before_start(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today - timedelta(days=1))
    login()
    response = client.post(log_url(habit_id), json={"date": (today - timedelta(days=3)).isoformat()})
    assert response.status_code == 400
    assert load_logs(app) == []


@pytest.mark.parametrize("payload", [
    {"date": "gestern"},
    {"completed": "ja"},
    {"note": "x" * 501},
    {"note": 42},
])
def test_log_rejects_invalid_input(app, client, make_user, make_habit, login, today, payload):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    assert client.post(log_url(habit_id), json=payload).status_code == 400
    assert load_logs(app) == []


def test_cannot_log_foreign_habit(app, client, make_user, make_habit, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    habit_id = make_habit(other_id)
    login()
    response = client.post(log_url(habit_id), json={"completed": True})
    assert response.status_code == 404
    assert response.get_json()["error"]
    assert load_logs(app) == []


def test_weekly_log_returns_week_count(client, make_user, make_habit, login, today):
    habit_id = make_habit(
        make_user(), frequency="weekly", target_per_period=3, start_date=today - timedelta(days=10)
    )
    login()
    data = client.post(log_url(habit_id), json={"completed": True}).get_json()
    assert data["week_count"] == 1
    assert data["streak_unit"] == "Wochen"


def test_dashboard_lists_only_due_habits(client, make_user, make_habit, login, today):
    user_id = make_user()
    other_id = make_user("berta", "berta@example.com")
    start = today - timedelta(days=3)
    make_habit(user_id, "Laufen", start_date=start)
    make_habit(user_id, "Altes Hobby", start_date=start, is_archived=True)
    make_habit(other_id, "Nachbars Habit", start_date=start)
    make_habit(
        user_id, "Nur morgen", frequency="weekdays", weekdays=str((today.weekday() + 1) % 7), start_date=start
    )
    login()
    html = client.get("/heute").get_data(as_text=True)
    assert "Laufen" in html
    assert "Altes Hobby" not in html
    assert "Nachbars Habit" not in html
    assert "Nur morgen" not in html


def test_dashboard_shows_progress(client, make_user, make_habit, login, today):
    user_id = make_user()
    first = make_habit(user_id, "Laufen", start_date=today)
    make_habit(user_id, "Lesen", start_date=today)
    login()
    assert "0 von 2" in client.get("/heute").get_data(as_text=True)
    client.post(log_url(first), json={"completed": True})
    assert "1 von 2" in client.get("/heute").get_data(as_text=True)


def test_detail_page_shows_stats(client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), "Laufen", start_date=today - timedelta(days=5))
    login()
    response = client.get(f"/habits/{habit_id}")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Laufen" in html
    assert "Aktuelle Serie" in html


def test_detail_page_of_foreign_habit_is_404(client, make_user, make_habit, login):
    make_user()
    habit_id = make_habit(make_user("berta", "berta@example.com"))
    login()
    assert client.get(f"/habits/{habit_id}").status_code == 404


def test_add_log_for_past_day(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today - timedelta(days=10))
    login()
    day = today - timedelta(days=3)
    response = client.post(
        f"/habits/{habit_id}/eintrag",
        data={"date": day.isoformat(), "completed": "y", "note": "Regen"},
        follow_redirects=True,
    )
    assert "Eintrag wurde gespeichert" in response.get_data(as_text=True)
    assert load_logs(app) == [{"date": day, "completed": True, "note": "Regen"}]


def test_add_log_rejects_future_date(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    tomorrow = today + timedelta(days=1)
    response = client.post(f"/habits/{habit_id}/eintrag", data={"date": tomorrow.isoformat(), "completed": "y"})
    assert "nicht in der Zukunft" in response.get_data(as_text=True)
    assert load_logs(app) == []


def test_add_log_rejects_date_before_start(app, client, make_user, make_habit, login, today):
    habit_id = make_habit(make_user(), start_date=today)
    login()
    day = today - timedelta(days=2)
    response = client.post(f"/habits/{habit_id}/eintrag", data={"date": day.isoformat(), "completed": "y"})
    assert "vor dem Startdatum" in response.get_data(as_text=True)
    assert load_logs(app) == []


def test_cannot_add_log_to_foreign_habit(app, client, make_user, make_habit, login, today):
    make_user()
    habit_id = make_habit(make_user("berta", "berta@example.com"), start_date=today)
    login()
    response = client.post(f"/habits/{habit_id}/eintrag", data={"date": today.isoformat(), "completed": "y"})
    assert response.status_code == 404
    assert load_logs(app) == []
