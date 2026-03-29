# MPP Django Marketplace Portal — Design Specification

**Datum:** 2026-03-29
**Autor:** Tobias Philipp / Lucent Trails
**Status:** Approved
**Basis:** lucent-app-mpp-TDD (Flask) als fachliche Vorlage

---

## 1. Überblick

Self-Service-Portal für automatisiertes IT-Service-Provisioning. Benutzer bestellen VMs, Datenbanken und Container aus einem Service-Katalog mit vollem Approval- und Provisioning-Workflow.

**Neukonzeption:** Das bestehende Flask/React-Projekt (862 Tests, 96 API-Endpoints) wird mit Django als Basistechnologie neu aufgebaut — kein API-First-Ansatz, sondern klassisches Server-Side Rendering.

---

## 2. Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Backend | Python 3.12, Django 6.0 |
| Rendering | Django Templates + HTMX |
| CSS | TailwindCSS + DaisyUI |
| Auth | django-allauth |
| Async | Celery + Redis |
| Echtzeit | Django Channels (WebSocket) |
| Datenbank | PostgreSQL 14+ (Django ORM) |
| Testing | pytest-django, factory_boy |
| Server | ASGI (Daphne/Uvicorn) |

**Kein:** React, DRF, REST-API, SPA, JWT

---

## 3. Architektur: Hybrid (Django-First + Service-Layer)

Jede Django-App enthält eigene Models, Views, Templates, Forms und einen `services.py` für Business-Logik. Shared Domain-Logik (Enums, Value Objects, Status-Machines) in `core/domain/`.

### Schichten-Regel pro App

```
View (HTTP-Request)
  → Form (Validierung)
    → Service (Business-Logik)
      → Model (Daten-Zugriff)
        → Template (Rendering)
```

### Dependency-Regeln

