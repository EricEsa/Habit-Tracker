from datetime import timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.extensions import db
from app.forms import CategoryForm, HabitForm, LogForm, TagForm
from app.models import FREQ_DAILY, FREQ_WEEKDAYS, FREQ_WEEKLY, Category, Habit, HabitLog, Tag
from app.services.search import DONE_OPTIONS, SORT_OPTIONS, STATUS_OPTIONS, run_search
from app.services.streaks import habit_stats
from app.services.tracking import completed_dates_by_habit, set_completion
from app.utils import owned_or_404, today_local

bp = Blueprint("habits", __name__)


def user_categories():
    return db.session.scalars(
        select(Category).where(Category.user_id == current_user.id).order_by(func.lower(Category.name))
    ).all()


def user_tags():
    return db.session.scalars(
        select(Tag).where(Tag.user_id == current_user.id).order_by(func.lower(Tag.name))
    ).all()


def habit_form_data(habit):
    return {
        "title": habit.title,
        "description": habit.description,
        "category_id": habit.category_id or 0,
        "frequency": habit.frequency,
        "weekdays": habit.weekday_list,
        "target_per_period": habit.target_per_period,
        "start_date": habit.start_date,
        "tags": [tag.id for tag in habit.tags],
    }


def fill_habit(habit, form):
    habit.title = form.title.data
    habit.description = form.description.data or None
    habit.category_id = form.category_id.data or None
    habit.frequency = form.frequency.data
    habit.weekday_list = form.weekdays.data if habit.frequency == FREQ_WEEKDAYS else []
    habit.target_per_period = form.target_per_period.data if habit.frequency == FREQ_WEEKLY else 1
    habit.start_date = form.start_date.data
    tag_ids = form.tags.data
    if tag_ids:
        habit.tags = db.session.scalars(
            select(Tag).where(Tag.user_id == current_user.id, Tag.id.in_(tag_ids))
        ).all()
    else:
        habit.tags = []


def render_detail(habit, log_form):
    today = today_local()
    completed = completed_dates_by_habit([habit.id])[habit.id]

    days = [today - timedelta(days=i) for i in range(14)]
    days = [day for day in days if habit.is_due_on(day)]

    recent_logs = db.session.scalars(
        select(HabitLog).where(HabitLog.habit_id == habit.id, HabitLog.date >= today - timedelta(days=13))
    ).all()
    notes = db.session.scalars(
        select(HabitLog)
        .where(HabitLog.habit_id == habit.id, HabitLog.note.is_not(None))
        .order_by(HabitLog.date.desc())
        .limit(10)
    ).all()

    return render_template(
        "habits/detail.html",
        habit=habit,
        stats=habit_stats(habit, completed, today),
        today=today,
        days=days,
        logs={log.date: log for log in recent_logs},
        notes=notes,
        log_form=log_form,
    )


@bp.route("/habits")
@login_required
def index():
    filters, page, cards = run_search(
        current_user.id, request.args, today_local(), current_app.config["ITEMS_PER_PAGE"]
    )
    return render_template(
        "habits/list.html",
        filters=filters,
        page=page,
        cards=cards,
        categories=user_categories(),
        tags=user_tags(),
        sort_options=SORT_OPTIONS,
        status_options=STATUS_OPTIONS,
        done_options=DONE_OPTIONS,
    )


@bp.route("/habits/neu", methods=["GET", "POST"])
@login_required
def create():
    form = HabitForm(data={"frequency": FREQ_DAILY, "target_per_period": 1, "start_date": today_local()})
    if form.validate_on_submit():
        habit = Habit(user_id=current_user.id)
        fill_habit(habit, form)
        db.session.add(habit)
        db.session.commit()
        flash("Gewohnheit wurde angelegt.", "success")
        return redirect(url_for("habits.index"))
    return render_template("habits/form.html", form=form, habit=None)


@bp.route("/habits/<int:habit_id>")
@login_required
def detail(habit_id):
    habit = owned_or_404(Habit, habit_id)
    return render_detail(habit, LogForm(habit=habit, data={"date": today_local(), "completed": True}))


