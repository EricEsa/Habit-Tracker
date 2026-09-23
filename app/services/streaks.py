from collections import Counter
from datetime import date, timedelta
from typing import Any

from app.models import FREQ_WEEKLY, Habit

RATE_WINDOWS = (7, 30, 90)


def week_start(day: date) -> date:
    """Montag der Woche, in der `day` liegt."""
    return day - timedelta(days=day.weekday())


def weekly_counts(completed: set[date]) -> Counter:
    """Anzahl der Erledigungen pro Woche (Schlüssel: Montag)."""
    return Counter(week_start(day) for day in completed)


def streak_unit(habit: Habit) -> str:
    return "Wochen" if habit.frequency == FREQ_WEEKLY else "Tage"


def week_progress(habit: Habit, completed: set[date], today: date) -> int:
    """Erledigungen in der laufenden Woche."""
    return weekly_counts(completed)[week_start(today)]


def current_streak(habit: Habit, completed: set[date], today: date) -> int:
    """Aktuelle Serie. Ein heute noch offener Tag unterbricht sie nicht."""
    if habit.frequency == FREQ_WEEKLY:
        return _weekly_current(habit, completed, today)

    streak = 0
    day = today
    if habit.is_due_on(today) and today not in completed:
        day -= timedelta(days=1)
    while day >= habit.start_date:
        if habit.is_due_on(day):
            if day not in completed:
                break
            streak += 1
        day -= timedelta(days=1)
    return streak


def longest_streak(habit: Habit, completed: set[date], today: date) -> int:
    """Längste Serie seit dem Startdatum."""
    if habit.frequency == FREQ_WEEKLY:
        return _weekly_longest(habit, completed, today)

    best = run = 0
    day = habit.start_date
    while day <= today:
        if habit.is_due_on(day):
            if day in completed:
                run += 1
                best = max(best, run)
            elif day != today:
                run = 0
        day += timedelta(days=1)
    return best


def success_rate(habit: Habit, completed: set[date], today: date, days: int) -> float | None:
    """Erfolgsquote (0 bis 1) der letzten `days` Tage, None wenn nichts fällig war."""
    window_start = max(today - timedelta(days=days - 1), habit.start_date)
    if window_start > today:
        return None

    span = (today - window_start).days + 1
    if habit.frequency == FREQ_WEEKLY:
        expected = habit.target_per_period * span / 7
        done = sum(1 for day in completed if window_start <= day <= today)
        return min(done / expected, 1.0)

    due = [window_start + timedelta(days=i) for i in range(span)]
    due = [day for day in due if habit.is_due_on(day)]
    if not due:
        return None
    return sum(1 for day in due if day in completed) / len(due)


def habit_stats(habit: Habit, completed: set[date], today: date) -> dict[str, Any]:
    return {
        "current": current_streak(habit, completed, today),
        "longest": longest_streak(habit, completed, today),
        "unit": streak_unit(habit),
        "rates": {days: success_rate(habit, completed, today, days) for days in RATE_WINDOWS},
        "total": len(completed),
    }


def _weekly_current(habit: Habit, completed: set[date], today: date) -> int:
    counts = weekly_counts(completed)
    target = habit.target_per_period
    first = week_start(habit.start_date)
    week = week_start(today)

    streak = 1 if counts[week] >= target else 0
    week -= timedelta(days=7)
    while week >= first and counts[week] >= target:
        streak += 1
        week -= timedelta(days=7)
    return streak


def _weekly_longest(habit: Habit, completed: set[date], today: date) -> int:
    counts = weekly_counts(completed)
    target = habit.target_per_period
    current = week_start(today)
    week = week_start(habit.start_date)

    best = run = 0
    while week <= current:
        if counts[week] >= target:
            run += 1
            best = max(best, run)
        elif week != current:
            run = 0
        week += timedelta(days=7)
    return best

MILESTONES = (7, 30, 100)


def milestones_reached(habit: Habit, completed: set[date], today: date) -> list[int]:
    """Meilensteine, die die längste Serie je erreicht hat."""
    best = longest_streak(habit, completed, today)
    return [m for m in MILESTONES if best >= m]
