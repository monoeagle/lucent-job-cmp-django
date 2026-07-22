# Audit-Log (Admin)

Das Audit-Log protokolliert revisionssicher alle relevanten Aktionen im System
und ist Admin/Superadmin vorbehalten.

## 1. Ziel der Seite

Ein Admin soll nachvollziehen können, wer wann was getan hat — gefiltert nach
Aktion und Ressourcentyp — und die Liste bei Bedarf als CSV exportieren.

## 2. Screenshot

![Audit-Log der Superadmin-Rolle: Filterfelder für Aktion und Ressourcentyp, CSV-Export-Button, Tabelle mit Zeitpunkt, Aktion (system_startup, template_updated, order_created, order_submitted), Ressource, Benutzer und Detail-JSON. Links ein zusätzlicher Admin-Navigationsblock (Admin Dashboard, Konfiguration, Regeln, Audit-Log, Django Admin).](../../docs/images/screenshots/Screenshot_12_cmp.png)

Als Admin/Superadmin wird links ein zusätzlicher Admin-Navigationsblock
sichtbar (Admin Dashboard, Konfiguration, Regeln, Audit-Log, Django Admin).
Die Tabelle zeigt Zeitpunkt, Aktion, Ressource (mit ID), Benutzer und die
Detail-Payload als JSON; zwei Filterfelder grenzen nach Aktion bzw.
Ressourcentyp ein.

## 3. Rolle und Zugriff

Geschützt durch `AdminRequiredMixin` (`cmp/core/mixins.py:79`) — nur Admin und
Superadmin sehen das Audit-Log; Requester und Approver erhalten
`PermissionDenied`. Die vier zusätzlichen Admin-Navigationspunkte im
Screenshot (Admin Dashboard, Konfiguration, Regeln, Django Admin) gehören zu
eigenen Views außerhalb dieser Seite: `AdminDashboardView` und
`AdminConfigView` sind ebenfalls `AdminRequiredMixin`-geschützt
(`cmp/apps/dashboard/admin_views.py:9`, `:21`), `AdminRulesView` dagegen ist
`SuperadminRequiredMixin`-geschützt und damit nur für Superadmin sichtbar
(`cmp/apps/dashboard/admin_views.py:38`, Mixin-Definition
`cmp/core/mixins.py:88`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/audit/` | `audit:list` | `AuditLogListView` | `cmp/apps/audit/views.py:10` |
| `/audit/export/` | `audit:export` | `AuditLogExportView` | `cmp/apps/audit/views.py:32` |

Eingebunden über `path("audit/", include("apps.audit.urls"))`,
`cmp/config/urls.py:12`.

## 5. Zusammenfassung

Der CSV-Export (`AuditLogExportView`) läuft ohne Paginierung über das
komplette `AuditLog.objects.all()` und schreibt direkt in die
HTTP-Response (`cmp/apps/audit/views.py:32-50`); die Listenansicht dagegen
paginiert mit `paginate_by = 50` (`cmp/apps/audit/views.py:13`).

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_12_cmp.png, cmp/apps/audit/views.py, cmp/apps/audit/urls.py, cmp/apps/dashboard/admin_views.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
