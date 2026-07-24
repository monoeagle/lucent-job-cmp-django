# 07 — Frontend: HTMX & DaisyUI

> **In diesem Kapitel:** CMP setzt auf **Server-Rendering** — Django liefert ganz
> normale HTML-Seiten aus, und HTMX macht sie dort interaktiv, wo es nötig ist,
> ganz ohne schweres JavaScript-Framework. Dieses Kapitel zeigt dir, wie das
> zusammenspielt.
>
> **Das lernst du:**
> - Warum CMP auf HTMX setzt (Server-Rendering + gezielte Interaktivität)
> - Wie ein HTMX-Request aussieht: `hx-get`, `hx-target`, `hx-swap`
> - Wo Templates und Styles im Code liegen
> - Wie DaisyUI und das Custom-Theme „Lucent" ins Spiel kommen
> - Wie Badge-Zähler (offene Bestellungen, Benachrichtigungen) in die Navigation kommen
>
> **Voraussetzung:** [07 — Async & Provisioning](07-async-und-provisioning.md)

---

## Warum HTMX?

Django kann von Haus aus fertige HTML-Seiten ausliefern — das ist robust,
einfach und gut testbar. Der Haken: Für kleine Interaktionen (eine Live-Suche,
ein Filter, ein Klick auf „Genehmigen", der nur eine Tabellenzeile aktualisieren
soll) müsste man sonst jedes Mal die ganze Seite neu laden.

Genau da setzt **HTMX** an: Es holt bei Bedarf ein kleines Stück Server-HTML nach
und tauscht es an Ort und Stelle aus — ohne schweres JavaScript-Framework und ohne
zweite Codebasis im Browser. Django bleibt die eine Quelle der Wahrheit; die Logik
liegt weiter in Views und Services.

💡 **Merke:** HTMX ist keine neue Sprache und kein Framework, das du lernen
musst. Es sind ein paar HTML-Attribute (`hx-get`, `hx-post`, `hx-target`, …),
die der Browser als „lade hier ein Stück Server-HTML nach" versteht. Die
eigentliche Logik bleibt komplett in Django — Views und Services liefern
einfach ein kleineres HTML-Fragment statt einer ganzen Seite.

---

## Ein HTMX-Request in der Praxis

Schauen wir uns ein reales Beispiel aus dem Katalog an (leicht vereinfacht,
aus `cmp/templates/catalog/template_list.html`):

```html
<input type="search" name="q" value="{{ request.GET.q|default:'' }}"
       class="input input-bordered flex-1"
       placeholder="Service suchen..."
       hx-get="{% url 'catalog:list' %}"
       hx-target="#template-grid"
       hx-swap="innerHTML"
       hx-trigger="input changed delay:300ms"
       hx-include="[name='category']">

<div id="template-grid">
  {% include "catalog/partials/template_grid.html" %}
</div>
```

Was hier passiert, Attribut für Attribut:

| Attribut | Bedeutung |
|----------|-----------|
| `hx-get` | Bei einem Event (siehe `hx-trigger`) macht HTMX einen `GET`-Request an diese URL — statt eines Formular-Submits mit vollem Reload. |
| `hx-target` | **Wohin** die Antwort eingebaut wird. Hier: das Element mit `id="template-grid"`. |
| `hx-swap` | **Wie** eingebaut wird. `innerHTML` heißt: Der Inhalt des Ziel-Elements wird komplett ersetzt. |
| `hx-trigger` | **Wann** ausgelöst wird. Hier: bei Tastatureingabe (`input`), aber erst 300ms nach der letzten Änderung (`delay:300ms`) — ein einfaches Debounce, ohne eine Zeile JavaScript. |
| `hx-include` | Welche zusätzlichen Formularfelder mitgeschickt werden — hier der Kategorie-Filter, damit Suchtext und Filter zusammen ausgewertet werden. |

Die View hinter `catalog:list` unterscheidet sich dabei kaum von einer
normalen Django-View. Sie prüft nur, ob es sich um einen HTMX-Request handelt
(`request.htmx`, bereitgestellt durch `django-htmx`), und rendert dann statt
der vollen Seite nur das Partial `catalog/partials/template_grid.html`.

