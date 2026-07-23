# Projektstruktur

## Verzeichnisbaum

```
lucent-app-mpp-TDD-Django/
├── cmp/                              # Django-Projekt
│   ├── config/                       # Projektkonfiguration
│   │   ├── settings/
│   │   │   ├── base.py              # Gemeinsame Settings
│   │   │   ├── development.py       # Dev: DEBUG=True, Celery EAGER
│   │   │   └── testing.py           # Test-DB, schnelle Hashes
│   │   ├── urls.py                  # Root-URL-Konfiguration
│   │   ├── celery.py                # Celery App
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── apps/                         # 10 Feature-Module
│   │   ├── accounts/                # Auth, User, Rollen
│   │   ├── catalog/                 # Service-Katalog
│   │   ├── orders/                  # Bestellungen + transitions.py (zentraler Statusübergang)
│   │   ├── approvals/              # Genehmigungen
│   │   ├── provisioning/           # Celery-Tasks, GitLab
│   │   ├── cmdb/                   # CMDB-Stub, Context
│   │   ├── notifications/          # Benachrichtigungen
│   │   ├── audit/                  # Audit-Logs
│   │   ├── subscriptions/          # Subscriptions
│   │   └── dashboard/             # Statistiken
│   │
│   ├── core/                        # Geteilter Code
│   │   ├── domain/
│   │   │   ├── enums.py            # UserRole
│   │   │   ├── value_objects.py    # OrderStatus, StatusMachine
│   │   │   └── validators.py       # TemplateValidator
│   │   ├── mixins.py               # TimeStampedModel, RoleMixins
│   │   └── exceptions.py           # Custom Exceptions
│   │
│   ├── templates/                   # Django Templates
│   │   ├── base.html               # DaisyUI Layout
│   │   ├── includes/               # Navbar, Sidebar, Messages
│   │   ├── account/                # allauth Overrides
│   │   ├── accounts/               # Profil
│   │   ├── catalog/                # Katalog + partials/
│   │   ├── orders/                 # Bestellungen
│   │   ├── approvals/              # Genehmigungen
│   │   ├── subscriptions/          # Subscriptions
│   │   ├── notifications/          # Benachrichtigungen
│   │   ├── audit/                  # Audit-Log
│   │   └── dashboard/             # Dashboard
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── input.css           # Tailwind Source
│   │   │   └── output.css          # Generiert (gitignored)
│   │   └── js/
│   │       └── htmx.min.js
│   │
│   ├── stubs/                       # Entwicklungs-Stubs
│   │   └── cmdb/
│   │       ├── locations.yml
│   │       ├── networks.yml
│   │       └── tenants.yml
│   │
│   └── manage.py
│
├── tests/                            # pytest-django Tests
│   ├── conftest.py                  # Shared Fixtures
│   ├── factories.py                 # factory_boy Factories
│   ├── unit/                        # Services, Domain, Installer (lib.sh/ui.sh)
│   ├── integration/                 # Views, Models
│   └── e2e/                         # Workflow-Tests
│
├── deploy/                           # Offline-Installer für AlmaLinux/Rocky 9
│   ├── install.sh                   # Orchestrierung: Preflight + 8 Schritte,
│   │                                #   Menü/--install/--check/--restart
│   ├── lib.sh                       # System-Logik: PostgreSQL-Erkennung
│   │                                #   (PGDG/AppStream), DB, systemd-Units,
│   │                                #   Zertifikat, Env — unit-getestet
│   └── ui.sh                        # Prüfbereich + Links/Ports + Panel-Render
│
├── tools/
│   └── build_release.py             # Offline-Bundle (App + Wheels + VERSION)
│
├── scripts/
│   └── run.sh                       # Dev-Launcher mit Menü
│
├── cmp-docs/                         # Zensical-Dokumentation
│   ├── docs/                        # Markdown-Quellen
│   │   └── intern/                  # NICHT im Docs-ZIP (Ausschluss in
│   │                                #   run.sh cmd_docs_zip: intern/ + intern-*.svg)
│   ├── zensical.toml                # Konfiguration
│   ├── build_docs.py
│   └── run_cmp_docs.sh
│
├── analyse/                          # Fremddoku + Analysen (Arbeitsdokumente)
│   ├── bestellportal_anon.md        # Bookstack-Export der Zielumgebung
│   │                                #   (anonymisiert: <org>, <autor>, …)
│   ├── anforderungen.md             # offene Fragen der Zielumgebung
│   ├── analyse-bestellportal.md     # Auswertung → Doku-Seite unter „Intern"
│   └── .gitignore                   # Screenshots (*.png) + gebaute HTML bleiben lokal
│
├── docs/superpowers/                 # Design-Specs + Pläne
│   ├── specs/
│   └── plans/
│
├── .claude/                          # Claude Code Agents
│   ├── agents/                      # 11 Agent-Definitionen
│   └── agent-memory/               # Persistenter Speicher
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── production.txt               # gunicorn, psycopg — env-basiert
│
├── pytest.ini
├── package.json
├── tailwind.config.js
├── CLAUDE.md
└── README.md
```

## App-interner Aufbau

Jede App unter `cmp/apps/` folgt demselben Pattern:

```
apps/{name}/
├── __init__.py
├── apps.py           # AppConfig
├── models.py         # Django Models
├── services.py       # Business-Logik
├── views.py          # Class-Based Views
├── forms.py          # Django Forms
├── admin.py          # Admin-Registrierung
├── urls.py           # URL-Patterns
└── migrations/       # Auto-generierte Migrationen
```

Sonderfälle:
- `provisioning/`: zusätzlich `tasks.py` (Celery) und `clients.py` (GitLab)
- `cmdb/`: zusätzlich `clients.py` (CMDB Stub)
- `accounts/`: zusätzlich `management/commands/seed.py`
