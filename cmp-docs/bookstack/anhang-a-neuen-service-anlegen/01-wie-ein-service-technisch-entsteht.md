# A.1 Wie ein Service technisch entsteht

Diese Seite erklärt in einem Durchgang, was im CMP passiert, wenn ein Service im Katalog
erscheint und bestellt wird. Wer das verstanden hat, kann die Rezepte A.3 und A.4 abarbeiten,
ohne den Code vorher zu lesen.

## 1. Ziel des Kapitels

Der Anhang A ist ein Kochbuch. Er beantwortet zwei Fragen:

- Wie ergänze ich eine **neue Bestelloption** an einem bestehenden Service? (A.3)
- Wie lege ich einen **kompletten neuen Service** an? (A.4)

Diese Seite liefert das Modell dahinter. Sie ist die einzige Seite des Anhangs, die erklärt
statt anzuleiten.

## 2. Der Kerngedanke: ein Service ist Daten, kein Code

Im CMP ist ein Service **keine eigene Klasse und kein eigenes Modul**. Ein Service ist ein
Datensatz in der Tabelle `service_templates`, abgebildet durch das Modell `ServiceTemplate`
(`cmp/apps/catalog/models.py:14`). Seine Bestelloptionen stehen als JSON im Feld `parameters`:

```
ServiceTemplate
├── name          "Linux VM"
├── category      "compute"
├── description   "Linux Server VM mit ..."
├── is_active     True
└── parameters    [ {…}, {…}, {…} ]   ← die Bestelloptionen, als Liste von Objekten
```

Daraus folgt der wichtigste Satz dieses Anhangs:

**Eine neue Bestelloption ist ein neuer Eintrag in einer Liste — keine Migration, kein neues
Formularfeld, keine neue View.** Formular, Wizard-Schritte und Validierung entstehen zur
Laufzeit aus diesem JSON.

## 3. Der Weg vom Schema zum Formularfeld

```
apps/catalog/services.py          SHARED_PARAMS / SEED_TEMPLATES   (Schema-Definition)
        │
        │  CatalogService.seed_templates()
        ▼
service_templates.parameters      JSON in der Datenbank
        │
        │  View liest template.parameters
        ▼
apps/orders/forms.py              Formularfelder werden zur Laufzeit erzeugt
        │
        ▼
Browser                           Eingabemaske
        │
        │  POST
        ▼
core/domain/validators.py         TemplateValidator.validate_parameters()
        │
        ▼
order_items.parameters            die gewählten Werte, wieder als JSON
```

Kein Schritt dieser Kette kennt einzelne Parameternamen. Wer `cpu_cores` sucht, findet es
ausschließlich in der Schema-Definition — nirgends im Formular-, View- oder Validierungscode.

## 4. Die zwei Bestellwege

Für denselben Service gibt es zwei Oberflächen. Das ist beim Testen einer neuen Option
wichtig, weil sie sich unterschiedlich verhalten:

| Weg | URL-Name | View | Formularklasse |
|---|---|---|---|
| Einseitiges Formular | `orders:create_form` | `OrderFormView` (`cmp/apps/orders/views.py:292`) | `FullOrderForm` (`cmp/apps/orders/forms.py:182`) |
| Wizard (mehrstufig) | `orders:create` | `OrderCreateView` (`cmp/apps/orders/views.py:81`) | `ParameterGroupForm` je Schritt (`cmp/apps/orders/forms.py:102`) |

Beide sind über den Umschalter oben rechts im Bestellformular erreichbar
(`cmp/templates/orders/form_view.html:16-19`).

Ein dritter Fall: `OrderParameterForm` (`cmp/apps/orders/forms.py:6`) wird verwendet, wenn eine
Position zu einer **bestehenden** Bestellung hinzugefügt wird (`OrderAddItemView`,
`cmp/apps/orders/views.py:375`).

**Merke:** Es gibt drei Formularklassen, die dieselbe Aufgabe erfüllen. Wer das Verhalten von
Parametern ändert, muss alle drei prüfen — sie sind nicht voneinander abgeleitet.

## 5. Wie der Wizard seine Schritte findet

Der Wizard ist nicht konfiguriert, er rechnet. `OrderCreateView._get_steps()`
(`cmp/apps/orders/views.py:90`) baut die Schritte so:

1. Schritt 0 ist immer „Kontext" (Standort, Mandant, Sicherheitszone).
2. Danach wird je **unterschiedlichem Wert von `group`** ein Schritt erzeugt.
3. Die Reihenfolge der Schritte ergibt sich aus dem kleinsten `display_order` innerhalb der
   Gruppe.
4. Der letzte Schritt ist immer „Zusammenfassung".

Praktische Folge: **Ein Parameter mit einem neuen `group`-Wert erzeugt automatisch einen
neuen Wizard-Schritt.** Wer das nicht will, ordnet den Parameter einer bestehenden Gruppe zu.

## 6. Was danach mit den Werten passiert

Die eingegebenen Werte landen als JSON in `order_items.parameters` — pro Position der
Bestellung ein Objekt mit den gewählten Werten. Der Schlüssel `tofu_variable_name` im Schema
ist dafür gedacht, diese Werte später an die Infrastruktur-Automatisierung zu übergeben.

**Ist-Stand, geprüft am 2026-07-22:** `tofu_variable_name` wird im Schema durchgängig
gepflegt, aber im Anwendungscode noch nirgends ausgewertet. Die Weitergabe an die
Provisionierung ist offen (siehe Arbeitspaket AP-13). Für dieses Kochbuch heißt das: Der
Schlüssel wird mitgepflegt, damit er später vollständig vorliegt — eine Wirkung im laufenden
System hat er heute nicht.

## 7. Zusammenfassung

- Ein Service ist ein `ServiceTemplate`-Datensatz, seine Optionen sind eine JSON-Liste.
- Formular, Wizard-Schritte und Validierung entstehen zur Laufzeit aus diesem JSON.
- Es gibt drei Formularklassen und zwei Bestellwege — bei Änderungen alle prüfen.
- Neue Gruppe im Schema bedeutet neuer Wizard-Schritt.
- Weiter mit A.2 (Feldreferenz des Schemas), dann A.3 oder A.4.

> Quelle: `cmp/apps/catalog/models.py:14`, `cmp/apps/catalog/services.py:15`, `cmp/apps/orders/forms.py:6,102,182`, `cmp/apps/orders/views.py:81,90,292,375`, `cmp/core/domain/validators.py:11` — am Code geprüft 2026-07-22
