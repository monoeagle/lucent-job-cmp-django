# Ist-Stand und Lücken

Alle Bausteine des Genehmigungs-Workflows existieren und sind einzeln
funktionsfähig — aber niemand im Anwendungscode ruft sie in der richtigen
Reihenfolge auf. Dieses Kapitel prüft den Ist-Stand frisch am Code (nicht aus
der Analyse übernommen) und beschreibt, was ein Nutzer heute real erlebt, wenn
er eine Bestellung einreicht.

## 1. Ziel des Kapitels

Wer den Genehmigungs-Workflow erweitert oder AP-13 umsetzt, muss den exakten
Bruchpunkt kennen — nicht „ungefähr, irgendwo nach dem Einreichen", sondern die
konkrete Methode, die heute nicht aufgerufen wird.

## 2. Soll-Ablauf, auf die Genehmigung verengt

Der vollständige Neun-Schritte-Ablauf steht in
[Kapitel 2.5](../02-architektur-und-prozesse/05-end-to-end-von-der-bestellung-zur-vm.md).
Für den Genehmigungsteil verkürzt: Bestellung einreichen
(`OrderService.submit_order`) → Genehmigungsanträge erzeugen
(`ApprovalService.create_approval_requests`) → Order wechselt zu
`pending_approval` → Genehmiger entscheidet über die Warteschlange
(`ApprovalService.approve`/`.reject`) → Order wechselt zu `approved` oder
`rejected`.

## 3. Ist-Ablauf — frisch am Code geprüft, 2026-07-22

**`OrderService.submit_order` endet bei `submitted`.** Die Methode
(`cmp/apps/orders/services.py:61-76`) führt die Übergänge `draft → validated`
und `validated → submitted` aus und gibt die Order zurück — kein Aufruf von
`ApprovalService` danach.

**`create_approval_requests` hat keinen Aufrufer im Anwendungscode.**
`grep -rn "create_approval_requests(" cmp/ --include=*.py` (erneut ausgeführt
für diese Seite) findet ausschließlich die Definition
(`apps/approvals/services.py:25`) — kein View, kein Signal, kein Celery-Task,
keine `apps.py`-Hooks. Dieselbe Prüfung für `needs_approval(` liefert nur die
eigene Definition (`services.py:14`).

**Die Warteschlange zeigt deshalb nur, was `seed.py` direkt anlegt.**
`ApprovalQueueView.get_queryset` (`apps/approvals/views.py:16-23`) filtert
`ApprovalRequest`-Objekte nach `status`. Da eine über die Oberfläche
eingereichte Bestellung nie eine solche Zeile erzeugt, bleiben dort
ausschließlich die Zeilen aus dem Management-Command
(`apps/accounts/management/commands/seed.py:178`, `:349`,
`ApprovalRequest.objects.create(...)` — direkt, nicht über den Service).

## 4. Der Beweis liegt im eigenen Test

`tests/e2e/test_order_workflow.py` demonstriert die Lücke ungewollt, aber
eindeutig: `test_complete_lifecycle_with_approval` (Zeile 60) kommentiert die
Schritte selbst durch — „1. Create + add item + submit" (Zeile 69),
„2. Check needs approval" (Zeile 74), „3. Create approval requests" (Zeile 77)
— und ruft `ApprovalService.create_approval_requests(order.pk)` **von Hand**
auf (Zeile 78), direkt im Test, nicht über einen View oder Task. Derselbe
Aufbau wiederholt sich in `test_rejected_order_workflow` (Zeilen 107-111).
`test_failed_provisioning_workflow` (Zeilen 116-127) geht noch weiter: Dort
setzt der Test `order.status = OrderStatus.APPROVED` **direkt per Zuweisung**
(Zeile 126-127), weil es keinen Ablauf gibt, der eine Order ohne manuellen
Eingriff dorthin bringt. Die 347 Tests des Projekts sind grün — sie testen die
Bausteine einzeln korrekt, nicht ihre Verkettung im Betrieb.

## 5. Was ein Nutzer heute real erlebt

Ein Nutzer füllt den Bestell-Wizard aus und klickt „Einreichen"
(`OrderSubmitView`, `apps/orders/views.py:431-440`). Die Bestellung erreicht
`submitted` — sichtbar für ihn selbst z. B. im Dashboard-Badge
`open_order_count`, das `status__in=["draft", "submitted"]` zählt
(`core/context_processors.py:21-23`): seine Bestellung bleibt dort dauerhaft
als „offen" stehen. Ein Genehmiger sieht in der Warteschlange
(`approvals:queue`) nichts Neues — `pending_approval_count`
(`context_processors.py:18-20`) und die Queue selbst zeigen ausschließlich die
`seed.py`-Demodaten. Es gibt keine Fehlermeldung, keinen sichtbaren Abbruch —
die Bestellung verschwindet einfach nicht aus dem Status „eingereicht" und
erreicht nie einen Genehmiger.

## 6. Einordnung

Der beschriebene Zustand deckt sich mit dem Befund in `todo.md`, AP-13
(„Bestellkette verdrahten", Vorrang-Arbeitspaket): „Die Bausteine existieren
und sind getestet, aber niemand ruft sie auf." Diese Seite bestätigt das am
Code, unabhängig von der Analyse vom 2026-07-21 — keine der dort getroffenen
Aussagen zur Genehmigungslücke musste korrigiert werden, sie sind am
2026-07-22 weiterhin so vorzufinden. AP-13 ist **nicht** Teil dieses Handbuchs
— dieses Kapitel beschreibt den Zustand, es schließt die Lücke nicht.

## 7. Zusammenfassung

Die Kette zwischen Bestellung und Genehmigung bricht exakt zwischen
`OrderService.submit_order` und `ApprovalService.create_approval_requests` ab:
Ersteres ruft Letzteres nirgends auf. Die Warteschlange, die Dashboard-Badges
und alle grünen Tests täuschen einen funktionierenden Ablauf vor, weil jeder
Baustein für sich getestet ist — real verdrahtet ist er nicht. Ein über die
Oberfläche eingereichter Auftrag bleibt für den Nutzer sichtbar „offen" und
erreicht nie einen Genehmiger, bis AP-13 umgesetzt ist.

> Quelle: cmp/apps/orders/services.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/accounts/management/commands/seed.py, cmp/core/context_processors.py, tests/e2e/test_order_workflow.py, todo.md (AP-13) — am Code geprüft 2026-07-22
