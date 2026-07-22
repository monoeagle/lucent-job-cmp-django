# MPP Django — Todo erledigt

> Fertige Arbeitspakete (newest-first). Quelle offen: `todo.md`. Stand 2026-07-22, v1.4.0, 347 Tests grün.

## AP-22 · Zugriffskontrolle schließen ✅
Objektbezogene Prüfung unterhalb der Rollen-Mixins: `get_order_for_user`,
`get_subscription_for_user`, `cancel_for_user` (Kündigen bleibt Besitzerhandlung),
`mark_read_for_user`. `/debug-layout/` nur noch bei `DEBUG` registriert.
`ApprovalRule.approver_role` wird über `ApprovalService._load_pending` endlich geprüft
(`ForbiddenError`); `RejectionForm` ersetzt den rohen `request.POST`-Zugriff.
Alle Lücken waren vorher mit einer Probe real ausnutzbar (fremde Bestellung HTTP 200,
`/debug-layout/` anonym HTTP 200, Genehmigung trotz zu schwacher Rolle) — je Lücke
zuerst ein roter Test. Dazu die Regression des eigenen Fixes abgefangen:
`approver_role` ist ein freies CharField — ein Wert ausserhalb der Rollenhierarchie
haette die Anfrage fuer niemanden entscheidbar gemacht (`choices` + `ConflictError`).
17 neue Tests (330 → 347).

## Deployment · VM-Installationsanleitung + Production-Settings ✅
Env-basiertes `config.settings.production` (django-environ) + `.env.example`, Hardening
(`check --deploy` ohne Warnungen), 8 neue Tests (230 → 238). Detaillierte VM-Anleitung
(Rocky/AlmaLinux 9, Voll-Produktion: gunicorn + nginx + systemd + PostgreSQL/Redis + TLS +
SELinux) in `docs/deployment/vm-installation.md`, im README verlinkt. AP-11 (Docker) zurückgestellt.

## AP-10 · Frontend (HTMX + DaisyUI, kein React) ✅
Base-Layout + Navigation (Lucent-Theme), Service-Catalog-UI, Order-Wizard, Approval-Queue,
Admin-Panel (Django Admin), Dashboard. 30 Templates.

## AP-9 · Integration & Polish (B9) ✅
Unified Seed Command, E2E-Tests (4 Workflows), Dev-Launcher (scripts/run.sh, mpp.sh).

## AP-8 · Subscriptions (B8) ✅
Subscription + GroupSubscription Models, SubscriptionService, Subscription-Views.

## AP-7 · Cross-Cutting Concerns (B7) ✅
AuditLog + AuditService (DSGVO), Notification + NotificationService, Audit-Log-View, Dashboard, Credential Delivery.

## AP-6 · Approval-Workflow (B6) ✅
ApprovalRule + ApprovalRequest, ApprovalService, Approval-Queue, Inline Approve/Reject.

## AP-5 · Provisioning-Engine (B5) ✅
Celery (Redis, EAGER), GitLab-Stub-Client, DispatchLog, ProvisioningService, Celery-Tasks.

## AP-4 · Context & CMDB (B4) ✅
CMDB-Stub (YAML), AvailabilityRule/ContextRestriction/UserTenantAssignment, ContextService.

## AP-3 · Order-Lifecycle (B3) ✅
OrderStatus (9 Zustände) + StatusMachine, Order/OrderItem/OrderItemGroup, OrderService, Bestellwizard.

## AP-2 · Service-Katalog (B2) ✅
ServiceTemplate (JSONField), TemplateValidator (5 Typen), CatalogService, HTMX-Katalog-Views.

## AP-1 · Identity & Access (B1) ✅
Custom User + 4 Rollen, django-allauth (Session), Access-Mixins, Login/Logout, AccountService (5 Demo-User).

## AP-0 · Projekt-Setup (B0) ✅
Django-Skeleton (config/, manage.py), PostgreSQL (mpp_dev/mpp_django_test), venv + requirements + .wheels,
pytest-django, Git-Repo.
