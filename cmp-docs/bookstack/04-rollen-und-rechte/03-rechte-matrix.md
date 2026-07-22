# Rechte-Matrix

Diese Seite listet je Aktion, welche Rolle sie ausführen darf, und belegt jede Zelle
mit dem Mixin oder der Code-Stelle, die das erzwingt — oder verhindert.

## 1. Ziel des Kapitels

Wer prüfen will, ob eine Rolle eine Aktion ausführen darf (oder ausführen können
sollte, aber technisch nicht kann), soll hier die durchsetzende Code-Stelle finden,
ohne den View-Code selbst durchsuchen zu müssen.

## 2. Die vier Rollen-Mixins

Alle rollenbasierten Prüfungen laufen über vier Mixins in `cmp/core/mixins.py`, jedes
mit einer festen `required_roles`-Liste. `RoleRequiredMixin.dispatch` prüft zuerst
`is_authenticated`, danach `request.user.role in self.required_roles` und wirft sonst
`PermissionDenied` — HTTP 403, kein stiller Redirect (`cmp/core/mixins.py:31-36`).

| Mixin | Erlaubte Rollen | Code |
|---|---|---|
| `RequesterRequiredMixin` | requester, approver, admin, superadmin | `cmp/core/mixins.py:61-67` |
| `ApproverRequiredMixin` | approver, admin, superadmin | `cmp/core/mixins.py:70-76` |
| `AdminRequiredMixin` | admin, superadmin | `cmp/core/mixins.py:79-85` |
| `SuperadminRequiredMixin` | superadmin | `cmp/core/mixins.py:88-94` |

## 3. Matrix

„ja" heißt: die Rolle erreicht die View und bekommt keinen 403. Ob sie dabei auch nur
ihre **eigenen** Objekte sieht, ist eine zweite Frage — dazu
[Kapitel 4.4](04-objektbezogene-sichtbarkeit.md).

