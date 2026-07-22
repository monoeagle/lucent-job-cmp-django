# Ein Handbuch zu schreiben ist die gründlichste Code-Prüfung, die es gibt

**Session 10 · 2026-07-22/23 · v1.3.3 → v1.4.0**

## Der Befund

Diese Session sollte Dokumentation schreiben. Sie hat stattdessen sieben Fehler im Code
gefunden, drei davon sicherheitsrelevant und alle drei real ausnutzbar. Kein Review, kein
Audit, kein Security-Scan war beauftragt — es genügte die Auflage, **jede Aussage über den
Code mit `datei.py:zeile` zu belegen**.

Gefunden wurden unter anderem:

- `OrderDetailView` lieferte fremde Bestellungen mit HTTP 200 aus (ebenso Subscription
  und Notification-MarkRead) — die Rollen-Mixins griffen, die Objektebene fehlte
- `/debug-layout/` war anonym erreichbar, ohne Login, ohne Mixin
- `ApprovalRule.approver_role` sah aus wie eine Rechteprüfung, wurde aber von keiner
  Codestelle gelesen — reine Dekoration in Admin und Seed
- `AuditService.log` wird ausschließlich aus `seed.py` aufgerufen; der Audit-Trail ist
  im Betrieb leer
- `submitted → approved` ist ein deklarierter, aber toter Übergang
- `npm run css:build` schlägt seit der Umbenennung MPP → CMP fehl, und `scripts/run.sh`
  verschluckt den Fehler und meldet Erfolg
- `ALLOWED_HOSTS` ist entgegen dem eigenen Docstring keine Pflichtvariable

Keiner dieser Punkte war neu entstanden. Sie lagen alle seit Monaten im Code, unter
330 grünen Tests.

## Warum Doku findet, was Tests nicht finden

Ein Test prüft eine Erwartung, die jemand hatte. Eine Doku-Zeile behauptet etwas über den
Code — und wer sie belegen muss, liest den Code **ohne Erwartung**. Genau dort fallen
Dinge auf, die niemand je erwartet hat und für die deshalb auch niemand einen Test schrieb.

`approver_role` ist das Musterbeispiel: Es gab keinen Test, der prüfte, dass die Rolle
*ignoriert* wird — warum sollte es den geben? Erst der Satz „dieses Feld legt fest, wer
genehmigen darf" zwang zu der Frage: *Wer liest es eigentlich?* Antwort: niemand.

Umgekehrt gilt: Wäre die Doku wie üblich aus der vorhandenen Doku abgeschrieben worden,
hätte sie den Fehler mitkopiert. `referenz/datenmodell.md` beschrieb `approver_role` als
„Welche Rolle genehmigt" — eine Aussage, die erst seit v1.4.0 wahr ist.

## Der Fix legt die nächste Mine

`approver_role` ist ein freies `CharField` ohne `choices`. Solange niemand es las, war ein
Wert wie `"netzwerk"` folgenlos. Seit der neuen Prüfung hätte er die Anfrage für
**niemanden** entscheidbar gemacht — auch nicht für den Superadmin, weil
`is_at_least_role` für unbekannte Werte stumm `False` liefert.

Ein defekter Code kann Konfigurationsfehler kaschieren. Wer ihn repariert, schärft sie.
**Beim Schließen einer Lücke gehört deshalb die Frage dazu: Was war bisher nur deshalb
harmlos, weil dieser Code nicht funktionierte?**

Gefunden hat das nicht der Fix, sondern erneut der Doku-Abgleich.

## Zwei Tests, die nichts prüften

`test_shows_only_own_orders` versprach im Namen eine Besitzprüfung, verglich aber nur den
Statuscode — sein eigener Kommentar sagte, was er hätte prüfen sollen. Er war jahrelang
grün und hätte den IDOR-Fehler nie gemeldet.

Und beim Absichern der `choices` schrieb ich selbst einen Test, der sofort grün war: Er
scheiterte an fehlendem `template`/`condition`, nicht an der Rolle. Ein grüner Test aus
dem falschen Grund ist schlimmer als kein Test, weil er Sicherheit vortäuscht.

**Regel:** Nach jedem neuen Test die Gegenprobe — kaputtmachen, was er prüfen soll, und
zusehen, ob er rot wird. Bei `test_shows_only_own_orders` wurde der Besitzfilter sabotiert;
erst als er fiel, war er ein Test.

## Was das für die Reihenfolge bedeutet

Die intuitive Reihenfolge ist: erst bauen, dann dokumentieren. Diese Session legt eine
andere nahe — **Dokumentieren ist ein Prüfverfahren, kein Nachbereiten.** Ein Kapitel über
ein Subsystem zu schreiben, bevor man es freigibt, findet mehr als ein Review desselben
Subsystems, weil das Review nach Fehlern sucht (und findet, was es erwartet), die Doku
aber nach Wahrheit (und findet, was da ist).

Der Preis ist Ehrlichkeit: Ein Handbuch, das Lücken beschönigt, verliert genau diese
Wirkung. Jede Seite hier nennt den Ist-Stand, mit Arbeitspaket-Verweis, wo etwas fehlt.

---

**Belege:** AP-22 (`todo-erledigt.md`), Commits `011dd5f`, `e44ee4e`, `ed3114f`;
Handbuch `cmp-docs/bookstack/` (74 Seiten); AP-23 (`todo.md`, offen)
