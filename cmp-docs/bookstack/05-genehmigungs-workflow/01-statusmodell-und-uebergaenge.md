# Statusmodell und Übergänge

Der gesamte Lebenszyklus einer Bestellung — von der ersten Anlage bis zum
Abschluss oder Abbruch — läuft über ein einziges Statusfeld auf `Order` und einen
zentralen Wächter dafür, den `StatusMachine`. Dieses Kapitel beschreibt alle neun
Statuswerte, jeden erlaubten Übergang und wer ihn im Code tatsächlich auslöst.

## 1. Ziel des Kapitels

Wer einen neuen Übergang einbaut oder einen bestehenden ändert, muss wissen: was
erlaubt der Automat, was davon setzt heute wirklich Code um — und wo beides
auseinanderfällt. Letzteres ist kein Randthema: Abschnitt 5 zeigt zwei Stellen, an
denen der reale Code vom deklarierten Automaten abweicht.

## 2. Die neun Statuswerte

`OrderStatus` (`cmp/core/domain/value_objects.py:5-14`), `models.TextChoices`:

| Wert | Konstante | Bedeutung |
|---|---|---|
| `draft` | `OrderStatus.DRAFT` | Bestellung angelegt, Positionen können noch geändert werden |
| `validated` | `OrderStatus.VALIDATED` | Zwischenschritt beim Einreichen, sofort gefolgt von `submitted` |
| `submitted` | `OrderStatus.SUBMITTED` | Eingereicht, wartet auf Genehmigungsprüfung |
| `pending_approval` | `OrderStatus.PENDING_APPROVAL` | Mindestens ein `ApprovalRequest` ist offen |
| `approved` | `OrderStatus.APPROVED` | Alle nötigen Genehmigungen liegen vor |
| `rejected` | `OrderStatus.REJECTED` | Abgelehnt — Endzustand |
| `provisioning` | `OrderStatus.PROVISIONING` | Bereitstellungs-Pipeline läuft |
| `done` | `OrderStatus.DONE` | Erfolgreich abgeschlossen — Endzustand |
| `failed` | `OrderStatus.FAILED` | Bereitstellung fehlgeschlagen — Endzustand |

`TERMINAL_STATES = {REJECTED, DONE, FAILED}` (`value_objects.py:29`) — aus diesen
drei Werten erlaubt `TRANSITIONS` keinen weiteren Übergang.

## 3. Erlaubte Übergänge — wer löst sie aus

Grundlage ist das Dict `TRANSITIONS` in `cmp/core/domain/value_objects.py:17-27`.
Geprüft wird jeder Übergang über `StatusMachine.validate_transition(from, to)`
(`value_objects.py:50-56`) — sie wirft `ValueError`, wenn der Zielstatus nicht in
der erlaubten Liste des Ausgangsstatus steht. Ob ein Aufrufer diese Prüfung
tatsächlich benutzt, ist Sache des jeweiligen Codes, nicht des Automaten selbst —
das ist entscheidend für Abschnitt 5.

| Von | Nach | Wer löst aus | Nutzt `validate_transition`? | Fundstelle |
|---|---|---|---|---|
| `draft` | `validated` | `OrderService.submit_order`, Schritt 1 | ja | `apps/orders/services.py:70-72` |
| `validated` | `submitted` | `OrderService.submit_order`, Schritt 2 | ja | `apps/orders/services.py:73-75` |
| `submitted` | `pending_approval` | `ApprovalService.create_approval_requests`, wenn mindestens ein Antrag entsteht | ja | `apps/approvals/services.py:40-45` |
| `submitted` | `approved` | vom Automaten erlaubt, aber **von keinem Code ausgeführt** (Details: Abschnitt 5) | — | `core/domain/value_objects.py:20` (nur im Dict) |
| `pending_approval` | `approved` | `ApprovalService.approve`, wenn kein Antrag mehr `pending` oder `rejected` ist | **nein** | `apps/approvals/services.py:71-72` |
| `pending_approval` | `rejected` | `ApprovalService.reject` | **nein** | `apps/approvals/services.py:92-93` |
| `approved` | `provisioning` | `ProvisioningService.dispatch_order` | ja | `apps/provisioning/services.py:22-24` |
| `provisioning` | `done` | `ProvisioningService.complete_dispatch`, wenn kein `DispatchLog` fehlgeschlagen ist | nein | `apps/provisioning/services.py:63-67` |
| `provisioning` | `failed` | `ProvisioningService.complete_dispatch`, wenn mindestens ein `DispatchLog` fehlgeschlagen ist | nein | `apps/provisioning/services.py:63-67` |

