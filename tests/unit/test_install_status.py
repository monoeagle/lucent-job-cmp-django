"""Unit-Tests fuer die Status-Erhebung (deploy/ui.sh).

Die Erhebung liefert reine Daten im Render-Format (`R|zustand|name|detail`)
und macht selbst keine Ausgabe. Dadurch pruefbar, ohne dass etwas installiert
ist: PostgreSQL/nginx/Dienste werden ueber Fakes bzw. CMP_PG_PREFIX gestellt.
"""

import os
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[2] / "deploy"


def run_sh(snippet, env=None):
    script = (
        f'set -euo pipefail\nsource "{DEPLOY}/lib.sh"\nsource "{DEPLOY}/ui.sh"\n{snippet}'
    )
    base = dict(os.environ)
    base["NO_COLOR"] = "1"
    if env:
        base.update(env)
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=base
    )


@pytest.fixture
def fake_systemctl(tmp_path):
    """systemctl-Ersatz: FAKE_ACTIVE_UNITS listet die aktiven Units."""
    script = tmp_path / "fake-systemctl"
    script.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "is-active" ]; then\n'
        '  for u in ${FAKE_ACTIVE_UNITS:-}; do\n'
        '    for a in "$@"; do [ "$a" = "$u" ] && exit 0; done\n'
        "  done\n"
        "  exit 3\n"
        "fi\n"
        "exit 0\n"
    )
    script.chmod(0o755)
    return str(script)


# ── Dienst-Status ─────────────────────────────────────────────────────────────


def test_status_service_aktiv(fake_systemctl):
    r = run_sh(
        "cmp_status_service cmp-web",
        env={"CMP_SYSTEMCTL": fake_systemctl, "FAKE_ACTIVE_UNITS": "cmp-web"},
    )

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "R|ok|cmp-web|aktiv"


def test_status_service_inaktiv(fake_systemctl):
    r = run_sh(
        "cmp_status_service cmp-web",
        env={"CMP_SYSTEMCTL": fake_systemctl, "FAKE_ACTIVE_UNITS": ""},
    )

    assert r.stdout.strip() == "R|fail|cmp-web|inaktiv"


# ── nginx ─────────────────────────────────────────────────────────────────────


def test_status_nginx_fehlend(tmp_path):
    r = run_sh("cmp_status_nginx", env={"CMP_NGINX": str(tmp_path / "weg")})

    assert r.stdout.strip() == "R|fail|nginx|nicht installiert"


def test_status_nginx_vorhanden(tmp_path):
    b = tmp_path / "nginx"
    b.write_text("#!/bin/sh\n")
    b.chmod(0o755)

    r = run_sh("cmp_status_nginx", env={"CMP_NGINX": str(b)})

    assert r.stdout.strip().startswith("R|ok|nginx|")


# ── PostgreSQL ────────────────────────────────────────────────────────────────


def _pg_root(tmp_path, kind):
    p = (
        tmp_path / "usr" / "pgsql-16" / "bin" / "psql"
        if kind == "pgdg"
        else tmp_path / "usr" / "bin" / "psql"
    )
    p.parent.mkdir(parents=True)
    p.write_text("#!/bin/sh\n")
    p.chmod(0o755)
    return tmp_path


def test_status_postgres_zeigt_erkannte_variante(tmp_path, fake_systemctl):
    root = _pg_root(tmp_path, "pgdg")

    r = run_sh(
        "cmp_status_postgres",
        env={
            "CMP_PG_PREFIX": str(root),
            "CMP_SYSTEMCTL": fake_systemctl,
            "FAKE_ACTIVE_UNITS": "postgresql-16.service",
        },
    )

    assert r.stdout.strip() == "R|ok|PostgreSQL|PGDG 16 · aktiv"


def test_status_postgres_appstream_inaktiv(tmp_path, fake_systemctl):
    root = _pg_root(tmp_path, "appstream")

    r = run_sh(
        "cmp_status_postgres",
        env={
            "CMP_PG_PREFIX": str(root),
            "CMP_SYSTEMCTL": fake_systemctl,
            "FAKE_ACTIVE_UNITS": "",
        },
    )

    assert r.stdout.strip() == "R|warn|PostgreSQL|AppStream · inaktiv"


def test_status_postgres_fehlend(tmp_path, fake_systemctl):
    r = run_sh(
        "cmp_status_postgres",
        env={"CMP_PG_PREFIX": str(tmp_path), "CMP_SYSTEMCTL": fake_systemctl},
    )

    assert r.stdout.strip() == "R|fail|PostgreSQL|nicht installiert"


# ── Installation / Version ────────────────────────────────────────────────────


def test_status_app_zeigt_installierte_version(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "VERSION").write_text("1.1.0\n")

    r = run_sh(f'cmp_status_app "{app}"')

    assert r.stdout.strip() == f"R|ok|{app}|v1.1.0"


def test_status_app_ohne_version_datei(tmp_path):
    """Aeltere Installation ohne VERSION-Marker: installiert, Version unbekannt
    — das darf nicht als Fehler und nicht als erfundene Version erscheinen."""
    app = tmp_path / "app"
    app.mkdir()

    r = run_sh(f'cmp_status_app "{app}"')

    assert r.stdout.strip() == f"R|warn|{app}|Version unbekannt"


def test_status_app_nicht_installiert(tmp_path):
    r = run_sh(f'cmp_status_app "{tmp_path}/gibtsnicht"')

    assert r.stdout.strip().startswith("R|fail|")
    assert "nicht installiert" in r.stdout


# ── Links & Ports ─────────────────────────────────────────────────────────────


def test_links_nutzen_fqdn_aus_der_env_datei(tmp_path):
    envfile = tmp_path / "cmp.env"
    envfile.write_text("ALLOWED_HOSTS=cmp.intern\n")

    r = run_sh(f'cmp_status_links "{envfile}"')

    assert r.returncode == 0, r.stderr
    assert "https://cmp.intern/" in r.stdout
    assert "8001" in r.stdout, "gunicorn-Port fehlt"
    assert "5432" in r.stdout, "PostgreSQL-Port fehlt"
    assert "6379" in r.stdout, "Redis-Port fehlt"


def test_links_erfinden_keine_url_wenn_nichts_installiert_ist(tmp_path):
    """Ohne Env-Datei gibt es keinen FQDN — dann darf dort keine erfundene
    URL stehen."""
    r = run_sh(f'cmp_status_links "{tmp_path}/gibtsnicht.env"')

    assert r.returncode == 0, r.stderr
    assert "https://" not in r.stdout
    assert "noch nicht installiert" in r.stdout


def test_links_sind_plain_zeilen_ohne_statussymbol(tmp_path):
    envfile = tmp_path / "cmp.env"
    envfile.write_text("ALLOWED_HOSTS=cmp.intern\n")

    r = run_sh(f'cmp_status_links "{envfile}"')

    for zeile in r.stdout.splitlines():
        if zeile.strip():
            assert zeile.startswith("P|") or zeile.startswith("S|"), (
                f"Links muessen Plain-Zeilen sein: {zeile}"
            )
