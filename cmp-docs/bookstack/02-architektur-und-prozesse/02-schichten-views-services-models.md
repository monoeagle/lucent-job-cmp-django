# Schichten: Views, Services, Models

CMP folgt einer festen Aufrufkette `views.py → services.py → models.py` mit
`forms.py` für Validierung. Dieses Kapitel zeigt jede Schicht an einem echten
Codebeispiel und nennt die Abhängigkeitsregeln, die die Trennung erzwingen.

## 1. Ziel des Kapitels

Wer eine neue Funktion baut, soll wissen: Wohin gehört welche Logik, und welche
Importrichtung ist verboten. Jede Regel unten ist an einem konkreten Beispiel aus
`cmp/apps/orders/` belegt.

## 2. Regel: Views bleiben dünn

Eine View prüft Berechtigung, liest Request-Daten, ruft **einen** Service auf und
rendert oder leitet weiter. Sie enthält keine Statuslogik. Beleg in
`cmp/apps/orders/views.py:433-439` (`OrderSubmitView.post`):

```python
class OrderSubmitView(RequesterRequiredMixin, View):
    """Submit a draft order for processing."""

    def post(self, request, pk):
        try:
            OrderService.submit_order(order_id=pk)
            messages.success(request, "Bestellung eingereicht.")
        except (ValidationError, ConflictError) as e:
            messages.error(request, e.message)
        return redirect("orders:detail", pk=pk)
```

Die View kennt weder den Order-Status noch die Übergangsregeln — sie ruft
`OrderService.submit_order` auf und übersetzt dessen Ergebnis (Erfolg oder
Exception) in eine Nutzermeldung. `RequesterRequiredMixin`
(`cmp/core/mixins.py:63-69`) übernimmt die Rollenprüfung, bevor `post()` überhaupt
läuft.

## 3. Regel: Forms validieren Eingaben

`OrderParameterForm` baut sein Feld-Set zur Laufzeit aus dem Parameter-Schema eines
`ServiceTemplate` auf — Validierung, keine Geschäftslogik. Beleg in
`cmp/apps/orders/forms.py:6-19`:

```python
class OrderParameterForm(forms.Form):
    """Dynamic form built from template parameters at runtime.

    Used by OrderAddItemView for adding items to existing orders.
    """

    def __init__(self, *args, template_parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        if template_parameters:
            for param in template_parameters:
                key = param["key"]
                label = param.get("label", key)
                required = param.get("required", False)
                param_type = param.get("type", "string")
                ...
```

Die View reicht `template_parameters` durch, das Form entscheidet anhand des
Parameter-Typs (`choice`, `enum`, …), welches Django-Feld mit welchen
Validierungsregeln entsteht. Business-Entscheidungen — etwa ob eine Bestellung
überhaupt eingereicht werden darf — stehen hier nicht; die trifft der Service.

## 4. Regel: Services tragen die Business-Logik

Services sind statische Methoden ohne Request-Objekt. Sie kennen Statusmaschine,
Geschäftsregeln und die Reihenfolge der Schritte. Beleg in
`cmp/apps/orders/services.py:61-76` (`OrderService.submit_order`):

```python
@staticmethod
def submit_order(order_id):
    """Submit a draft order (draft -> validated -> submitted)."""
    order = OrderService.get_order(order_id)
    if order.status != OrderStatus.DRAFT:
        raise ConflictError(
            f"Cannot submit order in status '{order.status}'."
        )
    if order.items.count() == 0:
        raise ValidationError("Cannot submit an order without items.")
    StatusMachine.validate_transition(order.status, OrderStatus.VALIDATED)
    order.status = OrderStatus.VALIDATED
    order.save()
    StatusMachine.validate_transition(order.status, OrderStatus.SUBMITTED)
    order.status = OrderStatus.SUBMITTED
    order.save()
    return order
```

Der Service prüft Vorbedingungen, nutzt `StatusMachine.validate_transition`
(`cmp/core/domain/value_objects.py`) und schreibt erst dann auf das Model. Ein
Service darf andere Services aufrufen (z. B. ruft `ApprovalService` in
`cmp/apps/approvals/services.py:5` `OrderService` auf) und auf `core/domain/`
zugreifen, aber nicht auf eine andere View.

## 5. Regel: Models enthalten nur Felder und Meta

Models sind reine Datenstrukturen — kein Statuswechsel, keine Validierungslogik.
Beleg in `cmp/apps/orders/models.py:9-29` (`Order`):

```python
class Order(TimeStampedModel):
    """A service order placed by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"
```

`status` ist ein einfaches `CharField` mit `choices` aus `OrderStatus`
(`cmp/core/domain/value_objects.py`) — die Übergangsregeln selbst (welcher Status
auf welchen folgen darf) liegen nicht im Model, sondern in `StatusMachine`, die vom
Service aufgerufen wird.

## 6. Dependency-Regeln im Überblick

| Von | Nach | Erlaubt |
|---|---|---|
| `views.py` | `services.py` | ja |
| `views.py` | `forms.py` | ja |
| `views.py` | `models.py` (lesend) | ja |
| `views.py` | `models.py` (schreibend) | nein |
| `services.py` | `models.py` | ja |
| `services.py` | `core/domain/` | ja |
| `services.py` | andere Services | ja |
| `core/` | `apps/` | nein (Zielregel) |
| `core/domain/` | Django | nein (nur `TextChoices`) |

Die Regel „`core/` → `apps/` nein" ist die dokumentierte Zielregel
(`cmp-docs/docs/grundlagen/architektur.md`), **aber am Code nicht durchgehend
eingehalten**: `cmp/core/context_processors.py:2-3` importiert
`apps.notifications.services.NotificationService` und
`apps.approvals.models.ApprovalRequest` direkt, `badge_counts()` importiert
zusätzlich `apps.orders.models.Order` innerhalb der Funktion
(`cmp/core/context_processors.py:12`, Kommentar dort: „Import here to avoid
circular imports"). Der Context-Processor braucht domänenübergreifende Badge-Zahlen
(ungelesene Benachrichtigungen, offene Genehmigungen, offene Bestellungen) für jede
Seite und bricht die Regel dafür bewusst. `core/domain/` selbst (Enums, Value
Objects, Validators) bleibt frei von `apps`-Importen — die Ausnahme betrifft nur
`core/context_processors.py`, nicht `core/domain/`.

## 7. Zusammenfassung

Jede der vier Schichten hat eine feste Aufgabe: Views delegieren, Forms validieren
Eingaben, Services tragen die Business-Logik inklusive Statuswechsel, Models sind
reine Datenstrukturen. Die Dependency-Tabelle ist überwiegend eingehalten — mit
einer dokumentierten Ausnahme: `core/context_processors.py` importiert aus drei
`apps`-Paketen, weil projektweite Badge-Zahlen keinen anderen Anknüpfungspunkt
haben. Das ist beim Weiterbauen zu beachten, nicht als Vorbild für neue
`core/`-Module zu kopieren.

> Quelle: cmp-docs/docs/entwicklung/conventions.md, cmp/apps/orders/views.py, cmp/apps/orders/forms.py, cmp/apps/orders/services.py, cmp/apps/orders/models.py, cmp/core/mixins.py, cmp/core/context_processors.py — am Code geprüft 2026-07-22
