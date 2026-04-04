# CLAUDE.md — MPP Django Marketplace Portal

## Was ist das?

**Marketplace Portal (MPP-Django)** ist ein Self-Service-Portal für automatisiertes IT-Service-Provisioning. Benutzer bestellen VMs, Datenbanken und Container aus einem Service-Katalog mit vollem Approval- und Provisioning-Workflow.

- **Backend:** Python 3.12, Django 6.0, PostgreSQL 14+
- **Frontend:** Django Templates + HTMX + DaisyUI (TailwindCSS)
- **Async:** Celery + Redis, Django Channels (WebSocket)
- **Auth:** django-allauth (Session-basiert)
- **Autor:** Tobias Philipp / Lucent Trails
- **Lizenz:** All Rights Reserved

---

## Prioritäten (bei Konflikten)

1. Architektur-Regeln (Clean Architecture, Dependency Rules)
2. Sicherheit & Datenintegrität
3. Korrektheit (keine Bugs)
4. Wartbarkeit & Lesbarkeit
5. Performance

---

## Entscheidungsrichtlinien

- Bevorzuge einfache Lösungen gegenüber komplexen
- Vermeide neue Abhängigkeiten, wenn bestehende Lösungen ausreichen
- Optimiere erst nach funktionaler Korrektheit
- Schreibe Code so, dass er ohne zusätzliche Erklärung verständlich ist

---

## Definition of Done

Eine Aufgabe ist abgeschlossen, wenn:

- Code kompiliert / ausführbar ist
- Tests vorhanden und sinnvoll sind
- Keine Architektur-Regeln verletzt werden
- Keine offensichtlichen Edge Cases fehlen
- Logging und Fehlerbehandlung berücksichtigt sind

---

## Tech-Stack

### Backend
- **Framework:** Django 6.0
- **ORM:** Django ORM (Models, Migrations, QuerySets)
- **Datenbank:** PostgreSQL 14+
- **Auth:** django-allauth (Session-basiert)
- **Migrations:** Django Migrations (integriert)
- **Async:** Celery + Redis
- **Echtzeit:** Django Channels (WebSocket)
- **Testing:** pytest-django, factory_boy
- **Server:** ASGI (Daphne/Uvicorn)
- **Port:** 8000

### Frontend (Server-Side Rendering)
- **Templates:** Django Templates
- **Dynamik:** HTMX (partielle Updates, Formulare)
- **CSS:** TailwindCSS + DaisyUI (Custom Theme "Lucent")
- **Kein:** React, TypeScript, Vite, SPA, REST-API

---

## Architektur (nicht verhandelbar)

Django-adaptierte Clean Architecture mit klarer Schichtentrennung:

### Backend-Struktur
```
mpp/                          # Django-Projekt
├── config/                   # Django Settings & URLs
│   ├── settings/
│   │   ├── base.py          # Gemeinsame Settings
│   │   ├── development.py   # Dev-spezifisch
│   │   ├── testing.py       # Test-spezifisch
│   │   └── production.py    # Prod-spezifisch
│   ├── urls.py              # Root URL-Konfiguration
│   └── wsgi.py / asgi.py
│
├── apps/                     # Django Apps (Feature-Module)
│   ├── accounts/            # Auth, Users, Rollen
│   ├── catalog/             # Service Templates, Parameter
│   ├── orders/              # Bestellungen, Items, Groups
│   ├── approvals/           # Approval-Regeln, Requests
│   ├── provisioning/        # Dispatch, Status, Webhooks
│   ├── cmdb/                # CMDB-Stub, Context, Availability
│   ├── notifications/       # In-App-Benachrichtigungen
│   ├── subscriptions/       # Subscriptions, Changes, Cancellations
│   ├── audit/               # Audit-Logs, DSGVO
│   └── dashboard/           # Admin-Dashboard, Stats
│
├── core/                     # Shared Code
│   ├── domain/              # Enums, Value Objects, Status-Machines
│   ├── mixins.py            # TimeStampedModel, RoleRequiredMixin
│   ├── exceptions.py        # Custom Exceptions
│   └── templatetags/        # Custom Template-Tags
│
├── templates/                # Projektweite Django Templates
│   ├── base.html            # DaisyUI Layout-Skeleton
│   ├── includes/            # Navbar, Sidebar, Messages
│   └── {app}/               # Pro App ein Ordner + partials/
│
├── static/                   # CSS, JS, Images
├── stubs/                    # Stub-Daten (CMDB YAML, GitLab Mock)
└── manage.py
```

### Dependency-Regeln

