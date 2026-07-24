# CloudMan Portal — Guide

Willkommen! Dieser Guide bringt dir das **CloudMan Portal (CMP)** von Grund auf bei —
vom „Was ist das überhaupt?" bis zu deinem ersten eigenen Code-Beitrag.

Er ist als **Lernpfad** gedacht: Die Kapitel bauen aufeinander auf. Arbeite sie
der Reihe nach durch. Jedes Kapitel sagt dir am Anfang, was du danach kannst.

> **Diese Doku ist bewusst eigenständig.** Sie steht *neben* der ausführlichen
> Referenzdokumentation unter [`cmp-docs/`](../../cmp-docs/) — die ist zum
> *Nachschlagen*, dieser Guide ist zum *Lernen*. Wenn du hier durch bist, findest
> du dort jedes Detail wieder.

---

## Der Lernpfad

### Teil 0 — Ankommen
Worum geht es hier eigentlich, und wie liest du diese Doku?

| # | Kapitel | Das lernst du |
|---|---------|---------------|
| 00 | [Willkommen](00-willkommen.md) | Was CMP ist, für wen, und wie du diesen Guide nutzt |
| 01 | [Das große Bild](01-das-grosse-bild.md) | Der Zweck des Portals in einem Diagramm |
| 02 | [Ziele & Anforderungen](02-ziele-und-anforderungen.md) | Was CMP leisten soll: Ziele, Anwendungsfälle, funktionale & nicht-funktionale Anforderungen |

### Teil 1 — Fundament (Konzepte, noch kein Code)
Die Begriffe und Abläufe, ohne die alles andere verwirrend bleibt.

| # | Kapitel | Das lernst du |
|---|---------|---------------|
| 03 | [Die Fachdomäne](03-fachdomaene.md) | Katalog, Bestellung, Genehmigung, Provisioning, Abo — mit ER-Diagramm |
| 04 | [Rollen & Rechte](04-rollen-und-rechte.md) | Wer darf was: requester · approver · admin · superadmin |
| 05 | [Der Bestell-Lebenszyklus](05-bestell-lebenszyklus.md) | Wie eine Bestellung ihre Zustände durchläuft — **Zustandsdiagramm** |

### Teil 2 — Die Technik verstehen
Wie der Code aufgebaut ist und wie die Teile zusammenspielen.

| # | Kapitel | Das lernst du |
|---|---------|---------------|
| 06 | [Architektur](06-architektur.md) | Thin Views → Services → Models, und die 10 Apps |
| 07 | [Async & Provisioning](07-async-und-provisioning.md) | Celery, Hintergrund-Tasks — **Sequenzdiagramm** |
| 08 | [Frontend: HTMX & DaisyUI](08-frontend-htmx-daisyui.md) | Wie die Oberfläche ohne großes JavaScript funktioniert |

### Teil 3 — Selbst loslegen
Von der leeren Maschine bis zum ersten gemergten Beitrag.

| # | Kapitel | Das lernst du |
|---|---------|---------------|
| 09 | [Setup lokal](09-setup-lokal.md) | Projekt zum Laufen bringen — inkl. typischer Stolpersteine |
| 10 | [So arbeiten wir](10-so-arbeiten-wir.md) | TDD-Pflicht, Tests, Code-Regeln, Git-Konventionen |
| 11 | [Dein erster Beitrag](11-dein-erster-beitrag.md) | Ein kleines Feature end-to-end, im TDD-Zyklus |

### Teil 4 — Betrieb (zum Verständnis)
Was passiert, wenn das Portal „echt" läuft?

| # | Kapitel | Das lernst du |
|---|---------|---------------|
| 12 | [Wie es in Produktion läuft](12-wie-es-in-produktion-laeuft.md) | Server, Prozesse, Deployment — **Topologie-Diagramm** |
| 13 | [Rundgang durch die Oberfläche](13-rundgang.md) | Die wichtigsten Screens: Login → Dashboard → Bestellen → Genehmigen → Audit |

### Anhang
| # | Kapitel | Zweck |
|---|---------|-------|
| A | [Glossar](A-glossar.md) | Alle Begriffe kurz erklärt |
| B | [Spickzettel](B-spickzettel.md) | Die wichtigsten Befehle auf einen Blick |
| C | [Einen neuen Service anlegen](C-neuen-service-anlegen.md) | Rezept: neuen bestellbaren Service kapseln (Katalog-Template + Provisioning-Client) |

---

## Voraussetzungen

Du solltest mitbringen (oder parallel nachlernen):

- **Python-Grundlagen** — Funktionen, Klassen, Module
- **Ein bisschen Django-Neugier** — wir erklären das Projektspezifische, aber
  „Was ist ein Model/View/Template?" solltest du nachschlagen können
- **Git-Basics** — clone, branch, commit, push

Kein Vorwissen nötig zu: Celery, HTMX, dem Provisioning-Ablauf oder der Deployment-Umgebung.
Das lernst du hier.

---

## Wie die Diagramme funktionieren

Dieser Guide nutzt **Mermaid**-Diagramme direkt im Text. GitHub und VS Code
(mit Markdown-Preview) rendern sie automatisch als Bild. Du brauchst **kein
Build-Werkzeug** — einfach die `.md`-Datei öffnen.

Siehst du irgendwo einen Codeblock mit ` ```mermaid ` statt eines Bildes?
Dann öffne die Datei auf GitHub oder in der VS-Code-Vorschau.

---

## Konventionen in diesem Guide

- 💡 **Merke** — etwas, das du dir einprägen solltest
- ⚠️ **Achtung** — ein typischer Fehler oder Stolperstein
- 🔍 **Im Code nachsehen** — wo du das Beschriebene selbst findest
- 🚧 **Status: Gerüst** — dieses Kapitel ist noch in Arbeit
