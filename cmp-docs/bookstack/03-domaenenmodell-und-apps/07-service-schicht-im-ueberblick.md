# Service-Schicht im Überblick

Alle Business-Logik von CMP liegt in Services, nicht in Views oder Models
(`views.py → services.py → models.py`). Dieses Kapitel listet alle Service-Klassen
mit Datei und den wichtigsten statischen Methoden — als Einstiegspunkt, bevor man
in eines der vorherigen Detailkapitel wechselt.

## 1. Ziel des Kapitels

Wer eine neue Funktion einbaut, soll hier in einer Tabelle finden, welcher Service
schon existiert und wofür — statt querbeet in `views.py`-Dateien zu suchen.

## 2. Wie die Liste entstanden ist

`grep -rn "class .*Service" cmp/apps cmp/core` (Stand 2026-07-22) findet genau zehn
Klassen mit dem Suffix `Service` unter `apps/*/services.py` — keine weitere
Service-Klasse liegt in `core/`. Das deckt sich mit der bestehenden Zählung "9
Services" plus `DashboardService`, das in der bisherigen `cmp-docs`-Referenz
mitgezählt, aber projektweit als zehnte Klasse geführt wird (siehe Abschnitt 4).

## 3. Alle zehn Service-Klassen

| Service | Datei | Zweck |
|---|---|---|
| `AccountService` | `apps/accounts/services.py:21` | Stub-User-Seeding, Rollen-Hierarchie |
| `CatalogService` | `apps/catalog/services.py:373` | Katalog lesen, suchen, Parameter validieren, Templates seeden |
| `ContextService` | `apps/cmdb/services.py:5` | Standort-/Mandanten-Verfügbarkeit, Parameter-Einschränkungen |
| `OrderService` | `apps/orders/services.py:8` | Bestellungen anlegen, Positionen verwalten, einreichen |
| `ApprovalService` | `apps/approvals/services.py:10` | Genehmigungsbedarf prüfen, Anträge erzeugen/entscheiden |
| `ProvisioningService` | `apps/provisioning/services.py:11` | Pipeline-Dispatch auslösen und abschließen |
| `SubscriptionService` | `apps/subscriptions/services.py:10` | Abos aus fertigen Bestellungen erzeugen, verwalten, kündigen |
| `AuditService` | `apps/audit/services.py:4` | Audit-Einträge schreiben/lesen, DSGVO-Anonymisierung |
| `NotificationService` | `apps/notifications/services.py:4` | Benachrichtigungen erzeugen, lesen, als gelesen markieren |
| `DashboardService` | `apps/dashboard/services.py:14` | Kennzahlen für User- und Admin-Dashboard aggregieren |

## 4. Wichtigste statische Methoden je Service

Alle Services sind zustandslose Klassen mit ausschließlich `@staticmethod`s — sie
werden nie instanziiert.

| Service | Methode | Kurzbeschreibung |
|---|---|---|
| `AccountService` | `seed_stub_users()` | Legt 5 Demo-User an, idempotent |
| `AccountService` | `is_at_least_role(user_role, minimum_role)` | Rollenvergleich über feste Hierarchie |
| `CatalogService` | `list_active_templates(category=None)` | Aktive Templates, optional gefiltert |
| `CatalogService` | `validate_template_parameters(template_id, values)` | Delegiert an `TemplateValidator` |
| `CatalogService` | `seed_templates()` | Legt "Linux VM" und "Windows VM" an |
| `ContextService` | `is_template_available(template_id, location, tenant)` | Prüft `AvailabilityRule`-Sperren |
| `ContextService` | `get_parameter_restrictions(template_id, context_field, context_value)` | Liest `ContextRestriction` |
| `OrderService` | `create_order(user, notes="")` | Neue Order im Status `draft` |
| `OrderService` | `add_item(order_id, template_id, parameters)` | Validiert und hängt Position an — nur im Status `draft` |
| `OrderService` | `submit_order(order_id)` | `draft` → `validated` → `submitted` |
| `ApprovalService` | `needs_approval(order_id)` | Prüft, ob aktive Regeln für die Order-Templates existieren |
| `ApprovalService` | `create_approval_requests(order_id)` | Legt Anträge an, schaltet Order auf `pending_approval` — Aufrufer siehe [Kapitel 3.4](04-genehmigung-approvalrequest.md) |
| `ApprovalService` | `approve(request_id, approver)` / `reject(request_id, approver, comment)` | Entscheidung, schaltet Order bei Vollständigkeit weiter |
| `ProvisioningService` | `dispatch_order(order_id)` | `approved` → `provisioning`, dispatcht alle Positionen an den Stub-Client |
| `ProvisioningService` | `complete_dispatch(dispatch_log_id, success)` | Schließt Dispatch ab, setzt Order auf `done`/`failed` |
| `SubscriptionService` | `create_from_order(order_id)` | Erstellt Subscriptions aus einer Order im Status `done` |
| `SubscriptionService` | `cancel(sub_id)` | `active` → `cancelled`, setzt `valid_until` |
| `AuditService` | `log(user, action, resource_type, resource_id, details, ip_address)` | Legt Audit-Eintrag an |
| `AuditService` | `anonymize_user(user_id)` | Setzt `user=None` auf allen Logs des Users (DSGVO) |
| `NotificationService` | `create(user, title, message, category)` | Legt Notification an |
| `NotificationService` | `unread_count(user_id)` | Für Dashboard-Badge |
| `DashboardService` | `get_user_stats(user)` / `get_admin_stats()` | Kennzahlen für User- bzw. Admin-Dashboard |
| `DashboardService` | `get_orders_by_status()` / `get_orders_by_month()` | Zeitreihen- und Verteilungsdaten für Charts |

Vollständige Signaturen inklusive Rückgabetypen stehen in
`cmp-docs/docs/referenz/services.md` — dort geprüft gegen dieselben Codestellen.

## 5. Fehlerbehandlung

Alle Services werfen dieselbe Exception-Hierarchie aus `cmp/core/exceptions.py`:
`ServiceError` als Basis, davon abgeleitet `ValidationError`, `NotFoundError`,
`ConflictError`, `ForbiddenError`. Views fangen diese Typen ab und übersetzen sie
in Messages oder HTTP-404 — es gibt keinen zentralen Exception-Handler, jede View
entscheidet selbst (siehe z. B. `apps/approvals/views.py:36`).

## 6. Zusammenfassung

Zehn Service-Klassen decken die komplette Business-Logik ab, alle als
zustandslose Static-Method-Container nach demselben Muster. Welche dieser
Methoden im Bestellfluss tatsächlich automatisch verkettet aufgerufen werden und
welche nur einzeln (Tests, Shell, Seed-Command) — das zeigen die Ist-Stand-Absätze
in den Kapiteln 3.4 bis 3.6.

> Quelle: cmp/apps/accounts/services.py, cmp/apps/catalog/services.py, cmp/apps/cmdb/services.py, cmp/apps/orders/services.py, cmp/apps/approvals/services.py, cmp/apps/provisioning/services.py, cmp/apps/subscriptions/services.py, cmp/apps/audit/services.py, cmp/apps/notifications/services.py, cmp/apps/dashboard/services.py, cmp/core/exceptions.py — am Code geprüft 2026-07-22
