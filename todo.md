# MPP Django — Todo (offen)

> AP-Quelle (offen). Fertige APs → `todo-erledigt.md`. Stand 2026-06-18.
> Architektur: Django + HTMX + allauth (kein API-First/React/DRF). Backend B0–B9 + Frontend fertig.

## AP-11 · Container-Setup (Podman/Quadlets, optional)
> Abwägung & Begründung: `docs/decisions/0001-deployment-native-vs-container.md`.
> Native systemd-Installation (`deploy/install.sh` + Wheelhouse) bleibt der Default
> für air-gapped Single-VM; Container nur bei Multi-Host / Dev-Prod-Parität /
> immutable Rollback. RHEL-nativ → **Podman**, nicht Docker-CE.
- [ ] Containerfile (App, Multi-Stage, rootless-tauglich)
- [ ] Quadlet-Units **oder** `podman-compose.yml` (web + PostgreSQL + Redis + Celery-Worker), SELinux-`:Z`-Volumes
- [ ] Entrypoint (migrate + collectstatic; seed optional)
- [ ] Offline-Image-Transport (`podman save`/`load`, Base-Image gespiegelt) — air-gapped-tauglich
- **DoD:** `podman-compose up` (bzw. Quadlets via `systemctl`) startet Portal lauffähig · 239 Tests grün im Container · Doku + ADR nachgezogen
