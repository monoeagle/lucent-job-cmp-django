# Insight — Gebaute Artefakte im Zielmedium verifizieren, nicht im Build-Log

**Datum:** 2026-06-27 · **Session:** 3 (Oberflächen-Galerie, gh-pages, Offline-Release)

## Beobachtung

Mehrere Bugs dieser Session waren in jedem Build-Log und Gate **grün**, aber im
echten Zielmedium **kaputt**:

1. **Doku-Screenshots „fehlten"** auf gh-pages. Das Doku-Gate (`verify_docs.sh`)
   meldete „Hero-SVG valide / referenziert" — es prüft aber nur, ob die
   **Datei existiert**, nicht ob der relative `<img src>` im Browser **auflöst**.
   Ursache: Tiefe-2-Seiten (`/referenz/oberflaeche/`) brauchen `../../images/`,
   nicht `../images/`. Derselbe Fehler steckte latent auch in `arbeitspakete.md`
   (Roadmap-Diagramme) — niemand hatte es bemerkt, weil das Gate grün war.
2. **Heatmap zeigte die laufende Arbeit nicht** — sie liest `project-activity.json`
   aus der **Git-Historie**, die Session-Arbeit war aber uncommittet. „Build grün"
   heißt nicht „Daten aktuell".
3. **Offline-Release**: „32 Wheels gebündelt" sagt nichts darüber, ob die
   Installation **wirklich offline** durchläuft.

## Lektion

**Ein grünes Build-/Gate-Log beweist nur, dass der Build lief — nicht, dass das
Artefakt im Zielmedium funktioniert.** Verifikation muss im echten Medium
passieren:

- **Doku** → headless Chrome auf der **deployten** Seite: `naturalWidth > 0` über
  alle Bilder, Klick-Toggle real auslösen, aufgelöste URL per `curl` prüfen.
  (Datei-Existenz ≠ Pfad-Auflösung.)
- **Aktivitätsdaten** → erst committen, dann regenerieren, dann live prüfen,
  dass „heute" auftaucht.
- **Offline-Release** → frisches venv + `pip install --no-index --find-links=wheels`
  laufen lassen + Smoke-Import. (Das fand die echte Bestätigung, dass das
  Wheelhouse vollständig ist.)

## Anwendung / Konsequenz

- Memory [[docs-verify-in-browser]] angelegt: nach jedem Doku-Deploy Browser-Check.
- Gate-Schwäche dokumentiert: `verify_docs.sh` könnte um eine Regel ergänzt werden,
  die für jede `<img src>` die **aufgelöste Pfadtiefe** gegen `site/` prüft
  (würde die `../images`-Falle künftig rot färben).
- Verallgemeinert: Bei jeder „X gebaut/erzeugt"-Behauptung die **Wirkung** im
  Zielmedium messen, nicht die Existenz des Outputs.

## Verwandt

- [[ludbxp-docs-referenz]] — luDBxP als Stil-/Release-Vorlage (Hero=APs,
  Architektur-Badge, Banded-Layer, Oberflächen-Galerie, gh-pages, Wheel-Bundle).
- [[versioning-policy]] — v1.0.0→v1.1.0, alle Versionsstellen synchron (R-VERSION).
