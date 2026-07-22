# End-to-End: von der Bestellung zur VM

Dieses Kapitel beschreibt den Weg vom Katalog-Klick bis zur laufenden Subscription —
als Soll-Ablauf mit den beteiligten Views/Services/Models je Schritt. Der wichtigste
Befund steht in Abschnitt 3: Die Kette ist heute **nicht durchgehend verdrahtet**
(Arbeitspaket AP-13). Soll und Ist werden hier bewusst getrennt beschrieben.

## 1. Ziel des Kapitels

Wer verstehen will, wie eine Bestellung fachlich durch das System läuft — und wer
zusätzlich wissen muss, ab welchem Schritt eine echte, über die Oberfläche
eingereichte Bestellung heute tatsächlich hängen bleibt.

## 2. Soll-Ablauf: neun Schritte von Katalog bis Subscription

| # | Schritt | View | Service | Model |
|---|---|---|---|---|
| 1 | Katalog durchsuchen/filtern | `TemplateListView` (`cmp/apps/catalog/views.py:12`) | `CatalogService.list_active_templates` / `.search_templates` | `ServiceTemplate` |
| 2 | Service wählen, Parameter ausfüllen (Wizard oder Einzelseite) | `OrderCreateView` bzw. `OrderFormView` (`cmp/apps/orders/views.py`) | `CatalogService.get_template` | `ServiceTemplate.parameters` (JSON) |
| 3 | Bestellung anlegen und Position hinzufügen | `OrderCreateView._submit_order` / `OrderFormView.post` | `OrderService.create_order`, `OrderService.add_item` (`cmp/apps/orders/services.py:12,30`) | `Order` (Status `draft`), `OrderItem` |
| 4 | Bestellung einreichen | `OrderSubmitView.post` (`cmp/apps/orders/views.py:433`) | `OrderService.submit_order` (`cmp/apps/orders/services.py:61-76`) | `Order.status`: `draft → validated → submitted` |
| 5 | Genehmigungsanfragen erzeugen | — (Soll: direkt im Anschluss an Schritt 4) | `ApprovalService.create_approval_requests` (`cmp/apps/approvals/services.py:25`) | `ApprovalRequest` (neu), `Order.status → pending_approval` |
| 6 | Genehmiger entscheidet | `ApprovalQueueView`, `ApprovalApproveView`/`ApprovalRejectView` (`cmp/apps/approvals/views.py:12,29,38`) | `ApprovalService.approve` / `.reject` | `ApprovalRequest.status`, `Order.status → approved` bzw. `rejected` |
| 7 | Provisioning anstoßen | — (Soll: am Ende von `approve`, sobald alle Requests genehmigt sind) | `dispatch_provisioning.delay(order.pk)` → `ProvisioningService.dispatch_order` (`cmp/apps/provisioning/services.py:15`, Celery-Task `cmp/apps/provisioning/tasks.py:8`) | `DispatchLog`, `Order.status → provisioning` |
| 8 | Rückmeldung der Pipeline | — (Soll: Callback bzw. Stub-Sofortabschluss) | `ProvisioningService.complete_dispatch` (`cmp/apps/provisioning/services.py:42`) | `Order.status → done` bzw. `failed` |
| 9 | Subscription anlegen | — (Soll: beim Übergang nach `done`) | `SubscriptionService.create_from_order` (`cmp/apps/subscriptions/services.py:14`) | `Subscription` |

Diese neun Schritte sind der fachlich vorgesehene Ablauf, wie er sich aus
Statusmaschine (`core/domain/value_objects.py`, `TRANSITIONS`-Dict:
`draft → validated → submitted → pending_approval → approved → provisioning →
done`, alternativ `→ failed`/`→ rejected`) und den vorhandenen Services ergibt.

## 3. Ist-Stand: die Kette bricht nach Schritt 4 ab

**Befund, per `grep` am Code geprüft (Stand 2026-07-22):** Schritte 1 bis 4 sind
über die Views tatsächlich erreichbar und funktionieren. Ab Schritt 5 ruft **nichts
im Anwendungscode** die nötige Methode auf:

