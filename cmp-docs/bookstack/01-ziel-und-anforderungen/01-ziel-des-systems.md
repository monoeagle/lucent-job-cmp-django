# Ziel des Systems

Das CloudMan Portal (CMP) ist ein Self-Service-Portal für IT-Service-Provisioning.
Dieses Kapitel beschreibt, was CMP leisten soll und auf welchem architektonischen
Grundsatz die Django-Variante bewusst aufbaut.

## 1. Ziel des Kapitels

Wer neu ins Projekt kommt, soll nach diesem Kapitel wissen: welches Problem CMP löst,
welche Kernprinzipien die Architektur bestimmen, und warum CMP Django kein API-First-
System ist, obwohl es ein Schwesterprojekt gibt, das genau das ist.

## 2. Das Problem

Anwender bestellen IT-Services (virtuelle Maschinen, Datenbanken, Container) heute über
Ticket- oder Mail-Prozesse. CMP ersetzt das durch einen Katalog mit parametrischen
Service-Vorlagen, einen Bestellassistenten und einen regelbasierten Genehmigungs-
Workflow, an dessen Ende automatisiertes Provisioning stehen soll.

## 3. Was CMP ist

CMP ist ein **Self-Service-IT-Provisioning-Portal**: Benutzer wählen einen Service aus
einem Katalog, füllen ein dynamisch aus dem Service-Schema erzeugtes Formular aus und
reichen eine Bestellung ein. Je nach hinterlegter Regel durchläuft die Bestellung eine
Genehmigung, bevor die Ressource aufgebaut wird
(`cmp-docs/docs/grundlagen/ueberblick.md`).

| Baustein | Zweck |
|---|---|
| Service-Katalog | Vorlagen mit parametrischem JSON-Schema (`ServiceTemplate`) |
| Bestellwizard | Dynamische Formulare aus den Template-Parametern |
| Approval-Workflow | Regelbasierte Genehmigung durch die Rolle Approver |
| Provisioning | Asynchrone Ausführung über Celery, Pipeline-Trigger (aktuell Stub) |
| Subscriptions | Verwaltung laufender, aus Bestellungen entstandener Services |
| Audit-Log | Revisionssicheres Protokoll von Aktionen |

Alle Bausteine existieren im Code; Kapitel 3 dieser Analyse-Reihe zeigt, welche davon in
der laufenden Anwendung tatsächlich miteinander verdrahtet sind und welche nicht (siehe
Abschnitt 6).

## 4. Kernprinzip: Server-Side Rendering statt API-First

CMP Django ist der **bewusste Gegenentwurf** zum Schwesterprojekt `lucent-job-CMP`, das
dasselbe fachliche Portal als Headless-JSON-Backend mit React-SPA umsetzt. Diese
Entscheidung steht ausdrücklich in `CLAUDE.md`: „Bewusstes Gegenstück zu mpp-TDD: kein
API-First, kein React, kein DRF."

CMP Django rendert die komplette Oberfläche serverseitig als HTML. Eine Prüfung aller
Views (`grep -rn "JsonResponse" cmp/apps`) findet **keinen** JSON-Endpunkt im
Anwendungscode — der Kontrakt zwischen Server und Browser ist Template ↔ Context, nicht
JSON-Schema (`cmp-docs/docs/referenz/architektur-vergleich.md`).

| Merkmal | CMP Django (SSR, dieses Projekt) | lucent-job-CMP (API-First, Schwester) |
|---|---|---|
| Rendering-Ort | Server — Django rendert HTML | Client — Browser rendert React |
| Backend liefert | fertiges HTML (`render()`) | JSON (`jsonify`) |
| API-Layer | keiner — bewusst kein DRF | versioniertes JSON-Backend |
| Auth | Session (django-allauth) | JWT / Token, stateless |
| Interaktivität | HTMX-Partials, punktuell | Client-seitige React-Logik |
| Port | 8000, ein Prozess | Backend 5000 / Frontend-Dev 3000, getrennt |

Das ist **keine Lücke gegenüber dem Schwesterprojekt**, sondern eine Grundsatz-
entscheidung: weniger bewegliche Teile, ein Prozess, eine Sprache, schnelleres
First-Paint, Grundfunktion ohne JavaScript — bezahlt mit fehlender Wiederverwendbarkeit
der Logik für einen Mobile- oder Drittsystem-Client
(`cmp-docs/docs/referenz/architektur-vergleich.md`).

## 5. Weitere Kernprinzipien

- **Thin Views** — Geschäftslogik liegt in `services.py`, nicht in Views oder Models
  (`CLAUDE.md`, `views.py → services.py → models.py`).
- **Django Admin als primäres Admin-Werkzeug** — Katalog, Regeln und Benutzer werden
  bewusst über Django Admin gepflegt, nicht über eine eigene Admin-Oberfläche
  (`.claude/rules/django.md`).
- **`ACCOUNT_SIGNUP_ENABLED=False`** — Self-Signup ist deaktiviert, Benutzer werden von
  einem Admin angelegt (`cmp/config/settings/base.py:99`).
- **TDD ist Pflicht** — jede Änderung entsteht test-first
  (`.claude/rules/testing.md`), belegt durch 347 Tests
  (`pytest --collect-only`, Stand 2026-07-22).
- **HTMX statt SPA** — HTMX liefert punktuelle Updates ohne Full-Page-Reload, ersetzt
  aber keinen API-Layer (`.claude/rules/htmx.md`).

## 6. Ist-Stand: gebaut, aber nicht durchgängig verdrahtet

Alle Bausteine aus Abschnitt 3 sind einzeln implementiert und getestet. Eine Prüfung des
laufenden Codes zeigt jedoch, dass die Kette „Bestellung einreichen → Genehmigung
anfordern → provisionieren → Subscription anlegen → protokollieren → benachrichtigen"
an mehreren Stellen nicht automatisch ausgelöst wird — zum Beispiel ruft
`OrderService.submit_order` (`cmp/apps/orders/services.py:61`) nach dem Einreichen
keinen Schritt auf, der eine `ApprovalRequest` erzeugt. Kapitel 3 dieser Analyse-Reihe
(`analyse/analyse-bestellportal.md`, Abschnitt 1c) und das Arbeitspaket AP-13
(`todo.md`) beschreiben diese Lücke im Detail; sie wird hier nur benannt, nicht
geschlossen.

## 7. Zusammenfassung

CMP löst das Problem manueller Bestellprozesse durch Katalog, Bestellassistent,
Genehmigungs-Workflow und automatisiertes Provisioning. Die Django-Variante setzt das
bewusst als Server-Side-Rendering-Anwendung um — Thin Views, Services, Django Admin,
Session-Auth, TDD-Pflicht — als kontrollierter Gegenentwurf zum API-First-
Schwesterprojekt. Die einzelnen Bausteine sind vollständig gebaut; ob und wie weit sie
im Betrieb bereits ineinandergreifen, ist Gegenstand der folgenden Kapitel.

> Quelle: CLAUDE.md, cmp-docs/docs/grundlagen/ueberblick.md, cmp-docs/docs/referenz/architektur-vergleich.md, cmp/config/settings/base.py, analyse/analyse-bestellportal.md — am Code geprüft 2026-07-22
