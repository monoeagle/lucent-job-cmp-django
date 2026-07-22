# Templates, Partials, Vererbung

Wo Templates liegen, wie `base.html` aufgebaut ist, und was in CMP ein Partial von
einer normalen Seite unterscheidet.

## 1. Ziel des Kapitels

Wer eine neue Seite anlegt, muss wissen: In welchen Ordner kommt die Datei, welche
Blöcke bietet `base.html`, und wann braucht eine HTMX-Antwort ein eigenes,
layoutloses Partial statt der vollen Seite. Alle Angaben sind gegen die 30
`.html`-Dateien unter `cmp/templates/` geprüft.

## 2. Ablage: ein Verzeichnis, nicht pro App

`.claude/rules/htmx.md` (Zeile 3) schreibt vor: „Templates in
`apps/<app>/templates/<app>/`" — die Django-Konvention für App-lokale Templates.
**Real liegen alle 30 Templates zentral unter `cmp/templates/<app-name>/`**, nicht in
den App-Paketen selbst. Kein einziges `apps/*/templates/`-Verzeichnis existiert.
Das ist über die Settings so konfiguriert, nicht zufällig:

```python
TEMPLATES = [{
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    ...
}]
```

(`cmp/config/settings/base.py:48,51-52`) `DIRS` verweist auf das projektweite
`templates/`-Verzeichnis; `APP_DIRS=True` bleibt aktiv, greift aber mangels
App-lokaler `templates/`-Ordner nirgends. Die Unterordnernamen entsprechen den
App-Namen (`templates/catalog/`, `templates/orders/`, …), das erhält die
Namensraum-Trennung, die `{% include %}`/`{% extends %}`-Pfade sonst bräuchten,
nur eben an einem zentralen Ort. **Abweichung von der Konvention:** Wer die Regel
in `.claude/rules/htmx.md` wörtlich nimmt, sucht Templates am falschen Ort.

## 3. `base.html` und seine Blöcke

`cmp/templates/base.html` (28 Zeilen) definiert das komplette Seitengerüst:
Navbar, aufklappbare Sidebar (DaisyUI `drawer`), Message-Bereich, und genau zwei
Blöcke:

| Block | Zweck | Vorgabewert |
|---|---|---|
| `{% block title %}` | Seitentitel im `<title>`-Tag | `CloudMan Portal` |
| `{% block content %}` | Seiteninhalt innerhalb des `drawer-content`-Bereichs | leer |

Ein dritter Block, `{% block fixed_sidebar %}`, existiert nach dem
`drawer`-`div` (`base.html:25`) für Inhalte außerhalb des normalen Layoutflusses.
Genutzt wird er von genau einer Seite: `orders/form_view.html:178-205` legt dort
eine fest positionierte Zusammenfassungs-Sidebar ab (`position:fixed`), die auch
beim Scrollen sichtbar bleibt — etwas, das innerhalb des regulären
`content`-Blocks mit dem `drawer`-Layout nicht funktionieren würde.

`base.html` bindet außerdem `includes/navbar.html` und `includes/sidebar.html` per
`{% include %}` fest ein (Zeilen 13 und 22) sowie `includes/messages.html`
(Zeile 17) für Django-Messages — jede Seite bekommt sie automatisch, ohne sie
selbst einzubinden.

## 4. Eine typische erbende Seite

```django
{% extends "base.html" %}
{% block title %}Service-Katalog{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Service-Katalog</h1>
...
{% endblock %}
```

(`cmp/templates/catalog/template_list.html:1-4`, gekürzt) — das ist die
durchgehende Form aller 20 Seiten-Templates: `extends "base.html"`, `title`-Block,
`content`-Block.

## 5. Partials: kein `extends`, kein `<html>`

Ein Partial ist ein Template-Fragment ohne `{% extends %}` und ohne eigenes
`<!DOCTYPE>`/`<html>` — nur der HTML-Ausschnitt, der entweder per `{% include %}`
in eine erbende Seite eingebettet oder direkt als HTMX-Antwort zurückgegeben wird.
Vier Partials existieren:

| Partial | Verwendungsart |
|---|---|
| `catalog/partials/template_grid.html` | per `{% include %}` in `template_list.html:25` UND direkt als HTMX-Response (siehe Kapitel 4) |
| `orders/wizard/step_context.html` | nur `{% include %}` in `orders/wizard/wizard.html:55` |
| `orders/wizard/step_params.html` | nur `{% include %}` in `orders/wizard/wizard.html:57` |
| `orders/wizard/step_summary.html` | nur `{% include %}` in `orders/wizard/wizard.html:59` |

`template_grid.html` ist damit das einzige Partial, das beide Rollen gleichzeitig
spielt — eingebettetes Fragment und eigenständige HTMX-Antwort, je nachdem, ob
`TemplateListView.get_template_names()` einen HTMX-Request erkennt
(`cmp/apps/catalog/views.py:25-28`). Die drei Wizard-Partials sind reine
Include-Fragmente ohne eigene URL.

Die vier `includes/*.html`-Dateien (`navbar.html`, `sidebar.html`,
`messages.html`, `status_badge.html`) sind technisch ebenfalls Partials, dienen
aber ausschließlich dem Seitengerüst selbst, nicht einzelnen Fach-Seiten.

## 6. Eine Ausnahme: `debug_layout.html` erbt nicht von `base.html`

`cmp/templates/debug_layout.html` ist ein eigenständiges HTML-Dokument mit
eigenem `<!DOCTYPE>`, `<html>` und Inline-`<style>` (Zeilen 1-12) — es erbt nicht
von `base.html` und folgt keiner der Konventionen aus Abschnitt 4. Es gehört zur
selben Diagnose-Seite `/debug-layout/`, die in Kapitel 6.1 als Route ohne
Rollenprüfung auffiel; hier zeigt sich dieselbe Sonderstellung auch auf
Template-Ebene.

## 7. Zusammenfassung

Alle Templates liegen zentral unter `cmp/templates/<app-name>/`, nicht in den
App-Paketen selbst — eine Abweichung von der in `.claude/rules/htmx.md`
festgehaltenen Konvention. `base.html` liefert Navbar, Sidebar, Messages und drei
Blöcke (`title`, `content`, `fixed_sidebar`) — Letzteren nutzt bislang nur
`orders/form_view.html` für eine fest positionierte Zusammenfassungs-Sidebar. Ein
Partial erkennt man daran, dass es nicht
von `base.html` erbt und kein eigenes `<html>`-Gerüst hat; vier solcher Partials
existieren, eines davon (`template_grid.html`) dient sowohl als Include als auch
als eigenständige HTMX-Antwort. `debug_layout.html` folgt keinem der beiden Muster
und ist die einzige Ausnahme im gesamten Bestand.

> Quelle: cmp/templates/base.html, cmp/templates/catalog/template_list.html, cmp/templates/catalog/partials/template_grid.html, cmp/templates/orders/wizard/wizard.html, cmp/templates/orders/wizard/step_context.html, cmp/templates/orders/wizard/step_params.html, cmp/templates/orders/wizard/step_summary.html, cmp/templates/orders/form_view.html, cmp/templates/debug_layout.html, cmp/templates/includes/messages.html, cmp/apps/catalog/views.py, cmp/config/settings/base.py, .claude/rules/htmx.md — am Code geprüft 2026-07-22
