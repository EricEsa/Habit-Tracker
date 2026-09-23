from sqlalchemy import func, select

from app.extensions import db
from app.models import User

REGISTER_DATA = {
    "username": "anna",
    "email": "anna@example.com",
    "password": "geheim123",
    "password2": "geheim123",
}


def count_users(app):
    with app.app_context():
        return db.session.scalar(select(func.count(User.id)))


def get_user(app, username="anna"):
    with app.app_context():
        return db.session.scalar(select(User).where(User.username == username))


def test_password_is_hashed(app):
    with app.app_context():
        user = User(username="x", email="x@example.com")
        user.set_password("geheim123")
        assert user.password_hash != "geheim123"
        assert user.check_password("geheim123")
        assert not user.check_password("falsch123")


def test_same_password_gives_different_hashes(app):
    with app.app_context():
        a = User(username="a", email="a@example.com")
        b = User(username="b", email="b@example.com")
        a.set_password("geheim123")
        b.set_password("geheim123")
        assert a.password_hash != b.password_hash


def test_register_success(app, client):
    response = client.post("/registrieren", data=REGISTER_DATA, follow_redirects=True)
    assert response.status_code == 200
    assert "Dein Konto wurde erstellt" in response.get_data(as_text=True)
    assert count_users(app) == 1
    assert get_user(app).password_hash != "geheim123"


def test_register_duplicate_username(app, client, make_user):
    make_user()
    response = client.post("/registrieren", data={**REGISTER_DATA, "email": "andere@example.com"})
    assert "bereits vergeben" in response.get_data(as_text=True)
    assert count_users(app) == 1


def test_register_duplicate_email(app, client, make_user):
    make_user()
    response = client.post("/registrieren", data={**REGISTER_DATA, "username": "berta"})
    assert "bereits registriert" in response.get_data(as_text=True)
    assert count_users(app) == 1


def test_register_password_too_short(app, client):
    data = {**REGISTER_DATA, "password": "abc1", "password2": "abc1"}
    response = client.post("/registrieren", data=data)
    assert "mindestens 8 Zeichen" in response.get_data(as_text=True)
    assert count_users(app) == 0


def test_register_passwords_do_not_match(app, client):
    response = client.post("/registrieren", data={**REGISTER_DATA, "password2": "anders123"})
    assert "stimmen nicht überein" in response.get_data(as_text=True)
    assert count_users(app) == 0


def test_login_with_username_and_email(client, make_user, login):
    make_user()
    assert login("anna", "geheim123").status_code == 302
    client.post("/logout")
    assert login("anna@example.com", "geheim123").status_code == 302


def test_login_wrong_password(make_user, login):
    make_user()
    response = login("anna", "falsch123")
    assert response.status_code == 200
    assert "Benutzername oder Passwort ist falsch" in response.get_data(as_text=True)


def test_protected_page_redirects_to_login(client):
    response = client.get("/heute")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert "next=" in response.headers["Location"]


def test_logout(client, make_user, login):
    make_user()
    login()
    assert client.get("/heute").status_code == 200
    client.post("/logout")
    assert client.get("/heute").status_code == 302


def test_login_ignores_external_next_url(client, make_user):
    make_user()
    data = {"identifier": "anna", "password": "geheim123"}
    response = client.post("/login?next=https://boese.example/", data=data)
    assert response.status_code == 302
    assert "boese.example" not in response.headers["Location"]


def test_login_follows_internal_next_url(client, make_user):
    make_user()
    data = {"identifier": "anna", "password": "geheim123"}
    response = client.post("/login?next=/profil", data=data)
    assert response.headers["Location"].endswith("/profil")


def test_theme_is_saved(app, client, make_user, login):
    make_user()
    login()
    client.post("/profil/theme", data={"theme": "dark"})
    assert get_user(app).theme == "dark"
    client.post("/profil/theme", data={"theme": "pink"})
    assert get_user(app).theme == "dark"


def test_change_email(app, client, make_user, login):
    make_user()
    login()
    client.post("/profil/email", data={"new_email": "neu@example.com", "email_password": "geheim123"})
    assert get_user(app).email == "neu@example.com"


def test_change_password(client, make_user, login):
    make_user()
    login()
    client.post("/profil/passwort", data={
        "current_password": "geheim123",
        "new_password": "neuesPasswort9",
        "confirm_password": "neuesPasswort9",
    })
    client.post("/logout")
    assert login("anna", "geheim123").status_code == 200
    assert login("anna", "neuesPasswort9").status_code == 302


def test_delete_account_needs_correct_password(app, client, make_user, login):
    make_user()
    login()
    client.post("/profil/loeschen", data={"delete_password": "falsch123"})
    assert count_users(app) == 1
    client.post("/profil/loeschen", data={"delete_password": "geheim123"})
    assert count_users(app) == 0


def test_post_without_csrf_token_is_rejected(app, client):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post("/registrieren", data=REGISTER_DATA)
    assert response.status_code == 302
    assert count_users(app) == 0
