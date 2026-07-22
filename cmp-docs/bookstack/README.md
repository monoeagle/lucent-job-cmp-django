# CMP-Handbuch für Bookstack

Dieses Verzeichnis enthält das CloudMan-Portal-Handbuch in der Form, in der es sich in
Bookstack einstellen lässt: **ein Ordner je Kapitel, eine Markdown-Datei je Seite.**

Diese Datei ist eine Lesehilfe für das Repository und **keine Bookstack-Seite** — sie wird
nicht importiert.

## Aufbau

```
bookstack/
├── 01-ziel-und-anforderungen/          Kapitel 1
├── 02-architektur-und-prozesse/        Kapitel 2
├── 03-domaenenmodell-und-apps/         Kapitel 3
└── anhang-a-neuen-service-anlegen/     Anhang A
```

Buch: „CloudMan Portal (CMP) — Betriebs- und Entwicklungshandbuch".
Ordnername = Kapitelname, Dateiname = Seitenname, Zahlen davor = Reihenfolge.
Der Seitentitel steht zusätzlich als erste Zeile (`# …`) in jeder Datei.

## Stand

Umgesetzt ist der **Pilot** aus der Spec (`docs/superpowers/specs/2026-07-22-bookstack-doku-design.md`):
Kapitel 1, 2, 3 und Anhang A. Die Kapitel 4 bis 11 (Rollen und Rechte, Genehmigungs-Workflow,
Views/URLs/HTMX, Logging, Deployment, Entwicklung, Oberfläche, Entscheidungen) sowie die
Anhänge B und C sind geplant, aber noch nicht geschrieben.

## Regeln für diese Dateien

Bookstack rendert kein MkDocs. Deshalb gilt in diesem Verzeichnis:

- reines CommonMark und Markdown-Tabellen
- keine Admonitions (`!!!`), keine Attributblöcke (`{: …}`), kein Frontmatter
- keine Mermaid-Codeblöcke — Abläufe als Tabelle oder als ASCII-Skizze im Codeblock
- jede Seite endet mit einer Quellenzeile, die die belegenden Code-Stellen nennt

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
