# Changelog

## v1.3.3 — Analyse der Bestellportal-Fremddoku — 2026-07-21

Reines Doku-Release. **PATCH**: keine Code-Änderung am Portal, kein neues
Anwendungs-Artefakt — das Offline-ZIP von v1.3.1 bleibt gültig.

### Neue interne Seite: Analyse der Bestellportal-Fremddoku

Ein Bookstack-Buch der Zielumgebung beschreibt ein Bestellportal als
**API-First-System mit DRF**. CMP ist der bewusste Gegenentwurf (rein SSR).
Die neue Seite wertet die Fremddoku vollständig gegen den echten CMP-Code aus:

- **Gap-Analyse** aller MUSS-/KANN-Anforderungen und des Domänenmodells,
  jede Zeile mit Beleg (Datei:Zeile) statt aus dem Gedächtnis behauptet.
- **Übersetzungstabelle** API-First → SSR, damit fremde Konzepte nicht
  fälschlich als „passt nicht" abgetan werden.
- **Antworten** auf die offenen Fragen der Zielumgebung: Installer-Idempotenz,
  granulares Logging, Dev/Test-Schalter, HTMX-Fallstricke, `.env` vs. `uv`,
  Absicherung, HA, Wartungsfenster (inkl. Mermaid-Prozesskette).
- **Prototyp-Bewertung** — was übernehmbar ist und was Anti-Pattern.

**Wichtigster Befund (CMP-intern):** Die Kette hinter der Genehmigung ist nicht
verdrahtet. `AuditService.log` und `NotificationService.create` werden
ausschließlich von `seed.py` aufgerufen, `SubscriptionService.create_from_order`
und die Celery-Tasks nur von Tests. Audit-Log und Benachrichtigungen enthalten
daher im laufenden Betrieb ausschließlich Seed-Daten. Aufgenommen als
Arbeitspaket mit Vorrang.

Zusätzlich gefunden und dokumentiert: `AuditLogListView` beantwortet
HTMX-Anfragen mit der kompletten Seite statt mit einem Fragment (fehlender
`get_template_names`-Zweig).

### Auslieferung

Die Seite liegt unter **Intern** und wird beim `docs-zip`-Bau **ausgeschlossen**
(`run.sh cmd_docs_zip`, Ausschluss oberster Ordner `intern/`). Sie ist Teil der
gh-pages-Doku, nicht des Kunden-Artefakts.

## v1.3.2 — Laufzeit-Topologie dokumentiert — 2026-07-20

Reines Doku-Release. **PATCH**: keine Code-Änderung, kein neues Anwendungs-Artefakt
— das Offline-ZIP von v1.3.1 bleibt gültig.

### Neue Seite: Betrieb → Laufzeit-Topologie

Das bestehende Architektur-Diagramm zeigt die **logischen Schichten** („was ruft
was") und enthält deshalb weder nginx noch gunicorn. Wie die Prozesse im Betrieb
zusammenhängen, stand nirgends. Die neue Seite schließt diese Lücke:

- **Drei Diagramme** — Produktion (nginx → gunicorn → PostgreSQL/Redis → Celery),
  Einstiegspunkte nach Rolle, Entwicklung (`runserver` + EAGER).
- **Wer macht was** — je Dienst die Aufgabe *und* deren Begründung: nginx puffert
  gegen langsame Clients (3 sync-Worker), gunicorn übersetzt HTTP ↔ WSGI, Redis
  ist Broker *und* Result-Backend, Celery entkoppelt lange Provisioning-Tasks.
- **Ports-Tabelle** — nur nginx ist exponiert, alles dahinter lauscht auf Loopback.
- **TLS** — der Installer erzeugt **kein** self-signed Zertifikat. Ohne passendes
  Zertifikat existiert gar kein 443-Listener, es gibt also auch keine wegklickbare
  Browser-Warnung, sondern *Connection refused*.
- **Zugriff vom Client** — FQDN statt IP (`ALLOWED_HOSTS`), hosts-Eintrag für
  Umgebungen ohne DNS, IP-Nachrüstung inkl. `CSRF_TRUSTED_ORIGINS`-Fallstrick.

### Build: `.nojekyll` überlebt den Build

`step_zensical_build()` löscht `site/` komplett und riss dabei jedes Mal die
getrackte `site/.nojekyll` mit — sie musste von Hand zurückgeholt werden
(Commit `cb4095e`). Ohne die Datei ignoriert GitHub Pages Unterstrich-Verzeichnisse,
`_data/project-activity.json` wäre auf gh-pages tot. Der Build legt sie jetzt selbst
wieder an.

## v1.3.1 — Panel-Breite + frische Oberflächen-Galerie — 2026-07-18

Zwei Nachbesserungen nach dem CMP-Rename. **PATCH**: Bugfix + Doku, keine neuen
Fähigkeiten.

### Installer-Panel: Breite wächst mit dem Inhalt

Das feste `CMP_UI_WIDTH=46` schnitt lange Portal-/Admin-URLs und Pfade mit „.."
ab (auf der VM aufgefallen). Jetzt ist 46 nur das Minimum: das Panel ermittelt die
nötige Breite aus dem längsten Inhalt (inkl. dynamischer name-Spalten) und rendert
die Box entsprechend — nichts wird mehr gekürzt, die Box bleibt bündig (UTF-8 +
ASCII-Fallback). **+2 Tests** (328 → 330).

### Oberflächen-Galerie neu aufgenommen

Der Rename hatte die Galerie-Bilder verwaist (Referenzen auf `_cmp.png`, Dateien
noch `_mpp.png`). Statt nur umzubenennen: 14 frische Screenshots gegen das
laufende Portal — „CloudMan Portal"-Branding, aktuelle UI (u. a. der Bestell-
Wizard; 05/05b in der Formular-Ansicht mit befüllter Zusammenfassung).
Reproduzierbar über das neue `tools/make_screenshots.py` (Selenium, full-page).

