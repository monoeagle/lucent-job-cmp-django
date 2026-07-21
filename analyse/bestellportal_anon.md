# Bestellportal

<span>umfasst die Informationen zum Bestellportal </span>

# tbd

[Siehe Bestellportal](https://books.mgmt.<domain>.de/books/betriebskonzept-cloud-management/page/architektur-prozessubersicht)

## Architektur

- Wir müssen definieren, welche Systeme wo aufgebaut werden und wie miteinander sprechen (eventuell 4 Systeme benötigt &gt; DEV in <umgebung> für Entwickler, Integration in <umgebung> für Anwender, Prod in <umgebung> sowie Prod in PROD).
- Details siehe: <ai-recherche-link>
- Das Orders-File (z.B. DEV-ORDERS) enthält ale Bestellungen und wird als GitLab CI/CD-Variable angelegt und jeweils durch das Web-Backend bei einer neuen Bestellung aktualisiert, anschließend die Pipeline getriggert und tofu ausgeführt:
- Beispiel einer Bestellung in DEV-Portal:
    - 14:00:00 Portal: Neue DEV-Order
    - 14:00:01 GitLab API: DEV\_ORDERS aktualisiert
    - 14:00:02 GitLab API: Pipeline triggered (TRIGGER\_DEV=true)
    - 14:00:05 Pipeline: plan-dev startet
    - 14:00:06 Runtime: current.auto.tfvars.json erstellt
    - 14:00:10 tofu plan: + dev-vm-999
    - 14:00:15 plan-dev fertig (Artefakt: tfplan)
    - 14:00:16 auto.tfvars.json GELÖSCHT (Job-Ende)
    - 14:01:00 Admin: approve-dev → apply-dev
- Oder konkreter:

1. Frontend → POST /orders {env: "dev", order\_id: "dev-vm-999", ...}
2. Oracle: INSERT orders → id=12345
3. Oracle: SELECT \* FROM orders WHERE env='dev' AND active=1 → 5 Orders
4. GitLab: DEV\_ORDERS = {"orders": \[vm-001, vm-002, ..., vm-999\]}
5. GitLab: Pipeline trigger (TRIGGER\_DEV=true)
6. Runner: $DEV\_ORDERS → current.auto.tfvars.json → tofu plan → + vm-999

- Approval bleibt erhalten in GitLab Pipeline, auch bei Pipeline Trigger! Hier dann nur 2-way: ORDER: Django Admin + GitLab Manual Approval (2 Stufen!), bei Code-Änderung 3way: CODE: MR Review + Merge + Manual Approval (3 Stufen!)
- Es bietet sich an das Approval direkt mit in Django einzubauen und zusätzlich per Mail darüber zu informieren. Bei Klick, dass es approved ist, wird in GitLab die Pipeline autoamtisch über die API approved und der Job fortgesetzt:

1. Django Admin: Create dev-vm-999
2. Pipeline #789 triggered (CI\_APPROVED=leer → approve-dev BLOCKED!)
3. Portal /approval/ → \[APPROVE\]
4. Django API → Pipeline #789 Variable: CI\_APPROVED=yes
5. Django API → approve-dev Job → job.play()
6. approve-dev → Script sieht CI\_APPROVED=yes ✓
7. apply-dev → VM deployed! 🎉

**Hier wird nochmal erklärt, wie die GitLab-Variable erstellt und anschließend die Pipeline getriggert wird (ausführliche Beschreibung hier:** [https://sharepoint.<domain>.de/sites/<org>/Freigegebene%20Dokumente/02%20Design%20%26%20Konzeption/POC\_Terraform(Opentofu)/opentofu-portal-wrapup.md](https://sharepoint.<domain>.de/sites/<org>/Freigegebene%20Dokumente/02%20Design%20%26%20Konzeption/POC_Terraform(Opentofu)/opentofu-portal-wrapup.md)<span style="white-space: pre-wrap;"> ):</span>

#### A. PROD\_ORDERS File-Variable aktualisieren

curl -X PUT "https://gitlab/api/v4/projects/$PROJECT\_ID/variables/PROD\_ORDERS"  
-H "PRIVATE-TOKEN: $PORTAL\_TOKEN"  
\--data-urlencode "value=$(cat new-prod-orders.json)"

#### B. Pipeline auf main triggern (mit PROD-Flag)

curl -X POST "https://gitlab/api/v4/projects/$PROJECT\_ID/pipelines"  
-H "PRIVATE-TOKEN: $PORTAL\_TOKEN"  
\--data-urlencode "ref=main"  
\--data-urlencode "variables\[TRIGGER\_PROD\]=true"  
\--data-urlencode "variables\[ORDER\_ID\]=12345"

PROD-Portal: Neue Order "prod-vm-005" ↓ GitLab API: $PROD\_ORDERS = {..., "prod-vm-005": {...}} ↓ GitLab API: Trigger Pipeline (main + TRIGGER\_PROD=true) ↓ Pipeline main: ✅ plan-prod → approve-prod(manual) → apply-prod ❌ plan-dev, plan-test übersprungen (rules!) ↓ Admin: approve-prod klickt → VM prod-vm-005 deployed!

#### Django/FastAPI Endpoint im PROD-Portal

```bash
@app.post("/create-order")
def create_prod_order(order_data: OrderSchema):
    # 1. Order in DB speichern
    order = Order.create(**order_data.dict())
    
    # 2. Alle PROD-Orders zu JSON
    all_orders = Order.get_active_prod_orders()
    orders_json = {"orders": [o.dict() for o in all_orders]}
    
    # 3. GitLab API: Variable + Pipeline
    gitlab.update_variable(PROJECT_ID, "PROD_ORDERS", orders_json)
    gitlab.trigger_pipeline(PROJECT_ID, "main", {
        "TRIGGER_PROD": "true",
        "ORDER_ID": order.id
    })
    
    return {"status": "Pipeline triggered", "order_id": order.id}
```

#### API-First oder SSR

[![image-1766415482554.png](https://books.mgmt.<domain>.de/uploads/images/gallery/2025-12/scaled-1680-/image-1766415482554.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2025-12/scaled-1680-/image-1766415482554.png)

- Für Frontend Standard App: SSR &gt; hier rendert Django die Seiten serverseitig, HTMX kann zusätzlich verwendet werden für eine reaktivere App (tauscht Fragmente im HTML aus), Alpine.js eventuell für minimales Client-JS:

```
pip install django cx_Oracle python-gitlab htmx django-crispy-forms
```

- Für Frontend moderne App: API-Ansatz &gt; hier kann das Backend ebenfalls mit Django erstellt werden, jedoch als API (bei reiner API wäre dann wahrscheinlich FastAPI die bessere Wahl)
    - Diese API kann dann durch ein Frontend-Framework (meist JS) benutzt werden (angular, react, Vue, svelte, solid etc.)
- Der API-Ansatz ist modularer, da einmal API programmiert und die Endpunkte definiert werden &gt; kann von jenster Web-App einfach über Angabe der API-Endpunkte eingebunden werden, wohingegen SSR-Ansatz ein ganzheitlicher Komplettansatz ist, bei dem am Ende die HTML-Seite bei herausfällt.
- Für das Bestellportal wird ein separates GitLab-Projekt mit eigenem Entwicklungsworkflow und Verteilung benötigt.
    - Dasselbe gilt für die ConfigDB und die Entwicklung des DB Data Discovery Mechanismus

## Prozesse

- Überlegung: Portal erstellt Change nach Bestellung automatisch mit allen Details anstatt wie bisher manuelle Change-Anlage &gt; dann Bestellung über Bestellportal
    - Um dies zu gewährleisten, muss der Prozess vom Ablauf aber geändert werden (entweder Applikationsverantwortlicher bestellt selbst, indem er Infos von Prov-Koord. erhält oder Proov-Koord. bestellt)

# Zieldefinition und Anforderungen

---

## 1\. Ziel des Systems

### 1.1 Gesamtziel

Ziel ist die Entwicklung eines **webbasierten, API-first Bestellportals**, über das standardisierte und zukünftig beliebige **automatisierbare Leistungen** angefordert, genehmigt und bereitgestellt werden können.

Der initiale Fokus liegt auf:

- der **Bestellung virtueller Maschinen** (Windows / Linux)

Langfristig soll das System als **zentrale Self-Service-Plattform** für automatisierte Prozesse dienen (z. B. Infrastruktur, Services, Zugänge, Jobs).

---

### 1.2 Kernprinzipien

- **Frontend / Backend strikt getrennt**
- **API-first-Ansatz** (DRF als zentrale Schnittstelle)
- **Erweiterbar & modular**
- **Automatisierungsfähig**
- **Betriebsfähig im Enterprise-Umfeld**

---

### 1.3 Langfristige Zielarchitektur

- Skalierbar (horizontal)
- Sicher (Role-Based Access, AD-Integration)
- Wartbar (saubere Domänentrennung)
- **High-Availability-fähig** (stateless API, externe Services)

---

## 2\. Benutzerrollen & Anwendungsfälle

### 2.1 Arten von Benutzern

- __Nutzer__
  - Besucher der Seite
- __<div id="unauth_nutzer">Unauthorisierter Nutzer</div>__ 
  - Ein Nutzer, welcher nicht angemeldet ist
  - Hat keinen Zugriff auf Systemfunktionen (kann sich anmelden)
- __<div id="besteller">Besteller (Requester)</div>__ 
  - Ein Nutzer, dem die Rolle "BESTELLER" zugeordnet wurde
  - Ein Nutzer, welcher Bestellungen durchführen kann
  - Hauptnutzer des Systems
- __<div id="genehmiger">Genehmiger (Approver)</div>__ 
  - Ein Nutzer, welcher durchgeführte Bestellungen genehmigen bzw. ablehnen kann
- __<div id="administrator">Administrator</div>__
  - Ein Nutzer, welcher komplette Kontrolle über das System hat
  - Hat Vollzugriff auf alle Funktionen des Systems, auch die Funktionen, welche von anderen Nutzern durchgeführt werden

### 2.2 Anwendungsfälle

#### 2.2.1 Anwendungsfalldiagramm

<div drawio-diagram="144"><img src="https://books.mgmt.<domain>.de/uploads/images/drawio/2026-01/drawing-24-1769090895.png"></div>

_Use-Case-Diagramm_

#### 2.2.2 Auflistung aller Anwendungsfälle

_Tabellenvorlage_

|ID|ID des Anwendungsfalls (z.B. UC_B01)|
|-|-|
|Name|Name des Anwendungsfalls (z.B. "Ein Produkt bestellen")|
|Akteur(e)|Beteiligte Nutzer(rollen)|
|Auslöser|Welche Aktion führt zu diesem Anwendungsfall?|
|<nobr>Voraussetzungen</nobr>|Was muss passieren, damit der Anwendungsfall durchgeführt werden kann?|
|Beschreibung|Beschreibung des Anwendungsfalls mit wichtigen Zwischenschritten|
|Ergebnis|Was passiert, nachdem der Anwendungsfall durchgeführt wurde?|
|Erweiterungen|Durch welche Anwendungsfälle wird dieser Anwendungsfall erweitert? <br>(z.B. eigene Bestellung modifizieren erweitert Bestellungsdetails einsehen) [Angabe durch Verlinkung des anderen Anwendungsfalls.]|


|ID|<div id="uc_b01">UC_B01</div>|
|-|-|
|Name|Eine neue Bestellung anlegen|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller hat eine Aufforderung zur Erstellung einer Bestellung über das Ticket-System erhalten|
|<nobr>Voraussetzungen</nobr>|Der Besteller ist im System angemeldet|
|Beschreibung|- Dem Besteller wird ein Ticket mit der Aufforderung einer Bestellung zugeordnet <br> - Der Besteller ruft im Bestellungsportal die Seite für die Bestellungen auf <br> - Der Besteller überträgt die Daten des Tickets in das Bestellportal <br> - Der Besteller schließt die Bestellung ab <br> Der Besteller kann zusätzlich entweder eine bestehende Bestellung als Vorlage nutzen oder eine Massenbestellung durchführen, also die gleiche Bestellung mehrfach ausführen lassen.|
|Ergebnis|Die Bestellung ist im System gespeichert und kann angenommen oder abgelehnt werden|
|Erweiterungen|-|


|ID|<div id="uc_b02">UC_B02</div>|
|-|-|
|Name|Übersicht über die eigenen Bestellungen einsehen|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller möchte die eigens durchgeführten Bestellungen einsehen|
|<nobr>Voraussetzungen</nobr>|- Der Besteller ist im System angemeldet <br> - Der Besteller hat in der Vergangenheit Bestellungen durchgeführt|
|Beschreibung|Der Besteller ruft die Übersicht seiner Bestellungen auf|
|Ergebnis|- Dem Besteller wird einer Übersicht der von ihm in der Vergangenheit durchgeführten Bestellungen angezeigt <br> - Bei den Bestellungen sieht der Besteller den Status der Bestellung und den Genehmigungsstatus|
|Erweiterungen|[Bestellungsdetails einsehen](#uc_b03)|


|ID|<div id="uc_b03">UC_B03</div>|
|-|-|
|Name|Bestellungsdetails einsehen|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller möchte die Details einer von ihm durchgeführten Bestellung einsehen|
|<nobr>Voraussetzungen</nobr>|- Der Besteller ist im System angemeldet <br> - Der Besteller hat in der Vergangenheit Bestellungen durchgeführt <br> - Der Besteller hat die eigene Bestellungsübersicht aufgerufen|
|Beschreibung|- Der Besteller hat die Bestellungsübersicht geöffnet <br> - Der Besteller ruft die Detailansicht einer Bestellung auf|
|Ergebnis|Dem Besteller wird eine Ansicht der Details der Bestellung angezeigt|
|Erweiterungen|[eigene Bestellung modifizieren](#uc_b04); [eigene Bestellung entfernen](#uc_b05)|


|ID|<div id="uc_b04">UC_B04</div>|
|-|-|
|Name|eigene Bestellung modifizieren|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller will eine eigene Bestellung verändern|
|<nobr>Voraussetzungen</nobr>|- Der Besteller ist im System angemeldet <br> - Der Besteller hat in der Vergangenheit Bestellungen durchgeführt <br> - Der Besteller hat die Detailsansicht einer eigenen Bestellung aufgerufen|
|Beschreibung|- Der Besteller drückt auf den Button zur Modifikation der Bestellung <br> - Der Besteller sieht eine Seite zur Modifikation einer Bestellung <br> - Der Besteller trägt die Änderungen in der Seite ein <br> - Der Besteller speichert die Änderungen|
|Ergebnis|Die veränderte Bestellung ist im System gespeichert|
|Erweiterungen|-|


|ID|<div id="uc_b05">UC_B05</div>|
|-|-|
|Name|eigene Bestellung entfernen|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller will eine eigene Bestellung entfernen|
|<nobr>Voraussetzungen</nobr>|- Der Besteller ist im System angemeldet <br> - Der Besteller hat in der Vergangenheit Bestellungen durchgeführt <br> - Der Besteller hat die Detailsansicht einer eigenen Bestellung aufgerufen|
|Beschreibung|- Der Besteller drückt auf den Button zur Entfernung der Bestellung <br> - Dem Besteller wird eine Bestätigungsmeldung angezeigt <br> - Der Besteller bestätigt das Entfernen der Bestellung|
|Ergebnis|Die Bestellung wurde aus dem System entfernt|
|Erweiterungen|-|


|ID|<div id="uc_b06">UC_B06</div>|
|-|-|
|Name|Produktkatalog einsehen|
|Akteur(e)|Besteller|
|Auslöser|Der Besteller möchte die möglichen Produkte einsehen|
|<nobr>Voraussetzungen</nobr>|Der Besteller ist im System angemeldet|
|Beschreibung|Der Besteller ruft den Produktkatalog auf|
|Ergebnis|Dem Besteller wird eine Übersicht über alle im System hinterlegten Produkte angezeigt|
|Erweiterungen|-|


|ID|<div id="uc_g01">UC_G01</div>|
|-|-|
|Name|Übersicht über genehmigungspflichtige Bestellungen einsehen|
|Akteur(e)|Genehmiger|
|Auslöser|Der Genehmiger möchte die Übersicht der genehmigungspflichtigen Bestellungen einsehen|
|<nobr>Voraussetzungen</nobr>|Der Genehmiger ist im System angemeldet|
|Beschreibung|Der Genehmiger ruft die Übersicht der genehmigungspflichtigen Bestellungen auf|
|Ergebnis|Dem Genehmiger wird eine Übersicht über alle zu genehmigenden Bestellungen angezeigt|
|Erweiterungen|[Details einer genehmigungspflichtigen Bestellung einsehen](#uc_g02)|


|ID|<div id="uc_g02">UC_G02</div>|
|-|-|
|Name|Details einer genehmigungspflichtigen Bestellung einsehen|
|Akteur(e)|Genehmiger|
|Auslöser|- Der Genehmiger möchte die Details einer genehmigungspflichtigen Bestellung einsehen <br> - Der Genehmiger ruft die Detailansicht einer genehmigungspflichtigen Bestellung auf|
|<nobr>Voraussetzungen</nobr>|- Der Genehmiger ist im System angemeldet <br> - Es liegt eine genehmigungspflichtige Bestellung im System vor <br> - Der Genehmiger hat die Übersicht der genehmigungspflichtigen Bestellungen aufgerufen|
|Beschreibung|Der Genehmiger ruft die Detailansicht einer genehmigungspflichtigen Bestellungen auf|
|Ergebnis|Dem Genehmiger wird die Detailansicht einer genehmigungspflichtigen Bestellung angezeigt|
|Erweiterungen|[Bestellung genehmigen/ablehnen](#uc_g03)|


|ID|<div id="uc_g03">UC_G03</div>|
|-|-|
|Name|Bestellung genehmigen/ablehnen|
|Akteur(e)|Genehmiger|
|Auslöser|Der Genehmiger möchte eine genehmigungspflichtige Bestellung genehmigen oder ablehnen|
|<nobr>Voraussetzungen</nobr>|- Der Genehmiger ist im System angemeldet <br> - Es liegt eine genehmigungspflichtige Bestellung im System vor <br> - Der Genehmiger hat die Detailansicht einer genehmigungspflichtigen Bestellung aufgerufen|
|Beschreibung|Entweder/Oder: <br> - Der Genehmiger genehmigt die Bestellung <br> - Der Genehmiger lehnt die Bestellung mit Begründung ab|
|Ergebnis|Entweder/Oder: <br> - Die Bestellung ist genehmigt und wird ausgeführt <br> - Die Bestellung ist abgelehnt, wird gelöscht und muss evtl. neu beantragt werden|
|Erweiterungen|-|


|ID|<div id="uc_a01">UC_A01</div>|
|-|-|
|Name|Verwalten der Benutzer (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Benutzerdaten einsehen, bearbeiten, löschen oder neue Benutzer anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Benutzer ein, oder <br> - legt einen neuen Benutzer an, oder <br> - bearbeitet die Daten eines existierenden Benutzers, oder <br> - löscht die Daten eines existierenden Benutzers|
|Ergebnis|Eine Übersicht der Benutzer wird angezeigt, oder ein neuer Datensatz eines Benutzers ist im System hinterlegt, oder ein bestehender Datensatz eines Benutzers wurde verändert oder gelöscht|
|Erweiterungen|-|


|ID|<div id="uc_a02">UC_A02</div>|
|-|-|
|Name|Verwalten der Benutzerrollen (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Daten zu den Benutzerrollen einsehen, bearbeiten, löschen oder neue Benutzerrollen anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Benutzerrollen ein, oder <br> - legt eine neue Benutzerrolle an, oder <br> - bearbeitet die Daten einer existierenden Benutzerrolle, oder <br> - löscht eine Benutzerrolle|
|Ergebnis|Eine Übersicht der Benutzerrollen wird angezeigt, oder eine neue Benutzerrolle wird im System hinterlegt, oder eine bestehende Benutzerrolle wurde verändert oder gelöscht|
|Erweiterungen|-|


|ID|<div id="uc_a03">UC_A03</div>|
|-|-|
|Name|Verwalten der Produkte (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Daten zu den Produkten einsehen, bearbeiten, löschen oder neue Produkte anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Produkte ein, oder <br> - legt ein neues Produkt an, oder <br> - bearbeitet die Daten eines existierenden Produktes, oder <br> - löscht ein Produkt|
|Ergebnis|Eine Übersicht der Produkte wird angezeigt, oder ein neues Produkt wird im System hinterlegt, oder ein bestehendes Produkt wurde verändert oder gelöscht|
|Erweiterungen|-|

|ID|<div id="uc_a04">UC_A04</div>|
|-|-|
|Name|Verwalten der Produktparameter (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Daten zu den Produktparametern einsehen, bearbeiten, löschen oder neue Produktparameter anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Produktparameter ein, oder <br> - legt einen neuen Produktparameter an, oder <br> - bearbeitet die Daten eines existierenden Produktparameter, oder <br> - löscht ein Produktparameter|
|Ergebnis|Eine Übersicht der Produktparameter wird angezeigt, oder ein neuer Produktparameter wird im System hinterlegt, oder ein bestehender Produktparameter wurde verändert oder gelöscht|
|Erweiterungen|-|


|ID|<div id="uc_a05">UC_A05</div>|
|-|-|
|Name|Verwalten der Genehmigungsregeln (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Daten zu den Genehmigungsregeln einsehen, bearbeiten, löschen oder neue Genehmigungsregeln anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Genehmigungsregeln ein, oder <br> - legt eine neue Genehmigungsregel an, oder <br> - bearbeitet die Daten einer existierenden Genehmigungsregel, oder <br> - löscht eine Genehmigungsregel|
|Ergebnis|Eine Übersicht der Genehmigungsregeln wird angezeigt, oder eine neue Genehmigungsregel wird im System hinterlegt, oder eine bestehende Genehmigungsregel wurde verändert oder gelöscht|
|Erweiterungen|-|

|ID|<div id="uc_a06">UC_A06</div>|
|-|-|
|Name|Verwalten der Workflows (zusammengefasst)|
|Akteur(e)|Administrator|
|Auslöser|Der Administrator möchte hinterlegte Daten zu den Workflows einsehen, bearbeiten, löschen oder neue Workflows anlegen|
|<nobr>Voraussetzungen</nobr>|Der Administrator ist im System angemeldet|
|Beschreibung|Der Administrator <br> - sieht eine Übersicht über alle im System hinterlegten Workflows ein, oder <br> - legt einen neuen Workflow an, oder <br> - bearbeitet die Daten eines existierenden Workflows, oder <br> - löscht einen Workflow|
|Ergebnis|Eine Übersicht der Workflows wird angezeigt, oder ein neuer Workflow wird im System hinterlegt, oder ein bestehender Workflow wurde verändert oder gelöscht|
|Erweiterungen|-|


---

## 3\. Funktionale Anforderungen

|ID|Name|Beschreibung|<nobr>Anwendungsfall|<nobr>Akteur(e)|Vorgänger|
|-|-|-|-|-|-|
|Identifikationsnummer der Anforderung (z.B FM_BE01)|Name der Anforderung|Beschreibung der Anforderung|Anwendungsfall, aus dem die Anforderung resultiert; Angabe durch Link zum Anwendungsfall|Betroffene Akteure|Durch welche Anforderung wird diese Anforderung ausgelöst; Angabe durch Link zur Anforderung|

_Tabellenvorlage_

### 3.1 MUSS-Kriterien

#### 3.1.1 Bestellung

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fm_be01">FM_BE01</div>|Bestellformular anzeigen|Das System muss dem Nutzer ein Formular zur Bestellung eines Produktes anzeigen.|<nobr>[UC_B01](#uc_b01)|<nobr>[Besteller](#besteller)|-|
|<nobr><div id="fm_be02">FM_BE02</div>|Bestellung speichern|Das System muss dem Nutzer die Möglichkeit geben, eine Bestellung im System zu speichern. Eine gespeicherte Bestellung muss (nach Genehmigung) den automatisierten Aufbau einer VM initialisieren.|[UC_B01](#uc_b01)|<nobr>[Besteller](#besteller)|[FM_BE01](#fm_be01)|
|<nobr><div id="fm_be03">FM_BE03</div>|automatisches Befüllen der Parameter|Das System muss auf Nutzereingaben im Bestellformular reagieren und bei manchen Formularfeldern Auswahlmöglichkeiten einschränken (nur bestimmte Werte anzeigen), bzw. Werte automatisch setzen.|[UC_B01](#uc_b01)|<nobr>[Besteller](#besteller)|[FM_BE01](#fm_be01)|
|<nobr><div id="fm_be04">FM_BE04</div>|Bestellungsübersicht anzeigen|Das System muss dem Nutzer eine Übersicht über alle im System gespeicherten Bestellungen anzeigen.|<nobr>[UC_B02](#uc_b02)<br>[UC_G01](#uc_g01)|<nobr>[Besteller](#besteller)<br>[Genehmiger](#genehmiger)|-|
|<nobr><div id="fm_be05">FM_BE05</div>|Filtern nach eigens durchgeführten Bestellungen|Das System muss Filterung der Bestellungsübersicht ermöglichen, insbesondere die Filterung nach eigens durchgeführten Bestellungen eines Bestellers.|<nobr>[UC_B02](#uc_b02)|<nobr>[Besteller](#besteller)|[FM_BE04](#fm_be04)|
|<nobr><div id="fm_be06">FM_BE06</div>|Status einer Bestellung anzeigen|Das System muss in der Bestellungsübersicht den Status der Bestellungen anzeigen.|<nobr>[UC_B02](#uc_b02)|<nobr>[Besteller](#besteller)|[FM_BE04](#fm_be04)|
|<nobr><div id="fm_be07">FM_BE07</div>|Details einer Bestellung anzeigen|Das System muss die Details einer Bestellung anzeigen, wenn aus der Übersicht die Detailansicht angefordert wird.|<nobr>[UC_B03](#uc_b03)|<nobr>[Besteller](#besteller)|[FM_BE04](#fm_be04)|
|<nobr><div id="fm_be08">FM_BE08</div>|Bearbeiten einer Bestellung|Das System muss einem Nutzer die Bearbeitung von Bestellungsdetails (Parameter der Bestellung) ermöglichen. Ein Besteller darf nur eigene Bestellungen bearbeiten.|<nobr>[UC_B04](#uc_b04)|<nobr>[Besteller](#besteller)<br>[Administrator](#administrator)|[FM_BE07](#fm_be07)|
|<nobr><div id="fm_be09">FM_BE09</div>|Entfernen einer Bestellung|Das System muss einem Nutzer das Entfernen einer gespeicherten Bestellung ermöglichen. Besteller dürfen nur eigens durchgeführte Bestellungen löschen.|<nobr>[UC_B05](#uc_b05)|<nobr>[Besteller](#besteller)<br>[Administrator](#administrator)|[FM_BE07](#fm_be07)|

#### 3.1.2 Genehmigung

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fm_ge01">FM_GE01</div>|Zu genehmigende Bestellungen anzeigen|Das System muss dem Nutzer die genehmigungspflichtigen Bestellungen anzeigen. (Filtern der Bestellungsübersicht nach genehmigungspflichtigen Bestellungen)|<nobr>[UC_G01](#uc_g01)|<nobr>[Genehmiger](#genehmiger)|[FM_BE04](#fm_be04)|
|<nobr><div id="fm_ge02">FM_GE02</div>|Erweiterung [Detailansicht](#fm_be07) für Genemigung|Das System muss dem Nutzer (Genehmiger) die Detailansicht um Genehmigungs-/Ablehnungsknöpfe erweitern.|<nobr>[UC_G02](#uc_g02)|<nobr>[Genehmiger](#genehmiger)|[FM_BE07](#fm_be07)|
|<nobr><div id="fm_ge03">FM_GE03</div>|Genehmigen einer Bestellung|Das System muss einem Nutzer die Möglichkeit geben, eine Bestellung zu genehmigen. Wenn eine Bestellung genehmigt wurde, muss das System den Aufbau des zugehörigen Produkts einleiten.|<nobr>[UC_G03](#uc_g03)|<nobr>[Genehmiger](#genehmiger)|[FM_GE01](#fm_ge01)<br>[FM_GE02](#fm_ge02)|
|<nobr><div id="fm_ge04">FM_GE04</div>|Ablehnen einer Bestellung|Das System muss einem Nutzer die Möglichkeit geben, eine Bestellung abzulehnen. Wenn eine Bestellung abgelehnt wurde, muss der zugehörige Besteller darüber informiert werden. Information per E-Mail und innerhalb der Webanwendung|<nobr>[UC_G03](#uc_g03)|<nobr>[Genehmiger](#genehmiger)|[FM_GE01](#fm_ge01)<br>[FM_GE02](#fm_ge02)|

#### 3.1.3 Produkte und Parameter

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fm_pp01">FM_PP01</div>|Produktübersicht anzeigen|Das System muss einem Nutzer eine Übersicht über alle verfügbaren Produkte anzeigen.|<nobr>[UC_B06](#uc_b06)|<nobr>[Besteller](#besteller)|-|
|<nobr><div id="fm_pp02">FM_PP02</div>|Produktdetails anzeigen|Das System muss einem Nutzer die Details eines Produktes anzeigen.|<nobr>[UC_B06](#uc_b06)|<nobr>[Besteller](#besteller)|[FM_PP01](#fm_pp01)|
|<nobr><div id="fm_pp03">FM_PP03</div>|Neues Produkt anlegen|Das System muss einem Nutzer das Erstellen eines neuen Produktes ermöglichen.|<nobr>[UC_A03](#uc_a03)|<nobr>[Admin](#administrator)|[FM_PP01](#fm_pp01)|
|<nobr><div id="fm_pp04">FM_PP04</div>|Bestehendes Produkt bearbeiten|Das System muss einem Nutzer das Bearbeiten eines bestehenden Produktes ermöglichen.|<nobr>[UC_A03](#uc_a03)|<nobr>[Admin](#administrator)|[FM_PP02](#fm_pp02)|
|<nobr><div id="fm_pp05">FM_PP05</div>|Bestehendes Produkt entfernen|Das System muss einem Nutzer ermöglichen, ein bestehendes Produkt zu entfernen (löschen).|<nobr>[UC_A03](#uc_a03)|<nobr>[Admin](#administrator)|[FM_PP02](#fm_pp02)|
|<nobr><div id="fm_pp06">FM_PP06</div>|Übersicht der Parameter anzeigen|Das System muss einem Nutzer eine Übersicht über alle Parameter anzeigen.|<nobr>[UC_A04](#uc_a04)|<nobr>[Admin](#administrator)|-|
|<nobr><div id="fm_pp07">FM_PP07</div>|Details eines Parameters anzeigen|Das System muss einem Nutzer die Details der Parameter anzeigen. Die Details sind dabei die Auswahlmöglichkeiten der jeweiligen Parameter. Z. B.: Parameter "CPU" hat die Auswahlmöglichkeiten 2, 4, 8, 16 Kerne.|<nobr>[UC_A04](#uc_a04)|<nobr>[Admin](#administrator)|[FM_PP06](#fm_pp06)|
|<nobr><div id="fm_pp08">FM_PP08</div>|Neuen Datensatz eines Parameters anlegen|Das System muss einem Nutzer ermöglichen, neue Datensätze für einen Parameter anzulegen|<nobr>[UC_A04](#uc_a04)|<nobr>[Admin](#administrator)|[FM_PP07](#fm_pp07)|
|<nobr><div id="fm_pp09">FM_PP09</div>|Datensatz eines Parameters bearbeiten|Das System muss einem Nutzer ermöglichen, existierende Datensätze eines Parameters zu bearbeiten|<nobr>[UC_A04](#uc_a04)|<nobr>[Admin](#administrator)|[FM_PP07](#fm_pp07)|
|<nobr><div id="fm_pp10">FM_PP10</div>|Datensatz eines Parameters entfernen|Das System muss einem Nutzer ermöglichen, existierende Datensätze eines Parameters zu entfernen|<nobr>[UC_A04](#uc_a04)|<nobr>[Admin](#administrator)|[FM_PP07](#fm_pp07)|
|<nobr><div id="fm_pp11">FM_PP11</div>|Anzeigen der Parameter im Bestellformular|Das System muss die jeweiligen Parameter und deren Datensätze im Bestellformular anzeigen und auswählbar machen.|<nobr>[UC_A04](#uc_a04)|-|-|

#### 3.1.4 Benutzerverwaltung und Authentifizierung

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fm_ba01">FM_BA01</div>|Authentifizierung der Nutzer|Das System muss einem Nutzer die Möglichkeit geben, sich anzumelden. Dabei muss eine Authentifizierung der Anmeldedaten stattfinden. Bei fehlerhaften Daten muss eine Fehlermeldung angezeigt werden.|-|[Unauthorisierter Nutzer](#unauth_nutzer)|-|
|<nobr><div id="fm_ba02">FM_BA02</div>|Benutzerübersicht anzeigen|Das System muss einem Nutzer eine Übersicht über alle im System registrierten Nutzer anzeigen.|<nobr>[UC_A01](#uc_a01)|[Admin](#administrator)|-|
|<nobr><div id="fm_ba03">FM_BA03</div>|Neuen Benutzer anlegen|Das System muss einem Nutzer die Möglichkeit bieten einen neuen Nutzer (mit neuen Nutzerdaten) anzulegen.|<nobr>[UC_A01](#uc_a01)|[Admin](#administrator)|[FM_BA02](#fm_ba02)|
|<nobr><div id="fm_ba04">FM_BA04</div>|Details eines Benutzers anzeigen|Das System muss einem Nutzer die Details eines Nutzers anzeigen. (Name, E-Mail, Rolle,...)|<nobr>[UC_A01](#uc_a01)|[Admin](#administrator)|[FM_BA02](#fm_ba02)|
|<nobr><div id="fm_ba05">FM_BA05</div>|Details eines Nutzers bearbeiten|Das System muss einem Nutzer die Möglichkeit geben, die Daten eines Nutzer (z. B. Rolle) zu verändern.|<nobr>[UC_A01](#uc_a01)|[Admin](#administrator)|[FM_BA04](#fm_ba04)|
|<nobr><div id="fm_ba06">FM_BA06</div>|Datensatz eines Nutzers entfernen|Das System muss einem Nutzer die Möglichkeit geben, den Datensatz eines bestehenden Nutzers zu entfernen.|<nobr>[UC_A01](#uc_a01)|[Admin](#administrator)|[FM_BA04](#fm_ba04)|
|<nobr><div id="fm_ba07">FM_BA07</div>|Anbindung an Active Directory|Das System muss automatisiert Nutzer anlegen, wenn ihnen bestimmte Rollen im Active Directory System zugewiesen sind. Z. B. sollten für Nutzer, welche im AD als Provisioning-Koordinatoren hinterlegt sind, automatisiert ein Benutzerkonto im Bestellportal angelegt werden.|-|-|-|

#### 3.1.5 Allgemein

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fm_ag01">FM_AG01</div>|Startseite anzeigen|Das System muss einem Nutzer eine übersichtliche Startseite anzeigen. Der Aufbau der Startseite sollte in Kacheln erfolgen, wobei die Kacheln zu den wichtigsten Systemkomponenten führen.|-|-|-|
|<nobr><div id="fm_ag02">FM_AG02</div>|<nobr>Anbindung<br>OpenTofu|Das System muss automatisiert nach einer genehmigten Bestellung alle benötigten Daten an eine Schnittstelle übergeben, sodass über OpenTofu automatisiert die Bestellung ausgeführt werden kann.|-|-|-|
|<nobr><div id="fm_ag03">FM_AG03</div>|Versenden von E-Mails|Das System muss automatisiert E-Mails an Besteller, bzw. Genehmiger senden, sobald eine Bestellung genehmigt/abgelehnt (für Besteller), oder eine neue Bestellung durchgeführt wurde und genehmigt werden muss (Genehmiger).|<nobr>[UC_B01](#uc_b01)<br>[UC_G03](#uc_g03)|[Besteller](#besteller)<br><nobr>[Genehmiger](#genehmiger)|[FM_BE02](#fm_be02)<br>[FM_GE03](#fm_ge03)<br>[FM_GE04](#fm_ge04)|
|<nobr><div id="fm_ag04">FM_AG04</div>|Systembenachrichtigungen|Das System muss einem Nutzer Systembenachrichtigungen anzeigen, sobald relevante Ereignisse eintreten. Z. B. Bestellung wurde abgeschlossen und muss genehmigt werden (Genehmiger); Bestellung wurde genehmigt/abgelehnt (Besteller).|<nobr>[UC_B01](#uc_b01)<br>[UC_G03](#uc_g03)|[Besteller](#besteller)<br><nobr>[Genehmiger](#genehmiger)|[FM_BE02](#fm_be02)<br>[FM_GE03](#fm_ge03)<br>[FM_GE04](#fm_ge04)|

### 3.2 KANN-Anforderungen

#### 3.2.1 Bestellung

|ID|Name|Beschreibung|Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fk_be01">FK_BE01</div>|Bestellung als Vorlage|Das System sollte einem Nutzer die Möglichkeit bieten, eine exisitierende Bestellung als Vorlage zu nutzen. Dabei sollten übernommene Parameterfelder gekennzeichnet werden.|<nobr>[UC_B01](#uc_b01)|[Besteller](#besteller)|[FM_BE01](#fm_be01)|
|<nobr><div id="fk_be02">FK_BE02</div>|Massenbestellung|Das System sollte einem Nutzer die Möglichkeit bieten, mehrere Bestellungen gleichzeitig auszuführen. Er sollte die Anzahl der gewünschten Produkte definieren können, wobei Parameter (wenn möglich) automatish gesetzt werden.|<nobr>[UC_B01](#uc_b01)|[Besteller](#besteller)|[FM_BE01](#fm_be01)|
|<nobr><div id="fk_be03">FK_BE03</div>|redundante Systeme|Das System sollte einem Nutzer die Möglichkeit bieten, redundante Systeme (1. Standort Dresden; 2. Standort Leipzig) weitestgehend automatisiert zu Bestellen.|<nobr>[UC_B01](#uc_b01)|[Besteller](#besteller)|[FM_BE01](#fm_be01)|

#### 3.2.2 Allgemein

|ID|Name|Beschreibung|<nobr>Anwen<br>dungs<br>fall|<nobr>Akteur(e)|<nobr>Vorgänger|
|-|-|-|-|-|-|
|<nobr><div id="fk_ag01">FK_AG01</div>|Personalisierung|Das System sollte einem Nutzer die Möglichkeit geben, Komponenten des Systems (insbesondere die Startseite) nach eigenen Wünschen anzupassen. (Dark-Mode; Auswahl der Kacheln der Startseite)|-|-|-|

### 3.1 Bestelleransicht

- Produktübersicht
- Produktdetails
- Bestellformular (parametrisiert)
  - Option: bestehende Subscription als Vorlage zu benutzen
    - vorbefülltes Bestellformular
    - Kennzeichnung:
      - "übernommene Parameter"
      - "unique Parameter"
  - Option: Mehrfachinstanzen Unique Felder editierbar 
- Statusübersicht eigener Bestellungen
- Historie abgeschlossener Bestellungen

---

### 3.2 Approver-Ansicht

- Übersicht offener Genehmigungen
- Detailansicht einer Bestellung
- Genehmigungsaktion:
    - Approve
    - Reject
- Anzeige von Abhängigkeiten & Parametern

---

### 3.3 Admin-Ansicht

- Benutzer- & Rollenverwaltung
- Produktkatalogpflege
- Approval-Workflow-Konfiguration
- Systemüberblick

---

### 3.4 Produktkatalog

Initial:

- Windows VM
- Linux VM

Produktdefinition:

- Name
- Typ
- Parameter (z. B. CPU, RAM, OS, Laufzeit)
- Genehmigungspflicht
- Automatisierungsziel (z. B. Provisioning-Job)

Parameter:
- Anzahl

---

### 3.5 Bestellprozess

- Produkt- bzw. Subscription-Auswahl
  - Auswahl eines oder mehrerer Produkte aus dem Produktkatalog
  - Möglichkeit, bestehende Subscription als Vorlage zu nutzen
    - Formularfelder werden vorbefüllt
    - Unique Parameter (z. B. Hostname, IP, Seriennummer) werden nicht übernommen

- Parametrierung
  - Dynamisches Bestellformular je Produkt
  - Eingabe von Parametern:
    - CPU, RAM, Betriebssystem, Laufzeit, Umgebung
  - Option: Mehrfachinstanzen pro Order
    - Beispiel: Quantity = 5 → es werden 5 Subscriptions erzeugt
    - Gemeinsame Parameter für alle Instanzen, instanz-spezifische Parameter separat

- Order-Erstellung
  - Erzeugung einer Order mit einem oder mehreren OrderItems
  - OrderItems referenzieren Produkt und Parameter
  - Für jede OrderItem-Instanz wird eine Subscription erstellt

- Änderung / Löschen
  - Bestellungen können modifiziert (Modify) oder storniert (Delete) werden
  - Änderungen an Subscriptions erfolgen über neue Orders, um Audit-Trail zu erhalten

- Approval Workflow (falls erforderlich)
  - Automatisches Routing an Approver(s) je Produktdefinition
  - Mehrstufige Genehmigungen möglich
  - Rollenbasierte Entscheidungen (Approve / Reject)
  - Genehmigungsstatus fließt zurück in die Order- bzw. Subscription-Statusübersicht

- Automatisierte Bereitstellung / Änderung / Löschung
  - Genehmigte Orders werden an Automation / Celery Worker übergeben
  - Worker erzeugt JSON für OpenTofu / Terraform
  - Provisioning der VMs oder Services entsprechend der Parametrierung

- Status- & Ergebnisrückmeldung
  - Echtzeit-Updates für Besteller:
    - Pending, Approved, Rejected, Provisioning, Completed, Failed
  - Historie der erstellten Subscriptions und deren Status
  - Audit-Trail: wer, wann, was ausgelöst hat

---

### 3.6 Bestellhistorie

- Vollständige Historie pro Benutzer
- Verknüpfung: Order -> erzeugte Subscriptions
- Anzeige: Order erzeugte xyz Verknüpfungen
- Navigation: Subscription -> Order zu dieser Subscription
- Statusverläufe
- Audit-Trail (wer, wann, was)

---

### 3.7 Approval Workflow

- Konfigurierbare Genehmigungsstufen
- Rollenbasierte Genehmigung
- Erweiterbar auf:
    - Mehrstufige Approvals
    - Bedingungen (z. B. Produkt, Kosten, Parameter)

---

### 3.8\. Deployment

- Integration mit:
    - Terraform / OpenTofu
    - CI/CD-Systemen

## 4\. Nicht-funktionale Anforderungen

### 4.1 Authentifizierung & Autorisierung

- **Active Directory / LDAP Anbindung**
- Rollenbasierte Zugriffskontrolle (RBAC)
- Trennung von:
    - Identität
    - Berechtigungen
    - Rollen

---

### 4.2 API-Dokumentation

- OpenAPI-konforme Dokumentation
- Automatisch generiert aus DRF
- Interaktiv (Swagger / Redoc)
- Versioniert

---

### 4.3 Logging & Monitoring

initial:
- Zentrales Logging (strukturierte Logs)
- Audit-Logs für sicherheitsrelevante Aktionen
- Monitoring der API-Verfügbarkeit
- Vorbereitung für externe Systeme 

---

### 4.4 Backup- & Update-Strategie

- Regelmäßige Backups:
    - Datenbank
    - Konfiguration
- Rollback-fähige Updates
- Migrationsstrategie (Schema & API)
- Zero-Downtime-fähige Deployments (Ziel)

---

## 5. Glossar

|Begriff|Beschreibung|
|-|-|
|Bestellung||
|Genehmigung||
|Produkt||
|Parameter||

# Architektur & Prozessübersicht

## 1\. Architekturübersicht (High-Level)

```
+------------------+        +------------------+
|    Frontend      | <----> |      API         |
| React / Dashy etc|        | Django + DRF     |
+------------------+        +------------------+
                                  |
                                  v
                           +---------------+
                           |  Services     |
                           |  OrderService |
                           |  Approval     |
                           |  Automation   |
                           +---------------+
                                  |
          +-----------------------+------------------------+
          |                                                |
  +-------v-------+                                +-------v--------+
  | Celery Worker |                                |  Database      |
  | JSON Generator|                                |  *PostgreSQL   |
  | GitLab Push   |                                +----------------+
  +-------+-------+
          |
          v
    +----------------+
    | OpenTofu       |
    | Pipeline       |
    +----------------+
          |
          v
    Provisioned Infrastruktur
```

---

## 2\. Komponenten & Apps

| App / Komponente | Funktion |
| --- | --- |
| `users` | Identity & AD-Anbindung |
| `products` | Produktkatalog & Parameter |
| `orders` | Bestellungen & Approval Workflow |
| `automation` | Celery Worker, JSON für OpenTofu |
| `api` | REST API Endpoints (v1) |
| `core` | Logging, Permissions, Utilities |

---

## 3\. Rollen & Berechtigungen

| Rolle | Aktionen |
| --- | --- |
| Requester | Bestellung erstellen, einreichen, Status prüfen |
| Approver | Genehmigungen durchführen, Kommentare hinzufügen |
| Admin | Produkte & Users verwalten, Status korrigieren, Audit einsehen |

- RBAC + Statusabhängige Checks
- AD-Gruppen mapping → Rollen

---

## 4\. Approval Workflow

```
[ DRAFT ] --submit--> [ PENDING_APPROVAL ] --approve/reject--> [ APPROVED / REJECTED ]
       \                                                     \
        \                                                     v
         ------------------------> [ PROVISIONING ] --> [ COMPLETED / FAILED ]
```

- Audit-Logging bei allen Statuswechseln
- Provisioning via Celery Worker → OpenTofu JSON

---

## 5\. API-Design

**Ressourcen & Endpoints**

| Ressource | Endpunkte & Methoden |
| --- | --- |
| Products | GET / POST / PATCH / DELETE |
| Orders | GET / POST / SUBMIT / STATUS |
| Approvals | GET / APPROVE / REJECT |
| Users | GET / PATCH / DISABLE |
| Auth | LOGIN / LOGOUT / REFRESH |

- Versioniert: `/api/v1/`
- Rollenbasierte Permissions integriert
- DTOs / Serializers zur Validierung

---

## 6\. Logging, Monitoring & Audit

- **Logging**: JSON, strukturiert, Fehler/Info/Debug
- **Monitoring**: Prometheus / Grafana, API Healthcheck `/health/`
- **Audit**: Unveränderbare Logs aller Bestellungen, Approvals, Provisioning
- **Alerts**: Slack / E-Mail bei Fehlern

---

## 7\. Deployment & Infrastruktur

- **Container-basiert***: Django, Celery, Redis, PostgreSQL, Nginx
- **HA / Skalierbar****: mehrere API & Worker Instanzen, Load Balancer
- **Celery Worker**: erzeugt JSON für OpenTofu → GitLab → Pipeline
- **Backup & Recovery****: DB, Audit-Log, GitLab JSON
- **Update-Strategie****: Rolling / Blue-Green, DB Migrations

*offen
**nicht initial

---

## 8\. CI/CD & Teststrategie

- **Pipeline Flow**: Commit → Lint → Unit / Integration / E2E Tests → Staging Deploy → Approval → Prod Deploy → Worker JSON → OpenTofu
- **Tests**:
    - Unit: Modelle, Services, Serializers
    - Integration: API, Workflow, Worker
    - E2E: Requester → Approval → JSON → OpenTofu → Status
- **Monitoring**: GitLab Dashboard, Test Coverage, Alerts
- **Rollback**: Versionierte Docker Images + JSON referenziert Release

---

## 9\. Zusammenfassung: End-to-End Prozess

```
[ Requester ] --> Create/Modify/Delete Order --> Submit --> [ ApprovalService ] 
                                                                     |
                                                                     v
                                                              Approved? 
                                                             /          \
                                                         Yes             No
                                                         |                \
                                                  [ Celery Worker ]       [ Reject Status ]
                                                         |
                                                         v
                                                  Generate JSON → GitLab → OpenTofu
                                                         |
                                                         v
                                                 Provisioning Infrastructure
                                                         |
                                                         v
                                                  Update Order.status
                                                         |
                                                         v
                                                     Audit Logging
```

- **JSON → GitLab → OpenTofu**: zentrale Automatisierung
- **Audit, Logging, Monitoring** integriert

nicht initial
- **HA, CI/CD, Teststrategie** vollständig abgedeckt

# A) Domänenmodell & App-Struktur (Django Apps)

## 1\. Ziel des Domänenmodells

Das Domänenmodell bildet die fachlichen Kernobjekte des Bestellportals ab und stellt sicher, dass:

- Logik klar von technischer Umsetzung getrennt ist
- Workflows erweiterbar bleiben
- neue Produktarten ohne Refactoring integrierbar sind
- Genehmigungen & Automatisierungen konsistent abgebildet werden
- Rollenbasierte UI/Dashboards implementierbar sind (Requester / Approver / Admin)

---

## 2\. Domänenübersicht (High-Level)

```
User / Identity
   │
   ├── Bestellung
   │      ├── OrderItem
   │      |      ├── Produkt
   │      |      ├── Parameter
   |      │      ├── Anzahl
   |      │      
   │      ├── Subscriptions (1..n)
   |      │      ├── Subscription
   |      │      |       ├── unique_parameter
   |      │      |       ├── status
   |      │      |       ├── lifecycle
   |      │            
   │      └── Approval
   │
   ├── Produkt
   │      └── Produktparameter
   │
   └── Automation / Provisioning
```

**Wichtig:** 
- Subscription ist kein OrderItem
- Subscription lebt länger als die Order
- Modify/Delete sind neue Orders auf bestehende Subscriptions


**Frontend-Login & Dashboards:**

```
[Login Frontend] --> Authentifizierung (AD)
       |
  ---------------------------
  |            |            |
Requester   Approver       Admin
Dashboard   Dashboard     Dashboard
  |            |            |
Orders List  Approvals     Users / Products / Audit
Order Detail Approval Detail Order Detail / Status
Submit Btn  Approve/Reject
```

---

## 3\. Fachliche Domänenobjekte

### 3.1 User / Identity

**Zweck:**

- Repräsentiert authentifizierte Benutzer aus AD / LDAP
- Trägt keine Business-Logik für Bestellungen

**Kerneigenschaften:**

- Eindeutige ID
- Username / E-Mail
- Rollen (Requester, Approver, Admin)
- Gruppen (aus AD übernehmbar)

➡️ Prinzip: **Identity ≠ Authorization ≠ Business Logic**

---

### 3.2 Produkt (Product)

**Zweck:**

- Abstraktion eines bestellbaren Elements
- Nicht auf VMs beschränkt

**Beispiele:**

- Windows VM
- Linux VM

**Zentrale Eigenschaften:**

- Name
- Produkttyp
- Beschreibung
- Genehmigungspflicht
- Aktiver Status
- Automatisierungsziel (Workflow -> OpenTofu)

---

### 3.3 Produktparameter (ProductParameter)

**Zweck:**

- Definiert konfigurierbare Eigenschaften eines Produkts

**Beispiele:**

- CPU, RAM, Betriebssystem, Laufzeit, Umgebung (Dev / Test / Prod)

**Eigenschaften:**

- Schlüssel
- Typ (String / Integer / Enum / Boolean)
- Pflichtfeld ja/nein
- Default-Wert
- Validierungsregeln

➡️ Wichtig für **dynamische Formulare & API-Validierung**

---

### 3.4 Bestellung (Order)

**Zweck:**

- Fachlicher Container für eine Anforderung

**Eigenschaften:**

- Besteller
- Produkt
- Parameterwerte (JSON)
- Status
- Erstellzeitpunkt / Abschlusszeitpunkt

**Statusmodell (Beispiel):**

```
DRAFT → SUBMITTED → PENDING_APPROVAL → APPROVED → PROVISIONING → COMPLETED / FAILED
                            ↘ REJECTED
```

---

### 3.5 Approval (Genehmigung)

**Zweck:**

- Abbildung von Genehmigungsentscheidungen

**Eigenschaften:**

- Zugehörige Bestellung
- Approver
- Entscheidung
- Begründung
- Zeitstempel

➡️ Mehrere Approvals pro Order möglich

---

### 3.6 Automation / Provisioning

**Zweck:**

- Kapselt die technische Umsetzung der Bestellung
- Trennung von Business-Logik und Automatisierung

**Beispiele:**

- Terraform Run

**Eigenschaften:**

- Referenz auf Job / Workflow
- Status
- Ergebnisdaten
- Logs / Rückgaben

---

## 4\. Django App-Struktur

### 4.1 Prinzipien

- Eine App = eine Domäne
- Keine „God Apps“
- Wiederverwendbare Services
- Klare API-Grenzen

---

### 4.2 App-Struktur

```
orderportal/
├── core/               # Querschnittsfunktionen
│   ├── permissions/
│   ├── middleware/
│   ├── auditing/
│   └── utils/
│
├── users/              # Identity & Rollen
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   └── views.py
│
├── products/           # Produktkatalog
│   ├── models/
│   │   ├── product.py
│   │   └── parameter.py
│   ├── serializers.py
│   └── views.py
│
├── orders/             # Bestellungen
│   ├── models/
│   │   ├── order.py
│   │   └── approval.py
│   ├── services/
│   │   ├── order_service.py
│   │   └── approval_service.py
│   ├── serializers.py
│   └── views.py
│
├── automation/         # Provisioning / Jobs
│   ├── models.py
│   ├── services.py
│   └── workers.py
│
├── api/                # API Routing & Versionierung
│   └── v1/
│       └── urls.py
│
└── config/             # Django Settings
```

---

## 5\. Trennung von Verantwortlichkeiten

| Ebene | Verantwortung |
| --- | --- |
| Models | Datenstruktur |
| Serializer | Validierung & API-Form |
| Services | Business-Logik |
| Views | Orchestrierung |
| Automation | Technische Umsetzung |

➡️ **Keine Business-Logik in Views oder Serializern**

---

## 6\. Erweiterbarkeit & HA-Fähigkeit

### 6.1 Skalierung

- Stateless API → horizontale Skalierung
- Externe DB / Cache
- Asynchrone Worker (Celery)

### 6.2 Erweiterungen

- Neue Produktarten → `products`
- Neue Workflows → `automation`
- Mehrstufige Approvals → `orders.approval`

---

## 7\. Abgrenzung

- UI-spezifische Logik nicht im Backend
- Infrastruktur-Details nicht in der Domäne

---

## 8\. Ergebnis dieses Kapitels

✔ Klar definiertes fachliches Modell  
✔ Saubere App-Grenzen  
✔ Rollenbasierte Dashboards (Requester / Approver / Admin) integriert  
✔ Grundlage für API-Design & Workflows  
✔ Zukunftssicher für Automatisierung & HA

---

# B) Rollen-, Rechte- & AD-Integrationskonzept

## 1\. Ziel des Kapitels

Dieses Kapitel beschreibt das **Sicherheits- und Berechtigungskonzept** des Bestellportals.  
Ziel ist eine:

- **Zentrale Authentifizierung** (AD / LDAP)
- **Feingranulare Autorisierung** (RBAC)
- **Saubere Trennung** von Identität, Rollen und Fachlogik
- **API-taugliche, skalierbare Lösung**

---

## 2\. Grundprinzipien

### 2.1 Trennung der Verantwortlichkeiten

| Bereich | Aufgabe |
| --- | --- |
| Authentication | Wer bist du? |
| Authorization | Was darfst du? |
| Business Rules | Was passiert fachlich? |

➡️ **Keine Vermischung dieser Ebenen**

---

### 2.2 Leitlinien

- AD ist **Source of Truth** für Identität
- Rollen werden **zentral gemappt**
- API entscheidet **immer serverseitig**
- Keine Rechte im Frontend

---

## 3\. Authentifizierung

### 3.1 Authentifizierungsstrategie

**Primär**

- Active Directory / LDAP

**Sekundär (Fallback / Dev)**

- Lokale Django User (optional)

---

### 3.2 Technische Umsetzung (Django)

**Komponenten**

- `django-auth-ldap`
- Django Custom User Model
- DRF + JWT

**Ablauf**

1.  Benutzer meldet sich an
2.  Authentifizierung gegen AD
3.  User wird lokal angelegt / synchronisiert
4.  Rollen & Gruppen werden gemappt
5.  JWT Token wird ausgestellt

---

### 3.3 Token-Strategie

- Access Token (kurzlebig)
- Refresh Token (rotation)
- Stateless API → HA-fähig

---

## 4\. Benutzer & Identitätsmodell

### 4.1 Custom User Model

**Pflicht**

- `AbstractBaseUser`
- Keine Fachlogik
- AD-Attribute speicherbar

**Beispielattribute**

- username
- email
- display_name
- ad_dn
- is_active

---

### 4.2 Gruppen & Rollen

- AD-Gruppen werden übernommen
- Keine direkte Kopplung an Business-Logik
- Mapping in lokale Rollen

---

## 5\. Rollenmodell (RBAC)

### 5.1 Definierte Rollen

| Rolle | Beschreibung |
| --- | --- |
| REQUESTER | Darf Produkte bestellen |
| MODIFIER | Darf Produkte anpassen |
| APPROVER | Darf Bestellungen genehmigen |
| ADMIN | Vollzugriff |

➡️ Rollen sind **fachlich**, nicht technisch

---

### 5.2 Rollenquelle

- Rollen werden aus:
    - AD-Gruppen
    - oder lokaler Konfiguration  
        gemappt

**Beispiel**

```
AD_Group_VM_Requester → REQUESTER
AD_Group_VM_Modifier  → MODIFIER
AD_Group_VM_Approver  → APPROVER
AD_Group_Admin        → ADMIN
```

---

## 6\. Autorisierung (Permissions)

### 6.1 Permission-Ebenen

| Ebene | Beispiel |
| --- | --- |
| Global | Ist Admin |
| Objekt | Gehört mir diese Bestellung |
| Aktion | Darf genehmigen |

---

### 6.2 DRF Permissions

**Standard**

- `IsAuthenticated`

**Custom Permissions**

- `IsRequester`
- `IsApprover`
- `IsAdmin`
- `IsOrderOwner`
- `CanApproveOrder`

---

### 6.3 Beispiel-Matrix

| Aktion | Requester | Modifier| Approver | Admin |
| --- | --- | --- | --- | --- |
| Produkt anzeigen | ✅   |✅| ✅   | ✅   |
| Bestellung anlegen | ✅   |❌| ❌   | ✅   |
| Bestellung bearbeiten | ✅   |✅| ❌   | ✅   |
| Bestellung entfernen | ✅   |✅| ❌   | ✅   |
| Eigene Bestellung sehen | ✅   |❌| ❌   | ✅   |
| Aktion genehmigen | ❌   |❌| ✅   | ✅   |
| Produkt verwalten | ❌   |❌| ❌   | ✅   |

---

## 7\. Objektbasierte Sicherheit

### 7.1 Bestellungen

- Requester sieht **nur eigene**
- Approver sieht:
    - nur Bestellungen, die seiner Rolle zugeordnet sind
- Admin sieht alle

---

### 7.2 Approval-Regeln

- Entscheidung basiert auf:
    - Rolle
    - Produkt
    - Status

➡️ Keine Hardcodierung in Views

---

## 8\. AD-Integration im Detail

### 8.1 Synchronisationsstrategie

- On-Login Sync
- Regelmäßiger Background Sync (optional)
- Kein Passwortspeichern lokal

---

### 8.2 AD-Attribute

- Gruppen
- Anzeigename
- E-Mail
- DN

---

### 8.3 Fehlerfälle

- AD nicht erreichbar → Login verweigern
- Rolle fehlt → Minimalrechte
- Deaktivierter AD-User → lokaler User deaktiviert

---

## 9\. Audit & Sicherheit

### 9.1 Audit-Logging

- Login / Logout
- Rollenänderungen
- Genehmigungen
- Admin-Aktionen

---

### 9.2 Sicherheitsmaßnahmen

- Rate Limiting
- Token Blacklisting
- IP-Filtering (optional)
- HTTPS only

---

## 10\. HA- & Skalierungsfähigkeit

### 10.1 HA-Design

- Stateless Auth (JWT)
- Kein Session-State
- Externe Token-Blacklist (Redis)

---

### 10.2 Skalierung

- Mehrere API-Instanzen
- Zentraler Identity-Provider
- Einheitliche Permission-Logik

---

## 11\. Ergebnis dieses Kapitels

✔ Sichere AD-basierte Authentifizierung  
✔ Klare Rollen & Permissions  
✔ API-first & HA-fähig  
✔ Erweiterbar ohne Refactoring

---

# C) Approval Workflow (fachlich & technisch)

## 1\. Ziel des Kapitels

Ziel ist die **Abbildung eines flexiblen, rollenbasierten Genehmigungsprozesses** für Bestellungen:

- Trennung von Besteller, Approver und Admin
- Mehrstufige Genehmigungen möglich
- Erweiterbar für unterschiedliche Produkte
- Automatisierbar für Provisioning-Tasks
- Auditierbar für Compliance

---

## 2\. Grundprinzipien des Workflows

1.  **Besteller erstellt, modifiziert oder löscht Bestellung**
    - Status: `DRAFT → SUBMITTED`
2.  **Genehmigungsprüfung**
    - Prüfung, ob Produkt Approval benötigt
    - Status: `PENDING_APPROVAL`
3.  **Genehmigung durch Approver**
    - Entscheidungen: Approve / Reject
    - Status-Update: `APPROVED` / `REJECTED`
4.  **Provisioning / Automatisierung**
    - Status: `PROVISIONING → COMPLETED` / `FAILED`
5.  **Abschluss**
    - Bestellung abgeschlossen
    - Historie & Audit-Log

---

## 3\. Statusmodell

| Status | Beschreibung | Verantwortlich |
| --- | --- | --- |
| DRAFT | Bestellung erstellt, noch nicht eingereicht | Requester |
| SUBMITTED | Bestellung eingereicht, wartet auf Approval Check | System |
| PENDING_APPROVAL | Genehmigung erforderlich, wartet auf Entscheidung | Approver |
| APPROVED | Genehmigt, bereit zur Provisionierung | System |
| REJECTED | Abgelehnt | Approver |
| PROVISIONING | Automatisierte Umsetzung läuft | System/Worker |
| COMPLETED | Provisionierung erfolgreich abgeschlossen | System |
| FAILED | Provisionierung fehlgeschlagen | System/Worker |

---

## 4\. Rollen & Workflow

| Rolle | Aktionen im Workflow |
| --- | --- |
| Requester | Bestellung erstellen, einreichen, Status verfolgen |
| Approver | Genehmigen / Ablehnen, Kommentar hinzufügen |
| Admin | Vollzugriff, kann Workflow überspringen / korrigieren, Audit einsehen |

---

## 5\. Approval-Arten

### 5.1 Einzelgenehmigung

- Nur ein Approver erforderlich
- Statuswechsel direkt nach Genehmigung oder Ablehnung

### 5.2 Mehrstufige Genehmigung

*noch nicht vorgesehen*

---

### 5.3 Regeln basierend auf Produkt

*noch offen*

z.B.:
- Approval erforderlich nur bei:
    - teuren Produkten
    - bestimmten VM-Typen
    - kritischen Parametern (z. B. hohe Ressourcen)
- Regeln zentral konfigurierbar in `orders` App

---

## 6\. Technische Umsetzung in Django

### 6.1 Modelle

```
# orders/models/order.py
class Order(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("PENDING_APPROVAL", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("PROVISIONING", "Provisioning"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    parameters = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

```
# orders/models/approval.py
class Approval(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(User, on_delete=models.PROTECT)
    decision = models.CharField(max_length=10, choices=[("APPROVED", "Approved"), ("REJECTED", "Rejected")])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 6.2 Services / Business Logic

- **OrderService**
    - `submit_order(order)`
    - prüft, ob Approval nötig → Status `PENDING_APPROVAL`
    - benachrichtigt Approver
- **ApprovalService**
    - `approve(order, user, comment)`
    - `reject(order, user, comment)`
    - prüft Rolle & Berechtigungen
    - aktualisiert Order-Status
    - löst Provisioning aus, falls genehmigt

---

### 6.3 Automatisierung

- Provisioning-Worker (Celery / Redis Queue)
- Statusupdates: `PROVISIONING → COMPLETED / FAILED`
- Fehlerhandling / Retry-Logik

---

## 7\. Audit & Logging

- Jede Approval-Entscheidung wird **unveränderbar** geloggt
- Historie von Statuswechseln
- Admin kann alle Entscheidungen nachverfolgen

---

## 8\. UI / API Implikationen

### 8.1 Requester API

- POST `/orders/` → neue Bestellung
- GET `/orders/` → eigene Bestellungen
- GET `/orders/<id>/` → Detailansicht

### 8.2 Approver API

- GET `/approvals/pending/` → offene Genehmigungen
- POST `/approvals/<order_id>/approve` → Genehmigen
- POST `/approvals/<order_id>/reject` → Ablehnen

### 8.3 Admin API

- GET `/orders/all/`
- GET `/approvals/all/`
- PATCH `/orders/<id>/status/` → Status korrigieren

---

## 9\. Erweiterbarkeit

- Neue Approval-Regeln → in `orders.services.approval_rules.py` konfigurieren
- Mehrstufig → ApprovalService kann Chain of Approvers abarbeiten
- Produktabhängig → ApprovalService prüft Produktattribute

---

## 10\. Zusammenfassung

- Approval Workflow **zentraler Geschäftsprozess**
- Rollenkonzept aus Kapitel 2 direkt integriert
- Statusmodell & Services klar getrennt
- Bereit für HA, Automatisierung und Audit
- Skalierbar für neue Produkte / Regeln

# D) API-Design

## 1\. Ziel des Kapitels

- **Frontend / Backend Trennung**: API-first Ansatz
- **Klar definierte Endpunkte** für Requester, Approver und Admin
- **Versionierung** für zukünftige Erweiterungen
- **Rollenbasierte Permissions** (Kapitel 2)
- **Datenvalidierung & DTOs** (Serializers)

---

## 2\. API-Prinzipien

- **REST-konform**
- **Versionierung**: `/api/v1/...`
- **Eindeutige Ressourcen**: Order, Product, Approval, User
- **Statusbasiert**: Statusfelder klar dokumentiert
- **Hypermedia optional** (HATEOAS) für Workflow-States

---

## 3\. API-Ressourcen

| Ressource | Zweck | Rollen |
| --- | --- | --- |
| `/products/` | Produktkatalog abrufen | ALL |
| `/orders/` | Bestellungen erstellen, anzeigen, verwalten | Requester/Approver/Admin |
| `/approvals/` | Genehmigungen durchführen | Approver/Admin |
| `/users/` | Benutzerverwaltung (nur Admin) | Admin |
| `/auth/` | JWT Token, Login / Logout | ALL |

---

## 4\. Endpunkte & Methoden

### 4.1 Authentifizierung

| Endpunkt | Methode | Beschreibung |
| --- | --- | --- |
| `/api/v1/auth/login/` | POST | Login via AD, JWT Token zurück |
| `/api/v1/auth/refresh/` | POST | Refresh Token |
| `/api/v1/auth/logout/` | POST | Token invalidieren |

---

### 4.2 Produkte

| Endpunkt | Methode | Rollen | Beschreibung |
| --- | --- | --- | --- |
| `/api/v1/products/` | GET | ALL | Liste aller aktiven Produkte |
| `/api/v1/products/<id>/` | GET | ALL | Detailansicht Produkt |
| `/api/v1/products/` | POST | ADMIN | Neues Produkt anlegen |
| `/api/v1/products/<id>/` | PATCH | ADMIN | Produkt bearbeiten |
| `/api/v1/products/<id>/` | DELETE | ADMIN | Produkt deaktivieren |

**Serializer (DTO)**:

```
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "type", "description", "active", "requires_approval"]
```

---

### 4.3 Bestellungen (Orders)

| Endpunkt | Methode | Rollen | Beschreibung |
| --- | --- | --- | --- |
| `/api/v1/orders/` | GET | REQUESTER | Eigene Bestellungen auflisten |
| `/api/v1/orders/all/` | GET | ADMIN | Alle Bestellungen |
| `/api/v1/orders/<id>/` | GET | OWNER/ADMIN/APPROVER | Detailansicht |
| `/api/v1/orders/` | POST | REQUESTER | Neue Bestellung erstellen |
| `/api/v1/orders/<id>/submit/` | POST | REQUESTER | Bestellung einreichen → Status `PENDING_APPROVAL` |
| `/api/v1/orders/<id>/status/` | PATCH | ADMIN | Status manuell ändern (z. B. Fehlerkorrektur) |

**Serializer Beispiel:**

```
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "user", "product", "parameters", "status", "created_at", "updated_at"]
        read_only_fields = ["status", "created_at", "updated_at"]
```

---

### 4.4 Genehmigungen (Approvals)

| Endpunkt | Methode | Rollen | Beschreibung |
| --- | --- | --- | --- |
| `/api/v1/approvals/pending/` | GET | APPROVER | Offene Genehmigungen anzeigen |
| `/api/v1/approvals/<order_id>/approve/` | POST | APPROVER | Bestellung genehmigen |
| `/api/v1/approvals/<order_id>/reject/` | POST | APPROVER | Bestellung ablehnen |
| `/api/v1/approvals/all/` | GET | ADMIN | Alle Genehmigungen einsehen |

**Serializer Beispiel:**

```
class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = ["id", "order", "approver", "decision", "comment", "created_at"]
        read_only_fields = ["approver", "created_at"]
```

---

### 4.5 Benutzerverwaltung (Admin)

| Endpunkt | Methode | Rollen | Beschreibung |
| --- | --- | --- | --- |
| `/api/v1/users/` | GET | ADMIN | Benutzerliste |
| `/api/v1/users/<id>/` | GET | ADMIN | Benutzer-Detail |
| `/api/v1/users/<id>/roles/` | PATCH | ADMIN | Rollen ändern |
| `/api/v1/users/<id>/disable/` | POST | ADMIN | Benutzer deaktivieren |

**Serializer Beispiel:**

```
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "roles", "is_active"]
```

---

## 5\. Permissions & Sicherheit

- **Global Permission**: `IsAuthenticated`
- **Resource-based Permission**:
    - `IsOwner` für Bestellungen
    - `IsApprover` für Approvals
    - `IsAdmin` für Admin-Endpunkte
- **Statusabhängige Checks**:
    - Approval nur bei Status `PENDING_APPROVAL`
    - Besteller kann eigene abgeschlossene Bestellungen nur lesen

---

## 6\. Versionierung

- Alle Endpunkte unter `/api/v1/`
- Vorteil:
    - API kann unabhängig weiterentwickelt werden
    - Alte Clients bleiben kompatibel

---

## 7\. Beispiel-Workflow via API

1.  **Besteller** erstellt Bestellung: `POST /orders/`
2.  **Besteller** reicht Bestellung ein: `POST /orders/<id>/submit/`
3.  **System** prüft Approval-Regeln → Status `PENDING_APPROVAL`
4.  **Approver** genehmigt: `POST /approvals/<id>/approve/`
5.  **System** startet Provisioning → Status `PROVISIONING → COMPLETED`
6.  **Besteller** sieht Status: `GET /orders/<id>/`

---

## 8\. Erweiterbarkeit

- Neue Produkte → `/products/` erweitern, ApprovalService prüft Regeln
- Mehrstufige Approvals → ApprovalService & Endpunkte bleiben gleich
- Automatisierungs-Logs → optional `/automation/logs/` Endpoint

---

## 9\. Zusammenfassung

- **REST-API mit klaren Ressourcen**
- **Rollen- & Statusabhängige Permissions**
- **DTOs / Serializers** zur Validierung
- **Versionierung** für zukunftssichere Weiterentwicklung
- Vollständig kompatibel mit **Frontend / HA / Automatisierung**

---

# E) Logging, Monitoring & Audit

## 1\. Ziel des Kapitels

- Sicherstellen, dass alle **Aktionen** nachvollziehbar sind
- **Fehler und Systemzustände** jederzeit sichtbar und analysierbar sind
- Grundlage für **Compliance, Debugging und Betrieb**
- Vorbereitung für **HA und skalierbare Deployments**

---

## 2\. Logging

### 2.1 Logging-Ebenen

| Ebene | Zweck | Beispiel |
| --- | --- | --- |
| DEBUG | Entwicklerinformationen | API-Request-Payload |
| INFO | Standard-Operations | Bestellung eingereicht |
| WARNING | Auffälligkeiten | Approver nicht verfügbar |
| ERROR | Fehler | Provisioning fehlgeschlagen |
| CRITICAL | Systemausfälle | DB-Verbindung verloren |

---

### 2.2 Technische Umsetzung (Django)

- Standard-Django Logging via `logging`\-Config
- JSON-Format für strukturierte Logs (z. B. ELK / Loki)
- Separate Logger für:
    - API Requests (`api_logger`)
    - Orders & Approvals (`order_logger`)
    - Automation / Provisioning (`automation_logger`)

**Beispiel config:**

```
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "pythonjsonlogger.jsonlogger.JsonFormatter"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
        "file": {"class": "logging.FileHandler", "filename": "/var/log/orderportal.log", "formatter": "json"}
    },
    "loggers": {
        "api_logger": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "order_logger": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "automation_logger": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
    },
}
```

---

### 2.3 API Request Logging

- Loggt:
    - User ID
    - Endpoint
    - Request Method
    - Status Code
    - Dauer
- Beispiel: `/orders/submit/` → INFO Log `User 123 submitted Order 456`

---

### 2.4 Fehler- & Exception-Logging

- Fehler werden per Sentry / Rollbar (optional) gesammelt
- Automatische Alerts bei:
    - Provisioning-Failure
    - DB- oder Queue-Ausfälle
    - Permission Errors (verdächtig)

---

## 3\. Monitoring

### 3.1 Metriken

| Metrik | Zweck |
| --- | --- |
| Bestellungen / Minute | Systemlast |
| Genehmigungen / Stunde | Workflow-Auslastung |
| Provisioning Success/Failure Rate | Automatisierungsqualität |
| API Response Times | Performance Monitoring |
| Authentifizierungsfehler | Sicherheit & Angriffserkennung |

---

### 3.2 Tools

- Prometheus / Grafana für Metriken
- Healthcheck-Endpunkt `/health/`
- Alerts via Slack / E-Mail / PagerDuty

---

### 3.3 Healthchecks

- DB-Verbindung
- Redis / Queue-Verbindung
- Worker-Status (Celery)
- API-Status (`200 OK`)

---

## 4\. Audit Logging

### 4.1 Zweck

- Vollständige Nachvollziehbarkeit aller kritischen Aktionen
- Compliance-relevant (Genehmigungen, Admin-Aktionen)
- Unveränderbar gespeichert (immutable Logs)

---

### 4.2 Audit Events

| Event | Gespeichert |
| --- | --- |
| Bestellung erstellt | User, Order ID, Timestamp |
| Bestellung eingereicht | User, Order ID, Timestamp, Status |
| Genehmigung | Approver, Order ID, Entscheidung, Kommentar, Timestamp |
| Statusänderung | Admin, Order ID, alter Status, neuer Status, Timestamp |
| Benutzer / Rollenänderung | Admin, User ID, alte Rolle, neue Rolle, Timestamp |
| Provisioning Result | Order ID, Status, Output, Timestamp |

---

### 4.3 Technische Umsetzung

- Separate Audit-Tabelle `audit_log` oder externe DB (z. B. PostgreSQL)
- Optional: immutable Event-Log (z. B. WORM Storage)
- Verbindung zu API / Services über `signals` oder `services.audit_logger()`

**Beispiel:**

```
class AuditLog(models.Model):
    event_type = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    approver = models.ForeignKey(User, related_name="approvals", null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, default=dict)
```

---

### 4.4 Integration in Services

- **OrderService**: `submit_order() → audit_log("ORDER_SUBMITTED")`
- **ApprovalService**: `approve_order() → audit_log("ORDER_APPROVED")`
- **AutomationService**: `provision_order() → audit_log("PROVISIONING_COMPLETED")`

---

## 5\. Skalierbarkeit & HA

- Logs zentralisieren (ELK / Loki / Graylog)
- Healthchecks für Auto-Scaling / Orchestrierung (z. B. Kubernetes)
- Monitoring-Dashboard für Admin / DevOps

---

## 6\. Zusammenfassung

- **Logging**: strukturiert, JSON, mehrschichtig
- **Monitoring**: Metriken + Healthchecks + Alerts
- **Audit**: immutable Events für Compliance & Debugging
- Vollständig **API- und Service-integriert**, skalierbar und HA-fähig

---

# F) Deployment & Infrastrukturkonzept

## 1\. Ziel des Kapitels (angepasst)

- Bereitstellung einer **stabilen Produktionsumgebung**
- **Automatisierte Bereitstellung von Bestellungen** via OpenTofu
- **HA, Skalierbarkeit, Monitoring**
- Trennung von **Entwicklung, Staging, Produktion**
- **JSON-basiertes Deployment** für Infrastruktur

---

## 2\. Workflow der Bereitstellung

### 2.1 Fachlicher Ablauf

1.  **Requester** erstellt Bestellung über API → Status `SUBMITTED`
2.  **ApprovalService** prüft Regeln → Status `PENDING_APPROVAL`
3.  **Approver** genehmigt → Status `APPROVED`
4.  **Provisioning-Phase**
    - **Celery Worker** erzeugt ein **JSON-Manifest** der Bestellung
    - JSON enthält:
        - Produkt & Parameter
        - Genehmigungs-IDs
        - Benutzer- / Environment-Infos
5.  **Lieferung des JSON**
    - Worker checkt JSON in **GitLab Repo** ein (Branch/Commit)
    - Optional: Merge Request → OpenTofu Pipeline triggert Deployment
6.  **OpenTofu**
    - Liest JSON aus GitLab
    - Führt Infrastrukturänderungen / VM-Provisioning aus
7.  **Celery Worker**
    - Prüft Status von OpenTofu-Run
    - Aktualisiert `Order.status`:
        - `PROVISIONING → COMPLETED / FAILED`
8.  **Auditing**
    - Alle Schritte werden in Audit-Log erfasst

---

### 2.2 Wer macht was?

| Aufgabe | Verantwortlich |
| --- | --- |
| JSON-Erstellung | Celery Worker (`automation.services`) |
| GitLab Integration | Celery Worker |
| OpenTofu Deployment | OpenTofu Pipeline |
| Status-Update & Logging | Celery Worker |
| Approval-Prüfung | ApprovalService (vor JSON-Erstellung) |

---

## 3\. Technische Umsetzung

### 3.1 Celery Worker

- Trigger:
    - Status `APPROVED` in `Order`
- Schritte:
    1.  JSON erzeugen (`order.to_json()`)
    2.  Commit in GitLab Repo (`python-gitlab` oder API)
    3.  Trigger OpenTofu Pipeline (GitLab CI/CD)
    4.  Polling / Callback für Status
    5.  Update `Order.status` → Audit-Log

**Beispiel: JSON**

```
{
  "order_id": 123,
  "user": "john.doe",
  "product": "Linux VM",
  "parameters": {
    "cpu": 4,
    "ram": 8192,
    "disk": 100
  },
  "approval_ids": [456],
  "environment": "prod"
}
```

---

### 3.2 GitLab Integration

- Branch pro Bestellung optional (`orders/<order_id>`)
- Commit JSON → Merge Request → OpenTofu Pipeline
- Vorteil: **Versionierbares Deployment**, Audit-fähig


<p class="callout info">Zum Hinweis:</p>
Die im OpenTofu GitLab-Projekt definierten API-Token müssen vom Order Portal genutzt werden, um auf dieses zuzugreifen und die CI/CD-Variablen mit den Order-Details anlegen und bearbeiten sowie die Pipeline triggern zu können.

Diese Token müssen im Portal zur Verfügung stehen und müssen daher bei der Verteilung des Portal-Codes auf die Portal-Server ebenfalls mit deployt werden. Details zu diesem Prozess sind hier zu finden:

[Deployment des Bestellportals](https://books.mgmt.<domain>.de/books/betriebskonzept-cloud-management/page/deployment-des-bestellportals)

---

### 3.3 OpenTofu Pipeline

- Pipeline liest JSON aus GitLab
- Führt Provisioning aus:
    - VM erstellen
    - Ressourcen konfigurieren
- Status zurück an Worker / API
- Optional:
    - Fehlerhandling / Retry
    - Notification an Requester

---

## 4\. Infrastrukturübersicht (erste Idee)

```
          +-------------------+
          |  Load Balancer    |
          +-------------------+
                  |
        +---------+---------+
        |                   |
   +----v----+         +----v----+
   | Web/API |         | Web/API |
   | Server1 |         | Server2 |
   +----+----+         +----+----+
        |                   |
        +---------+---------+
                  |
              +---v---+
              | Redis  |  <-- Cache & Celery Queue
              +---+---+
                  |
           +------v------+
           | Celery Worker |
           | JSON erzeugen |
           | GitLab push   |
           +------+--------+
                  |
             +----v----+
             | OpenTofu|
             | Pipeline |
             +----+----+
                  |
          Provisioning Infrastruktur
```

---

## 5\. Logging & Monitoring

- **Celery Worker** loggt:
    - JSON-Erstellung
    - GitLab Push
    - Pipeline-Trigger
    - Status von OpenTofu
- **API** zeigt:
    - `Order.status` (PROVISIONING, COMPLETED, FAILED)
- **Audit-Log** speichert:
    - JSON erzeugt
    - Commit ID
    - Pipeline Run ID
    - Ergebnis / Fehler

---

## 6\. HA & Skalierung

- **Celery Worker** kann horizontal skaliert werden
- **GitLab** ist zentraler Versionskontrollpunkt
- **OpenTofu** Pipeline unabhängig, kann parallel mehrere Deployments abarbeiten
- Stateless API → mehrere Web/API Instanzen möglich

---

## 7\. Backup & Recovery

- **GitLab** Versionierung sichert JSONs
- **Database Backup** speichert Orders + Status
- **Audit Logs** unveränderbar
- Fehler in OpenTofu → Worker kann Status zurücksetzen, erneuten Deployment-Run triggern

---

## 8\. Zusammenfassung

- Celery Worker erzeugt **JSON für OpenTofu**
- GitLab dient als **Versionierung / Trigger**
- OpenTofu Pipeline übernimmt Provisioning
- Status & Audit → Worker → API / DB
- HA, Monitoring, Logging und Backup vollständig integriert
- Architektur **API-first, skalierbar, erweiterbar**

# G) CI/CD Pipeline & Teststrategie

## 1\. Ziel des Kapitels

- **Automatisierte Code-Bereitstellung** für alle Komponenten: API, Celery Worker, OpenTofu JSON, Frontend
- **Qualitätssicherung** durch automatisierte Tests
- **Nahtlose Integration** von Bestellworkflow → Provisioning → Statusabgleich
- **Schnelle Fehlererkennung** durch Tests, Linter, Security Checks
- **Produktionsreife** durch Rollback- & Release-Management

---

## 2\. CI/CD Pipeline Overview

### 2.1 Pipeline Komponenten

| Schritt | Beschreibung | Tool |
| --- | --- | --- |
| Lint & Code Quality | PEP8, Black, Flake8, MyPy | GitLab CI/CD |
| Unit Tests | Modelle, Services, Serializers | pytest / pytest-django |
| Integration Tests | API Endpoints, Approval Workflow | pytest + DRF test client |
| Deployment → Staging | Auto-Deploy Staging-Umgebung | Docker Compose / Helm |
| Approval → Produktion | Merge / Deployment Pipeline | GitLab CI/CD + Celery Worker trigger |
| OpenTofu Trigger | Deployment JSON / Provisioning | Celery Worker + GitLab CI |
| Monitoring & Reporting | Test Coverage, Logs, Alerts | GitLab + Prometheus / Grafana |

---

### 2.2 Pipeline Flow (High-Level)

```
Code Commit → GitLab CI
       │
       ├─ Lint & Static Analysis
       │
       ├─ Unit Tests
       │
       ├─ Integration Tests
       │
       ├─ Deploy Staging
       │
       ├─ Approval (Code Review)
       │
       └─ Deploy Production + Trigger Celery Worker → OpenTofu JSON
```

---

## 3\. Teststrategie

### 3.1 Unit Tests

- **Modelle**: Validierung, Statuswechsel, Relations
- **Serializers**: Input Validation, JSON Output
- **Services**: Business-Logik (OrderService, ApprovalService)

**Beispiel: OrderService Test**

```
def test_submit_order_requires_approval(order_factory):
    order = order_factory(status="DRAFT", product_requires_approval=True)
    submit_order(order)
    assert order.status == "PENDING_APPROVAL"
```

---

### 3.2 Integration Tests

- **API Endpoints**
    - `/orders/submit/` → Statuswechsel
    - `/approvals/<id>/approve/` → Genehmigung
- **Approval Workflow**
    - Statusübergänge validieren
- **Celery Worker Integration**
    - Mock JSON-Erstellung & GitLab Push
    - Simulierte OpenTofu Response → Status Update

---

### 3.3 End-to-End Tests

- Simuliert **vollständigen Bestellprozess**:  
    Requester → Approval → JSON → OpenTofu → Status → Audit Log
- Verwendet Testdaten & Staging-Infrastruktur

---

## 4\. GitLab CI/CD Details

### 4.1 Branch-Strategie

- `main` → Produktionscode
- `develop` → Entwicklungszweig / Staging
- Feature-Branches → Merge Requests

### 4.2 Pipelines pro Branch

| Branch | Pipeline |
| --- | --- |
| develop | Lint → Unit Tests → Integration Tests → Staging Deploy |
| main | Lint → Unit Tests → Integration Tests → Production Deploy + Celery JSON Trigger |

---

### 4.3 GitLab Secrets & Variables

- DB Zugang, JWT Secrets → GitLab CI/CD Variables
- AD Bind Credentials → GitLab Secret
- OpenTofu API Token → GitLab Secret

---

## 5\. Celery Worker Integration in CI/CD

- Worker reagiert **nur auf Status APPROVED**
- Pipeline erstellt Docker Image für Worker
- Worker läuft in Production / Staging
- Worker erzeugt **JSON für OpenTofu**, pusht in GitLab → Pipeline triggert Provisioning
- Rückmeldung → Update `Order.status` + Audit

---

## 6\. Rollback & Release Management

- Versionierte Docker Images → Tagging (`v1.0.0`, `v1.1.0`)
- OpenTofu Deployment JSON referenziert spezifisches Release
- Fehler → Rollback:
    - Worker kann Status zurücksetzen
    - JSON kann angepasst & erneut deployed werden

---

## 7\. Monitoring & Reporting

- **Pipeline Status** → GitLab CI Dashboard
- **Test Coverage** → Badge in Repo
- **Alerts**:
    - Fehler bei Tests → Slack / E-Mail
    - Provisioning Fehler → Worker log → API Status

---

## 8\. Zusammenfassung

- Vollständig **CI/CD-automatisiert** für Bestellportal
- **Testabdeckung** von Unit → Integration → E2E
- **Celery Worker** integriert JSON-Erstellung + OpenTofu Trigger
- Rollback-Strategien & Versionierung vorhanden
- Monitoring & Reporting abgeschlossen → Produktionsreif

---

# Dokumentation Prototyp Bestellportal

## 1. Projektablage

Link zum Projekt (in <umgebung> Umgebung): https://git.mgmt.<domain>.de/hcm/cloud-management-order-portal

Link zur Belegarbeit: 
[Sharepoint](https://sharepoint.<domain>.de/sites/<org>/Freigegebene%20Dokumente/02%20Design%20%26%20Konzeption/POC_Terraform(Opentofu)/Belegarbeit_<autor>_CM_v04.docx?d=w7cf3e01a594340299e6d06400018497e)


## 2. Projektstruktur

[![](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-03/scaled-1680-/image-1772636870295.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-03/image-1772636870295.png)

*Ordner/Dateistruktur des Projektes*
### 2.1 Dateien

#### 2.1.1 Python/Django


[![Zusammenspiel_Dateien_Django.drawio.png](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-03/scaled-1680-/zusammenspiel-dateien-django-drawio.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-03/zusammenspiel-dateien-django-drawio.png)

*Zusammenspiel der grundlegenden Dateien in Django*

<p class="callout info">Um die Codeblöcke nicht unnötig zu vergrößern, wurden alle import-Statements weggelassen. Diese müssen natürlich aufgerufen werden, wenn der Code verwendet werden soll.</p>

##### admin.py

Wird nur genutzt, um Klassen der models.py-Datei in der Adminoberfläche anzuzeigen und bearbeitbar zu machen. Beispiel für eine Registrierung:


```python
admin.site.register(Order)
```

##### apps.py

In dieser Datei muss eine AppConfig-Klasse existieren.

```python
class OrderPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_portal'
```

Wenn eine signals.py-Datei verwendet wird, um bspw. nach einem Speichern-Event eine Funktion auszuführen, muss diese in der AppConfig-Klasse eingebunden werden.

```python
class OrderPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order_portal'

    def ready(self):
        import order_portal.signals
```

[Django-Dokumentation Application](https://docs.djangoproject.com/en/6.0/ref/applications/)

##### forms.py

Diese Datei wird genutzt um Formulare für Klassen der models.py zu definieren. Es gibt mehrere Möglichkeiten, das umzusetzen. Die einfachste Möglichkeit:


```python
class OrderForm(forms.ModelForm): # ModelForm creates a form from an existing model
    """An object which represents a form of an order."""
    
    class Meta: # telling the ModelForm which model it is associated with and which input-fields should be shown
        model = Order
        fields = "__all__" # all editable fields should be shown
```

[Django-Dokumentation Formulare](https://docs.djangoproject.com/en/6.0/topics/forms/)

##### models.py

In dieser Datei werden die Objekt-Klassen der Anwendung definiert. Die Klassen werden genutzt, um die Datenbanktabellen für die Objekte zu erstellen. Eine Klasse entspricht einer Tabelle und die Attribute der Klasse definieren die Spalten der Datenbanktabelle. Beispiel:


```python
class Order(models.Model):
    user_name = models.CharField(max_length=255)
    order_details = models.CharField(max_length=255)
    order_date = models.DateTimeField(auto_now_add=True)
    order_product = models.ForeignKey(Product, on_delete=models.PROTECT)
    order_location = models.ForeignKey(Location, on_delete=models.PROTECT)
    order_dns_address = models.ForeignKey(DNSAddress, on_delete=models.PROTECT)
    order_proxy_address = models.ForeignKey(ProxyServer, on_delete=models.PROTECT)
```

Es können zusätzlich Methods für die Klassen definiert werden. Eine to-String-Funktion existiert für Objektklassen schon, gibt aber nicht so sinnvolle Daten zurück. Um sinnvollere Daten zurückzugeben, kann die \_\_str__()-Method überschrieben werden:


```python
  def __str__(self):
        return "Bestellung " + str(self.pk) + ": " + self.order_product.name + " ordered by " + self.user_name
```

[Django-Dokumentation Models](https://docs.djangoproject.com/en/6.0/topics/db/models/)

##### signals.py

Diese Datei kann als Event-Handler genutzt werden. Dadurch kann bspw. nach einer Änderung in einer Datenbanktabelle unabhängig vom restlichen Code eine Funktion ausgeführt werden. Im folgenden Beispiel werden die Daten der Datenbanktabelle in eine Json-Datei geschrieben. "save_to_cicd()" ruft eine Custom-Funktion in der [utils.py]()-Datei auf.


```python
@receiver(post_save, sender=Order)
def export_order_recorders_to_json(sender, instance, **kwargs):
    orders_queryset = Order.objects.all()
    data = serializers.serialize("json", orders_queryset)
    
    save_to_cicd()
    
    with open("/home/<ad-domain>/<user-id>/portal_prototype/order_portal/tmp/order_records.json", "w") as file:
        file.write(data) # save the contents of the data variable in a Json-file
```

[Django-Dokumentation Signals](https://docs.djangoproject.com/en/6.0/topics/signals/)

##### tests.py

In dieser Datei können Unit- und Integrationstests angelegt und durchgeführt werden. Testcases werden als einzelne Funktionen in einer übergeordneten Klassen angelegt. Die Klassen sind meines Wissens nach nicht notwendig, sind aber nützlich, um die Testcases besser einzuteilen. Beispiel:


```python
class ProductModelTests(TestCase):
    def test_str_returns_product_name(self):
        """
        __str__() returns the product_name of the product
        """
        product = Product(product_name="Test Product")
        self.assertEqual(product.__str__(), product.product_name)
```

Um die Tests durchzuführen, muss in der Kommandozeile folgender Code ausgeführt werden:

```bash
python manage.py test
```

[Django-Dokumentation Tests](https://docs.djangoproject.com/en/6.0/topics/testing/overview/)

##### urls.py

Diese Datei wird verwendet um eine Anfrage eines Clients zu einer views.py Funktion zuzuordnen.


```python
path("order_form/", views.new_or_edit_order, name="new_order")
```

In dem Beispiel wird die Addresse "localhost:8000/order_portal/order_form/" vom CLient aufgerufen. Hier wird dann diese URL der views.py Funktion "new_or_edit_order()" zugeordnet und diese aufgerufen.


```python
name="new_order"
```

Durch diese Namensgebung kann in den HTML-Dateien "new_order" anstatt der URL verwendet werden, nach folgendem Schema:


```html
<a href={% url 'order_portal:new_order' %}></a>
```

[Django-Dokumentation URLs](https://docs.djangoproject.com/en/6.0/topics/http/urls/)

##### utils.py

Diese Datei ist eine eigens erstellte Hilfs-Datei. Diese muss keiner direkten Django-Architektur folgen. Sie kann genutzt werden, um Funktionen dem Rest der Webanwendung bereitzustellen. In unserem Fall wird sie genutzt, um die Ablage in der CI/CD-Variable von Gitlab zu realisieren. Beispielfunktion:


```python
def save_to_cicd():
    
    gl = gitlab.Gitlab(url="https://git.mgmt.<domain>.de", private_token=settings.GITLAB_VAR_TOKEN, ssl_verify=False)
    project = gl.projects.get(settings.PROJECT_ID)
    
    all_orders = Order.objects.all()
    orders_json = {
        'orders': [{
            'order_id': o.pk,
            'user_name': o.user_name,
            'order_details': o.order_details,
            'order_date': o.order_date,
            'order_product': o.order_product,
            'order_location': o.order_location,
            'order_dns_address': o.order_dns_address,
            'order_proxy_address': o.order_proxy_address
        } for o in all_orders]
    }
    
    import json
    var_data = {
        'key': 'ALL_ORDERS',
        'value': json.dumps(orders_json, default=str),
        'variable_type': 'file'
    }

    if project.variables.get('ALL_ORDERS'):
        project.variables.update("ALL_ORDERS", {"value": json.dumps(orders_json, default=str)})
    else:
        project.variables.create(var_data)
```

##### views.py

Diese Datei wird genutzt um zwischen Frontend und Backend zu kommunizieren. Die Funktionen nehmen fast immer einen HTTP-Request an, aus welchen bspw. die Art der Anfrage (GET, POST) extrahiert und genutzt werden kann.
Die Funktionen können auf zwei Wegen aufgebaut werden. Entweder als klassische Funktion:


```python
def get_modal_order_details(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "order_portal/partials/modal_order_detail.html", {'order': order})
```

Oder als Klasse, welche von den generic-Vorlagen von Django erbt:


```python
class DetailView(generic.DetailView):
    model = Order
    template_name = "order_portal/detail.html"
```

Bei normalen Funktionen ist eine gute Herangehensweise, immer ein "render" zurückzugeben. Dieser beinhaltet immer den HTTP-Request und ein HTML-Template. Es kann noch zusätzlicher Kontext übergeben werden, welcher dann in dem HTML-Template nutzbar gemacht wird. Bei dem oberen Beispiel ist das der letzte Abschnitt auf der "return"-Zeile: {"order": order}. Die Namensgebung ist dabei: {"\[Name der Variable im HTML]":\[Daten des Backends]}.
Darauf kann dann im HTML wie folgt zugegriffen werden:


```html
<div>Produkt: {{ order.order_product.name }}</div>
```

[Django-Dokumentation Views](https://docs.djangoproject.com/en/6.0/topics/http/views/)

###### **Beispiel**
[![](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-04/scaled-1680-/image-1777039787848.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-04/image-1777039787848.png)

Durch die Auswahl der Dropdowns für Location und DNS-Address wird in der ```views.py``` die Funktion ```def ajax_select_options``` aufgerufen, der Request übergeben und dort ausgelesen.
Bei Wahl eines Standorts (Location) wird die ```order_location``` mit ```1``` oder ```2``` befüllt und das ```field``` wird auf ```dns_address``` gesetzt.  Dadurch wird in der Funktion der jeweilige Case getriggert für das als Nächstes zu ladende Dropdown (in dem Fall ```dns_address```).
Wurde dann aus dem neu geladenen Dropdown ```dns_address``` eine Adresse ausgewählt, passiert derselbe Vorgang mit dem Dropdown für die Proxies (```order_dns_address``` wird ```1``` oder ```2``` und ```field``` wird ```proxy_address```.

[![](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-04/scaled-1680-/image-1777039949615.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-04/image-1777039949615.png)

#### 2.1.2 HTML-Templates

[Django-Dokumentation HTML-Templates](https://docs.djangoproject.com/en/6.0/topics/templates/)

##### base.html

Diese Datei dient als Basis für (fast) alle anderen HTML-Dateien. Sie wird nicht alleine aufgerufen, aber alle anderen erben von ihr. Das dient der Modularität und Performance.
Wenn statische Ressourcen in die HTML-Dateien eingebunden werden sollen (z. B. HTMX oder W3.css) muss am Anfang der Datei folgender Befehl ausgeführt werden:

```
{% load static %}
```

Die Frameworks können dann wie folgt im \<head> eingebunden werden:

```html
<link rel="stylesheet" href="{% static '/order_portal/w3.css' %}">
<script src="{% static '/order_portal/htmx.min.js' %}"></script>
```

Durch Blöcke kann definiert werden, welche Teile der Base.html durch andere HTML-Dateien ersetzt werden:

```html
<body>
  {% block body_content %}
  {% endblock %}
</body>
```

##### main_page.html

Diese Datei ist eine kleine Startseite für die Nutzer des Portals. Sie erbt von der base.html, indem am Anfang der folgende Code eingebunden ist:

```
{% extends 'order_portal/base.html' %}
```

Durch die Blöcke wird nun definiert, an welcher Stelle in der base.html welche Daten der main_page.html eingebunden werden:

```html
{% block title %}Bestellportal{% endblock %}

{% block body_content %}
    <h1 class="w3-container w3-margin w3-card">Startseite des Bestellportals</h1>

    <div class="w3-container">
        <a href="orders/">
            <span style="width: 200px; height: 200px; float: left;" class="w3-container w3-card w3-margin-right w3-hover-light-gray">
                Bestellungsübersicht
            </span>
        </a>
        <a href="order_form/">
            <span style="width: 200px; height: 200px; float: left;" class="w3-container w3-card w3-margin-right w3-hover-light-gray">
                Neue Bestellung anlegen
            </span>
        </a>
    </div>
{% endblock %}
```

<p class="callout info">Dieser Aufbau mit den Blöcken ist für alle anderen HTML-Dateien (außer die partials) identisch.</p>

##### orders.html

In dieser Datei wird eine Liste von Bestellungen realisiert und dem Nutzendem angezeigt. Eine Besonderheit ist hierbei die Nutzung einer Schleife um keinen Code zu wiederholen:

```html
{% for order in latest_orders_list %} <!-- iterate over all entries in the list -->
    <tr>
        <table id="list_order_{{ order.id }}" class="w3-container w3-card w3-hover-light-gray w3-padding" style="width: 100%;" 
            hx-get="{% url 'order_portal:modal_order_detail' order.id %}" 
            hx-swap="afterend">
            <tr>
                <th class="w3-left-align" style="width: 30%;">Produkt:</th>
                <th class="w3-left-align" style="width: 70%;">{{ order.order_product.name }}</th>
            </tr>
            <tr>
                <th class="w3-left-align">Bestellt von:</th>
                <th class="w3-left-align">{{ order.user_name }}</th>
            </tr>
            <tr>
                <th class="w3-left-align">Bestellungsdatum:</th>
                <th class="w3-left-align">{{ order.order_date }}</th>
            </tr>
        </table>
    </tr>
{% endfor %}
```

##### detail.html

Diese Datei wird genutzt, um dem Nutzenden eine seperate Seite für die Details einer Bestellung zu bieten.

##### order_form.html

Diese Datei wird genutzt, um den Nutzenden ein Bestellformular anzeigen zu können. Durch die Nutzung von HTMX kann leider nicht auf eine Schleife zurückgegriffen werden, um über alle Felder des Formulars zu iterieren. Beispiel Textfeld:

```html
<div class="w3-container w3-border w3-border-indigo w3-margin w3-padding w3-group">
    <div class="w3-container w3-padding-small">
        <label class="w3-tag w3-round w3-cobalt" for="id_user_name">Name des Bestellers</label>
    </div>
    <div class="w3-padding-small">
        <input value="{{ form.user_name.value }}" class="w3-input" type="text" name="user_name" maxlength="255" required id="id_user_name">
    </div>
</div>
```

Beispiel Dropdown-Feld ohne HTMX:

```html
<div class="w3-container w3-border w3-border-indigo w3-margin w3-padding w3-group">
    <div class="w3-container w3-padding-small">
        <label class="w3-tag w3-round w3-cobalt" for="id_order_product">Produkt</label>
    </div>
    <div class="w3-padding-small">
        <select name="order_product" id="id_order_product" class="w3-select">
            {% for value, label in form.order_product.field.choices %}
                <option value="{{ value }}"
                    {% if value == form.order_product.value %}selected{% endif %}>
                    {{ label }}
                </option>
            {% endfor %}
        </select>
    </div>
</div>
```

<p class="callout info">Hierbei wird über die Auswahlmöglichkeiten des Feldes iteriert. "value" steht für den Primärschlüssel der Auswahlmöglichkeit, "label" für den Namen.</p>

Beispiel Dropdown-Feld mit HTMX:

```html
<div class="w3-container w3-border w3-border-indigo w3-margin w3-padding w3-group">
  <div class="w3-container w3-padding-small">
      <label class="w3-tag w3-round w3-cobalt" for="id_order_location">Ort des Rechenzentrums</label>
  </div>
  <div class="w3-padding-small">
      <select 
          name="order_location" 
          id="id_order_location"
          class="w3-select"
          hx-get="{% url 'order_portal:ajax_select_options' %}"
          hx-target="#id_order_dns_address"
          hx-trigger="change"
          hx-include="#id_order_location"
          hx-vals='{"field": "dns_address"}'>
          {% for value, label in form.order_location.field.choices %}
              <option value="{{ value }}"
                  {% if value == form.order_location.value %}selected{% endif %}>
                  {{ label }}
              </option>
          {% endfor %}
      </select>
  </div>
</div>
```

##### partials

Partials sind kleine HTML-Dateien, welche *nicht* von der base.html erben. Sie werden bei asynchronen Anfragen durch HTMX (oder Javascript generell) benutzt, um eine zusätzliche HTML-Komponente in eine bestehende Seite einzubauen. Welches Element durch die partials ersetzt wird, wird von "hx-target=" definiert. Dafür muss dem zu ersetzenden HTML-Objekt eine id vergeben werden durch:

```html
<div id="id_der_komponente"></div>
```

**cascading_select_options.html**

Dieses partial wird genutzt, um die Auswahlmöglichkeiten eines Dropdown-Feldes einzugrenzen.

```html
<option value=""></option>
{% for obj in options %}
    <option value="{{ obj.id }}">{{ obj.name }}</option>
{% endfor %}
```

Durch löschen der obersten Zeile könnte zusätzlich bewirkt werden, dass automatisch eine Auswahlmöglichkeit ausgewählt wird, sobald die asynchrone Anfrage beim Server ankommt.

**modal_order_detail.html**

Dieses patial wird genutzt um ein zusätzliches Fenster einzublenden, was beim Klick auf eine Bestellung in der Bestellübersicht unter der jeweiligen Bestellung angezeigt wird. Der Aufbau un die Funktionsweise ist identisch zur detail.html, hat zusätzlich nur noch eine Kopf- und Fußzeile.

Zusätzlich existiert noch eine Datei mmit dem Namen "blank_modal.html". Diese wird aufgerufen um die modal_order_detail.html" zu ersetzen. Dadurch wird dieses Element in der Benutzeroberfläche durch drücken auf das "x" wieder gelöscht.


## 3. Feinheiten der Frameworks

### 3.1 HTMX

Beispiel eines HTMX-Request:

```html
hx-get="{% url 'order_portal:ajax_select_options' %}"
hx-target="#id_order_dns_address"
hx-trigger="change"
hx-include="#id_order_location"
hx-vals='{"field": "dns_address"}'
```

- hx-get
  - an welche url wird die asynchrone Anfrage gesendet
  - entweder Nutzung von url, oder Ausschreiben der kompletten addresse (in diesem Fall: "/order_portal/ajax/select_options/")
- target
  - welche HTML-Komponente soll durch die Antwort ersetzt werden
  - Angabe durch id (Wichtig: das #-Symbol vor der id nicht vergessen)
- trigger
  - Was soll die asynchrone Anfrage auslösen?
  - Möglichkeiten zum Beispiel:
    - click - beim anklicken der Komponente (Wenn nichts spezifiziert wird, ist es immer click)
    - change - wenn sich eine Auswahl (z. B. in einem Dropdown) ändert
- include
  - ermöglicht es, Daten zusätzlicher HTML-Komponenten mit zu übergeben
  - auch hier wichtig, nicht das #-Symbol zu vergessen
- vals
  - ermöglicht es, zusätzliche Parameter in den Ajax-Request einzufügen
  - in diesem Beispiel wird eine zusätzliche variable "field" eingefügt, mit dem Wert "dns_address"


## 4. Zusätzliche Ressourcen

### 4.1 Django

[Django-Dokumentation](https://docs.djangoproject.com/en/6.0/)

[W3schools Django Tutorial](https://www.w3schools.com/django/index.php)

### 4.2 HTMX

[HTMX-Dokumentation](https://htmx.org/docs/)

[HTMX-Referenzen](https://htmx.org/reference/)

### 4.3 W3.css

[W3.css Tutorial](https://www.w3schools.com/w3css/defaulT.asp)

## 5. Authentifizierung

Für die Admin-Seite muss ein User erzeugt werden:

```bash
uv run python manage.py createsuperuser
```

Anschließend den Usernamen ```<admin-user>``` und das Passwort eingeben (siehe Keepass).

Aufruf der Admin-Seite siehe [6. Start der Anwendung](#bkmrk-6.-start-der-anwendu).

## 6. Start der Anwendung

Lokale Ausführung des Development-Django-Webservers (am Besten über VSCode):

```bash
uv run python manage.py runserver
```

Anschließend öffnet sich über VSCode direkt der Browser. Es kann zur Applikation navigiert werden mit:

```bash
http://127.0.0.1:8000/order_portal/
```

Bzw. zum Django-Adminportal:

```bash
http://127.0.0.1:8000/admin/
```

# Deployment des Bestellportals

Der entwickelte Python-Code auf dem Entwicklungsserver wird in einem [GitLab-Projekt](https://git.mgmt.<domain>.de/hcm/cloud-management-order-portal) eingecheckt und soll von dort aus via CI/CD Pipelines auch automatisiert auf den produktiven Webportal-Servern deployt werden.

### Pipelines

#### Python Packages
Für den [Entwicklungsserver](https://books.mgmt.<domain>.de/books/cloud-management/page/spezifikationen#bkmrk-python) und den [Terminalserver](https://books.mgmt.<domain>.de/books/cloud-management/page/terminalserver#bkmrk-proxy) wurde eine direkte Freischaltung über den Proyy auf PyPi gemacht.
Ohne eine eigene zentrale interne Registry, welche die Packages von PyPi herunterlädt und cacht und dann für alle Server zur Verfügung stellt, wird sich an dieser Vorgehensweise auch nichts ändern.

Problem ist, dass dann auch auf allen produktiven Portalservern diese Freischaltung gemacht werden müsste, um beim Deployment über die Pipeline per ```pip/uv``` die Pakete installieren zu können.

Wenn dies nicht gewollt ist und die interne Registry auch noch nicht zur Verfügung steht, wäre eine Alternative dazu, auf dem Entwicklungsserver mit ```pip download``` alle benötigten Pakete zu Downloaden, diese im Projektverzeichnis in einem eigenen Ordner abzulegen und mit ins Repo aufzunehmen sowie anschließend beim Deployment in der Pipeline mit ```pip/uv``` diese Pakete aus dem Ordner zu installieren. Somit ist von den Zielservern aus keine Verbindung ins Internet notwendig.

Die Verwendung vom ```uv.lock```-File (Erstellung beim Entwickeln) und dem ```uv sync```-Kommando beim Deployment über die Pipelines auf die produktiven Portalserver (siehe [Guidelines](https://books.mgmt.<domain>.de/books/betriebskonzept-cloud-management/page/guidelines#bkmrk-lockfile)) wäre somit hinfällig, da der oben beschriebene Weg bereits alle Python Packages enthält und installiert. Die Erstellung des ```venv``` müsste dann jedoch in einen extra Schritt ausgelagert werden (kann mit ```python3.12 -m venv ./path-to-new-venv``` erzeugt werden), da ```uv add``` nicht verwendet wird, welches dies mit übernimmt.

### Problematik von Secrets im Applikations-Code
#### API-Token
Ein Teil der Logik des Order Portals ist die Verbindung via RestAPI und dem Python Package ```python-gitlab``` zum GitLab Projekt für OpenTofu, um dort die Order-Files als CI/CD-Variable zur weiteren Verarbeitung durch Tofu abzulegen.

Für diese Verbindung wird ein GitLab-Project Access Token (Anlage CI/CD-Variable) sowie Pipeline Trigger Token erstellt ([Erstellung siehe Guideline zu API-Token](https://books.mgmt.<domain>.de/books/betriebskonzept-cloud-management/page/guidelines#bkmrk-api-token)) und verwendet, welche für die Entwicklung des Portals lokal in einem ```.env``` -File ([siehe Guideline](https://books.mgmt.<domain>.de/books/betriebskonzept-cloud-management/page/guidelines#bkmrk-.env)) abgelegt und im Python-Code des Webportals geladen werden können.

Die erstellten Token wurden im Keypass-File des Cloud Management Teams abgelegt:

[![](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-02/scaled-1680-/image-1772006840537.png)](https://books.mgmt.<domain>.de/uploads/images/gallery/2026-02/image-1772006840537.png)


<details>
  <summary>Pipeline Trigger Token for Order Portal</summary>
  Für das Order Portal, um die GitLab Pipelines über die GitLab RestAPI zu triggern.
</details>

<details>
  <summary>Project Access Token for Order Portal (CI/CD-Order-Vars)</summary>
  Für die Mutation von CI/CD-Variablen (Order-Variablen) des Order-Portals über die GitLab RestAPI.
</details>

<p class="callout info">Dies ist ein Test, um die Funktionsweise erörtern zu können. Die Token wurden daher vorerst direkt im Order Portal GitLab-Projekt (https://git.mgmt.<domain>.de/hcm/cloud-management-order-portal) erstellt. Zum Test muss während der ersten Entwicklung daher auch darin die CI/CD-Variable erstellt und gegebenenfalls eine Pipeline getriggert werden. Sobald das OpenTofu Projekt vorhanden ist, können die entsprechenden Token dann dort erzeugt und im Order Portal zur Anlage der Variablen und dem triggern der Pipeline verwendet werden. Die Token und angelegten Variablen/Pipelines können dann wieder aus dem Order Portal entfernt werden.</p>

Diese Token sind als Secrets anzusehen und können daher natürlich nicht mit in die GitLab-Repo des Order Portals hochgeladen werden. Daher wird das ```.env```-File aus dem Repo mit ```.gitignore``` ausgeschlossen.

**Das Problem ist dann natürlich:
Wie kommen die Token trotzdem auf die produktiven Order Portal-Server, wenn sie im Repo nicht vorhanden sind und somit per Pipeline nicht auf die Ziele verteilt werden können?**

<p class="callout success">Die Lösung sind hier Masked GitLab CI/CD-Variablen, welche im Order Portal erstellt werden. Diese Variablen können anschließend in der Pipeline zum Deployment des Order Portals verwendet werden. Die Pipeline muss auf den Zielservern ebenfalls wieder die .env-Datei erstellen, so wie diese auch beim Entwickeln lokal vorhanden war. Dadurch kann derselbe Code zum Laden der lokalen Umgebungsvariablen des Python-Projekts auch dort zur Anwendung kommen und der Zugriff auf das OpenTofu GitLab-Projekt stattfinden:</p>

```bash
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 

# accessing and printing value
print(os.getenv("Python"))
```

<p class="callout info">Zu einem späteren Zeitpunkt sollte dies noch optimiert werden, in dem in der Pipeline - anstelle von in GitLab angelegten CI/CD-Variablen, welche direkt die Token zum OpenTofu-Projekt enthalten - eine CI/CD-Variable angelegt wird, welche stattdessen den Token zum zentralen Privilege Management Tool (PAM) enthält. Hier wäre das Vorgehen dann ein wenig anders. In der Pipeline wird der Token aus der Variable verwendet, um diesen in das .env-File auf dem Zielsystem zu schreiben. Im Python-Code müsste dann wiederum mit dotenv das .env-File ausgelesen werden und zuerst das PAM über die RestAPI abgefragt werden, um die eigentlichen Token zum Zugriff auf das OpenTofu-Projekt zu erhalten.</p>

#### Django Secret Key
Die Variable ```SECRET_KEY``` aus dem ```settings.py```-File in Django enthält ein Secret, welches dazu dient, Hashwerte aus Passwörtern etc. zu erzeugen.

Bei der Entwicklung kann dieses Secret ebenfalls lokal in der ```.env```-Datei abgelegt werden. Vom Repo ist es ausgeschlossen. Daher muss auch hier in GitLab eine Hidden CI/CD-Variable angelegt werden, welche entweder direkt den Django-Secret-Key enthält oder den Token zum Zugriff auf das PAM.

Auch diese Variable kann dann in der Pipeline geladen (siehe [API-Token](#bkmrk-api-token)) und auf auf den Zielsystemen in das ```.env```-File geschrieben werden. Je nachdem wird im Python-Code dann die Variable aus dem ```.env```-File geladen und kann direkt für Django verwendet werden oder es muss zuerst mit dem ausgelesenen PAM-Token der eigentliche Secret-Key aus dem PAM geladen werden.