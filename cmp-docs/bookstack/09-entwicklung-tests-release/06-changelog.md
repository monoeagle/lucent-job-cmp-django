# Changelog

Wie der CMP-Changelog aufgebaut ist und gepflegt wird — als Systematik
beschrieben, nicht als Kopie des Inhalts.

## 1. Ziel des Kapitels

Wer einen Changelog-Eintrag für ein neues Release schreibt, soll wissen,
welcher Aufbau erwartet wird und wo die Datei liegt — ohne die
Vergangenheit hier noch einmal abzuschreiben.

## 2. Ort und Sprache

Der Changelog liegt unter `cmp-docs/docs/entwicklung/changelog.md` und
ist vollständig auf Deutsch (`language = "de"`,
`cmp-docs/zensical.toml:63`). Eine Prüfung am 2026-07-22 (Suche nach
`*.en.md` sowie nach „en"-Varianten des Dateinamens im gesamten
Repository) ergibt: Es existiert **keine** separate
englischsprachige Fassung und keine EN/DE-Mirror-Struktur für diesen
Changelog — auch das Projekt-`README.md` ist rein deutsch. Sollte an
anderer Stelle von einem zweisprachigen Changelog ausgegangen werden, gilt
für den Stand 2026-07-22: nur die eine deutsche Datei.

## 3. Aufbau je Eintrag

Jeder Abschnitt beginnt mit einer `##`-Überschrift im Muster
`vX.Y.Z — Kurztitel — Datum` (bei reinen Wartungseinträgen ohne Tag auch
ohne Versionsnummer, z. B. „Wartung — 2026-06-18"), reverse-chronologisch
— der neueste Eintrag steht oben. Direkt im ersten Absatz folgt die
Versionsklasse mit Begründung, siehe Kapitel 9.5, Abschnitt 2. Danach
gliedern `###`-Zwischenüberschriften den Eintrag thematisch (z. B. „Neue
Seite: …", „Installer: …", „Behoben (durch die Tests gefunden): …").

## 4. Ein Eintrag pro Release, auch für reine Doku-Releases

Auch Releases ohne Code-Änderung bekommen einen vollständigen Eintrag —
`v1.3.1`, `v1.3.2` und `v1.3.3` sind alle als „Reines Doku-Release,
PATCH" gekennzeichnet, mit derselben Gliederungstiefe wie
Feature-Releases. Das hält den Changelog als vollständige
Entscheidungs- und Änderungshistorie nutzbar, nicht nur als
Feature-Liste.

## 5. Funde und Ursachen werden benannt, nicht nur Ergebnisse

Der Changelog dokumentiert nicht nur *was* sich geändert hat, sondern oft
auch *warum ein früherer Versuch nicht ausreichte* — etwa der Nachtrag zu
v1.3.3 ((„die Bestellkette bricht früher als beschrieben"), der eine
vorherige Analyse korrigiert und die Ursache des ersten Fehlschlusses
benennt. Dieses Muster — Befund, Korrektur, Ursache — ist im Changelog
durchgehend zu finden, nicht nur bei diesem einen Eintrag.

## 6. Kennzahlen gehören nicht in diesen Changelog

Eine Kennzahlen-Tabelle (Apps, Models, Services, Tests, Commits) steht nur
einmalig am Ende des `v1.0.0`-Eintrags. Laufende Kennzahlen je Session
werden **nicht** hier, sondern separat in `docs/session-kennzahlen.md`
geführt — der Changelog bleibt auf Release-Inhalte fokussiert.

## 7. Bezug zu anderen Doku-Flächen

Ein Changelog-Eintrag zieht typischerweise weitere Flächen nach: neue
Arbeitspakete werden zugleich in `todo.md`, der Roadmap-Tabelle, dem Board
und dem Gantt-Diagramm aufgenommen (so geschehen für AP-13…AP-21 in
`v1.3.3`) — jedes Arbeitspaket einzeln benannt, nicht als
Sammel-Spanne.

## 8. Zusammenfassung

Der Changelog ist eine einzelne, deutsche Markdown-Datei mit fester
Eintragsform: Versionsüberschrift, Klassifizierung im ersten Satz,
thematische Unterabschnitte, auch für reine Doku-Releases. Kennzahlen
gehören in eine separate Datei, nicht in den Changelog selbst — und es
gibt, anders als man vermuten könnte, keine EN-Fassung dieses Dokuments.

> Quelle: `cmp-docs/docs/entwicklung/changelog.md`, `cmp-docs/zensical.toml:63`, `README.md`, `docs/session-kennzahlen.md` (Existenz geprüft, Inhalt nicht Gegenstand dieser Seite) — am Code geprüft 2026-07-22
