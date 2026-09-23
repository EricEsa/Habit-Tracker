from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models import Habit, HabitLog

KEEP = object()


def habits_due_on(user_id: int, day: date) -> list[Habit]:
    """Aktive Habits des Nutzers, die an `day` fällig sind."""
    habits = db.session.scalars(
        select(Habit)
        .where(Habit.user_id == user_id, Habit.is_archived.is_(False))
        .order_by(func.lower(Habit.title))
    ).all()
    return [habit for habit in habits if habit.is_due_on(day)]


def completed_dates_by_habit(habit_ids: list[int]) -> dict[int, set[date]]:
    """Erledigte Tage je Habit (eine Abfrage für alle IDs)."""
    result: dict[int, set[date]] = {habit_id: set() for habit_id in habit_ids}
    if not habit_ids:
        return result
    rows = db.session.execute(
        select(HabitLog.habit_id, HabitLog.date).where(
            HabitLog.habit_id.in_(habit_ids), HabitLog.completed.is_(True)
        )
    )
    for habit_id, day in rows:
        result[habit_id].add(day)
    return result


def set_completion(habit: Habit, day: date, completed: bool | None = None, note=KEEP) -> HabitLog:
    """Legt den Eintrag für `day` an oder ändert ihn.

    completed=None schaltet um, note=KEEP lässt die Notiz unverändert.
    """
    log = db.session.scalar(
        select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.date == day)
    )
    if log is None:
        log = HabitLog(habit_id=habit.id, date=day, completed=True if completed is None else completed)
        db.session.add(log)
    elif completed is None:
        log.completed = not log.completed
    else:
        log.completed = completed

    if note is not KEEP:
        log.note = note or None

    db.session.commit()
    return log
