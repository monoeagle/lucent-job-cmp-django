"""Unit-Tests fuer deploy/lib.sh — die idempotenz-relevante Logik des
Offline-Installers.

Der Installer selbst braucht root, systemd, PostgreSQL und nginx und ist
deshalb nur auf einer echten VM als Ganzes pruefbar. Die Entscheidungslogik
(Env-Datei lesen, App-Verzeichnis spiegeln, Rolle/DB getrennt anlegen,
Dienste neu starten, Zertifikat gegen FQDN pruefen) laesst sich dagegen
isoliert testen — genau dort sitzen die Idempotenz-Fehler.

Externe Kommandos (psql, systemctl) werden ueber CMP_PSQL / CMP_SYSTEMCTL
injiziert und durch Fakes ersetzt.
"""

import subprocess
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[2] / "deploy" / "lib.sh"


def run_sh(snippet, cwd=None, env=None):
    """Sourcet lib.sh und fuehrt `snippet` in bash aus."""
    script = f'set -euo pipefail\nsource "{LIB}"\n{snippet}'
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


# ── cmp_env_get ───────────────────────────────────────────────────────────────


def test_env_get_liest_wert(tmp_path):
    envfile = tmp_path / "cmp.env"
    envfile.write_text("# kommentar\nSECRET_KEY=abc123\nDEBUG=False\n")

    r = run_sh(f'cmp_env_get "{envfile}" SECRET_KEY')

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "abc123"


def test_env_get_leer_wenn_schluessel_fehlt(tmp_path):
    envfile = tmp_path / "cmp.env"
    envfile.write_text("DEBUG=False\n")

    r = run_sh(f'cmp_env_get "{envfile}" SECRET_KEY')

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == ""


def test_env_get_leer_wenn_datei_fehlt(tmp_path):
    """Erstinstallation: es gibt noch keine Env-Datei — kein Fehler, nur leer."""
    r = run_sh(f'cmp_env_get "{tmp_path}/gibtsnicht.env" SECRET_KEY')

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == ""


def test_env_get_wert_mit_gleichheitszeichen_bleibt_ganz(tmp_path):
    """base64-Secrets koennen '=' als Padding enthalten."""
    envfile = tmp_path / "cmp.env"
    envfile.write_text("SECRET_KEY=ab==cd=\n")

    r = run_sh(f'cmp_env_get "{envfile}" SECRET_KEY')

    assert r.stdout.strip() == "ab==cd="


def test_env_get_matcht_nur_exakten_schluessel(tmp_path):
    """CELERY_BROKER_URL darf nicht als BROKER_URL durchgehen."""
    envfile = tmp_path / "cmp.env"
    envfile.write_text("CELERY_BROKER_URL=redis://localhost:6379/0\n")

    r = run_sh(f'cmp_env_get "{envfile}" BROKER_URL')

    assert r.stdout.strip() == ""


# ── cmp_env_args ──────────────────────────────────────────────────────────────


def test_env_args_haelt_wert_mit_leerzeichen_zusammen(tmp_path):
    """Regression: die alte $(...)-Expansion zerlegte ein DB-Passwort mit
    Leerzeichen in zwei Argumente und schickte Muell an manage.py."""
    envfile = tmp_path / "cmp.env"
    envfile.write_text(
        "SECRET_KEY=abc\n"
        "DATABASE_URL=postgres://cmp:pass wort@127.0.0.1:5432/cmp_prod\n"
    )

    r = run_sh(
        f'mapfile -d "" -t a < <(cmp_env_args "{envfile}"); '
        'printf "%s\\n" "${#a[@]}" "${a[@]}"'
    )

    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[0] == "2", f"erwartet 2 Argumente, bekam: {lines}"
    assert lines[2] == "DATABASE_URL=postgres://cmp:pass wort@127.0.0.1:5432/cmp_prod"


def test_env_args_ignoriert_kommentare_und_leerzeilen(tmp_path):
    envfile = tmp_path / "cmp.env"
    envfile.write_text("# kommentar\n\nDEBUG=False\n\n# noch einer\nSECRET_KEY=x\n")

    r = run_sh(
        f'mapfile -d "" -t a < <(cmp_env_args "{envfile}"); echo "${{#a[@]}}"'
    )

    assert r.stdout.strip() == "2"


# ── cmp_bundle_dir ────────────────────────────────────────────────────────────


def test_bundle_dir_ist_eine_ebene_ueber_deploy(tmp_path):
    """install.sh liegt im Bundle unter deploy/ — cmp/, wheels/ und
    requirements/ liegen eine Ebene hoeher."""
    (tmp_path / "deploy").mkdir()

    r = run_sh(f'cmp_bundle_dir "{tmp_path}/deploy"')

    assert r.stdout.strip() == str(tmp_path)


# ── Release-Bundle muss lib.sh mitliefern ─────────────────────────────────────


def test_release_bundle_enthaelt_lib_sh(tmp_path):
    """install.sh sourct lib.sh — fehlt sie im ZIP, ist der Installer auf der
    VM sofort tot. Die Staging-Regeln des Release-Builds duerfen sie nie
    wegfiltern."""
    import shutil
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    import build_release

    dest = tmp_path / "stage" / "deploy"
    shutil.copytree(LIB.parent, dest, ignore=build_release._ignore)

    assert (dest / "lib.sh").is_file(), "lib.sh fehlt im gestagten Bundle"
    assert (dest / "ui.sh").is_file(), "ui.sh fehlt im gestagten Bundle"
    assert (dest / "install.sh").is_file()


def test_bundle_bekommt_maschinenlesbare_version(tmp_path):
    """Die Version steht nur in lucent-hub.yml — die ist NICHT im Bundle.
    Ohne VERSION-Datei kann der Pruefbereich auf der VM keine Version zeigen.
    START-HIER.txt zaehlt nicht: Fliesstext ist nicht maschinenlesbar."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    import build_release

    stage = tmp_path / "stage"
    stage.mkdir()

    build_release.write_version(stage, "1.2.3")

    assert (stage / "VERSION").read_text().strip() == "1.2.3"
