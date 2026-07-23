# Eine spät zentralisierte Invariante entlarvt Tests, deren Setup nie real war

**Session 11 · 2026-07-23 · v1.4.0 → v1.5.0 · AP-13 (Bestellkette verdrahten)**

## Der Moment

AP-13 hat jeden Order-Statuswechsel über einen zentralen `transition()` geleitet, der
den Übergang **prüft** (`StatusMachine.validate_transition`). Vorher setzten
`approve`/`reject`/`submit` `order.status` **direkt** — ohne Prüfung. Nach dem Umbau
brach ein Test, der mit dem Feature nichts zu tun hatte: `TestGenehmigerRolle` in
`test_object_access.py` (die AP-22-Zugriffskontrolle) fiel mit
`ValueError: Invalid transition: draft → approved`.

Der Reflex wäre gewesen, den Übergang zu lockern oder den Test „anzupassen, damit er
wieder grün ist". Beides falsch. Der Blick ins Setup zeigte die eigentliche Ursache:

```python
ApprovalRequest.objects.create(
    order=OrderFactory(user=UserFactory()),   # Status: DRAFT (Default)
    rule=rule, status="pending"
)
```

Eine Anfrage im Status `pending` an einer Bestellung im Status `DRAFT` — **das ist ein
Zustand, den es im Betrieb nie gibt.** Eine offene Genehmigungsanfrage impliziert eine
Bestellung in `PENDING_APPROVAL`. Das alte, ungeprüfte `order.status = APPROVED`
tolerierte das unmögliche Setup stillschweigend; `transition()` erzwingt die Invariante
und macht es sichtbar. Der Fix war das Setup, nicht die Invariante:
`OrderFactory(status=OrderStatus.PENDING_APPROVAL)`.

## Die Lektion

**Wenn du eine Invariante nachträglich zentralisierst, budgetiere für die Alt-Tests,
die sie stillschweigend verletzt haben — und behandle jeden Bruch als Frage „war dieser
Zustand je real?", nicht als „wie kriege ich den Test wieder grün?".**

Ein Test kann über die richtige Sache das Richtige behaupten (hier: welche Rolle
genehmigen darf) und trotzdem von einem unmöglichen Ausgangszustand aus starten. Solange
kein Code die Invariante durchsetzt, fällt das nie auf — die grüne Farbe ist echt, der
Zustand ist erfunden. Erst der Wächter (`transition()` + der AST-Test gegen direkte
`order.status`-Zuweisung) trennt „sieht richtig aus" von „ist ein realer Ablauf".

Das ist dieselbe Kraft wie in Session 10 (Handbuch-Schreiben findet Code-Fehler) und
Session 8 (grep-Beleg findet die fehlende Verdrahtung), nur aus der anderen Richtung:
dort deckte das Lesen ohne Erwartung Fehler auf, hier deckt das **Erzwingen einer Regel**
auf, wo bisher gegen sie verstoßen wurde — im Produktionscode *und* in den Fixtures.

## Nebenbefund: der Plan selbst hatte den Fehler auch

Der erste Subagent (Task 1) fand einen Defekt in **meinem eigenen Plan**: ein Testfall
behauptete den Übergang `SUBMITTED → REJECTED` — den es in der `StatusMachine` gar nicht
gibt (`REJECTED` ist nur aus `PENDING_APPROVAL` erreichbar). Der Plan ist ein Zielbild,
keine Grundwahrheit — auch nicht der selbst geschriebene. Die zweistufige SDD-Prüfung
(Implementer stellt Rückfrage → Controller entscheidet) fing es vor dem ersten Commit ab.
Lehre: derselbe Zustandsautomat, der die Tests bricht, hätte den Plan-Testfall von Anfang
an widerlegt — hätte ich ihn beim Plan-Schreiben gegen `TRANSITIONS` geprüft statt aus
dem Kopf zu schreiben.
