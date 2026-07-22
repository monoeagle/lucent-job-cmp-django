# Design — CMP-Handbuch als Bookstack-Buch (SSR)

**Datum:** 2026-07-22
**Status:** freigegeben (Nutzer-Go am 2026-07-22 auf den HTML-Strukturvorschlag)
**Bezug:** `analyse/analyse-bestellportal.md` §2.11 (offenes AP „Bookstack-Export"),
`analyse/anforderungen.md` Z. 5 + Lernziel-Punkte, `analyse/bestellportal_anon.md` (Fremdbuch)

## Ziel

Ein **Bookstack-taugliches Handbuch für CMP** — dieselbe Kapitelfolge wie das Bestellportal-Buch
der Zielumgebung, aber durchgehend unser **SSR-Weg** (Django-Templates + HTMX, kein DRF).
Dazu ein **Anhang als Kochbuch**, der Schritt für Schritt zeigt, wie man einen neuen Service
oder eine neue Bestelloption ergänzt.

Zwei Leserkreise: (1) wer das Fremdbuch kennt und die Ansätze vergleichen will,
(2) wer am CMP weiterentwickelt und ein Rezept braucht.

## Was aus der Fremdstruktur übernommen wird

**Übernommen wird das Gerüst, nicht der Text.** Jede Aussage wird gegen den Code geprüft
(`grep`/Lesen), nicht aus dem Fremdbuch übersetzt.

| Fremdbuch | Entscheidung | Bei uns |
|---|---|---|
| Zieldefinition und Anforderungen | übernehmen | Kap. 1 — inkl. `FM_*`/`FK_*`-IDs, je Anforderung Status erfüllt/offen (AP-x) |
| Architektur & Prozessübersicht | anpassen | Kap. 2 — `views → services → models` statt Frontend/Backend-Schnitt |
| A) Domänenmodell & App-Struktur | übernehmen | Kap. 3 — 10 Apps, 15 Tabellen |
| B) Rollen, Rechte & AD | anpassen | Kap. 4 — allauth/Session; **AD/LDAP nur als Ausblick**, JWT entfällt |
| C) Approval Workflow | übernehmen | Kap. 5 — inkl. Ist-Stand/Lücken (AP-13) |
| D) API-Design (DRF) | **streichen** | Kap. 6 **neu**: Views, URLs & HTMX-Kontrakt |
| E) Logging, Monitoring & Audit | übernehmen | Kap. 7 |
| F) Deployment & Infrastruktur | anpassen | Kap. 8 — nativ/systemd (ADR-0001), Offline-Wheelhouse |
| G) CI/CD & Teststrategie | anpassen | Kap. 9 — TDD-Pflicht, Umgebungsweg Test→QS→Prod |
| Prototyp-Doku, Deployment-Kapitel | streichen bzw. eindampfen | HTMX-Fallstricke → Kap. 6, Secrets → 8.2 |
| — | **neu** | Kap. 10 Oberfläche, Kap. 11 ADRs, Anhang A/B/C |

Ebenfalls übernommen: die **Seitenform** des Fremdbuchs („1. Ziel des Kapitels" … „n. Zusammenfassung").
Sie ist für Bookstack-Seiten gut geschnitten und macht beide Bücher vergleichbar.

## Struktur

Ein Buch, 11 Kapitel + 3 Anhänge, ~45 Seiten. Vollständiger Baum: siehe HTML-Vorschlag
(`analyse/bookstack-struktur-vorschlag.html`), er ist Teil dieser Spec.

## Ablage und Format

- **Ort:** `cmp-docs/bookstack/<NN>-<kapitel-slug>/<NN>-<seiten-slug>.md`
- **Eine Datei = eine Bookstack-Seite.** Erste Zeile `# <Seitentitel>` = Seitenname in Bookstack.
- **Kein Frontmatter**, keine MkDocs-Erweiterungen (keine `!!!`-Admonitions, keine
  `{: .class}`-Attribute) — reines CommonMark + Tabellen, weil Bookstack sonst Rohtext zeigt.
- **Mermaid → PNG:** Bookstack rendert kein Mermaid. Diagrammquellen liegen unter
  `cmp-docs/mermaid-sources/`, gerendert wird mit `cmp-docs/tools/render_mermaid.sh`;
  eingebunden wird das Bild.
- **Bilder** relativ zur Seite, beim Import mit hochzuladen.