- `views.py` → `services.py` ✓
- `views.py` → `forms.py` ✓
- `views.py` → `models.py` (read für QuerySets) ✓
- `views.py` → `models.py` (write/create) ✗ (nur über Service)
- `services.py` → `models.py` ✓
- `services.py` → `core/domain/` ✓
- `core/domain/` → keine Django-Abhängigkeit ✓
- `core/` → `apps/` ✗ (keine zirkulären Imports)

---

## Django-spezifische Patterns

### Models
- Jede App hat eigene `models.py` mit Django Models
- JSONB via `django.contrib.postgres.fields.JSONField`
- Abstrakte Base-Models für Timestamps (`created_at`, `updated_at`)

### Views
- Class-Based Views (ListView, CreateView, DetailView, etc.)
- Dünn: max 15 Zeilen pro Methode
- View → Form → Service → Model → Template
- HTMX-Partials via `request.htmx` (django-htmx)
- Rollen-Mixins für Zugriffskontrolle

### Forms
- Django Forms für Input-Validierung
- ModelForms für CRUD-Operationen
- Template-Schema-Validierung in custom clean()

### Services
- Business-Logik in `apps/*/services.py`, NICHT in Views oder Models
- Services sind Framework-agnostisch (kein Request/Response)
- Statische Methoden oder Klassen

### Migrations
- Django Migrations (automatisch generiert, manuell reviewt)
- Keine Daten-Migrationen ohne Freigabe

---

## Benutzerrollen

| Rolle | Berechtigungen |
|-------|---------------|
| requester | Bestellungen erstellen/einsehen, eigene Subscriptions |
| approver | Bestellungen genehmigen/ablehnen, Approval-Queue |
| admin | Katalog verwalten, Regeln, Audit, DSGVO |
| superadmin | Systemweite Administration, Anonymisierung |

### Stub-Benutzer (Development)
- `test-requester` / `test123` (requester)
- `test-approver` / `test123` (approver)
- `test-admin` / `test123` (admin)
- `test-multi` / `test123` (approver — kann auch bestellen)
- `test-superadmin` / `test123` (superadmin)

---

## Befehle

### Backend
```bash
# Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Django Setup
python manage.py migrate
python manage.py seed  # Custom Management Command
python manage.py runserver 8000

# Tests
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

### Tailwind/DaisyUI Build
```bash
npm install                    # Tailwind + DaisyUI
npx tailwindcss -o static/css/output.css --watch  # CSS Build
```

### Dev-Launcher
```bash
bash scripts/mpp.sh  # Interaktiver Launcher
```

---

## Anweisungen für Claude

- Schreibe keine kompletten Dateien neu, es sei denn, es ist ausdrücklich notwendig
- Bevorzuge kleine, inkrementelle Änderungen
- Erkläre alle nicht offensichtlichen Entscheidungen
- Stelle Rückfragen, wenn Anforderungen unklar sind

---

## Design-Entscheidungen (nicht ändern)

- Django 6.0 statt Flask (Neukonzeption)
- Django ORM statt SQLAlchemy
- Django Migrations statt Alembic
- Django Templates + HTMX statt React SPA
- DaisyUI (TailwindCSS) statt eigenes CSS
- django-allauth statt JWT-Eigenbau
- Django Channels (WebSocket) statt SSE
- Celery + Redis für async Provisioning
- Django Admin als Haupt-Admin-Tool
- pytest-django statt unittest
- Kein API-First-Ansatz (kein DRF, kein REST)
- Prozesse bleiben extern (OpenTofu via GitLab)

---

## Verbote (NICHT tun)

- Keine destruktiven Commands ohne Nachfrage
- Keine Dependency-Änderungen ohne Bestätigung
- Kein DB-Schema-Upgrade ohne Freigabe
- Kein Architekturbruch
- Keine Business-Logik in Views, Forms oder Models
- Kein raw SQL ohne zwingende Performance-Gründe

---

## Vor jeder Änderung prüfen

1. Architektur-Regeln eingehalten?
2. Frontend + Backend betroffen?
3. Konstanten statt Magic Numbers?
4. Test vorhanden?
5. Datei < 200 Zeilen?
6. API synchron?

---

## Test-Richtlinien

- Teste Verhalten, nicht Implementierungsdetails
- Decke Edge Cases ab
- Mocke externe Abhängigkeiten (CMDB, GitLab)
- Bevorzuge kleine, fokussierte Tests
- factory_boy für Test-Fixtures
- pytest-django für DB-Tests
- Fixture-Scope: `function` (komplette Isolation)

---

## Bekannte Constraints

- Django Channels erfordert ASGI + Redis
- Celery erfordert Redis als Broker
- ACCOUNT_SIGNUP_ENABLED = False (nur Admin erstellt User)
- DEBUG=True + PRODUCTION → FATAL
- GITLAB_CLIENT Setting steuert Stub/Live-Modus
- CMDB_MODE=stub für Entwicklung
