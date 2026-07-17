# Architektur-Vergleich: SSR vs. API-First

## Überblick

CMP existiert als zwei bewusst gegensätzliche Schwesterprojekte, die dasselbe
Self-Service-IT-Provisioning-Portal umsetzen. **CMP Django** (dieses Projekt,
`lucent-job-mpp-TDD-Django`) rendert HTML auf dem Server (**SSR**) — bewusst
*ohne* DRF, *ohne* React, *ohne* API-First. **lucent-job-CMP** liefert ein
Headless-JSON-Backend an eine React-SPA (**API-First**).

Alle Kennzahlen unten sind per `grep`/`find` am echten Code **beider** Repos
erhoben (Stand 2026-07-15), nicht aus Doku fortgeschrieben.

## Grundparadigma

| Dimension           | CMP Django (dieses Projekt · SSR)        | lucent-job-CMP (Schwester · API-First)       |
|---------------------|------------------------------------------|----------------------------------------------|
| **Ansatz**          | Server-Side Rendering (SSR)              | API-First (Headless-Backend + SPA)           |
| **Rendering-Ort**   | Server — Django rendert HTML             | Client — der Browser rendert React           |
| **Stack**           | Django 6.0 + HTMX + DaisyUI              | Flask 3.1 + React 19 / TS / Vite 6           |
| **Backend liefert** | fertiges HTML (`render()`)               | JSON (`jsonify`)                             |
| **Ports**           | 8000 (ein Prozess)                       | Backend 5000 / Frontend-Dev 3000 (getrennt)  |
| **Routing**         | Server-Routing via `path()`-Includes     | React Router (SPA)                           |

## SSR-Beleg (am Code geprüft)

Die Präsentationsschicht von CMP Django lebt vollständig im Server; es existiert
keine JSON-API — der Kontrakt ist Template ↔ Context.

| Merkmal                          | CMP Django (SSR)                        | lucent-job-CMP (API-First)          |
|----------------------------------|-----------------------------------------|-------------------------------------|
| Server-HTML-Templates            | **30** `.html`-Templates (zentral in `templates/`) | **0** — nur SPA-Shell    |
| `render()` / TemplateView        | **13** in Views                         | **0** im App-Code                   |
| `JsonResponse` / JSON-Endpoints  | **0** — keine JSON-API                  | — (Normalfall)                      |
| Progressive Enhancement          | HTMX (**2** Templates aktuell; Middleware projektweit) | —                    |

## API-First-Beleg (am Code geprüft)

Ein versioniertes JSON-Backend entkoppelt Frontend und Server. Die React-Seite
spricht ausschließlich über eine typisierte Service-Schicht.

| Merkmal                  | CMP Django (SSR)                    | lucent-job-CMP (API-First)                       |
|--------------------------|-------------------------------------|--------------------------------------------------|
| Versionierte API         | keine (bewusst weggelassen)         | `app/api/v1/` — **20** Blueprints, **99** Routes |
| Typisierter Client-Layer | entfällt — Views greifen direkt zu  | `frontend/src/api/*.ts` — **10** Services        |
| Serializer-Schicht       | kein DRF, keine Serializer          | eigene Serializer in Services                    |
| Datenformat-Vertrag      | HTML — Template ↔ Context           | JSON — FE/BE entkoppelt                          |

## Schichtenarchitektur (analog, nur Präsentationsschicht differiert)

| Ebene           | CMP Django (SSR)                     | lucent-job-CMP (API-First)            |
|-----------------|--------------------------------------|---------------------------------------|
| Präsentation    | `templates/` (DTL) + HTMX            | `pages/` → `hooks/` → `api/` ← `types/` (React) |
| Eingang         | `views.py` (dünn)                    | `api/` (Blueprints)                   |
| Business        | `services.py`                        | `services/` (keine Flask-Imports)     |
| Validierung     | `forms.py`                           | Request-Schemas in API/Services       |
| Domain / Daten  | `models.py` (Django ORM) + `core/domain/` | `domain/` ← `data/` (SQLAlchemy) |
| Grenzregel      | `core/` → `apps/`, nicht umgekehrt   | `api/` → `data/` verboten             |

## Auth, State & Tooling

Der Rendering-Ansatz zieht sich bis in Authentifizierung und Zustandshaltung
durch: Server-Session gegen stateless Token.

| Dimension     | CMP Django (SSR)                        | lucent-job-CMP (API-First)                  |
|---------------|------------------------------------------|---------------------------------------------|
| Auth          | Session-basiert (django-allauth), Signup deaktiviert | JWT / Token (stateless), Modi `stub`/`ldap` |
| Zustand       | Server-Session — Server-State           | stateless Backend — State im Client         |
| Admin-Tooling | Django Admin als primäres Tool          | eigene Admin-API + React-Views              |
| Datenbank     | Django ORM + PostgreSQL, Celery + Redis | SQLAlchemy + Alembic                        |
| Live-Updates  | HTMX / Seitenaufruf; Channels geplant (AP-12) | —                                     |
| Tests         | **330**                                 | ≈ **878** (771 Backend / 107 Frontend)      |

## Kern-Trade-offs

### SSR (CMP Django · Django + HTMX)

- **Stärke:** Weniger Moving Parts (ein Prozess, eine Sprache); schnelleres
  First-Paint; Grundfunktion ohne JS; SEO-freundlich.
- **Preis:** Interaktivität an HTMX / Server-Roundtrips gebunden; kein
  wiederverwendbarer API-Layer.
- **Rendering liegt bei:** Server.

### API-First (lucent-job-CMP · Flask + React)

- **Stärke:** FE/BE entkoppelt; API auch für Mobile / 3rd-Party nutzbar; reiche
  Client-Interaktivität ohne Roundtrips.
- **Preis:** Zwei Deployments & Toolchains; JS-Bundle nötig; der API-Contract
  muss gepflegt werden.
- **Rendering liegt bei:** Browser.

## Fazit

Die beiden Repos sind das kontrollierte A/B-Experiment desselben Portals:
**CMP Django** treibt den SSR-Weg — der Server rendert HTML, Session-Auth,
Django Admin, HTMX für punktuelle Dynamik, bewusst *ohne* DRF/API-Layer.
**lucent-job-CMP** treibt den API-First/SPA-Weg — JSON-Backend, typisierte
React-Frontend-Schicht, JWT, getrennte Deployments.
