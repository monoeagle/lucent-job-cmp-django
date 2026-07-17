---
description: HTMX/DaisyUI Template-Konventionen fuer CMP-Django
globs: "*.html"
---
- HTMX fuer partielle Updates statt Full-Page-Reload
- DaisyUI-Komponenten mit custom "Lucent" Theme
- Templates in apps/<app>/templates/<app>/
- Keine Inline-Styles — Tailwind-Klassen verwenden
- hx-target, hx-swap explizit setzen (kein implizites Verhalten)
