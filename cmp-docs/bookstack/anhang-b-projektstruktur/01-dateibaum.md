# Anhang B — Projektstruktur

Diese Seite zeigt den echten Verzeichnisbaum des Repos, erzeugt per `find`/`tree` am
2026-07-22 — nicht aus vorhandener Doku abgeschrieben. Wo der Baum von
`cmp-docs/docs/entwicklung/projektstruktur.md` abweicht, gilt hier der echte Baum.

## 1. Ziel des Kapitels

Wer neu ins Projekt kommt, soll hier nachschlagen können, wo welcher Code liegt, ohne den
Baum erst selbst erlaufen zu müssen — und soll sich darauf verlassen können, dass jede
Zeile gegen das echte Dateisystem geprüft ist, nicht gegen die Erinnerung an eine ältere
Fassung der Doku.

## 2. Der Projektbaum

Erzeugt mit `tree -a -I 'venv|site|__pycache__|.git|node_modules|build|wheels|.wheels|
release|.tools|.pytest_cache|.ruff_cache|logs|.venv-docs|.cache'` und `find`, Stand
2026-07-22. Build- und Cache-Verzeichnisse sind unten in Abschnitt 4 gesondert erklärt,
statt hier ungekürzt aufgeblättert zu werden.

```
lucent-job-mpp-TDD-Django/                  # Projektwurzel
├── cmp/                                    # Django-Projekt (Anwendungscode)
│   ├── config/                             # Projektkonfiguration
│   │   ├── settings/
│   │   │   ├── base.py                     # gemeinsame Settings
│   │   │   ├── development.py              # DEBUG=True, Celery EAGER
│   │   │   ├── testing.py                  # Test-DB, schnelle Passwort-Hashes
│   │   │   └── production.py               # DEBUG muss hier False sein (FATAL-Regel)
│   │   ├── urls.py                         # Root-URL-Konfiguration
│   │   ├── celery.py                       # Celery-App
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/                               # 10 Feature-Apps (siehe Abschnitt 3)
│   │   ├── accounts/    ├── catalog/       ├── orders/    ├── approvals/
│   │   ├── provisioning/├── cmdb/          ├── notifications/
│   │   ├── audit/       ├── subscriptions/ └── dashboard/
│   ├── core/                               # geteilter Code, app-übergreifend
│   │   ├── domain/
│   │   │   ├── enums.py                    # UserRole
│   │   │   ├── value_objects.py            # OrderStatus, StatusMachine
│   │   │   └── validators.py               # TemplateValidator
│   │   ├── templatetags/cmp_tags.py        # eigene Template-Tags
│   │   ├── apps.py                         # AppConfig für core
│   │   ├── context_processors.py           # globaler Template-Context
│   │   ├── mixins.py                       # TimeStampedModel, RoleMixins
│   │   └── exceptions.py                   # Custom Exceptions
│   ├── templates/                          # Django-Templates (30 .html-Dateien)
│   │   ├── base.html                       # DaisyUI-Layout
│   │   ├── debug_layout.html               # Layout-Debug-Hilfsseite
│   │   ├── includes/                       # Navbar, Sidebar, Messages
│   │   ├── admin_panel/                    # eigenes Admin-Dashboard (Custom, nicht Django-Admin)
│   │   ├── account/, accounts/             # allauth-Overrides / Profil
│   │   ├── catalog/partials/               # Katalog + HTMX-Fragmente
│   │   ├── orders/wizard/                  # mehrstufiges Bestellformular
│   │   ├── approvals/, audit/, dashboard/, notifications/, subscriptions/
│   ├── static/
│   │   ├── css/input.css                   # Tailwind-Quelle
│   │   ├── css/output.css                  # generiert (gitignored)
│   │   └── js/htmx.min.js, chart.umd.min.js  # lokal gebundelt, kein CDN
│   ├── stubs/cmdb/*.yml                    # Entwicklungs-Stubs (locations/networks/tenants)
│   └── manage.py
│
├── tests/                                  # pytest-django-Tests (347; View-Tests fast durchweg client-Fixture)
│   ├── conftest.py, factories.py           # Shared Fixtures / factory_boy
│   ├── unit/                               # Services, Domain, Installer (lib.sh/ui.sh via Python-Tests)
│   ├── integration/                        # Views, Models
│   └── e2e/                                # Workflow-Tests
│
├── deploy/                                 # Offline-Installer für AlmaLinux/Rocky 9
│   ├── install.sh                          # Orchestrierung: Preflight + 8 Schritte
│   ├── lib.sh                              # System-Logik (PostgreSQL, DB, systemd, TLS)
│   └── ui.sh                               # Prüfbereich, Panel-Render
│
├── scripts/                                # lokale Dev-Werkzeuge (3 Skripte, Anhang C)
│   ├── run.sh                              # interaktiver Dev-Launcher (Menü)
│   ├── cmp.sh                              # zweiter, aufgabenorientierter Launcher
│   └── fix_databases.sh                    # DB-Rolle/DBs neu anlegen (braucht sudo)
│
├── tools/                                  # Release-Werkzeuge (Projektwurzel-Ebene)
│   ├── build_release.py                    # Offline-Bundle (App + Wheels + VERSION)
│   └── make_screenshots.py                 # Oberflächen-Galerie neu aufnehmen (Selenium)
│
├── cmp-docs/                                # Zensical-Dokumentation + dieses Bookstack-Buch
│   ├── docs/                                # Markdown-Quellen (betrieb/, entwicklung/, grundlagen/,
│   │   │                                     #  referenz/, decisions/, intern/, images/, ...)
│   ├── bookstack/                           # dieses Buch (Bookstack-Import-Format)
│   ├── mermaid-sources/                     # .mmd-Quellen der Diagramme
│   ├── tools/                               # Doku-Werkzeuge (Anhang C)
│   │   ├── build_docs.py    (im Root von cmp-docs, nicht unter tools/ — siehe Anhang C)
│   │   ├── extract_mermaid_blocks.py
│   │   ├── generate_project_activity.py
│   │   └── render_mermaid.sh
│   ├── build_docs.py, run_cmp_docs.sh, verify_docs.sh, deploy_ghpages.sh, zensical.toml
│   └── .venv-docs/, site/, .cache/          # generiert — siehe Abschnitt 4
│
├── analyse/                                 # Fremddoku + Analysen (Arbeitsdokumente, kein Anwendungscode)
│   ├── bestellportal_anon.md                # anonymisierter Bookstack-Export der Zielumgebung
│   ├── anforderungen.md, analyse-bestellportal.md, bookstack-struktur-vorschlag.html
│   └── *.png (Screenshots, .gitignore-d)
│
├── docs/                                    # Session-/Prozessdoku (Handoffs, Insights, Specs)
│   ├── deployment/                          # VM-Installationsanleitungen (online + offline)
│   ├── handoffs/, insights/                 # je 1 Datei pro Session
│   ├── specs/, superpowers/{plans,specs}/   # Design-Specs + Pläne
│   ├── session-kennzahlen.md                # KPI-Matrix je Session
│   └── CLAUDE.md.v1-archive
│
├── .claude/                                 # Claude-Code-Agenten + Regeln
│   ├── agents/                              # 11 Agent-Definitionen
│   ├── agent-memory/                        # persistenter Speicher je Agent
│   └── rules/                               # django.md, htmx.md, testing.md
│
├── requirements/{base,dev,production}.txt   # abgestufte Requirements (env-basiert)
├── build/, release/, wheels/, .wheels/      # Build-Artefakte — siehe Abschnitt 4
├── node_modules/, .tools/, logs/, .pytest_cache/, .ruff_cache/  # generiert/Caches
│
├── CLAUDE.md, README.md                     # Projektregeln / Einstieg
├── run.sh                                   # Release-/AppImage-/Docs-ZIP-Werkzeug (Anhang C)
├── pytest.ini, package.json, package-lock.json
├── lucent-hub.yml                           # Single-Source für Versionsnummer + Docs-Port
├── todo.md, todo-erledigt.md                # AP-Roadmap (offen / erledigt)
└── .env.example
```