## v1.3.0 — CloudMan Portal (Rename) + Installer-HTTP-Modus — 2026-07-17

Zwei Themen: Das Projekt heißt jetzt **CloudMan Portal (CMP)** — durchgängig von
Code über Deploy-Schicht bis Doku. Und die erste echte VM-Rückmeldung deckte drei
Installer-Lücken auf (Portal über HTTP nicht erreichbar, Redis nicht air-gapped,
Doku nur als Linux-AppImage), die hier behoben sind. MINOR: neue Installer-
Fähigkeiten, Portal-Code unverändert. Suite **317 → 328**.

### Rename MPP → CloudMan Portal (CMP)

Container `mpp/`→`cmp/`, 31 Bash-Funktionen `cmp_*`, System-Identifier
(`/opt/cmp`, `cmp.env`, User `cmp`, DB `cmp_prod`, Services `cmp-web`/`cmp-celery`),
Test-/Dev-DB, templatetags, Celery-App, Branding und Doku-Site (`cmp-docs/`). Der
Django-Applikationscode (`apps.*`, `config.*`) war importfrei von `mpp` — kein
Import geändert. History, Repo-URLs und das Schwesterprojekt `mpp-TDD` bleiben
unangetastet.

### Installer: HTTP/HTTPS automatisch

Fehlt ein zum FQDN passendes Zertifikat, läuft das Portal jetzt über **HTTP**
statt an erzwungenem TLS zu scheitern — inklusive der nötigen Django-Settings
(`SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` aus, CSRF-
Origin auf `http://`), sonst wäre der Login über reines HTTP unmöglich. Liegt ein
Zertifikat vor, HTTPS wie bisher. Kein automatisches self-signed mehr; der
Prüfbereich zeigt das tatsächliche Protokoll/Port.

### Redis air-gapped aus dem Bundle

Fehlt Redis, zieht `install.sh` es offline aus `rpms/redis*.rpm`
(`dnf --disablerepo='*'`) statt abzubrechen; `--with-packages` installiert es
weiterhin online mit.

### Doku als HTML-ZIP (Windows-tauglich)

`./run.sh docs-zip` packt die Doku-Site als statisches HTML-ZIP — entpacken,
`index.html` im Browser öffnen, kein Server, keine Installation. Das Docs-AppImage
bleibt optionale Linux-Variante; das Doku-Gate prüft jetzt das ZIP (R-DOCS-ZIP).

> **Weiterhin nicht auf echter Hardware verifiziert:** Die Installer-Logik ist per
> Fakes getestet (328 Tests), aber HTTP-Modus, Redis-RPM-Installation und die
> PostgreSQL-Erkennung sind noch nicht auf einer echten AlmaLinux-9-VM gelaufen.

## v1.2.0 — Offline-Installer produktionsreif — 2026-07-16

Der Installer war nicht wiederholbar und traf harte PGDG-Annahmen. Jetzt ist er
idempotent, erkennt PostgreSQL in beiden Varianten und startet am Terminal mit
einem Prüfbereich. Die Entscheidungslogik liegt in `deploy/lib.sh`, Status/Panel
in `deploy/ui.sh` — **78 Unit-Tests** (Suite **239 → 317**). Der Portal-Code
selbst ist unverändert; MINOR wegen der neuen Installer-Fähigkeiten.

**Bundle-Inhalt geändert** (deshalb neues Release statt v1.1.0-Ersatz):
`install.sh` neu geschrieben, `lib.sh` + `ui.sh` neu, `VERSION` mitgeliefert.

