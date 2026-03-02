import os
from pathlib import Path

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
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_this")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
