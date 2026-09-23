from flask_login import current_user
from flask_wtf import FlaskForm
from sqlalchemy import func, select
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Regexp, ValidationError
from wtforms.widgets import CheckboxInput, ColorInput, DateInput, ListWidget

from app.extensions import db
from app.models import FREQ_WEEKDAYS, FREQUENCY_LABELS, WEEKDAY_NAMES, Category, Tag, User
from app.utils import today_local

MIN_PASSWORD_LENGTH = 8

ICON_CHOICES = [
    ("bi-tag", "Etikett"),
    ("bi-heart-pulse", "Gesundheit"),
    ("bi-bicycle", "Sport"),
    ("bi-cup-hot", "Ernährung"),
    ("bi-moon-stars", "Schlaf"),
    ("bi-book", "Lernen"),
    ("bi-briefcase", "Arbeit"),
    ("bi-house", "Haushalt"),
    ("bi-people", "Soziales"),
    ("bi-piggy-bank", "Finanzen"),
    ("bi-music-note-beamed", "Kreativität"),
    ("bi-tree", "Natur"),
    ("bi-phone", "Digital"),
    ("bi-star", "Sonstiges"),
]


class BaseForm(FlaskForm):
    # das CSRF-Token prüft CSRFProtect für alle Requests
    class Meta:
        csrf = False


class GermanDateField(DateField):
    widget = DateInput()

    def process_formdata(self, valuelist):
        try:
            super().process_formdata(valuelist)
        except ValueError:
            raise ValueError("Bitte gib ein gültiges Datum ein.")


def clean(value):
    return value.strip() if isinstance(value, str) else value


def clean_email(value):
    return value.strip().lower() if isinstance(value, str) else value


def password_rules(form, field):
    password = field.data or ""
    if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        raise ValidationError("Das Passwort muss mindestens einen Buchstaben und eine Ziffer enthalten.")


