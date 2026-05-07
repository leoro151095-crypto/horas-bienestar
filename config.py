import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = INSTANCE_DIR / "app.db"


def _normalize_database_url(database_url):
    if not database_url:
        return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    if not database_url.startswith("sqlite:///"):
        return database_url

    sqlite_path = database_url[len("sqlite:///"):]
    if sqlite_path in ("", ":memory:"):
        return database_url

    if sqlite_path.startswith("/"):
        return database_url

    if len(sqlite_path) >= 3 and sqlite_path[1] == ":" and sqlite_path[2] in ("/", "\\"):
        return f"sqlite:///{Path(sqlite_path).as_posix()}"

    resolved_path = (BASE_DIR / sqlite_path).resolve()
    return f"sqlite:///{resolved_path.as_posix()}"

class Config:
    APP_ENV = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development")).lower()
    IS_PRODUCTION = APP_ENV == "production"
    DEBUG = os.environ.get("FLASK_DEBUG", "false" if IS_PRODUCTION else "true").lower() == "true"
    SECURITY_HARDENING_ENABLED = os.environ.get("SECURITY_HARDENING_ENABLED", "false").lower() == "true"

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_this")
    REQUIRE_STRONG_SECRET_KEY = SECURITY_HARDENING_ENABLED and os.environ.get("REQUIRE_STRONG_SECRET_KEY", "true" if IS_PRODUCTION else "false").lower() == "true"
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Reverse-proxy support (Render/Nginx/etc.)
    TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "true" if IS_PRODUCTION else "false").lower() == "true"

    # Session/cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true" if IS_PRODUCTION else "false").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get("SESSION_LIFETIME_HOURS", "8")))
    SESSION_INACTIVITY_TIMEOUT_MINUTES = int(os.environ.get("SESSION_INACTIVITY_TIMEOUT_MINUTES", "30"))
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024

    # HTTPS transport security (applied only on secure requests)
    HSTS_SECONDS = int(os.environ.get("HSTS_SECONDS", "31536000" if IS_PRODUCTION else "0"))
    HSTS_INCLUDE_SUBDOMAINS = os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
    HSTS_PRELOAD = os.environ.get("HSTS_PRELOAD", "false").lower() == "true"

    # Logging
    LOG_FILE = os.environ.get("LOG_FILE", "app.log")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Notificaciones email
    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"

    # Notificaciones SMS (Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")

    # Admin de prueba persistente
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@campusucc.edu.co")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")
    DEFAULT_ADMIN_NAME = os.environ.get("DEFAULT_ADMIN_NAME", "admin")

    # Meta de horas de bienestar por estudiante
    REQUIRED_WELLBEING_HOURS = float(os.environ.get("REQUIRED_WELLBEING_HOURS", "40"))
