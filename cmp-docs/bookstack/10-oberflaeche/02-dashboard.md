# Dashboard

Das Dashboard ist die Startseite nach dem Login und fasst den Status des
angemeldeten Benutzers (oder — bei Admin/Superadmin — des gesamten Systems) in
Kennzahlen, Tabellen und zwei Diagrammen zusammen.

## 1. Ziel der Seite

Die Seite soll auf einen Blick zeigen: Wie viele Bestellungen und Genehmigungen
sind offen, wie viele Services sind aktiv, was ist zuletzt passiert. Requester
sehen ihre eigenen Zahlen, Admin/Superadmin sehen systemweite Zahlen.

## 2. Screenshot

![Requester-Dashboard: vier KPI-Kacheln (Offene Bestellungen, Offene Genehmigungen, Aktive Services, Templates), Karten für Benachrichtigungen und Review Requests, Tabelle der letzten Bestellungen, Donut-Diagramm 'Bestellungen nach Status', Liste beliebter Services und ein Liniendiagramm 'Bestellungen pro Monat'.](../../docs/images/screenshots/Screenshot_02_cmp.png)

Oben vier KPI-Kacheln (Offene Bestellungen, Offene Genehmigungen, Aktive
Services, Templates), darunter Karten für Benachrichtigungen und Review
Requests, die letzten Bestellungen mit Status-Badges, ein Donut-Diagramm
„Bestellungen nach Status", die beliebtesten Services und der Bestell-Verlauf
pro Monat als Liniendiagramm. Die Diagramme nutzen lokal gebundeltes Chart.js
(keine CDN-Abhängigkeit).

## 3. Rolle und Zugriff

Geschützt durch `RequesterRequiredMixin` (`cmp/core/mixins.py:61`) — jede
angemeldete Rolle (Requester, Approver, Admin, Superadmin) darf die Seite
sehen. Der Inhalt unterscheidet sich aber je nach Rolle: `DashboardView`
prüft mit `AccountService.is_at_least_role(user.role, UserRole.ADMIN)`
(`cmp/apps/dashboard/views.py:18`), ob systemweite Admin-Statistiken
(`DashboardService.get_admin_stats`) oder benutzerbezogene Statistiken
(`DashboardService.get_user_stats`) angezeigt werden.

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/` | `dashboard:home` | `DashboardView` | `cmp/apps/dashboard/views.py:10` |

Eingebunden über `path("", include("apps.dashboard.urls"))`,
`cmp/config/urls.py:14`, mit `path("", views.DashboardView.as_view(), name="home")`
in `cmp/apps/dashboard/urls.py:8`.

## 5. Zusammenfassung

Das Dashboard ist eine einzelne View mit rollenabhängiger Datenauswahl statt
zweier getrennter Templates — der Unterschied zwischen Requester- und
Admin-Ansicht entsteht ausschließlich im Kontext, den `get_context_data`
zusammenstellt.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_02_cmp.png, cmp/apps/dashboard/views.py, cmp/apps/dashboard/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
