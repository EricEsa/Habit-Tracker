import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from app.extensions import csrf, db, limiter, login_manager
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY fehlt. Kopiere .env.example nach .env und trage einen Wert ein.")

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melde dich an, um diese Seite zu sehen."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from app import models
    from app.api.routes import bp as api_bp
    from app.auth.routes import bp as auth_bp
    from app.habits.routes import bp as habits_bp
    from app.main.routes import bp as main_bp
    from app.stats.routes import bp as stats_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(habits_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_constants():
        return {
            "FREQUENCY_LABELS": models.FREQUENCY_LABELS,
            "WEEKDAY_NAMES": models.WEEKDAY_NAMES,
        }

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    def is_api():
        return request.path.startswith("/api/")

    @app.errorhandler(404)
    def not_found(error):
        if is_api():
            return jsonify(error="Nicht gefunden."), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        if is_api():
            return jsonify(error="Zu viele Anfragen."), 429
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        if is_api():
            return jsonify(error="Interner Serverfehler."), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if is_api():
            return jsonify(error="Sicherheits-Token ungültig. Bitte Seite neu laden."), 400
        flash("Das Formular ist abgelaufen oder ungültig. Bitte versuche es erneut.", "warning")
        return redirect(url_for("main.index"))
