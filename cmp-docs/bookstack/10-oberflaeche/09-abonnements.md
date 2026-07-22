# Abonnements (Subscriptions)

Die Subscriptions-Seite listet die aktiven Service-Abonnements des angemeldeten
Benutzers.

## 1. Ziel der Seite

Ein Benutzer soll seine laufenden Services mit Gültigkeitszeitraum einsehen
und bei Bedarf kündigen können. Ein Abonnement entsteht, sobald eine
Bestellung erfolgreich bereitgestellt wurde.

## 2. Screenshot

![Seite 'Meine Subscriptions': Tabelle mit Spalten Nummer, Service, Status-Badge 'active', Gueltig ab, Gueltig bis und Details-Button für die Services Linux VM und Windows VM.](../../docs/images/screenshots/Screenshot_09_cmp.png)

Pro Zeile: Nummer, Service, Status-Badge, Gültigkeitszeitraum (Gültig ab /
Gültig bis) und ein Detail-Link.

## 3. Rolle und Zugriff

Geschützt durch `RequesterRequiredMixin` (`cmp/core/mixins.py:61`) — alle vier
Rollen sehen ihre eigenen Abonnements. Die Liste ist strikt auf den
angemeldeten Benutzer eingeschränkt:
`SubscriptionService.list_user_subscriptions(self.request.user.pk)`
(`cmp/apps/subscriptions/views.py:21-23`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View-Klasse | Codestelle |
|---|---|---|---|
| `/subscriptions/` | `subscriptions:list` | `SubscriptionListView` | `cmp/apps/subscriptions/views.py:14` |
| `/subscriptions/detail/<int:pk>/` | `subscriptions:detail` | `SubscriptionDetailView` | `cmp/apps/subscriptions/views.py:26` |
| `/subscriptions/cancel/<int:pk>/` | `subscriptions:cancel` | `SubscriptionCancelView` | `cmp/apps/subscriptions/views.py:39` |

Eingebunden über `path("subscriptions/", include("apps.subscriptions.urls"))`,
`cmp/config/urls.py:13`.

## 5. Zusammenfassung

Die Kündigung (`SubscriptionCancelView`) ist ein reiner POST-Endpunkt, der an
`SubscriptionService.cancel` delegiert und danach auf die Liste zurückleitet
(`cmp/apps/subscriptions/views.py:44-48`).

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_09_cmp.png, cmp/apps/subscriptions/views.py, cmp/apps/subscriptions/urls.py, cmp/core/mixins.py — am Code geprüft 2026-07-22
