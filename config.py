# =============================================================================
# config.py
# =============================================================================
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
QR_DIR     = os.path.join(STATIC_DIR, "qrcodes")

DATABASE_PATH = os.path.join(BASE_DIR, "database", "sdel_inventory.db")

SECRET_KEY = os.environ.get("SECRET_KEY", "sdel-vinci-secret-2024-change-en-prod")

HOST  = "0.0.0.0"
PORT  = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

APP_URL = os.environ.get("APP_URL", f"http://localhost:{PORT}")

QR_BOX_SIZE        = 10
QR_BORDER          = 4
QR_ERROR_CORRECTION = "H"

ROLES = {
    "admin":     "Administrateur",
    "operateur": "Opérateur",
    "lecteur":   "Lecteur",
}
MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM     = os.environ.get("MAIL_FROM", "")
MAIL_ALERT_TO = os.environ.get("MAIL_ALERT_TO", "")
