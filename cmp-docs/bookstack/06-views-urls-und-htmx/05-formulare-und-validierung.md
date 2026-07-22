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

Zwei Stellen lesen Werte roh aus `request.POST`, ohne Form:

| Stelle | Wert | Grund |
|---|---|---|
| `OrderCreateView.post` (`orders/views.py:180,190`) | `action`, `target_step` | Wizard-Navigationssteuerung (welcher Button wurde gedrückt), keine Domänendaten |
| `ApprovalRejectView.post` (`approvals/views.py:43`) | `comment` | Freitext-Ablehnungsgrund, landet ungeprüft in `ApprovalService.reject()` |

Die ersten beiden sind reine Steuerwerte für die View-interne Zustandsmaschine des
Wizards, keine Werte, die validiert oder persistiert würden — vertretbar. `comment`
in `ApprovalRejectView` dagegen wird an den Service durchgereicht und landet in
der Datenbank, ganz ohne Längen- oder Inhaltsprüfung durch ein Form-Feld. Das ist
eine echte Abweichung von der Regel „Forms fuer Validierung", nicht nur eine
Steuergröße — in `todo.md` bisher nicht als eigenes Arbeitspaket erfasst.

## 6. Zusammenfassung

Formular-Felder für Bestellparameter entstehen zur Laufzeit aus
`ServiceTemplate.parameters` (Kapitel siehe Anhang A.2), unabhängig davon in
welcher der drei parameterbasierten Formen dieselbe Typ-zu-Feld-Logik dreimal
dupliziert im Modul steht. Validiert wird zweistufig — die Form an der
HTTP-Grenze, `TemplateValidator` über den Service an der Business-Grenze vor dem
Schreiben. Zwei Stellen greifen roh auf `request.POST` zu: die Wizard-Steuerwerte
sind unkritisch, der Ablehnungskommentar in `ApprovalRejectView` ist eine
unvalidierte Ausnahme von der Form-Pflicht.

> Quelle: cmp/apps/orders/forms.py, cmp/apps/catalog/forms.py, cmp/apps/orders/services.py, cmp/apps/catalog/services.py, cmp/core/domain/validators.py, cmp/apps/orders/views.py, cmp/apps/approvals/views.py, .claude/rules/django.md — am Code geprüft 2026-07-22
