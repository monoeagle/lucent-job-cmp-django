# Wann JS, wann HTMX

CMP ist bewusst SSR: kein Frontend-Framework, kein Build-Schritt für
Anwendungslogik. Diese Seite zeigt, wie wenig eigenes JavaScript daraus folgt —
und in welchen drei Fällen es trotzdem eingesetzt wird.

## 1. Ziel des Kapitels

Wer eine neue Interaktion baut, muss entscheiden: HTMX-Request, oder eigenes
JavaScript? Diese Seite leitet die Regel nicht abstrakt her, sondern aus den
tatsächlich vorhandenen Fällen im Code — es gibt genau drei Kategorien, keine
vierte.

## 2. Der Bestand: fast kein eigenes JavaScript

`cmp/static/js/` enthält zwei Dateien, beide Fremdbibliotheken:

| Datei | Herkunft |
|---|---|
| `htmx.min.js` | HTMX-Runtime |
| `chart.umd.min.js` | Chart.js |

**Keine einzige eigene `.js`-Datei existiert im Projekt.** Eigenes JavaScript
kommt ausschließlich als Inline-`<script>`-Block in fünf Templates vor:
`orders/form_view.html`, `approvals/approval_queue.html`, `dashboard/dashboard.html`,
`admin_panel/dashboard.html`, `debug_layout.html` (Letzteres ein Diagnose-Template
ohne Fachbezug, siehe Kapitel 6.3 Abschnitt 6). Das ist die Kernaussage dieser
Seite: **die Entscheidung „JS oder HTMX" stellt sich in CMP kaum, weil so selten
JS gebraucht wird.**

## 3. Fall 1 — HTMX: ein Request, ein Ziel-Element

Wenn eine Interaktion mit **einem** serverseitig gerenderten Fragment beantwortet
werden kann, ist HTMX das Mittel der Wahl — die zwei Stellen aus Kapitel 6.4
(Katalog-Suche, Audit-Filter) sind die einzigen Beispiele, und beide folgen genau
diesem Muster: Tastatureingabe löst `hx-get` aus, die View liefert ein Partial,
htmx tauscht ein Element aus. Kein JavaScript nötig.

## 4. Fall 2 — Vendor-JS: eine Fähigkeit, die es nur als Bibliothek gibt

`dashboard/dashboard.html:135` und `admin_panel/dashboard.html:139` binden
Chart.js über `chart.umd.min.js` ein, um die Bestellstatistiken als Diagramm zu
rendern. Das lässt sich nicht durch HTMX ersetzen — HTMX tauscht HTML aus, zeichnet
aber kein Canvas. Beide Templates lesen die Chart-Daten aus einem
serverseitig gerenderten `{{ ... |json_script:"..." }}`-Block und reichen sie an
`new Chart(...)` weiter; die serverseitige Aufbereitung bleibt in
`DashboardService`, nur das Zeichnen selbst ist JS.

## 5. Fall 3 — eigenes JavaScript: rein clientseitiger Zustand oder Mehrfach-Requests

Zwei Templates begründen eigenes JavaScript, aus zwei unterschiedlichen Gründen:

**Rein clientseitige Interaktion ohne Server-Roundtrip:**
`approvals/approval_queue.html:159-171` klappt Genehmigungs-Details ein/aus
(`toggleReview`) — reine DOM-Manipulation (`style.display`,
`style.transform`), die serverseitig nichts zu validieren oder nachzuladen hat.
Ebenso liest `orders/form_view.html:91-167` das Parameter-Schema als JSON
(`{{ template_parameters_json|json_script:"template-params" }}`, Zeile 89) und
wertet `affects_options_of` **im Browser** aus: Ändert sich ein `enum`-Feld,
füllt das Skript abhängige Felder aus `constraints.options[].metadata` aus
(`form_view.html:109-143`) — komplett clientseitig, ohne Request. Das ist die
praktische Ergänzung zu [Anhang A.2](../anhang-a-neuen-service-anlegen/02-das-parameter-schema.md),
die `affects_options_of` als „ausgewertet in `templates/orders/form_view.html:104`"
nennt: **die Auswertung ist Browser-JavaScript, kein Server-Code.**

**Mehrere sequenzielle Requests, kein einzelnes Ziel-Element:**
Für die Sammel-Aktionen „Alle genehmigen"/„Alle ablehnen" reicht ein einzelner
HTMX-Swap nicht — jede ausgewählte Genehmigung braucht einen eigenen POST gegen
`/approvals/<pk>/approve/` bzw. `/approvals/<pk>/reject/`
(dieselben URLs wie in Kapitel 6.1), aber nacheinander und mit Reload erst nach
dem letzten. `approval_queue.html:215-235` löst das mit rohem `fetch()` in einer
rekursiven Funktion `submitBulk()`, die die IDs einzeln abarbeitet:

```javascript
var formData = new FormData(form);
fetch(form.action, { method: 'POST', body: formData, redirect: 'follow' })
  .then(function() { submitBulk(ids, action, comment); });
```

Das ist der einzige Ort im Projekt, an dem `fetch()` statt HTMX oder eines
normalen Formular-POSTs verwendet wird — begründet dadurch, dass HTMX für „N
Requests nacheinander, ein Reload am Ende" kein eingebautes Muster anbietet.

## 6. Die Entscheidungsregel

| Situation | Mittel | Beleg |
|---|---|---|
| Ein Server-Roundtrip liefert ein Fragment, das ein Element ersetzt | HTMX | Katalog-Suche, Audit-Filter (Kapitel 6.4) |
| Eine Fähigkeit existiert nur als JS-Bibliothek (Diagramme) | Vendor-JS einbinden | Chart.js in beiden Dashboards |
| Reiner Client-Zustand ohne Serverbezug, oder mehrere Requests ohne einzelnes Swap-Ziel | eigenes Inline-JavaScript | Collapse/Auto-Fill in `form_view.html`, Bulk-Aktionen in `approval_queue.html` |

## 7. Zusammenfassung

CMP hat de facto kein eigenständiges JavaScript-Ökosystem — zwei Vendor-Dateien,
fünf Inline-`<script>`-Blöcke, keine eigene `.js`-Datei. HTMX deckt jeden Fall ab,
in dem ein Server-Fragment ein Element ersetzt. JavaScript kommt nur dort ins
Spiel, wo entweder eine Fähigkeit fehlt, die HTMX grundsätzlich nicht bietet
(Diagramme), oder wo die Interaktion clientseitig bleibt bzw. mehrere Requests
ohne ein einzelnes Ziel-Element braucht. Wer eine neue Funktion baut und in einer
dieser drei Kategorien landet, hat damit auch das passende Mittel gefunden.

> Quelle: cmp/static/js/, cmp/templates/orders/form_view.html, cmp/templates/approvals/approval_queue.html, cmp/templates/dashboard/dashboard.html, cmp/templates/admin_panel/dashboard.html, cmp/templates/debug_layout.html — am Code geprüft 2026-07-22
