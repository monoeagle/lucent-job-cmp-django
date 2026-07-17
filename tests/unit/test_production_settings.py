"""Tests fuer das Production-Settings-Modul (config.settings.production).

Das Modul liest sicherheitsrelevante Werte aus der Umgebung (django-environ).
Diese Tests sichern die Kern-Invarianten: DEBUG=False, Secrets aus der Env,
ALLOWED_HOSTS als Liste, DB aus DATABASE_URL und die Security-Hardening-Flags.
"""

import importlib
import sys

import pytest

# Vollstaendige, valide Produktions-Umgebung als Basis fuer die Tests.
VALID_ENV = {
    "SECRET_KEY": "test-secret-from-env-not-the-default",
    "ALLOWED_HOSTS": "cmp.example.com,www.cmp.example.com",
    "DATABASE_URL": "postgres://cmp:s3cret@db.internal:5432/cmp_prod",
}

# Env-Variablen, die zwischen den Testlaeufen sauber zurueckgesetzt werden.
_MANAGED_KEYS = (
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "DATABASE_URL",
    "DEBUG",
    "CSRF_TRUSTED_ORIGINS",
    "SECURE_SSL_REDIRECT",
)


def _load_production(monkeypatch, env):
    """Laedt config.settings.production frisch mit der gegebenen Umgebung."""
    for key in _MANAGED_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("config.settings.production", None)
    return importlib.import_module("config.settings.production")


def test_debug_is_false_by_default(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert mod.DEBUG is False


def test_secret_key_comes_from_env(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert mod.SECRET_KEY == "test-secret-from-env-not-the-default"
    assert "change-me" not in mod.SECRET_KEY


def test_missing_secret_key_raises(monkeypatch):
    env = {k: v for k, v in VALID_ENV.items() if k != "SECRET_KEY"}
    with pytest.raises(Exception):
        _load_production(monkeypatch, env)


def test_allowed_hosts_parsed_as_list(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert mod.ALLOWED_HOSTS == ["cmp.example.com", "www.cmp.example.com"]


def test_database_read_from_url(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    db = mod.DATABASES["default"]
    assert db["ENGINE"] == "django.db.backends.postgresql"
    assert db["NAME"] == "cmp_prod"
    assert db["HOST"] == "db.internal"
    assert str(db["PORT"]) == "5432"


def test_security_hardening_enabled(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert mod.SESSION_COOKIE_SECURE is True
    assert mod.CSRF_COOKIE_SECURE is True
    assert mod.SECURE_HSTS_SECONDS > 0
    assert mod.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert mod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_static_root_configured_for_collectstatic(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert str(mod.STATIC_ROOT).endswith("staticfiles")


def test_celery_not_eager_in_production(monkeypatch):
    mod = _load_production(monkeypatch, VALID_ENV)
    assert mod.CELERY_TASK_ALWAYS_EAGER is False
