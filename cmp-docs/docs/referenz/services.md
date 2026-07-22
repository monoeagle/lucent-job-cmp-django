# Services

## Übersicht

10 Service-Klassen kapseln die Business-Logik. Alle Services sind statische Klassen ohne Zustand — sie werden nicht instanziiert, sondern direkt aufgerufen.

**Regel:** Views rufen Services auf. Services rufen Models auf. Kein direkter Model-Zugriff aus Views.

## AccountService

**Datei:** `apps/accounts/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `seed_stub_users()` | — | `int` | Erstellt 5 Demo-User, idempotent |
| `is_at_least_role(user_role, minimum_role)` | str, str | `bool` | Prüft Rollen-Hierarchie |

## CatalogService

**Datei:** `apps/catalog/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `list_active_templates(category=None)` | str? | `list[ServiceTemplate]` | Aktive Templates, optional nach Kategorie |
| `search_templates(query)` | str | `list[ServiceTemplate]` | Suche in Name + Description |
| `get_template(template_id)` | int | `ServiceTemplate` | Template by ID, NotFoundError |
| `validate_template_parameters(template_id, values)` | int, dict | `list[dict]` | Validiert Parameter gegen Schema |
| `seed_templates()` | — | `int` | Erstellt 3 Demo-Templates |

## OrderService

**Datei:** `apps/orders/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `create_order(user, notes="")` | User, str | `Order` | Neue Bestellung (Draft) |
| `get_order(order_id)` | int | `Order` | Order by ID, NotFoundError — **ohne** Zugriffsprüfung, nur für Service-zu-Service |
| `get_order_for_user(order_id, user)` | int, User | `Order` | Wie oben, aber nur Besitzer oder Approver+; sonst `NotFoundError` (→ 404). Von den Views zu verwenden |
| `list_user_orders(user_id)` | int | `list[Order]` | Bestellungen eines Users |
| `add_item(order_id, template_id, parameters)` | int, int, dict | `OrderItem` | Item hinzufügen (nur Draft) |
| `remove_item(item_id)` | int | `None` | Item entfernen (nur Draft) |
| `submit_order(order_id)` | int | `Order` | Bestellung einreichen (Draft → Submitted) |

## ContextService

**Datei:** `apps/cmdb/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `is_template_available(template_id, location, tenant)` | int, str, str | `bool` | Prüft Verfügbarkeit |
| `get_available_templates(location, tenant)` | str, str | `list[ServiceTemplate]` | Verfügbare Templates im Kontext |
| `get_parameter_restrictions(template_id, context_field, context_value)` | int, str, str | `dict` | Parameter-Einschränkungen |
| `get_user_tenants(user_id)` | int | `list[str]` | Tenants eines Users |

## ProvisioningService

**Datei:** `apps/provisioning/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `dispatch_order(order_id)` | int | `None` | Provisioning starten (Approved → Provisioning) |
| `complete_dispatch(dispatch_log_id, success)` | int, bool | `None` | Dispatch abschließen, Order-Status aktualisieren |

## ApprovalService

**Datei:** `apps/approvals/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `needs_approval(order_id)` | int | `bool` | Prüft ob Approval nötig |
| `create_approval_requests(order_id)` | int | `list[ApprovalRequest]` | Erstellt Requests (Submitted → Pending) |
| `approve(request_id, approver)` | int, User | `None` | Genehmigen — prüft `rule.approver_role` |
| `reject(request_id, approver, comment)` | int, User, str | `None` | Ablehnen — prüft `rule.approver_role` |
| `_load_pending(request_id, approver)` | int, User | `ApprovalRequest` | Intern: lädt die offene Anfrage und prüft die von der Regel verlangte Rolle (`ForbiddenError`); unbekannter Rollenwert → `ConflictError` |
| `list_pending_requests()` | — | `list[ApprovalRequest]` | Offene Requests |

## NotificationService

**Datei:** `apps/notifications/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `create(user, title, message, category)` | User, str, str, str | `Notification` | Erstellt Benachrichtigung |
| `list_unread(user_id)` | int | `list[Notification]` | Ungelesene Notifications |
| `list_all(user_id)` | int | `list[Notification]` | Alle Notifications |
| `mark_read(notification_id)` | int | `None` | Als gelesen markieren — **ohne** Empfängerprüfung |
| `mark_read_for_user(notification_id, user)` | int, User | `None` | Als gelesen markieren, nur für den Empfänger. Von den Views zu verwenden |
| `mark_all_read(user_id)` | int | `None` | Alle als gelesen |
| `unread_count(user_id)` | int | `int` | Anzahl ungelesene |

## AuditService

**Datei:** `apps/audit/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `log(user, action, resource_type, resource_id, details, ip_address)` | ... | `AuditLog` | Audit-Eintrag erstellen |
| `list_logs(resource_type=None)` | str? | `list[AuditLog]` | Logs auflisten |
| `anonymize_user(user_id)` | int | `None` | DSGVO-Anonymisierung |

## SubscriptionService

**Datei:** `apps/subscriptions/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `create_from_order(order_id)` | int | `list[Subscription]` | Subscriptions aus fertigem Order |
| `list_user_subscriptions(user_id)` | int | `list[Subscription]` | User-Subscriptions |
| `get_subscription(sub_id)` | int | `Subscription` | Subscription by ID — **ohne** Zugriffsprüfung |
| `get_subscription_for_user(sub_id, user)` | int, User | `Subscription` | Nur Besitzer oder Approver+; sonst `NotFoundError` |
| `cancel(sub_id)` | int | `None` | Kündigen — **ohne** Besitzprüfung |
| `cancel_for_user(sub_id, user)` | int, User | `None` | Kündigen, nur durch den Besitzer. Von den Views zu verwenden |

## DashboardService

**Datei:** `apps/dashboard/services.py`

| Methode | Parameter | Rückgabe | Beschreibung |
|---------|-----------|----------|-------------|
| `get_user_stats(user)` | User | `dict` | Kennzahlen eines Users (Orders, Subscriptions, …) |
| `get_admin_stats()` | — | `dict` | Globale Kennzahlen (Admin-Dashboard) |
| `get_orders_by_status(user=None)` | User? | `dict` | Order-Verteilung nach Status |
| `get_orders_by_month(user=None, months=6)` | User?, int | `list` | Orders je Monat (Zeitreihe) |
| `get_recent_orders(user=None, limit=5)` | User?, int | `list[Order]` | Letzte Bestellungen |
| `get_popular_templates(limit=5)` | int | `list` | Häufigste Templates |

## Exceptions

Alle Services werfen Custom Exceptions aus `core/exceptions.py`:

| Exception | HTTP-Äquivalent | Verwendung |
|-----------|----------------|------------|
| `ValidationError` | 400 | Ungültige Eingabe |
| `NotFoundError` | 404 | Ressource nicht gefunden |
| `ConflictError` | 409 | Ungültiger Status-Übergang |
| `ForbiddenError` | 403 | Keine Berechtigung |
