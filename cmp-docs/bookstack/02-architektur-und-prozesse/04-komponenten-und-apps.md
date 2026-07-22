# Komponenten und Apps

CMP besteht aus zehn Django-Apps unter `cmp/apps/` plus einem geteilten `core/`-Paket.
Dieses Kapitel beschreibt Zweck und Abhängigkeiten jeder App, geprüft per
`ls cmp/apps` und den `from apps.…`-Imports der jeweiligen Dateien.

## 1. Ziel des Kapitels

Wer eine neue Funktion einordnen will, findet hier, welche App wofür zuständig ist
und welche anderen Apps sie bereits importiert — als Orientierung, wo eine
Erweiterung ansetzen sollte, ohne bestehende Abhängigkeitsrichtungen umzudrehen.

## 2. Die zehn Apps

Die tatsächliche App-Liste (`ls cmp/apps`, Stand 2026-07-22) und die
`INSTALLED_APPS`-Reihenfolge in `cmp/config/settings/base.py:19-29` stimmen
überein:

| App | Zweck | Nutzt (Imports aus anderen Apps) |
|---|---|---|
| `accounts` | Custom `User`-Model mit Rollenfeld, Auth über django-allauth, `AccountService` (u. a. `is_at_least_role`) | keine |
| `catalog` | `ServiceTemplate`-Katalog mit JSON-Parameter-Schema, `CatalogService` zum Listen/Suchen/Validieren | keine |
| `orders` | Bestellungen, Positionen, Gruppen, Status-Machine, Bestell-Wizard | `catalog` (Templates), `cmdb` (Kontext-Validierung), `accounts` (Rollenprüfung in der View) |
| `approvals` | Genehmigungsregeln und -anfragen, Approval-Queue | `orders` |
| `provisioning` | Celery-Tasks, GitLab-Anbindung (aktuell Stub), `DispatchLog` | `orders` |
| `cmdb` | CMDB-Stub (Locations/Networks/Tenants aus YAML), Verfügbarkeitsregeln, Kontext-Einschränkungen | `catalog` |
| `notifications` | In-App-Benachrichtigungen | keine |
| `audit` | Audit-Log, DSGVO-Anonymisierung | keine |
| `subscriptions` | Laufende Services aus abgeschlossenen Bestellungen, Kündigung | `orders` |
| `dashboard` | Aggregierte Statistik-Übersicht, keine eigenen Models | `approvals`, `notifications`, `accounts`, `cmdb`, `orders`, `catalog`, `subscriptions` |

## 3. accounts — Nutzer, Rollen, Auth

`User` erbt von `TimeStampedModel` und Djangos `AbstractUser`, mit einem
zusätzlichen `role`-Feld (`CharField`, Choices aus `UserRole`,
`cmp/apps/accounts/models.py:7-13`). Auth läuft über django-allauth;
Registrierung ist deaktiviert (`ACCOUNT_SIGNUP_ENABLED=False`), Accounts legt ein
Admin im Django Admin an. `AccountService` wird von anderen Apps für Rollenprüfung
genutzt, etwa `orders/views.py:32` (lokaler Import in `OrderListView._can_see_all`).

## 4. catalog — Service-Katalog

`ServiceTemplate` (`cmp/apps/catalog/models.py:14-20`) trägt Name, Kategorie,
Beschreibung und ein `parameters`-JSONField, das das Bestellformular zur Laufzeit
erzeugt (Details dazu in Anhang A). `CatalogService`
(`cmp/apps/catalog/services.py:373`) bietet `list_active_templates`,
`search_templates`, `get_template`, `validate_template_parameters` und
`seed_templates`. `catalog` hat selbst keine Abhängigkeit auf andere Apps und ist
damit die unterste fachliche Schicht, auf die `orders`, `cmdb` und `dashboard`
aufsetzen.

## 5. orders — Bestellungen

Drei Models: `Order`, `OrderItemGroup`, `OrderItem`
(`cmp/apps/orders/models.py:9-67`). `OrderService`
(`cmp/apps/orders/services.py:8`) trägt Statusmaschine und Positionslogik
(`create_order`, `add_item`, `remove_item`, `submit_order`, siehe Kapitel 2.2).
`orders` importiert `CatalogService` (Template-Auflösung,
`cmp/apps/orders/services.py:2` und `views.py:9`), `CmdbStubClient` für
Kontextfelder im Formular (`cmp/apps/orders/forms.py:3`) und lokal
`AccountService` für die Sichtbarkeits-Filterung in der Bestellliste.

## 6. approvals — Genehmigungen

`ApprovalRule` und `ApprovalRequest`
(`cmp/apps/approvals/models.py:7-26`). `ApprovalService`
(`cmp/apps/approvals/services.py:8`) importiert `OrderService`
(`cmp/apps/approvals/services.py:5`), um Order-Status und Positionen zu lesen bzw.
zu setzen. Die Queue-View (`ApprovalQueueView`,
`cmp/apps/approvals/views.py:12`) ist rollenbeschränkt auf `approver` aufwärts
(`ApproverRequiredMixin`).

## 7. provisioning — Celery-Tasks und externe Anbindung

