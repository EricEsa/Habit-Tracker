from datetime import timedelta

import pytest

from app.extensions import db
from app.models import Habit, HabitLog, Tag
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


def attach_tag(app, habit_id, tag_id):
    with app.app_context():
        habit = db.session.get(Habit, habit_id)
        tag = db.session.get(Tag, tag_id)
        habit.tags.append(tag)
        db.session.commit()


def page(client, query=""):
    response = client.get(f"/habits{query}")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_search_matches_title_and_description(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Frühsport", description="Morgens joggen im Park")
    make_habit(user_id, "Buch lesen")
    make_habit(user_id, "Meditation")
    login()
    html = page(client, "?q=joggen")
    assert "Frühsport" in html
    assert "Buch lesen" not in html
    assert "Meditation" not in html
    html = page(client, "?q=BUCH")
    assert "Buch lesen" in html
    assert "Frühsport" not in html


def test_search_needs_all_words(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Buch lesen")
    login()
    assert "Buch lesen" in page(client, "?q=lesen+buch")
    assert "Buch lesen" not in page(client, "?q=buch+joggen")


def test_search_treats_wildcards_as_normal_characters(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Volle 100% Einsatz")
    make_habit(user_id, "Ganz normal")
    make_habit(user_id, "a_b Test")
    make_habit(user_id, "axb Test")
    login()
    html = page(client, "?q=%25")
    assert "Volle 100% Einsatz" in html
    assert "Ganz normal" not in html
    html = page(client, "?q=a_b")
    assert "a_b Test" in html
    assert "axb Test" not in html


def test_filter_by_category(client, make_user, make_habit, make_category, login):
    user_id = make_user()
    other_id = make_user("berta", "berta@example.com")
    fitness = make_category(user_id, "Fitness")
    foreign = make_category(other_id, "Fremd")
    make_habit(user_id, "Laufen", category_id=fitness)
    make_habit(user_id, "Lesen")
    make_habit(other_id, "Nachbars Habit", category_id=foreign)
    login()

    html = page(client, f"?category={fitness}")
    assert "Laufen" in html
    assert "Lesen" not in html

    html = page(client, "?category=none")
    assert "Lesen" in html
    assert "Laufen" not in html

    html = page(client, f"?category={foreign}")
    assert "Nachbars Habit" not in html
    assert "Laufen" not in html


def test_filter_by_tag(app, client, make_user, make_habit, make_tag, login):
    user_id = make_user()
    tag_id = make_tag(user_id, "morgens")
    tagged = make_habit(user_id, "Kaltdusche")
    make_habit(user_id, "Tagebuch")
    attach_tag(app, tagged, tag_id)
    login()
    html = page(client, f"?tag={tag_id}")
    assert "Kaltdusche" in html
    assert "Tagebuch" not in html


def test_filter_by_frequency(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Wochenlauf", frequency="weekly", target_per_period=2)
    make_habit(user_id, "Tageslauf")
    login()
    html = page(client, "?frequency=weekly")
    assert "Wochenlauf" in html
    assert "Tageslauf" not in html


def test_filter_by_status(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Aktives Habit")
    make_habit(user_id, "Altes Habit", is_archived=True)
    login()

    html = page(client)
    assert "Aktives Habit" in html
    assert "Altes Habit" not in html

    html = page(client, "?status=archived")
    assert "Altes Habit" in html
    assert "Aktives Habit" not in html

    html = page(client, "?status=all")
    assert "Altes Habit" in html
    assert "Aktives Habit" in html


def test_filter_done_and_open_today(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    start = today - timedelta(days=3)
    done_id = make_habit(user_id, "Wasser trinken", start_date=start)
    make_habit(user_id, "Tagebuch schreiben", start_date=start)
    make_habit(
        user_id, "Nur morgen", frequency="weekdays", weekdays=str((today.weekday() + 1) % 7), start_date=start
    )
    add_logs(app, done_id, [today])
    login()

    html = page(client, "?done=done")
    assert "Wasser trinken" in html
    assert "Tagebuch schreiben" not in html

    html = page(client, "?done=open")
    assert "Tagebuch schreiben" in html
    assert "Wasser trinken" not in html
    assert "Nur morgen" not in html


def test_sort_by_name_and_created(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Beta")
    make_habit(user_id, "Alpha")
    make_habit(user_id, "Gamma")
    login()

    html = page(client, "?sort=name_asc")
    assert html.index("Alpha") < html.index("Beta") < html.index("Gamma")
    html = page(client, "?sort=name_desc")
    assert html.index("Gamma") < html.index("Beta") < html.index("Alpha")
    html = page(client, "?sort=created_asc")
    assert html.index("Beta") < html.index("Alpha") < html.index("Gamma")
    html = page(client, "?sort=created_desc")
    assert html.index("Gamma") < html.index("Alpha") < html.index("Beta")


def test_sort_by_longest_streak(app, client, make_user, make_habit, login, today):
    user_id = make_user()
    start = today - timedelta(days=10)
    long_id = make_habit(user_id, "Langstrecke", start_date=start)
    short_id = make_habit(user_id, "Kurzstrecke", start_date=start)
    make_habit(user_id, "Neustart", start_date=start)
    add_logs(app, long_id, [today - timedelta(days=i) for i in (1, 2, 3)])
    add_logs(app, short_id, [today - timedelta(days=5)])
    login()

    html = page(client, "?sort=streak_desc")
    assert html.index("Langstrecke") < html.index("Kurzstrecke") < html.index("Neustart")
    html = page(client, "?sort=streak_asc")
    assert html.index("Neustart") < html.index("Kurzstrecke") < html.index("Langstrecke")


def test_pagination(client, make_user, make_habit, login):
    user_id = make_user()
    for number in range(1, 13):
        make_habit(user_id, f"Habit {number:02d}")
    login()

    html = page(client)
    assert "Habit 01" in html
    assert "Habit 10" in html
    assert "Habit 11" not in html
    assert "page=2" in html

    html = page(client, "?page=2")
    assert "Habit 11" in html
    assert "Habit 12" in html
    assert "Habit 01" not in html

    assert "Habit 11" in page(client, "?page=99")
    assert "Habit 01" in page(client, "?page=abc")


def test_pagination_links_keep_filters(client, make_user, make_habit, login):
    user_id = make_user()
    for number in range(1, 13):
        make_habit(user_id, f"Habit {number:02d}")
    login()
    assert "q=habit&amp;page=2" in page(client, "?q=habit")


def test_invalid_parameters_do_not_crash(client, make_user, login):
    make_user()
    login()
    page(client, "?category=abc&tag=xyz&sort=hack&status=x&done=y&frequency=z&page=-3")
    page(client, "?category=99999999999999999999")
    page(client, "?tag=99999999999999999999")
    page(client, "?category=%C2%B2")


def test_search_api_needs_login(client):
    assert client.get("/api/habits/suche").status_code == 401


def test_search_api_returns_rendered_results(client, make_user, make_habit, login):
    user_id = make_user()
    make_habit(user_id, "Laufen")
    make_habit(user_id, "Lesen")
    login()
    response = client.get("/api/habits/suche?q=lauf")
    data = response.get_json()
    assert response.status_code == 200
    assert data["total"] == 1
    assert "Laufen" in data["html"]
    assert "Lesen" not in data["html"]
