# Oberflächen

Galerie der wichtigsten Screens des Marketplace Portals — Klick auf ein Bild
öffnet die Lightbox-Ansicht (Zoom, Vor/Zurück-Navigation, ESC zum Schließen).

Die Oberfläche ist rollenbasiert: **Requester** bestellen Services, **Approver**
genehmigen, **Admin/Superadmin** verwalten Katalog, Regeln und Audit. Die linke
Navigation und die sichtbaren Bereiche richten sich nach der Rolle des
angemeldeten Benutzers.

---

## Anmeldung

<img src="../../images/screenshots/Screenshot_01_mpp.png"
     alt="Login-Seite des MPP Django: Anmeldeformular mit Feldern für Benutzername und Passwort sowie Anmelden-Button auf der Lucent-Oberfläche.">

Session-basierte Anmeldung über django-allauth. Self-Service-Registrierung ist
deaktiviert (`ACCOUNT_SIGNUP_ENABLED=False`) — alle Benutzer werden vom Admin
angelegt. Die Anmeldung erfolgt über **Benutzername** und Passwort.

---

## Dashboard

<img src="../../images/screenshots/Screenshot_02_mpp.png"
     alt="Requester-Dashboard: vier KPI-Kacheln (Offene Bestellungen, Offene Genehmigungen, Aktive Services, Templates), Karten für Benachrichtigungen und Review Requests, Tabelle der letzten Bestellungen, Donut-Diagramm 'Bestellungen nach Status', Liste beliebter Services und ein Liniendiagramm 'Bestellungen pro Monat'.">

Die Startseite nach dem Login. Oben vier KPI-Kacheln (Offene Bestellungen,
Offene Genehmigungen, Aktive Services, Templates), darunter die letzten
Bestellungen mit Status-Badges, ein Donut-Diagramm „Bestellungen nach Status",
die beliebtesten Services und der Bestell-Verlauf pro Monat. Die Diagramme
nutzen lokal gebundeltes Chart.js (keine CDN-Abhängigkeit).

---

## Service-Katalog (Shop)

<img src="../../images/screenshots/Screenshot_03_mpp.png"
     alt="Service-Katalog: Suchfeld und Kategorie-Filter oben, darunter zwei Service-Karten (Linux VM, Windows VM) mit Kategorie-Badge 'compute', Kurzbeschreibung, Parameter-Anzahl '30 Parameter · v1' und Details-Button.">

Der Katalog listet alle bestellbaren Services als Karten. Ein Suchfeld und ein
Kategorie-Filter grenzen die Auswahl live ein. Jede Karte zeigt Kategorie,
Kurzbeschreibung, Parameter-Anzahl und Version. Der **Details**-Button führt zur
Service-Detailseite.

---

## Katalog-Detail — Parameter-Übersicht

<img src="../../images/screenshots/Screenshot_04_mpp.png"
     alt="Detailseite des Service-Templates 'Linux VM': Titel mit Kategorie-Badge 'compute' und Version v1, darunter eine Parameter-Tabelle mit Spalten Name, Typ, Pflicht, Standard, Optionen über alle 30 Parameter (Systemtyp, Mandant, Standort, CPU Cores, RAM …). Unten der Button 'Jetzt bestellen'.">

Die Detailseite eines Templates zeigt die vollständige Parameter-Spezifikation:
Name, Typ (`enum`, `string`, `integer`, `boolean`), Pflichtangabe, Default und
Optionen. Beim **Linux VM** sind das 30 Parameter über Kontext, Netzwerk, Sizing
und Betrieb. „Jetzt bestellen" öffnet das Bestellformular.

---

## Bestellformular — Linux VM bestellen

