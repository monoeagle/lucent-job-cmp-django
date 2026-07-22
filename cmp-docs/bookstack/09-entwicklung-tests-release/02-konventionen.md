# Konventionen

Python-, Django- und HTMX-Konventionen, die für neuen Code im Projekt
gelten — mit je einem echten Codebeispiel und, wo die Praxis abweicht,
mit dem tatsächlichen Ist-Stand daneben.

## 1. Ziel des Kapitels

Wer neuen Code beiträgt, soll wissen, welche Form erwartet wird — und wo
das Repository selbst noch nicht überall der eigenen Regel folgt.

## 2. Python-Stil

- `snake_case` für Variablen, Funktionen, Module, URL-Namen
- Zeilenlänge: dokumentiertes Ziel 100 Zeichen
- Imports: Standard → Third-Party → Local, je alphabetisch
- Linter: `ruff`
- Dateigröße: Richtwert < 200 Zeilen

**Ist-Stand zur Zeilenlänge:** Es liegt weder ein `ruff.toml` noch ein
`pyproject.toml` mit `line-length` im Repository (geprüft: beide fehlen).
`ruff` läuft damit mit seinem Default von 88 Zeichen, nicht mit den
dokumentierten 100. Ein Lauf gegen `cmp/` am 2026-07-22
(`ruff check cmp/ --select E501`) liefert **128** Treffer. Das Ziel „100
Zeichen" ist damit nicht durch Konfiguration erzwungen.

## 3. Views bleiben dünn — plus HTMX-Partial

`TemplateListView` liefert für HTMX-Requests ein Fragment statt der
ganzen Seite. Beleg in `cmp/apps/catalog/views.py:13-33`:

```python
class TemplateListView(RequesterRequiredMixin, ListView):
    model = ServiceTemplate
    template_name = "catalog/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        category = self.request.GET.get("category")
        query = self.request.GET.get("q")
        if query:
            return CatalogService.search_templates(query)
        return CatalogService.list_active_templates(category=category or None)

    def get_template_names(self):
        if self.request.htmx:
            return ["catalog/partials/template_grid.html"]
        return [self.template_name]
```

Die View entscheidet nur, *welches* Template gerendert wird — die Suche
selbst steckt in `CatalogService`. Weitere Beispiele für dünne Views:
Kapitel 2.2 (`OrderSubmitView`), Anhang A.

## 4. Forms validieren, ohne Geschäftslogik

`TemplateFilterForm` bildet die Katalog-Filterfelder ab, sonst nichts.
Beleg in `cmp/apps/catalog/forms.py:7-13`:

```python
class TemplateFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Suche")
    category = forms.ChoiceField(
        required=False,
        choices=[("", "Alle Kategorien")] + TemplateCategory.choices,
        label="Kategorie",
    )
```

Die Wahl, was mit `q` und `category` geschieht (Suche vs. Filter), trifft
die View über `CatalogService`, nicht das Form.

## 5. Services tragen die Logik, sind statisch

`CatalogService.get_template` kennt keinen Request, wirft bei Bedarf eine
Custom Exception. Beleg in `cmp/apps/catalog/services.py:394-402`:

```python
@staticmethod
def get_template(template_id):
    """Get a template by ID or raise NotFoundError."""
    try:
        return ServiceTemplate.objects.get(pk=template_id)
    except ServiceTemplate.DoesNotExist:
        raise NotFoundError(
            f"ServiceTemplate with id={template_id} not found."
        )
```

## 6. Models: nur Felder und Meta

Beleg in `cmp/apps/catalog/models.py:14-27` (`ServiceTemplate`):

```python
class ServiceTemplate(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=30)
    description = models.TextField(blank=True, default="")
    parameters = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "service_templates"
        ordering = ["name"]
```

## 7. Fehlerbehandlung über eine feste Exception-Hierarchie

Alle Service-Fehler erben von `ServiceError`. Beleg in
`cmp/core/exceptions.py:1-25`:

```python
class ServiceError(Exception):
    """Base exception for service-layer errors."""
    def __init__(self, message: str, details: list | None = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class ValidationError(ServiceError): ...
class NotFoundError(ServiceError): ...
class ConflictError(ServiceError): ...
class ForbiddenError(ServiceError): ...
```

Views fangen diese Typen und übersetzen sie in `messages.error(...)` —
siehe Kapitel 2.2.

## 8. django-environ statt hartkodierter Secrets

`config/settings/production.py:18-29` deklariert Typ und Default je
Umgebungsvariable, bevor sie gelesen wird:

```python
env = environ.Env(
    DEBUG=(bool, False),
    SECURE_SSL_REDIRECT=(bool, True),
    SECURE_HSTS_SECONDS=(int, 31536000),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
)
...
SECRET_KEY = env("SECRET_KEY")  # ohne Default -> Fehlstart, wenn nicht gesetzt
```

`DEBUG=True` in Produktion ist projektweit als fatal eingestuft (siehe
`CLAUDE.md`) — deshalb hat `DEBUG` hier einen sicheren Default, `SECRET_KEY`
bewusst keinen.

## 9. Keine Inline-Styles — Ist-Stand

Regel (`.claude/rules/htmx.md`): Tailwind-Klassen statt `style="..."`.
Nachgezählt am 2026-07-22 (`grep -rc 'style="' cmp --include="*.html"`):
**6 Templates**, zusammen **75 Zeilen** mit Inline-`style`, darunter
`dashboard/dashboard.html`, `admin_panel/dashboard.html` und
`approvals/approval_queue.html` — überwiegend Layout-Grids und
Statuswerte, die nicht über DaisyUI-Klassen abgebildet wurden. Die Regel
gilt für neuen Code; bestehende Treffer sind nicht rückwirkend bereinigt.

## 10. Git-Commit-Konvention

Format `type(scope): Beschreibung`. Reale Verteilung über 159 Commits auf
`main` (`git log --oneline`, Stand 2026-07-22):

| Typ | Anzahl |
|---|---|
| `feat` | 62 |
| `docs` | 50 |
| `fix` | 21 |
| `chore` | 12 |
| `release` | 4 |
| `refactor` | 4 |

`chore` und `release` werden in der Praxis zusätzlich zu den in
`cmp-docs/docs/entwicklung/conventions.md` genannten Typen (`feat`, `fix`,
`docs`, `refactor`, `test`) verwendet — die Doku ist an dieser Stelle
unvollständig, nicht falsch.

## 11. Zusammenfassung

Die Kernregeln — dünne Views, validierende Forms, Services mit
Geschäftslogik, datenreine Models, `django-environ` statt Secrets im
Code — werden im aktuellen Code eingehalten. Zwei Abweichungen sind
real belegt und sollten beim Weiterbauen nicht überrascht: `ruff` erzwingt
100 Zeichen nicht (kein Config-File, Default 88), und sechs Templates
enthalten noch Inline-Styles.

> Quelle: `cmp/apps/catalog/views.py:13-33`, `cmp/apps/catalog/forms.py:7-13`, `cmp/apps/catalog/services.py:394-402`, `cmp/apps/catalog/models.py:14-27`, `cmp/core/exceptions.py:1-25`, `cmp/config/settings/production.py:18-29`, `.claude/rules/django.md`, `.claude/rules/htmx.md`, `cmp-docs/docs/entwicklung/conventions.md`, `git log --oneline` (main) — am Code geprüft 2026-07-22
