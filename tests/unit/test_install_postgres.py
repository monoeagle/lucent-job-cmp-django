"""Unit-Tests fuer die PostgreSQL-Erkennung und die Paket-Installation
(`--with-packages`) des Offline-Installers.

Hintergrund: PGDG und das AppStream-Modul unterscheiden sich in Paketname,
Service-Name und Binary-Pfad. install.sh hatte `postgresql-16.service` (PGDG)
hart verdrahtet und rief `psql` ueber den PATH auf — PGDG legt seine Binaries
aber nach /usr/pgsql-16/bin/. Beides wird hier abgesichert.

Die Erkennung liest unterhalb von CMP_PG_PREFIX, damit sie ohne echte
Installation gegen ein Fake-Wurzelverzeichnis testbar ist.
"""

import os
import subprocess
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[2] / "deploy" / "lib.sh"


def run_sh(snippet, env=None):
    script = f'set -euo pipefail\nsource "{LIB}"\n{snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env
    )


def _fake_root(tmp_path, kind):
    """Baut ein Wurzelverzeichnis, das eine PGDG- bzw. AppStream-Installation
    nachbildet."""
    if kind == "pgdg":
        p = tmp_path / "usr" / "pgsql-16" / "bin" / "psql"
    elif kind == "appstream":
        p = tmp_path / "usr" / "bin" / "psql"
    else:
        return tmp_path
    p.parent.mkdir(parents=True)
    p.write_text("#!/bin/sh\n")
    p.chmod(0o755)
    return tmp_path


def _env(tmp_path):
    e = dict(os.environ)
    e["CMP_PG_PREFIX"] = str(tmp_path)
    return e


# ── cmp_pg_flavor ─────────────────────────────────────────────────────────────


def test_pg_flavor_erkennt_pgdg(tmp_path):
    root = _fake_root(tmp_path, "pgdg")

    r = run_sh("cmp_pg_flavor", env=_env(root))

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "pgdg"


def test_pg_flavor_erkennt_appstream(tmp_path):
    root = _fake_root(tmp_path, "appstream")

    r = run_sh("cmp_pg_flavor", env=_env(root))

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "appstream"


def test_pg_flavor_bevorzugt_pgdg_wenn_beide_da_sind(tmp_path):
    """PGDG 16 ist die dokumentierte Wahl; liegt daneben noch ein
    AppStream-Client, darf der nicht gewinnen."""
    root = _fake_root(tmp_path, "pgdg")
    _fake_root(tmp_path, "appstream")

    r = run_sh("cmp_pg_flavor", env=_env(root))

    assert r.stdout.strip() == "pgdg"


def test_pg_flavor_meldet_fehler_wenn_kein_postgres_da(tmp_path):
    r = run_sh("cmp_pg_flavor", env=_env(tmp_path))

    assert r.returncode != 0, "fehlendes PostgreSQL muss als Fehler durchschlagen"


# ── cmp_psql_bin ──────────────────────────────────────────────────────────────


def test_psql_bin_pgdg_nutzt_absoluten_pfad(tmp_path):
    """Regression: PGDG legt psql nicht in den PATH — `command -v psql` ging
    ins Leere und die DB-Anlage schlug spaeter hart fehl."""
    root = _fake_root(tmp_path, "pgdg")

    r = run_sh("cmp_psql_bin", env=_env(root))

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root / "usr/pgsql-16/bin/psql")


def test_psql_bin_appstream(tmp_path):
    root = _fake_root(tmp_path, "appstream")

    r = run_sh("cmp_psql_bin", env=_env(root))

    assert r.stdout.strip() == str(root / "usr/bin/psql")


# ── cmp_pg_service ────────────────────────────────────────────────────────────


def test_pg_service_pgdg(tmp_path):
    root = _fake_root(tmp_path, "pgdg")

    r = run_sh("cmp_pg_service", env=_env(root))

    assert r.stdout.strip() == "postgresql-16.service"


def test_pg_service_appstream(tmp_path):
    """AppStream nennt die Unit postgresql.service — ein hart verdrahtetes
    postgresql-16.service liefe hier ins Leere."""
    root = _fake_root(tmp_path, "appstream")

    r = run_sh("cmp_pg_service", env=_env(root))

    assert r.stdout.strip() == "postgresql.service"


# ── Unit-Rendering: Requires auf den ERKANNTEN Service ────────────────────────


def test_web_unit_haengt_hart_am_erkannten_pg_service(tmp_path):
    """Regression: die Doku forderte Requires=postgresql-16.service,
    install.sh schrieb nur After= — cmp-web startete auch ohne Datenbank."""
    r = run_sh(
        'cmp_render_web_unit cmp /opt/cmp/app /opt/cmp/venv /etc/cmp/cmp.env postgresql.service'
    )

    assert r.returncode == 0, r.stderr
    assert "Requires=postgresql.service" in r.stdout
    assert "After=" in r.stdout and "postgresql.service" in r.stdout
    assert "postgresql-16.service" not in r.stdout, "PGDG-Name faelschlich fest verdrahtet"


def test_web_unit_nutzt_pgdg_service_wenn_uebergeben(tmp_path):
    r = run_sh(
        'cmp_render_web_unit cmp /opt/cmp/app /opt/cmp/venv /etc/cmp/cmp.env postgresql-16.service'
    )

    assert "Requires=postgresql-16.service" in r.stdout


def test_web_unit_startet_gunicorn_auf_8001(tmp_path):
    r = run_sh(
        'cmp_render_web_unit cmp /opt/cmp/app /opt/cmp/venv /etc/cmp/cmp.env postgresql.service'
    )

    assert "/opt/cmp/venv/bin/gunicorn config.wsgi:application" in r.stdout
    assert "127.0.0.1:8001" in r.stdout