`DispatchLog` (`cmp/apps/provisioning/models.py:7`) protokolliert
Provisioning-Läufe. `ProvisioningService.dispatch_order` und `.complete_dispatch`
(`cmp/apps/provisioning/services.py:11-15,42`) laufen als Celery-Tasks
(`dispatch_provisioning`, `complete_provisioning`,
`cmp/apps/provisioning/tasks.py:8,14`) und importieren `OrderService`
(`cmp/apps/provisioning/services.py:4`). Der GitLab-Client ist aktuell ein reiner
In-Memory-Stub: `GitLabStubClient.trigger_pipeline` erzeugt eine zufällige
Pipeline-ID (`uuid.uuid4().hex[:12]`) ohne HTTP-Aufruf
(`cmp/apps/provisioning/clients.py:5-16`) — ein echter GitLab-Client ist AP-20.

## 8. cmdb — Kontext-Stub

`AvailabilityRule`, `ContextRestriction`, `UserTenantAssignment`
(`cmp/apps/cmdb/models.py:7-41`) importieren `ServiceTemplate` aus `catalog`
(`cmp/apps/cmdb/models.py:1`). `CmdbStubClient` lädt Locations, Networks und
Tenants aus YAML-Dateien unter `cmp/stubs/cmdb/` statt aus einem echten CMDB-System
(`cmp/apps/cmdb/clients.py:5-16`) — ein bewusster Stub für die
Entwicklungsumgebung, austauschbar gegen einen echten Client.

## 9. notifications — In-App-Benachrichtigungen

Ein Model `Notification` (`cmp/apps/notifications/models.py:7`),
`NotificationService` mit `create`, `list_unread`, `list_all`, `mark_read`,
`mark_all_read`, `unread_count` (`cmp/apps/notifications/services.py:4-30`).
`notifications` hat keine Abhängigkeit auf andere Apps; `dashboard` und
`core/context_processors.py` lesen von hier für Badge-Zahlen.

## 10. audit — Audit-Log

`AuditLog` (`cmp/apps/audit/models.py:5-19`, kein `TimeStampedModel`, eigenes
`timestamp`-Feld). `AuditService.log`, `.list_logs`, `.anonymize_user`
(`cmp/apps/audit/services.py:4-24`) hat keine Abhängigkeit auf andere Apps. Aktuell
wird `AuditService.log` ausschließlich vom Seed-Kommando
(`cmp/apps/accounts/management/commands/seed.py`) aufgerufen, nicht aus dem
Bestell-Workflow — siehe Kapitel 2.5.

## 11. subscriptions — Laufende Services

`Subscription` und `GroupSubscription`
(`cmp/apps/subscriptions/models.py:8-33`). `SubscriptionService`
(`cmp/apps/subscriptions/services.py:10`) importiert `OrderService`
(`cmp/apps/subscriptions/services.py:4`), um aus einer abgeschlossenen Bestellung
eine Subscription zu erzeugen (`create_from_order`).

## 12. dashboard — Aggregation ohne eigene Models

`dashboard` hat keine `models.py`-Klassen (`grep "^class " cmp/apps/dashboard/models.py`
liefert nichts). `DashboardView` (`TemplateView`,
`cmp/apps/dashboard/views.py:10`) und `dashboard/services.py` importieren aus
sechs anderen Apps — `approvals`, `notifications`, `accounts`, `cmdb`, `orders`,
`catalog`, `subscriptions` — um eine Übersicht zusammenzustellen. Das ist die App
mit der größten Zahl eingehender Abhängigkeiten im gesamten Projekt.

## 13. core/ — geteilter Code

`core/` liegt unter `apps/` in der Aufrufkette (siehe Kapitel 2.2) und bündelt:

- `core/domain/enums.py` — `UserRole` (`TextChoices`, rollenlos von Django-Views)
- `core/domain/value_objects.py` — `OrderStatus`, `StatusMachine` mit
  `TRANSITIONS`-Dict und `validate_transition`
- `core/domain/validators.py` — `TemplateValidator`
- `core/mixins.py` — `TimeStampedModel` sowie `RequesterRequiredMixin`,
  `ApproverRequiredMixin`, `AdminRequiredMixin`, `SuperadminRequiredMixin`
  (kumulative Rollenprüfung, `cmp/core/mixins.py:63-95`)
- `core/exceptions.py` — `ServiceError`-Hierarchie: `ValidationError`,
  `NotFoundError`, `ConflictError`, `ForbiddenError`
  (`cmp/core/exceptions.py`)
- `core/context_processors.py` — `badge_counts()`, die Ausnahme von der
  „`core/` importiert nicht aus `apps/`"-Regel (siehe Kapitel 2.2, Abschnitt 6)

## 14. Zusammenfassung

`catalog`, `accounts`, `notifications` und `audit` sind fachlich unabhängig und
werden von anderen Apps importiert, nicht umgekehrt. `orders` ist der zentrale
Knoten für `approvals`, `provisioning` und `subscriptions`. `dashboard` bündelt am
Ende alles zu einer Übersicht, ohne selbst Daten zu besitzen. Zwei Stellen sind
bewusste Stubs für die Entwicklungsumgebung: `GitLabStubClient`
(`provisioning`) und `CmdbStubClient` (`cmdb`) — beide simulieren externe Systeme
ohne echten Netzwerkaufruf.

> Quelle: cmp-docs/docs/entwicklung/projektstruktur.md, cmp/config/settings/base.py, cmp/apps/*/models.py, cmp/apps/*/services.py, cmp/core/ — am Code geprüft 2026-07-22
