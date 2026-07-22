# URL-Referenz

Vollständige Liste aller CMP-URLs mit View-Klasse, HTTP-Methode und erforderlicher
Rolle. Jede Zeile ist gegen `cmp/config/urls.py` und die `urls.py` der jeweiligen
App geprüft.

## 1. Ziel des Kapitels

Wer eine URL im Browser oder in einem Template sucht, findet hier den Pfad, den
Namen für `{% url %}`/`reverse()`, die View-Klasse und die Mindestrolle. Die Tabellen
lösen das bisherige `cmp-docs/docs/referenz/url-referenz.md` ab, das an mehreren
Stellen vom Code abweicht (Abschnitt 10).

## 2. Rollen-Legende

CMP kennt genau vier Rollen (`cmp/core/domain/enums.py:5-9`): `requester`,
`approver`, `admin`, `superadmin`. Die Rollenprüfung erfolgt über vier Mixins in
`cmp/core/mixins.py:61-95`, die jeweils eine Liste erlaubter Rollen zurückgeben:

| Kürzel | Mixin | Erlaubte Rollen |
|---|---|---|
| requester+ | `RequesterRequiredMixin` | requester, approver, admin, superadmin |
| approver+ | `ApproverRequiredMixin` | approver, admin, superadmin |
| admin+ | `AdminRequiredMixin` | admin, superadmin |
| superadmin | `SuperadminRequiredMixin` | superadmin |

Da es keine Rolle unterhalb von `requester` gibt, deckt `requester+` **jeden
angemeldeten Nutzer** ab — „alle" und „requester+" sind im Code dieselbe Menge. Die
Tabellen unten schreiben deshalb einheitlich `requester+`.

## 3. Dashboard (`cmp/apps/dashboard/urls.py`, Prefix `""`)

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/` | `dashboard:home` | `DashboardView` (`views.py:10`) | GET | requester+ |
| `/debug-layout/` | `dashboard:debug_layout` | `TemplateView` (Django, inline in `urls.py:29-36`) | GET | **keine, nur wenn `DEBUG=True`** |
| `/admin-panel/` | `dashboard:admin_dashboard` | `AdminDashboardView` (`admin_views.py:9`) | GET | admin+ |
| `/admin-panel/config/` | `dashboard:admin_config` | `AdminConfigView` (`admin_views.py:21`) | GET | admin+ |
| `/admin-panel/rules/` | `dashboard:admin_rules` | `AdminRulesView` (`admin_views.py:38`) | GET | superadmin |

Bis AP-22 war `/debug-layout/` unbedingt in `urlpatterns` verdrahtet — ohne
eigene View-Klasse, ohne Rollen-Mixin, und damit als einzige Seite im Portal ganz
ohne Login erreichbar. Seit AP-22 steht die Route hinter einer Bedingung
(`dashboard/urls.py:29`):

```python
if settings.DEBUG:
    urlpatterns += [
        path(
            "debug-layout/",
            TemplateView.as_view(template_name="debug_layout.html"),
            name="debug_layout",
        ),
    ]
```

In Produktion (`DEBUG=False`) wird die Route also gar nicht erst registriert —
ein Aufruf von `/debug-layout/` liefert dort `404`, nicht etwa eine ungeschützte
Seite. Immer noch ohne eigenes Rollen-Mixin, aber das ist in der Entwicklung
(wo die Route existiert) bewusst so: ein reines Diagnose-Template für das
Sidebar-Layout, nirgends verlinkt.

## 4. Katalog (`cmp/apps/catalog/urls.py`, Prefix `catalog/`)

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/catalog/` | `catalog:list` | `TemplateListView` (`views.py:13`) | GET | requester+ |
| `/catalog/<pk>/` | `catalog:detail` | `TemplateDetailView` (`views.py:36`) | GET | requester+ |

`catalog:list` liefert bei HTMX-Requests nur das Partial
`catalog/partials/template_grid.html` zurück, siehe Kapitel 4.

## 5. Bestellungen (`cmp/apps/orders/urls.py`, Prefix `orders/`)

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/orders/` | `orders:list` | `OrderListView` (`views.py:24`) | GET | requester+ |
| `/orders/<pk>/` | `orders:detail` | `OrderDetailView` (`views.py:60`) | GET | requester+ |
| `/orders/create/<template_pk>/` | `orders:create` | `OrderCreateView` (`views.py:81`) | GET, POST | requester+ |
| `/orders/create/<template_pk>/form/` | `orders:create_form` | `OrderFormView` (`views.py:292`) | GET, POST | requester+ |
| `/orders/<pk>/add-item/<template_pk>/` | `orders:add_item` | `OrderAddItemView` (`views.py:375`) | GET, POST | requester+ |
| `/orders/<pk>/remove-item/<item_pk>/` | `orders:remove_item` | `OrderRemoveItemView` (`views.py:419`) | POST | requester+ |
| `/orders/<pk>/submit/` | `orders:submit` | `OrderSubmitView` (`views.py:431`) | POST | requester+ |

`orders:create` ist der mehrschrittige Wizard mit Session-State, `orders:create_form`
eine alternative Einzelseiten-Variante mit allen Feldern auf einmal — beide führen
zum selben `OrderService.add_item`.

## 6. Genehmigungen (`cmp/apps/approvals/urls.py`, Prefix `approvals/`)

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/approvals/` | `approvals:queue` | `ApprovalQueueView` (`views.py:12`) | GET | approver+ |
| `/approvals/<pk>/approve/` | `approvals:approve` | `ApprovalApproveView` (`views.py:31`) | POST | approver+ |
| `/approvals/<pk>/reject/` | `approvals:reject` | `ApprovalRejectView` (`views.py:41`) | POST | approver+ |

