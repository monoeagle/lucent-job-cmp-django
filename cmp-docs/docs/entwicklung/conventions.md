# Conventions

## Python-Stil

- **Namensgebung:** `snake_case` für alles (Variablen, Funktionen, Module, URLs)
- **Zeilenlänge:** max. 100 Zeichen
- **Imports:** Standard → Third-Party → Local, jeweils alphabetisch
- **Linter:** ruff
- **Dateigröße:** < 200 Zeilen pro Datei

## Django-Patterns

### Views (dünn)

```python
# Gut: View delegiert an Service
class OrderCreateView(RequesterRequiredMixin, FormView):
    def form_valid(self, form):
        order = OrderService.create_order(user=self.request.user)
        return redirect("orders:detail", pk=order.pk)

# Schlecht: Business-Logik im View
class OrderCreateView(RequesterRequiredMixin, FormView):
    def form_valid(self, form):
        order = Order.objects.create(user=self.request.user)
        if order.items.count() > 5:
            order.needs_approval = True
        order.save()
```

### Services (Business-Logik)

```python
# Services sind statisch, kein Request-Objekt
class OrderService:
    @staticmethod
    def submit_order(order_id: int) -> Order:
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError("Cannot submit")
        ...
```

### Forms (Validierung)

```python
# Forms validieren Input, keine Business-Logik
class OrderParameterForm(forms.Form):
    def __init__(self, *args, template_parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Felder aus Template-Schema
```

### Models (Daten)

```python
# Models: Nur Felder und Meta, keine Business-Logik
class Order(TimeStampedModel):
    user = models.ForeignKey(...)
    status = models.CharField(...)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"
```

## Template-Patterns

### HTMX-Partials

Views liefern Partials für HTMX-Requests:

```python
def get_template_names(self):
    if self.request.htmx:
        return ["catalog/partials/template_grid.html"]
    return ["catalog/template_list.html"]
```

### DaisyUI-Komponenten

| Element | DaisyUI-Klasse |
|---------|----------------|
| Layout | `drawer`, `navbar` |
| Cards | `card`, `card-body` |
| Tabellen | `table`, `table-zebra` |
| Buttons | `btn`, `btn-primary`, `btn-sm` |
| Badges | `badge`, `badge-primary` |
| Formulare | `form-control`, `input`, `select` |
| Alerts | `alert`, `alert-success` |

## Git-Conventions

### Commit-Messages

Format: `type(scope): description`

```
feat(B2): add CatalogService with list, search, validate
fix: restore conftest keepdb and flush stale test data
docs: add Phase B3 order lifecycle implementation plan
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`
**Scopes:** `B0`–`B9` (Phasen), App-Namen

## Fehlerbehandlung

Services werfen Custom Exceptions:

```python
from core.exceptions import ValidationError, NotFoundError, ConflictError

# Im Service:
raise ValidationError("Parameter validation failed.", details=[...])

# Im View:
try:
    OrderService.submit_order(order_id=pk)
except (ValidationError, ConflictError) as e:
    messages.error(request, e.message)
```
