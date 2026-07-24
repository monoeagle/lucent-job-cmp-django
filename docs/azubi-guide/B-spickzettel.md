# B — Spickzettel

> **In diesem Anhang:** Die wichtigsten Befehle aus dem Guide auf einen Blick —
> zum Kopieren, wenn du nicht erst wieder das ganze Kapitel durchsuchen willst.

## Setup

```bash
# Virtuelle Umgebung anlegen
python3.12 -m venv venv

# Abhängigkeiten installieren
venv/bin/pip install -r requirements/dev.txt

# Alternativ: interaktiver Launcher (Menüpunkt "Vollständiges Setup")
bash scripts/run.sh
```

## Datenbank & Seed

```bash
python cmp/manage.py migrate
python cmp/manage.py seed
```

Demo-Logins nach dem Seed:

| Login | Passwort | Rolle |
|-------|----------|-------|
| `test-requester` | `test123` | requester |
| `test-approver` | `test123` | approver |
| `test-multi` | `test123` | approver |
| `test-admin` | `test123` | admin |
| `test-superadmin` | `test123` | superadmin |

## Dev-Server

```bash
python cmp/manage.py runserver
```

Danach erreichbar unter **http://127.0.0.1:8000**.

## Tests

```bash
# Alle Tests, aus dem Repo-Root
python -m pytest

# Einzelnen Test gezielt ausführen
python -m pytest tests/unit/... -k name
```

`pytest.ini` (Repo-Root) setzt `DJANGO_SETTINGS_MODULE=config.settings.testing`
und `pythonpath=cmp` — deshalb funktioniert `python -m pytest` ohne
zusätzliches Setup.

## Lint/CSS

```bash
ruff check
npm run css:build
```

## Launcher/Skripte

```bash
# Interaktiver Dev-Launcher mit Menü:
# Setup / Server / Tests / Migrationen / Seed / Shell / Check / CSS
bash scripts/run.sh
```

```bash
# PG-Rolle `cmp` + DBs cmp_django_dev/cmp_django_test neu anlegen (braucht sudo)
bash scripts/fix_databases.sh
```

## Git/Release

Die Versionsnummer steht in `lucent-hub.yml` (`version: "1.5.0"`). Releases
werden als Tag `vX.Y.Z` markiert, der zugehörige Commit trägt die Message
`release: vX.Y.Z — …`.

## Stolpersteine

| Symptom | Ursache / Lösung |
|---------|-------------------|
| `ModuleNotFoundError: No module named 'config'` | Django-Kommando wurde nicht aus `cmp/` gestartet — entweder ins Verzeichnis `cmp/` wechseln oder den Pfad `cmp/manage.py` verwenden. |
| Keine `.env`-Datei vorhanden | Für die lokale Entwicklung nicht nötig — Dev- und Test-Settings haben ihre Werte fest im Code. `.env.example` ist nur die Vorlage für Produktion. |
| CSS-Build findet Pfade wie `mpp/static/css/input.css` | Altlast aus der Zeit, als das Projekt noch `mpp` hieß — `package.json` wurde an dieser Stelle noch nicht auf `cmp/` umgestellt. |
| `ProgrammingError: relation "..." does not exist` nach Model-Änderung | Die Test-DB `cmp_django_test` läuft mit `keepdb=True` (der User `cmp` hat kein `CREATEDB`-Recht) und wird zwischen Testläufen wiederverwendet. Nach Schema-Änderungen manuell neu aufsetzen: `PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"` und danach `cd cmp && python manage.py migrate --settings=config.settings.testing`. |

---

⟵ [A — Glossar](A-glossar.md) · [📖 Übersicht](README.md) · [C — Einen neuen Service anlegen](C-neuen-service-anlegen.md) ⟶
