# Marketplace Portal (MPP) — Django Edition

Self-Service-Portal für automatisiertes IT-Service-Provisioning mit Django, HTMX & DaisyUI.

## Features

| Feature | Beschreibung |
|---------|-------------|
| Service-Katalog | Templates für VMs, DBs, Container mit parametrischen Formularen |
| Shop-Wizard | Mehrstufiger Bestellprozess mit kontextabhängigen Optionen |
| Bestellungen | Draft → Validiert → Submitted → Provisioning → Done |
| Groups & Quantity | Mengenbestellung mit Per-Instance-Parametern |
| Approval-Workflow | Regelbasierte Genehmigung durch Approver |
| Subscriptions | Laufende Services verwalten, ändern, kündigen |
| Notifications | In-App-Benachrichtigungen (WebSocket) |
| Dashboard | Admin-Übersicht mit Statistiken |
| DSGVO | Audit-Logs, Anonymisierung |
| Rollen | requester, approver, admin, superadmin |

## Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Backend | Python 3.12, Django 6.0 |
| Frontend | Django Templates + HTMX |
| CSS | TailwindCSS + DaisyUI |
| Auth | django-allauth (Session-basiert) |
| Async | Celery + Redis |
| Echtzeit | Django Channels (WebSocket) |
| Datenbank | PostgreSQL 14+ |
| Tests | pytest-django, factory_boy |
| Admin | Django Admin |

## Quick Start

```bash
bash scripts/mpp.sh
```

## Demo-Zugänge

| User | Passwort | Rolle |
|------|----------|-------|
| test-requester | test123 | requester |
| test-approver | test123 | approver |
| test-admin | test123 | admin |
| test-multi | test123 | approver (kann auch bestellen) |
| test-superadmin | test123 | superadmin |

## Projektstruktur

```
mpp/                    # Django-Projekt
├── config/             # Settings, URLs, ASGI, Celery
├── apps/               # 10 Django Apps (Feature-Module)
│   └── {app}/
│       ├── models.py   # Django Models
│       ├── services.py # Business-Logik
│       ├── views.py    # Class-Based Views (dünn)
│       ├── forms.py    # Input-Validierung
│       ├── admin.py    # Django Admin
│       └── urls.py
├── core/               # Shared Domain, Mixins, Exceptions
├── templates/          # Django Templates + DaisyUI
│   └── {app}/
│       └── partials/   # HTMX-Partials
├── static/             # CSS (Tailwind), JS (HTMX)
├── stubs/              # CMDB YAML, GitLab Mock
└── manage.py

tests/                  # pytest-django
├── unit/
├── integration/
└── e2e/
```

## Tests

```bash
pytest tests/ -v
```

## Lizenz

All Rights Reserved — Tobias Philipp / Lucent Trails
