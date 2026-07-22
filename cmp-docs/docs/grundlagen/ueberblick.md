# Überblick

Self-Service-Portal für automatisiertes IT-Service-Provisioning mit Django, HTMX und DaisyUI.

## Was ist CMP?

Das **CloudMan Portal** ermöglicht Benutzern, IT-Services (VMs, Datenbanken, Container) aus einem Katalog zu bestellen. Ein regelbasierter Approval-Workflow steuert die Genehmigung, und ein Provisioning-Engine (Celery + GitLab) erstellt die Ressourcen automatisch.

## Features

| Feature | Beschreibung |
|---------|-------------|
| Service-Katalog | Templates mit parametrischen JSON-Schemas, Suche und Filter |
| Bestellwizard | Dynamische Formulare aus Template-Parametern, HTMX-basiert |
| Order-Lifecycle | draft → validated → submitted → approved → provisioning → done |
| Mengenbestellungen | OrderItemGroups mit Quantity und Shared Parameters |
| Approval-Workflow | Regelbasierte Genehmigung durch Approver-Rolle |
| Provisioning | Async via Celery, GitLab-Pipeline-Trigger (Stub/Live) |
| Subscriptions | Laufende Services verwalten und kündigen |
| Notifications | In-App-Benachrichtigungen |
| Audit-Logs | DSGVO-konform, Anonymisierung möglich |
| CMDB-Integration | Stub-basiert (YAML), Location/Network/Tenant-Context |
| Rollen-System | requester, approver, admin, superadmin |
| Django Admin | Katalog-, Regel- und User-Verwaltung |
| Dashboard | Statistiken und Übersicht |

## Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Backend | Python 3.12, Django 6.0 |
| Frontend | Django Templates + HTMX |
| CSS | TailwindCSS + DaisyUI (Theme "Lucent") |
| Auth | django-allauth (Session-basiert) |
| Async | Celery + Redis |
| Datenbank | PostgreSQL 14+ (Django ORM) |
| Testing | pytest-django, factory_boy |
| Server | ASGI (Daphne/Uvicorn) |

## Kennzahlen

| Metrik | Wert |
|--------|------|
| Django Apps | 10 |
| Datenbank-Tabellen | 15 |
| Services | 10 |
| Tests | 347 |
| TDD-Phasen | B0–B9 |

## Schnellstart

```bash
bash scripts/run.sh
# → Menüpunkt 1: Vollständiges Setup
# → Menüpunkt 2: Dev-Server starten
# → http://localhost:8000
```

Login: `test-requester` / `test123`
