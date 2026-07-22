# Genehmigung: ApprovalRule und ApprovalRequest

`ApprovalRule` legt fest, dass Bestellungen mit einem bestimmten Template eine
Genehmigung brauchen. `ApprovalRequest` ist die einzelne Entscheidung dazu. Dieses
Kapitel dokumentiert beide Modelle und benennt ehrlich, welcher Teil der Kette
aktuell verdrahtet ist und welcher nicht (AP-13).

## 1. Ziel des Kapitels

Wer die Genehmigungslogik ändert oder erweitert, muss wissen, welche Felder real
existieren, wie ein Antrag heute entsteht — und an welcher Stelle die Kette
zwischen Bestellung und Genehmigung tatsächlich abreißt.

## 2. Feldreferenz ApprovalRule

`cmp/apps/approvals/models.py:7`, Tabelle `approval_rules`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `template` | `ForeignKey → service_templates`, `on_delete=CASCADE` | Für welches Template (`related_name="approval_rules"`) |
| `condition` | `JSONField`, default `dict` | Zusatzbedingung — siehe Abschnitt 5 |
| `approver_role` | `CharField(20)`, default `"approver"` | Freitext-Rolle, kein `choices=` |
| `is_active` | `BooleanField`, default `True` | Regel aktiv |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

## 3. Feldreferenz ApprovalRequest

`cmp/apps/approvals/models.py:26`, Tabelle `approval_requests`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `order` | `ForeignKey → orders`, `on_delete=CASCADE` | Betroffene Bestellung (`related_name="approval_requests"`) |
| `rule` | `ForeignKey → approval_rules`, `on_delete=CASCADE` | Auslösende Regel |
| `status` | `CharField(20)`, default `"pending"` | `pending`, `approved`, `rejected` — Freitext, kein `choices=` |
| `decided_by` | `ForeignKey → users`, nullable, `on_delete=SET_NULL` | Entscheider |
| `decided_at` | `DateTimeField`, nullable | Entscheidungszeitpunkt |
| `comment` | `TextField`, blank | Kommentar (nur bei Ablehnung befüllt) |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`Meta.ordering = ["-created_at"]`.

## 4. Wie `ApprovalService` einen Antrag erzeugt

`ApprovalService.create_approval_requests(order_id)`
(`cmp/apps/approvals/services.py:25`) sammelt alle `ApprovalRule`-Zeilen mit
`is_active=True`, deren `template_id` unter den Templates der Bestellpositionen
vorkommt, und legt für **jede** passende Regel einen `ApprovalRequest` mit
`status="pending"` an. Gibt es mindestens einen Antrag, schaltet die Methode die
Order von `submitted` auf `pending_approval`
(`StatusMachine.validate_transition`). `ApprovalService.needs_approval(order_id)`
prüft dieselbe Bedingung nur lesend (`exists()`), ohne etwas anzulegen.

## 5. Was `condition` bewirkt — ehrlich geprüft

Das Feld `condition` wird angelegt und in der Seed-Fixture stets mit `{}` befüllt
(`cmp/apps/accounts/management/commands/seed.py:44`), aber **an keiner Stelle im
Code gelesen oder ausgewertet** (`grep -rn "\.condition" cmp/apps` findet außer der
Modell-Definition keine weitere Fundstelle). `create_approval_requests()` prüft nur
`template_id` und `is_active` — nicht `condition`. Das Feld ist heute reine
Vorbereitung für eine spätere, feinere Regel-Auswertung (z. B. "nur ab min_cpu"),
nicht aktiv wirksam.

## 6. Der reale Bruch: Wer ruft `create_approval_requests()` auf?

**Niemand außer der eigenen Definition.** Eine projektweite Suche
(`grep -rn "create_approval_requests" cmp/apps`, Stand 2026-07-22) findet die
Methode nur in `apps/approvals/services.py` selbst — kein View, kein Signal, kein
Celery-Task ruft sie auf. `OrderService.submit_order()`
(`cmp/apps/orders/services.py:61`) bringt eine Order bis `submitted` und stoppt
dort; nichts im Anwendungscode prüft danach `needs_approval()` oder erzeugt
Genehmigungsanträge automatisch.

Auch `ApprovalService.approve()`/`reject()` — aufgerufen aus
`cmp/apps/approvals/views.py:34` und `:45` über die Genehmigungs-Queue — setzen nur
den Status der bereits existierenden `ApprovalRequest` und ggf. der `Order`
(`approved`/`rejected`). Sie erzeugen selbst keine neuen Anträge und stoßen auch
kein Provisioning an (siehe [Kapitel 3.5](05-provisioning-und-subscription.md)).

Die einzige Stelle, an der heute `ApprovalRequest`-Zeilen für Demo-Bestellungen
entstehen, ist das Management-Command `seed.py`
(`cmp/apps/accounts/management/commands/seed.py:178`, `:349`) — und dort **direkt**
über `ApprovalRequest.objects.create(...)`, nicht über
`ApprovalService.create_approval_requests()`. Der Service-Pfad selbst ist im
laufenden Betrieb ungenutzt; das ist der in AP-13 benannte Lückenteil an dieser
Stelle der Bestellkette.

## 7. Zusammenfassung

`ApprovalRule` und `ApprovalRequest` sind vollständig modelliert, und
`ApprovalService` kann Anträge korrekt erzeugen und entscheiden — geprüft per
Unit-Test-fähigem Service-Aufruf. Was fehlt, ist die Verdrahtung: Kein Aufrufer im
Request- oder Task-Pfad ruft `create_approval_requests()` nach dem Einreichen einer
Bestellung auf. Das Feld `condition` existiert, wird aber nirgends ausgewertet.

> Quelle: cmp/apps/approvals/models.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/orders/services.py, cmp/apps/accounts/management/commands/seed.py — am Code geprüft 2026-07-22
