# Technische Umsetzung — ApprovalService

`ApprovalService` bündelt die gesamte Genehmigungslogik als vier statische
Methoden. Dieses Kapitel geht `approve` und `reject` Schritt für Schritt durch,
inklusive Aufrufkette aus den Views — und benennt eine Stelle, an der beide
Methoden bewusst anders arbeiten als der Rest des Bestellflusses.

## 1. Ziel des Kapitels

Wer eine Genehmigungsentscheidung debuggt oder die Methoden erweitert, muss die
genaue Reihenfolge der Schritte kennen — insbesondere, welche Prüfung
`StatusMachine.validate_transition` durchläuft und welche nicht.

## 2. `create_approval_requests` — Schritt für Schritt

`ApprovalService.create_approval_requests(order_id)` (`apps/approvals/services.py:24-46`):

1. `OrderService.get_order(order_id)` lädt die Bestellung oder wirft `NotFoundError`.
2. `order.items.values_list("template_id", flat=True).distinct()` ermittelt die betroffenen Templates.
3. `ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True)` liefert alle passenden Regeln.
4. Für **jede** Regel: `ApprovalRequest.objects.create(order=order, rule=rule, status="pending")`.
5. Nur wenn mindestens ein Antrag entstanden ist: `StatusMachine.validate_transition(order.status, PENDING_APPROVAL)`, dann `order.status = PENDING_APPROVAL`, `order.save()`.
6. Rückgabe: Liste der erzeugten `ApprovalRequest`-Objekte (leer, wenn keine Regel passte).

## 3. `approve` — Schritt für Schritt

`ApprovalService.approve(request_id, approver)` (`apps/approvals/services.py:48-72`):

1. `ApprovalRequest.objects.select_related("order").get(pk=request_id)` — sonst `NotFoundError`.
2. Wenn `req.status != "pending"`: `ConflictError(f"Request already decided: {req.status}")`.
3. `req.status = "approved"`, `req.decided_by = approver`, `req.decided_at = timezone.now()`, `req.save()`.
4. Prüfung über **alle** `ApprovalRequest`-Zeilen derselben Order: kein `pending`, kein `rejected` mehr vorhanden.
5. Trifft das zu: `order.status = OrderStatus.APPROVED`, `order.save()`.

**Wichtig, am Code geprüft:** Schritt 5 ruft `StatusMachine.validate_transition`
**nicht** auf — anders als `create_approval_requests` (Schritt 5 oben) und
`OrderService.submit_order`. Der Statuswechsel wird direkt zugewiesen. Das ist
kein Style-Detail: Es bedeutet, ein künftiger Aufrufer könnte `approve` auf
einer Order in einem Status aufrufen, den der deklarierte Automat für diesen
Übergang gar nicht vorsieht, ohne dass der Code das bemerkt oder verhindert.
Weiter vertieft in [Kapitel 5.1 Abschnitt 5](01-statusmodell-und-uebergaenge.md).

## 4. `reject` — Schritt für Schritt

`ApprovalService.reject(request_id, approver, comment="")`
(`apps/approvals/services.py:74-93`):

1. Laden wie bei `approve`, gleiche Fehlerbehandlung.
2. Wenn `req.status != "pending"`: `ConflictError`.
3. `req.status = "rejected"`, `req.decided_by`, `req.decided_at`, `req.comment = comment`, `req.save()`.
4. `req.order.status = OrderStatus.REJECTED`, `req.order.save()` — **sofort**, ohne die übrigen Anträge derselben Order zu prüfen.

Auch hier: kein Aufruf von `validate_transition`. Anders als `approve` prüft
`reject` außerdem nicht den Zustand der anderen Anträge — ein einziger
abgelehnter Antrag reicht, um die gesamte Order auf `rejected` zu setzen
(vertieft in [Seite 3](03-ein-und-mehrstufige-genehmigung.md)).

## 5. `list_pending_requests` und `needs_approval`

`list_pending_requests()` (`services.py:95-102`) ist eine reine Leseoperation:
`ApprovalRequest.objects.filter(status="pending").select_related("order", "rule")`.
`needs_approval(order_id)` (`services.py:13-22`) führt dieselbe
Template/`is_active`-Prüfung wie `create_approval_requests` aus, legt aber
nichts an — reine `.exists()`-Abfrage, geeignet für einen Vorab-Check ohne
Seiteneffekt.

## 6. Aufrufkette aus den Views

`approvals/urls.py:7-19` bindet drei Pfade an drei Views:

| URL-Name | View | Methode | Ruft auf |
|---|---|---|---|
| `approvals:queue` | `ApprovalQueueView` (`views.py:12-28`) | `get_queryset` | direktes ORM, kein Service |
| `approvals:approve` | `ApprovalApproveView.post` (`views.py:31-38`) | `ApprovalService.approve(pk, request.user)` | fängt `ConflictError`/`NotFoundError`, zeigt Django-Message |
| `approvals:reject` | `ApprovalRejectView.post` (`views.py:41-49`) | `ApprovalService.reject(pk, request.user, comment=...)` | gleiche Fehlerbehandlung |

Beide Views leiten nach der Entscheidung auf `approvals:queue` um
(`views.py:38`, `:49`) — unabhängig davon, ob die Aktion erfolgreich war oder
eine der beiden Ausnahmen auftrat.

## 7. Fehlerbehandlung

`NotFoundError` (`core/exceptions.py:16-17`) und `ConflictError`
(`exceptions.py:20-21`) sind beide Unterklassen von `ServiceError`
(`exceptions.py:4-9`) mit `.message`.
Die Views fangen genau diese zwei Typen ab; jede andere Ausnahme aus dem Service
(z. B. ein Programmierfehler) würde ungefangen als 500 durchschlagen.

## 8. Zusammenfassung

`create_approval_requests`, `approve` und `reject` sind klar strukturierte,
kurze Methoden mit sauberer Fehlerbehandlung über `NotFoundError`/
`ConflictError`. Der belegte Mangel: `approve` und `reject` setzen
`order.status` direkt und ohne `StatusMachine.validate_transition` — im
Unterschied zu `create_approval_requests` selbst und zu
`OrderService.submit_order`. Das ist Teil des in AP-13 (`todo.md`) benannten
Befunds und wird durch diese Seite nicht behoben, nur präzise verortet.

> Quelle: cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/approvals/urls.py, cmp/core/exceptions.py, cmp/core/domain/value_objects.py, todo.md (AP-13) — am Code geprüft 2026-07-22