**Ungeprüft, bewusst offen gelassen:** Wie die Ziel-Bookstack-Instanz importiert (Version,
Rechte, API-Token). Deshalb das robusteste Format — eine Datei je Seite in nummerierten
Ordnern —, das für alle drei denkbaren Wege taugt (manuelles Einfügen, API-Skript,
eingebaute Import-Funktion). Ein Import-Skript ist **nicht** Teil dieser Scheibe.

## Quelle und Drift

`cmp-docs/docs/` bleibt die Quelle für alles, was es dort schon gibt. Für den Pilot werden
die Bookstack-Seiten **von Hand** verfasst — erst wenn die Form steht, lohnt ein Generator.
Solange gilt: jede Seite nennt am Ende ihre Quelle (Doku-Datei oder Code-Stelle), damit
Drift auffällt. Ein Generator `cmp-docs → bookstack/` ist ein eigenes, späteres AP.

## Abgrenzung

- **Keine Interna.** Das Repo ist öffentlich: nichts aus `analyse/bestellportal_anon.md`,
  keine Kennungen, Klarnamen, internen Hostnamen. Aussagen über die Zielumgebung nur, soweit
  sie unseren eigenen Code betreffen.
- **Kein Anwendungscode** wird in dieser Scheibe geändert. AP-13 (Bestellkette verdrahten)
  bleibt davon unberührt; das Handbuch **beschreibt** die Lücke, es schließt sie nicht.
- Kapitel 4–11 sind Teil des Zielbilds, aber **nicht** dieser Scheibe.

## Umfang dieser Scheibe (Pilot)

Kapitel 1, 2, 3 und Anhang A — 23 Seiten. Zweck: die Form einmal treffen und gegenlesen
lassen, bevor der Rest entsteht.

### Anhang A — „Neuen Service / neue Bestelloption anlegen"

Kochbuch, nicht Konzept. Jede Seite: Ausgangslage → nummerierte Schritte → kopierbarer Code
→ Probe („so siehst du, dass es geklappt hat").

| Seite | Inhalt | Code-Anker |
|---|---|---|
| A.1 Wie ein Service technisch entsteht | `ServiceTemplate.parameters` (JSON) → Formular zur Laufzeit → Validierung → Bestellung | `apps/catalog/models.py`, `apps/orders/forms.py` |
| A.2 Das Parameter-Schema | Feldreferenz: `key`, `label`, `type`, `required`, `default`, `group`, `display_order`, `constraints.options`, `depends_on`, `affects_options_of`, `tofu_variable_name` | `apps/catalog/services.py` (`SHARED_PARAMS`) |
| A.3 Rezept: neue Bestelloption | häufigster Fall, mit TDD-Reihenfolge (Test zuerst) | `apps/catalog/services.py`, Tests |
| A.4 Rezept: kompletter neuer Service | durchgehendes Beispiel bis Seed und Test | Katalog → Wizard → Approval → Provisioning |
| A.5 Abhängige Optionen & Validierung | `depends_on`/`affects_options_of`, Regeln | `core/domain/validators.py` |
| A.6 Häufige Fehler | Symptom → Ursache → Prüfbefehl | — |

## Erfolgskriterien

1. 23 Markdown-Dateien unter `cmp-docs/bookstack/`, jede mit `# Titel` als erster Zeile.
2. Keine MkDocs-only-Syntax (prüfbar: kein `!!!`, kein `{: `, kein ```` ```mermaid ```` in `bookstack/`).
3. Jede Tabellen-/Feld-/Endpunkt-Angabe ist am Code geprüft, nicht aus `cmp-docs` übernommen,
   wo `cmp-docs` selbst ungeprüft ist.
4. Anhang A ist ohne Vorwissen ausführbar: Wer A.3 folgt, hat am Ende eine neue Bestelloption
   im Formular — der Ablauf wird beim Schreiben real durchgespielt, nicht behauptet.
5. Keine Kennung, kein Klarname, kein interner Hostname im Ergebnis (`grep` vor dem Commit).

## Offene Punkte

- Import-Weg an der Bookstack-Instanz nachsehen (siehe oben) — danach ggf. Format nachziehen.
- Generator `cmp-docs → bookstack/` als späteres AP, sobald die Form steht.
- Kapitel 4–11 nach Freigabe des Pilots.
