# HTMX-Konventionen und Fallstricke

Wie CMP HTMX tatsächlich einsetzt — an genau zwei Stellen im gesamten Bestand —
und ein dokumentierter Fehler, der zeigt, was passiert, wenn eine der beiden
Seiten der Konvention nicht folgt.

## 1. Ziel des Kapitels

`.claude/rules/htmx.md` verlangt „HTMX fuer partielle Updates statt
Full-Page-Reload" und „hx-target, hx-swap explizit setzen (kein implizites
Verhalten)". Dieses Kapitel zeigt an den beiden real existierenden HTMX-Stellen,
was das bedeutet — und wo die zweite Regel im Code nicht eingehalten wird.

## 2. Voraussetzung: `django-htmx`

`HtmxMiddleware` aus dem Paket `django-htmx` ist in
`cmp/config/settings/base.py` in `MIDDLEWARE` eingetragen und stellt
`request.htmx` als Wahrheitswert auf jedem Request bereit — das ist die einzige
Stelle, an der eine View serverseitig erkennen kann, ob eine Anfrage von HTMX
(statt vom normalen Seitenaufruf) stammt.

## 3. Die einzigen zwei HTMX-Stellen im Projekt

Ein Volltextgrep nach `hx-` über alle Templates ergibt **ausschließlich** Treffer
in zwei Dateien:

| Datei | hx-Attribute | Ziel |
|---|---|---|
| `templates/catalog/template_list.html:6-17` | `hx-get`, `hx-target`, `hx-trigger`, `hx-include` | Live-Suche und Kategorie-Filter |
| `templates/audit/audit_list.html:11-29` | `hx-get`, `hx-target`, `hx-trigger`, `hx-include`, `hx-push-url` | Filterfelder für Aktion/Ressourcentyp |

Kein anderes Template im Bestand verwendet HTMX — jede sonstige Interaktion läuft
über normale Formular-POSTs mit vollem Seiten-Redirect (siehe die `View`-Klassen
in Kapitel 2).

## 4. Das funktionierende Muster: Katalog-Suche

```django
<input type="search" name="q" ...
       hx-get="{% url 'catalog:list' %}"
       hx-target="#template-grid"
       hx-trigger="input changed delay:300ms"
       hx-include="[name='category']">
```

(`templates/catalog/template_list.html:6-12`) Das Eingabefeld feuert `hx-get` auf
dieselbe URL, die auch die volle Seite liefert. Die View entscheidet anhand
`request.htmx`, was sie zurückgibt:

```python
def get_template_names(self):
    if self.request.htmx:
        return ["catalog/partials/template_grid.html"]
    return [self.template_name]
```

(`cmp/apps/catalog/views.py:25-28`) Bei einem normalen Aufruf rendert dieselbe
`get_queryset()` die volle Seite mit `base.html`; bei einem HTMX-Request nur das
Partial `template_grid.html`, das htmx dann per `hx-target="#template-grid"` in
das Ziel-Element einsetzt. **Das ist der Kern der Konvention:** dieselbe View,
zwei Ausgabeformen, je nach `request.htmx`.

## 5. Fallstrick: `hx-target` ohne htmx-Zweig in der View

`audit_list.html` setzt dieselben vier hx-Attribute wie der Katalog, aber
`AuditLogListView` (`cmp/apps/audit/views.py:10`) hat **keine**
`get_template_names()`-Überschreibung und prüft `request.htmx` nirgends. Bei
jedem Filter-Tastendruck liefert die View die **komplette Seite** inklusive
`base.html` (Navbar, Sidebar) zurück, und htmx setzt dieses gesamte Markup als
`innerHTML` in `#audit-table` ein — verschachtelte Navbar und Sidebar innerhalb
der Tabelle, statt nur die Tabelle auszutauschen.

Der Fehler ist bereits als Arbeitspaket erfasst: `todo.md`, AP-15
„HTMX-Fragment-Fix Audit-Log", mit genau diesem Befund und der Katalog-Seite als
Vorlage für die Korrektur (Partial auslagern, `get_template_names()` analog zu
`cmp/apps/catalog/views.py:25` ergänzen).

## 6. Fallstrick: `hx-swap` wird nirgends explizit gesetzt

`.claude/rules/htmx.md` (Zeile 5) verlangt „`hx-target`, `hx-swap` explizit
setzen". In den real existierenden HTMX-Stellen (Abschnitt 3) taucht `hx-swap`
**kein einziges Mal** auf — beide Seiten verlassen sich auf htmx' Vorgabewert
`innerHTML`. Das funktioniert beim Katalog, weil das zurückgegebene Partial genau
den Inhalt von `#template-grid` beschreibt. Beim Audit-Log verschärft das
implizite `innerHTML` den Fehler aus Abschnitt 5 zusätzlich, weil die komplette
Seite eingesetzt wird, statt beim Fehlen eines expliziten `hx-swap` wenigstens
frühzeitig aufzufallen.

## 7. Zusammenfassung

HTMX kommt in CMP an genau zwei Stellen zum Einsatz, beide für Live-Filter über
`hx-get`/`hx-target`/`hx-trigger`/`hx-include`. Das Muster „View liefert je nach
`request.htmx` volle Seite oder Partial" funktioniert im Katalog vorbildlich, fehlt
aber beim Audit-Log komplett (AP-15) — dort wird ungewollt die gesamte Seite in
ein Tabellen-`div` geswappt. Zusätzlich wird `hx-swap` an keiner der beiden
Stellen explizit gesetzt, obwohl die Konvention das verlangt. Wer eine neue
HTMX-Stelle baut, sollte sich am Katalog orientieren, nicht am Audit-Log.

> Quelle: cmp/config/settings/base.py, cmp/templates/catalog/template_list.html, cmp/templates/audit/audit_list.html, cmp/apps/catalog/views.py, cmp/apps/audit/views.py, .claude/rules/htmx.md, todo.md (AP-15) — am Code geprüft 2026-07-22