> **Nicht verifiziert:** Die System-Schritte (postgres/nginx/systemd/SELinux)
> sind weiterhin nie auf einer echten AlmaLinux-9-VM gelaufen. Die Tests
> beweisen, dass die Logik die richtigen Kommandos in der richtigen Reihenfolge
> wählt — nicht, dass echtes `dnf`, systemd, PGDG und SELinux mitspielen.
> `sudo ./deploy/install.sh --check` sagt auf der VM in einem Aufruf, was fehlt.

### Installer: Menü mit Prüfbereich, Links & Ports

`install.sh` startet am Terminal jetzt mit einem Prüfbereich (Ist-Zustand) plus
Links-/Ports-Übersicht und einem Aktionsmenü, statt sofort loszulaufen.
**+35 Tests** (282 → 317).

- **Neu**: `deploy/ui.sh` — Status-Erhebung und Panel-Rendering, strikt
  getrennt: die Render-Funktion bekommt ihre Daten über stdin und weiss nicht,
  woher sie stammen. Dadurch ist das Panel gegen erfundene Zustände testbar,
  ohne dass etwas installiert sein muss.
- **Neu**: Aktionen `--install`, `--check`, `--restart`. `--check` ändert nichts
  und liefert **Exit 0 nur, wenn alles grün ist** — damit als Health-Check für
  Monitoring/Cron nutzbar.
- **Neu**: Links & Ports (Portal, Admin, gunicorn :8001, PostgreSQL :5432,
  Redis :6379). Der FQDN kommt aus `ALLOWED_HOSTS`; ohne Installation wird
  **keine URL erfunden**, dort steht „noch nicht installiert".
- **Neu**: `VERSION`-Datei im Release-Bundle (`tools/build_release.py`), von
  `install.sh` mitinstalliert. Vorher stand die Version nur in
  `lucent-hub.yml` (nicht im Bundle) und als Fließtext in `START-HIER.txt` —
  auf der VM war sie nicht maschinenlesbar.
- **Ohne Terminal** (Pipe, CI, `ssh host './install.sh'`) erscheint kein Menü,
  es wird direkt installiert — bestehende Automatisierung bleibt gültig.
- **Behoben (durch die Tests gefunden)**: `_cmp_ui_pad` hätte den Installer
  unter `set -e` abgebrochen — `[ $pad -gt 0 ] && printf …` als letzter Befehl
  liefert bei exakt passender Breite eine 1 zurück.
- **Behoben (durch die Tests gefunden)**: `printf %-20s` polstert nach Bytes,
  nicht nach Zeichen — mit `✓`/`═` wäre die Box schief. Ohne UTF-8-Locale
  (`LANG=C`, auf VMs üblich) gibt es jetzt einen ASCII-Fallback, sonst stünde
  dort Buchstabensalat. `NO_COLOR` wird respektiert.

### Installer: PostgreSQL-Erkennung (PGDG + AppStream) + `--with-packages`

Der Installer verdrahtete PGDG-Annahmen hart und lief damit auf einer
AppStream-VM ins Leere. Beide Ursprünge werden jetzt **erkannt**, nicht geraten.
Neu ist ausserdem ein optionaler Online-Modus. **+20 Tests** (262 → 282).

- **Behoben**: `install.sh` rief `psql` über den **PATH** auf — PGDG legt seine
  Binaries aber nach `/usr/pgsql-16/bin/`. Der Preflight warnte nur folgenlos,
  die DB-Anlage wäre danach hart gescheitert. Der Pfad wird jetzt aus der
  erkannten Variante abgeleitet.
- **Behoben**: `postgresql-16.service` war in den systemd-Units fest verdrahtet
  (PGDG-Name); auf einer AppStream-VM (`postgresql.service`) griff das `After=`
  stillschweigend ins Leere.
- **Behoben**: Doku-Drift — die Doku forderte `Requires=postgresql-16.service`,
  `install.sh` schrieb nur `After=`. `cmp-web` startete also auch ohne
  laufende Datenbank. Die Units werden jetzt aus `lib.sh` gerendert (getestet).
- **Behoben**: Fehlendes PostgreSQL führte zu einer folgenlosen Warnung statt
  zum Abbruch.
- **Neu**: `--with-packages` (Online-Modus, **kein Default**) richtet PGDG-Repo
  + EPEL ein, deaktiviert das kollidierende AppStream-Modul, installiert die
  System-Pakete und initialisiert den Cluster — letzteres nur, wenn noch keiner
  existiert (`PG_VERSION`-Prüfung), damit ein Re-Run keine Daten anfasst.
- **Unverändert**: Der Offline-Pfad ohne Flag bleibt der Standard; das Bundle
  enthält weiterhin keine RPMs.

### Offline-Installer idempotent + Bundle-Pfad-Fix

