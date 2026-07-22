# Architekturüberblick (SSR)

CMP Django rendert die komplette Oberfläche serverseitig als HTML — bewusst ohne
JSON-API und ohne Single-Page-App. Dieses Kapitel erklärt das Grundprinzip und grenzt
es gegen das API-First-Schwesterprojekt ab.

## 1. Ziel des Kapitels

Wer neu ins Projekt kommt, soll nach diesem Kapitel beantworten können: Wo entsteht das
HTML, was unterscheidet einen normalen Seitenaufruf von einem HTMX-Request, und warum
gibt es hier keine REST-/JSON-API wie im Schwesterprojekt.

## 2. Server-Side-Rendering als Grundprinzip

Django selbst liefert für jeden Request fertiges HTML aus — es gibt keine JSON-API,
die ein Frontend-Framework befüllen müsste. Eine Prüfung aller View-Dateien
(`cmp/apps/*/views.py`) findet **keinen einzigen** `JsonResponse` im Anwendungscode.
Stattdessen rendern Views über `render()` oder Django-generische `TemplateView`s direkt
gegen die 30 HTML-Templates unter `cmp/templates/` (`find cmp/templates -name "*.html"`,
Stand 2026-07-22).

Der Browser bekommt damit bei jedem Aufruf eine vollständige oder teilweise fertige
Seite, keine Rohdaten. Das Kontrakt-Objekt zwischen Server und Browser ist die
Kombination aus Django-Template und dessen Context — nicht ein JSON-Schema.

## 3. Die Schichtenkette im Request

Jeder Request durchläuft dieselbe Kette, unabhängig davon, ob er eine Vollseite oder
ein HTMX-Partial anfordert:

```
Browser (HTMX-Attribute im HTML)
    |
    v
Django View (duenn, cmp/apps/<app>/views.py)
    |
    v
Django Form (Validierung, cmp/apps/<app>/forms.py)
    |
    v
Service (Business-Logik, cmp/apps/<app>/services.py)
    |
    v
Django ORM / Model (cmp/apps/<app>/models.py)
    |
    v
PostgreSQL
```

Views greifen auf Models nur lesend direkt zu; jede Änderung läuft über einen Service
(siehe [Kapitel 2.2 — Schichten](02-schichten-views-services-models.md)). Diese Kette
ist unabhängig davon, ob am Ende eine Vollseite oder ein HTMX-Fragment zurückkommt —
der Unterschied entsteht erst bei der Template-Auswahl am Ende der View.

## 4. Vollseite vs. HTMX-Partial

`django_htmx` ist als App und Middleware eingebunden
(`cmp/config/settings/base.py:17` — `"django_htmx"` in `INSTALLED_APPS`;
`cmp/config/settings/base.py:44` — `"django_htmx.middleware.HtmxMiddleware"`
in `MIDDLEWARE`). Die Middleware setzt `request.htmx`, sodass eine View am selben
Endpunkt zwei Antworten geben kann: eine Vollseite für den normalen Aufruf und ein
kleines HTML-Fragment für ein HTMX-Update.

Beleg dafür in `cmp/apps/catalog/views.py:25-27`:

```python
def get_template_names(self):
    if self.request.htmx:
        return ["catalog/partials/template_grid.html"]
    return [self.template_name]
```

`TemplateListView` liefert bei einem normalen Browseraufruf die volle Katalogseite
(inkl. `base.html`, Navbar, Sidebar), bei einem HTMX-Request nur das Grid-Fragment,
das per `hx-swap` in die bestehende Seite eingesetzt wird. Aktuell nutzen genau **zwei**
Templates HTMX-Attribute (`hx-get`, `hx-post`, `hx-target` oder `hx-swap`):
`cmp/templates/catalog/template_list.html` und `cmp/templates/audit/audit_list.html`
(`grep -rl "hx-get\|hx-post\|hx-target\|hx-swap" cmp/templates/`, Stand 2026-07-22). Der
Rest der Oberfläche arbeitet mit klassischen Vollseiten-Requests und Redirects — die
`HtmxMiddleware` steht projektweit zur Verfügung, wird aber bewusst nur punktuell
eingesetzt, nicht als generelles SPA-Ersatzmuster.

## 5. Abgrenzung zum API-First-Schwesterprojekt

CMP existiert zweimal: als SSR-Variante (dieses Projekt, `lucent-job-mpp-TDD-Django`)
und als API-First-Variante (`lucent-job-CMP`, Flask-Backend + React-SPA). Beide setzen
dasselbe fachliche Portal um, mit gegensätzlichem Rendering-Ansatz.

| Merkmal | CMP Django (dieses Projekt) | lucent-job-CMP (Schwester) |
|---|---|---|
| Rendering-Ort | Server (Django rendert HTML) | Client (Browser rendert React) |
| Backend liefert | HTML (`render()`) | JSON (`jsonify`) |
| API-Layer | keiner — bewusst kein DRF | versioniertes JSON-Backend |
| Port | 8000, ein Prozess | Backend 5000 / Frontend-Dev 3000, getrennt |
| Auth | Session (django-allauth) | JWT / Token, stateless |
| Zustand | Server-Session | State im Client |
| Live-Updates | HTMX-Partials; Channels/WebSocket geplant (AP-12) | eigener Client-State |

Der wichtigste Unterschied ist strukturell: In CMP Django gibt es keinen
wiederverwendbaren API-Layer, den ein Mobile-Client oder ein Drittsystem ansprechen
könnte — jede Interaktion läuft über eine HTML-Antwort an genau diesen Browser. Das ist
kein Zwischenstand, sondern die bewusste Entscheidung dieses Schwesterprojekts (siehe
`CLAUDE.md`: „Bewusstes Gegenstück zu mpp-TDD: kein API-First, kein React, kein DRF").

## 6. Zusammenfassung

CMP Django liefert bei jedem Request fertiges HTML, nie JSON — im Code nachweisbar
durch null `JsonResponse`-Treffer im gesamten App-Code. `django_htmx` erlaubt es
einzelnen Views, je nach `request.htmx` zwischen Vollseite und Partial zu unterscheiden;
das ist heute in zwei von 30 Templates umgesetzt, nicht projektweit. Die Abgrenzung zum
API-First-Schwesterprojekt ist kein Detail, sondern das Grundprinzip: kein API-Layer,
keine SPA, Server-Session statt Token. Die folgenden Kapitel gehen auf die
Schichtentrennung (2.2), die Laufzeit-Topologie (2.3), die App-Landschaft (2.4) und den
End-to-End-Ablauf (2.5) ein.

> Quelle: cmp-docs/docs/grundlagen/architektur.md, cmp-docs/docs/referenz/architektur-vergleich.md, cmp/config/settings/base.py, cmp/apps/catalog/views.py — am Code geprüft 2026-07-22
