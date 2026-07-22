# Funktionale Anforderungen

Dieses Kapitel listet die funktionalen Anforderungen an CMP mit Status und
Code-Beleg. Die IDs (`FM_*` = Muss-Anforderung, `FK_*` = Kann-Anforderung) und die
Gruppierung stammen aus der internen Gap-Analyse gegen die Fremddoku des
Bestellportals; jeder Status wurde für dieses Kapitel erneut am Code geprüft.

## 1. Ziel des Kapitels

Wer wissen will, ob eine bestimmte Funktion in CMP existiert — und wenn ja, wo im Code
— findet hier die vollständige Liste mit Status (✅ erfüllt, 🟡 teilweise, ❌ offen) und
einer konkreten Codestelle als Beleg statt einer Behauptung.

## 2. Legende

| Symbol | Bedeutung |
|---|---|
| ✅ | Anforderung im Code umgesetzt und über die Oberfläche erreichbar |
| 🟡 | Teilweise umgesetzt — Baustein existiert, aber unvollständig oder nicht verdrahtet |
| ❌ | Nicht umgesetzt |

## 3. Bestellung (FM_BE01–09)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FM_BE01 | Bestellformular anzeigen | ✅ | `cmp/apps/orders/urls.py:11-12` (`create`, `create_form`), `cmp/templates/orders/form_view.html` |
| FM_BE02 | Bestellung speichern, löst Aufbau aus | 🟡 | Speichern ✅ `OrderService.create_order` (`cmp/apps/orders/services.py:12`) — Auslösen des Aufbaus nicht verdrahtet, siehe Abschnitt 7 |
| FM_BE03 | Parameter automatisch befüllen/einschränken | ✅ | `cmp/apps/orders/forms.py:12-30` (dynamische Felder aus `template_parameters`), `cmp/apps/cmdb/models.py:24` (`ContextRestriction`) |
| FM_BE04 | Bestellungsübersicht | ✅ | `cmp/apps/orders/urls.py:9` (`list`), `cmp/templates/orders/order_list.html` |
| FM_BE05 | Filter auf eigene Bestellungen | ✅ | `OrderService.list_user_orders` (`cmp/apps/orders/services.py:25`) |
| FM_BE06 | Status in der Übersicht | ✅ | `cmp/templates/orders/order_list.html:55` (`{% status_badge %}`) |
| FM_BE07 | Detailansicht | ✅ | `cmp/apps/orders/urls.py:10` (`detail`) |
| FM_BE08 | Bestellung bearbeiten | 🟡 | Nur Positionen: `add_item`/`remove_item` (`cmp/apps/orders/urls.py:13-14`) — keine Edit-View für die Order selbst |
| FM_BE09 | Bestellung entfernen | ❌ | Kein `delete` in `cmp/apps/orders/views.py` (`grep -n delete cmp/apps/orders/views.py` ohne Treffer) — gelöscht wird nur ein `OrderItem` (`OrderService.remove_item`, `cmp/apps/orders/services.py:47-58`) |

## 4. Genehmigung (FM_GE01–04)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FM_GE01 | Genehmigungspflichtige Bestellungen anzeigen | ✅ | `cmp/apps/approvals/urls.py:8` (`queue`), `ApprovalService.list_pending_requests` (`cmp/apps/approvals/services.py:96`) |
| FM_GE02 | Detailansicht um Approve/Reject erweitern | ✅ | `cmp/apps/approvals/urls.py:9-18`, `cmp/templates/approvals/approval_queue.html` |
| FM_GE03 | Genehmigen, danach Aufbau einleiten | 🟡 | Genehmigen ✅ `ApprovalService.approve` (`cmp/apps/approvals/services.py:49`) — setzt die Order auf `approved` und endet dort, kein Provisioning-Trigger |
| FM_GE04 | Ablehnen + Besteller informieren (Mail und In-App) | 🟡 | Ablehnen ✅ `ApprovalService.reject` (`cmp/apps/approvals/services.py:75`) — keine Benachrichtigung, keine Mail wird ausgelöst |

## 5. Produkte und Parameter (FM_PP01–11)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FM_PP01 | Produktübersicht | ✅ | `cmp/apps/catalog/urls.py:8` (`list`) |
| FM_PP02 | Produktdetails | ✅ | `cmp/apps/catalog/urls.py:9` (`detail`) |
| FM_PP03–05 | Produkt anlegen/bearbeiten/löschen (Admin) | ✅ | Django Admin (`cmp/apps/catalog/admin.py`) — bewusst als primäres Admin-Werkzeug (`CLAUDE.md`) |
| FM_PP06–10 | Parameter verwalten | 🟡 | Parameter sind JSON im Template (`ServiceTemplate.parameters = JSONField(default=list)`, `cmp/apps/catalog/models.py:18`), kein eigenes `ProductParameter`-Modell → keine eigene Verwaltungs-UI, Pflege nur im JSON-Feld über Django Admin |
| FM_PP11 | Parameter im Bestellformular anzeigen | ✅ | `cmp/apps/orders/forms.py:12-30` baut Felder zur Laufzeit aus `parameters` |

