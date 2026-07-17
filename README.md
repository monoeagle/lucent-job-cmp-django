# CloudMan Portal (CMP)

**CloudMan Portal (CMP)** — Self-Service IT-Provisioning-Portal.
Django-Rewrite, bewusst ohne API-First/React/DRF.

- **Stack:** Django 6.0 · PostgreSQL · Redis · Celery · django-allauth · HTMX + DaisyUI
- **Auth:** Session-basiert (allauth), Self-Service-Signup deaktiviert — Admin legt User an
- **Architektur:** Thin Views → Services → Models

## Schnellstart (Entwicklung)

```bash
python3.12 -m venv venv
venv/bin/pip install -r requirements/dev.txt
# PostgreSQL/Redis lokal bereitstellen (siehe Settings: config/settings/development.py)
venv/bin/python cmp/manage.py migrate
venv/bin/python cmp/manage.py runserver   # http://127.0.0.1:8000
```

Tests:

```bash
venv/bin/python -m pytest        # config.settings.testing
```

## Deployment

- **VM (Produktion, Rocky/AlmaLinux 9):** Schritt-für-Schritt-Anleitung →
  [`docs/deployment/vm-installation.md`](docs/deployment/vm-installation.md)
- **VM offline / air-gapped (ohne Internet):** Bundle-Transport-Anleitung →
  [`docs/deployment/vm-installation-offline.md`](docs/deployment/vm-installation-offline.md)
- Produktions-Settings: `config.settings.production` (env-basiert, django-environ).
  Vorlage der Umgebungsvariablen: [`.env.example`](.env.example)
- Container-Setup (Docker/Compose): geplant als AP-11.

## Dokumentation

Ausführliche Projekt-Doku (Architektur, Datenmodell, Services, Konventionen) in
`cmp-docs/` (zensical/MkDocs).