def test_celery_unit_haengt_am_erkannten_pg_service(tmp_path):
    r = run_sh(
        'cmp_render_celery_unit cmp /opt/cmp/app /opt/cmp/venv /etc/cmp/cmp.env postgresql.service'
    )

    assert r.returncode == 0, r.stderr
    assert "postgresql.service" in r.stdout
    assert "/opt/cmp/venv/bin/celery -A config worker" in r.stdout
    assert "postgresql-16.service" not in r.stdout


# ── cmp_install_packages (--with-packages) ───────────────────────────────────


@pytest.fixture
def fake_dnf(tmp_path):
    log = tmp_path / "dnf.log"
    script = tmp_path / "fake-dnf"
    script.write_text('#!/usr/bin/env bash\necho "$*" >> "$FAKE_DNF_LOG"\nexit 0\n')
    script.chmod(0o755)
    e = dict(os.environ)
    e.update(CMP_DNF=str(script), FAKE_DNF_LOG=str(log))
    return {"env": e, "log": log}


def test_install_packages_richtet_pgdg_repo_ein(fake_dnf):
    r = run_sh("cmp_install_packages", env=fake_dnf["env"])

    assert r.returncode == 0, r.stderr
    log = fake_dnf["log"].read_text()
    assert "pgdg-redhat-repo-latest.noarch.rpm" in log


def test_install_packages_deaktiviert_appstream_modul_vor_der_installation(fake_dnf):
    """Ohne 'module disable postgresql' kollidiert PGDG mit dem AppStream-Modul."""
    r = run_sh("cmp_install_packages", env=fake_dnf["env"])

    assert r.returncode == 0, r.stderr
    zeilen = fake_dnf["log"].read_text().splitlines()
    disable_idx = next(
        (i for i, z in enumerate(zeilen) if "module" in z and "disable" in z), None
    )
    install_idx = next(
        (i for i, z in enumerate(zeilen) if "postgresql16-server" in z), None
    )
    assert disable_idx is not None, f"kein 'module disable': {zeilen}"
    assert install_idx is not None, f"postgresql16-server nie installiert: {zeilen}"
    assert disable_idx < install_idx, "AppStream-Modul muss VOR der Installation weg"


def test_install_packages_installiert_alle_systempakete(fake_dnf):
    r = run_sh("cmp_install_packages", env=fake_dnf["env"])

    log = fake_dnf["log"].read_text()
    for paket in ("python3.12", "postgresql16-server", "redis", "nginx", "openssl"):
        assert paket in log, f"{paket} fehlt in der Installation"


# ── cmp_pg_datadir / cmp_pg_initdb ───────────────────────────────────────────


def test_pg_datadir_pgdg(tmp_path):
    root = _fake_root(tmp_path, "pgdg")

    r = run_sh("cmp_pg_datadir", env=_env(root))

    assert r.stdout.strip() == str(root / "var/lib/pgsql/16/data")


def test_pg_datadir_appstream(tmp_path):
    root = _fake_root(tmp_path, "appstream")

    r = run_sh("cmp_pg_datadir", env=_env(root))

    assert r.stdout.strip() == str(root / "var/lib/pgsql/data")


def _fake_setup_bin(root, kind):
    """Legt den initdb-Helfer der jeweiligen Variante als Logger an."""
    if kind == "pgdg":
        p = root / "usr" / "pgsql-16" / "bin" / "postgresql-16-setup"
    else:
        p = root / "usr" / "bin" / "postgresql-setup"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('#!/usr/bin/env bash\necho "$*" >> "$FAKE_SETUP_LOG"\nexit 0\n')
    p.chmod(0o755)
    return p


def test_pg_initdb_ruft_pgdg_setup_mit_initdb(tmp_path):
    root = _fake_root(tmp_path, "pgdg")
    _fake_setup_bin(root, "pgdg")
    log = tmp_path / "setup.log"
    e = _env(root)
    e["FAKE_SETUP_LOG"] = str(log)

    r = run_sh("cmp_pg_initdb", env=e)

    assert r.returncode == 0, r.stderr
    assert log.read_text().strip() == "initdb"


def test_pg_initdb_ruft_appstream_setup_mit_doppelstrich_initdb(tmp_path):
    """AppStream nutzt `postgresql-setup --initdb`, nicht `initdb`."""
    root = _fake_root(tmp_path, "appstream")
    _fake_setup_bin(root, "appstream")
    log = tmp_path / "setup.log"
    e = _env(root)
    e["FAKE_SETUP_LOG"] = str(log)

    r = run_sh("cmp_pg_initdb", env=e)

    assert r.returncode == 0, r.stderr
    assert log.read_text().strip() == "--initdb"


def test_pg_initdb_laesst_initialisierten_cluster_in_ruhe(tmp_path):
    """Idempotenz: initdb auf einem bestehenden Cluster schlaegt fehl — und
    duerfte im schlimmsten Fall Daten anfassen. Also vorher pruefen."""
    root = _fake_root(tmp_path, "pgdg")
    _fake_setup_bin(root, "pgdg")
    datadir = root / "var/lib/pgsql/16/data"
    datadir.mkdir(parents=True)
    (datadir / "PG_VERSION").write_text("16\n")
    log = tmp_path / "setup.log"
    e = _env(root)
    e["FAKE_SETUP_LOG"] = str(log)

    r = run_sh("cmp_pg_initdb", env=e)

    assert r.returncode == 0, r.stderr
    assert not log.exists(), "initdb wurde auf bestehendem Cluster aufgerufen"
