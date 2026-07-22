# Benutzerrollen und Anwendungsfälle

CMP kennt vier Benutzerrollen mit hierarchisch aufeinander aufbauenden Rechten. Dieses
Kapitel zeigt die Rollen, wie sie im Code durchgesetzt werden, und welche
Anwendungsfälle je Rolle möglich sind.

## 1. Ziel des Kapitels

Wer eine neue View oder einen neuen Anwendungsfall plant, soll hier nachschlagen können:
welche Rolle existiert, wie eine Rolle im Code geprüft wird, und welche Rolle für welchen
bestehenden Anwendungsfall mindestens nötig ist.

## 2. Die vier Rollen

Die Rolle ist ein Feld auf dem User-Modell, kein separates Berechtigungssystem:

```python
# cmp/core/domain/enums.py:5-9
class UserRole(models.TextChoices):
    REQUESTER = "requester", "Requester"
    APPROVER = "approver", "Approver"
    ADMIN = "admin", "Admin"
    SUPERADMIN = "superadmin", "Superadmin"
```

`User.role` (`cmp/apps/accounts/models.py:9`) speichert einen dieser vier Werte, Default
ist `requester`. Die Rollen bilden eine Hierarchie
(`cmp/apps/accounts/services.py:5-10`, `ROLE_HIERARCHY`): jede höhere Rolle schließt die
Rechte der niedrigeren ein.

| Rolle | Bedeutung |
|---|---|
| `requester` | Standardrolle. Bestellt Services, sieht eigene Bestellungen und Subscriptions. |
| `approver` | Zusätzlich: Genehmigungs-Queue einsehen, genehmigen/ablehnen. |
| `admin` | Zusätzlich: Admin-Dashboard, Systemkonfiguration ansehen, Audit-Log einsehen/exportieren, Zugang zu Django Admin. |
| `superadmin` | Zusätzlich: Regel-Verwaltung im Admin-Panel (Approval-, Availability-, Context-Regeln, Mandantenzuweisungen), volle Django-Admin-Rechte. |

## 3. Rollenprüfung im Code

Views erben von einem der vier Mixins in `cmp/core/mixins.py`, jedes mit einer eigenen
`required_roles`-Liste:

| Mixin | Erlaubte Rollen | Code |
|---|---|---|
| `RequesterRequiredMixin` | requester, approver, admin, superadmin (= jeder angemeldete Benutzer) | `cmp/core/mixins.py:61-67` |
| `ApproverRequiredMixin` | approver, admin, superadmin | `cmp/core/mixins.py:70-76` |
| `AdminRequiredMixin` | admin, superadmin | `cmp/core/mixins.py:79-85` |
| `SuperadminRequiredMixin` | superadmin | `cmp/core/mixins.py:88-94` |

`RoleRequiredMixin.dispatch` (`cmp/core/mixins.py:22-36`) prüft zuerst, ob der Benutzer
angemeldet ist, danach `request.user.role in self.required_roles` — bei Verstoß wird
`PermissionDenied` ausgelöst. Eine nicht abgedeckte Rolle führt also zu HTTP 403, nicht
zu einem stillen Redirect.

`is_staff` (Zugang zu Django Admin) und `is_superuser` sind eigene Django-Felder, keine
Ableitung aus `role`. Beim Anlegen der Stub-User setzt `AccountService.seed_stub_users`
sie konventionsgemäß mit: `is_staff = role in (admin, superadmin)`,
`is_superuser = role == superadmin` (`cmp/apps/accounts/services.py:26-34`). Ein über
Django Admin frei angelegter Benutzer mit `role=admin` bekommt `is_staff`/`is_superuser`
nicht automatisch — das ist Konvention der Seed-Routine, keine Modell-Regel.

## 4. Demo-Zugänge

Erzeugt über `python manage.py seed`, das intern `AccountService.seed_stub_users`
aufruft (`cmp/apps/accounts/services.py:12-18`):

| Username | Rolle | is_staff | is_superuser |
|---|---|---|---|
| test-requester | requester | Nein | Nein |
| test-approver | approver | Nein | Nein |
| test-multi | approver | Nein | Nein |
| test-admin | admin | Ja | Nein |
| test-superadmin | superadmin | Ja | Ja |

Passwort für alle: `test123` (`cmp/apps/accounts/services.py:37`).

## 5. Anwendungsfälle je Rolle

### Requester (Basisrolle, in jeder höheren Rolle enthalten)

