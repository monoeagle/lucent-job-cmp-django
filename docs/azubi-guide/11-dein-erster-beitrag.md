# 10 — Dein erster Beitrag

> **In diesem Kapitel:** Theorie beiseite — du schreibst jetzt echten Code. Wir
> begleiten dich Schritt für Schritt durch einen kleinen, kompletten Beitrag:
> von der leeren Idee bis zum fertigen Commit. Als Beispiel nehmen wir eine
> kleine, **erfundene** Erweiterung des Benachrichtigungs-Systems — klein genug,
> um sie in einer Sitzung durchzuziehen, aber echt genug, um die tatsächlichen
> Muster des Projekts zu zeigen.
>
> **Das lernst du:**
> - Wie du eine kleine Aufgabe in einen TDD-Zyklus (ROT → GRÜN → REFACTOR) verpackst
> - Wie eine Test-Factory mit `factory_boy` benutzt wird
> - Wie eine neue Service-Methode ins Projekt passt, ohne die View aufzublähen
> - Wie du vor dem Commit selbst prüfst, ob du die Konventionen eingehalten hast
>
> **Voraussetzung:** [10 — So arbeiten wir](10-so-arbeiten-wir.md) (TDD-Pflicht,
> Test-Layout, Code-Regeln — hier wenden wir das an).

---

## Die Aufgabe: Benachrichtigungen nach Kategorie filtern

Das `notifications`-App kennt bereits Kategorien (`info`, `warning`, …) auf
jeder `Notification` — aber es gibt noch keine Möglichkeit, gezielt „nur die
Benachrichtigungen einer bestimmten Kategorie" abzufragen. Genau das bauen wir
jetzt: eine neue Methode `NotificationService.list_by_category()`.

💡 **Merke:** Das ist bewusst eine **kleine** Aufgabe. Dein erster echter
Beitrag muss kein großes Feature sein — im Gegenteil, klein und sauber ist der
bessere Einstieg.

Bevor du eine Zeile Code schreibst: **Rot, bevor du Grün siehst.** Das ist keine
Empfehlung, sondern Pflicht (siehe [10 — So arbeiten wir](10-so-arbeiten-wir.md)).

---

## Schritt 1 — ROT: Der Failing-Test

Wir öffnen die vorhandene Testdatei für den `NotificationService` —
`tests/unit/test_notification_service.py` — und fügen der bestehenden
Testklasse eine neue Testmethode hinzu. Die Datei nutzt schon das Muster, das
wir übernehmen: eine `UserFactory` aus `tests/factories.py` und direkte Aufrufe
der Service-Methoden.

```python
# tests/unit/test_notification_service.py
class TestNotificationService:
    # ... bestehende Tests bleiben unverändert ...

    def test_list_by_category(self):
        user = UserFactory()
        NotificationService.create(
            user=user, title="Wartung", message="m", category="warning"
        )
        NotificationService.create(
            user=user, title="Info", message="m", category="info"
        )

        result = NotificationService.list_by_category(user.pk, "warning")

        assert len(result) == 1
        assert result[0].category == "warning"
```

Jetzt der Testlauf — aus dem Repo-Root, nicht aus `cmp/`:

```bash
python -m pytest tests/unit/test_notification_service.py -k list_by_category
```

Das Ergebnis ist **rot**:

```text
AttributeError: type object 'NotificationService' has no attribute 'list_by_category'
```

🔍 **Genau das wollen wir hier.** Ein roter Test ist der Beweis, dass der Test
wirklich etwas prüft — und noch keine zufällig grüne Attrappe ist.

⚠️ **Achtung:** Schreib niemals erst die Implementierung und danach einen Test,
der „zufällig" grün ist. Ohne den roten Zwischenschritt weißt du nie, ob dein
Test überhaupt fehlschlagen *kann*.

---

## Schritt 2 — GRÜN: Minimale Implementierung

Jetzt — und erst jetzt — machen wir den Test grün. Die neue Methode kommt in
`cmp/apps/notifications/services.py`, direkt neben die anderen statischen
Service-Methoden. Sie folgt exakt demselben Muster wie `list_unread()` und
`list_all()`, die schon da sind:

```python
# cmp/apps/notifications/services.py
class NotificationService:
    # ... bestehende Methoden bleiben unverändert ...

    @staticmethod
    def list_by_category(user_id, category):
        return list(
            Notification.objects.filter(user_id=user_id, category=category)
        )
```

Kein Umweg über die View, kein zusätzliches Model — nur eine schlanke
Filter-Query, genau wie ihre Nachbarn in derselben Klasse.

```bash
python -m pytest tests/unit/test_notification_service.py -k list_by_category
```

```text
1 passed
```

💡 **Merke:** „Minimal" heißt hier wörtlich minimal. Keine Sortierung, kein
Caching, keine Extras einbauen, die niemand verlangt hat — das kommt erst,
wenn ein Test es einfordert.

---

## Schritt 3 — REFACTOR

Jetzt, wo der Test grün ist, schaust du noch einmal drüber: Ist der Name klar?
Passt der Code-Stil zu den Nachbarmethoden? Hier gibt es nichts zu refactorn —
die Methode ist schon so knapp wie möglich. Das ist ein völlig normales
Ergebnis bei einer kleinen Aufgabe wie dieser.

Trotzdem läuft der Linter über die geänderte Datei, bevor irgendetwas committet
wird:

```bash
ruff check cmp/apps/notifications/services.py
```

```text
All checks passed!
```

Und zur Sicherheit noch einmal die **komplette** Testdatei, nicht nur der eine
Test — schließlich soll nichts anderes kaputtgegangen sein:

```bash
python -m pytest tests/unit/test_notification_service.py
```

