import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'biz2skill.db')}"
    )
    # Some hosts (Render, Heroku) provide postgres:// URLs, but SQLAlchemy 1.4+
    # requires the postgresql:// scheme — normalize it automatically.
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Platform business rules ----
    # Kept as a *default* only. The authoritative, admin-editable value lives
    # in the PlatformSetting table (see app/models/platform_setting.py) so it
    # can be changed at runtime without a redeploy.
    PLATFORM_COMMISSION_PERCENT_DEFAULT = float(
        os.environ.get("PLATFORM_COMMISSION_PERCENT", "9")
    )

    # ---- Uploads ----
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "instance", "uploads")
    )
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "8")) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_FILE_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "webp", "pdf", "doc", "docx",
        "zip", "ppt", "pptx", "xls", "xlsx", "txt", "mp4", "mov",
    }

    # ---- AI service ----
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
    AI_API_KEY = os.environ.get("AI_API_KEY", "")
    AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")

    # ---- Payment service ----
    PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "mock")
    PAYMENT_API_KEY = os.environ.get("PAYMENT_API_KEY", "")
    PAYMENT_API_SECRET = os.environ.get("PAYMENT_API_SECRET", "")

    # ---- Session ----
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
