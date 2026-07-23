# AP-13 — Bestellkette verdrahten (Design)

**Datum:** 2026-07-23
**Status:** freigegeben (Brainstorming), bereit für Implementierungsplanung
**Vorgänger-Analyse:** `analyse/analyse-bestellportal.md` §1c, §5
**Quelle Arbeitspaket:** `todo.md` → AP-13

## Problem

Alle Bausteine der Kette „eingereicht → genehmigt → provisioniert → fertig →
Subscription → Audit → Benachrichtigung" existieren, sind getestet und funktionieren
einzeln — **aber niemand ruft sie aus dem laufenden Code auf.** Grep-belegt am Ist-Stand:

- `OrderService.submit_order` endet bei `SUBMITTED`. `ApprovalService.create_approval_requests`
  wird in `cmp/` nirgends aufgerufen → es entsteht kein `ApprovalRequest`, die Genehmiger-Queue
  bleibt leer. Eine über die Oberfläche eingereichte Bestellung erreicht **keinen Genehmiger**.
- `dispatch_provisioning` / `complete_provisioning` (Celery) werden von niemandem aufgerufen.
- `SubscriptionService.create_from_order` wird nie aufgerufen.
- `AuditService.log` und `NotificationService.create` nur aus `seed.py` → Audit-Log und
  Benachrichtigungs-Glocke zeigen im Betrieb **ausschließlich Seed-Demodaten**.

Zusätzlich setzen `submit_order`, `ApprovalService.approve/reject` und der
`ProvisioningService` `order.status` **direkt** und umgehen damit teils
`validate_transition`.

## Ziel

Die sechs fehlenden Aufrufe verdrahten, jeden Statuswechsel über einen zentralen
Übergang leiten (der zugleich das Audit-Log füllt), und die Kette per E2E-Test
**durch die Views** absichern.

## Architektur & Grenzen

### Zentraler Übergang: `apps/orders/transitions.py`

Neue Funktion:

```python
def transition(order, to_status, actor, **details):
    # 1. StatusMachine.validate_transition(order.status, to_status)   (core.domain, rein)
    # 2. from_status merken; order.status = to_status; order.save()
    # 3. AuditService.log(actor, f"order.{to_status}", "order", order.pk,
    #                      details={"from": from_status, **details})
```

- **Einziger erlaubter Ort für `order.status = …`.** Alle heutigen direkten Zuweisungen
  in orders/approvals/provisioning-Services werden hierauf umgestellt.
- **`StatusMachine` bleibt unverändert rein** in `core/domain/value_objects.py`
  (nur die Übergangstabelle + Prüfung, keine App-Abhängigkeit).

### Warum `apps/orders/` statt `core/domain/` (Abweichung von der Spec)

Die ursprüngliche Arbeitspaket-Notiz nennt `core/domain/transitions.py`. Das würde die
Architekturregel **`core/ → apps/ (nicht umgekehrt)`** brechen, weil `transition()`
`AuditService` (aus `apps.audit`) aufruft. Ein Domain-Modul, das einen App-Service
importiert, dreht genau diese Abhängigkeit um.

**Entscheidung:** Der Orchestrator wohnt in `apps/orders/transitions.py` (Order ist der
Aggregate-Root des Übergangs). `apps → apps` und `apps → core` sind beide erlaubt →
keine Regelverletzung. Die reine Regeltabelle (`StatusMachine`) bleibt in `core/domain`.

### Benachrichtigungen bleiben am Aufrufort

`transition()` schreibt **nur** Audit, **keine** Benachrichtigungen. Empfänger und Text
sind je Übergang verschieden (Genehmiger vs. Besteller, unterschiedliche Kategorien) und
bleiben deshalb an der jeweiligen Aufrufstelle in den Services.

### Audit-Konvention

- `action` = `f"order.{to_status}"` (z. B. `order.approved`, `order.pending_approval`, `order.done`).
- `resource_type` = `"order"`, `resource_id` = `order.pk`.
- `details` = `{"from": <from_status>, …}` plus aufrufspezifischer Kontext.

## Zustandsfluss durch die sechs Lücken

```
submit_order(order_id, actor)                      [actor = Besteller]
  DRAFT →(t) VALIDATED →(t) SUBMITTED
  needs_approval? ──ja──▶ create_approval_requests: SUBMITTED →(t) PENDING_APPROVAL
                  └─nein─▶ SUBMITTED →(t) APPROVED   (Übergang bereits in TRANSITIONS erlaubt)
  ▶ Lücke 6: bei PENDING_APPROVAL → berechtigte Genehmiger benachrichtigen

approve(request_id, approver)                      [actor = Genehmiger]
  letzter offener Request genehmigt: PENDING_APPROVAL →(t) APPROVED
  ▶ transaction.on_commit(lambda: dispatch_provisioning.delay(order.pk))
  ▶ Lücke 6: Besteller „genehmigt" benachrichtigen

dispatch_order (Celery-Task)  APPROVED →(t) PROVISIONING    [actor = None/System]
complete_dispatch (Stub schließt sofort ab)                 [actor = None/System]
  alle DispatchLogs fertig: PROVISIONING →(t) DONE | FAILED
  ▶ Lücke 4: bei DONE → SubscriptionService.create_from_order(order_id)
  ▶ Lücke 6: Besteller „fertig" (success) / „fehlgeschlagen" (error) benachrichtigen

reject(request_id, approver, comment)              [actor = Genehmiger]
  PENDING_APPROVAL →(t) REJECTED
  ▶ Lücke 6: Besteller „abgelehnt" (warning) benachrichtigen
```

