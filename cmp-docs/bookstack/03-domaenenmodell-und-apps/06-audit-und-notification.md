# Audit und Notification

`AuditLog` und `Notification` sind die beiden Modelle, über die CMP Ereignisse
protokolliert bzw. Nutzer informiert. Dieses Kapitel dokumentiert die Felder und
prüft per `grep`, wer sie im laufenden Betrieb tatsächlich schreibt.

## 1. Ziel des Kapitels

Wer sich fragt, wann ein Audit-Eintrag oder eine Notification entsteht, findet
hier die Feldreferenz und — genauso wichtig — die ehrliche Antwort, welche
Aufrufer real existieren und welche nicht.

## 2. Feldreferenz AuditLog

`cmp/apps/audit/models.py:5`, Tabelle `audit_logs`. Einziges Modell in diesem
Kapitel **ohne** `TimeStampedModel`-Basis (`models.Model` direkt):

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, nullable, `on_delete=SET_NULL` | Auslösender User (null nach Anonymisierung) |
| `action` | `CharField(100)` | Aktion, z. B. `"order_created"` |
| `resource_type` | `CharField(50)` | Betroffener Ressourcentyp, z. B. `"order"` |
| `resource_id` | `IntegerField` | ID der Ressource |
| `details` | `JSONField`, default `dict` | Zusatzdaten |
| `ip_address` | `GenericIPAddressField`, nullable | IP-Adresse |
| `timestamp` | `DateTimeField`, `auto_now_add` | Zeitpunkt |

`Meta.ordering = ["-timestamp"]`. Da `AuditLog` kein `TimeStampedModel` ist, gibt
es hier — anders als bei den meisten übrigen Modellen dieses Kapitels 3 — kein
zusätzliches `created_at`/`updated_at`-Paar.

## 3. Feldreferenz Notification

`cmp/apps/notifications/models.py:7`, Tabelle `notifications`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, `on_delete=CASCADE` | Empfänger (`related_name="notifications"`) |
| `title` | `CharField(200)` | Titel |
| `message` | `TextField` | Nachrichtentext |
| `is_read` | `BooleanField`, default `False` | Gelesen-Status |
| `category` | `CharField(50)`, blank, default `"info"` | Freitext-Kategorie, kein `choices=` |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`Meta.ordering = ["-created_at"]`. Real vorkommende Kategoriewerte (aus
`seed.py`): `"system"`, `"provisioning"`, `"order"`, `"approval"` — `category` ist
aber ein freies Textfeld, keine geschlossene Liste im Code.

## 4. `AuditService.log()` — wer ruft ihn wirklich auf?

`AuditService.log(user, action, resource_type, resource_id, details, ip_address)`
(`cmp/apps/audit/services.py:5`) legt einen `AuditLog`-Eintrag an. Eine
projektweite Suche (`grep -rn "AuditService.log" cmp/apps`, Stand 2026-07-22)
findet **ausschließlich** Aufrufe im Management-Command `seed.py`
(`cmp/apps/accounts/management/commands/seed.py:377-407`, sieben Aufrufe für
Demo-Daten). Kein View, kein Service in `orders`, `approvals` oder `provisioning`
ruft `AuditService.log()` auf realen Geschäftsereignissen (Bestellung erstellt,
Genehmigung erteilt, Provisioning abgeschlossen) auf. `AuditService.list_logs()`
und `AuditService.anonymize_user()` sind über die Audit-Liste
(`apps/audit/views.py`) lesend nutzbar, aber der Schreibpfad im Betrieb existiert
aktuell nur für die Seed-Demodaten.

## 5. `NotificationService.create()` — wer ruft ihn wirklich auf?

`NotificationService.create(user, title, message, category)`
(`cmp/apps/notifications/services.py:5`) legt eine `Notification` an. Eine
projektweite Suche (`grep -rn "NotificationService" cmp/apps`) zeigt: Real
verwendet werden im Anwendungscode nur die **Lesepfade** —
`NotificationService.unread_count()` (Dashboard-Badge, `apps/dashboard/services.py`
und `apps/dashboard/views.py`), sowie `mark_read()`/`mark_all_read()` aus
`apps/notifications/views.py`. `NotificationService.create()` selbst hat **keinen
Aufrufer** außerhalb seiner eigenen Definition. Alle Demo-Notifications entstehen
in `seed.py` direkt über `Notification.objects.create(...)`
(`cmp/apps/accounts/management/commands/seed.py:181`, `:187`, `:252`, `:352`,
`:360`, `:366`) — nicht über den Service.

## 6. Muster: Seed-Command umgeht die Service-Schicht

Für `ApprovalRequest`, `Notification`, `Subscription` und `AuditLog` gilt
gleichermaßen: Die Demo-Daten im Management-Command `seed.py` werden per direktem
`Model.objects.create(...)` erzeugt, nicht über die jeweiligen Services
(`ApprovalService.create_approval_requests`, `NotificationService.create`,
`SubscriptionService.create_from_order`). Das widerspricht der Architekturregel
"Views/Commands rufen Services auf" nur im Seed-Command — dessen Zweck ist reines
Faktenlegen für feste Demo-Szenarien, nicht das Nachstellen des Bestellflusses.
Für den eigentlichen Anwendungsfall (ein Nutzer bestellt real etwas) bedeutet das:
Ohne die in Kapitel 3.4 und 3.5 beschriebene Verdrahtung entstehen im Betrieb
weder automatische Genehmigungsanträge noch automatische Notifications oder
Audit-Einträge.

## 7. Zusammenfassung

`AuditLog` und `Notification` sind vollständig modelliert und über ihre Services
lesbar. Der Schreibpfad über `AuditService.log()` und
`NotificationService.create()` ist im laufenden Betrieb aktuell ungenutzt — beide
Modelle werden ausschließlich über das Seed-Command mit Demodaten befüllt, nicht
aus echten Geschäftsereignissen heraus.

> Quelle: cmp/apps/audit/models.py, cmp/apps/audit/services.py, cmp/apps/notifications/models.py, cmp/apps/notifications/services.py, cmp/apps/notifications/views.py, cmp/apps/dashboard/services.py, cmp/apps/accounts/management/commands/seed.py — am Code geprüft 2026-07-22
