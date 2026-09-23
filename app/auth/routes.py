from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.forms import (
    ChangeEmailForm,
    ChangePasswordForm,
    DeleteAccountForm,
    LoginForm,
    RegistrationForm,
    ThemeForm,
)
from app.models import User

bp = Blueprint("auth", __name__)


def is_safe_url(target):
    if not target:
        return False
    host = urlparse(request.host_url)
    url = urlparse(urljoin(request.host_url, target))
    return url.scheme in ("http", "https") and host.netloc == url.netloc


@bp.route("/registrieren", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Benutzername oder E-Mail-Adresse ist bereits vergeben.", "danger")
            return render_template("auth/register.html", form=form)
        flash("Dein Konto wurde erstellt. Bitte melde dich jetzt an.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        ident = form.identifier.data.lower()
        user = db.session.scalar(
            select(User).where(or_(func.lower(User.username) == ident, func.lower(User.email) == ident))
        )
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Willkommen zurück, {user.username}!", "success")
            next_url = request.args.get("next")
            if not is_safe_url(next_url):
                next_url = url_for("main.dashboard")
            return redirect(next_url)
        flash("Benutzername oder Passwort ist falsch.", "danger")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Du wurdest abgemeldet.", "info")
    return redirect(url_for("main.index"))


def render_profile(**forms):
    forms.setdefault("email_form", ChangeEmailForm(formdata=None))
    forms.setdefault("password_form", ChangePasswordForm(formdata=None))
    forms.setdefault("theme_form", ThemeForm(formdata=None, data={"theme": current_user.theme}))
    forms.setdefault("delete_form", DeleteAccountForm(formdata=None))
    return render_template("auth/profile.html", **forms)


@bp.route("/profil")
@login_required
def profile():
    return render_profile()


@bp.post("/profil/email")
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        current_user.email = form.new_email.data
        db.session.commit()
        flash("Deine E-Mail-Adresse wurde geändert.", "success")
        return redirect(url_for("auth.profile"))
    return render_profile(email_form=form)


@bp.post("/profil/passwort")
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Dein Passwort wurde geändert.", "success")
        return redirect(url_for("auth.profile"))
    return render_profile(password_form=form)


@bp.post("/profil/theme")
@login_required
def set_theme():
    form = ThemeForm()
    if form.validate_on_submit():
        current_user.theme = form.theme.data
        db.session.commit()
    else:
        flash("Ungültige Darstellung.", "danger")
    target = request.referrer
    if not is_safe_url(target):
        target = url_for("auth.profile")
    return redirect(target)


@bp.post("/profil/loeschen")
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user = current_user._get_current_object()
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash("Dein Konto und alle zugehörigen Daten wurden gelöscht.", "info")
        return redirect(url_for("main.index"))
    return render_profile(delete_form=form)