`deploy/install.sh` ist jetzt wiederholt ausführbar: Ein zweiter Lauf
aktualisiert eine bestehende Installation, statt sie zu beschädigen oder
stillschweigend nichts zu tun. Die Entscheidungslogik wurde nach
`deploy/lib.sh` ausgelagert und ist unit-getestet (**+23 Tests**, 239 → 262).

- **Behoben**: `BUNDLE_DIR` zeigte auf `deploy/` statt auf die Bundle-Wurzel —
  der Installer brach sofort mit „cmp/ fehlt im Bundle" ab. Der Offline-Weg
  war damit gar nicht lauffähig.
- **Behoben**: `systemctl enable --now` startet eine laufende Unit nicht neu —
  nach einem Upgrade lief der **alte Code** weiter, während das Skript Erfolg
  meldete. Jetzt expliziter `restart`.
- **Behoben**: Die DB-Anlage hing an der Existenz der **Rolle**. Brach Lauf 1
  nach `CREATE ROLE` ab, legte kein Folgelauf die Datenbank je an.
  Rolle und Datenbank werden nun getrennt geprüft.
- **Behoben**: Jeder Lauf erzeugte einen neuen `SECRET_KEY` und warf alle
  angemeldeten Nutzer raus. Ein bestehender Key wird jetzt übernommen.
- **Behoben**: `cp -a` merged nur — im neuen Release gelöschte Module und alte
  Migrationen blieben auf der VM liegen. Der App-Ordner wird jetzt gespiegelt.
- **Behoben**: Die Env-Übergabe an `manage.py` war ungequotet; ein DB-Passwort
  mit Leerzeichen zerfiel in mehrere Argumente (traf auch den Erstlauf).
- **Neu**: Das TLS-Zertifikat wird gegen den FQDN geprüft statt nur auf
  Datei-Existenz; ein CA-signiertes Zertifikat wird dabei nie überschrieben.
- **Neu**: `createsuperuser` wird übersprungen, wenn schon ein Superuser da ist.
- **Unverändert**: Die System-Schritte (postgres/nginx/systemd/SELinux) sind
  weiterhin **nicht** auf einer echten AlmaLinux-9-VM verifiziert.

## Neue Referenz-Seite „Architektur-Vergleich" (SSR vs. API-First) — 2026-07-15

Neue Referenz-Seite `referenz/architektur-vergleich.md`, die CMP Django (SSR,
dieses Projekt) gegen das Schwesterprojekt `lucent-job-CMP` (API-First,
Flask + React) stellt — das kontrollierte A/B-Experiment desselben Portals.

- **Neu**: `referenz/architektur-vergleich.md` in der Referenz-Navigation.
  Vergleich über Grundparadigma, SSR-/API-First-Belege, Schichtenarchitektur,
  Auth/State/Tooling und Kern-Trade-offs.
- **Alle Kennzahlen frisch am echten Code beider Repos erhoben** (`grep`/`find`),
  nicht aus der Vorlage fortgeschrieben. Dabei korrigiert gegenüber der
  Schwester-Doku: Django **30** Templates (nicht 439), **13** `render()`/
  TemplateView (nicht 24), **2** HTMX-Templates (nicht ~7); CMP **20**
  Blueprints (nicht 18), **≈878** Tests (771 Backend / 107 Frontend).
- Channels weiterhin korrekt als **geplant (AP-12)** ausgewiesen, nicht live.

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
  `https://monoeagle.github.io/lucent-job-cmp-django/`. Wiederverwendbares
  Deploy-Skript `cmp-docs/deploy_ghpages.sh` (worktree-basiert, `main` bleibt
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
- `.gitignore`: `cmp-docs/{.venv-docs,site,.cache}` ergänzt; generiertes `site/` aus dem Tracking genommen.

## Wartung — 2026-06-18 (Doku-Sync)

- Test-Umgebung offline aus `.wheels/` ins projekt-eigene `venv` wiederhergestellt (Django 6.0.3, pytest 8.4.2).
- Volle Suite verifiziert: **230 Tests grün** (Unit 129 · Integration 97 · E2E 4), 0 Collection-Errors.
- Doku-Zahlen an den Ist-Stand angeglichen: Tests 228 → 230, Services 9 → 10 (`DashboardService`).
- `todos.md` auf realen Stand gespiegelt (Backend B0–B9 + HTMX-Frontend erledigt; Docker offen).

## v1.0.0 — 2026-03-29

Initiale Implementierung mit TDD (Test-Driven Development) in 10 Phasen.

### Phase B0: Projekt-Setup
- Django 6.0.3 Projekt-Skeleton mit Split Settings (base/dev/testing)
- PostgreSQL-Anbindung (cmp_dev, cmp_test)
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
