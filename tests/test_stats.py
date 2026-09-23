from datetime import timedelta

import pytest

from app.extensions import db
from app.models import HabitLog
from app.utils import today_local


@pytest.fixture()
def today(app):
    with app.app_context():
        return today_local()


def add_logs(app, habit_id, days):
    with app.app_context():
        for day in days:
            db.session.add(HabitLog(habit_id=habit_id, date=day, completed=True))
        db.session.commit()


def test_stats_page_requires_login(client):
    response = client.get("/statistiken")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_stats_page_loads(client, make_user, login):
    make_user()
    login()
    assert client.get("/statistiken").status_code == 200


def test_overview_requires_login(client):
    assert client.get("/api/stats/uebersicht").status_code == 401


def test_overview_is_empty_for_new_user(client, make_user, login):
    make_user()
    login()
    data = client.get("/api/stats/uebersicht").get_json()
    assert data["habits"] == []
    assert data["milestones"] == []
    assert sum(data["weekly_counts"]) == 0


def test_overview_counts_weekly_completions(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    habit_id = make_habit(user_id, "Laufen", start_date=today - timedelta(days=20))
    add_logs(app, habit_id, [today, today - timedelta(days=1), today - timedelta(days=7)])
    login()
    data = client.get("/api/stats/uebersicht").get_json()
    assert len(data["weekly_labels"]) == 12
    assert sum(data["weekly_counts"]) == 3
    assert data["weekly_counts"][-1] == 2


def test_overview_success_rate_is_sorted_descending(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    strong = make_habit(user_id, "Stark", start_date=today - timedelta(days=10))
    weak = make_habit(user_id, "Schwach", start_date=today - timedelta(days=10))
    add_logs(app, strong, [today - timedelta(days=i) for i in range(11)])
    add_logs(app, weak, [today])
    login()
    rates = client.get("/api/stats/uebersicht").get_json()["success_rates"]
    assert rates[0]["title"] == "Stark"
    assert rates[0]["rate"] == 100
    assert rates[-1]["title"] == "Schwach"


def test_overview_groups_by_category(client, make_user, make_habit, make_category, login, today):
    user_id = make_user()
    sport = make_category(user_id, "Sport")
    make_habit(user_id, "Laufen", category_id=sport, start_date=today)
    make_habit(user_id, "Lesen", category_id=sport, start_date=today)
    make_habit(user_id, "Ohne Kategorie", start_date=today)
    login()
    data = client.get("/api/stats/uebersicht").get_json()
    combined = dict(zip(data["category_labels"], data["category_counts"]))
    assert combined["Sport"] == 2
    assert combined["Ohne Kategorie"] == 1


def test_overview_ignores_archived_habits(client, make_user, make_habit, login, today):
    user_id = make_user()
    make_habit(user_id, "Aktiv", start_date=today)
    make_habit(user_id, "Archiviert", start_date=today, is_archived=True)
    login()
    titles = [h["title"] for h in client.get("/api/stats/uebersicht").get_json()["habits"]]
    assert "Aktiv" in titles
    assert "Archiviert" not in titles


def test_overview_heatmap_data(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    habit_id = make_habit(user_id, "Laufen", start_date=today - timedelta(days=5))
    add_logs(app, habit_id, [today, today - timedelta(days=2)])
    login()
    data = client.get("/api/stats/uebersicht").get_json()
    assert today.isoformat() in data["heatmap_combined"]
    assert today.isoformat() in data["heatmap_by_habit"][str(habit_id)]


def test_overview_milestones(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    habit_id = make_habit(user_id, "Serientäter", start_date=today - timedelta(days=10))
    add_logs(app, habit_id, [today - timedelta(days=i) for i in range(7)])
    login()
    data = client.get("/api/stats/uebersicht").get_json()
    assert len(data["milestones"]) == 1
    assert data["milestones"][0]["milestones"] == [7]
    assert data["all_milestones"] == [7, 30, 100]


def test_overview_only_shows_own_data(client, make_user, make_habit, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    make_habit(other_id, "Fremd")
    login()
    assert client.get("/api/stats/uebersicht").get_json()["habits"] == []