<div class="adb-shot-compare">
  <figure>
    <img src="../../images/screenshots/Screenshot_05_mpp.png"
         alt="Leere Bestellmaske 'Linux VM bestellen': gruppierte Abschnitte Kontext, Netzwerk, Platzierung, Betriebssystem, VM Sizing, Server-Informationen usw. mit leeren Dropdowns/Feldern. Die Zusammenfassung rechts ist noch leer.">
    <figcaption>Leere Maske — die Zusammenfassung rechts ist noch leer. <em>(oben beschnitten · Klick = ganzes Bild)</em></figcaption>
  </figure>
  <figure>
    <img src="../../images/screenshots/Screenshot_05b_mpp.png"
         alt="Dieselbe Bestellmaske vollständig ausgefüllt: alle Dropdowns gewählt, Zahlen-/Textfelder befüllt, Backup-Checkboxen aktiv. Die Zusammenfassung rechts listet nun alle Werte (Standort, Mandant, CPU Cores, RAM, Template, E-Mails, Backupstatus …) und zeigt den grünen Button 'Zur Bestellung hinzufügen'.">
    <figcaption>Ausgefüllt — dieselbe Maske; die <strong>Zusammenfassung</strong> rechts füllt sich live mit. <em>(oben beschnitten · Klick = ganzes Bild)</em></figcaption>
  </figure>
</div>

Das All-in-One-Formular fasst Kontext, alle Template-Parameter und die Menge auf
einer Seite zusammen, gruppiert nach Abschnitten (Kontext, Netzwerk, Platzierung,
Betriebssystem, VM Sizing, Server-Informationen, Software-Management, Backup).
Rechts läuft eine **Live-Zusammenfassung** der gewählten Werte mit, die sich mit
jeder Eingabe aktualisiert — der Vergleich oben zeigt den Bereich, der sich füllt:
links leer, rechts vollständig. Validierung erfolgt zweistufig: Django-Form
(Feldtypen) und Service-Layer (`TemplateValidator` gegen das Template-Schema).

---

## Bestellungen — Übersicht

<img src="../../images/screenshots/Screenshot_06_mpp.png"
     alt="Bestellübersicht: Tabs 'Alle Bestellungen' / 'Meine Bestellungen', Status-Filterchips (Alle, Entwurf, Eingereicht, Genehmigung, Bereitstellung, Aktiv, Fehlgeschlagen, Abgelehnt) und eine Tabelle mit Spalten Nummer, Notizen, Besteller, farbigen Status-Badges, Positionen, Erstellt-Datum und Details-Button.">

Die Bestellliste mit Filter-Tabs und Status-Chips. Jede Zeile zeigt Nummer,
Notiz, Besteller, farbcodierten Status (Entwurf, Eingereicht, Genehmigung,
Abgeschlossen …), Positionsanzahl und Erstellzeitpunkt. „Details" öffnet die
Bestelldetailseite.

---

## Bestelldetail

<img src="../../images/screenshots/Screenshot_07_mpp.png"
     alt="Detailansicht der Bestellung #12 mit Status-Badge 'Eingereicht': Kopf mit Notiz, Erstelldatum und Besteller, darunter der Abschnitt Positionen (1) mit der Position 'Linux VM' und allen aufgelösten Parameterwerten in einem Raster (ram_gb 16, cpu_cores 8, location standort2, os_template ubuntu2204 …).">

Die Detailseite einer Bestellung zeigt Kopfdaten (Status, Notiz, Besteller) und
alle Positionen mit ihren vollständig aufgelösten Parameterwerten im Raster. Der
Status-Badge spiegelt die Position im Workflow (Entwurf → Eingereicht →
Genehmigung → Bereitstellung → Aktiv).

---

## Benachrichtigungen

<img src="../../images/screenshots/Screenshot_08_mpp.png"
     alt="Benachrichtigungs-Seite: Tabs 'Alle' / 'Ungelesen', Button 'Alle als gelesen markieren', darunter Benachrichtigungskarten mit Typ-Badges (provisioning, order), Titel, Text, Zeitstempel und einem Punkt-Indikator für ungelesene Einträge.">