def password_validators():
    return [
        DataRequired(message="Bitte gib ein Passwort ein."),
        Length(min=MIN_PASSWORD_LENGTH, message=f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein."),
        password_rules,
    ]


def email_validators():
    return [
        DataRequired(message="Bitte gib eine E-Mail-Adresse ein."),
        Email(message="Bitte gib eine gültige E-Mail-Adresse ein."),
        Length(max=120, message="Die E-Mail-Adresse ist zu lang."),
    ]


def category_choices():
    rows = db.session.scalars(
        select(Category).where(Category.user_id == current_user.id).order_by(func.lower(Category.name))
    ).all()
    return [(0, "Keine Kategorie")] + [(c.id, c.name) for c in rows]


def tag_choices():
    rows = db.session.scalars(
        select(Tag).where(Tag.user_id == current_user.id).order_by(func.lower(Tag.name))
    ).all()
    return [(t.id, t.name) for t in rows]


class RegistrationForm(BaseForm):
    username = StringField("Benutzername", filters=[clean], validators=[
        DataRequired(message="Bitte gib einen Benutzernamen ein."),
        Length(min=3, max=30, message="Der Benutzername muss 3 bis 30 Zeichen lang sein."),
        Regexp(r"^[A-Za-z0-9_.-]+$", message="Erlaubt sind nur Buchstaben (ohne Umlaute), Ziffern und _ . -"),
    ])
    email = StringField("E-Mail-Adresse", filters=[clean_email], validators=email_validators())
    password = PasswordField("Passwort", validators=password_validators())
    password2 = PasswordField("Passwort wiederholen", validators=[
        DataRequired(message="Bitte wiederhole dein Passwort."),
        EqualTo("password", message="Die Passwörter stimmen nicht überein."),
    ])
    submit = SubmitField("Konto erstellen")

    def validate_username(self, field):
        taken = db.session.scalar(select(User.id).where(func.lower(User.username) == field.data.lower()))
        if taken:
            raise ValidationError("Dieser Benutzername ist bereits vergeben.")

    def validate_email(self, field):
        taken = db.session.scalar(select(User.id).where(func.lower(User.email) == field.data.lower()))
        if taken:
            raise ValidationError("Diese E-Mail-Adresse ist bereits registriert.")


class LoginForm(BaseForm):
    identifier = StringField("Benutzername oder E-Mail", filters=[clean], validators=[
        DataRequired(message="Bitte gib Benutzername oder E-Mail ein."),
    ])
    password = PasswordField("Passwort", validators=[DataRequired(message="Bitte gib dein Passwort ein.")])
    remember = BooleanField("Angemeldet bleiben")
    submit = SubmitField("Anmelden")


class ChangeEmailForm(BaseForm):
    new_email = StringField("Neue E-Mail-Adresse", filters=[clean_email], validators=email_validators())
    email_password = PasswordField("Aktuelles Passwort", validators=[
        DataRequired(message="Bitte bestätige mit deinem Passwort."),
    ])
    submit = SubmitField("E-Mail ändern")

    def validate_new_email(self, field):
        other = db.session.scalar(
            select(User.id).where(func.lower(User.email) == field.data.lower(), User.id != current_user.id)
        )
        if other:
            raise ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")

    def validate_email_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError("Das Passwort ist nicht korrekt.")


class ChangePasswordForm(BaseForm):
    current_password = PasswordField("Aktuelles Passwort", validators=[
        DataRequired(message="Bitte gib dein aktuelles Passwort ein."),
    ])
    new_password = PasswordField("Neues Passwort", validators=password_validators())
    confirm_password = PasswordField("Neues Passwort wiederholen", validators=[
        DataRequired(message="Bitte wiederhole das neue Passwort."),
        EqualTo("new_password", message="Die Passwörter stimmen nicht überein."),
    ])
    submit = SubmitField("Passwort ändern")

    def validate_current_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError("Das aktuelle Passwort ist nicht korrekt.")


class ThemeForm(BaseForm):
    theme = SelectField("Darstellung", choices=[("light", "Hell"), ("dark", "Dunkel")], validators=[
        DataRequired(message="Bitte wähle eine Darstellung."),
    ])
    submit = SubmitField("Speichern")


class DeleteAccountForm(BaseForm):
    delete_password = PasswordField("Passwort zur Bestätigung", validators=[
        DataRequired(message="Bitte bestätige mit deinem Passwort."),
    ])
    submit = SubmitField("Konto endgültig löschen")

    def validate_delete_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError("Das Passwort ist nicht korrekt.")


class HabitForm(BaseForm):
    title = StringField("Titel", filters=[clean], validators=[
        DataRequired(message="Bitte gib einen Titel ein."),
        Length(max=100, message="Der Titel darf höchstens 100 Zeichen lang sein."),
    ])
    description = TextAreaField("Beschreibung", filters=[clean], validators=[
        Length(max=1000, message="Die Beschreibung darf höchstens 1000 Zeichen lang sein."),
    ])
    category_id = SelectField("Kategorie", coerce=int)
    frequency = SelectField("Häufigkeit", choices=list(FREQUENCY_LABELS.items()))
    weekdays = SelectMultipleField(
        "Wochentage",
        coerce=int,
        choices=list(enumerate(WEEKDAY_NAMES)),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
    )
    target_per_period = IntegerField("Ziel pro Woche", validators=[
        DataRequired(message="Bitte gib eine Zahl von 1 bis 7 ein."),
        NumberRange(min=1, max=7, message="Bitte gib eine Zahl von 1 bis 7 ein."),
    ])
    start_date = GermanDateField("Startdatum", validators=[DataRequired(message="Bitte wähle ein Startdatum.")])
    tags = SelectMultipleField(
        "Tags",
        coerce=int,
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
    )
    submit = SubmitField("Speichern")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id.choices = category_choices()
        self.tags.choices = tag_choices()

    def validate_weekdays(self, field):
        if self.frequency.data == FREQ_WEEKDAYS and not field.data:
            raise ValidationError("Bitte wähle mindestens einen Wochentag.")


class CategoryForm(BaseForm):
    name = StringField("Name", filters=[clean], validators=[
        DataRequired(message="Bitte gib einen Namen ein."),
        Length(max=50, message="Der Name darf höchstens 50 Zeichen lang sein."),
    ])
    color = StringField("Farbe", widget=ColorInput(), validators=[
        Regexp(r"^#[0-9a-fA-F]{6}$", message="Bitte wähle eine gültige Farbe."),
    ])
    icon = SelectField("Symbol", choices=ICON_CHOICES)
    submit = SubmitField("Speichern")

    def __init__(self, *args, editing_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editing_id = editing_id

    def validate_name(self, field):
        query = select(Category.id).where(
            Category.user_id == current_user.id,
            func.lower(Category.name) == field.data.lower(),
        )
        if self.editing_id:
            query = query.where(Category.id != self.editing_id)
        if db.session.scalar(query):
            raise ValidationError("Diese Kategorie gibt es schon.")


class TagForm(BaseForm):
    name = StringField("Name", filters=[clean], validators=[
        DataRequired(message="Bitte gib einen Namen ein."),
        Length(max=30, message="Der Name darf höchstens 30 Zeichen lang sein."),
    ])
    submit = SubmitField("Speichern")

    def __init__(self, *args, editing_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editing_id = editing_id

    def validate_name(self, field):
        query = select(Tag.id).where(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == field.data.lower(),
        )
        if self.editing_id:
            query = query.where(Tag.id != self.editing_id)
        if db.session.scalar(query):
            raise ValidationError("Diesen Tag gibt es schon.")

class LogForm(BaseForm):
    date = GermanDateField("Datum", validators=[DataRequired(message="Bitte wähle ein Datum.")])
    completed = BooleanField("Erledigt")
    note = TextAreaField("Notiz (optional)", filters=[clean], validators=[
        Length(max=500, message="Die Notiz darf höchstens 500 Zeichen lang sein."),
    ])
    submit = SubmitField("Eintrag speichern")

    def __init__(self, *args, habit, **kwargs):
        super().__init__(*args, **kwargs)
        self.habit = habit

    def validate_date(self, field):
        if field.data > today_local():
            raise ValidationError("Das Datum darf nicht in der Zukunft liegen.")
        if field.data < self.habit.start_date:
            raise ValidationError("Das Datum liegt vor dem Startdatum der Gewohnheit.")
