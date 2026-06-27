#!/usr/bin/env python3
"""Build the OFFLINE delivery ZIP for AlmaLinux/Rocky 9 (runtime only).

Assembles an allow-listed subset of the repo + the offline wheelhouse + the
installer + the deployment docs into a versioned ZIP. Everything not needed to
RUN/INSTALL the portal is left out (git history, tests, docs sources, tooling,
CLAUDE.md, caches).

Run from anywhere:
    python3 tools/build_release.py
Output:
    release/Lucent-MPP-Django-<version>-almalinux9-offline.zip
"""
from __future__ import annotations
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG_BASENAME = "Lucent-MPP-Django"
TARGET = "almalinux9-offline"

# Allow-list: ONLY what the VM needs to install + run the portal.
INCLUDE_FILES = [".env.example"]
INCLUDE_DIRS = ["mpp", "requirements", "wheels", "deploy"]
INCLUDE_DOCS = ["docs/deployment/vm-installation-offline.md",
                "docs/deployment/vm-installation.md"]

PRUNE_DIRS = {"__pycache__", ".pytest_cache", "node_modules", ".git", "staticfiles"}
PRUNE_SUFFIXES = (".pyc", ".pyo", ".sqlite3")
PRUNE_NAMES = {".env", "db.sqlite3"}


def version() -> str:
    hub = (ROOT / "lucent-hub.yml").read_text(encoding="utf-8")
    m = re.search(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', hub, re.MULTILINE)
    return m.group(1) if m else "0.0.0"


def _ignore(_dir, names):
    return [n for n in names
            if n in PRUNE_DIRS or n in PRUNE_NAMES or n.endswith(PRUNE_SUFFIXES)]


def start_here(ver: str) -> str:
    return f"""\
MPP Django — Marketplace Portal v{ver}  ·  OFFLINE-Release für AlmaLinux/Rocky 9
================================================================================

Dieses Bundle installiert das Portal OHNE Internet. Es bringt alle Python-Pakete
als Wheels (wheels/) mit.

WAS DU AUF DER VM BRAUCHST (einmalig, siehe docs/vm-installation-offline.md):
  - AlmaLinux/Rocky 9, x86_64
  - System-Pakete: python3.12, postgresql16-server, redis, nginx, openssl
    (Online:  sudo dnf install python3.12 postgresql16-server redis nginx openssl
     Offline: aus dem RPM-Bundle, Doku §2/§7)
  - PostgreSQL + Redis gestartet (Doku §8)

INSTALLATION (idiotensicher, ein Befehl):
  1. Bundle auf die VM kopieren und entpacken:
        tar -xzf {PKG_BASENAME}-{ver}-{TARGET}.zip   (bzw. unzip)
        cd {PKG_BASENAME}-{ver}-{TARGET}
  2. Installer als root ausführen:
        sudo ./deploy/install.sh
     Er fragt nur FQDN + DB-Passwort, macht den Rest: venv + Wheels offline,
     DB anlegen, .env, Migrationen, Static, systemd (gunicorn+celery), nginx+TLS,
     firewalld/SELinux.
  3. Browser:  https://<FQDN>/        Admin: https://<FQDN>/admin/

Vollständige Schritt-für-Schritt-Doku (inkl. RPM-Beschaffung air-gapped):
  docs/vm-installation-offline.md   (offline / air-gapped)
  docs/vm-installation.md           (online-Variante, Let's Encrypt)

Stack: Django 6 · Python 3.12 · PostgreSQL 16 · Redis · gunicorn · nginx
"""


def main() -> Path:
    ver = version()
    pkg = f"{PKG_BASENAME}-{ver}-{TARGET}"
    build = ROOT / "build"
    stage = build / pkg
    out = ROOT / "release" / f"{pkg}.zip"
    (ROOT / "release").mkdir(exist_ok=True)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    missing = []
    for f in INCLUDE_FILES:
        src = ROOT / f
        shutil.copy2(src, stage / Path(f).name) if src.is_file() else missing.append(f)
    for d in INCLUDE_DIRS:
        src = ROOT / d
        shutil.copytree(src, stage / d, ignore=_ignore) if src.is_dir() else missing.append(d + "/")
    docs_dst = stage / "docs"
    docs_dst.mkdir(exist_ok=True)
    for doc in INCLUDE_DOCS:
        src = ROOT / doc
        shutil.copy2(src, docs_dst / Path(doc).name) if src.is_file() else missing.append(doc)

    (stage / "START-HIER.txt").write_text(start_here(ver), encoding="utf-8")
    # install.sh ausführbar halten
    (stage / "deploy" / "install.sh").chmod(0o755)

    wheels = list((stage / "wheels").glob("*.whl")) if (stage / "wheels").is_dir() else []
    sdists = list((stage / "wheels").glob("*.tar.gz")) if (stage / "wheels").is_dir() else []

    if out.exists():
        out.unlink()
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in stage.rglob("*"):
            if p.is_file():
                z.write(p, Path(pkg) / p.relative_to(stage))
                n += 1

    mb = out.stat().st_size / 1_000_000
    print(f"Paket  : {pkg}")
    print(f"Wheels : {len(wheels)} (.whl){'  ⚠ ' + str(len(sdists)) + ' sdists!' if sdists else ''}")
    print(f"Dateien: {n}")
    print(f"ZIP    : {out}  ({mb:.1f} MB)")
    if not wheels:
        print("WARN   : kein Wheel im Bundle — zuerst wheels/ erzeugen (siehe wheels/README.md)")
    if missing:
        print("WARN   : nicht gefunden (übersprungen): " + ", ".join(missing))
    return out


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
