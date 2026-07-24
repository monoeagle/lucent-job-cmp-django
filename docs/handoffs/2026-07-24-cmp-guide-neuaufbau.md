# Handoff — Neuer CMP-Guide (`docs/azubi-guide/`) + Doppel-Build

**Datum:** 2026-07-24 · **Stand:** vollständig gebaut, code-verifiziert gegen v1.5.0

## Was ist das

Ein **neuer, eigenständiger Onboarding-/Referenz-Guide** unter `docs/azubi-guide/`,
bewusst **neben** der bestehenden `cmp-docs/`-Doku. Ziel: einem Einsteiger CMP von
Grund auf verständlich machen — mit Diagrammen (Mermaid) und klarer Progression.

**18 Dateien:** `README.md` (Lernpfad) + Kapitel `00`–`13` + Anhänge `A`, `B`, `C`.

| # | Kapitel | Diagramm | Besonderheit |
|---|---------|----------|--------------|
| 00 | Willkommen | – | |
| 01 | Das große Bild | Kontext (flowchart) | |
| 02 | Ziele & Anforderungen | – | **SSR-first**, Soll/Ist |
| 03 | Die Fachdomäne | ER-Diagramm | + CMDB/Kontext |
| 04 | Rollen & Rechte | – | Mixin-Erklärung, **AD-Ausblick (geplant)** |
| 05 | Der Bestell-Lebenszyklus | State-Diagramm | Vorbild-Kapitel; 3 ⚑ Befunde |
| 06 | Architektur | High-Level + Schichten | 10 Apps, Dependency-Matrix |
| 07 | Async & Provisioning | Sequenz-Diagramm | ⚑ Idempotenz |
| 08 | Frontend: HTMX & DaisyUI | – | ⚑ package.json-Pfade (AP-23) |
| 09 | Setup lokal | – | Troubleshooting, keepdb |
| 10 | So arbeiten wir | – | TDD, Konventionen, **CI/CD-Abschnitt** |
| 11 | Dein erster Beitrag | – | TDD-Walkthrough |
| 12 | Wie es in Produktion läuft | Topologie + Promotion | Umgebungen, Checkliste, Logging/Monitoring, Backup |
| 13 | Rundgang durch die Oberfläche | – | 14 Screenshots aus `cmp-docs/.../screenshots/` |
| A | Glossar · B | Spickzettel · C | Einen neuen Service anlegen (Katalog-Template + Provisioning-Client) |

## Harte Vorgaben / Design-Entscheidungen (unbedingt beibehalten)

- **SSR-first, KEIN API-First-Vergleich.** Der Guide beschreibt CMP als server-gerendertes
  Django-+-HTMX-Portal. Keine Vergleichstabellen zum Schwesterprojekt, kein „mpp-TDD".
- **Kein Gendern** — generisches Maskulinum (Nutzer, Entwickler, …). Keine „:innen"/Binnen-I.
- **Code-first / Ehrlichkeit:** Diagramme + Aussagen zeigen den **Ist-Zustand (v1.5.0)**.
  Geplantes steht als **„Soll/Ausblick"** im Text, nie im Diagramm. Beispiel: die
  **Modifier-Rolle** und **AD-Anbindung** existieren im Code nicht → nur als Ausblick in
  Kap. 04; Diagramme werden erst aktualisiert, wenn der Code sie hergibt.
- **⚑ Befunde** = echte offene Code-Stellen, verifiziert: Approval-Race (kein
  `select_for_update`), `complete_dispatch()` nicht idempotent (Celery at-least-once),
  partielles Provisioning ohne Kompensation, nur `Order.status` ist echte Enum,
  `package.json`-`mpp/`-Pfade (bekannt, AP-23).
- **Veraltete Referenz-Claims verworfen:** „Bestellkette nicht verdrahtet" (in v1.5.0
  verdrahtet), „3 Templates" (es sind 2), feste Testzahlen.

## Zwei Ausgaben aus einer Quelle — der Build

Werkzeug: **`docs/azubi-guide/_build/`** (siehe dessen `README.md`).

```bash
cd docs/azubi-guide/_build
npm install marked @mermaid-js/mermaid-cli   # einmalig
node build.js
```

- **`_build/build/html/`** — HTML-Vorschau: Mermaid als SVG (hell/dunkel), **Lightbox**
  (Galerie mit ‹ ›, Bildunterschrift), **linke sticky Kapitel-Navigation**, **obere +
  untere** Vor/Zurück-Leiste, zentrierte Bilder, kein horizontaler Scroll
  (`overflow-x:clip`), Tabellen mit `break-word`.
- **`_build/build/bookstack/`** — **BookStack-Import-Ziel**: Mermaid → PNG (`images/`),
  `<details>` → normale Abschnitte, Footer-Nav entfernt, `.md`-Links zu Klartext.
  Import-Hinweise in `_IMPORT-HINWEIS.md` (wird mitgebaut).

> Wichtig: Die ```` ```mermaid ````-Quellen bleiben in den `.md` (GitHub/VS-Code rendern
> sie). Der Build erzeugt daraus die PNGs für BookStack. Lightbox/`<details>`/Mermaid sind
> **HTML-only**, weil das Ziel-BookStack **keine Custom-Head-Erweiterungen** erlaubt.

## Offene Punkte / mögliche nächste Schritte

- **BookStack-Import** ist noch nicht durchgeführt (Artefakte in `_build/build/bookstack/`
  sind bereit; Bilder müssen beim Import hochgeladen werden).
- Bewusst **nicht** übernommen (Legacy/API-First, passt nicht zum Single-VM-Zielbild):
  HA/Skalierung/K8s, OpenTofu/GitLab-Direktpipeline, AWS, Prometheus/Grafana-Stack.
- Roadmap-Themen, im Guide als „geplant" markiert: CI-Pipeline (empfohlen, nicht gebaut),
  echtes Provisioning-Backend (AP-20), Django Channels (AP-12), strukturiertes Logging
  (AP-14), AD/LDAP + Modifier-Rolle (Richtung AP-21), Installer-Uninstall (AP-16),
  automatisiertes Backup.
