# Detailvergleich: MPP Flask+React vs MPP Django+HTMX

**Datum:** 2026-03-30
**Zweck:** Gegenüberstellung beider Implementierungen des Marketplace Portals

---

## 1. Architektur-Übersicht

| | Flask (mpp-TDD) | Django (mpp-TDD-Django) |
|---|---|---|
| **Ansatz** | API-First (REST + SPA) | Server-Side Rendering |
| **Backend** | Flask 3.1 + SQLAlchemy 2.0 | Django 6.0 + Django ORM |
| **Frontend** | React 19 + TypeScript | Django Templates + HTMX |
| **CSS** | TailwindCSS (via Vite) | TailwindCSS + DaisyUI |
| **Auth** | JWT (eigener AuthService) | django-allauth (Session) |
| **Async** | — | Celery + Redis |
| **Echtzeit** | SSE | Django Channels (geplant) |
| **DB-Migrations** | Alembic | Django Migrations |
| **State** | Zustand + TanStack Query | Server-Session |

---

## 2. Kennzahlen

| Metrik | Flask | Django | Faktor |
|--------|-------|--------|--------|
| **Python-Dateien** | 74 | 97 | 1.3x Django |
| **Python LOC** | 6.197 | 3.744 | 1.7x Flask |
| **Frontend-Dateien** | 82 (TSX/TS) | 30 (HTML) | 2.7x Flask |
| **Frontend LOC** | 5.729 | 2.126 | 2.7x Flask |
| **Gesamt LOC** | ~11.927 | ~9.702 | 1.2x Flask |
| **Tests** | 764 | 230 | 3.3x Flask |
| **Test-Dateien** | 83 | 33 | 2.5x Flask |
| **Git Commits** | 219 | 79 | 2.8x Flask |
| **Projektgröße** | 950 MB | 4,1 MB | 230x Flask |
| **Dependencies** | 26 (8 Py + 18 JS) | 11 (7+4) | 2.4x Flask |

---

## 3. Domain-Parität

| Aspekt | Flask | Django | Identisch? |
|--------|-------|--------|-----------|
| **Models** | 15 | 15 | Ja |
| **Services** | 15 | 10 | ~70% |
| **Templates** | 2 (Linux/Windows VM) | 2 (Linux/Windows VM) | Ja |
| **Parameter pro VM** | 30+ | 30+ | Ja |
| **Rollen** | 4 | 4 | Ja |
| **Demo-User** | 5 | 5 | Ja |
| **Demo-Bestellungen** | 8 | 8 | Ja |

---

## 4. API / Routing

| | Flask | Django |
|---|---|---|
| **Endpoint-Dekoratoren** | 98 REST-Routen | — |
| **URL-Patterns** | — | 36 |
| **Grund** | React SPA braucht JSON-API | Templates rendern direkt |

Flask braucht 98 API-Endpoints weil das React-Frontend JSON konsumiert. Django braucht nur 36 URL-Patterns — die Views rendern HTML direkt. **62 Endpoints weniger.**

---

## 5. Vorteile Flask + React

### Stärken

1. **Entkopplung Frontend/Backend** — Teams können parallel entwickeln. API-Vertrag als Schnittstelle.

2. **Rich Client Interaktivität** — React-State-Management ermöglicht komplexe UI-Logik (Parameter-Dependencies, conditional rendering, Auto-Fill) vollständig clientseitig ohne Server-Roundtrips.

3. **Offline-fähig** — SPA kann gecacht werden, funktioniert bei schwacher Verbindung.

4. **Wiederverwendbare API** — REST-API kann von Mobile-Apps, CLI-Tools, oder Drittanbietern genutzt werden.

5. **Testabdeckung** — 764 Tests vs 230. Deutlich umfassender getestet.

6. **Type Safety** — TypeScript fängt Frontend-Fehler zur Compile-Zeit ab.

7. **Bessere UX für Wizard** — Multi-Step-Wizard mit sofortigem Feedback, keine Page-Reloads, Scroll-Positionen bleiben erhalten.

### Schwächen

1. **Doppelter Code** — Validierungslogik im Frontend UND Backend. Parameter-Schemas werden in TypeScript-Types UND Python-Models abgebildet.

2. **Build-Pipeline nötig** — Node.js, Vite, TypeScript-Compiler. Erhöht Setup-Komplexität.

3. **26 Dependencies** — Größere Angriffsfläche, mehr Update-Aufwand.

4. **950 MB Projektgröße** — node_modules + Build-Artefakte.

5. **Kein Async** — Kein Celery/Task-Queue. Provisioning läuft synchron oder via externe Trigger.

6. **JWT-Management** — Token-Refresh, Expiration, Logout-Invalidierung müssen selbst implementiert werden.

---

## 6. Vorteile Django + HTMX

### Stärken

1. **Kein Build-Step** — Kein Node.js, kein TypeScript, kein Vite. `python manage.py runserver` reicht.

2. **Single-Language Stack** — Python für alles. Kein JavaScript (außer inline für Charts + Sticky-Sidebar).

