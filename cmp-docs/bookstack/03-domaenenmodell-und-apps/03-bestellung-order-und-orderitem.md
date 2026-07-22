# Bestellung: Order, OrderItem und OrderItemGroup

Eine Bestellung besteht aus einem `Order`-Kopf mit einem Status sowie einer oder
mehreren Positionen (`OrderItem`), optional gebündelt in einer `OrderItemGroup` für
Mehrfachbestellungen derselben Konfiguration. Dieses Kapitel dokumentiert alle drei
Modelle und die real erreichbaren Statuswerte.

## 1. Ziel des Kapitels

Wer eine Bestellung technisch nachvollziehen will — welche Felder sie hat, welche
Status sie durchlaufen kann und wie Positionen mit Gruppen zusammenhängen — findet
hier die vollständige, am Code geprüfte Referenz.

## 2. Feldreferenz Order

`cmp/apps/orders/models.py:9`, Tabelle `orders`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, `on_delete=CASCADE` | Besteller (`related_name="orders"`) |
| `status` | `CharField(30)`, choices `OrderStatus` | Aktueller Status, default `draft` |
| `notes` | `TextField`, blank | Freitext-Anmerkung |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`Meta.ordering = ["-created_at"]` — Listen zeigen neueste Bestellung zuerst.

## 3. Feldreferenz OrderItemGroup

`cmp/apps/orders/models.py:32`, Tabelle `order_item_groups`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `order` | `ForeignKey → orders`, `on_delete=CASCADE` | Zugehörige Bestellung (`related_name="groups"`) |
| `template` | `ForeignKey → service_templates`, `on_delete=PROTECT` | Verwendetes Template |
| `quantity` | `PositiveIntegerField`, default `1` | Anzahl identischer Instanzen |
| `shared_parameters` | `JSONField`, default `dict` | Für alle Instanzen der Gruppe geteilte Parameterwerte |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`on_delete=PROTECT` auf `template`: Ein Template kann nicht gelöscht werden, solange
eine `OrderItemGroup` darauf verweist.

## 4. Feldreferenz OrderItem

`cmp/apps/orders/models.py:51`, Tabelle `order_items`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `order` | `ForeignKey → orders`, `on_delete=CASCADE` | Zugehörige Bestellung (`related_name="items"`) |
| `template` | `ForeignKey → service_templates`, `on_delete=PROTECT` | Verwendetes Template |
| `parameters` | `JSONField`, default `dict` | Gewählte Parameterwerte dieser Position |
| `group` | `ForeignKey → order_item_groups`, nullable, `on_delete=SET_NULL` | Optionale Gruppen-Zuordnung (`related_name="items"`) |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

Anders als in der bisherigen Referenzdoku (`cmp-docs/docs/referenz/datenmodell.md`)
hat `OrderItem` — wie alle drei Modelle dieses Kapitels — auch `updated_at`, weil
alle von `TimeStampedModel` erben.

## 5. Statuswerte

`OrderStatus` (`cmp/core/domain/value_objects.py`) definiert neun Werte, identisch
zur bisherigen Referenzdoku:

`draft`, `validated`, `submitted`, `pending_approval`, `approved`, `rejected`,
`provisioning`, `done`, `failed`.

## 6. Erlaubte Übergänge

`StatusMachine` (`cmp/core/domain/value_objects.py`) kapselt die Übergangstabelle
`TRANSITIONS` und wirft bei einem unerlaubten Übergang `ValueError`:

| Von | Erlaubt nach |
|---|---|
| `draft` | `validated` |
| `validated` | `submitted` |
| `submitted` | `pending_approval`, `approved` |
| `pending_approval` | `approved`, `rejected` |
| `approved` | `provisioning` |
| `provisioning` | `done`, `failed` |
| `rejected`, `done`, `failed` | — (terminal) |

## 7. Was `OrderService` davon tatsächlich auslöst

`OrderService.submit_order()` (`cmp/apps/orders/services.py:61`) ist der einzige
Service, der Statusübergänge auf einer `Order` durchführt: Er prüft, dass die
Order im Status `draft` mit mindestens einer Position ist, und schaltet sie in
**einem** Aufruf über `validated` direkt weiter nach `submitted`
(zwei `StatusMachine.validate_transition()`-Aufrufe, zwei `order.save()`).
Die übrigen Statuswerte (`pending_approval`, `approved`, `rejected`,
`provisioning`, `done`, `failed`) werden ausschließlich von `ApprovalService` und
`ProvisioningService` gesetzt — siehe [Kapitel 3.4](04-genehmigung-approvalrequest.md)
und [Kapitel 3.5](05-provisioning-und-subscription.md) für den Ist-Stand, ob diese
Services nach `submitted` überhaupt automatisch erreicht werden.

## 8. Beziehungen im Überblick

```
orders (1) ---< order_item_groups (viele)
orders (1) ---< order_items (viele)
order_item_groups (1) ---< order_items (viele, group nullable)
order_items (1) ---< dispatch_logs (viele)      -> Kapitel 3.5
order_items (1) ---< subscriptions (viele)      -> Kapitel 3.5
orders (1) ---< approval_requests (viele)       -> Kapitel 3.4
```

Eine `OrderItemGroup` bündelt mehrere `OrderItem`-Zeilen mit identischem Template
und geteilten Parametern (`shared_parameters`); jede einzelne Instanz bleibt aber
eine eigene Zeile in `order_items` mit eigenen `parameters`.

## 9. Zusammenfassung

`Order`, `OrderItemGroup` und `OrderItem` bilden die Kernkette einer Bestellung.
Neun Statuswerte und eine feste Übergangstabelle sind implementiert; real
automatisiert setzt `OrderService` heute nur den Weg von `draft` bis `submitted`.
Alle drei Modelle tragen zusätzlich zu ihren fachlichen Feldern `created_at` und
`updated_at` aus `TimeStampedModel` — ein Punkt, an dem die bisherige Referenzdoku
unvollständig war.

> Quelle: cmp/apps/orders/models.py, cmp/apps/orders/services.py, cmp/core/domain/value_objects.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