## 3. App-interner Aufbau

Jede App unter `cmp/apps/` folgt im Kern demselben Muster — `apps.py`, `models.py`,
`services.py`, `views.py`, `forms.py`, `admin.py`, `urls.py`, `migrations/` — aber nicht
ausnahmslos. Am echten Dateibestand geprüft (`find cmp/apps/<app> -maxdepth 1 -type f`):

| App | Weicht vom Muster ab | Beleg |
|---|---|---|
| `provisioning/` | kein `urls.py` (keine eigenen HTTP-Routen); zusätzlich `tasks.py` (Celery), `clients.py` (GitLab) | nicht in `cmp/config/urls.py` includiert |
| `cmdb/` | kein `urls.py`, kein `views.py`, kein `forms.py` — reine Backend-/Stub-Schicht; zusätzlich `clients.py` | nicht in `cmp/config/urls.py` includiert |
| `dashboard/` | **kein** `models.py`, **kein** `forms.py`, **kein** `admin.py` — dafür `admin_views.py` statt `admin.py` | `find cmp/apps/dashboard -maxdepth 1 -type f` |
| `accounts/` | zusätzlich `management/commands/seed.py` **und** `seed_users.py` (zwei Seed-Kommandos, nicht nur eines) | `find cmp/apps/accounts/management/commands` |
| `notifications/`, `audit/`, `subscriptions/` | kein `forms.py` — diese Apps nehmen keine Formulareingaben entgegen, ihre Schreibpfade sind einfache POST-Aktionen | `find cmp/apps/<app> -maxdepth 1 -name forms.py` ohne Treffer |