3. **Django Admin gratis** — Vollständiges Admin-Interface ohne eigenen Code. Template-Verwaltung, User-Management, Daten-Inspektion.

4. **Weniger Code** — 9.702 LOC vs 11.927. ~19% weniger Code für gleiche Features.

5. **11 statt 26 Dependencies** — Weniger Wartungsaufwand, kleinere Angriffsfläche.

6. **4 MB statt 950 MB** — 230x kleinere Projektgröße.

7. **Session-Auth** — Django's eingebaute Session-Authentifizierung ist robuster als DIY-JWT. CSRF-Schutz inklusive.

8. **Celery integriert** — Async-Provisioning von Anfang an. Background-Tasks für Pipeline-Trigger.

9. **django-allauth** — Social Login, MFA, Account-Management out-of-the-box erweiterbar.

10. **36 statt 98 Routen** — Kein API-Layer nötig. Weniger Boilerplate.

### Schwächen

1. **Weniger Tests** — 230 vs 764. Das Django-Projekt ist weniger umfassend getestet.

2. **Tailwind-Purge-Problem** — Dynamische CSS-Klassen werden nicht generiert. Erfordert Inline-Styles als Workaround.

3. **Begrenzte Client-Interaktivität** — Parameter-Dependencies (depends_on, affects_options_of) erfordern inline JavaScript. Kein React-artiges State-Management.

4. **Keine wiederverwendbare API** — Kein REST-Endpoint für Mobile-Apps oder externe Systeme. Falls später nötig, muss DRF nachgerüstet werden.

5. **HTMX-Limitierungen** — Komplexe UI-Logik (Wizard, Auto-Fill, conditional Fields) braucht vanilla JavaScript. HTMX allein reicht nicht.

6. **Server-Roundtrips** — Jede Wizard-Step-Navigation ist ein Form-Post + Redirect. Spürbare Latenz bei vielen Steps.

7. **Kein TypeScript** — Keine statische Typprüfung im Frontend. JavaScript-Fehler erst zur Laufzeit sichtbar.

---

## 7. Architektur-Vergleich

### Clean Architecture vs. Django Hybrid

| Aspekt | Flask (Clean Arch) | Django (Hybrid) |
|--------|-------------------|-----------------|
| **Schichten** | api/ → services/ → domain/ ← data/ | views → services → models |
| **Domain** | Eigene Entities + Value Objects | Django TextChoices + standalone VOs |
| **Repository** | Explizites Repository Pattern | Django ORM direkt in Services |
| **Dependency Rule** | Streng (Domain kennt kein Framework) | Pragmatisch (Domain nutzt TextChoices) |
| **Testbarkeit** | Höher (alles mockbar) | Gut (factory_boy + pytest-django) |

Flask folgt Clean Architecture strenger — Domain-Entities sind Framework-agnostisch. Django's Hybrid-Ansatz ist pragmatischer: Services kapseln die Logik, aber nutzen Django ORM direkt.

---

## 8. Developer Experience

| Aspekt | Flask | Django |
|--------|-------|--------|
| **Setup-Zeit** | ~10 Min (Python + Node + DB) | ~3 Min (Python + DB) |
| **Dev-Server starten** | 2 Prozesse (Flask + Vite) | 1 Prozess (Django) |
| **Hot Reload** | Vite HMR (sofort) | Django auto-reload (~1s) |
| **Debugging** | Browser DevTools + Python | Nur Python |
| **Lernkurve** | Hoch (Flask + React + TS + SQLAlchemy) | Mittel (Django) |

---

## 9. Empfehlung

### Flask + React wählen, wenn:
- Mehrere Frontend-Clients geplant (Web + Mobile + API)
- Team hat React/TypeScript-Expertise
- Komplexe Client-Side-Logik nötig (Echtzeit-Validierung, Drag&Drop)
- API-First-Strategie gewünscht

### Django + HTMX wählen, wenn:
- Schnelle Time-to-Market wichtig
- Team ist klein oder Python-fokussiert
- Admin-Interface als Ops-Tool benötigt
- Keine Mobile-App oder externe API-Konsumenten geplant
- Weniger Wartungsaufwand gewünscht

### Hybrid-Option:
Django mit HTMX als Basis, bei Bedarf DRF für spezifische API-Endpoints nachrüsten. Hält den initialen Aufwand niedrig und erlaubt spätere Erweiterung.

---

## 10. Fazit

Beide Ansätze liefern das gleiche Produkt mit identischem Domain-Modell (15 Models, 30+ Parameter, 8 Demo-Bestellungen). Der fundamentale Trade-off:

**Flask + React** = Mehr Flexibilität, mehr Code, mehr Komplexität, bessere Client-Interaktivität
**Django + HTMX** = Weniger Code, schnellerer Start, weniger Dependencies, aber eingeschränktere UI-Dynamik

Das Django-Projekt erreicht ~85% Feature-Parität mit ~80% des Codes und ~40% der Dependencies. Die verbleibenden 15% sind primär: weniger Tests, eingeschränkte Client-Side-Logik, kein REST-API-Layer.