- `grep -rn "create_approval_requests(" cmp/ --include=*.py` findet nur die
  Definition selbst (`cmp/apps/approvals/services.py:25`) — keinen einzigen
  Aufrufer außerhalb von Tests.
- `OrderService.submit_order` (`cmp/apps/orders/services.py:61-76`) endet nach dem
  Übergang zu `SUBMITTED` und ruft nichts Nachfolgendes auf.
- `ApprovalQueueView.get_queryset` (`cmp/apps/approvals/views.py:17-23`) filtert
  auf `ApprovalRequest`-Objekte. Da nie eines entsteht, zeigt die Queue
  ausschließlich die von `seed.py` erzeugten Requests
  (`cmp/apps/accounts/management/commands/seed.py:178,349`).

**Folge:** Eine über die Oberfläche eingereichte Bestellung bleibt dauerhaft im
Status `submitted` und erreicht keinen Genehmiger. `ApprovalService.approve` wird
im laufenden Betrieb nie erreicht, obwohl die Methode selbst funktioniert und
getestet ist.

Dieselbe Lücke setzt sich fort: `grep -rn "dispatch_provisioning" cmp/ --include=*.py`
findet den Celery-Task nur in seiner eigenen Datei
(`cmp/apps/provisioning/tasks.py:8`), `grep -rn "create_from_order" cmp/ --include=*.py`
findet `SubscriptionService.create_from_order` nur in seiner Definition
(`cmp/apps/subscriptions/services.py:14`). Auch `AuditService.log` und
`NotificationService.create` werden im Bestell-Workflow nirgends aufgerufen — beide
nur aus dem Seed-Kommando. Damit zeigen Audit-Log und Benachrichtigungen im
Betrieb ausschließlich Seed-Daten, keine echten Ereignisse.

Zusätzlich fällt beim Lesen von `ApprovalService.approve`/`.reject`
(`cmp/apps/approvals/services.py:47-91`) auf: Beide setzen `order.status` direkt,
ohne `StatusMachine.validate_transition` — anders als `create_approval_requests`
und `OrderService.submit_order`, die diese Prüfung nutzen.

## 4. Warum das im Alltag nicht auffällt

347 Tests sind grün, und Seed-Daten füllen Queue, Audit-Log und
Benachrichtigungen — die Oberfläche wirkt dadurch vollständig, obwohl die reale
Kette hinter dem ersten Klick abbricht. Jeder einzelne Baustein (Statusmaschine,
`ApprovalService`, Celery-Task, `SubscriptionService`) ist für sich getestet und
funktioniert bei direktem Aufruf — es fehlt ausschließlich die Verdrahtung
zwischen ihnen.

## 5. Was das für Anhang A bedeutet

Die Rezepte in Anhang A („Neuen Service anlegen") betreffen Schritte 1–4 (Katalog,
Formular, Bestellung anlegen/einreichen) — dieser Teil der Kette ist heute real
begehbar und in den Beispielen dort nachvollziehbar. Alles ab Schritt 5
(Genehmigung, Provisioning, Subscription) lässt sich derzeit nur über direkte
Service-Aufrufe in Tests demonstrieren, nicht über einen durchgängigen Klickpfad
in der Oberfläche.

## 6. Zusammenfassung

Der Soll-Ablauf umfasst neun Schritte von der Katalogsuche bis zur Subscription,
getragen von klar benannten Views, Services und Models. Real verdrahtet über die
Oberfläche sind heute nur die ersten vier Schritte — eine Bestellung erreicht
`submitted` und bleibt dort stehen, weil `create_approval_requests` nirgends
aufgerufen wird. Das schließt die gesamte Folgekette (Genehmigung, Provisioning,
Subscription, Audit, Benachrichtigung) im laufenden Betrieb faktisch aus, obwohl
jeder Baustein einzeln existiert und getestet ist. Das Schließen dieser Lücke ist
Arbeitspaket AP-13 und ausdrücklich **nicht** Teil dieses Handbuchs — dieses Kapitel
beschreibt den Zustand, es ändert ihn nicht.

> Quelle: analyse/analyse-bestellportal.md (§1c, §5), todo.md (AP-13), cmp/apps/orders/services.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/provisioning/tasks.py, cmp/apps/subscriptions/services.py — am Code geprüft 2026-07-22
