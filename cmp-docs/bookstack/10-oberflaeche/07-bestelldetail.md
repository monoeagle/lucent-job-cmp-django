# Bestelldetail

Die Detailseite einer Bestellung zeigt Kopfdaten und alle Positionen mit ihren
vollständig aufgelösten Parameterwerten.

## 1. Ziel der Seite

Wer eine einzelne Bestellung nachvollziehen will — welche Werte wurden
gewählt, in welchem Status steht sie — findet hier die vollständige Ansicht
inklusive aller Positionen. Bei Entwurfsbestellungen lässt sich hier zusätzlich
ein weiterer Service hinzufügen (siehe Dropdown „Add Service" im Code) oder die
Bestellung einreichen.

## 2. Screenshot

![Detailansicht der Bestellung #12 mit Status-Badge 'Eingereicht': Kopf mit Notiz, Erstelldatum und Besteller, darunter der Abschnitt Positionen (1) mit der Position 'Linux VM' und allen aufgelösten Parameterwerten in einem Raster (ram_gb 16, cpu_cores 8, location standort2, os_template ubuntu2204 …).](../../docs/images/screenshots/Screenshot_07_cmp.png)

Kopfdaten (Status, Notiz, Besteller) stehen oben, darunter jede Position mit
Template-Name und allen Parameterwerten im Raster. Der Status-Badge spiegelt
die Position im Workflow (Entwurf → Eingereicht → Genehmigung →
Bereitstellung → Aktiv).

## 3. Rolle und Zugriff

Geschützt durch `RequesterRequiredMixin` (`cmp/core/mixins.py:61`) — alle vier
Rollen dürfen eine Bestelldetailseite öffnen, sofern sie die ID kennen; die
View selbst schränkt den Zugriff nicht auf den Besteller ein (kein
`user=request.user`-Filter in `OrderDetailView.get_object`,
`cmp/apps/orders/views.py:66-70`). Existiert die Bestellung nicht, wirft
`OrderService.get_order` einen `NotFoundError`, den die View in `Http404`
übersetzt.

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/orders/<int:pk>/` | `orders:detail` | `OrderDetailView` | `cmp/apps/orders/views.py:60` |

Eingebunden über `path("orders/", include("apps.orders.urls"))`,
`cmp/config/urls.py:9`, mit `path("<int:pk>/", views.OrderDetailView.as_view(), name="detail")`
in `cmp/apps/orders/urls.py:10`.

## 5. Zusammenfassung

Der Kontext liefert zusätzlich die Liste aktiver Templates, wenn die
Bestellung noch im Status `draft` ist (`cmp/apps/orders/views.py:76-77`) — nur
dann macht ein „weitere Position hinzufügen" in der Oberfläche Sinn.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_07_cmp.png, cmp/apps/orders/views.py, cmp/apps/orders/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
