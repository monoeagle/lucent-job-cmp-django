# Rückwärts geprüft ist halb geprüft

**Session 9 · 2026-07-22 · v1.3.3 (getaggt)**

Kurze Fortsetzungssession: aus der Analyse der Vorsession wurden Arbeitspakete. Dabei
fiel ein Fehler in der Analyse selbst auf — und der Fehler war methodisch, nicht zufällig.

---

## Der Befund war richtig, die Grenze falsch

Session 8 hatte festgestellt: die Bestellkette ist nicht verdrahtet. Belegt über vier
`grep`s, die zeigten, dass `dispatch_provisioning`, `create_from_order`,
`AuditService.log` und `NotificationService.create` **niemand** aus dem Produktivcode
aufruft. Die Schlussfolgerung im Report: „`approve()` setzt `APPROVED` und danach
passiert nichts mehr."

Beim Ausformulieren des Arbeitspakets — der Frage „was genau muss ein Entwickler tun?" —
zeigte sich: **`approve()` wird im laufenden System nie erreicht.** Schon
`submit_order()` endet bei `SUBMITTED`, ohne `create_approval_requests` zu rufen. Es
entsteht gar kein `ApprovalRequest`, die Approval-Queue bleibt leer, die Bestellung
hängt für immer. Der beschriebene Bruch war der **zweite von sechs**, nicht der erste.

### Warum das durchrutschte

Die Prüfung lief **rückwärts**: Ich hatte vier ungenutzte Bausteine und fragte je
„wer ruft dich auf?". Das findet zuverlässig alles, was nicht aufgerufen wird — aber
nur, wenn man die Liste der Bausteine vollständig hat. `create_approval_requests` stand
nicht auf der Liste, weil es aus Sicht der Gap-Analyse „erledigt" aussah: es existiert,
es ist getestet, und die zugehörige Anforderung (FM_GE01, Genehmigungen anzeigen) war
über die vorhandene Queue-View als erfüllt abgehakt.

**Vorwärts** — vom Klick des Nutzers her, Schritt für Schritt — wäre es sofort
aufgefallen: „Nutzer klickt Einreichen → was passiert? → `submit_order` → und dann?"

**Lehre:** Rückwärtsprüfung („wer ruft X?") findet tote Bausteine. Nur die
Vorwärtsprüfung („was passiert nach dem Klick?") findet **fehlende Übergänge**. Für
Ketten braucht es beides — und die Vorwärtsrichtung zuerst, weil sie die Liste liefert,
die die Rückwärtsrichtung braucht.

Beim Ausformulieren fiel derselben Methode noch ein **siebter** Punkt zum Opfer:
`approve()` und `reject()` setzen `order.status` direkt und umgehen
`StatusMachine.validate_transition` komplett. Die Statusmaschine wird heute nur in
`submit_order` respektiert — eine Regel, die zur Hälfte gilt, gilt nicht.

---

## „Ist das Best Practice?" ist die falsche Frage

Der Nutzer fragte zum vorgeschlagenen `StatusTransitionService`: „ist eher Best
Practice?" Die bequeme Antwort wäre „ja" gewesen. Die richtige war: **es gibt kein
Muster dieses Namens.** Was Best Practice ist, ist das Prinzip dahinter — *mach das
Richtige zur einzigen Möglichkeit*.

Der Wert lag dann im Differenzieren statt im Zustimmen:

| Aspekt | Gleichförmig? | Konsequenz |
|---|---|---|
| Statuswechsel + Übergangsprüfung | ja | zentralisieren |
| Audit-Eintrag (wer, was, von→nach) | ja | zentralisieren |
| Benachrichtigung (Empfänger, Text) | **nein** | am Aufrufort lassen |

Hätte ich alle drei in eine Funktion gelegt — der ursprüngliche Vorschlag —, wäre eine
Signatur mit sechs Optionalparametern und `if to_status == …`-Ketten entstanden. Genau
die Sorte Helfer, die man später wieder auseinandernimmt.

Ebenfalls wichtig war zu benennen, was **nicht** empfohlen wird, obwohl es naheliegt:
`save()` überschreiben oder Signals. Beides macht die Regel unumgehbar — und versteckt
I/O an einer Stelle, die Fixtures, Migrationen und `seed.py` ungewollt auslösen. Das ist
das Anti-Pattern des fremden Prototyps (`post_save` → synchroner GitLab-Call), nur
eleganter verpackt. Die ehrliche Ergänzung: Zentralisierung **garantiert** nichts,
solange `order.status = …` schreibbar bleibt — deshalb der Wächter-Test im AP.

---

## Konsequenzen

1. **AP-13 … AP-21 angelegt** — in `todo.md`, Roadmap-Tabelle, Board- und Gantt-Quelle;
   jedes AP einzeln, im **gerenderten SVG** einzeln gegengeprüft.
2. **Analyse korrigiert und neu deployt** — §1c mit Nachtrag inkl. Ursache, §5 mit der
   vollständigen Liste der sechs Lücken, Priorisierung um eine AP-Spalte ergänzt.
3. **Für künftige Ketten-Analysen:** erst vorwärts vom Nutzer-Klick durchgehen, dann
   rückwärts nach toten Bausteinen suchen. Nicht umgekehrt.
