# Changelog

## Doku-Korrektur Channels + neues AP-12 — 2026-07-03

Doku-Drift behoben: Die Referenz behauptete, Benachrichtigungen würden „über
Django Channels (WebSocket) live ausgeliefert" — Channels ist aber nie gebaut
worden (kein `channels` in den Requirements, `config/asgi.py` Django-Default,
kein Consumer/Channel-Layer). Das Deployment (nginx + gunicorn/WSGI) passt zum
realen Stand; die Doku war falsch, nicht das Deployment.

- **Korrigiert**: `referenz/oberflaeche.md` (Benachrichtigungen aktualisieren
  per Seitenaufruf), Stack-Zeile in `CLAUDE.md`, Architektur-Diagramm
  (WebSocket-Knoten nun als „geplant AP-12" gestrichelt).
- **Neu: AP-12 · Live-Updates via Django Channels** in `todo.md` — Consumer +
  Channel-Layer (Redis), ASGI-Deployment (Uvicorn-Worker + nginx-WS-Upgrade),
  Wheelhouse-Erweiterung, TDD. In AP-Überblick und Gantt aufgenommen.

## v1.1.0 — Oberflächen-Galerie + gh-pages — 2026-06-27

Erste Doku-Veröffentlichung auf GitHub Pages plus neue Screen-Galerie und ein
Bugfix im Bestell-Flow.

- **Neue Referenz-Seite „Oberflächen"** (`referenz/oberflaeche.md`): Galerie mit
  13 Screenshots aller Hauptscreens über die Rollen Requester / Approver /
  Admin (Login, Dashboard, Katalog, Bestellformular, Bestelldetail,
  Benachrichtigungen, Subscriptions, Profil, Genehmigungen, Audit-Log,
  Django-Admin), klickbar via Lightbox. Screenshots automatisiert per Selenium
  aus der laufenden App aufgenommen.
- **gh-pages-Deployment**: Doku live unter
  `https://monoeagle.github.io/lucent-job-MPP_Django/`. Wiederverwendbares
  Deploy-Skript `mpp-docs/deploy_ghpages.sh` (worktree-basiert, `main` bleibt
  unberührt) + `.nojekyll`. Repo dafür auf public gestellt.
- **Bugfix Bestell-Flow**: `OrderFormView` filterte den Pflicht-Parameter
  `location` als vermeintlichen Kontext-Key heraus → „Parameter validation
  failed" bei jeder Linux-VM-Bestellung. Fix: Kontext-Keys, die zugleich echte
  Template-Parameter sind, bleiben erhalten. TDD (RED→GREEN), Suite **238 → 239**.
- **Doku-Fix**: relative Bildpfade auf Tiefe-2-Seiten korrigiert
  (`../images` → `../../images`) — betraf auch die zuvor kaputten
  Roadmap-Diagramme auf der Arbeitspakete-Seite.
- **Offline-Release für AlmaLinux 9**: gebündelte Wheels (32 cp312/manylinux),
  `tools/build_release.py` + `deploy/install.sh` (idiotensicher), `./run.sh release`.
  Als **GitHub-Release v1.1.0** veröffentlicht; Offline-Doku um den
  GitHub-Release-Weg (ziehen → transferieren → `install.sh`) erweitert.
- **ADR-0001 (Deployment: Native vs. Container)**: native systemd-Installation
  bleibt Default für air-gapped Single-VM; AP-11 von „Docker" auf
  **Podman/Quadlets** umgeschrieben. Entscheidung: **Python bleibt 3.12**
  (AlmaLinux 9 paketiert kein 3.14).
- **Startseite & Architektur** an luDBxP angeglichen (Hero = gruppierte APs,
  Header-Badge „Architektur", `graph TB` Banded-Layer); **Heatmap-Detailliste**
  per Klick togglebar.

## Produktions-Settings + VM-Deployment — 2026-06-19

Deployment-Fähigkeit ergänzt; AP-11 (Docker) bewusst zurückgestellt.

- **`config.settings.production`** (neu): env-basiert via `django-environ` —
  `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, Celery-URLs aus der Umgebung.
  Security-Hardening (HSTS, `SECURE_SSL_REDIRECT`, secure Cookies,
  `SECURE_PROXY_SSL_HEADER`, `STATIC_ROOT`). `manage.py check --deploy`: 0 Issues.
- **`.env.example`** als Vorlage; `requirements/production.txt` (gunicorn);
  `django-environ` in base/pinned requirements.
- **TDD**: 8 neue Tests (`tests/unit/test_production_settings.py`), RED→GREEN.
  Volle Suite **230 → 238 grün** (Unit 137 · Integration 97 · E2E 4).
- **Deployment-Doku** (`docs/deployment/`): `vm-installation.md` (Rocky/AlmaLinux 9,
  Voll-Produktion: gunicorn + nginx + systemd + PostgreSQL 16 + Redis + TLS via
  Let's Encrypt + SELinux/firewalld) und `vm-installation-offline.md` (air-gapped:
  Bundle-Transport, lokales RPM-Repo, `pip --no-index`, internes/self-signed TLS).
- **Repo-Hygiene**: App-AppImage (85 MB) + Docs-AppImage untracked, `*.AppImage`
  + `.tools/` in `.gitignore`; Merge mit Remote-`.claude/`-Untracking.

## Doku-TDD-Gate (docs-release-sync.pattern §G) — 2026-06-18

Doku-Erstellung ist jetzt **TDD**: `verify_docs.sh` prüft 11 Regeln (R-BUILD … R-AP-SYNC),
Exit 0 nur bei null ✗. „Fertig" = Gate grün. Dafür ergänzt/gefixt:

- **R-HOME**: Startseite auf reines Home-Layout reduziert; Beschreibung/Tech-Stack →
  `grundlagen/ueberblick.md`.
- **R-DIAGRAMME + R-AP-SYNC**: AP-Roadmap aus B0–B9 rekonstruiert — `todo.md`/`todo-erledigt.md`
  (Repo-Root) + `entwicklung/arbeitspakete.md` mit AP-Überblick-Flowchart + Roadmap-Gantt
  (Spannen schematisch, Historie zu v1.0.0 gestaucht); `addRoadmapBadge()` reaktiviert.
- **R-NO-CDN**: `theme.font = false` → kein Google-Fonts-CDN mehr (System-Fonts, offline).
- **R-NO-PLACEHOLDER**: letzte `ADAPT:`/`__ROADMAP_GANTT__`-Reste aus `icon-rail.js` entfernt.
- `todos.md` → `todo.md` + `todo-erledigt.md` konsolidiert (Pattern-Namensschema).
- **§H / R-APPRUN**: Docs-AppImage-`AppRun` neu — Standalone nutzt **zufälligen Ephemeral-Port**
  (`bind(…,0)`, nie Port-Kollision) statt fix 5063, öffnet eine **isolierte Chromium-App-Instanz**
  (Temp-Profil) statt `xdg-open`/Default-Firefox; Flags `--port=` (Hub), `--no-browser`,
  `--port-prefer=`. Funktional verifiziert (Port 35515, HTTP 200). 12. Gate-Regel ergänzt.

## Doku-Angleichung an lucent-docs.pattern — 2026-06-18

Die Doku war eine Pre-„App-Look"-Minimal-Zensical-Variante. Auf den Standard ab 2026-06 gehoben:

- **JS-Suite** (lokal gebündelt, kein CDN): `icon-rail.js` (linke Icon-Leiste statt Material-Tabs),
  `activity-heatmap.js` (Git-Aktivität + Insights), `mermaid.min.js`, `mermaid-init.js`,
  `palette-init.js`, `lightbox.js`, `hub-stop.js` (Hub-„Doku beenden"-Button).
- **Voll-`extra.css`** (~1980 Z., rail/home/heatmap-Styles), Akzentfarbe Lucent-Grün `#34D399`.
- **Mermaid-Pipeline**: `tools/extract_mermaid_blocks.py` + `render_mermaid.sh`, Pipeline-`build_docs.py`;
  Startseite als Home-Layout mit Hero-Architekturdiagramm (`mermaid-sources/index-1.mmd` → SVG via mmdc).
- **Aktivitäts-Heatmap/Insights** aus `git log` (`tools/generate_project_activity.py` →
  `docs/_data/project-activity.json`, `testCount` = 230 echte Tests).
- `zensical.toml`: `extra_javascript`-Block ergänzt, `navigation.tabs`/`.tabs.sticky` entfernt.
- `.gitignore`: `mpp-docs/{.venv-docs,site,.cache}` ergänzt; generiertes `site/` aus dem Tracking genommen.

## Wartung — 2026-06-18 (Doku-Sync)

- Test-Umgebung offline aus `.wheels/` ins projekt-eigene `venv` wiederhergestellt (Django 6.0.3, pytest 8.4.2).
- Volle Suite verifiziert: **230 Tests grün** (Unit 129 · Integration 97 · E2E 4), 0 Collection-Errors.
- Doku-Zahlen an den Ist-Stand angeglichen: Tests 228 → 230, Services 9 → 10 (`DashboardService`).
- `todos.md` auf realen Stand gespiegelt (Backend B0–B9 + HTMX-Frontend erledigt; Docker offen).

## v1.0.0 — 2026-03-29

Initiale Implementierung mit TDD (Test-Driven Development) in 10 Phasen.

### Phase B0: Projekt-Setup
- Django 6.0.3 Projekt-Skeleton mit Split Settings (base/dev/testing)
- PostgreSQL-Anbindung (mpp_dev, mpp_test)
- pytest-django Konfiguration
- TailwindCSS 4 + DaisyUI 5 + HTMX 2.0.4
- Core Domain (UserRole Enum), Mixins, Custom Exceptions

### Phase B1: Identity & Access
- Custom User Model mit Rollen-Feld (4 Rollen)
- django-allauth Integration (Session-basiert)
- Rollen-basierte Access Mixins (Requester/Approver/Admin/Superadmin)
- AccountService mit Seed-Funktion (5 Demo-User)
- Login/Logout Templates (DaisyUI)
- Profil-View und Dashboard

### Phase B2: Service Catalog
- ServiceTemplate Model mit JSONField Parameters
- TemplateValidator (Domain-Logik, 5 Typen)
- CatalogService (list, search, validate, seed)
- Katalog-Views mit HTMX Suche/Filter
- DaisyUI Card-Grid und Detail-Ansicht

### Phase B3: Order Lifecycle
- OrderStatus Enum (9 Zustände) + StatusMachine
- Order, OrderItem, OrderItemGroup Models
- OrderService (create, add/remove items, submit)
- Bestellwizard mit dynamischem Formular aus Template-Schema
- Order-List, Detail, Submit Views

### Phase B4: Context & CMDB
- CMDB Stub Client (YAML-basiert: 3 Locations, 7 Networks, 2 Tenants)
- AvailabilityRule, ContextRestriction, UserTenantAssignment Models
- ContextService (Verfügbarkeit, Einschränkungen, Tenant-Zuordnung)

### Phase B5: Provisioning Engine
- Celery Konfiguration (Redis Broker, EAGER in Dev/Test)
- GitLab Stub Client (Pipeline-Simulation)
- DispatchLog Model
- ProvisioningService (dispatch, complete mit Order-Status-Rollup)
- Celery Tasks (dispatch_provisioning, complete_provisioning)

### Phase B6: Approval Workflow
- ApprovalRule und ApprovalRequest Models
- ApprovalService (needs_approval, create, approve, reject)
- Approval-Queue View (ApproverRequired)
- Inline Approve/Reject Buttons

### Phase B7: Cross-Cutting Concerns
- AuditLog Model + AuditService (inkl. DSGVO-Anonymisierung)
- Notification Model + NotificationService (create, read, mark)
- Notification-Views (list, mark-read, mark-all-read)
- Audit-Log View (AdminRequired, paginiert)
- Dashboard mit echten Statistiken

### Phase B8: Subscriptions
- Subscription + GroupSubscription Models
- SubscriptionService (create_from_order, list, cancel)
- Subscription-Views (list, detail, cancel)

### Phase B9: Integration & Polish
- Unified Seed Command (User + Templates + Rules + Tenants)
- E2E Tests (4 komplette Workflows)
- Dev-Launcher (scripts/run.sh) mit Statusanzeige

### Kennzahlen

| Metrik | Wert |
|--------|------|
| Django Apps | 10 |
| Models | 15 |
| Services | 10 |
| Tests | 230 |
| Commits | 47 |
| TDD-Phasen | B0–B9 |
