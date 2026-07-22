# Formulare und Validierung

Wie CMP Django-Forms statt rohem `request.POST` einsetzt, wo dynamische
Formularfelder aus dem Parameter-Schema entstehen, und wo die Validierung in zwei
Schichten läuft.

## 1. Ziel des Kapitels

`.claude/rules/django.md` (Zeile 2) verlangt „Forms fuer Validierung, nicht rohe
request.POST". Diese Seite zeigt, welche Formklassen es gibt, wie sie sich zur
Laufzeit aus `ServiceTemplate.parameters` aufbauen, wie die Validierung danach
noch einmal im Service erfolgt — und zwei konkrete Stellen, an denen die Regel
nicht eingehalten wird.

## 2. Die fünf Form-Klassen in `apps/orders/forms.py`

| Form | Zweck | Felder |
|---|---|---|
| `OrderParameterForm` (`forms.py:6-62`) | Position zu bestehender Draft-Order hinzufügen | dynamisch aus `template_parameters` |
| `ContextForm` (`forms.py:65-99`) | Wizard-Schritt „Kontext" | `location`, `tenant`, `security_zone` — Auswahllisten aus `CmdbStubClient` |
| `ParameterGroupForm` (`forms.py:102-161`) | ein Wizard-Schritt je Parametergruppe | dynamisch, nur die Parameter der aktuellen Gruppe |
| `QuantityForm` (`forms.py:164-179`) | Wizard-Schritt „Zusammenfassung" | `quantity` (1-50) |
| `FullOrderForm` (`forms.py:182-264`) | Einzelseiten-Formular, alle Felder auf einmal | Kontext + alle Parameter + `quantity` |

Dazu `TemplateFilterForm` (`apps/catalog/forms.py:7-13`) für die Katalog-Suche —
`q` und `category`, beide `required=False`.

## 3. Dynamische Felder aus dem Parameter-Schema

Alle vier parameterbasierten Forms (`OrderParameterForm`, `ParameterGroupForm`,
`FullOrderForm`, und implizit die Wizard-Steps) bauen ihre Felder im `__init__`
aus derselben Fallunterscheidung nach `param["type"]` auf:

```python
if param_type in ("choice", "enum"):
    ...
    self.fields[key] = forms.ChoiceField(...)
elif param_type == "boolean":
    self.fields[key] = forms.BooleanField(...)
elif param_type in ("integer", "float"):
    self.fields[key] = field_cls(...)
else:  # string
    self.fields[key] = forms.CharField(...)
```

(sinngemäß aus `OrderParameterForm.__init__`, `forms.py:21-59`, und praktisch
identisch in `ParameterGroupForm.__init__`, `forms.py:115-158`, sowie
`FullOrderForm.__init__`, `forms.py:228-255`) — dieselbe Typ-zu-Feld-Zuordnung
steht damit **dreimal** im Modul. Das Schema selbst — Schlüssel, Typen,
`constraints` — ist in
[Anhang A.2](../anhang-a-neuen-service-anlegen/02-das-parameter-schema.md)
vollständig dokumentiert; diese Seite beschreibt nur, wie daraus ein Formularfeld
entsteht.

## 4. Zwei Validierungsschichten: Form und Service

Ein Parameterwert wird **zweimal** geprüft, an zwei unterschiedlichen Stellen mit
unterschiedlichem Zweck:

1. **Django-Form (HTTP-Grenze):** `field.clean()` prüft Typ und Pflichtfeld anhand
   des zur Laufzeit gebauten Feldes (Abschnitt 3) — das ist, was der Nutzer als
   Fehlermeldung neben dem Feld sieht.
2. **`TemplateValidator` (Business-Grenze):** `OrderService.add_item`
   (`apps/orders/services.py:29-42`) ruft vor dem Schreiben zusätzlich
   `CatalogService.validate_template_parameters()`
   (`apps/catalog/services.py:403-408`) auf, die an
   `TemplateValidator.validate_parameters()`
   (`core/domain/validators.py:11-70`) delegiert — eine reine, Django-freie
   Prüfung von `schema` gegen `values`, die bei Fehlern eine Liste von
   `{key, message}`-Dicts zurückgibt. Der Service wandelt eine nicht-leere Liste
   in eine `ValidationError` (`core/exceptions.py`) um:

```python
errors = CatalogService.validate_template_parameters(template_id, parameters)
if errors:
    raise ValidationError("Parameter validation failed.", details=errors)
```

(`apps/orders/services.py:36-41`) Die Form schützt die Eingabemaske, der Service
schützt den Schreibpfad unabhängig davon, über welchen Weg die Daten kommen
(Wizard, Einzelseiten-Formular, oder ein künftiger dritter Weg). Fällt eine der
beiden Schichten weg, bleibt die andere als Netz bestehen.

## 5. Wo direkt auf `request.POST` zugegriffen wird

Eine Stelle liest Werte weiterhin roh aus `request.POST`, ohne Form:

| Stelle | Wert | Grund |
|---|---|---|
| `OrderCreateView.post` (`orders/views.py:180,190`) | `action`, `target_step` | Wizard-Navigationssteuerung (welcher Button wurde gedrückt), keine Domänendaten |

Das ist eine reine Steuergröße für die View-interne Zustandsmaschine des Wizards,
kein Wert, der validiert oder persistiert würde — vertretbar.

Bis AP-22 griff auch `ApprovalRejectView.post` roh auf `request.POST.get("comment", "")`
zu, und der Wert landete ungeprüft in `ApprovalService.reject()` — eine echte
Abweichung von der Regel „Forms fuer Validierung", weil er anders als die
Wizard-Steuerwerte tatsächlich persistiert wird. Seit AP-22 validiert
`RejectionForm` (`apps/approvals/forms.py:10-22`) den Kommentar, bevor er den
Service erreicht:

```python
class RejectionForm(forms.Form):
    comment = forms.CharField(
        max_length=COMMENT_MAX_LENGTH,  # 2000
        required=False,
        strip=True,
        widget=forms.Textarea,
        label="Begruendung",
    )
```

`ApprovalRejectView.post` (`approvals/views.py:44-49`) instanziiert das Form aus
`request.POST`, verwirft ungültige Eingaben mit einer Django-Message statt sie
weiterzureichen, und liest den Kommentar erst danach aus `cleaned_data`:

```python
form = RejectionForm(request.POST)
if not form.is_valid():
    messages.error(request, "Begruendung ungueltig — Ablehnung verworfen.")
    return redirect("approvals:queue")
comment = form.cleaned_data["comment"]
```

Die Grenze von 2000 Zeichen sitzt bewusst im Form, nicht im Modell — `comment`
ist ein `TextField` ohne eigene Längenbegrenzung (Kapitel 3.4); ein Form kann eine
Grenze melden, ein reines `TextField` nicht.

## 6. Zusammenfassung

Formular-Felder für Bestellparameter entstehen zur Laufzeit aus
`ServiceTemplate.parameters` (Kapitel siehe Anhang A.2), unabhängig davon in
welcher der drei parameterbasierten Formen dieselbe Typ-zu-Feld-Logik dreimal
dupliziert im Modul steht. Validiert wird zweistufig — die Form an der
HTTP-Grenze, `TemplateValidator` über den Service an der Business-Grenze vor dem
Schreiben. Eine Stelle greift weiterhin roh auf `request.POST` zu — die
unkritischen Wizard-Steuerwerte in `OrderCreateView`. Der frühere Ablehnungskommentar
in `ApprovalRejectView` war bis AP-22 dieselbe Art Ausnahme, ist aber seit AP-22
über `RejectionForm` validiert.

> Quelle: cmp/apps/orders/forms.py, cmp/apps/catalog/forms.py, cmp/apps/approvals/forms.py, cmp/apps/orders/services.py, cmp/apps/catalog/services.py, cmp/core/domain/validators.py, cmp/apps/orders/views.py, cmp/apps/approvals/views.py, .claude/rules/django.md — am Code geprüft 2026-07-22
