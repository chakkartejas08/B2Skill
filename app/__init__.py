import os

from flask import Flask, render_template

from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (register models with SQLAlchemy)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User

        return User.query.get(user_id)

    # ---- Blueprints ----
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.business import business_bp
    from app.routes.projects import projects_bp
    from app.routes.messages import messages_bp
    from app.routes.notifications import notifications_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(business_bp, url_prefix="/business")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ---- Context processors ----
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.services.notification_service import unread_count

        unread = 0
        if current_user.is_authenticated:
            unread = unread_count(current_user.id)
        return {"unread_notification_count": unread, "app_name": "B2Skill AI"}

    # ---- CLI commands ----
    from app.cli import register_cli

    register_cli(app)

    return app