| Anwendungsfall | URL / View | Beleg |
|---|---|---|
| Katalog durchsuchen | `catalog:list`, `catalog:detail` | `cmp/apps/catalog/urls.py:8-9`, `TemplateListView`/`TemplateDetailView` mit `RequesterRequiredMixin` (`cmp/apps/catalog/views.py:6,13,36`) |
| Bestellung anlegen und Positionen hinzufügen | `orders:create`, `orders:create_form`, `orders:add_item` | `cmp/apps/orders/urls.py:11-13` |
| Bestellung einreichen | `orders:submit` | `cmp/apps/orders/urls.py:16`, `OrderSubmitView` (`cmp/apps/orders/views.py:431`) |
| Eigene Bestellungen ansehen | `orders:list`, `orders:detail` | `cmp/apps/orders/urls.py:9-10` |
| Eigene Subscriptions ansehen/kündigen | `subscriptions:list`, `subscriptions:cancel` | `cmp/apps/subscriptions/urls.py:9,15-19` |
| Benachrichtigungen lesen | `notifications:list`, `notifications:mark_read` | `cmp/apps/notifications/urls.py:7-12` |
| Eigenes Profil ansehen | `accounts:profile` | `cmp/apps/accounts/urls.py:6`, `ProfileView` (`cmp/apps/accounts/views.py:5`) |
| Dashboard/Startseite | `dashboard:home` | `cmp/apps/dashboard/urls.py:8` |

### Approver (zusätzlich zu Requester)

| Anwendungsfall | URL / View | Beleg |
|---|---|---|
| Genehmigungs-Queue ansehen | `approvals:queue` | `cmp/apps/approvals/urls.py:8`, `ApprovalQueueView` mit `ApproverRequiredMixin` (`cmp/apps/approvals/views.py:7,12`) |
| Bestellung genehmigen | `approvals:approve` | `cmp/apps/approvals/urls.py:9-13` |
| Bestellung ablehnen | `approvals:reject` | `cmp/apps/approvals/urls.py:14-18` |

### Admin (zusätzlich zu Approver)

| Anwendungsfall | URL / View | Beleg |
|---|---|---|
| Admin-Dashboard (Statistiken) | `dashboard:admin_dashboard` | `cmp/apps/dashboard/urls.py:10-14`, `AdminDashboardView` mit `AdminRequiredMixin` (`cmp/apps/dashboard/admin_views.py:3,9`) |
| Systemkonfiguration ansehen | `dashboard:admin_config` | `cmp/apps/dashboard/urls.py:15-19`, `AdminConfigView` (`cmp/apps/dashboard/admin_views.py:21`) |
| Audit-Log ansehen und exportieren | `audit:list`, `audit:export` | `cmp/apps/audit/urls.py:6-7`, `AuditLogListView`/`AuditLogExportView` mit `AdminRequiredMixin` (`cmp/apps/audit/views.py:6,10,32`) |
| Katalog, Benutzer, Regeln über Django Admin pflegen | `/admin/` | `cmp-docs/docs/entwicklung/credentials.md`; Zugriff auf einzelne Modelle setzt zusätzlich Django-Permissions voraus, die im Seed nicht vergeben werden (siehe Abschnitt 3) |

### Superadmin (zusätzlich zu Admin)

| Anwendungsfall | URL / View | Beleg |
|---|---|---|
| Regel-Verwaltung im Admin-Panel (Approval-/Availability-/Context-Regeln, Mandantenzuweisungen) | `dashboard:admin_rules` | `cmp/apps/dashboard/urls.py:20-24`, `AdminRulesView` mit `SuperadminRequiredMixin` (`cmp/apps/dashboard/admin_views.py:3,38`) |
| Voller Django-Admin-Zugriff (`is_superuser`) | `/admin/` | `cmp/apps/accounts/services.py:32` |

Wichtig: die Regel-Verwaltung im **eigenen** Admin-Panel (nicht Django Admin) ist
`superadmin`-only, nicht `admin` — eine reine Admin-Rolle sieht Statistiken und
Konfiguration, aber keine Regeln (`cmp/apps/dashboard/admin_views.py:38`).

## 6. Zusammenfassung

Vier Rollen — requester, approver, admin, superadmin — bilden eine strikte Hierarchie,
durchgesetzt über vier Mixins, die jeweils eine Liste erlaubter Rollen prüfen und bei
Verstoß mit HTTP 403 antworten. Requester deckt den kompletten Bestellweg ab, Approver
kommt der Genehmigungs-Workflow hinzu, Admin bekommt Auswertung und Audit, Superadmin
allein darf die Regeln pflegen, die den Genehmigungs- und Verfügbarkeits-Workflow
steuern. Die tatsächlichen fachlichen Anforderungen hinter diesen Anwendungsfällen
beschreibt Kapitel 3.

> Quelle: cmp/core/domain/enums.py, cmp/apps/accounts/models.py, cmp/apps/accounts/services.py, cmp/core/mixins.py, cmp/apps/*/urls.py, cmp/apps/*/views.py, cmp/apps/dashboard/admin_views.py, cmp-docs/docs/entwicklung/credentials.md — am Code geprüft 2026-07-22
