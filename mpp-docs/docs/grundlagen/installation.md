# Installation

## Voraussetzungen

| Software | Version | Zweck |
|----------|---------|-------|
| Python | 3.12+ | Backend |
| PostgreSQL | 14+ | Datenbank |
| Node.js | 20+ | Tailwind CSS Build |
| npm | 10+ | Paketmanager Frontend |

## Automatisches Setup

```bash
bash scripts/run.sh
# Menüpunkt 1 wählen → Setup läuft automatisch
```

Das Setup erledigt:

1. Virtual Environment erstellen
2. Python-Abhängigkeiten installieren
3. Node-Pakete installieren (Tailwind + DaisyUI)
4. CSS bauen
5. PostgreSQL-Datenbanken anlegen
6. Migrationen ausführen
7. Demo-Daten laden

## Manuelles Setup

### 1. Virtual Environment

```bash
cd lucent-app-mpp-TDD-Django
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
```

### 2. PostgreSQL

```bash
# User und Datenbanken anlegen
sudo -u postgres psql -c "CREATE USER mpp WITH PASSWORD 'mpp' CREATEDB;"
sudo -u postgres createdb mpp_dev -O mpp
sudo -u postgres createdb mpp_test -O mpp
```

### 3. Django einrichten

```bash
cd mpp
python manage.py migrate
python manage.py seed
```

### 4. Frontend (Tailwind CSS)

```bash
npm install
npm run css:build
```

### 5. Verifizierung

```bash
# Django Check
cd mpp && python manage.py check
# → System check identified no issues.

# Tests
python -m pytest tests/ -v
# → 228+ passed
```

## Abhängigkeiten

### Python (requirements/base.txt)

| Paket | Version | Zweck |
|-------|---------|-------|
| Django | 6.0 | Web-Framework |
| django-allauth | 65+ | Authentifizierung |
| django-htmx | 1.21+ | HTMX-Middleware |
| psycopg[binary] | 3.2+ | PostgreSQL-Treiber |
| celery | 5.4+ | Task Queue |
| redis | 5.0+ | Celery Broker |
| PyYAML | 6.0+ | CMDB Stub-Daten |

### Python (requirements/dev.txt)

| Paket | Version | Zweck |
|-------|---------|-------|
| pytest | 8.3+ | Test-Framework |
| pytest-django | 4.9+ | Django-Integration |
| factory-boy | 3.3+ | Test-Factories |
| ruff | 0.8+ | Linter |

### Node.js (package.json)

| Paket | Version | Zweck |
|-------|---------|-------|
| tailwindcss | 4.0+ | Utility CSS |
| daisyui | 5.0+ | UI-Komponenten |
