# Troubleshooting

## Häufige Probleme

### PostgreSQL nicht erreichbar

**Symptom:** `connection to server on socket ... failed`

```bash
# Status prüfen
pg_isready -h localhost -p 5432

# Service starten (Ubuntu/Debian)
sudo systemctl start postgresql

# Service starten (Fedora/RHEL)
sudo systemctl start postgresql
```

### Datenbank existiert nicht

**Symptom:** `FATAL: database "cmp_django_dev" does not exist`

```bash
# DB anlegen (braucht superuser)
sudo -u postgres createdb cmp_django_dev -O cmp
sudo -u postgres createdb cmp_django_test -O cmp
```

Falls der User `cmp` nicht existiert:

```bash
sudo -u postgres psql -c "CREATE USER cmp WITH PASSWORD 'cmp' CREATEDB;"
```

### Migrationen fehlgeschlagen

**Symptom:** `relation "..." already exists` oder `column "..." does not exist`

```bash
# Test-DB zurücksetzen
PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd cmp && DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py migrate

# Dev-DB zurücksetzen
PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_dev -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd cmp && python manage.py migrate && python manage.py seed
```

### Port 8000 belegt

**Symptom:** `Error: That port is already in use.`

```bash
# Prozess finden
lsof -i :8000

# Prozess beenden
kill -9 $(lsof -t -i :8000)

# Oder anderen Port nutzen
python manage.py runserver 8001
```

### Node.js Version zu alt

**Symptom:** Tailwind CSS Build schlägt fehl

```bash
# Version prüfen
node --version
# TailwindCSS v4 braucht Node >= 20

# nvm verwenden
nvm install 22
nvm use 22
npm run css:build
```

### Tests schlagen fehl nach Schema-Änderung

**Symptom:** `ProgrammingError: relation "..." does not exist`

Die Test-DB nutzt `keepdb=True`. Nach Model-Änderungen:

```bash
# Migrationen auf Test-DB anwenden
cd cmp
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py migrate
```

### Virtual Environment Probleme

**Symptom:** `ModuleNotFoundError`

```bash
# venv komplett neu erstellen
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
```

### Celery-Fehler im Development

**Symptom:** `redis.exceptions.ConnectionError`

Im Development-Modus ist Redis nicht erforderlich. Prüfe:

```python
# cmp/config/settings/development.py
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

Falls diese Einstellung fehlt, werden Tasks asynchron geschickt und brauchen Redis.

### HTMX funktioniert nicht

**Symptom:** Suche/Filter laden nicht dynamisch

Prüfe:
1. `cmp/static/js/htmx.min.js` existiert
2. `django_htmx` in INSTALLED_APPS
3. `HtmxMiddleware` in MIDDLEWARE
4. `<script src="{% static 'js/htmx.min.js' %}" defer></script>` in base.html

### Django Admin nicht erreichbar

**Symptom:** 403 Forbidden

Nur User mit `is_staff=True` haben Zugang:
- `test-admin` (is_staff=True)
- `test-superadmin` (is_staff=True, is_superuser=True)

## Nützliche Befehle

```bash
# Django Check (findet Konfigurationsprobleme)
cd cmp && python manage.py check

# Alle Migrationen anzeigen
python manage.py showmigrations

# Django Shell (interaktiv)
python manage.py shell

# Alle registrierten URLs anzeigen
python manage.py show_urls  # (braucht django-extensions)

# Datenbank-Inhalt prüfen
PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_dev -c "SELECT username, role FROM users;"
```