## Die sechs Lücken (Umsetzungsdetail)

| # | Aufruf | Ort | actor |
|---|--------|-----|-------|
| 1 | `create_approval_requests` bzw. Auto-Approve `SUBMITTED → APPROVED` | Ende `OrderService.submit_order` | Besteller |
| 2 | `transaction.on_commit(dispatch_provisioning.delay)` | Ende `ApprovalService.approve`, wenn alle Requests genehmigt | Genehmiger |
| 3 | Rückmeldung → `complete_dispatch` | Stub schließt sofort ab (echter Rückkanal: AP-20) | None/System |
| 4 | `SubscriptionService.create_from_order` | Übergang nach `DONE` in `complete_dispatch` | None/System |
| 5 | `approve`/`reject` auf `transition()` umstellen | statt direktem `order.status =` | Genehmiger |
| 6 | `NotificationService.create` | eingereicht→Genehmiger · entschieden/fertig/fehlgeschlagen→Besteller | — |

### Zwei Fallstricke (aus der Analyse)

1. **`transaction.on_commit`** — der Celery-Start muss in `on_commit`, sonst läuft der Task
   vor dem Commit und findet die Order nicht (in dev/test durch `CELERY_TASK_ALWAYS_EAGER`
   sonst unsichtbar).
2. **Auto-Approve** — `SUBMITTED → APPROVED` (ohne matchende Regel) ist in `TRANSITIONS`
   bereits erlaubt (`core/domain/value_objects.py`), wird heute aber nirgends genutzt.

## Signatur-Änderungen (Actor-Threading)

Damit das Audit-Log den Handelnden kennt:

- `OrderService.submit_order(order_id)` → **`(order_id, actor)`**; `OrderSubmitView` reicht `request.user`.
- `ApprovalService.create_approval_requests(order_id)` → **`(order_id, actor)`** (actor = Besteller aus dem submit-Fluss).
- `ApprovalService.approve/reject` haben `approver` bereits.
- `ProvisioningService.dispatch_order` / `complete_dispatch`: **actor = `None`** (System-Übergang).
  `AuditService.log` erlaubt `user=None`.

## Benachrichtigungen (Lücke 6)

- **Genehmiger** (Order erreicht `PENDING_APPROVAL`): neuer Helper
  `AccountService.list_users_with_min_role(role)` liefert je matchender Regel die berechtigten
  User (Pull-Queue-Modell — es gibt keine Einzel-Zuweisung); an jeden
  `NotificationService.create(user, "Neue Genehmigung", …, category="info")`.
  Bei Auto-Approve (keine Regel greift) entfällt diese Benachrichtigung.
- **Besteller** (`order.user`):
  - genehmigt → `category="success"`
  - abgelehnt → `category="warning"` (mit Kommentar)
  - fertig (`DONE`) → `category="success"`
  - fehlgeschlagen (`FAILED`) → `category="error"`

## Wächter-Test

`test_no_direct_status_assignment` — AST-Scan über `apps/` + `core/`: sucht
Attribut-Zuweisungen an `*.status` auf Order-artigen Zielen (`order.status =`,
`req.order.status =`, `log.order_item.order.status =` …) und schlägt fehl, wenn eine
außerhalb `apps/orders/transitions.py` liegt. Verhindert das Zurückschleichen des Umwegs.
Wird per Fehlerinjektion belegt (eine bewusst wieder direkt gesetzte Zuweisung muss den
Test rot machen).

## Test-Strategie & Definition of Done

- **TDD ist Pflicht:** je Lücke zuerst ein roter Test; Wächter-Test per Fehlerinjektion belegt.
- **`on_commit`-Falle in Tests:** `transaction.on_commit`-Callbacks feuern nur mit
  `django_db(transaction=True)` bzw. `captureOnCommitCallbacks`. Der E2E-Test nutzt das
  explizit, sonst läuft die Kette scheinbar nie über `APPROVED` hinaus.
- **E2E durch die Views (DoD):** `POST orders:submit` → Queue enthält den Request →
  `POST approvals:approve` → Order `DONE`, Subscription existiert, Audit-Log gefüllt,
  Besteller benachrichtigt. **Kein direkter Service-Aufruf im Testkörper.**
- Wächter-Test grün.

## Bewusst außerhalb des Scopes (YAGNI)

- **AP-14** Logging-Fundament — Voraussetzung, um die Kette im Betrieb zu beobachten, aber eigenes AP.
- **AP-18** E-Mail-Versand — braucht die hier gelieferten Auslösepunkte, eigenes AP.
- **AP-20** echter GitLab-Client statt Stub + echter Rückkanal (Polling) — ersetzt später das
  Sofort-Abschließen aus Lücke 3.

## Betroffene Dateien (Erwartung)

- **neu:** `apps/orders/transitions.py`
- **geändert:** `apps/orders/services.py`, `apps/approvals/services.py`,
  `apps/provisioning/services.py`, `apps/accounts/services.py` (neuer Rollen-Helper),
  `apps/orders/views.py` (actor-Threading), ggf. `apps/approvals/views.py`
- **unverändert:** `core/domain/value_objects.py` (StatusMachine bleibt rein)
- **Tests:** je Lücke + Wächter-Test + E2E-Durchstich
