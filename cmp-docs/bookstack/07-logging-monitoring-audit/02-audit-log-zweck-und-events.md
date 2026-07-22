# Audit-Log: Zweck und Events

Das `AuditLog`-Modell ist der revisionssichere Nachweis, wer wann was an
Bestellungen, Genehmigungen und Templates geändert hat. Diese Seite
beschreibt das Modell, den Schreibpfad `AuditService.log()` und listet per
`grep` ermittelt, welche Events real geschrieben werden — und welche nicht.

## 1. Ziel des Kapitels

Zweck des Audit-Logs ist Nachvollziehbarkeit: Wer hat eine Bestellung
angelegt, wer eine Vorlage geändert, wer einen Genehmigungsschritt
ausgelöst? Diese Seite beantwortet nicht nur „wie ist das Modell aufgebaut",
sondern vor allem „welche dieser Fragen kann das Audit-Log heute tatsächlich
beantworten" — und das ist, geprüft am Code, deutlich weniger, als der Name
verspricht.

## 2. Das Modell `AuditLog`

`cmp/apps/audit/models.py:5`, Tabelle `audit_logs`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `user` | `ForeignKey → users`, nullable, `on_delete=SET_NULL` | Auslösender User (wird `null`, wenn der User anonymisiert wurde) |
| `action` | `CharField(100)` | Aktion als Freitext, z. B. `"order_created"` |
| `resource_type` | `CharField(50)` | Betroffener Ressourcentyp, z. B. `"order"` |
| `resource_id` | `IntegerField` | ID der Ressource |
| `details` | `JSONField`, default `dict` | Zusatzdaten |
| `ip_address` | `GenericIPAddressField`, nullable | IP-Adresse |
| `timestamp` | `DateTimeField`, `auto_now_add` | Zeitpunkt |

`Meta.ordering = ["-timestamp"]` (`cmp/apps/audit/models.py:19-21`). `action`
und `resource_type` sind reine `CharField`s ohne `choices=` — welche Werte
vorkommen, bestimmt ausschließlich der Aufrufer.

## 3. Der Schreibpfad: `AuditService.log()`

`AuditService.log(user, action, resource_type, resource_id, details=None,
ip_address=None)` (`cmp/apps/audit/services.py:6-14`) ist die einzige Stelle,
die einen `AuditLog`-Eintrag anlegt (`AuditLog.objects.create(...)`). Daneben
bietet die Klasse zwei Lesemethoden: `list_logs(resource_type=None)`
(`cmp/apps/audit/services.py:17-21`) und `anonymize_user(user_id)`
(`cmp/apps/audit/services.py:24-25`), die alle Einträge eines Users auf
`user=None` setzt.

## 4. Welche Events real geschrieben werden

Projektweite Suche, Stand 2026-07-22:

```
grep -rn "AuditService.log" cmp/apps
```

Das Ergebnis sind **ausschließlich** sieben Aufrufe in einem einzigen
Management-Command, `cmp/apps/accounts/management/commands/seed.py:377-411`:

| Zeile | Auslösende Stelle | `action` | `resource_type` / `resource_id` |
|---|---|---|---|
| `seed.py:377-381` | `_seed_audit_logs()` | `order_created` | `order` / `1` |
| `seed.py:382-386` | `_seed_audit_logs()` | `order_created` | `order` / `2` |
| `seed.py:387-391` | `_seed_audit_logs()` | `order_submitted` | `order` / `3` |
| `seed.py:392-396` | `_seed_audit_logs()` | `order_created` | `order` / `5` |
| `seed.py:397-401` | `_seed_audit_logs()` | `order_created` | `order` / `7` |
| `seed.py:402-406` | `_seed_audit_logs()` | `template_updated` | `template` / `1` |
| `seed.py:407-411` | `_seed_audit_logs()` | `system_startup` | `system` / `0` |

Alle sieben Einträge entstehen als feste Demo-Fakten beim Ausführen des
Seed-Commands, nicht als Reaktion auf eine reale Benutzeraktion. Kein View
und kein Service in `orders`, `approvals` oder `provisioning` ruft
`AuditService.log()` auf — das ist mit derselben Suche belegt: Sie findet
außerhalb von `seed.py` keinen weiteren Treffer.

