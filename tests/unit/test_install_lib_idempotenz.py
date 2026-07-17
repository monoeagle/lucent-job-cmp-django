"""Unit-Tests fuer die Idempotenz-Logik in deploy/lib.sh.

Jeder Test hier bildet einen konkreten Fehler ab, der einen zweiten
Installer-Lauf falsch ausgehen liess. psql und systemctl werden durch Fakes
ersetzt, die ihre Aufrufe protokollieren.
"""

import subprocess
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[2] / "deploy" / "lib.sh"


def run_sh(snippet, env=None):
    script = f'set -euo pipefail\nsource "{LIB}"\n{snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env
    )


@pytest.fixture
def fake_psql(tmp_path):
    """Ein psql-Ersatz, der Aufrufe mitschreibt und Existenz-Abfragen
    ueber FAKE_ROLE_EXISTS / FAKE_DB_EXISTS beantwortet."""
    log = tmp_path / "psql.log"
    script = tmp_path / "fake-psql"
    script.write_text(
        "#!/usr/bin/env bash\n"
        'args="$*"\n'
        'stdin=""\n'
        '[ -t 0 ] || stdin="$(cat)"\n'
        'printf "%s %s\\n" "$args" "$stdin" >> "$FAKE_PSQL_LOG"\n'
        'case "$args" in\n'
        '  *pg_roles*)    [ "${FAKE_ROLE_EXISTS:-0}" = 1 ] && echo 1 ;;\n'
        '  *pg_database*) [ "${FAKE_DB_EXISTS:-0}" = 1 ] && echo 1 ;;\n'
        "esac\n"
        "exit 0\n"
    )
    script.chmod(0o755)
    return {"cmd": str(script), "log": log}


def psql_env(fake_psql, role_exists=0, db_exists=0):
    import os

    e = dict(os.environ)
    e.update(
        CMP_PSQL=fake_psql["cmd"],
        FAKE_PSQL_LOG=str(fake_psql["log"]),
        FAKE_ROLE_EXISTS=str(role_exists),
        FAKE_DB_EXISTS=str(db_exists),
    )
    return e


# ── cmp_pg_ensure: Rolle und DB muessen getrennt geprueft werden ──────────────


def test_pg_ensure_legt_rolle_und_db_an_wenn_nichts_existiert(fake_psql):
    r = run_sh(
        'cmp_pg_ensure cmp cmp_prod "geheim"',
        env=psql_env(fake_psql, role_exists=0, db_exists=0),
    )

    assert r.returncode == 0, r.stderr
    log = fake_psql["log"].read_text()
    assert "CREATE ROLE cmp" in log
    assert "CREATE DATABASE cmp_prod" in log


def test_pg_ensure_legt_db_an_wenn_nur_die_rolle_existiert(fake_psql):
    """Regression: Bricht Lauf 1 nach CREATE ROLE ab, sah Lauf 2 die Rolle
    und legte die Datenbank nie an — migrate lief dann ins Leere."""
    r = run_sh(
        'cmp_pg_ensure cmp cmp_prod "geheim"',
        env=psql_env(fake_psql, role_exists=1, db_exists=0),
    )

    assert r.returncode == 0, r.stderr
    log = fake_psql["log"].read_text()
    assert "CREATE DATABASE cmp_prod" in log, (
        "Datenbank wurde nicht angelegt, obwohl sie fehlt:\n" + log
    )
    assert "CREATE ROLE" not in log, "Rolle existiert bereits, kein CREATE erwartet"


def test_pg_ensure_legt_nichts_doppelt_an_wenn_beides_existiert(fake_psql):
    r = run_sh(
        'cmp_pg_ensure cmp cmp_prod "geheim"',
        env=psql_env(fake_psql, role_exists=1, db_exists=1),
    )

    assert r.returncode == 0, r.stderr
    log = fake_psql["log"].read_text()
    assert "CREATE ROLE" not in log
    assert "CREATE DATABASE" not in log
    assert "ALTER ROLE cmp" in log, "Passwort sollte aktualisiert werden"


# ── cmp_sync_app: veraltete Dateien duerfen nicht ueberleben ──────────────────


def test_sync_app_entfernt_dateien_die_es_im_bundle_nicht_mehr_gibt(tmp_path):
    """Regression: cp -a merged nur — ein im neuen Release geloeschtes Modul
    (inkl. alter Migrationen) blieb auf der VM liegen."""
    src = tmp_path / "bundle" / "cmp"
    src.mkdir(parents=True)
    (src / "manage.py").write_text("v2")
    dest = tmp_path / "app" / "cmp"
    dest.mkdir(parents=True)
    (dest / "manage.py").write_text("v1")
    (dest / "altmodul.py").write_text("alt")

    r = run_sh(f'cmp_sync_app "{src}" "{dest}"')

    assert r.returncode == 0, r.stderr
    assert (dest / "manage.py").read_text() == "v2"
    assert not (dest / "altmodul.py").exists(), "veraltete Datei ueberlebt"


def test_sync_app_verweigert_leeres_ziel(tmp_path):
    """rm -rf mit leerer Variable darf nie passieren — und zwar an der eigenen
    Guard-Klausel scheitern, nicht zufaellig erst an rm selbst."""
    src = tmp_path / "cmp"
    src.mkdir()

    r = run_sh(f'cmp_sync_app "{src}" ""')

    assert r.returncode != 0, "leeres Ziel muss abgelehnt werden"
    assert "leeres Ziel" in r.stderr, (
        "muss an der Guard-Klausel scheitern, stderr war: " + r.stderr
    )


# ── cmp_secret_key: darf bei einem Re-Run nicht rotieren ──────────────────────


