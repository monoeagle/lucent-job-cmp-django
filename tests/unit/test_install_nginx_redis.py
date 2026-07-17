"""Unit-Tests fuer die nginx- und Redis-Behandlung des Installers.

Hintergrund: Der Preflight prüfte nginx gar nicht. Fehlte es, lief der
Installer komplett durch (venv, DB, Migrationen, systemd) und starb erst ganz
am Ende an `cat > /etc/nginx/conf.d/cmp.conf`, weil das Verzeichnis nicht
existiert — spaet und unverstaendlich.

Redis wurde nur bemaengelt ("laeuft nicht"), statt es zu starten.
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


# ── cmp_nginx_present ─────────────────────────────────────────────────────────


def _fake_bin(tmp_path, name):
    p = tmp_path / name
    p.write_text('#!/usr/bin/env bash\nexit 0\n')
    p.chmod(0o755)
    return p


def test_nginx_present_erkennt_vorhandenes_nginx(tmp_path):
    bin_ = _fake_bin(tmp_path, "nginx")
    e = dict(os.environ)
    e["CMP_NGINX"] = str(bin_)

    r = run_sh("cmp_nginx_present", env=e)

    assert r.returncode == 0, r.stderr


def test_nginx_present_erkennt_fehlendes_nginx(tmp_path):
    e = dict(os.environ)
    e["CMP_NGINX"] = str(tmp_path / "gibtsnicht")

    r = run_sh("cmp_nginx_present", env=e)

    assert r.returncode != 0, "fehlendes nginx muss erkannt werden"


# ── cmp_ensure_redis ──────────────────────────────────────────────────────────


@pytest.fixture
def fake_systemctl(tmp_path):
    """systemctl-Ersatz mit Zustand: `enable --now` schaltet die Unit aktiv,
    sofern sie ueberhaupt installiert ist (FAKE_UNIT_INSTALLED)."""
    state = tmp_path / "state"
    state.mkdir()
    log = tmp_path / "systemctl.log"
    script = tmp_path / "fake-systemctl"
    script.write_text(
        "#!/usr/bin/env bash\n"
        'echo "$*" >> "$FAKE_SC_LOG"\n'
        'sub="$1"\n'
        'case "$sub" in\n'
        "  is-active)\n"
        '    [ -f "$FAKE_SC_STATE/active" ] && exit 0 || exit 3 ;;\n'
        "  enable|start|restart)\n"
        '    if [ -f "$FAKE_SC_STATE/installed" ] || [ "${FAKE_UNIT_INSTALLED:-1}" = 1 ]; then\n'
        '      touch "$FAKE_SC_STATE/active"; exit 0\n'
        "    else\n"
        '      echo "Unit redis.service not found." >&2; exit 1\n'
        "    fi ;;\n"
        "esac\n"
        "exit 0\n"
    )
    script.chmod(0o755)
    e = dict(os.environ)
    e.update(
        CMP_SYSTEMCTL=str(script),
        FAKE_SC_LOG=str(log),
        FAKE_SC_STATE=str(state),
    )
    return {"env": e, "log": log, "state": state}


def test_ensure_redis_laesst_laufenden_redis_in_ruhe(fake_systemctl):
    (fake_systemctl["state"] / "active").touch()

    r = run_sh("cmp_ensure_redis", env=fake_systemctl["env"])

    assert r.returncode == 0, r.stderr
    log = fake_systemctl["log"].read_text()
    assert "enable" not in log, "laufender Redis darf nicht erneut aktiviert werden"


def test_ensure_redis_startet_installierten_aber_gestoppten_redis(fake_systemctl):
    """Regression: frueher wurde nur gewarnt — der Installer lief weiter und
    Celery scheiterte spaeter am fehlenden Broker."""
    r = run_sh("cmp_ensure_redis", env=fake_systemctl["env"])

    assert r.returncode == 0, r.stderr
    log = fake_systemctl["log"].read_text()
    assert "enable" in log and "redis" in log, f"Redis wurde nicht gestartet: {log}"
    assert (fake_systemctl["state"] / "active").exists()


def test_ensure_redis_meldet_fehler_wenn_redis_nicht_installiert(fake_systemctl):
    e = dict(fake_systemctl["env"])
    e["FAKE_UNIT_INSTALLED"] = "0"

    r = run_sh("cmp_ensure_redis", env=e)

    assert r.returncode != 0, "nicht installierter Redis muss als Fehler durchschlagen"


@pytest.fixture
def fake_dnf(tmp_path, fake_systemctl):
    """dnf-Ersatz: loggt den Aufruf und markiert Redis danach als installiert
    (setzt den installed-Marker, den fake_systemctl beim enable prüft)."""
    log = tmp_path / "dnf.log"
    script = tmp_path / "fake-dnf"
    script.write_text(
        "#!/usr/bin/env bash\n"
        'echo "$*" >> "$FAKE_DNF_LOG"\n'
        'touch "$FAKE_SC_STATE/installed"\n'
        "exit 0\n"
    )
    script.chmod(0o755)
    e = dict(fake_systemctl["env"])
    e.update(CMP_DNF=str(script), FAKE_DNF_LOG=str(log), FAKE_UNIT_INSTALLED="0")
    return {"env": e, "dnf_log": log, "sc": fake_systemctl}


def test_ensure_redis_installiert_aus_bundle_rpm_wenn_fehlt(tmp_path, fake_dnf):
    """Offline-Bundle: fehlt Redis, liegt aber ein redis-RPM im Bundle, wird es
    air-gapped nachinstalliert (statt Abbruch) — Celery braucht den Broker."""
    rpmdir = tmp_path / "rpms"
    rpmdir.mkdir()
    (rpmdir / "redis-7.0.0-1.el9.x86_64.rpm").write_text("fake")

    r = run_sh(f'cmp_ensure_redis "{rpmdir}"', env=fake_dnf["env"])

    assert r.returncode == 0, r.stderr
    dnf_log = fake_dnf["dnf_log"].read_text()
    assert "install" in dnf_log and "redis" in dnf_log, f"dnf install nicht aufgerufen: {dnf_log}"
    assert (fake_dnf["sc"]["state"] / "active").exists(), "Redis nach Install nicht gestartet"


def test_ensure_redis_ohne_rpm_und_ohne_redis_schlaegt_fehl(tmp_path, fake_dnf):
    """Kein Redis installiert UND kein redis-RPM im Bundle → Fehler (nicht still
    durchlaufen; Celery scheitert sonst am fehlenden Broker)."""
    rpmdir = tmp_path / "rpms"
    rpmdir.mkdir()  # leer — kein redis-RPM

    r = run_sh(f'cmp_ensure_redis "{rpmdir}"', env=fake_dnf["env"])

    assert r.returncode != 0, "ohne Redis und ohne RPM muss es fehlschlagen"
