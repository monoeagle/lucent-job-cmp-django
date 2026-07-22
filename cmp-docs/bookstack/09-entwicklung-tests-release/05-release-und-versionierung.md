# Release und Versionierung

Wie CMP-Releases versioniert, an welchen Stellen die Version im
Repository steht, und wie ein Release-Tag entsteht.

## 1. Ziel des Kapitels

Wer ein Release vorbereitet, soll wissen: welche Version-Klasse
(MAJOR/MINOR/PATCH) hier gilt, wo überall die Versionsnummer nachgezogen
werden muss, und was ein automatisiertes Gate davon bereits abdeckt.

## 2. Semantische Versionierung, projektspezifisch gehandhabt

Das Projekt folgt SemVer (`MAJOR.MINOR.PATCH`), mit einer Besonderheit:
**MAJOR-Sprünge sind eine Nutzerentscheidung**, MINOR und PATCH werden im
laufenden Betrieb eigenständig vergeben. Über sechs Releases (`v1.1.0` …
`v1.3.3`) ist bislang **kein** MAJOR-Sprung erfolgt — alles blieb `1.x`.
Die Einordnung steht jeweils im ersten Absatz des Changelog-Eintrags,
zum Beispiel (`cmp-docs/docs/entwicklung/changelog.md:5-6`):

```text
Reines Doku-Release. PATCH: keine Code-Änderung am Portal, kein neues
Anwendungs-Artefakt — das Offline-ZIP von v1.3.1 bleibt gültig.
```

und für v1.3.0 (`changelog.md:131`): „MINOR: neue Installer-Fähigkeiten,
Portal-Code unverändert." Die Faustregel aus der Praxis: reine
Doku-/Bugfix-Releases sind PATCH, neue Fähigkeiten (auch am Installer,
nicht nur am Portal-Code) sind MINOR.

## 3. Wo die Versionsnummer überall steht

Grep über das Repository (`grep -rl "1.3.3"`, 2026-07-22, ohne generierte
Doku-Site und Handoff-Dateien) findet die Versionsnummer an diesen
Codestellen:

| Datei | Zeile | Rolle |
|---|---|---|
| `lucent-hub.yml` | 6 | Single Source of Truth für Build-Skripte |
| `cmp-docs/zensical.toml` | 7 | `site_description`-Zeile der Doku-Site |
| `cmp-docs/docs/javascripts/icon-rail.js` | 26 | Versionsanzeige im Doku-Header |
| `run.sh` | 16 | `APP_VERSION`, **aus `lucent-hub.yml` abgeleitet**, nicht hartkodiert |
| `cmp/apps/accounts/management/commands/seed.py` | 410 | Seed-Detail eines `AuditService.log`-Eintrags |
| `todo-erledigt.md` | 3 | Kopfzeile „Stand …, vX.Y.Z, N Tests grün" |

`run.sh:13-17` kommentiert ausdrücklich, warum die Ableitung aus
`lucent-hub.yml` gewählt wurde: eine frühere hartkodierte Version dort
war einmal hinter `lucent-hub.yml` zurückgefallen, ohne dass eine Prüfung
das bemerkt hätte.

## 4. Automatisiertes Gate prüft nur vier der sechs Stellen

`cmp-docs/verify_docs.sh` (Regel **R-VERSION**, `verify_docs.sh:64-83`)
vergleicht `zensical.toml`, `lucent-hub.yml`, `icon-rail.js` und die aus
`lucent-hub.yml` abgeleitete `run.sh`-Version gegeneinander:

```bash
rule "R-VERSION — zensical.toml == lucent-hub.yml == icon-rail.js == run.sh"
```

`seed.py:410` und die Kopfzeile in `todo-erledigt.md:3` werden von dieser
Regel **nicht** erfasst — sie müssen bei jedem Release von Hand
nachgezogen werden. Das Gate meldet grün, auch wenn genau diese beiden
Stellen veraltet sind.

## 5. Tags markieren das Release

```bash
git tag -l --sort=-creatordate
```

liefert `v1.3.3`, `v1.3.2`, `v1.3.1`, `v1.3.0`, `v1.2.0`, `v1.1.0`. Es
sind **annotierte** Tags (`git cat-file -t v1.3.3` → `tag`, nicht
`commit`) mit einer kurzen Release-Beschreibung als Tag-Message, zum
Beispiel für `v1.3.3`: „v1.3.3 — Analyse der Bestellportal-Fremddoku +
AP-13…AP-21" mit einer Zeile zur Einordnung („Reines Doku-Release, kein
Anwendungscode"). Es gibt keinen separaten Release-Branch — der Tag
zeigt direkt auf einen Commit auf `main`.

## 6. Ablauf eines Releases in der Praxis

1. Version an den in Abschnitt 3 gelisteten Stellen anheben (alle sechs,
   nicht nur die vier vom Gate geprüften)
2. Neuen Abschnitt oben im Changelog ergänzen, mit PATCH/MINOR/MAJOR-Satz
   im ersten Absatz (Kapitel 9.6)
3. `cmp-docs/verify_docs.sh` grün — deckt vier von sechs Versionsstellen ab, die zwei übrigen manuell gegenprüfen
4. Bei Bedarf Artefakt bauen: `./run.sh docs-zip` (Doku) bzw. `./run.sh release` (Offline-Wheelhouse, AlmaLinux 9)
5. Annotierten Tag setzen (`vX.Y.Z`) mit Kurzbeschreibung als Message

## 7. Zusammenfassung

CMP folgt SemVer mit einer Governance-Regel: MAJOR ist Nutzerentscheidung,
MINOR/PATCH werden autonom vergeben — bislang ausschließlich innerhalb
`1.x`. Die Versionsnummer steht an sechs Stellen im Repository; das
automatisierte Gate deckt vier davon ab, `seed.py` und
`todo-erledigt.md` bleiben Handarbeit. Releases werden über annotierte
Git-Tags markiert, nicht über Branches.

> Quelle: `cmp-docs/docs/entwicklung/changelog.md:5-6,131`, `lucent-hub.yml:6`, `cmp-docs/zensical.toml:7`, `cmp-docs/docs/javascripts/icon-rail.js:26`, `run.sh:13-17`, `cmp/apps/accounts/management/commands/seed.py:410`, `todo-erledigt.md:3`, `cmp-docs/verify_docs.sh:64-83`, `git tag -l`, `git cat-file -t v1.3.3` — am Code geprüft 2026-07-22
