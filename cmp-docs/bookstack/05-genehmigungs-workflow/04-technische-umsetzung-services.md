# Technische Umsetzung — ApprovalService

`ApprovalService` bündelt die gesamte Genehmigungslogik als sechs statische
Methoden. Dieses Kapitel geht `approve` und `reject` Schritt für Schritt durch,
inklusive der gemeinsamen Ladefunktion `_load_pending` (seit AP-22) und der
Aufrufkette aus den Views — und benennt eine Stelle, an der beide Methoden
bewusst anders arbeiten als der Rest des Bestellflusses.

## 1. Ziel des Kapitels

Wer eine Genehmigungsentscheidung debuggt oder die Methoden erweitert, muss die
genaue Reihenfolge der Schritte kennen — insbesondere, welche Prüfung
`StatusMachine.validate_transition` durchläuft und welche nicht.

## 2. `create_approval_requests` — Schritt für Schritt

`ApprovalService.create_approval_requests(order_id)` (`apps/approvals/services.py:26-48`):

1. `OrderService.get_order(order_id)` lädt die Bestellung oder wirft `NotFoundError`.
2. `order.items.values_list("template_id", flat=True).distinct()` ermittelt die betroffenen Templates.
3. `ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True)` liefert alle passenden Regeln.
4. Für **jede** Regel: `ApprovalRequest.objects.create(order=order, rule=rule, status="pending")`.
5. Nur wenn mindestens ein Antrag entstanden ist: `StatusMachine.validate_transition(order.status, PENDING_APPROVAL)`, dann `order.status = PENDING_APPROVAL`, `order.save()`.
6. Rückgabe: Liste der erzeugten `ApprovalRequest`-Objekte (leer, wenn keine Regel passte).

## 3. `_load_pending` — die gemeinsame Ladefunktion seit AP-22

Bis AP-22 luden `approve` und `reject` die `ApprovalRequest` jeweils mit
identischem, dupliziertem Code. Seit AP-22 bündelt die private Hilfsmethode
`ApprovalService._load_pending(request_id, approver)`
(`apps/approvals/services.py:51-80`) das Laden und eine zusätzliche
Rollenprüfung, die beide Methoden zuerst aufrufen:

1. `ApprovalRequest.objects.select_related("order", "rule").get(pk=request_id)` — sonst `NotFoundError`.
2. Wenn `req.status != "pending"`: `ConflictError(f"Request already decided: {req.status}")`.
3. Konfigurationsprüfung (später ergänzt, siehe unten): `req.rule.approver_role not in UserRole.values` —
   trifft das zu, `ConflictError`, weil die Regel eine unbekannte Rolle nennt (`services.py:68-75`).
4. Rollenabgleich: `AccountService.is_at_least_role(approver.role, req.rule.approver_role)` —
   reicht die Rolle nicht, `ForbiddenError(f"Diese Entscheidung verlangt die Rolle '{verlangt}'.")`.
5. Rückgabe der geladenen `ApprovalRequest`.

Schritt 4 ist die in [Kapitel 5.2](02-wer-genehmigt-was.md) beschriebene
Durchsetzung von `ApprovalRule.approver_role` — bis AP-22 gab es diesen Schritt
nicht, jede Rolle ab `approver` konnte jede Anfrage entscheiden. Schritt 3 kam
erst in einer zweiten, späteren Korrektur dazu: `approver_role` trägt seither
`choices=UserRole.choices` (`apps/approvals/models.py:20-22`, Migration
`0002_alter_approvalrule_approver_role.py`), und `_load_pending` weist einen
Regelwert außerhalb der vier Rollen als Konfigurationsfehler zurück, statt
Schritt 4 stumm `False` liefern und damit die Anfrage für jede Rolle sperren zu
lassen.

## 4. `approve` — Schritt für Schritt

`ApprovalService.approve(request_id, approver)` (`apps/approvals/services.py:83-97`):

1. `req = ApprovalService._load_pending(request_id, approver)` (Abschnitt 3).
2. `req.status = "approved"`, `req.decided_by = approver`, `req.decided_at = timezone.now()`, `req.save()`.
3. Prüfung über **alle** `ApprovalRequest`-Zeilen derselben Order: kein `pending`, kein `rejected` mehr vorhanden.
4. Trifft das zu: `order.status = OrderStatus.APPROVED`, `order.save()`.

**Wichtig, am Code geprüft:** Schritt 4 ruft `StatusMachine.validate_transition`
**nicht** auf — anders als `create_approval_requests` (Schritt 5 oben) und
`OrderService.submit_order`. Der Statuswechsel wird direkt zugewiesen. Das ist
kein Style-Detail: Es bedeutet, ein künftiger Aufrufer könnte `approve` auf
einer Order in einem Status aufrufen, den der deklarierte Automat für diesen
Übergang gar nicht vorsieht, ohne dass der Code das bemerkt oder verhindert.
Weiter vertieft in [Kapitel 5.1 Abschnitt 5](01-statusmodell-und-uebergaenge.md).
AP-22 hat daran nichts geändert — nur das Laden und die Rollenprüfung laufen jetzt
über `_load_pending`, der Statuswechsel selbst blieb unangetastet.

