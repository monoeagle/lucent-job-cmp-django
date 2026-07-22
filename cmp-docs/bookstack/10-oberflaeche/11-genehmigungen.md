# Genehmigungen (Approver)

Die Genehmigungs-Queue ist die erste Maske dieses Kapitels, die nicht mehr
allen Rollen offensteht — sie erscheint erst ab der Rolle Approver.

## 1. Ziel der Seite

Ein Approver soll offene Genehmigungsanfragen sehen, filtern und einzeln oder
per Mehrfachauswahl genehmigen bzw. ablehnen können.

## 2. Screenshot

![Genehmigungs-Queue der Approver-Rolle: Filter-Tabs (Ausstehend, Genehmigt, Abgelehnt, Alle), Bulk-Aktionen 'Ausgewählte genehmigen' / 'Ausgewählte ablehnen' mit Checkboxen, zwei ausstehende Anträge ('Abloesung alter NAS-Appliance', 'Erweiterung Webfarm fuer Black Friday') mit Datum und Status-Badge 'Ausstehend'. In der Navigation erscheint zusätzlich 'Review Requests'.](../../docs/images/screenshots/Screenshot_11_cmp.png)

Angemeldet als Approver erscheint in der linken Navigation zusätzlich der
Menüpunkt „Review Requests". Filter-Tabs trennen ausstehende, genehmigte und
abgelehnte Anträge; Checkboxen und die beiden Buttons oben erlauben
Mehrfachauswahl für Bulk-Genehmigung bzw. -Ablehnung.

## 3. Rolle und Zugriff

Geschützt durch `ApproverRequiredMixin` (`cmp/core/mixins.py:70`) — Approver,
Admin und Superadmin dürfen die Queue sehen; ein Requester erhält
`PermissionDenied` (`cmp/core/mixins.py:35`, ausgelöst über die gemeinsame
`RoleRequiredMixin.dispatch`-Prüfung, `cmp/core/mixins.py:31-36`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/approvals/` | `approvals:queue` | `ApprovalQueueView` | `cmp/apps/approvals/views.py:12` |
| `/approvals/<int:pk>/approve/` | `approvals:approve` | `ApprovalApproveView` | `cmp/apps/approvals/views.py:31` |
| `/approvals/<int:pk>/reject/` | `approvals:reject` | `ApprovalRejectView` | `cmp/apps/approvals/views.py:41` |

Eingebunden über `path("approvals/", include("apps.approvals.urls"))`,
`cmp/config/urls.py:10`.

## 5. Zusammenfassung

Genehmigen und Ablehnen sind reine POST-Endpunkte, die an
`ApprovalService.approve` bzw. `.reject` delegieren und `ConflictError`/
`NotFoundError` in eine Fehlermeldung übersetzen
(`cmp/apps/approvals/views.py:33-38`, `:44-48`). Ob eine genehmigte Bestellung
automatisch weiterläuft (Provisioning), ist gemäß Kapitel 3.4/3.5 der
Domänendokumentation aktuell nicht durchgängig verdrahtet (AP-13) — diese
Seite dokumentiert nur die Genehmigungsmaske selbst.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_11_cmp.png, cmp/apps/approvals/views.py, cmp/apps/approvals/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
