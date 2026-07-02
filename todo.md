# MPP Django — Todo (offen)

> AP-Quelle (offen). Fertige APs → `todo-erledigt.md`. Stand 2026-07-03.
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

## AP-12 · Live-Updates via Django Channels (WebSocket)
> Kontext: Channels stand von Anfang an im Zielbild (v1-Design: „Channels statt SSE"),
> ist aber nie gebaut worden — kein `channels` in requirements, `config/asgi.py` ist
> Django-Default, Benachrichtigungen aktualisieren nur per Seiten-Reload.
> Doku-Behauptung „live via WebSocket" wurde 2026-07-03 korrigiert; dieses AP macht sie wahr.
- [ ] Dependencies: `channels` + `channels-redis` (auch ins Offline-Wheelhouse, cp312)
- [ ] `config/asgi.py` → ProtocolTypeRouter (http + websocket), `CHANNEL_LAYERS` (Redis) in Settings
- [ ] NotificationConsumer + Routing (Auth via Session, Gruppe je User); Push aus den Services (`channel_layer.group_send`)
- [ ] Frontend: Badge/Liste live aktualisieren (HTMX `ws`-Extension oder kleines Vanilla-JS)
- [ ] Deployment nachziehen: gunicorn mit Uvicorn-Workern auf `config.asgi` (statt `config.wsgi`), nginx-`mpp.conf` um WebSocket-Upgrade (`Upgrade`/`Connection`-Header) erweitern — `deploy/install.sh` + VM-Doku
- [ ] TDD: Consumer-Tests (`channels.testing`), Service-Push-Tests, Settings-Tests
- **DoD:** Benachrichtigungs-Badge aktualisiert ohne Reload · Tests grün (inkl. Consumer) · Offline-Install mit erweitertem Wheelhouse verifiziert · Doku (Architektur/Oberfläche/Deployment) sagt wieder die Wahrheit
