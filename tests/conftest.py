import pytest
from sqlalchemy import func, select

from app import create_app
from app.extensions import db
from app.models import Category, Habit, Tag, User
from config import TestingConfig


@pytest.fixture()
def app():
    app = create_app(TestingConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def make(username="anna", email="anna@example.com", password="geheim123"):
        with app.app_context():
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user.id

    return make


@pytest.fixture()
def login(client):
    def do_login(identifier="anna", password="geheim123", **kwargs):
        return client.post("/login", data={"identifier": identifier, "password": password}, **kwargs)

    return do_login


@pytest.fixture()
def make_habit(app):
    def make(user_id, title="Sport", **kwargs):
        with app.app_context():
            habit = Habit(user_id=user_id, title=title, **kwargs)
            db.session.add(habit)
            db.session.commit()
            return habit.id

    return make


@pytest.fixture()
def make_category(app):
    def make(user_id, name="Sport"):
        with app.app_context():
            category = Category(user_id=user_id, name=name)
            db.session.add(category)
            db.session.commit()
            return category.id

    return make


@pytest.fixture()
def make_tag(app):
    def make(user_id, name="morgens"):
        with app.app_context():
            tag = Tag(user_id=user_id, name=name)
            db.session.add(tag)
            db.session.commit()
            return tag.id

    return make


@pytest.fixture()
def count_rows(app):
    def count(model):
        with app.app_context():
            return db.session.scalar(select(func.count(model.id)))

    return count
