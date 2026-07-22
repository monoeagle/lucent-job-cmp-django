# Arbeitspakete & Roadmap

Arbeitspaket-Quelle: `todo.md` (offen) / `todo-erledigt.md` (fertig) im Repo-Root.
Status: **AP-0 … AP-10 fertig** (Backend B0–B9 + HTMX-Frontend) und **AP-22 erledigt**
(Zugriffskontrolle) — 347 Tests grün, v1.4.0. **AP-11 … AP-21 und AP-23 offen**.

### Offene Arbeitspakete

| AP | Titel | Auslöser |
|---|---|---|
| AP-11 | Container (Podman/Quadlets) | bewusst optional — Abwägung siehe [ADR-0001](../decisions/0001-deployment-native-vs-container.md) |
| AP-12 | Live-Updates (Django Channels) | stand im v1-Zielbild, nie gebaut (kein `channels` in den Requirements, `asgi.py` Django-Default); Benachrichtigungen aktualisieren bis dahin per Seiten-Reload |
| **AP-13** | **Bestellkette verdrahten** *(Vorrang)* | eingereichte Bestellungen erreichen keinen Genehmiger; Audit-Log und Benachrichtigungen zeigen nur Seed-Daten — [Analyse §1c](../intern/analyse-bestellportal.md) |
| AP-14 | Logging-Fundament | keine `LOGGING`-Konfiguration und kein einziger Logger-Aufruf im Projekt |
| AP-15 | HTMX-Fragment-Fix Audit-Log | Filter liefert die komplette Seite statt eines Fragments |
| AP-16 | Installer: Abräumzweig + Protokoll | kein `--uninstall`/`--purge`; Installation hinterlässt kein Protokoll |
| AP-17 | VM-Verifikation | `install.sh` lief nie auf echter Hardware; Idempotenz ist behauptet, nicht bewiesen |
| AP-18 | E-Mail-Benachrichtigungen | kein `send_mail`/`EMAIL_BACKEND` im Projekt |
| AP-19 | Security-Hardening (CSP + Rate Limiting) | keine CSP; Login-Brute-Force ungebremst |
| AP-20 | Echter GitLab-/OpenTofu-Client | Provisioning ist ein In-Memory-Stub |
| AP-21 | AD-/LDAP-Anbindung | kein `django-auth-ldap`; Rollen werden als Feld gepflegt |
| AP-23 | Rename-Reste und Doku-Drift | `npm run css:build` schlägt fehl und wird von `run.sh` verschluckt; URL-Referenz und Projektstruktur hinken dem Code hinterher |

Empfohlene Reihenfolge: **13 → 15 → 14 → 16+17 → 18 → 19 → 20 → 21**, AP-23 nebenher.
AP-18 und AP-20 zahlen erst ein, wenn AP-13 die Auslösepunkte geschaffen hat.
AP-22 (Zugriffskontrolle) stand hier zuerst und ist mit v1.4.0 erledigt.
AP-13 bis AP-21 stammen aus der [Analyse der Bestellportal-Fremddoku](../intern/analyse-bestellportal.md),
AP-22 (erledigt) und AP-23 aus dem Code-Abgleich beim Schreiben des Bookstack-Handbuchs.

Zusätzlich (nicht-AP):

- env-basierte Produktions-Settings + VM-Deployment-Anleitungen (online + offline)
- Doku-Veröffentlichung auf **GitHub Pages** inkl. **Oberflächen-Galerie** (13 Screenshots)
- **Offline-Release für AlmaLinux 9** (gebündelte Wheels + `install.sh`, GitHub-Release v1.3.1 · Doku v1.3.3)
- Bugfix Bestell-Flow (`location`-Pflichtparameter) + Doku-/Heatmap-Politur

## AP-Überblick

<img src="../../images/mermaid/entwicklung-arbeitspakete-1.svg" alt="Diagramm 1 aus entwicklung/arbeitspakete.md">

## Roadmap-Gantt

> Spannen **schematisch**: Die Git-Historie wurde zu v1.0.0 (2026-03-29) gestaucht — die
> AP-**Reihenfolge** ist real, die Tagesspannen illustrieren nur den Ablauf. Für AP-13 … AP-21
> sind die Spannen **Schätzungen**, keine Zusagen.
> Offen: AP-11, AP-12 sowie AP-13 … AP-21 (siehe Tabelle oben).

<img src="../../images/mermaid/entwicklung-arbeitspakete-2.svg" alt="Diagramm 2 aus entwicklung/arbeitspakete.md">