## 5. Welche Übergänge KEINEN Audit-Eintrag erzeugen

Geprüft an den Service-Methoden selbst:

```
grep -n "def submit_order" cmp/apps/orders/services.py       → Zeile 61
grep -n "create_approval_requests\|AuditService" cmp/apps/orders/services.py cmp/apps/approvals/services.py
```

`OrderService.submit_order` (`cmp/apps/orders/services.py:61`) enthält keinen
Aufruf von `AuditService.log` oder `create_approval_requests` — die Methode
setzt den Bestellstatus und endet dort. `ApprovalService.create_approval_requests`
(`cmp/apps/approvals/services.py:25`) existiert als eigenständige Methode,
wird aber von `submit_order` nicht aufgerufen. Damit erzeugt im laufenden
Betrieb **keiner** der folgenden Vorgänge einen Audit-Eintrag:

| Vorgang | Fehlender Auslösepunkt |
|---|---|
| Bestellung wird über die Oberfläche eingereicht | `submit_order` ruft `AuditService.log` nicht auf |
| Genehmigungsantrag entsteht | `submit_order` ruft `create_approval_requests` nicht auf — es entsteht ohnehin kein `ApprovalRequest` |
| Genehmigung wird über `approve`/`reject` entschieden | kein `AuditService.log` an dieser Stelle |
| Provisioning wird abgeschlossen | kein `AuditService.log` an dieser Stelle |

Das ist die im Handbuch bereits an anderer Stelle beschriebene Lücke der
Bestellkette (Kapitel 3.6, „Muster: Seed-Command umgeht die Service-Schicht"):
Dort wurde belegt, dass die Services selbst nicht verdrahtet sind. Diese
Seite vertieft die Audit-spezifische Konsequenz: Ohne diese Verdrahtung ist
`AuditLog` im Betrieb keine Historie realer Ereignisse, sondern ausschließlich
Demo-Datenbestand. Das offene Arbeitspaket **AP-13 · Bestellkette verdrahten**
(`todo.md:36-61`) sieht dafür eine zentrale Funktion `transition()` in einer
noch nicht existierenden Datei `core/domain/transitions.py` vor
(`grep -n def cmp/core/domain/*.py` zeigt aktuell nur `enums.py`,
`validators.py`, `value_objects.py` — keine `transitions.py`), die
Statuswechsel und `AuditService.log` an einer Stelle bündeln soll.

## 6. Lesezugriff: wo das Audit-Log heute genutzt wird

Zwei Views lesen `AuditLog`, beide nur für Admins
(`AdminRequiredMixin`, `cmp/apps/audit/views.py:6`):

| View | Datei:Zeile | Zweck |
|---|---|---|
| `AuditLogListView` | `cmp/apps/audit/views.py:10` | Paginierte Liste, filterbar nach `action`/`resource_type` |
| `AuditLogExportView` | `cmp/apps/audit/views.py:32` | CSV-Export aller Einträge |

Beide zeigen aktuell ausschließlich die sieben Seed-Einträge aus Abschnitt 4,
da im Betrieb keine weiteren Einträge entstehen.

## 7. Zusammenfassung

`AuditLog` ist vollständig modelliert und über `AuditService` sowie zwei
Admin-Views lesbar. Der Schreibpfad ist jedoch im laufenden Betrieb ungenutzt:
Alle sieben real vorhandenen Einträge stammen aus dem Seed-Command, kein
einziger aus einer echten Bestellung, Genehmigung oder einem
Provisioning-Vorgang. Ursache ist die fehlende Verdrahtung der Bestellkette
(AP-13) — solange sie offen ist, bleibt das Audit-Log bei Demo-Daten stehen.

> Quelle: cmp/apps/audit/models.py, cmp/apps/audit/services.py, cmp/apps/audit/views.py, cmp/apps/accounts/management/commands/seed.py, cmp/apps/orders/services.py, cmp/apps/approvals/services.py, cmp/core/domain/, todo.md (AP-13) — am Code geprüft 2026-07-22
