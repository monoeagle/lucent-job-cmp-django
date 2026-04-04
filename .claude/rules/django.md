---
description: Django Konventionen fuer MPP-Django
globs: "*.py"
---
- Thin Views: Logik in Services, nicht in Views
- Forms fuer Validierung, nicht rohe request.POST
- Django Admin als primaeres Admin-Tool
- ACCOUNT_SIGNUP_ENABLED=False (Admin erstellt alle User)
- Celery fuer async Provisioning-Tasks
- Django Channels fuer WebSocket-Updates
- factory_boy + pytest-django fuer Tests
- Migrationen: squashen vor Release
- Settings via django-environ, nie hardcoded Secrets
- DEBUG=True in PRODUCTION ist FATAL — nie deployen