def test_secret_key_bleibt_bei_bestehender_env_datei_erhalten(tmp_path):
    """Regression: jeder Lauf erzeugte einen neuen SECRET_KEY und warf damit
    alle angemeldeten Nutzer raus."""
    envfile = tmp_path / "cmp.env"
    envfile.write_text("SECRET_KEY=bestehender-key-nicht-anfassen\n")

    r = run_sh(f'cmp_secret_key "{envfile}"')

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "bestehender-key-nicht-anfassen"


def test_secret_key_wird_bei_erstinstallation_erzeugt(tmp_path):
    r = run_sh(f'cmp_secret_key "{tmp_path}/gibtsnicht.env"')

    assert r.returncode == 0, r.stderr
    assert len(r.stdout.strip()) >= 40, "generierter Key zu kurz"


def test_secret_key_ist_bei_zwei_erstinstallationen_verschieden(tmp_path):
    a = run_sh(f'cmp_secret_key "{tmp_path}/x.env"').stdout.strip()
    b = run_sh(f'cmp_secret_key "{tmp_path}/x.env"').stdout.strip()

    assert a != b


# ── cmp_restart_services: ein Upgrade muss den neuen Code laden ───────────────


def test_restart_services_startet_laufende_dienste_wirklich_neu(tmp_path):
    """Regression: `systemctl enable --now` ist auf einer bereits laufenden
    Unit ein No-Op — nach einem Upgrade lief der alte Code weiter."""
    import os

    log = tmp_path / "systemctl.log"
    fake = tmp_path / "fake-systemctl"
    fake.write_text(
        '#!/usr/bin/env bash\necho "$*" >> "$FAKE_SC_LOG"\nexit 0\n'
    )
    fake.chmod(0o755)
    e = dict(os.environ)
    e.update(CMP_SYSTEMCTL=str(fake), FAKE_SC_LOG=str(log))

    r = run_sh("cmp_restart_services cmp-web cmp-celery", env=e)

    assert r.returncode == 0, r.stderr
    calls = log.read_text().splitlines()
    assert "daemon-reload" in calls
    assert any(
        c.startswith("restart") and "cmp-web" in c and "cmp-celery" in c
        for c in calls
    ), f"kein restart beider Units: {calls}"
    assert any(c.startswith("enable") for c in calls), "Autostart muss gesetzt sein"


# ── cmp_cert_matches_fqdn: Zertifikat darf nicht zum FQDN driften ─────────────


def _make_cert(tmp_path, fqdn):
    crt = tmp_path / f"{fqdn}.crt"
    key = tmp_path / f"{fqdn}.key"
    subprocess.run(
        [
            "openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048",
            "-days", "1", "-keyout", str(key), "-out", str(crt),
            "-subj", f"/CN={fqdn}", "-addext", f"subjectAltName=DNS:{fqdn}",
        ],
        check=True, capture_output=True,
    )
    return crt


def test_cert_matches_fqdn_erkennt_passendes_zertifikat(tmp_path):
    crt = _make_cert(tmp_path, "cmp.internal.example.com")

    r = run_sh(f'cmp_cert_matches_fqdn "{crt}" cmp.internal.example.com')

    assert r.returncode == 0, r.stderr


def test_cert_matches_fqdn_erkennt_geaenderten_fqdn(tmp_path):
    """Regression: das Zertifikat war nur per Datei-Existenz geschuetzt — nach
    einem Re-Run mit neuem FQDN lieferte nginx den alten CN aus."""
    crt = _make_cert(tmp_path, "alt.example.com")

    r = run_sh(f'cmp_cert_matches_fqdn "{crt}" neu.example.com')

    assert r.returncode != 0, "FQDN-Drift wurde nicht erkannt"


def test_cert_matches_fqdn_ohne_zertifikat(tmp_path):
    r = run_sh(f'cmp_cert_matches_fqdn "{tmp_path}/keins.crt" cmp.example.com')

    assert r.returncode != 0


# ── cmp_cert_is_self_signed: fremde Zertifikate nie ueberschreiben ────────────


def test_cert_is_self_signed_erkennt_eigenes_zertifikat(tmp_path):
    crt = _make_cert(tmp_path, "cmp.example.com")

    r = run_sh(f'cmp_cert_is_self_signed "{crt}"')

    assert r.returncode == 0, r.stderr


def test_cert_is_self_signed_erkennt_ca_signiertes_zertifikat(tmp_path):
    """Ein vom Admin eingespieltes CA-Zertifikat darf der Installer nicht als
    eigenes Wegwerf-Zertifikat einstufen und ueberschreiben."""
    ca_key = tmp_path / "ca.key"
    ca_crt = tmp_path / "ca.crt"
    subprocess.run(
        ["openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048", "-days", "1",
         "-keyout", str(ca_key), "-out", str(ca_crt), "-subj", "/CN=Interne CA"],
        check=True, capture_output=True,
    )
    csr = tmp_path / "srv.csr"
    srv_key = tmp_path / "srv.key"
    srv_crt = tmp_path / "srv.crt"
    subprocess.run(
        ["openssl", "req", "-nodes", "-newkey", "rsa:2048", "-keyout", str(srv_key),
         "-out", str(csr), "-subj", "/CN=cmp.example.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["openssl", "x509", "-req", "-in", str(csr), "-CA", str(ca_crt),
         "-CAkey", str(ca_key), "-CAcreateserial", "-days", "1", "-out", str(srv_crt)],
        check=True, capture_output=True,
    )

    r = run_sh(f'cmp_cert_is_self_signed "{srv_crt}"')

    assert r.returncode != 0, "CA-signiertes Zertifikat faelschlich als self-signed erkannt"