| Aktion | requester | approver | admin | superadmin | Beleg |
|---|---|---|---|---|---|
| Katalog ansehen | ja | ja | ja | ja | `RequesterRequiredMixin` auf `TemplateListView`/`TemplateDetailView` (`cmp/apps/catalog/views.py:6,13,36`) |
| Bestellung anlegen, Positionen hinzufügen, einreichen | ja | ja | ja | ja | `RequesterRequiredMixin` auf allen Order-Views (`cmp/apps/orders/views.py:11,24,60,81,292,375,419,431`) |
| Nur eigene Bestellungen sehen (Standard-Tab) | ja | ja | ja | ja | `OrderListView.get_queryset` filtert auf `user=self.request.user`, außer der Tab „all" greift (`cmp/apps/orders/views.py:39-50`) |
| Alle Bestellungen sehen (Tab „all") | nein | ja | ja | ja | `OrderListView._can_see_all()` prüft `is_at_least_role(role, APPROVER)` (`cmp/apps/orders/views.py:30-37,41`) |
| Genehmigungs-Queue ansehen | nein | ja | ja | ja | `ApproverRequiredMixin` auf `ApprovalQueueView` (`cmp/apps/approvals/views.py:7,12`) |
| Bestellung genehmigen/ablehnen | nein | ja | ja | ja | `ApproverRequiredMixin` auf `ApprovalApproveView`/`ApprovalRejectView` (`cmp/apps/approvals/views.py:7,31,41`) |
| Admin-Dashboard (Statistiken) | nein | nein | ja | ja | `AdminRequiredMixin` auf `AdminDashboardView` (`cmp/apps/dashboard/admin_views.py:3,9`) |
| Systemkonfiguration ansehen | nein | nein | ja | ja | `AdminRequiredMixin` auf `AdminConfigView` (`cmp/apps/dashboard/admin_views.py:3,21`) |
| Audit-Log ansehen/exportieren | nein | nein | ja | ja | `AdminRequiredMixin` auf `AuditLogListView`/`AuditLogExportView` (`cmp/apps/audit/views.py:6,10,32`) |
| Regel-Übersicht im Admin-Panel ansehen | nein | nein | nein | ja | `SuperadminRequiredMixin` auf `AdminRulesView` (`cmp/apps/dashboard/admin_views.py:3,38`) |
| Katalog pflegen (Templates anlegen/ändern) | nein | nein | (siehe unten) | (siehe unten) | Keine App-View — nur `/admin/`, `ServiceTemplateAdmin` (`cmp/apps/catalog/admin.py:6-10`; `cmp/apps/catalog/views.py` hat nur List/Detail) |
| Regeln pflegen (Approval-/Availability-/Context-Regeln, Mandantenzuweisungen) | nein | nein | (siehe unten) | (siehe unten) | Keine App-View — nur `/admin/` (`cmp/apps/approvals/admin.py:6-15`, `cmp/apps/cmdb/admin.py:6-19`); `AdminRulesView` selbst zeigt die Regeln nur an, ohne Formular (`cmp/templates/admin_panel/rules.html`, geprüft: keine `<form>`/`hx-post` im Template) |
| Benutzer/Rollen pflegen | nein | nein | (siehe unten) | (siehe unten) | Keine App-View — nur `/admin/`, `UserAdmin` (`cmp/apps/accounts/admin.py:6-16`) |

## 4. Lücke: Django-Admin-Rechte hängen nicht an der Rolle

Die drei mit „(siehe unten)" markierten Zeilen sind eine Django-Admin-Angelegenheit,
keine `role`-Prüfung: Zugriff auf ein Modell in `/admin/` setzt `is_staff=True`
**und** die passende Django-Permission (z. B. `catalog.change_servicetemplate`)
voraus, sofern der Account nicht `is_superuser=True` ist.

Im Seed werden Permissions an niemanden vergeben (geprüft:
`grep -rn "user_permissions\|\.groups\.add\|assign_perm" cmp/apps/` — kein Treffer
außer dem `ManyToManyField` der Migration selbst,
`cmp/apps/accounts/migrations/0001_initial.py:36`). `AccountService.seed_stub_users`
setzt nur `is_staff`/`is_superuser` (`cmp/apps/accounts/services.py:26-34`):

```python
"is_staff": user_data["role"] in (UserRole.ADMIN, UserRole.SUPERADMIN),
"is_superuser": user_data["role"] == UserRole.SUPERADMIN,
```

Das heißt konkret: `test-superadmin` (`is_superuser=True`) hat sicher vollen
Admin-Zugriff auf alle Modelle. `test-admin` (`is_staff=True`, `is_superuser=False`)
darf sich unter `/admin/` einloggen, hat dort aber ohne zusätzlich vergebene
Permissions keinen garantierten Zugriff auf einzelne Modelle — Django prüft je
Modell `has_change_permission`/`has_view_permission` und die verlangen bei
`is_superuser=False` eine explizit zugewiesene `auth.Permission`. Ein über Django
Admin frei angelegter `admin`-Benutzer hat also nicht automatisch dieselben Rechte
wie `test-admin` aus dem Seed, wenn dabei keine Permissions gesetzt werden.

## 5. `approver_role` wird seit AP-22 vor jeder Entscheidung geprüft

`ApprovalRule` hat ein Feld `approver_role` (Default `approver`,
`cmp/apps/approvals/models.py:20-22`), das festlegt, welche Rolle eine
konkrete Regel genehmigen darf. Bis AP-22 lasen `ApprovalService.approve` und
`.reject` dieses Feld nicht — jeder Benutzer mit Rolle `approver`, `admin` oder
`superadmin` konnte jede offene Anfrage entscheiden, unabhängig vom Regelwert.

Seit AP-22 laden beide Methoden die Anfrage über die private Hilfsmethode
`ApprovalService._load_pending` (`cmp/apps/approvals/services.py:51-80`), die
zusätzlich zur bisherigen `pending`-Prüfung die Rolle des Entscheiders gegen
`req.rule.approver_role` abgleicht:

```python
verlangt = req.rule.approver_role
if not AccountService.is_at_least_role(approver.role, verlangt):
    raise ForbiddenError(
        f"Diese Entscheidung verlangt die Rolle '{verlangt}'."
    )
```

Reicht die Rolle nicht, wirft `_load_pending` `ForbiddenError`
(`cmp/core/exceptions.py:24-25`) — `approve` (`services.py:83-97`) und `reject`
(`services.py:100-109`) rufen beide zuerst `_load_pending` auf, bevor sie den
Status ändern. Die Views fangen `ForbiddenError` neben `ConflictError` und
`NotFoundError` ab und zeigen sie als Django-Message
(`cmp/apps/approvals/views.py:38`, `:53`). `ApproverRequiredMixin` bleibt die
View-Ebene (Abschnitt 3) und reicht für sich allein nicht mehr aus — die
Regel-Rolle ist jetzt eine zweite, service-seitige Schranke.

Eine zweite, spätere Korrektur schließt eine Lücke, die diese Prüfung selbst
aufriss: `approver_role` trägt jetzt `choices=UserRole.choices` statt Freitext,
und `_load_pending` weist einen Regelwert außerhalb der vier Rollen vor der
Rollenprüfung mit `ConflictError` zurück (`services.py:68-75`) — Details in
[Kapitel 5.3](../05-genehmigungs-workflow/03-ein-und-mehrstufige-genehmigung.md).

## 6. Zusammenfassung

Die Rollen-Durchsetzung in den Fach-Views ist konsistent über vier Mixins gelöst und
lässt sich lückenlos auf `required_roles`-Listen zurückführen. Eine Stelle weicht
davon ab: „Katalog/Regeln/Benutzer pflegen" hängt faktisch an Django-Admin-
Permissions, nicht an `role` — für `admin` (im Unterschied zu `superadmin`) ist das
nur im Seed abgesichert, nicht als Modell-Regel. Die frühere zweite Lücke —
`ApprovalService` prüfte `ApprovalRule.approver_role` nicht — ist seit AP-22
geschlossen: `_load_pending` erzwingt sie vor jeder Entscheidung. Welche Objekte
eine Rolle darüber hinaus sieht oder bearbeiten kann, zeigt die folgende Seite.

> Quelle: cmp/core/mixins.py, cmp/apps/catalog/views.py, cmp/apps/catalog/admin.py, cmp/apps/orders/views.py, cmp/apps/approvals/views.py, cmp/apps/approvals/services.py, cmp/apps/approvals/models.py, cmp/apps/approvals/admin.py, cmp/apps/cmdb/admin.py, cmp/apps/dashboard/admin_views.py, cmp/apps/audit/views.py, cmp/apps/accounts/admin.py, cmp/apps/accounts/services.py, cmp/apps/accounts/migrations/0001_initial.py, cmp/core/exceptions.py, cmp/templates/admin_panel/rules.html — am Code geprüft 2026-07-22