## 5. `reject` — Schritt für Schritt

`ApprovalService.reject(request_id, approver, comment="")`
(`apps/approvals/services.py:100-109`):

1. `req = ApprovalService._load_pending(request_id, approver)` — gleiche Ladefunktion und
   Fehlerbehandlung wie bei `approve`, inklusive `ForbiddenError` bei zu schwacher Rolle.
2. `req.status = "rejected"`, `req.decided_by`, `req.decided_at`, `req.comment = comment`, `req.save()`.
3. `req.order.status = OrderStatus.REJECTED`, `req.order.save()` — **sofort**, ohne die übrigen Anträge derselben Order zu prüfen.

Auch hier: kein Aufruf von `validate_transition`. Anders als `approve` prüft
`reject` außerdem nicht den Zustand der anderen Anträge — ein einziger
abgelehnter Antrag reicht, um die gesamte Order auf `rejected` zu setzen
(vertieft in [Seite 3](03-ein-und-mehrstufige-genehmigung.md)).

## 6. `list_pending_requests` und `needs_approval`

`list_pending_requests()` (`services.py:111-118`) ist eine reine Leseoperation:
`ApprovalRequest.objects.filter(status="pending").select_related("order", "rule")`.
`needs_approval(order_id)` (`services.py:15-24`) führt dieselbe
Template/`is_active`-Prüfung wie `create_approval_requests` aus, legt aber
nichts an — reine `.exists()`-Abfrage, geeignet für einen Vorab-Check ohne
Seiteneffekt. Beide Methoden gehen nicht über `_load_pending` — sie betreffen
keine einzelne, bereits existierende Entscheidung.

## 7. Aufrufkette aus den Views

`approvals/urls.py:7-19` bindet drei Pfade an drei Views:

| URL-Name | View | Methode | Ruft auf |
|---|---|---|---|
| `approvals:queue` | `ApprovalQueueView` (`views.py:14-30`) | `get_queryset` | direktes ORM, kein Service |
| `approvals:approve` | `ApprovalApproveView.post` (`views.py:33-40`) | `ApprovalService.approve(pk, request.user)` | fängt `ConflictError`/`ForbiddenError`/`NotFoundError`, zeigt Django-Message |
| `approvals:reject` | `ApprovalRejectView.post` (`views.py:43-55`) | validiert zuerst `RejectionForm(request.POST)` (Kapitel 6.5), dann `ApprovalService.reject(pk, request.user, comment=...)` | gleiche Fehlerbehandlung, zusätzlich ein früher Redirect bei ungültigem Formular |

Beide Views leiten nach der Entscheidung auf `approvals:queue` um
(`views.py:40`, `:55`) — unabhängig davon, ob die Aktion erfolgreich war oder
eine der drei Ausnahmen (`ConflictError`, `ForbiddenError`, `NotFoundError`)
auftrat. `ApprovalRejectView` hat seit AP-22 zusätzlich einen frühen Redirect
(`views.py:48`), wenn `RejectionForm` den Kommentar ablehnt — dieser Fall
erreicht `ApprovalService.reject` gar nicht erst.

## 8. Fehlerbehandlung

`NotFoundError` (`core/exceptions.py:16-17`), `ConflictError`
(`exceptions.py:20-21`) und `ForbiddenError` (`exceptions.py:24-25`, seit AP-22)
sind alle drei Unterklassen von `ServiceError` (`exceptions.py:4-9`) mit
`.message`. Die Views fangen genau diese drei Typen ab; jede andere Ausnahme aus
dem Service (z. B. ein Programmierfehler) würde ungefangen als 500
durchschlagen.

## 9. Zusammenfassung

`create_approval_requests`, `_load_pending`, `approve` und `reject` sind klar
strukturierte, kurze Methoden mit sauberer Fehlerbehandlung über
`NotFoundError`/`ConflictError`/`ForbiddenError`. Seit AP-22 laufen `approve` und
`reject` beide zuerst durch `_load_pending`, das zusätzlich zum `pending`-Status
die Rolle des Entscheiders gegen `rule.approver_role` prüft. Unverändert bleibt
der belegte Mangel: `approve` und `reject` setzen `order.status` direkt und ohne
`StatusMachine.validate_transition` — im Unterschied zu
`create_approval_requests` selbst und zu `OrderService.submit_order`. Das ist
Teil des in AP-13 (`todo.md`) benannten Befunds und wird durch diese Seite nicht
behoben, nur präzise verortet.

> Quelle: cmp/apps/approvals/services.py, cmp/apps/approvals/models.py, cmp/apps/approvals/migrations/0002_alter_approvalrule_approver_role.py, cmp/apps/approvals/views.py, cmp/apps/approvals/urls.py, cmp/apps/approvals/forms.py, cmp/apps/accounts/services.py, cmp/core/exceptions.py, cmp/core/domain/value_objects.py, todo.md (AP-13) — am Code geprüft 2026-07-22
