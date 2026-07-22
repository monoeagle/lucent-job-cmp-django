# View-Typen und Thin-View-Regel

Welche Django-CBVs CMP tatsächlich einsetzt, wo eine View aufhört und ein Service
anfängt, und eine konkrete Stelle, an der diese Grenze heute verwischt.

## 1. Ziel des Kapitels

CLAUDE.md fordert „Thin Views — Logik gehoert in Services, nicht in Views oder
Models" (`.claude/rules/django.md`, Zeile 1). Dieses Kapitel zeigt, welche
Django-View-Klassen dafür verwendet werden, was „dünn" in CMP konkret bedeutet, und
benennt eine reale Stelle, an der zwei Views dieselbe Logik duplizieren statt sie
gemeinsam an einen Service zu delegieren.

## 2. Verwendete CBV-Typen

Ausgezählt über alle 25 Views in `cmp/apps/*/views.py` und
`cmp/apps/dashboard/admin_views.py`:

| Django-CBV | Anzahl | Verwendung |
|---|---|---|
| `django.views.View` | 7 | Reine Aktionen ohne eigenes Template: Genehmigen/Ablehnen, Kündigen, Bestellung einreichen/Position entfernen, CSV-Export |
| `ListView` | 4 | Listen mit Such-/Filterparametern aus der Query-String |
| `TemplateView` | 5 | Seiten mit zusammengesetztem Kontext ohne Django-Model-Queryset (Dashboard, Admin-Panel, Profil) |
| `DetailView` | 3 | Einzelobjekt-Anzeige über `get_object()` |
| `FormView` | 1 | `OrderAddItemView` — einzige View mit Djangos `form_valid`/`form_invalid`-Zyklus |

**Auffällig:** Kein `CreateView`, `UpdateView` oder `DeleteView` kommt vor. Diese
Django-Generics binden ein ModelForm direkt an `model.save()`/`model.delete()` und
laden dazu ein, Geschäftsregeln (Statuswechsel, Vorbedingungen) in die View statt in
den Service zu ziehen. CMP verzichtet bewusst darauf — jede schreibende Aktion läuft
über ein einfaches `View` mit einem expliziten Service-Aufruf, siehe
`OrderSubmitView` in Kapitel 2 des Handbuchs
(`02-architektur-und-prozesse/02-schichten-views-services-models.md`).

## 3. Was „dünn" bei jedem CBV-Typ bedeutet

| CBV | Dünn heißt | Beleg |
|---|---|---|
| `View` | `post()`/`get()` ruft genau einen Service-Aufruf, übersetzt Exception in `messages`, leitet weiter | `OrderSubmitView.post` (`orders/views.py:434-440`) |
| `ListView` | `get_queryset()` liest Query-Parameter und reicht sie an einen Service oder direkt an den Model-Manager weiter, keine Statuslogik | `OrderListView.get_queryset` (`orders/views.py:39-50`) |
| `DetailView` | `get_object()` fängt `NotFoundError` des Service ab und wandelt sie in `Http404` | `OrderDetailView.get_object` (`orders/views.py:66-70`) |
| `TemplateView` | `get_context_data()` sammelt Werte aus Services, entscheidet aber keine Geschäftsregel selbst | `DashboardView.get_context_data` (`dashboard/views.py:13-36`) |
| `FormView` | `form_valid()` reicht `cleaned_data` an einen Service, fängt dessen Exceptions ab | `OrderAddItemView.form_valid` (`orders/views.py:399-416`) |

## 4. Wo die Regel real verletzt wird

`OrderCreateView` (Wizard, `orders/views.py:81-289`) und `OrderFormView`
(Einzelseiten-Formular, `orders/views.py:292-372`) enthalten **identische**
Gruppierungslogik für Template-Parameter — beide Views bauen unabhängig
voneinander dieselbe Struktur:

```python
groups = {}
for param in template.parameters:
    group = param.get("group", "Allgemein")
    if group not in groups:
        groups[group] = []
    groups[group].append(param)
sorted_groups = sorted(
    groups.items(),
    key=lambda g: min(p.get("display_order", 999) for p in g[1]),
)
```

Beleg: `OrderCreateView._get_steps` (`orders/views.py:101-113`) und
`OrderFormView._get_grouped_parameters` (`orders/views.py:303-312`) — Zeile für
Zeile dieselbe Gruppier- und Sortierlogik, einmal inline in einer Methode namens
`_get_steps`, einmal in einer eigenen Hilfsmethode. Das ist keine
Statusmaschinen-Logik wie in Kapitel 2, aber es ist Datenaufbereitung, die zweimal
in `views.py` steht statt einmal in `CatalogService`. Wer die Gruppierregel ändert
(z. B. eine dritte Sortierdimension), muss beide Stellen finden und synchron
halten. Kein Arbeitspaket in `todo.md` erfasst das bisher — es ist ein offener
Befund dieses Kapitels, kein bekanntes AP.

Der in Kapitel 6.1 genannte Fall `/debug-layout/` war bis AP-22 eine andere Art
von Regelverstoß (fehlende Rollenprüfung, kein Schichtproblem); seit AP-22
existiert die Route in Produktion gar nicht mehr und gehört ohnehin nicht
hierher.

## 5. Zusammenfassung

CMP nutzt CBVs konsequent nach Zweck: `View` für Aktionen, `ListView`/`DetailView`
für Lesezugriffe, `TemplateView` für zusammengesetzte Seiten, `FormView` einmalig
für den formularbasierten Add-Item-Fall. Model-mutierende Generics
(`CreateView`/`UpdateView`/`DeleteView`) werden bewusst gemieden. Die Thin-View-Regel
selbst ist eingehalten, was Statuswechsel angeht — an einer Stelle aber nicht, was
Datenaufbereitung angeht: `OrderCreateView` und `OrderFormView` duplizieren dieselbe
Gruppierlogik, die eigentlich einmal in `CatalogService` gehören würde.

> Quelle: cmp/apps/orders/views.py, cmp/apps/catalog/views.py, cmp/apps/dashboard/views.py, cmp/apps/dashboard/admin_views.py, cmp/apps/subscriptions/views.py, cmp/apps/notifications/views.py, cmp/apps/audit/views.py, cmp/apps/approvals/views.py, cmp/apps/accounts/views.py, .claude/rules/django.md, todo.md — am Code geprüft 2026-07-22