@bp.post("/habits/<int:habit_id>/eintrag")
@login_required
def add_log(habit_id):
    habit = owned_or_404(Habit, habit_id)
    form = LogForm(habit=habit)
    if form.validate_on_submit():
        set_completion(habit, form.date.data, form.completed.data, form.note.data or None)
        flash("Eintrag wurde gespeichert.", "success")
        return redirect(url_for("habits.detail", habit_id=habit.id))
    return render_detail(habit, form)


@bp.route("/habits/<int:habit_id>/bearbeiten", methods=["GET", "POST"])
@login_required
def edit(habit_id):
    habit = owned_or_404(Habit, habit_id)
    form = HabitForm(data=habit_form_data(habit))
    if form.validate_on_submit():
        fill_habit(habit, form)
        db.session.commit()
        flash("Änderungen wurden gespeichert.", "success")
        return redirect(url_for("habits.index", status="archived" if habit.is_archived else "active"))
    return render_template("habits/form.html", form=form, habit=habit)


@bp.post("/habits/<int:habit_id>/loeschen")
@login_required
def delete(habit_id):
    habit = owned_or_404(Habit, habit_id)
    archived = habit.is_archived
    db.session.delete(habit)
    db.session.commit()
    flash("Gewohnheit wurde gelöscht.", "info")
    return redirect(url_for("habits.index", status="archived" if archived else "active"))


@bp.post("/habits/<int:habit_id>/archivieren")
@login_required
def toggle_archive(habit_id):
    habit = owned_or_404(Habit, habit_id)
    habit.is_archived = not habit.is_archived
    db.session.commit()
    if habit.is_archived:
        flash("Gewohnheit wurde archiviert.", "info")
        return redirect(url_for("habits.index"))
    flash("Gewohnheit wurde wiederhergestellt.", "success")
    return redirect(url_for("habits.index", status="archived"))


@bp.route("/kategorien", methods=["GET", "POST"])
@login_required
def categories():
    form = CategoryForm(data={"color": "#4f46e5", "icon": "bi-tag"})
    if form.validate_on_submit():
        category = Category(
            user_id=current_user.id,
            name=form.name.data,
            color=form.color.data,
            icon=form.icon.data,
        )
        db.session.add(category)
        db.session.commit()
        flash("Kategorie wurde angelegt.", "success")
        return redirect(url_for("habits.categories"))
    return render_template("habits/categories.html", form=form, categories=user_categories(), editing=None)


@bp.route("/kategorien/<int:category_id>/bearbeiten", methods=["GET", "POST"])
@login_required
def edit_category(category_id):
    category = owned_or_404(Category, category_id)
    form = CategoryForm(
        editing_id=category.id,
        data={"name": category.name, "color": category.color, "icon": category.icon},
    )
    if form.validate_on_submit():
        category.name = form.name.data
        category.color = form.color.data
        category.icon = form.icon.data
        db.session.commit()
        flash("Kategorie wurde gespeichert.", "success")
        return redirect(url_for("habits.categories"))
    return render_template("habits/categories.html", form=form, categories=user_categories(), editing=category)


@bp.post("/kategorien/<int:category_id>/loeschen")
@login_required
def delete_category(category_id):
    category = owned_or_404(Category, category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Kategorie wurde gelöscht. Die Gewohnheiten darin bleiben erhalten.", "info")
    return redirect(url_for("habits.categories"))


@bp.route("/tags", methods=["GET", "POST"])
@login_required
def tags():
    form = TagForm()
    if form.validate_on_submit():
        db.session.add(Tag(user_id=current_user.id, name=form.name.data))
        db.session.commit()
        flash("Tag wurde angelegt.", "success")
        return redirect(url_for("habits.tags"))
    return render_template("habits/tags.html", form=form, tags=user_tags(), editing=None)


@bp.route("/tags/<int:tag_id>/bearbeiten", methods=["GET", "POST"])
@login_required
def edit_tag(tag_id):
    tag = owned_or_404(Tag, tag_id)
    form = TagForm(editing_id=tag.id, data={"name": tag.name})
    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.commit()
        flash("Tag wurde gespeichert.", "success")
        return redirect(url_for("habits.tags"))
    return render_template("habits/tags.html", form=form, tags=user_tags(), editing=tag)


@bp.post("/tags/<int:tag_id>/loeschen")
@login_required
def delete_tag(tag_id):
    tag = owned_or_404(Tag, tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash("Tag wurde gelöscht.", "info")
    return redirect(url_for("habits.tags"))
