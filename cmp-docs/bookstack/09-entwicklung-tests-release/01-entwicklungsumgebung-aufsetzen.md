# Entwicklungsumgebung aufsetzen

Diese Seite beschreibt, wie eine lokale CMP-Entwicklungsumgebung von Null an
lauffähig wird: Voraussetzungen, Setup-Weg, Server-Start und die bekannten
Stolperfallen.

## 1. Ziel des Kapitels

Wer das Repository frisch auscheckt, soll ohne Rätselraten zu einem
laufenden Dev-Server kommen — mit den echten Befehlen, nicht mit
angenommenen.

## 2. Voraussetzungen

| Werkzeug | Version im Projekt | Prüfbefehl |
|---|---|---|
| Python | 3.12 (`venv/bin/python3 --version`) | `python3 --version` |
| PostgreSQL | erreichbar auf `localhost:5432` | `pg_isready -h localhost -p 5432` |
| Node.js | optional, für Tailwind-CSS-Build | `node --version` |
| Redis | optional — ohne Redis läuft Celery im `EAGER`-Modus | `redis-cli ping` |

Python bleibt bewusst auf 3.12, weil das Ziel-Betriebssystem (AlmaLinux 9)
kein 3.14 paketiert (siehe Kapitel 11, ADR-0001-Umfeld).

## 3. Zwei Skripte namens „run.sh" — nicht verwechseln

Im Repository liegen **zwei** Skripte mit demselben Dateinamen:

| Pfad | Zweck |
|---|---|
| `scripts/run.sh` | interaktiver Dev-Launcher (Menü 1–8): Setup, Server, Tests, Migrationen, Seed, Shell, Check, CSS-Build |
| `run.sh` (Projektwurzel) | Kommandozeilen-Werkzeug für Betrieb/Release: `serve`, `appimage-build`, `docs-appimage`, `docs-zip`, `release` (`run.sh:400-409`) |

Für die tägliche Entwicklungsarbeit ist `scripts/run.sh` gemeint. Der
Root-`run.sh` startet den Server ebenfalls (`cmd_serve`, `run.sh:117-126`,
`python manage.py runserver 8000`), wird aber vor allem für Release-Artefakte
gebraucht (Kapitel 8).

## 4. Setup über den Dev-Launcher

```bash
bash scripts/run.sh
# → Taste 1: Vollständiges Setup
```

Menüpunkt 1 (`do_setup`, `scripts/run.sh:164-247`) führt real aus:

1. `python3 -m venv venv`, falls `venv/` fehlt
2. `pip install -q -r requirements/dev.txt`
3. `npm install` + `npm run css:build`, falls `npm` gefunden wird (sonst Warnung, kein Abbruch)
4. Prüft `pg_isready`, legt bei Bedarf `cmp_django_dev` und `cmp_django_test` per `createdb` an
5. `python manage.py migrate --no-input`
6. Setzt `Site` (id=1) auf `localhost:8000`
7. `python manage.py seed`

`requirements/dev.txt` zieht `requirements/base.txt` mit (Django, allauth,
django-htmx, psycopg, django-environ, celery, redis) und ergänzt
`pytest`, `pytest-django`, `factory-boy`, `ruff`. Für Produktion existiert
separat `requirements/production.txt` (Base + `gunicorn`); das gebündelte
`requirements.txt` in der Projektwurzel ist ein Freeze-Snapshot für den
AppImage-Bau (Kapitel 8), nicht der Weg für lokale Entwicklung.

## 5. Bekannte Stolperfalle: Tailwind-CSS-Build zeigt auf einen alten Pfad

`package.json` (Projektwurzel) wurde beim Rename MPP → CloudMan Portal
(v1.3.0) nicht mitgezogen: `css:build`/`css:watch` rufen Tailwind noch mit
`mpp/static/css/...` auf, das Verzeichnis heißt aber `cmp/static/css/`.
Nachgestellt am 2026-07-22: `npm run css:build` bricht mit
`Specified input file './mpp/static/css/input.css' does not exist.` ab.
`scripts/run.sh` unterdrückt den Fehler (`2>/dev/null`) und meldet trotzdem
„Tailwind CSS gebaut" — das vorhandene `cmp/static/css/output.css` bleibt
also der alte Stand, bis der Pfad in `package.json` korrigiert oder
manuell mit dem richtigen Pfad gebaut wird:

```bash
npx tailwindcss -i cmp/static/css/input.css -o cmp/static/css/output.css
```

Dieser Aufruf wurde für diese Seite real ausgeführt und läuft durch.

## 6. Server manuell starten

```bash
source venv/bin/activate
cd cmp && python manage.py runserver 8000
```

Im Browser: `http://localhost:8000`.

## 7. Demo-Zugänge

Aus `manage.py seed` (Quelle: `cmp-docs/docs/grundlagen/schnellstart.md`):

| User | Passwort | Rolle |
|---|---|---|
| test-requester | test123 | requester |
| test-approver | test123 | approver |
| test-admin | test123 | admin |
| test-multi | test123 | approver |
| test-superadmin | test123 | superadmin |

Reine Demo-Zugänge für die lokale Seed-Datenbank, keine echten Zugangsdaten.

## 8. Probe: Setup erfolgreich?

```bash
venv/bin/python3 -m pytest --collect-only -q
```

Erwartete letzte Zeile (nachgemessen am 2026-07-22): `330 tests collected`.
Details zur Testzahl in Kapitel 9.3.

## 9. Häufige Fehler

| Symptom | Ursache | Prüfbefehl |
|---|---|---|
| `ERROR: venv not found` beim Root-`run.sh serve` | `venv/` fehlt noch | zuerst `scripts/run.sh` → Setup |
| `PostgreSQL nicht erreichbar` im Statusblock | Dienst läuft nicht | `pg_isready -h localhost -p 5432` |
| `npm run css:build` bricht ab | veralteter `mpp/`-Pfad in `package.json` (siehe Abschnitt 5) | `npx tailwindcss -i cmp/static/css/input.css -o cmp/static/css/output.css` |
| Redis-Warnung im Statusblock | Redis nicht installiert/gestartet | unkritisch für Dev — Celery läuft `EAGER` |

## 10. Zusammenfassung

`scripts/run.sh` (nicht der gleichnamige Root-`run.sh`) ist der reguläre
Weg in eine lauffähige Dev-Umgebung: venv, `requirements/dev.txt`,
PostgreSQL-Datenbanken, Migrationen, Seed — alles in einem Menüpunkt. Eine
reale, verifizierte Lücke bleibt der Tailwind-Build, der aktuell einen
Pfad aus der Zeit vor dem CMP-Rename referenziert.

> Quelle: `scripts/run.sh:164-301`, `run.sh:117-126,400-409`, `requirements/base.txt`, `requirements/dev.txt`, `requirements/production.txt`, `package.json`, `cmp-docs/docs/grundlagen/schnellstart.md` — am Code geprüft 2026-07-22