| Von | Nach | Erlaubt? |
|-----|------|----------|
| views.py | services.py | ✓ |
| views.py | forms.py | ✓ |
| views.py | models.py (read für QuerySets) | ✓ |
| services.py | models.py | ✓ |
| services.py | core/domain/ | ✓ |
| services.py | andere apps/*/services.py | ✓ |
| forms.py | models.py | ✓ |
| models.py | core/mixins.py | ✓ |
| models.py | core/domain/ | ✓ |
| core/ | apps/ | ✗ |
| views.py | models.py (write/create) | ✗ |

---

## 4. Projektstruktur

```
lucent-app-mpp-TDD-Django/
├── mpp/                              # Django-Projekt
│   ├── config/                       # Projektkonfiguration
│   │   ├── settings/
│   │   │   ├── base.py              # Gemeinsame Settings
│   │   │   ├── development.py       # DEBUG=True, Stubs aktiv
│   │   │   ├── testing.py           # Test-DB, CELERY_TASK_ALWAYS_EAGER
│   │   │   └── production.py        # Security-gehärtet
│   │   ├── urls.py                  # Root-URLs
│   │   ├── asgi.py                  # ASGI für Channels
│   │   ├── wsgi.py
│   │   └── celery.py                # Celery App
│   │
│   ├── apps/                         # 10 Django-Apps
│   │   ├── accounts/                # Auth, User, Rollen
│   │   │   ├── models.py           # Custom User (AbstractUser)
│   │   │   ├── services.py         # AuthService
│   │   │   ├── forms.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   └── apps.py
│   │   ├── catalog/                 # Service-Templates, Parameter
│   │   ├── orders/                  # Bestellungen, Items, Groups
│   │   ├── approvals/              # Approval-Regeln, Requests
│   │   ├── provisioning/           # Celery-Tasks, GitLab-Client
│   │   │   ├── tasks.py            # Celery-Tasks
│   │   │   ├── clients.py          # GitLabStubClient / GitLabLiveClient
│   │   │   └── services.py
│   │   ├── cmdb/                   # CMDB-Stub, Context, Availability
│   │   ├── notifications/          # In-App + WebSocket
│   │   │   ├── consumers.py        # WebSocket Consumer
│   │   │   └── routing.py          # WebSocket URLs
│   │   ├── subscriptions/          # Services verwalten
│   │   ├── audit/                  # Audit-Logs, DSGVO
│   │   └── dashboard/             # Stats, Übersichten
│   │
│   ├── core/                        # Shared Code
│   │   ├── domain/
│   │   │   ├── enums.py            # UserRole, OrderStatus, etc.
│   │   │   └── value_objects.py    # Status-Machine, Validation Rules
│   │   ├── mixins.py               # TimeStampedModel, RoleRequiredMixin
│   │   ├── exceptions.py           # Custom Exception Hierarchy
│   │   └── templatetags/           # Custom Template-Tags
│   │
│   ├── templates/                   # Projektweite Templates
│   │   ├── base.html               # DaisyUI Layout-Skeleton
│   │   ├── includes/               # Navbar, Sidebar, Footer, Messages
│   │   ├── accounts/
│   │   ├── catalog/
│   │   ├── orders/
│   │   │   └── partials/           # HTMX-Partials
│   │   ├── approvals/
│   │   ├── subscriptions/
│   │   ├── notifications/
│   │   ├── audit/
│   │   └── dashboard/
│   │
│   ├── static/
│   │   ├── css/                    # Tailwind Output
│   │   ├── js/                     # HTMX
│   │   └── images/
│   │
│   ├── stubs/
│   │   ├── cmdb/                   # YAML CMDB-Daten
│   │   └── gitlab_mock.py          # GitLab-Pipeline-Simulator
│   │
│   └── manage.py
│
├── tests/
│   ├── conftest.py                  # Shared Fixtures
│   ├── factories.py                 # factory_boy Factories
│   ├── unit/                        # Service-Tests, Domain-Tests
│   ├── integration/                 # View-Tests, Model-Tests
│   └── e2e/                         # Workflow-Tests
│
├── scripts/
│   ├── mpp.sh                       # Dev-Launcher
│   └── screenshot_tool.py
│
├── docs/
│   ├── specs/                       # Feature-Spezifikationen
│   └── superpowers/specs/           # Design-Docs
│
├── requirements/
│   ├── base.txt                     # Django, Channels, Celery
│   ├── dev.txt                      # pytest, factory_boy, ruff
│   └── prod.txt                     # gunicorn, sentry
│
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── tailwind.config.js
├── package.json
└── .env.example
```

---

## 5. Datenmodell (15 Models)

### Abstrakte Basis

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

### Models pro App

| App | Model | Schlüsselfelder |
|-----|-------|----------------|
| accounts | `User` | username, email, role (CharField Choices) |
| catalog | `ServiceTemplate` | name, category, description, parameters (JSONField), is_active, version |
| orders | `Order` | user (FK→User), status, notes |
| orders | `OrderItem` | order (FK), template (FK), parameters (JSONField), group (FK, nullable) |
| orders | `OrderItemGroup` | order (FK), template (FK), quantity, shared_parameters (JSONField) |
| approvals | `ApprovalRule` | template (FK), condition (JSONField), approver_role |
| approvals | `ApprovalRequest` | order (FK), rule (FK), status, decided_by (FK, nullable), comment |
| provisioning | `DispatchLog` | order_item (FK), pipeline_id, status, payload (JSONField) |
| cmdb | `AvailabilityRule` | template (FK), location, tenant, is_available |
| cmdb | `ContextRestriction` | template (FK), parameter_key, context_field, allowed_values (JSONField) |
| cmdb | `UserTenantAssignment` | user (FK), tenant |
| notifications | `Notification` | user (FK), title, message, is_read, category |
| subscriptions | `Subscription` | user (FK), order_item (FK), status, valid_from, valid_until |
| subscriptions | `GroupSubscription` | user (FK), order_item_group (FK), status |
| audit | `AuditLog` | user (FK, nullable), action, resource_type, resource_id, details (JSONField) |

### Status-Machine (Order)

```
draft → validated → submitted → pending_approval → approved → provisioning → done
                                                  → rejected
                                        provisioning → failed
```

Implementiert als Value Object in `core/domain/value_objects.py` mit expliziter Whitelist gültiger Übergänge.

---

## 6. Authentifizierung & Rollen

### django-allauth

- Session-basiertes Login (kein JWT)
- `ACCOUNT_LOGIN_METHODS = {"username"}`
- `ACCOUNT_SIGNUP_ENABLED = False` (Admin erstellt User)
- Erweiterbar für LDAP/OAuth via allauth-Provider

### Rollen

```python
class UserRole(models.TextChoices):
    REQUESTER = "requester"
    APPROVER = "approver"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
```

Approver ist Superset von Requester (kann auch bestellen).

### Rollen-Mixins

```python
class RoleRequiredMixin(LoginRequiredMixin):
    required_roles = []
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in self.required_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

### Berechtigungsmatrix

| Aktion | requester | approver | admin | superadmin |
|--------|-----------|----------|-------|------------|
| Katalog ansehen | ✓ | ✓ | ✓ | ✓ |
| Bestellen | ✓ | ✓ | ✓ | ✓ |
| Approval-Queue | – | ✓ | ✓ | ✓ |
| Katalog verwalten | – | – | ✓ | ✓ |
| Audit-Logs | – | – | ✓ | ✓ |
| DSGVO-Anonymisierung | – | – | – | ✓ |
| Django Admin | – | – | ✓ | ✓ |

### Stub-User (Development)

| Username | Passwort | Rolle |
|----------|----------|-------|
| test-requester | test123 | requester |
| test-approver | test123 | approver |
| test-admin | test123 | admin |
| test-multi | test123 | approver (kann auch bestellen) |
| test-superadmin | test123 | superadmin |

---

## 7. Provisioning & Async

### Infrastruktur

```
Django (ASGI) ←→ Redis ←→ Celery Worker
     ↓              ↓
PostgreSQL    Django Channels (WebSocket)
     ↓
GitLab (Mock/Live) → OpenTofu
```

### Celery-Tasks

- `dispatch_provisioning(order_item_id)` — GitLab-Pipeline triggern
- `simulate_pipeline_completion(pipeline_id)` — Stub: nach X Sekunden success
- `check_pipeline_status(pipeline_id)` — Polling (Live-Mode)

### GitLab-Client

- `GitLabStubClient` — Simuliert Pipelines (Development)
- `GitLabLiveClient` — Echte GitLab-API (Production)
- Umschaltung via `GITLAB_CLIENT` Setting

### WebSocket (Django Channels)

- `NotificationConsumer` — Pro User eine Gruppe
- Push bei: Provisioning-Status, Approval-Entscheidung, neue Notification
- Redis als Channel Layer
- Testing: `InMemoryChannelLayer`

### Testing

- `CELERY_TASK_ALWAYS_EAGER = True` in testing.py
- Tasks laufen synchron in Tests
- WebSocket: InMemoryChannelLayer

---

## 8. UI-Architektur

### DaisyUI Theme "Lucent"

- Primary: Indigo (#4f46e5)
- Secondary: Violet (#7c3aed)
- Accent: Cyan (#06b6d4)
- Custom Theme in `tailwind.config.js`

### Template-Hierarchie

- `base.html` — HTML-Skeleton mit Navbar, Drawer-Sidebar, Content, Footer
- `includes/` — Navbar, Sidebar, Messages, Pagination
- Pro App ein Template-Ordner mit `partials/` für HTMX

### HTMX-Patterns

1. **Suche/Filter:** `hx-get` mit `delay:300ms` auf Input-Felder
2. **Wizard-Steps:** Session-basierter State, HTMX lädt Steps
3. **Inline-Actions:** `hx-post` mit `hx-target` + `hx-swap="outerHTML"`
4. **Live-Status:** WebSocket-Push aktualisiert Status-Badges

### Responsive

- Desktop: Sidebar permanent
- Tablet: Drawer (togglebar)
- Mobile: Hamburger-Menü Overlay

---

## 9. URL-Struktur

| URL | View | Rolle |
|-----|------|-------|
| `/` | DashboardView | alle |
| `/catalog/` | TemplateListView | alle |
| `/catalog/<pk>/` | TemplateDetailView | alle |
| `/orders/` | OrderListView | requester+ |
| `/orders/create/<template_pk>/` | OrderCreateView | requester+ |
| `/orders/<pk>/` | OrderDetailView | requester+ |
| `/orders/<pk>/add-item/` | OrderItemCreateView | requester+ |
| `/orders/<pk>/remove-item/<item_pk>/` | OrderItemDeleteView | requester+ |
| `/orders/<pk>/submit/` | OrderSubmitView | requester+ |
| `/orders/<pk>/add-group/` | OrderGroupCreateView | requester+ |
| `/approvals/` | ApprovalQueueView | approver+ |
| `/approvals/<pk>/` | ApprovalDetailView | approver+ |
| `/approvals/<pk>/approve/` | ApprovalApproveView | approver+ |
| `/approvals/<pk>/reject/` | ApprovalRejectView | approver+ |
| `/subscriptions/` | SubscriptionListView | requester+ |
| `/subscriptions/<pk>/` | SubscriptionDetailView | requester+ |
| `/subscriptions/<pk>/change/` | SubscriptionChangeView | requester+ |
| `/subscriptions/<pk>/cancel/` | SubscriptionCancelView | requester+ |
| `/notifications/` | NotificationListView | alle |
| `/notifications/mark-read/<pk>/` | NotificationMarkReadView | alle |
| `/notifications/mark-all-read/` | NotificationMarkAllReadView | alle |
| `/audit/` | AuditLogListView | admin+ |
| `/audit/anonymize/<user_pk>/` | AuditAnonymizeView | superadmin |
| `/admin/` | Django Admin | admin+ |

---

## 10. Phasenplan

| Phase | Name | Inhalt | ~Tests |
|-------|------|--------|--------|
| B0 | Projekt-Setup | Django, PostgreSQL, pytest, Tailwind/DaisyUI, Git | 10 |
| B1 | Identity & Access | Custom User, allauth, Rollen-Mixins, Login Views | 40 |
| B2 | Service Catalog | ServiceTemplate, Validator, CatalogService, Views | 80 |
| B3 | Order Lifecycle | Order/Item/Group, Status-Machine, Wizard | 120 |
| B4 | Context & CMDB | CMDB Stub, ContextService, Availability | 60 |
| B5 | Provisioning | Celery, GitLab Stub, Dispatch | 50 |
| B6 | Approvals | Rules, Requests, Queue | 70 |
| B7 | Cross-Cutting | Audit, Notifications, WebSocket, Dashboard | 80 |
| B8 | Subscriptions | Subscription Models, Views | 50 |
| B9 | Integration | Seed, Docker, Dev-Launcher, E2E | 40 |
| **Gesamt** | | | **~600** |

### TDD-Workflow pro Feature

```
Product-Owner → Spec (REQ, VAL, EC)
  → Backend-Architect → Architektur-Review
    → QA-Test-Writer → Tests (alle rot)
      → Django-Dev → Implementation (Tests grün)
        → Clean-Architect → Refactoring
          → Security-Engineer → Security-Review (pro Phase)
            → Auditor → Phase-Audit
```

---

## 11. Agent-Workflow

| Agent | Rolle | Model | Wann |
|-------|-------|-------|------|
| marketplace-product-owner | Feature-Specs | Sonnet | Feature-Start |
| marketplace-backend-architect | Architektur | Opus | Neue Module |
| qa-test-writer | Tests schreiben | Sonnet | Vor Implementation |
| python-django-dev | Implementation | Opus | Tests grün machen |
| clean-architect | Refactoring | Opus | Nach Implementation |
| security-engineer | Security-Review | Opus | Pro Phase |
| devops-engineer | CI/CD, Docker | Sonnet | Infrastruktur |
| auditor | Quality Gate | Opus | Phasenende |
| senior-debugger | Bug-Diagnose | Opus | Bei Fehlern |

---

## 12. Verbote

- Keine Business-Logik in Views, Forms oder Models
- Kein raw SQL ohne zwingende Performance-Gründe
- Keine Django-Abhängigkeiten in `core/domain/`
- Keine zirkulären Imports zwischen Apps
- Kein `DEBUG=True` in Production
- Keine destruktiven Commands ohne Bestätigung
- Keine Dependency-Änderungen ohne Freigabe
- Kein DB-Schema-Upgrade ohne Review