## 7. Subscriptions (`cmp/apps/subscriptions/urls.py`, Prefix `subscriptions/`)

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/subscriptions/` | `subscriptions:list` | `SubscriptionListView` (`views.py:14`) | GET | requester+ |
| `/subscriptions/detail/<pk>/` | `subscriptions:detail` | `SubscriptionDetailView` (`views.py:26`) | GET | requester+ |
| `/subscriptions/cancel/<pk>/` | `subscriptions:cancel` | `SubscriptionCancelView` (`views.py:39`) | POST | requester+ |

## 8. Benachrichtigungen und Audit

Benachrichtigungen (`cmp/apps/notifications/urls.py`, Prefix `notifications/`):

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/notifications/` | `notifications:list` | `NotificationListView` (`views.py:11`) | GET | requester+ |
| `/notifications/mark-read/<pk>/` | `notifications:mark_read` | `NotificationMarkReadView` (`views.py:31`) | POST | requester+ |
| `/notifications/mark-all-read/` | `notifications:mark_all_read` | `NotificationMarkAllReadView` (`views.py:37`) | POST | requester+ |

Audit (`cmp/apps/audit/urls.py`, Prefix `audit/`):

| Pfad | Name | View | Methode | Rolle |
|---|---|---|---|---|
| `/audit/` | `audit:list` | `AuditLogListView` (`views.py:10`) | GET | admin+ |
| `/audit/export/` | `audit:export` | `AuditLogExportView` (`views.py:32`) | GET | admin+ |

`audit:export` liefert einen CSV-`HttpResponse`, kein Template.

## 9. Konten und Login

`cmp/config/urls.py:6-7` bindet unter demselben Prefix `accounts/` zwei Quellen ein:
django-allauth (`allauth.urls`) und die eigene `apps.accounts.urls`.

| Pfad | Name | Quelle | Methode | Rolle |
|---|---|---|---|---|
| `/accounts/login/` | `account_login` | allauth (`allauth/account/urls.py:11`) | GET, POST | anonym |
| `/accounts/logout/` | `account_logout` | allauth (`allauth/account/urls.py:12`) | GET, POST | requester+ |
| `/accounts/profile/` | `accounts:profile` | `ProfileView` (`cmp/apps/accounts/views.py:5`) | GET | requester+ |

`/accounts/profile/` ist **keine** allauth-Seite, sondern eine eigene
`TemplateView` mit `RequesterRequiredMixin`. Signup-URLs existieren im
allauth-Paket, sind aber über `ACCOUNT_SIGNUP_ENABLED = False`
(`cmp/config/settings/base.py:99`) funktional gesperrt — Nutzer legt ausschließlich
der Django Admin an.

## 10. Abweichungen zur bisherigen Referenz-Doku

`cmp-docs/docs/referenz/url-referenz.md` weicht an folgenden Stellen vom Code ab:

| Referenz-Doku | Code | Befund |
|---|---|---|
| `/subscriptions/<pk>/` | `/subscriptions/detail/<pk>/` | Segment `detail/` fehlt in der Doku |
| `/subscriptions/<pk>/cancel/` | `/subscriptions/cancel/<pk>/` | Segment-Reihenfolge vertauscht |
| — | `/debug-layout/`, `/admin-panel/`, `/admin-panel/config/`, `/admin-panel/rules/` | in der Doku komplett fehlend |
| — | `/orders/create/<template_pk>/form/`, `/orders/<pk>/add-item/<template_pk>/`, `/orders/<pk>/remove-item/<item_pk>/` | in der Doku komplett fehlend |
| — | `/audit/export/` | in der Doku komplett fehlend |
| „Auth (django-allauth)" listet `/accounts/profile/` ohne View-Angabe | eigene `ProfileView`, keine allauth-Seite | Doku suggeriert allauth-Herkunft |

## 11. Zusammenfassung

CMP hat 21 anwendungseigene URLs über acht Apps plus die allauth-Login/Logout-Routen.
Die Rollenprüfung läuft ausschließlich über die vier Mixins aus Abschnitt 2; eine
Ausnahme ist `/debug-layout/`, die ganz ohne Login auskommt — seit AP-22 aber nur
noch in der Entwicklung, weil die Route bei `DEBUG=False` gar nicht registriert
wird. Die bisherige Referenz-Doku war an sechs Stellen veraltet oder unvollständig
— Abschnitt 10 zeigt die Korrekturen.

> Quelle: cmp/config/urls.py, cmp/apps/dashboard/urls.py, cmp/apps/dashboard/views.py, cmp/apps/dashboard/admin_views.py, cmp/apps/catalog/urls.py, cmp/apps/catalog/views.py, cmp/apps/orders/urls.py, cmp/apps/orders/views.py, cmp/apps/approvals/urls.py, cmp/apps/approvals/views.py, cmp/apps/subscriptions/urls.py, cmp/apps/subscriptions/views.py, cmp/apps/notifications/urls.py, cmp/apps/notifications/views.py, cmp/apps/audit/urls.py, cmp/apps/audit/views.py, cmp/apps/accounts/urls.py, cmp/apps/accounts/views.py, cmp/core/mixins.py, cmp/core/domain/enums.py, cmp/config/settings/base.py, venv/lib/python3.12/site-packages/allauth/account/urls.py, cmp-docs/docs/referenz/url-referenz.md — am Code geprüft 2026-07-22
