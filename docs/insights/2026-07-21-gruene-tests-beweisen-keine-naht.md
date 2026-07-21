# Grüne Tests beweisen keine Naht — und „anonymisiert" ist eine Behauptung

**Session 8 · 2026-07-21 · v1.3.3**

Zwei Erkenntnisse, die nichts miteinander zu tun haben, außer dass beide dieselbe
Form hatten: etwas sah geprüft aus und war es nicht.

---

## 1. 330 grüne Tests, und der Workflow läuft trotzdem nicht

Aufgabe war, eine Fremddoku (Bestellportal der Zielumgebung, API-First/DRF) gegen
CMP auszuwerten. Der wichtigste Befund kam nicht aus der Fremddoku, sondern aus dem
Zwang, jede Anforderung **gegen echten Code** zu belegen statt gegen unsere eigene Doku.

Beim Abhaken von FM_GE03 („Genehmigen, danach Aufbau einleiten") fiel auf:
`ApprovalService.approve()` setzt den Status auf `APPROVED` — und endet. Die Frage
„wer ruft danach das Provisioning?" führte zu vier `grep`s mit demselben Ergebnis:

| Baustein | Aufgerufen von |
|---|---|
| `dispatch_provisioning` / `complete_provisioning` (Celery) | niemandem |
| `SubscriptionService.create_from_order` | nur Tests |
| `AuditService.log` | nur `seed.py` |
| `NotificationService.create` | nur `seed.py` und Tests |

**Das Audit-Log enthält im laufenden Betrieb ausschließlich Seed-Demodaten.** Eine
echte Genehmigung in der Oberfläche erzeugt keinen Eintrag, keine Benachrichtigung,
keine Subscription. Modell, Service, View und CSV-Export existieren vollständig und
sind getestet — verdrahtet ist nichts.

### Warum das durch alle Netze fiel

Jeder Baustein hat Tests, und alle sind grün. Auch der E2E-Test ist grün — aber er
ruft die Schritte **selbst nacheinander auf**:

```python
ProvisioningService.dispatch_order(order.pk)
ProvisioningService.complete_dispatch(log.pk, success=True)
subs = SubscriptionService.create_from_order(order.pk)
```

Damit beweist er, dass die Bausteine **zusammenpassen** — nicht, dass jemand sie
zusammenruft. Der Test ist selbst der fehlende Produktionscode. Er ersetzt genau die
Verdrahtung, deren Fehlen er hätte aufdecken sollen.

Dazu kommt: **Seed-Daten kaschieren das perfekt.** Die Oberfläche zeigt Audit-Einträge
und Benachrichtigungen, die Glocke hat eine Zahl — alles sieht funktionierend aus.
Wer das Portal demonstriert, sieht nie den Unterschied zwischen „wird erzeugt" und
„wurde einmal geseedet".

**Lehre:** Ein E2E-Test, der Services direkt aufruft, ist ein Integrationstest der
Bausteine. Ein echter E2E-Test geht **durch die Views** — durch den Weg, den ein
Nutzer nimmt. Nur der beweist die Naht. Und wenn eine Kette aus n Schritten besteht,
ist die Frage nicht „hat jeder Schritt einen Test?", sondern **„wer ruft Schritt k+1?"**

Nebenbefund derselben Methode: `AuditLogListView` beantwortet HTMX-Anfragen mit der
kompletten Seite statt mit einem Fragment (fehlender `get_template_names`-Zweig,
die korrekte Vorlage steht in `catalog/views.py:25`). Auch das war unsichtbar —
niemand hatte den Filter je im Browser benutzt.

---

## 2. „anon" im Dateinamen ist keine Anonymisierung

Die Fremddoku hieß `bestellportal_anon.md` und war es teilweise: die Domain war
konsequent zu `<domain>` maskiert. Nicht maskiert waren:

- AD-Domäne und Benutzerkennung in einem Beispielpfad (`/home/POLADM/p1enpa2904/…`)
- der **Klarname** des Autors einer verlinkten Belegarbeit
- der Name eines Admin-Kontos, die Organisationseinheit, die Umgebungsbezeichnung
- ein AI-Recherchelink, dessen URL-Slug die interne Fragestellung enthielt

Die Datei lag zu diesem Zeitpunkt bereits **öffentlich** auf GitHub. Der Dateiname
hatte die Prüfung ersetzt: „anon" gelesen, Domain-Maskierung stichprobenartig
gesehen, Rest angenommen. Ein `grep` nach Namensmustern, Home-Pfaden und externen
URLs fand in Sekunden, was das Vertrauen in den Dateinamen übersehen hatte.

### Und: Force-Push löscht nichts

Nach dem History-Rewrite war der alte Commit über seine SHA **weiterhin öffentlich
abrufbar** — geprüft, nicht angenommen:

```
gh api "repos/…/contents/bestellportal_anon.md?ref=e8e6cac" | base64 -d | grep -c POLADM
→ 1
```

GitHub sammelt unreferenzierte Objekte nicht automatisch ein. „Ich habe die History
bereinigt" wäre eine wahre Aussage über das Repo und eine falsche über die
Erreichbarkeit gewesen. Vollständig schließt das nur ein Support-Ticket.

**Lehre:** Bei allem, was veröffentlicht wird, prüft man **das Ergebnis am Ziel**,
nicht den eigenen Arbeitsschritt. `git push --force` meldet Erfolg für etwas anderes
als das, was man erreichen wollte.

---

## 3. Zwei eigene Fehler, beide beim Nachprüfen gefunden

- **CRLF stillschweigend normalisiert.** Mein Anonymisierungs-Skript las mit
  `read_text()` und schrieb mit `write_text()` — das wandelte 2672 CRLF-Zeilenenden
  nach LF. Der Diff zeigte 2675 geänderte Zeilen statt der 7 gewollten. Aufgefallen
  nur, weil ich den Diff **gezählt** habe, statt „Ersetzung lief durch" zu lesen.
  Byte-genau neu gemacht (`read_bytes`/`write_bytes`).
- **Falscher Bildpfad.** Der Mermaid-Renderer setzte `../images/` für eine
  Tiefe-2-Seite; die Konvention ist `../../images/`. Hätte ein kaputtes Diagramm auf
  der Live-Seite ergeben. Gefunden, weil ich den `<img src>` gegen die reale
  Dateilage geprüft habe statt „Build ohne Fehler" zu glauben.

Beide Fehler hatten dieselbe Form wie die beiden Hauptbefunde: **eine Erfolgsmeldung
über den Vorgang, nicht über das Ergebnis.**

---

## Konsequenzen

1. **Vorgeschlagen als AP-13 (Vorrang, noch nicht angelegt — Entscheidung offen):**
   Workflow verdrahten — `approve → dispatch → done → Subscription`, dazu
   `AuditService.log` und `NotificationService.create` an jedem Statuswechsel.
   Abnahme über einen E2E-Test, der **durch die Views** geht.
2. Vor jedem `git push` in ein öffentliches Repo: Muster-Grep auf Namen, Home-Pfade,
   interne Hosts, externe Links — auch (gerade) wenn die Datei „anon" heißt.
3. Bilder sind nicht greppbar. Screenshots aus fremden Umgebungen bleiben ungetrackt
   (`analyse/.gitignore`), bis jemand sie angesehen hat.
