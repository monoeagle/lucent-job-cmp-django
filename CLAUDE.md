# CLAUDE.md — MPP Django

**Marketplace Portal (MPP-Django)** — Self-Service IT-Provisioning Portal, Django Rewrite.
Bewusstes Gegenstueck zu mpp-TDD: kein API-First, kein React, kein DRF.

- **Port:** 8000
- **Stack:** Django 6.0, PostgreSQL, Celery+Redis, HTMX+DaisyUI (Django Channels geplant, AP-12)
- **Auth:** django-allauth (Session-basiert), ACCOUNT_SIGNUP_ENABLED=False
- **Admin:** Django Admin als primaeres Admin-Tool (Admin erstellt alle User)
- **Theme:** Custom "Lucent" DaisyUI-Theme
- **Autor:** Tobias Philipp / LucentTools

## Architektur

Thin Views — Logik gehoert in Services, nicht in Views oder Models.

```
views.py → services.py → models.py
views.py → forms.py (Validierung)
core/ → apps/ (nicht umgekehrt)
```

## FATAL

DEBUG=True in PRODUCTION ist FATAL — nie deployen.

## Docs & Konventionen

- Detaillierte Architektur: `docs/CLAUDE.md.v1-archive`
- Django-Konventionen: `.claude/rules/django.md`
- Template/HTMX-Konventionen: `.claude/rules/htmx.md`
- Test-Richtlinien: `.claude/rules/testing.md`