## 4. ASCII-Skizze

```
DRAFT
  -> VALIDATED
       -> SUBMITTED
            +-> PENDING_APPROVAL
            |     +-> APPROVED -> PROVISIONING -> DONE     [Ende]
            |     |                            -> FAILED   [Ende]
            |     +-> REJECTED                             [Ende]
            +-> APPROVED   (lt. TRANSITIONS erlaubt, aber nie ausgefuehrt -- s. Abschnitt 5)
```

## 5. Wo der Automat mehr erlaubt als der Code nutzt

Zwei Befunde, per `grep` gegen den echten Code geprüft (Stand 2026-07-22):

**`submitted → approved` ist deklariert, aber tot.** `grep -rn "OrderStatus.APPROVED"
cmp --include=*.py` findet den Wert nur in drei Dateien: dreimal im
`TRANSITIONS`-Dict selbst (`value_objects.py:20-22`), als Statusprüfung in
`ProvisioningService.dispatch_order` (`provisioning/services.py:18`) und als
Zuweisung in `ApprovalService.approve` (`approvals/services.py:71`) — Letztere
kommt aber ausschließlich von `pending_approval`, nie direkt von `submitted`. Der
im `todo.md` unter AP-13 skizzierte Soll-Weg — eine Bestellung ohne passende
`ApprovalRule` sollte direkt `submitted → approved` überspringen — ist damit im
Automaten vorbereitet, aber in keinem Service umgesetzt. `create_approval_requests`
setzt bei null Treffern gar keinen neuen Status; die Order bleibt auf `submitted`
stehen (siehe [Seite 5](05-ist-stand-und-luecken.md)).

**`ApprovalService.approve`/`.reject` prüfen nicht über den Automaten.** Beide
Methoden weisen `order.status` direkt zu (`approvals/services.py:71`, `:92`) statt
vorher `StatusMachine.validate_transition` aufzurufen — anders als
`create_approval_requests`, `OrderService.submit_order` und
`ProvisioningService.dispatch_order`, die diese Prüfung nutzen. In der Praxis
bleibt das folgenlos, solange `approve`/`reject` nur von `pending_approval` aus
aufgerufen werden — der Automat würde denselben Übergang ohnehin erlauben. Es ist
aber eine Inkonsistenz im Zugriffsmuster, benannt in
[Seite 4](04-technische-umsetzung-services.md).

## 6. Zusammenfassung

Neun Statuswerte, acht deklarierte Übergänge, drei Endzustände. Sechs der acht
Übergänge werden von genau einer Service-Methode ausgelöst und dabei über
`StatusMachine.validate_transition` geprüft. Zwei Abweichungen sind belegt: der
Übergang `submitted → approved` existiert nur im Dict, ohne einen einzigen
Aufrufer, und `ApprovalService.approve`/`.reject` setzen den Order-Status direkt,
ohne die Prüfung zu nutzen, die sonst überall im Bestellfluss verwendet wird.

> Quelle: cmp/core/domain/value_objects.py, cmp/apps/orders/services.py, cmp/apps/approvals/services.py, cmp/apps/provisioning/services.py, todo.md (AP-13) — am Code geprüft 2026-07-22
