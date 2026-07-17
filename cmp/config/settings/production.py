"""Produktions-Settings — alle sicherheitsrelevanten Werte aus der Umgebung.

Geladen via ``DJANGO_SETTINGS_MODULE=config.settings.production``.

Konfiguration erfolgt ueber Umgebungsvariablen (django-environ). Auf der VM
werden diese typischerweise per systemd ``EnvironmentFile=`` injiziert
(siehe docs/deployment/vm-installation.md). Optional wird eine ``.env``-Datei
neben ``manage.py`` gelesen, falls vorhanden.

Pflicht-Variablen: SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL.
"""

import environ

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

env = environ.Env(
    DEBUG=(bool, False),
    SECURE_SSL_REDIRECT=(bool, True),
    SECURE_HSTS_SECONDS=(int, 31536000),  # 1 Jahr
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    # Secure-Cookies sind sicher-by-default an; der Installer schaltet sie nur
    # im HTTP-Modus (kein TLS verfuegbar) ab — sonst kaeme ueber reines HTTP
    # weder Session- noch CSRF-Cookie an und Login waere unmoeglich.
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
)

# Optionale .env-Datei (neben manage.py). In Produktion liefert systemd die
# Variablen i.d.R. direkt; eine fehlende Datei ist daher kein Fehler.
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

# ── Kern ──────────────────────────────────────────────────────────────────────
DEBUG = env("DEBUG")  # default False — DEBUG=True in PRODUCTION ist FATAL
SECRET_KEY = env("SECRET_KEY")  # ohne default -> Fehlstart, wenn nicht gesetzt
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── Datenbank (DATABASE_URL, z.B. postgres://user:pw@host:5432/db) ───────────
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"].setdefault("CONN_MAX_AGE", env.int("DB_CONN_MAX_AGE", default=60))

# ── Celery / Redis ────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = False

# ── Static Files (collectstatic -> von nginx ausgeliefert) ───────────────────
STATIC_ROOT = BASE_DIR / "staticfiles"

# ── Security-Hardening ────────────────────────────────────────────────────────
# nginx terminiert TLS und setzt X-Forwarded-Proto -> Django vertraut dem Header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")

SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
