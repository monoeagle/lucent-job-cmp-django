# Arbeitspakete & Roadmap

Arbeitspaket-Quelle: `todo.md` (offen) / `todo-erledigt.md` (fertig) im Repo-Root.
Status: **AP-0 … AP-10 fertig** (Backend B0–B9 + HTMX-Frontend, 326 Tests grün, v1.1.0), **AP-11 Container (Podman/Quadlets) offen** — Abwägung Native-vs-Container siehe [ADR-0001](../decisions/0001-deployment-native-vs-container.md) —, **AP-12 Live-Updates (Django Channels) offen** — Channels stand im v1-Zielbild, ist aber noch nicht gebaut (kein `channels` in den Requirements, `asgi.py` Django-Default); Benachrichtigungen aktualisieren bis dahin per Seiten-Reload.
Zusätzlich (nicht-AP):

- env-basierte Produktions-Settings + VM-Deployment-Anleitungen (online + offline)
- Doku-Veröffentlichung auf **GitHub Pages** inkl. **Oberflächen-Galerie** (13 Screenshots)
- **Offline-Release für AlmaLinux 9** (gebündelte Wheels + `install.sh`, GitHub-Release v1.1.0)
- Bugfix Bestell-Flow (`location`-Pflichtparameter) + Doku-/Heatmap-Politur

## AP-Überblick

<img src="../../images/mermaid/entwicklung-arbeitspakete-1.svg" alt="Diagramm 1 aus entwicklung/arbeitspakete.md">

## Roadmap-Gantt

> Spannen **schematisch**: Die Git-Historie wurde zu v1.0.0 (2026-03-29) gestaucht — die
> AP-**Reihenfolge** ist real, die Tagesspannen illustrieren nur den Ablauf.
> AP-11 (Container/Podman) und AP-12 (Live-Updates/Channels) offen.

<img src="../../images/mermaid/entwicklung-arbeitspakete-2.svg" alt="Diagramm 2 aus entwicklung/arbeitspakete.md">
