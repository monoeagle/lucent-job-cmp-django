---
description: Test-Richtlinien fuer CMP-Django
globs: "test_*.py"
---
- TDD ist PFLICHT
- pytest-django + factory_boy
- RequestFactory fuer View-Tests (nicht Client)
- Celery-Tasks: CELERY_ALWAYS_EAGER=True in Tests
- Externe Abhaengigkeiten mocken
- Kleine, fokussierte Tests
