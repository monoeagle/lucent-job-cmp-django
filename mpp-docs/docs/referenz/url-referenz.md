# URL-Referenz

## Übersicht

Alle URLs sind als Django-Views mit Class-Based Views implementiert. Authentifizierung über django-allauth (Session-basiert).

**Rollen-Legende:**

| Symbol | Bedeutung |
|--------|-----------|
| alle | Jeder authentifizierte User |
| requester+ | requester, approver, admin, superadmin |
| approver+ | approver, admin, superadmin |
| admin+ | admin, superadmin |
| superadmin | nur superadmin |

## Dashboard

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/` | DashboardView | alle | Startseite mit Statistiken |

## Katalog

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/catalog/` | TemplateListView | alle | Katalog-Übersicht mit Suche/Filter |
| `/catalog/<pk>/` | TemplateDetailView | alle | Template-Detail mit Parametern |

**HTMX:** Suche und Kategorie-Filter aktualisieren die Liste ohne Seitenneuladen.

## Bestellungen

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/orders/` | OrderListView | requester+ | Eigene Bestellungen |
| `/orders/<pk>/` | OrderDetailView | requester+ | Bestelldetail mit Items |
| `/orders/create/<template_pk>/` | OrderCreateView | requester+ | Wizard: aus Template bestellen |
| `/orders/<pk>/submit/` | OrderSubmitView (POST) | requester+ | Bestellung einreichen |

## Genehmigungen

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/approvals/` | ApprovalQueueView | approver+ | Offene Genehmigungen |
| `/approvals/<pk>/approve/` | ApprovalApproveView (POST) | approver+ | Genehmigen |
| `/approvals/<pk>/reject/` | ApprovalRejectView (POST) | approver+ | Ablehnen |

## Subscriptions

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/subscriptions/` | SubscriptionListView | requester+ | Laufende Services |
| `/subscriptions/<pk>/` | SubscriptionDetailView | requester+ | Subscription-Detail |
| `/subscriptions/<pk>/cancel/` | SubscriptionCancelView (POST) | requester+ | Kündigen |

## Benachrichtigungen

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/notifications/` | NotificationListView | alle | Alle Benachrichtigungen |
| `/notifications/mark-read/<pk>/` | NotificationMarkReadView (POST) | alle | Als gelesen markieren |
| `/notifications/mark-all-read/` | NotificationMarkAllReadView (POST) | alle | Alle gelesen |

## Audit

| URL | View | Rolle | Beschreibung |
|-----|------|-------|-------------|
| `/audit/` | AuditLogListView | admin+ | Audit-Log mit Filtern |

## Auth (django-allauth)

| URL | Beschreibung |
|-----|-------------|
| `/accounts/login/` | Login-Seite |
| `/accounts/logout/` | Logout |
| `/accounts/profile/` | Benutzerprofil |

## Admin

| URL | Beschreibung |
|-----|-------------|
| `/admin/` | Django Admin Interface |
