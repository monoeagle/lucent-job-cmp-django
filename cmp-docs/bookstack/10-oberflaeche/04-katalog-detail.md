# Katalog-Detail — Parameter-Übersicht

Die Detailseite eines Service-Templates zeigt dessen vollständige
Parameter-Spezifikation, bevor der Requester eine Bestellung startet.

## 1. Ziel der Seite

Wer einen Service bestellen will, soll vorher sehen können, welche Angaben
nötig sind — Name, Typ, Pflichtstatus, Default und mögliche Optionen je
Parameter — ohne dafür schon das Bestellformular öffnen zu müssen.

## 2. Screenshot

![Detailseite des Service-Templates 'Linux VM': Titel mit Kategorie-Badge 'compute' und Version v1, darunter eine Parameter-Tabelle mit Spalten Name, Typ, Pflicht, Standard, Optionen über alle 30 Parameter (Systemtyp, Mandant, Standort, CPU Cores, RAM …). Unten der Button 'Jetzt bestellen'.](../../docs/images/screenshots/Screenshot_04_cmp.png)

Die Tabelle zeigt Name, Typ (`enum`, `string`, `integer`, `boolean`),
Pflichtangabe, Default und Optionen für jeden Parameter des Templates. Beim
**Linux VM**-Template sind das 30 Parameter über Kontext, Netzwerk, Sizing und
Betrieb hinweg. Der Button „Jetzt bestellen" führt zum Bestellformular (siehe
[Bestellformular](05-bestellformular.md)).

## 3. Rolle und Zugriff

Geschützt durch `RequesterRequiredMixin` (`cmp/core/mixins.py:61`) — alle vier
Rollen dürfen Katalog-Details ansehen. Existiert kein Template mit der
angefragten ID, wirft `CatalogService.get_template` einen `NotFoundError`, den
die View in `Http404` übersetzt (`cmp/apps/catalog/views.py:41-45`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/catalog/<int:pk>/` | `catalog:detail` | `TemplateDetailView` | `cmp/apps/catalog/views.py:36` |

Eingebunden über `path("catalog/", include("apps.catalog.urls"))`,
`cmp/config/urls.py:8`, mit `path("<int:pk>/", views.TemplateDetailView.as_view(), name="detail")`
in `cmp/apps/catalog/urls.py:9`.

## 5. Zusammenfassung

Die Parameter-Tabelle ist eine reine Anzeige des JSON-Feldes
`ServiceTemplate.parameters` (Feldreferenz siehe Anhang A.2) — sie validiert
nichts, das übernimmt erst das Bestellformular.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_04_cmp.png, cmp/apps/catalog/views.py, cmp/apps/catalog/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