## 6. Benutzerverwaltung und Authentifizierung (FM_BA01–07)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FM_BA01 | Anmeldung mit Authentifizierung | ✅ | django-allauth, Session-basiert; `ACCOUNT_SIGNUP_ENABLED = False` (`cmp/config/settings/base.py:99`) |
| FM_BA02–06 | Benutzer anzeigen/anlegen/bearbeiten/löschen | ✅ | Django Admin (`cmp/apps/accounts/admin.py`); Rolle als Feld (`cmp/apps/accounts/models.py:9`) |
| FM_BA07 | Anbindung Active Directory | ❌ | Kein `django-auth-ldap` in den Requirements, keine AD-Sync-Logik im Code |

## 7. Allgemein (FM_AG01–04)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FM_AG01 | Startseite mit Kacheln | ✅ | `cmp/apps/dashboard/urls.py:8` (`home`), `cmp/templates/dashboard/dashboard.html` |
| FM_AG02 | Anbindung OpenTofu/GitLab | ❌ | `cmp/apps/provisioning/clients.py` ist `GitLabStubClient` — In-Memory-Dict, `uuid4()` als Pipeline-ID, kein echter HTTP-Call |
| FM_AG03 | E-Mail-Versand | ❌ | Kein `send_mail`/`EMAIL_BACKEND` im Projekt |
| FM_AG04 | Systembenachrichtigungen | 🟡 | Modell, Service und Oberfläche vollständig vorhanden (`cmp/apps/notifications/`), aber kein Workflow im laufenden Betrieb erzeugt eine — nur `seed.py` legt Demo-Einträge an |

## 8. Kann-Anforderungen (FK_BE/FK_AG)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| FK_BE01 | Bestehende Bestellung als Vorlage | ❌ | Keine Kopier-/Vorlagen-Funktion in `cmp/apps/orders/views.py` oder `services.py` |
| FK_BE02 | Massenbestellung | ✅ | `OrderItemGroup` mit `quantity` + `shared_parameters` (`cmp/apps/orders/models.py:32-45`) — deckt gemeinsame vs. instanzspezifische Parameter ab |
| FK_BE03 | Redundante Systeme (zwei Standorte) | 🟡 | Datenseitig möglich über `AvailabilityRule.location` (`cmp/apps/cmdb/models.py:7-15`), kein Bestell-Komfort dafür |
| FK_AG01 | Personalisierung / Dark-Mode | 🟡 | DaisyUI-Theme „Lucent" vorhanden, kein Umschalter, keine Kachel-Konfiguration |

## 9. Warum mehrere Muss-Anforderungen nur teilweise erfüllt sind

FM_BE02, FM_GE03, FM_GE04 und FM_AG04 hängen an derselben Ursache: Die einzelnen
Bausteine der Kette „Bestellung einreichen → Genehmigung → Provisioning → Subscription
→ Audit → Benachrichtigung" sind gebaut und getestet, aber im laufenden System nicht
lückenlos miteinander verdrahtet. Konkret ruft `OrderService.submit_order`
(`cmp/apps/orders/services.py:61`) nach dem Einreichen keine Funktion auf, die eine
`ApprovalRequest` erzeugt — eine über die Oberfläche eingereichte Bestellung erscheint
deshalb bei keinem Genehmiger. Details und die vollständige Liste der fehlenden Aufrufe
stehen in `analyse/analyse-bestellportal.md` (Abschnitt 1c) und im Arbeitspaket AP-13
(`todo.md`). Dieses Kapitel beschreibt die Lücke, schließt sie aber nicht.

## 10. Zusammenfassung

Von den erfassten Muss-Anforderungen sind die reinen Anzeige- und CRUD-Funktionen
(Katalog, Bestellungsübersicht, Detailansichten, Django-Admin-Verwaltung) vollständig
erfüllt. Offen sind ausschließlich externe Anbindungen (AD/LDAP, echtes
OpenTofu/GitLab, E-Mail-Versand) sowie zwei fehlende Funktionen (Order löschen, Order
bearbeiten). Teilweise erfüllt sind alle Anforderungen, die von der noch nicht
verdrahteten Bestellkette abhängen — das ist der wichtigste Einzelbefund dieses
Kapitels und wird in Kapitel 3 der Domänen-Analyse vertieft.

> Quelle: analyse/analyse-bestellportal.md (Abschnitt 1a, Stand 2026-07-21, Statuswerte am 2026-07-22 gegen den Code neu geprüft), todo.md (AP-13), cmp/apps/orders/, cmp/apps/approvals/, cmp/apps/catalog/, cmp/apps/accounts/, cmp/apps/dashboard/, cmp/apps/provisioning/, cmp/apps/notifications/, cmp/apps/cmdb/ — am Code geprüft 2026-07-22
