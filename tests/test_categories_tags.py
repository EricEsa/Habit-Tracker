from app.extensions import db
from app.models import Category, Habit, Tag

CATEGORY_DATA = {"name": "Sport", "color": "#ff0000", "icon": "bi-bicycle"}


def test_create_category(client, make_user, count_rows, login):
    make_user()
    login()
    response = client.post("/kategorien", data=CATEGORY_DATA, follow_redirects=True)
    assert "Kategorie wurde angelegt" in response.get_data(as_text=True)
    assert count_rows(Category) == 1


def test_duplicate_category_name_is_rejected(client, make_user, make_category, count_rows, login):
    user_id = make_user()
    make_category(user_id, "Sport")
    login()
    response = client.post("/kategorien", data={**CATEGORY_DATA, "name": "sport"})
    assert "gibt es schon" in response.get_data(as_text=True)
    assert count_rows(Category) == 1


def test_same_category_name_for_another_user_is_allowed(client, make_user, make_category, count_rows, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    make_category(other_id, "Sport")
    login()
    client.post("/kategorien", data=CATEGORY_DATA)
    assert count_rows(Category) == 2


def test_invalid_category_color_is_rejected(client, make_user, count_rows, login):
    make_user()
    login()
    client.post("/kategorien", data={**CATEGORY_DATA, "color": "rot"})
    assert count_rows(Category) == 0


def test_edit_category(app, client, make_user, make_category, login):
    user_id = make_user()
    category_id = make_category(user_id, "Sport")
    login()
    client.post(
        f"/kategorien/{category_id}/bearbeiten",
        data={"name": "Fitness", "color": "#00ff00", "icon": "bi-heart-pulse"},
    )
    with app.app_context():
        category = db.session.get(Category, category_id)
        assert (category.name, category.color, category.icon) == ("Fitness", "#00ff00", "bi-heart-pulse")


def test_edit_category_may_keep_its_own_name(app, client, make_user, make_category, login):
    user_id = make_user()
    category_id = make_category(user_id, "Sport")
    login()
    client.post(f"/kategorien/{category_id}/bearbeiten", data={**CATEGORY_DATA, "color": "#0000ff"})
    with app.app_context():
        assert db.session.get(Category, category_id).color == "#0000ff"


def test_delete_category_keeps_habits(app, client, make_user, make_category, make_habit, count_rows, login):
    user_id = make_user()
    category_id = make_category(user_id, "Sport")
    habit_id = make_habit(user_id, category_id=category_id)
    login()
    client.post(f"/kategorien/{category_id}/loeschen")
    assert count_rows(Category) == 0
    with app.app_context():
        assert db.session.get(Habit, habit_id).category_id is None


def test_cannot_touch_foreign_category(app, client, make_user, make_category, count_rows, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    category_id = make_category(other_id, "Fremd")
    login()
    assert client.get(f"/kategorien/{category_id}/bearbeiten").status_code == 404
    assert client.post(f"/kategorien/{category_id}/bearbeiten", data=CATEGORY_DATA).status_code == 404
    assert client.post(f"/kategorien/{category_id}/loeschen").status_code == 404
    assert count_rows(Category) == 1
    with app.app_context():
        assert db.session.get(Category, category_id).name == "Fremd"


def test_create_tag(client, make_user, count_rows, login):
    make_user()
    login()
    response = client.post("/tags", data={"name": "morgens"}, follow_redirects=True)
    assert "Tag wurde angelegt" in response.get_data(as_text=True)
    assert count_rows(Tag) == 1


def test_duplicate_tag_is_rejected(client, make_user, make_tag, count_rows, login):
    user_id = make_user()
    make_tag(user_id, "morgens")
    login()
    response = client.post("/tags", data={"name": "MORGENS"})
    assert "gibt es schon" in response.get_data(as_text=True)
    assert count_rows(Tag) == 1


def test_edit_tag(app, client, make_user, make_tag, login):
    user_id = make_user()
    tag_id = make_tag(user_id, "morgens")
    login()
    client.post(f"/tags/{tag_id}/bearbeiten", data={"name": "abends"})
    with app.app_context():
        assert db.session.get(Tag, tag_id).name == "abends"


def test_delete_tag_keeps_habit(app, client, make_user, make_tag, make_habit, count_rows, login):
    user_id = make_user()
    tag_id = make_tag(user_id, "morgens")
    habit_id = make_habit(user_id)
    with app.app_context():
        habit = db.session.get(Habit, habit_id)
        habit.tags.append(db.session.get(Tag, tag_id))
        db.session.commit()
    login()
    client.post(f"/tags/{tag_id}/loeschen")
    assert count_rows(Tag) == 0
    with app.app_context():
        assert db.session.get(Habit, habit_id).tags == []


def test_cannot_touch_foreign_tag(app, client, make_user, make_tag, count_rows, login):
    make_user()
    other_id = make_user("berta", "berta@example.com")
    tag_id = make_tag(other_id, "fremd")
    login()
    assert client.get(f"/tags/{tag_id}/bearbeiten").status_code == 404
    assert client.post(f"/tags/{tag_id}/bearbeiten", data={"name": "gehackt"}).status_code == 404
    assert client.post(f"/tags/{tag_id}/loeschen").status_code == 404
    assert count_rows(Tag) == 1
    with app.app_context():
        assert db.session.get(Tag, tag_id).name == "fremd"
