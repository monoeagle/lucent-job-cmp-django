# Architektur

## Überblick

CMP Django verwendet eine **Hybrid-Architektur**: Django-Konventionen mit einem expliziten Service-Layer für Business-Logik.

```
Browser (HTMX)
    ↓
Django Views (dünn)
    ↓
Django Forms (Validierung)
    ↓
Services (Business-Logik)
    ↓
Django ORM (Models)
    ↓
PostgreSQL
```

!!! info "Das ist die logische Sicht"
    Dieses Bild beantwortet **„was ruft was"**. Prozesse, Dienste und Ports kommen
    darin bewusst nicht vor — nginx und gunicorn tauchen hier nicht auf, weil sie
    keine Business-Logik aufrufen, sondern den gesamten Web-Layer *hosten*.

    Wie das im Betrieb zusammenhängt — welcher Prozess auf welchem Port lauscht,
    was nginx, gunicorn, Redis und Celery jeweils tun, wie der Zugriff vom Client
    aussieht — steht in der [Laufzeit-Topologie](../betrieb/laufzeit-topologie.md).

## Schichtentrennung

### Regel: Views sind dünn

Views delegieren an Services. Keine Business-Logik in Views, Forms oder Models.

```
View → Form → Service → Model → Template
```

### Dependency-Regeln

| Von | Nach | Erlaubt |
|-----|------|---------|
| views.py | services.py | ✓ |
| views.py | forms.py | ✓ |
| views.py | models.py (read) | ✓ |
| views.py | models.py (write) | ✗ |
| services.py | models.py | ✓ |
| services.py | core/domain/ | ✓ |
| services.py | andere services | ✓ |
| core/ | apps/ | ✗ |
| core/domain/ | Django | ✗ (nur TextChoices) |

Diese Regel bestimmt, wo der zentrale Statusübergang wohnt: `transition(order,
to_status, actor, **details)` (seit v1.5.0) bündelt Übergangsprüfung + Statuswechsel
+ Audit-Log und liegt in `apps/orders/transitions.py`, **nicht** in `core/domain/` —
denn er ruft `AuditService` aus `apps/` auf, und `core/ → apps/` ist verboten. Die
reine Regeltabelle `StatusMachine` bleibt in `core/domain/value_objects.py`. Details
und Ablaufdiagramm: [Services → Bestellkette](../referenz/services.md).

## App-Struktur (Hybrid-Pattern)

Jede Django-App folgt dem gleichen Aufbau:

```
apps/{name}/
├── models.py      # Django Models (Daten-Schicht)
├── services.py    # Business-Logik (Framework-agnostisch)
├── views.py       # Class-Based Views (dünn, max 15 Zeilen/Methode)
├── forms.py       # Input-Validierung
├── admin.py       # Django Admin Konfiguration
├── urls.py        # URL-Patterns (app-namespaced)
└── apps.py        # AppConfig
```

## 10 Django Apps

| App | Verantwortung |
|-----|---------------|
| `accounts` | Custom User, Rollen, Auth (allauth) |
| `catalog` | Service-Templates, Parameter-Schemas |
| `orders` | Bestellungen, Items, Groups, zentraler Statusübergang (`transitions.py`) |
| `approvals` | Approval-Regeln, Genehmigungs-Requests |
| `provisioning` | Celery-Tasks, GitLab-Client, DispatchLog |
| `cmdb` | CMDB-Stub, Verfügbarkeits-Regeln, Context |
| `notifications` | In-App-Benachrichtigungen |
| `audit` | Audit-Logs, DSGVO-Anonymisierung |
| `subscriptions` | Laufende Services, Kündigungen |
| `dashboard` | Statistiken, Übersicht |

## Shared Code (core/)

```
core/
├── domain/
│   ├── enums.py          # UserRole
│   ├── value_objects.py  # OrderStatus, StatusMachine
│   └── validators.py     # TemplateValidator
├── mixins.py             # TimeStampedModel, RoleRequiredMixin, ...
└── exceptions.py         # ServiceError, ValidationError, ...
```

## Rollen-System

```
superadmin ⊃ admin ⊃ approver ⊃ requester
```

| Rolle | Zugriff |
|-------|---------|
| requester | Katalog, Bestellen, eigene Orders/Subscriptions |
| approver | + Genehmigungen, Approval-Queue |
| admin | + Django Admin, Audit-Log, Katalog-Verwaltung |
| superadmin | + DSGVO-Anonymisierung, User-Verwaltung |

## Order-Lifecycle (Status-Machine)

```
draft → validated → submitted → pending_approval → approved → provisioning → done
                                                  → rejected
                                                    provisioning → failed
```

Terminale Zustände: `done`, `failed`, `rejected`

## Externe Systeme

| System | Anbindung | Modus |
|--------|-----------|-------|
| PostgreSQL | Django ORM | Direkt |
| Redis | Celery Broker | Optional (EAGER in Dev) |
| GitLab | Pipeline-Trigger | Stub (YAML) / Live |
| CMDB | Locations, Networks | Stub (YAML) / Live |
| LDAP/OAuth | django-allauth | Vorbereitet, nicht aktiv |

Ports, systemd-Units und die Aufgabenteilung der Dienste: siehe [Laufzeit-Topologie](../betrieb/laufzeit-topologie.md).
