# MPP Django — Todo (offen)

> AP-Quelle (offen). Fertige APs → `todo-erledigt.md`. Stand 2026-06-18.
> Architektur: Django + HTMX + allauth (kein API-First/React/DRF). Backend B0–B9 + Frontend fertig.

## AP-11 · Docker-Setup
- [ ] Dockerfile (App, Multi-Stage)
- [ ] docker-compose (web + PostgreSQL + Redis + Celery-Worker)
- [ ] Entrypoint (migrate + seed + collectstatic)
- **DoD:** `docker compose up` startet Portal lauffähig · 230 Tests grün im Container · Doku nachgezogen
