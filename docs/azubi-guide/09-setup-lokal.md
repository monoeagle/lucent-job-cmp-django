# 08 — Setup lokal

> **In diesem Kapitel:** Du bringst CMP auf deiner eigenen Maschine zum Laufen —
> vom leeren Checkout bis zum Login im Browser. Du lernst zwei Wege kennen: den
> manuellen (Schritt für Schritt, gut zum Verstehen) und den komfortablen
> (ein Skript, das alles für dich erledigt).
>
> **Das lernst du:**
> - Welche Voraussetzungen du brauchst (Python, PostgreSQL)
> - Wie du das Projekt manuell aufsetzt — und wie der Launcher `run.sh` das automatisiert
> - Wie du Demo-Daten lädst und dich einloggst
> - Wie du die Tests ausführst
> - Die typischen Stolpersteine beim ersten Setup
>
> **Voraussetzung:** [08 — Frontend: HTMX & DaisyUI](08-frontend-htmx-daisyui.md)
> (hilfreich für den CSS-Build-Schritt weiter unten, aber kein Hard-Blocker).

---

## Plattform: Linux (oder macOS)

CMP wird auf **Linux** entwickelt und betrieben — der Launcher `scripts/run.sh`
ist ein Bash-Skript, die Deployment-Doku richtet sich an Rocky/AlmaLinux 9. Die
Befehle in diesem Kapitel sind entsprechend für **bash** geschrieben und
funktionieren so auch auf macOS.

💡 **Merke:** Windows taugt zum *Lesen und Reviewen* des Codes (z. B. mit VS Code),
aber nicht als primäre Entwicklungsumgebung — `run.sh` läuft dort nicht nativ,
und PostgreSQL lokal aufzusetzen ist unter Linux deutlich unkomplizierter. Wenn
du auf Windows sitzt, nutze WSL2 mit einer Linux-Distribution.

---

## Voraussetzungen

| Werkzeug | Version | Wofür |
|----------|---------|-------|
| Python | 3.12+ | Django 6.0 verlangt mindestens 3.12 |
| PostgreSQL | lokal erreichbar | Einzige unterstützte Datenbank (dev **und** test) |
| Node.js + npm | aktuelle LTS | Nur für den CSS-Build (Tailwind + DaisyUI), siehe [Kapitel 08](08-frontend-htmx-daisyui.md) |
| Redis | optional | Dev nutzt Celery im **EAGER**-Modus — kein Redis nötig |

🔍 **Im Code nachsehen:** Die exakten Python-Pakete stehen in
[`requirements/base.txt`](../../requirements/base.txt) (`Django>=6.0,<6.1`,
`django-allauth`, `celery`, `redis`, …) und
[`requirements/dev.txt`](../../requirements/dev.txt) (zusätzlich `pytest`,
`pytest-django`, `factory-boy`, `ruff`).

---

## Weg A — Manuelles Setup

Der ausführliche, transparente Weg. Gut geeignet, wenn du verstehen willst,
was tatsächlich passiert.

```bash
# 1. Virtuelle Umgebung anlegen
python3.12 -m venv venv

# 2. Abhängigkeiten installieren
venv/bin/pip install -r requirements/dev.txt

# 3. PostgreSQL lokal bereitstellen (Redis ist optional, siehe oben)
#    Erwartet werden die Datenbanken cmp_django_dev und cmp_django_test,
#    Rolle "cmp" mit Passwort "cmp" (siehe cmp/config/settings/base.py)

# 4. Migrationen anwenden
venv/bin/python cmp/manage.py migrate

# 5. Dev-Server starten
venv/bin/python cmp/manage.py runserver
```

Danach ist das Portal unter **http://127.0.0.1:8000** erreichbar.

> **Kleines Detail am Rande:** Eine `.env`-Datei brauchst du lokal **nicht**.
> Die dev- und test-Settings haben ihre Werte (DB-Zugang, `SECRET_KEY`, …)
> fest im Code hinterlegt. `.env.example` im Repo-Root ist die Vorlage für die
> **Produktions**-Umgebung, nicht für die lokale Entwicklung.

### Demo-Daten laden

Ohne Demo-Daten ist das Portal leer — kein Katalog, keine User außer dir
selbst (falls du einen Superuser angelegt hast). Der Seed-Befehl füllt beides:

```bash
venv/bin/python cmp/manage.py seed
```

Danach kannst du dich mit fünf Demo-Logins anmelden — alle mit demselben
Passwort. Details zu den Rollen (inkl. `is_staff`/`is_superuser`) stehen in
[Kapitel 04](04-rollen-und-rechte.md#demo-zugänge-zum-ausprobieren):

| Login | Passwort | Rolle |
|-------|----------|-------|
| `test-requester` | `test123` | requester |
| `test-approver` | `test123` | approver |
| `test-multi` | `test123` | approver |
| `test-admin` | `test123` | admin |
| `test-superadmin` | `test123` | superadmin |

🔍 **Im Code nachsehen:** Der Befehl steckt in
[`cmp/apps/accounts/management/commands/seed.py`](../../cmp/apps/accounts/management/commands/seed.py)
und ruft u. a. `AccountService.seed_stub_users()` und
`CatalogService.seed_templates()` auf. Beim zweiten Aufruf legt er keine
doppelten Demo-Bestellungen mehr an — nur fehlende User/Templates werden
nachgezogen.

---

## Weg B — Der interaktive Launcher `run.sh`

Für den Alltag gibt es ein Bash-Menü, das die manuellen Schritte oben (und
mehr) automatisiert:

```bash
bash scripts/run.sh
```

Der Menüpunkt **„Vollständiges Setup"** macht in einem Rutsch:

1. `venv` anlegen (falls nicht vorhanden) + `pip install -r requirements/dev.txt`
2. `npm install` + `npm run css:build` (Tailwind/DaisyUI-CSS bauen)
3. PostgreSQL-Datenbanken `cmp_django_dev` und `cmp_django_test` anlegen (falls nicht vorhanden)
4. `migrate`
5. `seed` (Demo-Daten, siehe oben)

Danach bringt dich das Menü direkt zu den weiteren Aktionen:

| Menüpunkt | Macht |
|-----------|-------|
| Dev-Server starten | `runserver` auf Port 8000, zeigt dir die Demo-Logins an |
| Tests ausführen | Alle / Unit / Integration / E2E, wahlweise |
| Migrationen | `migrate`, `makemigrations`, `showmigrations` |
| Demo-Daten laden | Ruft `seed` separat auf |
| Django Shell | `manage.py shell` |
| Django System Check | `manage.py check` |
| Tailwind CSS Build | Einmalig oder im Watch-Modus |

💡 **Merke:** `run.sh` zeigt beim Start außerdem einen **Status-Check** (Python-
Version, venv, Django, PostgreSQL-Erreichbarkeit, Redis, Node.js, gebautes CSS,
registrierte Tests, laufender Dev-Server) — praktisch, um schnell zu sehen,
was noch fehlt.

---

## Tests ausführen

```bash
python -m pytest
```

`pytest.ini` im Repo-Root sorgt dafür, dass alles automatisch passt:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
pythonpath = cmp
testpaths = tests
```

Die Tests laufen gegen `config.settings.testing` und damit gegen die
**eigene** Datenbank `cmp_django_test` — deine Entwicklungsdaten in
`cmp_django_dev` bleiben unangetastet.

---

## Stolpersteine & Troubleshooting

Die meisten Probleme beim ersten Setup wiederholen sich — hier die typischen
Symptome mit Ursache und Fix:

| Symptom | Ursache | Fix |
|---------|---------|-----|
| `connection to server on socket ... failed` | PostgreSQL läuft nicht oder ist nicht erreichbar | `pg_isready -h localhost -p 5432` prüfen, dann `sudo systemctl start postgresql` |
| `FATAL: database "cmp_django_dev" does not exist` | Die Datenbank wurde noch nicht angelegt | `sudo -u postgres createdb cmp_django_dev -O cmp` (analog für `cmp_django_test`) |
| `relation "..." already exists` bei `migrate` | Schema und Migrationshistorie sind inkonsistent (z. B. DB manuell verändert) | Schema zurücksetzen: `psql -h localhost -U cmp -d cmp_django_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`, danach erneut `migrate` |
| `Error: That port is already in use.` | Es läuft noch ein Dev-Server auf Port 8000 (z. B. in einem vergessenen Terminal) | `kill -9 $(lsof -t -i :8000)` oder `manage.py runserver 8001` |
| Tailwind-CSS-Build (`npm run css:build`) schlägt fehl | Node.js ist zu alt — TailwindCSS v4 braucht **Node ≥ 20** | `node --version` prüfen, ggf. mit `nvm install 22 && nvm use 22` aktualisieren |
| `ModuleNotFoundError: No module named 'config'` | Django-Kommando wurde nicht aus `cmp/` heraus gestartet | Aus `cmp/` heraus starten oder mit Pfad `cmp/manage.py` aufrufen (Details siehe unten) |
| `redis.exceptions.ConnectionError` | Celery versucht tatsächlich, mit Redis zu sprechen | Prüfen, ob in `development.py`/`testing.py` `CELERY_TASK_ALWAYS_EAGER = True` gesetzt ist — im Dev-/Test-Betrieb ist kein Redis nötig |
| HTMX-Interaktionen (Suche, Filter) laden nicht dynamisch | `htmx.min.js` fehlt oder `django_htmx` ist nicht eingebunden | Prüfen: `cmp/static/js/htmx.min.js` vorhanden, `"django_htmx"` in `INSTALLED_APPS`, `HtmxMiddleware` in `MIDDLEWARE` |
| Django-Admin liefert `403 Forbidden` | Der eingeloggte User hat `is_staff=False` | Mit `test-admin` oder `test-superadmin` einloggen (siehe Demo-Zugänge oben) |

> ⚠️ **Achtung:** Django-Kommandos musst du aus dem Verzeichnis `cmp/` heraus
> starten (oder mit dem Pfad `cmp/manage.py` aufrufen), sonst bekommst du
> `ModuleNotFoundError: No module named 'config'`. Der Grund: `cmp/` ist der
> Import-Root des Projekts, und das Settings-Paket heißt `config` — Python
> findet es nur, wenn `cmp/` im Suchpfad liegt.

🔍 **Im Code nachsehen:** Genau das übernimmt `pytest.ini` für dich mit
`pythonpath = cmp` — deshalb funktioniert `python -m pytest` aus dem Repo-Root
heraus problemlos, während `manage.py`-Befehle das nicht automatisch tun.

> ⚠️ **Achtung — die keepdb-Falle:** Der Test-DB-User `cmp` hat **kein**
> `CREATEDB`-Recht — deshalb nutzt `tests/conftest.py` `keepdb=True`
> (`setup_databases(..., keepdb=True)`), und `cmp_django_test` wird zwischen
> Testläufen **wiederverwendet** statt neu erzeugt. Das ist normalerweise
> praktisch (schnellere Testläufe), wird aber zur Falle, sobald du ein Model
> änderst: die alte Test-DB kennt das neue Schema nicht, und Tests schlagen
> plötzlich mit `ProgrammingError: relation "..." does not exist` fehl —
> obwohl dein Code korrekt ist. Fix:
>
> ```bash
> cd cmp && DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py migrate
> ```
>
> Reicht das nicht (z. B. bei entfernten Feldern), hilft nur ein harter Reset
> der Test-DB:
>
> ```bash
> PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
> cd cmp && DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py migrate
> ```

🔍 **Im Code nachsehen:** `tests/conftest.py` (`django_db_setup`-Fixture).

Ein weiterer, kleinerer Stolperstein beim CSS-Build:

> ⚠️ **Achtung:** In `package.json` können dir noch Pfade mit `mpp/` statt
> `cmp/` auffallen (`mpp/static/css/input.css` u. ä.) — eine Altlast aus der
> Zeit, als das Projekt noch `mpp` hieß. Mehr dazu und wie der CSS-Build im
> Detail funktioniert, steht in [Kapitel 08](08-frontend-htmx-daisyui.md).

Falls bei dir mehrere PostgreSQL-Rollen/Datenbanken durcheinandergeraten sind
(z. B. nach einem kaputten lokalen Setup), gibt es außerdem
[`scripts/fix_databases.sh`](../../scripts/fix_databases.sh) — legt die Rolle
`cmp` sowie `cmp_django_dev`/`cmp_django_test` neu an, migriert und seedet sie.
Das Skript braucht `sudo` (PostgreSQL-Superuser-Operationen) und ist eher ein
Reparatur-Werkzeug für den Notfall als Teil des normalen Setup-Wegs.

---

## Vertiefung für Entwickler

<details>
<summary><b>Die vier Settings-Module</b></summary>

CMP hat **kein** einzelnes `settings.py` — stattdessen vier Module unter
`cmp/config/settings/`, die alle von einer gemeinsamen Basis erben:

| Modul | Erbt von | `DEBUG` | Datenbank | Celery | Besonderheit |
|-------|----------|---------|-----------|--------|--------------|
| `base.py` | — | (nicht gesetzt) | `cmp_django_dev` (Default) | `CELERY_TASK_ALWAYS_EAGER = False` | Gemeinsame Basis: `INSTALLED_APPS`, `AUTH_USER_MODEL`, allauth-Konfiguration, Templates |
| `development.py` | `base` | `True` | (übernimmt Basis) | `True` (eager) | `ALLOWED_HOSTS = ["*"]`, fest hinterlegter `SECRET_KEY` — nur für lokale Entwicklung |
| `testing.py` | `base` | `False` | `cmp_django_test` | `True` (eager) | `MD5PasswordHasher` statt des echten Hashers, damit Tests schneller laufen |
| `production.py` | `base` | env-abhängig (Default `False`) | über `DATABASE_URL` (env-basiert) | `False` (echter Redis-Broker) | **Alles** sicherheitsrelevante kommt über `django-environ` aus der Umgebung — kein Wert ist hartkodiert. Fehlt `SECRET_KEY`, startet die App gar nicht erst. |

Welches Modul aktiv ist, entscheidet die Umgebungsvariable
`DJANGO_SETTINGS_MODULE`. Für `manage.py runserver` lokal ist das per Default
`config.settings.development`, für Tests erzwingt `pytest.ini` explizit
`config.settings.testing`, und auf der VM setzt systemd
`config.settings.production` (siehe `docs/deployment/vm-installation.md`).

💡 **Merke:** `development.py` und `testing.py` sind bewusst **eager** —
Celery-Tasks laufen synchron im selben Prozess, ohne Redis oder Worker. Das
macht das lokale Arbeiten und Testen einfach, bedeutet aber auch: Nebenläufigkeits-
und Timing-Effekte aus dem echten Async-Betrieb (siehe
[Kapitel 07](07-async-und-provisioning.md)) siehst du hier nie.

</details>

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Die vier Settings-Module | `cmp/config/settings/base.py`, `development.py`, `testing.py`, `production.py` |
| Der interaktive Launcher | `scripts/run.sh` |
| Der Seed-Befehl | `cmp/apps/accounts/management/commands/seed.py` |
| Test-Konfiguration | `pytest.ini` (Repo-Root) |
| Die `keepdb`-Fixture für die Test-DB | `tests/conftest.py` |
| Python-Abhängigkeiten | `requirements/base.txt`, `requirements/dev.txt` |
| Produktions-Umgebungsvariablen (Vorlage) | `.env.example` (Repo-Root) |
| DB-Reparatur-Skript (Notfall) | `scripts/fix_databases.sh` |

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Warum brauchst du für die lokale Entwicklung keine `.env`-Datei — wo sitzen
   die Werte stattdessen?
2. Du rufst `python manage.py migrate` direkt aus dem Repo-Root auf und
   bekommst `ModuleNotFoundError: No module named 'config'`. Was ist der
   Fehler, und wie behebst du ihn?
3. Warum brauchst du für dev und test kein laufendes Redis?

<details>
<summary>Antworten anzeigen</summary>

1. `development.py` und `testing.py` haben ihre Werte (DB-Zugang,
   `SECRET_KEY`, …) fest im Code stehen. Eine `.env`-Datei ist nur für
   `production.py` relevant, wo alles env-basiert über `django-environ` kommt.
2. Django-Kommandos müssen aus `cmp/` heraus laufen (bzw. mit dem Pfad
   `cmp/manage.py`), weil `cmp/` der Import-Root ist und das Settings-Paket
   `config` sonst nicht gefunden wird.
3. Weil in beiden Settings-Modulen `CELERY_TASK_ALWAYS_EAGER = True` gesetzt
   ist — Celery-Tasks laufen synchron im selben Prozess statt über einen
   Redis-Broker an einen Worker.

</details>

---

⟵ [08 — Frontend: HTMX & DaisyUI](08-frontend-htmx-daisyui.md) · [📖 Übersicht](README.md) · [10 — So arbeiten wir](10-so-arbeiten-wir.md) ⟶