Das Benachrichtigungs-Center bündelt System-Events (Bereitstellung
abgeschlossen, Bestellung eingereicht …) mit Typ-Badges und Lesestatus.
Einzelne Einträge oder alle auf einmal lassen sich als gelesen markieren. Updates
werden über Django Channels (WebSocket) live ausgeliefert.

---

## Abonnements (Subscriptions)

<img src="../../images/screenshots/Screenshot_09_mpp.png"
     alt="Seite 'Meine Subscriptions': Tabelle mit Spalten Nummer, Service, Status-Badge 'active', Gueltig ab, Gueltig bis und Details-Button für die Services Linux VM und Windows VM.">

Aktive Service-Abonnements des Benutzers — pro Eintrag Service, Status,
Gültigkeitszeitraum und ein Detail-Link. Ein Abonnement entsteht aus einer
erfolgreich bereitgestellten Bestellung und kann hier eingesehen und gekündigt
werden.

---

## Profil

<img src="../../images/screenshots/Screenshot_10_mpp.png"
     alt="Profil-Karte: Benutzername test-requester, E-Mail (leer), Rolle als Badge 'requester' und 'Mitglied seit' Datum.">

Die Profilseite zeigt Benutzername, E-Mail, Rolle und Beitrittsdatum. Benutzer
und Rollen werden ausschließlich über den Admin gepflegt.

---

## Genehmigungen (Approver)

<img src="../../images/screenshots/Screenshot_11_mpp.png"
     alt="Genehmigungs-Queue der Approver-Rolle: Filter-Tabs (Ausstehend, Genehmigt, Abgelehnt, Alle), Bulk-Aktionen 'Ausgewählte genehmigen' / 'Ausgewählte ablehnen' mit Checkboxen, zwei ausstehende Anträge ('Abloesung alter NAS-Appliance', 'Erweiterung Webfarm fuer Black Friday') mit Datum und Status-Badge 'Ausstehend'. In der Navigation erscheint zusätzlich 'Review Requests'.">

Angemeldet als **Approver** erscheint die Genehmigungs-Queue (Menüpunkt „Review
Requests"). Anträge lassen sich einzeln oder per Mehrfachauswahl genehmigen bzw.
ablehnen; Filter-Tabs trennen ausstehende, genehmigte und abgelehnte Anträge.

---

## Audit-Log (Admin)

<img src="../../images/screenshots/Screenshot_12_mpp.png"
     alt="Audit-Log der Superadmin-Rolle: Filterfelder für Aktion und Ressourcentyp, CSV-Export-Button, Tabelle mit Zeitpunkt, Aktion (system_startup, template_updated, order_created, order_submitted), Ressource, Benutzer und Detail-JSON. Links ein zusätzlicher Admin-Navigationsblock (Admin Dashboard, Konfiguration, Regeln, Audit-Log, Django Admin).">

Als **Admin/Superadmin** wird ein zusätzlicher Admin-Navigationsblock sichtbar
(Admin Dashboard, Konfiguration, Regeln, Audit-Log, Django Admin). Das Audit-Log
protokolliert revisionssicher alle relevanten Aktionen mit Zeitpunkt, Akteur,
Ressource und Detail-Payload und lässt sich nach CSV exportieren.

---

## Django-Admin

<img src="../../images/screenshots/Screenshot_13_mpp.png"
     alt="Django-Verwaltungsoberfläche (Django-Admin): Abschnitte für Accounts (Users), Approvals (Approval requests, Approval rules), Audit, CMDB (Availability rules, Context restrictions, User tenant assignments), Notifications, Orders, Provisioning, Service Catalog, Subscriptions und Websites mit Hinzufügen-/Ändern-Links.">

Der Django-Admin ist das primäre Administrationswerkzeug: Benutzerverwaltung,
Genehmigungsregeln, CMDB-Kontextregeln, Service-Templates, Bestellungen,
Abonnements und Audit-Logs werden hier gepflegt. Der Admin legt insbesondere alle
Benutzerkonten an.
