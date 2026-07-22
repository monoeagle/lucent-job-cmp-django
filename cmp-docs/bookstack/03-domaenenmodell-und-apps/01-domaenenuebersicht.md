# Domänenübersicht

CMP verteilt sein Domänenmodell auf 10 Django-Apps und 15 Tabellen. Dieses Kapitel
zeigt, welche Objekte es gibt, in welcher App und Tabelle sie leben, und wie sie
über Fremdschlüssel zusammenhängen — als Landkarte für die folgenden Detailseiten.

## 1. Ziel des Kapitels

Wer neu ins Domänenmodell einsteigt, soll hier eine vollständige, geprüfte Liste
aller Objekte finden sowie die Beziehungen zwischen ihnen — bevor er in die
Detailseiten zu Katalog, Bestellung, Genehmigung, Provisioning, Audit und
Notification einsteigt.

## 2. Die zehn Apps

10 Django-Apps unter `cmp/apps/` (`ls cmp/apps/`, Stand 2026-07-22):

| App | Zweck |
|---|---|
| `accounts` | User-Modell, Rollen, Stub-User-Seeding |
| `catalog` | Service-Katalog (`ServiceTemplate`), Parameter-Schema |
| `cmdb` | Standort-/Mandanten-Kontext (`AvailabilityRule`, `ContextRestriction`, `UserTenantAssignment`) |
| `orders` | Bestellungen (`Order`, `OrderItem`, `OrderItemGroup`) |
| `approvals` | Genehmigungsregeln und -anfragen (`ApprovalRule`, `ApprovalRequest`) |
| `provisioning` | Pipeline-Dispatch (`DispatchLog`), Celery-Tasks |
| `subscriptions` | Aktive Abos (`Subscription`, `GroupSubscription`) |
| `audit` | Revisionslog (`AuditLog`) |
| `notifications` | Benutzerbenachrichtigungen (`Notification`) |
| `dashboard` | Kennzahlen-Aggregation — **hat kein eigenes Model** |

`dashboard` besitzt keine `models.py` (geprüft: `find cmp/apps/dashboard -name models.py`
liefert kein Ergebnis). `DashboardService` liest stattdessen direkt aus `Order`,
`ServiceTemplate`, `Subscription`, `ApprovalRequest` sowie über `NotificationService`
aus `Notification` — siehe [Kapitel 3.7](07-service-schicht-im-ueberblick.md).

## 3. Alle 15 Domänenobjekte

| Objekt | App | Tabelle | Zweck |
|---|---|---|---|
| `User` | accounts | `users` | Login, Rolle (Requester/Approver/Admin/Superadmin) |
| `ServiceTemplate` | catalog | `service_templates` | Katalogeintrag mit Parameter-Schema (JSON) |
| `AvailabilityRule` | cmdb | `availability_rules` | Sperrt ein Template für Standort/Mandant |
| `ContextRestriction` | cmdb | `context_restrictions` | Schränkt einen Parameterwert je Kontextfeld ein |
| `UserTenantAssignment` | cmdb | `user_tenant_assignments` | Mandantenzuordnung je User |
| `Order` | orders | `orders` | Bestellkopf mit Status |
| `OrderItemGroup` | orders | `order_item_groups` | Mehrfachbestellung (quantity) mit geteilten Parametern |
| `OrderItem` | orders | `order_items` | Einzelposition einer Bestellung |
| `ApprovalRule` | approvals | `approval_rules` | Regel, wann ein Template eine Genehmigung braucht |
| `ApprovalRequest` | approvals | `approval_requests` | Einzelne Genehmigungsentscheidung |
| `DispatchLog` | provisioning | `dispatch_logs` | Protokoll eines Pipeline-Dispatch je Bestellposition |
| `Subscription` | subscriptions | `subscriptions` | Aktives Abo aus einem `OrderItem` |
| `GroupSubscription` | subscriptions | `group_subscriptions` | Aktives Abo aus einer `OrderItemGroup` |
| `AuditLog` | audit | `audit_logs` | Revisionssicherer Eintrag |
| `Notification` | notifications | `notifications` | Benutzerbenachrichtigung |

Alle Tabellennamen stammen aus `Meta.db_table` der jeweiligen Modelle, nicht aus
Konvention — jede Detailseite in diesem Kapitel nennt die genaue Codestelle.

## 4. Beziehungen zwischen den Objekten

```
users
 |-< orders                      (Order.user)
 |-< notifications                (Notification.user)
 |-< subscriptions                (Subscription.user)
 |-< group_subscriptions          (GroupSubscription.user)
 |-< user_tenant_assignments      (UserTenantAssignment.user)
 |-< audit_logs                   (AuditLog.user, nullable)
 `-< approval_requests            (ApprovalRequest.decided_by, nullable)

service_templates
 |-< order_items                  (OrderItem.template)
 |-< order_item_groups            (OrderItemGroup.template)
 |-< approval_rules               (ApprovalRule.template)
 |-< availability_rules           (AvailabilityRule.template)
 `-< context_restrictions         (ContextRestriction.template)

orders
 |-< order_item_groups            (OrderItemGroup.order)
 |-< order_items                  (OrderItem.order)
 `-< approval_requests            (ApprovalRequest.order)

order_item_groups
 |-< order_items                  (OrderItem.group, nullable)
 `-< group_subscriptions          (GroupSubscription.order_item_group)

order_items
 |-< dispatch_logs                (DispatchLog.order_item)
 `-< subscriptions                (Subscription.order_item)

approval_rules
 `-< approval_requests            (ApprovalRequest.rule)
```

`-<` liest sich als "eins-zu-viele". Jede Kante ist ein `ForeignKey` im jeweiligen
Model — geprüft in `cmp/apps/*/models.py`.

## 5. Wo die Kette real aufhört

Diese Kette (`orders` → `approval_requests` → `dispatch_logs` → `subscriptions`)
beschreibt nur, **welche Fremdschlüssel existieren** — nicht, ob eine Bestellung sie
im Betrieb tatsächlich durchläuft. Die Detailseiten 3.4 und 3.5 belegen per `grep`,
dass der automatische Übergang von `submitted` zu `approval_requests` sowie von
`approved` zu `dispatch_logs`/`subscriptions` aktuell nicht verdrahtet ist (AP-13).

## 6. Zusammenfassung

15 Objekte, 10 Apps, ein durchgängiges FK-Netz von `users` und `service_templates`
über `orders` bis zu `dispatch_logs` und `subscriptions`. Die Struktur existiert
vollständig im Datenmodell; ob sie zur Laufzeit auch durchlaufen wird, klären die
folgenden Seiten je Teilbereich.

> Quelle: cmp/apps/accounts/models.py, cmp/apps/catalog/models.py, cmp/apps/cmdb/models.py, cmp/apps/orders/models.py, cmp/apps/approvals/models.py, cmp/apps/provisioning/models.py, cmp/apps/subscriptions/models.py, cmp/apps/audit/models.py, cmp/apps/notifications/models.py — am Code geprüft 2026-07-22
