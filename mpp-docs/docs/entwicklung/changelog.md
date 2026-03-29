# Changelog

## v1.0.0 — 2026-03-29

Initiale Implementierung mit TDD (Test-Driven Development) in 10 Phasen.

### Phase B0: Projekt-Setup
- Django 6.0.3 Projekt-Skeleton mit Split Settings (base/dev/testing)
- PostgreSQL-Anbindung (mpp_dev, mpp_test)
- pytest-django Konfiguration
- TailwindCSS 4 + DaisyUI 5 + HTMX 2.0.4
- Core Domain (UserRole Enum), Mixins, Custom Exceptions

### Phase B1: Identity & Access
- Custom User Model mit Rollen-Feld (4 Rollen)
- django-allauth Integration (Session-basiert)
- Rollen-basierte Access Mixins (Requester/Approver/Admin/Superadmin)
- AccountService mit Seed-Funktion (5 Demo-User)
- Login/Logout Templates (DaisyUI)
- Profil-View und Dashboard

### Phase B2: Service Catalog
- ServiceTemplate Model mit JSONField Parameters
- TemplateValidator (Domain-Logik, 5 Typen)
- CatalogService (list, search, validate, seed)
- Katalog-Views mit HTMX Suche/Filter
- DaisyUI Card-Grid und Detail-Ansicht

### Phase B3: Order Lifecycle
- OrderStatus Enum (9 Zustände) + StatusMachine
- Order, OrderItem, OrderItemGroup Models
- OrderService (create, add/remove items, submit)
- Bestellwizard mit dynamischem Formular aus Template-Schema
- Order-List, Detail, Submit Views

### Phase B4: Context & CMDB
- CMDB Stub Client (YAML-basiert: 3 Locations, 7 Networks, 2 Tenants)
- AvailabilityRule, ContextRestriction, UserTenantAssignment Models
- ContextService (Verfügbarkeit, Einschränkungen, Tenant-Zuordnung)

### Phase B5: Provisioning Engine
- Celery Konfiguration (Redis Broker, EAGER in Dev/Test)
- GitLab Stub Client (Pipeline-Simulation)
- DispatchLog Model
- ProvisioningService (dispatch, complete mit Order-Status-Rollup)
- Celery Tasks (dispatch_provisioning, complete_provisioning)

### Phase B6: Approval Workflow
- ApprovalRule und ApprovalRequest Models
- ApprovalService (needs_approval, create, approve, reject)
- Approval-Queue View (ApproverRequired)
- Inline Approve/Reject Buttons

### Phase B7: Cross-Cutting Concerns
- AuditLog Model + AuditService (inkl. DSGVO-Anonymisierung)
- Notification Model + NotificationService (create, read, mark)
- Notification-Views (list, mark-read, mark-all-read)
- Audit-Log View (AdminRequired, paginiert)
- Dashboard mit echten Statistiken

### Phase B8: Subscriptions
- Subscription + GroupSubscription Models
- SubscriptionService (create_from_order, list, cancel)
- Subscription-Views (list, detail, cancel)

### Phase B9: Integration & Polish
- Unified Seed Command (User + Templates + Rules + Tenants)
- E2E Tests (4 komplette Workflows)
- Dev-Launcher (scripts/run.sh) mit Statusanzeige

### Kennzahlen

| Metrik | Wert |
|--------|------|
| Django Apps | 10 |
| Models | 15 |
| Services | 9 |
| Tests | 228 |
| Commits | 47 |
| TDD-Phasen | B0–B9 |
