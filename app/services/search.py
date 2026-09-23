import math
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from sqlalchemy import and_, func, or_, select

from app.extensions import db
from app.models import FREQ_WEEKDAYS, FREQUENCY_LABELS, Habit, HabitLog, Tag
from app.services.streaks import current_streak, longest_streak, streak_unit
from app.services.tracking import completed_dates_by_habit

SORT_OPTIONS = {
    "name_asc": "Name (A–Z)",
    "name_desc": "Name (Z–A)",
    "created_desc": "Neueste zuerst",
    "created_asc": "Älteste zuerst",
    "streak_desc": "Längste Serie (höchste zuerst)",
    "streak_asc": "Längste Serie (niedrigste zuerst)",
}
STATUS_OPTIONS = {"active": "Aktiv", "archived": "Archiviert", "all": "Alle"}
DONE_OPTIONS = {"done": "Heute erledigt", "open": "Heute offen"}
DEFAULT_SORT = "name_asc"
MAX_ID = 2**31


@dataclass
class HabitFilters:
    q: str = ""
    category: str = ""
    tag: int | None = None
    frequency: str = ""
    status: str = "active"
    done: str = ""
    sort: str = DEFAULT_SORT
    page: int = 1

    @classmethod
    def from_args(cls, args) -> "HabitFilters":
        """Liest Filter aus den URL-Parametern. Ungültige Werte werden ignoriert."""
        category = args.get("category", "")
        if category != "none" and not (category.isascii() and category.isdigit() and len(category) < 10):
            category = ""

        tag = args.get("tag", type=int)
        if tag is not None and not 0 < tag < MAX_ID:
            tag = None

        frequency = args.get("frequency", "")
        status = args.get("status", "active")
        done = args.get("done", "")
        sort = args.get("sort", DEFAULT_SORT)

        return cls(
            q=args.get("q", "").strip()[:100],
            category=category,
            tag=tag,
            frequency=frequency if frequency in FREQUENCY_LABELS else "",
            status=status if status in STATUS_OPTIONS else "active",
            done=done if done in DONE_OPTIONS else "",
            sort=sort if sort in SORT_OPTIONS else DEFAULT_SORT,
            page=max(args.get("page", 1, type=int), 1),
        )

    def query(self, **overrides) -> dict[str, Any]:
        """URL-Parameter für diese Filter (Standardwerte werden weggelassen)."""
        values = {**asdict(self), **overrides}
        params: dict[str, Any] = {}
        for key in ("q", "category", "tag", "frequency", "done"):
            if values[key]:
                params[key] = values[key]
        if values["status"] != "active":
            params["status"] = values["status"]
        if values["sort"] != DEFAULT_SORT:
            params["sort"] = values["sort"]
        if values["page"] > 1:
            params["page"] = values["page"]
        return params


@dataclass
class Page:
    items: list[Habit]
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page))

    @property
    def numbers(self) -> range:
        return range(max(1, self.page - 2), min(self.pages, self.page + 2) + 1)


def escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def due_today(today: date):
    """SQL-Bedingung: Habit ist heute fällig (entspricht Habit.is_due_on)."""
    return and_(
        Habit.start_date <= today,
        or_(Habit.frequency != FREQ_WEEKDAYS, Habit.weekdays.like(f"%{today.weekday()}%")),
    )


def build_conditions(user_id: int, filters: HabitFilters, today: date) -> list:
    conditions = [Habit.user_id == user_id]

    if filters.status != "all":
        conditions.append(Habit.is_archived.is_(filters.status == "archived"))

    for word in filters.q.split():
        pattern = f"%{escape_like(word)}%"
        conditions.append(or_(
            Habit.title.ilike(pattern, escape="\\"),
            Habit.description.ilike(pattern, escape="\\"),
        ))

    if filters.category == "none":
        conditions.append(Habit.category_id.is_(None))
    elif filters.category:
        conditions.append(Habit.category_id == int(filters.category))

    if filters.tag:
        conditions.append(Habit.tags.any(Tag.id == filters.tag))

    if filters.frequency:
        conditions.append(Habit.frequency == filters.frequency)

    if filters.done:
        done_today = Habit.logs.any(and_(HabitLog.date == today, HabitLog.completed.is_(True)))
        if filters.done == "done":
            conditions.append(done_today)
        else:
            conditions.append(and_(due_today(today), ~done_today))

    return conditions


def search_habits(user_id: int, filters: HabitFilters, today: date, per_page: int) -> Page:
    conditions = build_conditions(user_id, filters, today)
    total = db.session.scalar(select(func.count(Habit.id)).where(*conditions))
    pages = max(1, math.ceil(total / per_page))
    number = min(filters.page, pages)
    offset = (number - 1) * per_page
    field, order = filters.sort.rsplit("_", 1)

    if field == "streak":
        # Die Serie wird in Python berechnet, deshalb wird hier nicht in SQL sortiert.
        habits = list(db.session.scalars(select(Habit).where(*conditions)))
        completed = completed_dates_by_habit([habit.id for habit in habits])
        longest = {habit.id: longest_streak(habit, completed[habit.id], today) for habit in habits}
        habits.sort(key=lambda habit: (longest[habit.id], habit.title.lower()), reverse=order == "desc")
        items = habits[offset:offset + per_page]
    else:
        column = func.lower(Habit.title) if field == "name" else Habit.created_at
        direction = column.asc() if order == "asc" else column.desc()
        items = list(db.session.scalars(
            select(Habit).where(*conditions).order_by(direction, Habit.id).limit(per_page).offset(offset)
        ))

    return Page(items, number, per_page, total)


def habit_cards(habits: list[Habit], today: date) -> list[dict[str, Any]]:
    """Habits samt Serien-Daten für die Kartenansicht."""
    completed = completed_dates_by_habit([habit.id for habit in habits])
    return [
        {
            "habit": habit,
            "done": today in completed[habit.id],
            "current": current_streak(habit, completed[habit.id], today),
            "longest": longest_streak(habit, completed[habit.id], today),
            "unit": streak_unit(habit),
        }
        for habit in habits
    ]


def run_search(user_id: int, args, today: date, per_page: int) -> tuple[HabitFilters, Page, list[dict[str, Any]]]:
    filters = HabitFilters.from_args(args)
    page = search_habits(user_id, filters, today, per_page)
    return filters, page, habit_cards(page.items, today)
