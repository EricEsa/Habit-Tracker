from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager

FREQ_DAILY = "daily"
FREQ_WEEKLY = "weekly"
FREQ_WEEKDAYS = "weekdays"
FREQUENCY_LABELS = {
    FREQ_DAILY: "Täglich",
    FREQ_WEEKLY: "Wöchentlich",
    FREQ_WEEKDAYS: "Bestimmte Wochentage",
}
WEEKDAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


habit_tags = db.Table(
    "habit_tags",
    db.Column("habit_id", db.Integer, db.ForeignKey("habits.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (db.CheckConstraint("theme IN ('light', 'dark')", name="ck_users_theme"),)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    theme = db.Column(db.String(10), nullable=False, default="light")

    categories = db.relationship("Category", back_populates="user", cascade="all, delete-orphan")
    habits = db.relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    tags = db.relationship("Tag", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#6c757d")
    icon = db.Column(db.String(50), nullable=False, default="bi-tag")

    user = db.relationship("User", back_populates="categories")
    habits = db.relationship("Habit", back_populates="category")


class Habit(db.Model):
    __tablename__ = "habits"
    __table_args__ = (
        db.CheckConstraint("frequency IN ('daily', 'weekly', 'weekdays')", name="ck_habits_frequency"),
        db.CheckConstraint("target_per_period >= 1", name="ck_habits_target"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.String(10), nullable=False, default=FREQ_DAILY)
    weekdays = db.Column(db.String(13), nullable=False, default="")  # z. B. "0,2,4" (0 = Montag)
    target_per_period = db.Column(db.Integer, nullable=False, default=1)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    is_archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="habits")
    category = db.relationship("Category", back_populates="habits")
    logs = db.relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="habit", cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary=habit_tags, back_populates="habits")

    @property
    def weekday_list(self):
        parts = (self.weekdays or "").split(",")
        return sorted(int(p) for p in parts if p.strip().isdigit())

    @weekday_list.setter
    def weekday_list(self, values):
        self.weekdays = ",".join(str(int(v)) for v in sorted(set(values)))

    def is_due_on(self, day):
        start = self.start_date or date.today()
        if day < start:
            return False
        if self.frequency == FREQ_WEEKDAYS:
            return day.weekday() in self.weekday_list
        return True


class HabitLog(db.Model):
    __tablename__ = "habit_logs"
    __table_args__ = (db.UniqueConstraint("habit_id", "date", name="uq_habit_logs_habit_date"),)

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=True)
    note = db.Column(db.String(500), nullable=True)

    habit = db.relationship("Habit", back_populates="logs")


class Tag(db.Model):
    __tablename__ = "tags"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(30), nullable=False)

    user = db.relationship("User", back_populates="tags")
    habits = db.relationship("Habit", secondary=habit_tags, back_populates="tags")


class Goal(db.Model):
    __tablename__ = "goals"
    __table_args__ = (db.CheckConstraint("target_streak >= 1", name="ck_goals_target"),)

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    target_streak = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    achieved = db.Column(db.Boolean, nullable=False, default=False)

    habit = db.relationship("Habit", back_populates="goals")