⚠️ **Achtung:** Laut Konvention (siehe [`.claude/rules/htmx.md`](../../.claude/rules/htmx.md))
müssen `hx-target` **und** `hx-swap` **immer explizit** gesetzt werden — auch
wenn HTMX für `hx-swap` einen Default (`innerHTML`) mitbringt. Verlass dich
beim Schreiben neuer Templates nicht auf dieses implizite Verhalten. Explizit
heißt: für andere Entwickler (und für dich in drei Monaten) sofort
sichtbar, was passiert.

---

## Wo der Code liegt

| Was | Wo |
|-----|-----|
| App-Templates | `cmp/templates/<app>/` — z. B. `cmp/templates/catalog/`, `cmp/templates/orders/` |
| Wiederverwendbare Bausteine | `cmp/templates/includes/` — Navbar, Sidebar, Status-Badge, Messages |
| Basis-Layout | `cmp/templates/base.html` — bindet CSS, HTMX-JS und die Includes ein |
| CSS-Quelle (Tailwind + DaisyUI) | `cmp/static/css/input.css` |
| Gebautes CSS (nicht editieren!) | `cmp/static/css/output.css` |
| HTMX selbst (lokal, kein CDN) | `cmp/static/js/htmx.min.js` |

In `base.html` wird HTMX ganz gewöhnlich als lokale Datei eingebunden:

```html
<script src="{% static 'js/htmx.min.js' %}" defer></script>
```

💡 **Merke:** CMP lädt **kein** JavaScript von einem CDN — weder HTMX noch
Chart.js (`cmp/static/js/chart.umd.min.js`). Alles liegt lokal unter
`cmp/static/js/`. Das macht das Portal unabhängig von externen Diensten und
passt zur restriktiven Deployment-Umgebung (siehe [Kapitel 12](12-wie-es-in-produktion-laeuft.md)).

---

## DaisyUI und das Lucent-Theme

Für die Optik nutzt CMP **Tailwind CSS** als Utility-Framework und **DaisyUI**
als Komponenten-Bibliothek darauf (Buttons, Badges, Cards, Inputs — siehe die
`btn`-, `badge`- und `input`-Klassen im Beispiel oben). Darüber liegt ein
projekteigenes DaisyUI-Theme namens **„Lucent"**.

Das fertige CSS entsteht nicht von Hand, sondern wird aus `input.css` gebaut.
Dafür gibt es zwei npm-Scripts:

```bash
npm run css:build   # einmalig bauen (für Produktion / Commit)
npm run css:watch   # baut automatisch neu bei jeder Änderung
```

⚠️ **Achtung:** Es gibt **keine** Inline-Styles in CMP-Templates. Jede
optische Anpassung läuft über Tailwind-Klassen direkt im HTML. Wenn du dich
dabei ertappst, `style="..."` zu schreiben, ist das ein Signal, stattdessen
nach der passenden Utility-Klasse zu suchen (oder das Theme zu erweitern).

---

## Badges in der Navigation: `badge_counts`

Dir ist beim Beispiel oben vielleicht aufgefallen, dass in der Sidebar Zahlen
neben „Bestellungen" oder „Genehmigungen" auftauchen können — z. B. wie viele
Bestellungen noch offen sind. Diese Zähler kommen nicht aus jeder View
einzeln, sondern aus einem **Context-Processor**:
`cmp/core/context_processors.py::badge_counts`.

Ein Context-Processor läuft bei **jedem** Template-Rendering automatisch mit
und stellt seine Rückgabewerte allen Templates als Variablen zur Verfügung —
ohne dass jede View sie explizit übergeben müsste:

```python
def badge_counts(request):
    """Add notification and approval badge counts to every template."""
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": NotificationService.unread_count(request.user.pk),
        "pending_approval_count": ApprovalRequest.objects.filter(status="pending").count(),
        "open_order_count": Order.objects.filter(
            user=request.user, status__in=["draft", "submitted"]
        ).count(),
    }
```

In `cmp/templates/includes/sidebar.html` wird daraus einfach eine DaisyUI-Badge:

```html
{% if open_order_count and open_order_count > 0 %}
  <span class="badge badge-sm badge-primary">{{ open_order_count }}</span>
{% endif %}
```

💡 **Merke:** Context-Processoren sind der richtige Ort für Werte, die
**überall** im Template gebraucht werden (Navigation, Header). Für alles, was
nur eine einzelne Seite betrifft, bleibt der normale Weg über den View-Context
die bessere Wahl.

---

## Vertiefung für Entwickler

<details>
<summary><b>Build-Konfiguration — veraltete Pfade in <code>package.json</code> (bekannt, AP-23)</b></summary>

Die CSS-Scripts in `package.json` zeigen noch auf die **alten** Pfade aus der
Zeit, als das Projekt `mpp` hieß:

```json
"css:build": "tailwindcss -i mpp/static/css/input.css -o mpp/static/css/output.css",
"css:watch": "tailwindcss -i mpp/static/css/input.css -o mpp/static/css/output.css --watch"
```

Die tatsächlichen Assets liegen aber unter `cmp/static/css/input.css` bzw.
`cmp/static/css/output.css` — eine Altlast aus der Umbenennung `mpp` → `cmp`
(siehe [`CLAUDE.md`](../../CLAUDE.md): „Marketplace Portal (MPP-Django)").

In der Praxis heißt das: Führst du `npm run css:build`
ohne Anpassung aus, läuft Tailwind ins Leere (falscher Input-Pfad) oder
schreibt das Ergebnis an eine Stelle, die Django gar nicht ausliefert. Bis das
gefixt ist, prüfe die Pfade in `package.json` gegen die echten Verzeichnisse
unter `cmp/static/css/`, bevor du den CSS-Build startest.

Das ist ein **bekannter** Punkt — im Projekt als Arbeitspaket **AP-23**
(„Rename-Reste") erfasst, kein übersehener Fehler.
</details>

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| HTMX-Konventionen des Projekts | [`.claude/rules/htmx.md`](../../.claude/rules/htmx.md) |
| Basis-Layout mit CSS-/JS-Einbindung | `cmp/templates/base.html` |
| Ein vollständiges Live-Filter-Beispiel | `cmp/templates/catalog/template_list.html` + `cmp/templates/catalog/partials/` |
| Der Badge-Context-Processor | `cmp/core/context_processors.py` |
| Wo `badge_counts` registriert ist | `cmp/config/settings/base.py` (`TEMPLATES` → `context_processors`) |
| `django-htmx`-Middleware | `cmp/config/settings/base.py` (`HtmxMiddleware`) |

Öffne `cmp/templates/audit/audit_list.html` — dort findest du ein zweites,
sehr ähnliches Live-Such-Beispiel mit `hx-trigger="keyup changed delay:300ms"`.
Vergleiche es mit dem Katalog-Beispiel oben: gleiches Muster, andere Seite.

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Was macht `hx-target`, und was macht `hx-swap` — worin unterscheiden sie sich?
2. Warum lädt CMP HTMX als lokale Datei statt von einem CDN?
3. Wo müsstest du eine neue Zahl ergänzen, die z. B. „offene Genehmigungen für mich als Approver" in der Sidebar anzeigt?

<details>
<summary>Antworten anzeigen</summary>

1. `hx-target` bestimmt, **welches** Element die Antwort bekommt.
   `hx-swap` bestimmt, **wie** die Antwort dort eingebaut wird (z. B.
   `innerHTML` = Inhalt ersetzen). Beide müssen laut Konvention immer explizit
   gesetzt sein.
2. Damit CMP unabhängig von externen Diensten läuft und keine Anfragen an
   Drittanbieter-CDNs schickt — passend zur restriktiven Deployment-Umgebung.
3. In `badge_counts()` in `cmp/core/context_processors.py` einen neuen Wert im
   zurückgegebenen Dict ergänzen und ihn in `cmp/templates/includes/sidebar.html`
   ausgeben.
</details>

---

⟵ [07 — Async & Provisioning](07-async-und-provisioning.md) · [📖 Übersicht](README.md) · [09 — Setup lokal](09-setup-lokal.md) ⟶
