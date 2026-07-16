# Insight: Ein Skript testbar zu machen ist der Bug-Fund — nicht die Vorbereitung darauf

**Datum:** 2026-07-16 · **Session:** 5 · **Kontext:** Frage „läuft `install.sh` idempotent?"

## Was passiert ist

Die Frage war eine Review-Frage. Die Antwort war „nein" — aber der Weg dorthin
förderte **mehr Fehler zutage als das Lesen je gefunden hätte**, und zwar nicht
weil die Tests clever waren, sondern weil Testbarkeit den Code zwingt,
Annahmen offenzulegen.

**Beim Lesen lag ich falsch.** Erste Hypothese: `cp -a "$BUNDLE/mpp" "$APP_DIR/"`
verschachtelt beim zweiten Lauf zu `app/mpp/mpp`. Ein 20-Sekunden-Test widerlegte
das — GNU `cp` merged. Der echte Fehler an derselben Stelle war ein anderer: Es
merged *nur*, entfernt also nie etwas; ein im neuen Release gelöschtes Modul und
alte Migrationen überleben jedes Upgrade. **Die richtige Zeile, die falsche
Begründung** — hätte ich den „Fix" ohne Test geschrieben, wäre er am Problem
vorbeigegangen.

**Die Tests fanden Fehler, die im Code unsichtbar waren.** `_mpp_ui_pad` endete
auf `[ $pad -gt 0 ] && printf …`. Bei exakt passender Breite liefert diese Kette
1 zurück — als letzter Befehl der Funktion heißt das Rückgabewert 1, und unter
dem `set -e`, mit dem `install.sh` läuft, hätte das den **gesamten Installer
abgebrochen**. Mein manueller Aufruf lief fehlerfrei durch und verschluckte es;
sichtbar wurde es nur, weil die Tests mit `set -euo pipefail` laufen wie das
echte Skript.

**Testbarkeit erzwang die richtige Architektur.** Um das Panel prüfen zu können,
mussten Erhebung und Rendering getrennt werden (Daten über stdin). Um die
Datenbank-Logik zu prüfen, musste `psql` injizierbar sein — und genau dabei fiel
auf, dass der Aufruf über den **PATH** lief, während PGDG seine Binaries nach
`/usr/pgsql-16/bin/` legt. Die Fake-Injektion war nicht Testgerüst, sie war der
Befund. Dasselbe bei `postgresql-16.service`: hart verdrahtet, und die Doku
forderte ein `Requires=`, das das Skript nie schrieb.

**Vakuum-grüne Tests sind keine Tests.** Mehrere Tests waren beim ersten Lauf
grün, weil „Befehl nicht gefunden" (127) zufällig die erwartete Bedingung
erfüllte. Jeder wurde per Mutation gegen die naive Alt-Implementierung
gegengeprüft; einer war tatsächlich wertlos (`rm -rf ""` scheitert von selbst)
und musste auf die konkrete Guard-Meldung geschärft werden.

## Die Lektion

1. **„Ist X idempotent?" beantwortet man nicht durch Lesen.** Zwei von drei
   meiner Lese-Hypothesen waren falsch oder unvollständig. Shell-Semantik
   (`cp`-Merge, `set -e` + `&&`-Ketten, byte- statt zeichenweises `printf`) ist
   zu subtil für Code-Review aus dem Kopf.
2. **Der Refactor zur Testbarkeit *ist* die Fehlersuche.** Jede Injektionsstelle
   (`MPP_PSQL`, `MPP_SYSTEMCTL`, `MPP_PG_PREFIX`) zwang dazu, eine versteckte
   Annahme zu benennen — und drei davon waren falsch.
3. **Tests müssen in derselben Umgebung laufen wie das Ziel.** `set -euo
   pipefail` in den Testrunner zu übernehmen war kein Detail; es war der einzige
   Grund, warum der schwerste Bug sichtbar wurde.
4. **Jeder grüne Test braucht einen Gegenbeweis.** Ein Test, der nie rot war,
   beweist nichts. Mutation (Alt-Implementierung wieder einsetzen → muss rot
   werden) ist billig und deckte einen Blindgänger auf.
5. **Gates können selbst driften.** `R-STALE` meldete jahrelang grün und suchte
   dabei nach fossilen Konstanten (`228|244`) in nur `*.html`. Eine Regel, deren
   Wahrheit hartkodiert ist, veraltet mit jedem Release. Regeln müssen ihre
   Wahrheit **erheben** (`pytest --collect-only`), nicht speichern — und bei
   „nicht ermittelbar" fehlschlagen statt durchzuwinken.

## Konsequenz für dieses Projekt

- Installer-Logik liegt in `deploy/lib.sh` + `deploy/ui.sh`, 78 Unit-Tests
  (`tests/unit/test_install_*.py`), externe Kommandos injizierbar.
- `R-STALE` vergleicht gegen die frisch erhobene Testzahl statt gegen Konstanten
  und prüft HTML **und** JS.
- Unverändert offen und ehrlich: **nichts davon lief je auf einer echten
  AlmaLinux-9-VM.** Die Fakes beweisen, dass die Logik die richtigen Kommandos in
  der richtigen Reihenfolge wählt — nicht, dass echtes `dnf`, systemd, PGDG und
  SELinux mitspielen. Der neue `--check`-Modus macht genau diesen Test billiger.
