# Bestellungen — Übersicht

Die Bestellliste zeigt alle Bestellungen mit Filter-Tabs und Status-Chips —
für Requester die eigenen, für Approver und höher wahlweise alle.

## 1. Ziel der Seite

Der Benutzer soll den Status seiner Bestellungen verfolgen und über „Details"
zur Einzelansicht springen können. Wer mindestens Approver ist, kann
zusätzlich zwischen „Meine Bestellungen" und „Alle Bestellungen" umschalten.

## 2. Screenshot

![Bestellübersicht: Tabs 'Alle Bestellungen' / 'Meine Bestellungen', Status-Filterchips (Alle, Entwurf, Eingereicht, Genehmigung, Bereitstellung, Aktiv, Fehlgeschlagen, Abgelehnt) und eine Tabelle mit Spalten Nummer, Notizen, Besteller, farbigen Status-Badges, Positionen, Erstellt-Datum und Details-Button.](../../docs/images/screenshots/Screenshot_06_cmp.png)

Jede Zeile zeigt Nummer, Notiz, Besteller, farbcodierten Status (Entwurf,
Eingereicht, Genehmigung, Bereitstellung, Aktiv, Fehlgeschlagen, Abgelehnt),
Positionsanzahl und Erstellzeitpunkt. „Details" öffnet die Bestelldetailseite
(siehe [Bestelldetail](07-bestelldetail.md)).

## 3. Rolle und Zugriff

Geschützt durch `RequesterRequiredMixin` (`cmp/core/mixins.py:61`) — alle vier
Rollen sehen die Seite, aber mit unterschiedlichem Datenumfang:
`OrderListView._can_see_all` prüft mit `AccountService.is_at_least_role(
role, UserRole.APPROVER)`, ob der Tab „Alle Bestellungen" überhaupt Daten
zeigt (`cmp/apps/orders/views.py:30-37`). Requester sehen in jedem Fall nur
`Order.objects.filter(user=self.request.user)`
(`cmp/apps/orders/views.py:44-46`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/orders/` | `orders:list` | `OrderListView` | `cmp/apps/orders/views.py:24` |

Eingebunden über `path("orders/", include("apps.orders.urls"))`,
`cmp/config/urls.py:9`, mit `path("", views.OrderListView.as_view(), name="list")`
in `cmp/apps/orders/urls.py:9`.

## 5. Zusammenfassung

Die Sichtbarkeitsregel („eigene vs. alle Bestellungen") liegt direkt in der
View (`_can_see_all`), nicht in einem separaten Service — für eine reine
Lese-/Filteroperation ohne Nebenwirkungen ist das im Rahmen der
Thin-Views-Konvention vertretbar.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_06_cmp.png, cmp/apps/orders/views.py, cmp/apps/orders/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
