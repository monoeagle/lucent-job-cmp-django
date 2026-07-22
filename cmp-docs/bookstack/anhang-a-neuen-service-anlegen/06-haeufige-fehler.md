# A.6 Häufige Fehler

Symptom, Ursache, Prüfbefehl. Alle Fälle stammen aus dem tatsächlichen Verhalten des Codes,
nicht aus Vermutungen.

## 1. Ziel des Kapitels

Wer A.3 oder A.4 abgearbeitet hat und ein unerwartetes Ergebnis sieht, findet hier zuerst
nach — die Ursache steht in den meisten Fällen darunter.

## 2. Das neue Feld erscheint nicht im Formular

**Häufigste Ursache: Die Vorlage in der Datenbank ist noch die alte.**
`CatalogService.seed_templates()` (`cmp/apps/catalog/services.py:411`) legt Vorlagen mit
`get_or_create(name=…)` an. Existiert der Name bereits, wird **nichts aktualisiert** —
ein erneuter Seed-Lauf ändert am Parametersatz nichts.

Prüfen:

```
venv/bin/python cmp/manage.py shell -c \
  "from apps.catalog.models import ServiceTemplate; \
   t=ServiceTemplate.objects.get(name='Linux VM'); \
   print([p['key'] for p in t.parameters])"
```

Steht der Schlüssel dort nicht, ist es die Datenbank und nicht der Code. Abhilfe: Vorlage im
Django-Admin bearbeiten oder die Entwicklungsdatenbank neu aufsetzen (siehe A.3, Abschnitt 5).

Zweite Ursache: Der Parameter wurde in `SEED_TEMPLATES` einer anderen Vorlage zugeordnet als
gedacht. Prüfen mit `grep -n '"key": "<dein_key>"' cmp/apps/catalog/services.py` und dem
umgebenden Vorlagenblock.

## 3. Die Vorbelegung greift nicht

**Ursache: `default_value` statt `default`.** Die Formularklassen lesen ausschließlich
`param["default"]` (`cmp/apps/orders/forms.py:61,113,226`); mehrere ausgelieferte Parameter
schreiben aber `default_value` (`cmp/apps/catalog/services.py:169,307,315`).

Betroffen sind im Auslieferungszustand `tshirt_size`, `backup_enabled` und `site_replication` —
ihre Vorgaben erscheinen nicht im Formular. Für eigene Parameter immer `default` verwenden.

## 4. Ein Auswahlwert fehlt in der Liste

**Ursache: `enabled: false`.** Das Formular übernimmt nur Optionen mit `enabled: true`
(`cmp/apps/orders/forms.py:24,118,231`), und der Validator lehnt gesperrte Werte ab
(`cmp/core/domain/validators.py:52-58`). Das ist gewollt: So bleiben Altwerte im Schema, ohne neu
bestellbar zu sein.

Prüfen: den Optionsblock in `cmp/apps/catalog/services.py` ansehen.

## 5. Ein unerwarteter Wizard-Schritt ist aufgetaucht

**Ursache: neuer `group`-Wert.** Der Wizard erzeugt je unterschiedlichem `group` einen Schritt
(`cmp/apps/orders/views.py:90`). Ein Tippfehler — „Netzwerk " mit Leerzeichen oder „netzwerk"
klein — erzeugt eine zweite Gruppe und damit einen zusätzlichen Schritt.

Prüfen:

```
grep -n '"group":' cmp/apps/catalog/services.py | sort -u -t: -k3
```

Nebenwirkung: Die Schrittbeschriftung entsteht aus `group` über `.title()`
(`cmp/apps/orders/views.py:118`) — aus „VM Sizing" wird angezeigt „Vm Sizing". Wer eine saubere
Beschriftung braucht, wählt einen Gruppennamen, der `.title()` überlebt.

## 6. Die Reihenfolge stimmt nicht

**Ursache: `display_order` fehlt oder kollidiert.** Ohne Angabe gilt 999
(`cmp/apps/orders/views.py:112`, `cmp/apps/orders/forms.py:221`), das Feld rutscht ans Ende.
Bei gleichem Wert entscheidet die Listenreihenfolge — vermeidbar durch eindeutige Zahlen mit
Lücken (10, 11, 12 …), wie im Bestand gehalten.

## 7. Eine Zahlenschranke wird nicht durchgesetzt

**Ursache: `min`/`max`/`pattern` werden nicht geprüft.** Der Validator wertet aus
`constraints` nur `options` aus (`cmp/core/domain/validators.py:15-73`). Die übrigen Schlüssel
sind beschreibend. Wer eine harte Grenze braucht, hinterlegt sie zusätzlich im Formularfeld.

## 8. Eine Kombination ist unsinnig, wird aber angenommen

**Ursache: Abhängigkeiten werden serverseitig nicht geprüft.** `depends_on` wird nirgends
ausgewertet, und die Einschränkungen in `metadata` wirken nur als Vorbelegung im Browser —
Einzelheiten in A.5.

## 9. Im Wizard fehlt die automatische Vorbelegung

**Kein Fehler, sondern der Ist-Stand.** Das Skript für die Vorbelegung steht nur in
`cmp/templates/orders/form_view.html`; die Wizard-Vorlagen unter `cmp/templates/orders/wizard/`
haben keines. Beim Prüfen einer neuen Option deshalb immer beide Wege ansehen.

## 10. Die Bestellung erscheint nicht in der Genehmigungs-Warteschlange

**Kein Fehler in deiner Option.** `ApprovalService.create_approval_requests`
(`cmp/apps/approvals/services.py:25`) wird im Anwendungscode nicht aufgerufen; die
Bestellkette bricht bereits beim Absenden ab. Erfasst als Arbeitspaket AP-13. Bis dahin lässt
sich der Genehmigungsweg nur über Tests oder Demodaten (`manage.py seed`) betrachten.

## 11. Tests brechen nach einem neuen Pflichtfeld

**Ursache: bestehende Tests bauen Bestellungen mit vollständigen Parametern.** Ein neues
`required: true` macht diese Datensätze unvollständig. Entweder das Feld optional halten oder
die betroffenen Tests und die Testdaten in `tests/factories.py` mitziehen.

Prüfen:

```
venv/bin/python -m pytest -q
```

## 12. Zusammenfassung

Die drei mit Abstand häufigsten Ursachen: die Datenbank wurde nicht aktualisiert
(Abschnitt 2), `default_value` statt `default` (Abschnitt 3) und ein versehentlich neuer
`group`-Wert (Abschnitt 5).

> Quelle: `cmp/apps/catalog/services.py:169,307,315,411`, `cmp/apps/orders/forms.py:24,61,113,118,221,226,231`, `cmp/apps/orders/views.py:90,112,118`, `cmp/core/domain/validators.py:15,52`, `cmp/apps/approvals/services.py:25` — am Code geprüft 2026-07-22