Nur `accounts/`, `catalog/`, `orders/` und `approvals/` bringen alle sechs Kerndateien mit.
`approvals/forms.py` ist die jüngste davon: es kam mit v1.4.0 hinzu, als der
Ablehnungskommentar von `request.POST` auf ein Formular umgestellt wurde.

## 4. Generierte und nicht versionierte Verzeichnisse

Diese Verzeichnisse gehören nicht zum Quellbaum — sie werden von Werkzeugen erzeugt oder
sind reine Abhängigkeits-Caches. Sie sind oben kollabiert dargestellt, nicht ausgeblättert:

| Pfad | Inhalt | Getrackt? |
|---|---|---|
| `build/` | AppImage-Staging (`build/appimage/…`) + fertige Release-Bundles je Version | nein |
| `release/` | ausgelieferte AppImages/ZIPs (Kopie aus `build/`) | nein |
| `wheels/` | Offline-Wheelhouse für den Installer, aktuell 32 `.whl` (`wheels/README.md` beschreibt den Download-Befehl) | nein (`.gitignore:22`) |
| `.wheels/` | 35 `.whl`-Dateien, **von keinem Skript referenziert** (`grep -rn "\.wheels" **/*.sh **/*.py` — 0 Treffer außerhalb generierter Bundles) | **ja** — wirkt wie ein verwaistes Altartefakt |
| `node_modules/`, `.tools/` | npm-Abhängigkeiten (Tailwind) bzw. heruntergeladenes `appimagetool` | nein |
| `.pytest_cache/`, `.ruff_cache/`, `logs/` | Test-/Linter-Caches, Laufzeit-Logs | nein |
| `cmp-docs/.venv-docs/` | eigenes venv nur für die Doku-Toolchain (Zensical) | nein |
| `cmp-docs/site/`, `cmp-docs/.cache/` | gebaute Doku-Site bzw. Zensical-Cache | nein |

## 5. Abweichungen zu `projektstruktur.md`

Die bestehende Doku-Seite `cmp-docs/docs/entwicklung/projektstruktur.md` ist im Kern
richtig, aber an folgenden Stellen veraltet gegenüber dem echten Baum:

- `cmp/config/settings/` hat zusätzlich `production.py` — in der Doku nicht erwähnt, obwohl
  genau diese Datei für die FATAL-Regel „DEBUG=True in PRODUCTION" relevant ist.
- `cmp/core/` hat zusätzlich `apps.py`, `context_processors.py` und
  `templatetags/cmp_tags.py` — die Doku nennt nur `domain/`, `mixins.py`, `exceptions.py`.
- `cmp/templates/` hat zusätzlich `admin_panel/`, `orders/wizard/` und `debug_layout.html` —
  fehlen in der Doku-Liste.
- Das „App-interner Aufbau"-Muster in der Doku gilt nicht ausnahmslos: `dashboard/` hat
  weder `models.py` noch `forms.py` noch `admin.py` (dafür `admin_views.py`); `cmdb/` und
  `provisioning/` haben kein `urls.py`/`views.py`/`forms.py` (siehe Abschnitt 3).
- Root-Ebene: Es gibt **zwei** `run.sh` (Projektwurzel und `scripts/run.sh`) sowie ein
  drittes Launcher-Skript `scripts/cmp.sh` — die Doku nennt nur `scripts/run.sh`.
- `wheels/` liegt direkt unter der Projektwurzel (nicht unter `deploy/`, wie man vermuten
  könnte); zusätzlich existiert das nicht referenzierte `.wheels/` (siehe Abschnitt 4).

## 6. Zusammenfassung

Der reale Baum folgt der Schichtenteilung `views → services → models` sauber je App, aber
mit realen Ausnahmen bei `dashboard/`, `cmdb/` und `provisioning/`, die je nach Rolle
(Stub-Client, Celery-Worker, Stats-View) keine volle App-Schablone brauchen. Generierte
Verzeichnisse (`build/`, `wheels/`, venvs, Caches) sind bewusst nicht Teil des Quellbaums.
Ein Altartefakt (`.wheels/`) liegt getrackt im Repo, ohne von einem Werkzeug referenziert zu
werden — das ist keine Fehlfunktion, aber räumbar.

> Quelle: `tree`/`find` am echten Dateisystem (2026-07-22), `cmp-docs/docs/entwicklung/projektstruktur.md`, `wheels/README.md`, `.gitignore`, `cmp/config/urls.py` — am Code geprüft 2026-07-22
