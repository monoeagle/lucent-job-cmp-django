# CMP-Handbuch für Bookstack

Dieses Verzeichnis enthält das CloudMan-Portal-Handbuch in der Form, in der es sich in
Bookstack einstellen lässt: **ein Ordner je Kapitel, eine Markdown-Datei je Seite.**

Diese Datei ist eine Lesehilfe für das Repository und **keine Bookstack-Seite** — sie wird
nicht importiert.

## Aufbau

```
bookstack/
├── 01-ziel-und-anforderungen/          Kapitel 1     5 Seiten
├── 02-architektur-und-prozesse/        Kapitel 2     5 Seiten
├── 03-domaenenmodell-und-apps/         Kapitel 3     7 Seiten
├── 04-rollen-und-rechte/               Kapitel 4     5 Seiten
├── 05-genehmigungs-workflow/           Kapitel 5     5 Seiten
├── 06-views-urls-und-htmx/             Kapitel 6     6 Seiten
├── 07-logging-monitoring-audit/        Kapitel 7     4 Seiten
├── 08-deployment-und-betrieb/          Kapitel 8     8 Seiten
├── 09-entwicklung-tests-release/       Kapitel 9     6 Seiten
├── 10-oberflaeche/                     Kapitel 10   13 Seiten
├── 11-entscheidungen-adr/              Kapitel 11    2 Seiten
├── anhang-a-neuen-service-anlegen/     Anhang A      6 Seiten
├── anhang-b-projektstruktur/           Anhang B      1 Seite
└── anhang-c-werkzeuge-im-repo/         Anhang C      1 Seite
```

Buch: „CloudMan Portal (CMP) — Betriebs- und Entwicklungshandbuch".
Ordnername = Kapitelname, Dateiname = Seitenname, Zahlen davor = Reihenfolge.
Der Seitentitel steht zusätzlich als erste Zeile (`# …`) in jeder Datei.

## Stand

**Vollständig** gegenüber der Spec (`docs/superpowers/specs/2026-07-22-bookstack-doku-design.md`):
11 Kapitel und 3 Anhänge, 74 Seiten. Zuerst entstand der Pilot (Kapitel 1–3 + Anhang A), nach
dessen Abnahme die übrigen Kapitel.

Offen bleibt der **Importweg** (siehe unten) und ein Generator, der diesen Stand automatisch
gegen `cmp-docs/docs/` abgleicht.

Die Seiten beschreiben den Ist-Stand, nicht ein Zielbild: Wo eine Funktion fehlt oder eine
Kette nicht verdrahtet ist, steht das als Lücke mit Verweis auf das Arbeitspaket in `todo.md`.

## Regeln für diese Dateien

Bookstack rendert kein MkDocs. Deshalb gilt in diesem Verzeichnis:

- reines CommonMark und Markdown-Tabellen
- keine Admonitions (`!!!`), keine Attributblöcke (`{: …}`), kein Frontmatter
- keine Mermaid-Codeblöcke — Abläufe als Tabelle oder als ASCII-Skizze im Codeblock
- Bilder als Markdown (`![alt](pfad)`), nie als `<img>`-Tag
- jede Seite endet mit einer Quellenzeile, die die belegenden Code-Stellen nennt

Kapitel 10 bindet die 14 Screenshots relativ aus `../../docs/images/screenshots/` ein. Beim
Import müssen die Bilder mit hochgeladen und die Pfade auf die Bookstack-Ablage umgestellt
werden — die relative Form gilt nur für das Repository und die lokale Vorschau.

Prüfen lässt sich das so:

```
grep -rn '^!!!\|{: \|```mermaid' cmp-docs/bookstack/
```

Kein Treffer bedeutet: importierbar.

## Verhältnis zur übrigen Doku

`cmp-docs/docs/` bleibt die Quelle des MkDocs-Auftritts. Die Seiten hier sind daraus und aus
dem Code neu verfasst, nicht kopiert; jede Seite nennt am Ende ihre Belege. Ein Generator, der
beide Stände automatisch abgleicht, ist ein eigenes, späteres Arbeitspaket.

## Import nach Bookstack

Der Importweg hängt von Version und Rechten der Ziel-Instanz ab und ist noch **nicht geprüft**.
Das hier gewählte Format — eine Datei je Seite — taugt für alle gängigen Wege: manuelles
Einfügen, Import über die Bookstack-API oder die eingebaute Import-Funktion. Sobald der Weg
feststeht, wird dieser Abschnitt ergänzt.
