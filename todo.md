# CloudMan Portal (CMP) — Todo (offen)

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
- **DoD:** `podman-compose up` (bzw. Quadlets via `systemctl`) startet Portal lauffähig · 317 Tests grün im Container · Doku + ADR nachgezogen

## AP-12 · Live-Updates via Django Channels (WebSocket)
> Kontext: Channels stand von Anfang an im Zielbild (v1-Design: „Channels statt SSE"),
> ist aber nie gebaut worden — kein `channels` in requirements, `config/asgi.py` ist
> Django-Default, Benachrichtigungen aktualisieren nur per Seiten-Reload.
> Doku-Behauptung „live via WebSocket" wurde 2026-07-03 korrigiert; dieses AP macht sie wahr.
- [ ] Dependencies: `channels` + `channels-redis` (auch ins Offline-Wheelhouse, cp312)
- [ ] `config/asgi.py` → ProtocolTypeRouter (http + websocket), `CHANNEL_LAYERS` (Redis) in Settings
- [ ] NotificationConsumer + Routing (Auth via Session, Gruppe je User); Push aus den Services (`channel_layer.group_send`)
- [ ] Frontend: Badge/Liste live aktualisieren (HTMX `ws`-Extension oder kleines Vanilla-JS)
- [ ] Deployment nachziehen: gunicorn mit Uvicorn-Workern auf `config.asgi` (statt `config.wsgi`), nginx-`cmp.conf` um WebSocket-Upgrade (`Upgrade`/`Connection`-Header) erweitern — `deploy/install.sh` + VM-Doku
- [ ] TDD: Consumer-Tests (`channels.testing`), Service-Push-Tests, Settings-Tests
- **DoD:** Benachrichtigungs-Badge aktualisiert ohne Reload · Tests grün (inkl. Consumer) · Offline-Install mit erweitertem Wheelhouse verifiziert · Doku (Architektur/Oberfläche/Deployment) sagt wieder die Wahrheit

---

> **AP-13 … AP-21** ergänzt am 2026-07-22 aus der Analyse der Bestellportal-Fremddoku
> (`analyse/analyse-bestellportal.md`, Doku-Seite unter „Intern"). Jede Zeile dort ist
> grep-belegt gegen den echten Code. **AP-13 ist mit v1.5.0 erledigt** (→ `todo-erledigt.md`).
> Empfohlene Reihenfolge der offenen: **15 → 14 → 16+17 → 18 → 19 → 20 → 21**.

## AP-14 · Logging-Fundament
> **Befund:** `grep LOGGING cmp/config/` und `grep getLogger cmp/` → **je 0 Treffer**.
> CMP hat keine eigene Logging-Konfiguration und keinen einzigen Logger-Aufruf.
- [ ] `LOGGING`-Dict in `config/settings/base.py`, Level je Umgebung überschreibbar
- [ ] Logger je Domäne: `cmp.orders`, `cmp.approvals`, `cmp.provisioning`, `cmp.audit`
- [ ] Ausgabe nach stdout → journald (passt zur systemd-Installation); Datei nur mit Rotation
- [ ] Seed-Schritte über Logger statt `self.stdout.write`
- [ ] Abgrenzung dokumentieren: Logging ist technisch, Audit-Log ist fachlich — keins ersetzt das andere
- **DoD:** Statuswechsel und Provisioning erscheinen im Journal · Tests prüfen die Logger-Aufrufe

## AP-15 · HTMX-Fragment-Fix Audit-Log
> **Befund:** `templates/audit/audit_list.html:15-29` feuert `hx-get` auf `#audit-table`,
> aber `AuditLogListView` (`apps/audit/views.py:9`) hat keinen htmx-Zweig — die **komplette
> Seite** inkl. `base.html` wird in ein `<div>` derselben Seite geswappt.
- [ ] Partial `templates/audit/partials/audit_table.html`
- [ ] `get_template_names()` mit `if self.request.htmx` — Vorlage: `apps/catalog/views.py:25`
- [ ] Übrige HTMX-Stellen gegenprüfen (aktuell nur Katalog + Audit)
- **DoD:** Filter tauscht nur die Tabelle · keine doppelten IDs · im Browser verifiziert

## AP-16 · Installer: Abräumzweig + Protokoll
> **Befund:** `grep uninstall|purge deploy/install.sh` → 0 Treffer. Für eine wiederholt
> aufzusetzende Testumgebung fehlt die Gegenrichtung. Zudem wird nichts persistiert —
> wer die Konsole schließt, hat kein Protokoll.
- [ ] `--uninstall`: Dienste stoppen/deaktivieren, Units + nginx-Site + App-Verzeichnis entfernen (**DB und `.env` bleiben**)
- [ ] `--purge`: zusätzlich DB-Rolle, Datenbank, `.env`, Logs — mit expliziter Rückfrage
- [ ] `--dry-run` für beide; Menüpunkt „4) Entfernen"
- [ ] Beide über dieselben `lib.sh`-Bausteine wie die Installation
- [ ] Abschlussprotokoll → `/var/log/cmp/install-<zeitstempel>.log` + `/opt/cmp/INSTALL-REPORT.txt`:
      Version, OS, Ports, Units, TLS-Modus, DB, Migrationsstand, Seed-Ergebnis, Portal-URL — **ohne Secrets**
- **DoD:** Install → Uninstall → Install läuft auf der VM sauber durch · Protokoll vollständig · keine Secrets darin

## AP-17 · VM-Verifikation (offen seit v1.3.0)
> **Befund:** `deploy/install.sh:23` **behauptet** Idempotenz — das Skript lief nie auf
> echter Hardware. Auch die Laufzeit-Topologie-Doku ist aus dem Code abgeleitet, nie beobachtet.
- [ ] Offline-Release auf die AlmaLinux-TestVM, `install.sh` ausführen
- [ ] Zugriff vom Client über `http://<fqdn>/` — erwartete Stolpersteine: FQDN statt IP (`ALLOWED_HOSTS`), hosts-Eintrag ohne DNS
- [ ] **Zweiter Lauf** als Idempotenz-Nachweis
- [ ] `systemctl status cmp-web cmp-celery`, `ss -tlnp` gegen die dokumentierten Ports/Units
- [ ] Abweichungen in `betrieb/laufzeit-topologie.md` korrigieren statt die Doku zu behalten
- **DoD:** Jede Topologie-Aussage belegt oder korrigiert · Idempotenz bewiesen statt behauptet

## AP-18 · E-Mail-Benachrichtigungen
> **Befund:** `grep send_mail|EMAIL_BACKEND cmp/` → **0 Treffer**. FM_AG03/FM_GE04 der
> Fremddoku-Anforderungen sind unerfüllt. Setzt AP-13 voraus (vorher gibt es keine Auslösepunkte).
- [ ] `EMAIL_*` via `django-environ`; Konsolen-Backend in dev, `locmem` in Tests
- [ ] Templates: neue Genehmigung (an Genehmiger), genehmigt/abgelehnt (an Besteller), fertig/fehlgeschlagen
- [ ] Versand aus den Services an denselben Punkten wie die In-App-Benachrichtigung
- [ ] Fehlerverhalten: Mailausfall darf den Workflow **nicht** abbrechen
- **DoD:** Mail bei Approve/Reject/neuer Genehmigung · Tests mit `locmem` · Ausfall bricht nichts ab

## AP-19 · Security-Hardening (CSP + Rate Limiting)
> **Befund:** `grep Content-Security cmp/ deploy/` → 0 Treffer; kein Rate Limiting →
> Login-Brute-Force ist ungebremst. Alle Assets liegen bereits lokal, eine strenge CSP
> ist damit fast kostenlos.
- [ ] Inline-`<script>` aus `base.html`, `dashboard.html`, `approval_queue.html` in Dateien auslagern
- [ ] CSP im nginx-Block (`deploy/lib.sh:334`): `default-src 'self'`, ohne `unsafe-inline`
- [ ] Login-Throttling (`django-axes` oder nginx `limit_req`) — Offline-Wheelhouse beachten
- **DoD:** CSP aktiv, Portal unverändert bedienbar (im Browser geprüft) · Brute-Force gebremst · Tests grün

## AP-20 · Echter GitLab-/OpenTofu-Client
> **Befund:** `apps/provisioning/clients.py` ist der `GitLabStubClient` (In-Memory-Dict,
> `uuid4()` als Pipeline-ID) — kein HTTP-Call, kein `python-gitlab`. FM_AG02 unerfüllt.
> Setzt AP-13 voraus.
- [ ] `python-gitlab` in Requirements **und** Offline-Wheelhouse (cp312)
- [ ] CI/CD-Variable aktualisieren + Pipeline triggern; Order-Manifest als JSON
- [ ] Token via systemd `EnvironmentFile=` (`0600`) — **nicht** `.env` im App-Verzeichnis
- [ ] Echter Rückkanal: Polling-Task ersetzt das Sofort-Abschließen aus AP-13 (Lücke 3)
- [ ] Stub bleibt für Dev/Tests wählbar (Client per Settings austauschbar)
- [ ] Doku-Kapitel „OpenTofu-Export" + „GitLab-Schnittstelle" **erst danach** schreiben — vorher wäre es abgeschrieben statt geprüft
- **DoD:** Genehmigte Bestellung löst eine echte Pipeline aus · kein Token im Repo · Stub weiterhin testbar

## AP-21 · AD-/LDAP-Anbindung
> **Befund:** `grep ldap requirements.txt` → 0 Treffer. FM_BA07 unerfüllt; Rollen werden
> heute als Feld gepflegt statt aus AD-Gruppen gemappt.
- [ ] `django-auth-ldap` (Offline-Wheelhouse, cp312)
- [ ] Gruppen → Rollen-Mapping konfigurierbar; On-Login-Sync
- [ ] Fehlerfälle: AD nicht erreichbar → Login verweigern; Rolle fehlt → Minimalrechte; deaktivierter AD-User → lokal deaktiviert
- [ ] Lokaler Fallback-Login für Dev/Notfall bleibt erhalten
- **DoD:** Login gegen AD-Testumgebung · Rollen aus Gruppen · Fehlerfälle getestet · kein Passwort lokal gespeichert

---

> **AP-23** stammt aus dem Code-Abgleich beim Schreiben des Bookstack-Handbuchs
> (2026-07-22). Das dort ebenfalls entstandene AP-22 ist erledigt — siehe `todo-erledigt.md`.

## AP-23 · Rename-Reste und Doku-Drift bereinigen
> **Befund:** Beim Abgleich Handbuch ↔ Code fiel auf, dass die Umbenennung MPP → CMP
> an mehreren Rändern liegen geblieben ist und die Referenz-Doku dem Code hinterherhinkt.
- [ ] `package.json` zeigt auf `mpp/static/css/…` — `npm run css:build` schlägt real fehl, und `scripts/run.sh` unterdrückt den Fehler und meldet trotzdem Erfolg (beides fixen: Pfad **und** die verschluckte Fehlermeldung)
- [ ] `.env.example` trägt noch „MPP"
- [ ] `cmp-docs/docs/referenz/url-referenz.md`: zwei falsche Pfade (Subscription-Detail/Cancel) und acht fehlende URLs (u. a. das gesamte Admin-Panel, `/audit/export/`, die Wizard-Routen)
- [ ] `cmp-docs/docs/entwicklung/projektstruktur.md` kennt `cmp/config/settings/production.py` nicht — ausgerechnet die Datei mit der FATAL-Regel
- [ ] Docstring in `cmp/config/settings/production.py` nennt `ALLOWED_HOSTS` als Pflicht-Variable; real hat sie einen stillen `[]`-Default, nur `SECRET_KEY` und `DATABASE_URL` erzwingen den Abbruch
- [ ] `.wheels/` (git-getrackt) wird von keinem Skript referenziert — klären, ob Altartefakt, dann entfernen
- **DoD:** `npm run css:build` läuft durch und scheitert sichtbar, wenn es scheitert · url-referenz.md und projektstruktur.md stimmen mit dem Code überein (grep-belegt) · kein „MPP" mehr außerhalb der History
