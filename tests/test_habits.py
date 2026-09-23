from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.models import Category, Habit, HabitLog, Tag


def habit_data(**overrides):
    data = {
        "title": "Laufen",
        "description": "",
        "category_id": "0",
        "frequency": "daily",
        "target_per_period": "1",
        "start_date": date.today().isoformat(),
    }
    data.update(overrides)
    return data


def first_habit_id(app):
    with app.app_context():
        return db.session.scalar(select(Habit.id))


def load_habit(app, habit_id):
    with app.app_context():
        habit = db.session.get(Habit, habit_id)
        if habit is None:
            return None
        return {
            "title": habit.title,
            "user_id": habit.user_id,
            "category_id": habit.category_id,
            "is_archived": habit.is_archived,
            "frequency": habit.frequency,
            "weekdays": habit.weekday_list,
            "tags": sorted(tag.name for tag in habit.tags),
        }


def test_habit_pages_require_login(client):
    for url in ("/habits", "/habits/neu", "/kategorien", "/tags"):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_create_habit(app, client, make_user, count_rows, login):
    user_id = make_user()
    login()
    response = client.post("/habits/neu", data=habit_data(), follow_redirects=True)
    assert "Gewohnheit wurde angelegt" in response.get_data(as_text=True)
    assert count_rows(Habit) == 1
    habit = load_habit(app, first_habit_id(app))
    assert habit["user_id"] == user_id
    assert habit["frequency"] == "daily"


def test_create_habit_with_category_and_tags(app, client, make_user, make_category, make_tag, login):
    user_id = make_user()
    category_id = make_category(user_id, "Sport")
    tag_a = make_tag(user_id, "morgens")
    tag_b = make_tag(user_id, "draussen")
    login()
    client.post("/habits/neu", data=habit_data(category_id=str(category_id), tags=[str(tag_a), str(tag_b)]))
    habit = load_habit(app, first_habit_id(app))
    assert habit["category_id"] == category_id
    assert habit["tags"] == ["draussen", "morgens"]


def test_habit_needs_a_title(client, make_user, count_rows, login):
    make_user()
    login()
    response = client.post("/habits/neu", data=habit_data(title="  "))
    assert "Bitte gib einen Titel ein" in response.get_data(as_text=True)
    assert count_rows(Habit) == 0


def test_weekdays_frequency_needs_a_day(client, make_user, count_rows, login):
    make_user()
    login()
    response = client.post("/habits/neu", data=habit_data(frequency="weekdays"))
    assert "mindestens einen Wochentag" in response.get_data(as_text=True)
    assert count_rows(Habit) == 0


def test_weekdays_are_saved(app, client, make_user, login):
    make_user()
    login()
    client.post("/habits/neu", data=habit_data(frequency="weekdays", weekdays=["4", "0", "2"]))
    habit = load_habit(app, first_habit_id(app))
    assert habit["frequency"] == "weekdays"
    assert habit["weekdays"] == [0, 2, 4]


def test_edit_habit(app, client, make_user, make_habit, login):
    user_id = make_user()
    habit_id = make_habit(user_id, "Sport")
    login()
    page = client.get(f"/habits/{habit_id}/bearbeiten")
    assert 'value="Sport"' in page.get_data(as_text=True)
    client.post(f"/habits/{habit_id}/bearbeiten", data=habit_data(title="Yoga"))
    assert load_habit(app, habit_id)["title"] == "Yoga"


def test_delete_habit_removes_its_logs(app, client, make_user, make_habit, count_rows, login):
    user_id = make_user()
    habit_id = make_habit(user_id)
    with app.app_context():
        db.session.add(HabitLog(habit_id=habit_id, date=date.today(), completed=True))
        db.session.commit()
    login()
    client.post(f"/habits/{habit_id}/loeschen")
    assert load_habit(app, habit_id) is None
    assert count_rows(HabitLog) == 0


def test_archive_and_restore(app, client, make_user, make_habit, login):
    user_id = make_user()
    habit_id = make_habit(user_id, "Sport")
    login()
    client.post(f"/habits/{habit_id}/archivieren")
    assert load_habit(app, habit_id)["is_archived"] is True
    assert "Sport" not in client.get("/habits").get_data(as_text=True)
    assert "Sport" in client.get("/habits?status=archived").get_data(as_text=True)
    client.post(f"/habits/{habit_id}/archivieren")
    assert load_habit(app, habit_id)["is_archived"] is False


def test_cannot_touch_foreign_habit(app, client, make_user, make_habit, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    habit_id = make_habit(other_id, "Geheim")
    login()
    assert client.get(f"/habits/{habit_id}/bearbeiten").status_code == 404
    assert client.post(f"/habits/{habit_id}/bearbeiten", data=habit_data(title="Gehackt")).status_code == 404
    assert client.post(f"/habits/{habit_id}/archivieren").status_code == 404
    assert client.post(f"/habits/{habit_id}/loeschen").status_code == 404
    habit = load_habit(app, habit_id)
    assert habit["title"] == "Geheim"
    assert habit["is_archived"] is False


def test_list_shows_only_own_habits(client, make_user, make_habit, login):
    user_id = make_user()
    other_id = make_user("berta", "berta@example.com")
    make_habit(user_id, "Meine Gewohnheit")
    make_habit(other_id, "Fremde Gewohnheit")
    login()
    html = client.get("/habits").get_data(as_text=True)
    assert "Meine Gewohnheit" in html
    assert "Fremde Gewohnheit" not in html


def test_cannot_use_foreign_category_or_tag(client, make_user, make_category, make_tag, count_rows, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    foreign_category = make_category(other_id, "Fremd")
    foreign_tag = make_tag(other_id, "fremd")
    login()
    client.post("/habits/neu", data=habit_data(category_id=str(foreign_category)))
    client.post("/habits/neu", data=habit_data(tags=[str(foreign_tag)]))
    assert count_rows(Habit) == 0


def test_deleting_account_removes_all_data(client, make_user, make_habit, make_category, make_tag, count_rows, login):
    user_id = make_user()
    make_habit(user_id)
    make_category(user_id)
    make_tag(user_id)
    login()
    client.post("/profil/loeschen", data={"delete_password": "geheim123"})
    assert count_rows(Habit) == 0
    assert count_rows(Category) == 0
    assert count_rows(Tag) == 0


def test_is_due_on():
    habit = Habit(frequency="weekdays", start_date=date(2026, 1, 1))
    habit.weekday_list = [0]
    assert habit.is_due_on(date(2026, 9, 21))
    assert not habit.is_due_on(date(2026, 9, 22))
    assert not habit.is_due_on(date(2025, 12, 29))
