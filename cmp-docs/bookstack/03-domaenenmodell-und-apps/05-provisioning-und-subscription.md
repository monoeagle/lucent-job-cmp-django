# Provisioning und Subscription

`DispatchLog` protokolliert den Versand einer Bestellposition an die
Provisioning-Pipeline, `Subscription`/`GroupSubscription` sind die daraus
entstehenden aktiven Abos. Dieses Kapitel dokumentiert alle drei Modelle sowie den
Celery-Task- und Stub-Client-Pfad — mit demselben Ist-Stand-Anspruch wie Kapitel 3.4.

## 1. Ziel des Kapitels

Wer Provisioning oder Subscriptions anfasst, soll wissen: welche Felder es gibt,
wie ein Dispatch heute technisch funktioniert (Stub-Client, Celery-Task), und ob
er im Betrieb tatsächlich ausgelöst wird.

## 2. Feldreferenz DispatchLog

`cmp/apps/provisioning/models.py:7`, Tabelle `dispatch_logs`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `order_item` | `ForeignKey → order_items`, `on_delete=CASCADE` | Betroffene Position (`related_name="dispatch_logs"`) |
| `pipeline_id` | `CharField(100)` | ID der (simulierten) Pipeline |
| `status` | `CharField(30)`, default `"pending"` | `pending`, `running`, `success`, `failed` — Freitext |
| `payload` | `JSONField`, default `dict` | Request-Daten (Template-Name + Parameter) |
| `dispatched_at` | `DateTimeField`, `auto_now_add` | Dispatch-Zeitpunkt |
| `completed_at` | `DateTimeField`, nullable | Abschluss-Zeitpunkt |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` — **zusätzlich** zu `dispatched_at` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`DispatchLog` erbt von `TimeStampedModel` und hat dadurch `created_at` *und*
`dispatched_at` als zwei separate, beide automatisch gesetzte Zeitstempel — die
bisherige Referenzdoku nannte nur `dispatched_at`/`completed_at`.
`Meta.ordering = ["-dispatched_at"]`.

## 3. Feldreferenz Subscription

`cmp/apps/subscriptions/models.py:8`, Tabelle `subscriptions`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, `on_delete=CASCADE` | Inhaber (`related_name="subscriptions"`) |
| `order_item` | `ForeignKey → order_items`, `on_delete=CASCADE` | Ursprüngliche Position (`related_name="subscriptions"`) |
| `status` | `CharField(30)`, default `"active"` | `active`, `cancelled` — Freitext |
| `valid_from` | `DateTimeField`, `auto_now_add` | Gültig ab |
| `valid_until` | `DateTimeField`, nullable | Gültig bis (bei Kündigung gesetzt) |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

## 4. Feldreferenz GroupSubscription

`cmp/apps/subscriptions/models.py:33`, Tabelle `group_subscriptions`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, `on_delete=CASCADE` | Inhaber (`related_name="group_subscriptions"`) |
| `order_item_group` | `ForeignKey → order_item_groups`, `on_delete=CASCADE` | Ursprüngliche Gruppe (`related_name="subscriptions"`) |
| `status` | `CharField(30)`, default `"active"` | `active`, `cancelled` |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

Anders als `Subscription` hat `GroupSubscription` **kein** eigenes
`valid_from`/`valid_until`-Feld.

## 5. Der Dispatch-Pfad: Stub-Client und Service

`ProvisioningService.dispatch_order(order_id)` (`cmp/apps/provisioning/services.py:14`)
verlangt eine Order im Status `approved`, schaltet sie auf `provisioning` und ruft
für jede Position `GitLabStubClient.trigger_pipeline()`
(`cmp/apps/provisioning/clients.py`) auf. Der Stub-Client hält Pipelines nur
in-memory (`dict`), vergibt eine zufällige `pipeline_id` (`uuid4().hex[:12]`) und
setzt sie sofort auf `"running"` — es gibt keine echte GitLab-Anbindung.
Für jede Position entsteht ein `DispatchLog` mit `status="running"`.

`ProvisioningService.complete_dispatch(dispatch_log_id, success)` markiert einen
`DispatchLog` als `success`/`failed`; sind alle Logs einer Order abgeschlossen,
setzt sie die Order auf `done` (kein Log `failed`) oder `failed` (mindestens ein
Log `failed`).

## 6. Celery-Tasks — definiert, aber nicht verdrahtet

`cmp/apps/provisioning/tasks.py` definiert zwei `@shared_task`-Funktionen,
`dispatch_provisioning(order_id)` und `complete_provisioning(dispatch_log_id, success)`,
die jeweils nur den zugehörigen `ProvisioningService`-Aufruf weiterreichen. Eine
projektweite Suche nach asynchronen Aufrufen
(`grep -rn "\.delay(\|apply_async(" cmp/apps`, Stand 2026-07-22) liefert **keinen
Treffer**. Die Tasks existieren, werden aber von keinem View, Signal oder anderen
Service tatsächlich per `.delay()`/`.apply_async()` in eine Celery-Queue gelegt.

Auch der synchrone Pfad ist nicht angebunden: `ProvisioningService.dispatch_order()`
wird laut Suche (`grep -rn "dispatch_order(" cmp/apps`) nur aus `tasks.py` selbst
aufgerufen — kein View aus `apps/approvals` oder `apps/orders` ruft ihn nach einer
Genehmigung auf. Da zusätzlich Kapitel 3.4 zeigt, dass `ApprovalRequest`-Zeilen im
Betrieb gar nicht automatisch entstehen, bricht die Kette schon vor diesem Schritt.

## 7. `SubscriptionService.create_from_order` — ebenfalls ungenutzt

`SubscriptionService.create_from_order(order_id)`
(`cmp/apps/subscriptions/services.py:14`) verlangt eine Order im Status `done` und
legt für jede Position eine `Subscription` an. Eine projektweite Suche
(`grep -rn "create_from_order" cmp/apps`) findet außer der Definition **keinen
Aufrufer**. Die Demo-`Subscription`-Zeilen in `seed.py`
(`cmp/apps/accounts/management/commands/seed.py:249`, `:285`, `:316`) entstehen
direkt über `Subscription.objects.create(...)`, nicht über den Service.

## 8. Zusammenfassung

Alle drei Modelle (`DispatchLog`, `Subscription`, `GroupSubscription`) sind
vollständig implementiert, ebenso `ProvisioningService` und
`SubscriptionService` als aufrufbare, für sich funktionierende Bausteine. Die
Celery-Tasks existieren, werden aber nirgends enqueued; `dispatch_order()` und
`create_from_order()` haben im Anwendungscode keinen Aufrufer außerhalb ihrer
eigenen Definition bzw. der Task-Hülle. Provisioning und Subscription-Erzeugung
laufen heute ausschließlich manuell (Shell, Tests) oder über direktes
ORM-Anlegen im Seed-Command — nicht automatisch aus dem Bestellfluss.

> Quelle: cmp/apps/provisioning/models.py, cmp/apps/provisioning/services.py, cmp/apps/provisioning/clients.py, cmp/apps/provisioning/tasks.py, cmp/apps/subscriptions/models.py, cmp/apps/subscriptions/services.py, cmp/apps/accounts/management/commands/seed.py — am Code geprüft 2026-07-22