```text
6 passed
```

---

## Schritt 4 — Selbst prüfen

Bevor du committest, geh die Checkliste aus [Kapitel 10](10-so-arbeiten-wir.md)
im Kopf durch:

- [ ] Test zuerst geschrieben, tatsächlich rot gesehen?
- [ ] Implementierung minimal, keine Logik in der View gelandet?
- [ ] `ruff check` sauber?
- [ ] Migration nötig? — Hier **nein**: `category` existiert als Feld schon
      lange, wir haben kein Model geändert. Hättest du ein neues Feld
      hinzugefügt, wäre jetzt der Moment für
      `python manage.py makemigrations notifications` gewesen.
- [ ] Ganze Testdatei (nicht nur dein neuer Test) noch grün?

⚠️ **Achtung:** Migration und Model-Änderung gehören **immer** in denselben
Commit wie der Code, der sie braucht. Eine Migration „nachzureichen" führt
schnell zu einer Datenbank, die nicht zum Code passt.

---

## Schritt 5 — Commit

Ein Commit, eine klare, kurze Message im Stil des Projekts (Conventional-
Commits-artig, siehe `git log` für weitere Beispiele):

```bash
git add cmp/apps/notifications/services.py tests/unit/test_notification_service.py
git commit -m "feat(notifications): Benachrichtigungen nach Kategorie filtern"
```

💡 **Merke:** Test und Implementierung gehören in **einen** Commit. Ein
Reviewer soll sehen können, dass der Test schon da war, als der Code kam —
nicht getrennt in „Test folgt später".

🔍 Details zu Commit-Konventionen, Branch-Namen und Review-Ablauf findest du in
[Kapitel 10](10-so-arbeiten-wir.md) — dieses Kapitel zeigt nur den Ablauf
*innerhalb* eines Beitrags.

---

## Vertiefung für Entwickler

<details>
<summary><b>Wo dein Code hingehört — eine Entscheidungshilfe</b></summary>

Bei jedem neuen Stück Code lohnt sich vorher die Frage: *Wo gehört das hin?*
Im CMP ist die Antwort fast immer eindeutig, wenn du dich an diese Reihenfolge
hältst:

1. **Ist es Fachlogik** — irgendeine Regel, Berechnung oder Abfrage, die man
   auch ohne HTTP-Request erklären könnte (wie unser `list_by_category` oben)?
   → Gehört in `services.py`. Genau wie in diesem Kapitel: statische Methode,
   keine Abhängigkeit vom Request-Objekt.

2. **Ist es Validierung von Nutzereingaben** — Pflichtfelder, Formate,
   Bereichsprüfungen aus einem Formular? → Gehört in `forms.py`, **nicht** als
   `if`-Kaskade in die View und **nicht** als Extra-Check im Service. Django
   Forms sind dafür gebaut.

3. **Ändert es den Status einer `Order`?** → Läuft **ausschließlich** über
   `transition()` in `cmp/apps/orders/transitions.py` — siehe
   [Kapitel 05](05-bestell-lebenszyklus.md). Kein `order.status = ...` an
   irgendeiner anderen Stelle im Code, egal wie klein die Änderung erscheint.

4. **Bleibt danach noch etwas übrig, das in die View soll?** Dann fast immer
   nur: Request entgegennehmen, den passenden Service aufrufen, Ergebnis an
   Template oder Redirect weiterreichen. Die View selbst trifft **keine**
   fachlichen Entscheidungen — siehe [Kapitel 06](06-architektur.md) zur
   Thin-Views-Regel.

Die Reihenfolge oben ist kein Zufall: Sie ist genau die Prüf-Reihenfolge, mit
der du bei jedem neuen Code-Stück in Sekunden entscheidest, in welche Datei es
gehört — ohne lange nachzudenken oder Kollegen fragen zu müssen.

</details>

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Das Vorbild-Muster für statische Service-Methoden | `cmp/apps/notifications/services.py` |
| Die Test-Factories (`UserFactory` & Co.) | `tests/factories.py` |
| Geteilte Test-Fixtures (Datenbank-Setup) | `tests/conftest.py` |
| Bestehende Unit-Tests im selben Stil | `tests/unit/test_notification_service.py` |
| Wie eine schlanke View einen Service aufruft | `cmp/apps/notifications/views.py` |

Öffne `views.py` und vergleiche: Keine einzige View ruft direkt auf
`Notification.objects...` zu — immer geht der Umweg über den Service. Genau
dieses Muster hast du in diesem Kapitel selbst angewendet.

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Warum schreibst du zuerst den Test — und erst danach den Code, der ihn grün
   macht?
2. Du willst eine neue Fachregel einbauen, die keine Nutzereingabe validiert
   und keinen Order-Status ändert. In welche Datei kommt sie?
3. Mit welchem Befehl lässt du **nur** deinen neuen Test laufen, statt die
   ganze Suite?

<details>
<summary>Antworten anzeigen</summary>

1. Nur ein Test, der zuerst **rot** war, beweist, dass er wirklich etwas
   prüft. Ein Test, der von Anfang an grün ist, könnte auch einfach nichts
   testen.
2. In den passenden `services.py` der zuständigen App — als statische Methode,
   analog zu den bestehenden Methoden dort.
3. `python -m pytest <pfad-zur-datei> -k <testname>`, z. B.
   `python -m pytest tests/unit/test_notification_service.py -k list_by_category`.

</details>

---

⟵ [10 — So arbeiten wir](10-so-arbeiten-wir.md) · [📖 Übersicht](README.md) · [12 — Wie es in Produktion läuft](12-wie-es-in-produktion-laeuft.md) ⟶
