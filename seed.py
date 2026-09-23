import random
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Category, Habit, HabitLog, Tag, User

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"


def seed():
    app = create_app()
    with app.app_context():
        if db.session.query(User).filter_by(username=DEMO_USERNAME).first():
            print("Demo-Nutzer existiert bereits.")
            return

        user = User(username=DEMO_USERNAME, email=DEMO_EMAIL)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()

        sport = Category(user_id=user.id, name="Sport", color="#f59e0b", icon="bi-bicycle")
        gesundheit = Category(user_id=user.id, name="Gesundheit", color="#10b981", icon="bi-heart-pulse")
        lernen = Category(user_id=user.id, name="Lernen", color="#0ea5e9", icon="bi-book")
        db.session.add_all([sport, gesundheit, lernen])
        db.session.flush()

        morgens = Tag(user_id=user.id, name="morgens")
        abends = Tag(user_id=user.id, name="abends")
        db.session.add_all([morgens, abends])
        db.session.flush()

        start = date.today() - timedelta(days=40)

        laufen = Habit(
            user_id=user.id, category_id=sport.id, title="Laufen",
            description="30 Minuten joggen gehen.", frequency="daily",
            target_per_period=1, start_date=start,
        )
        laufen.tags.append(morgens)

        wasser = Habit(
            user_id=user.id, category_id=gesundheit.id, title="2 Liter Wasser trinken",
            description="Über den Tag verteilt genug trinken.", frequency="daily",
            target_per_period=1, start_date=start,
        )

        lesen = Habit(
            user_id=user.id, category_id=lernen.id, title="Lesen",
            description="Mindestens 20 Seiten lesen.", frequency="weekly",
            target_per_period=3, start_date=start,
        )
        lesen.tags.append(abends)

        db.session.add_all([laufen, wasser, lesen])
        db.session.flush()

        random.seed(42)
        today = date.today()
        day = start
        while day <= today:
            if laufen.is_due_on(day) and random.random() < 0.75:
                db.session.add(HabitLog(habit_id=laufen.id, date=day, completed=True))
            if wasser.is_due_on(day) and random.random() < 0.6:
                note = "Geschafft!" if random.random() < 0.1 else None
                db.session.add(HabitLog(habit_id=wasser.id, date=day, completed=True, note=note))
            if lesen.is_due_on(day) and day.weekday() in (0, 2, 4) and random.random() < 0.7:
                db.session.add(HabitLog(habit_id=lesen.id, date=day, completed=True))
            day += timedelta(days=1)

        db.session.commit()
        print(f"Demo-Nutzer angelegt: {DEMO_USERNAME} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
