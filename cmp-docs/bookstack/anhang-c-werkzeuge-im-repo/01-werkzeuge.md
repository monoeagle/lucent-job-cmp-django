# Anhang C — Werkzeuge im Repo

Diese Seite listet die ausführbaren Werkzeuge im Repo — was sie tun, wie man sie wirklich
aufruft (nicht wie man es vermuten würde) und wann man sie braucht. Alle Aufrufformen sind
am Skript selbst nachgelesen oder mit `--help`/`--version` real ausgeführt.

## 1. Ziel des Kapitels

Wer im CMP entwickelt, soll hier nachschlagen können, welches Skript für Serve/Test/Release/
Doku zuständig ist, ohne die Skripte selbst lesen zu müssen — inklusive der einen Falle, die
in diesem Repo alle Werkzeug-Aufrufe betrifft: kaputte venv-Konsolen-Skripte.

## 2. Die venv-Falle: Interpreter statt Konsolen-Skript

Beide venvs (`venv/` fürs Projekt, `cmp-docs/.venv-docs/` für die Doku-Toolchain) wurden unter
einem inzwischen umbenannten Verzeichnispfad erzeugt. Ihre Konsolen-Skripte tragen deshalb eine
Shebang-Zeile auf den alten Pfad und laufen ins Leere — real geprüft:

```
$ head -1 venv/bin/pip
#!/home/…/lucent-app-mpp-TDD-Django/venv/bin/python3        (alter Pfad, existiert nicht mehr)
$ venv/bin/pip --version
bash: venv/bin/pip: Kann nicht ausführen. Datei nicht gefunden.
```

Der Interpreter selbst ist ein normaler Symlink und bleibt davon unberührt. Deshalb gilt für
**jedes** Werkzeug unten: über den Interpreter aufrufen, nicht über das Konsolen-Skript.

| Statt (bricht) | Aufruf (funktioniert, real geprüft) |
|---|---|
| `venv/bin/pip …` | `venv/bin/python3 -m pip …` |
| `venv/bin/pytest` | `venv/bin/python3 -m pytest` |
| `cmp-docs/.venv-docs/bin/zensical …` | `cmp-docs/.venv-docs/bin/python3 -m zensical …` |

Frisch verifiziert (2026-07-22): `venv/bin/python3 -m pip --version` → `pip 24.0 …`;
`cmp-docs/.venv-docs/bin/python3 -m zensical --version` → `0.0.31`. `build_docs.py` selbst
ruft intern bereits `sys.executable -m zensical` auf (`cmp-docs/build_docs.py:156`) und ist
von der Falle deshalb nicht betroffen.

## 3. run.sh (Projektwurzel) — Release- und Docs-Auslieferung

Aufruf: `./run.sh <kommando>` (Default ohne Argument: `serve`). Alle Kommandos aus dem
Dispatch am Skriptende (`run.sh:400-409`):

| Kommando | Zweck | Beleg |
|---|---|---|
| `serve` | Dev-Server auf Port 8000, aktiviert `venv/` und startet `manage.py runserver` | `run.sh:117-126` |
| `appimage-build` | Baut eine Linux-AppImage der Anwendung (bundelt Python standalone) | `run.sh:128-223` |
| `docs-appimage` | Baut eine AppImage der gebauten Doku-Site (braucht vorher `cmp-docs/site/`) | `run.sh:225ff.` |
| `docs-zip` | Packt `cmp-docs/site/` als Windows-taugliches HTML-ZIP nach `release/`, schließt `intern/` aus | `run.sh:360-395` |
| `release` | Lädt bei Bedarf die Offline-Wheelhouse (`wheels/`) und baut das Offline-Release-Bundle via `tools/build_release.py` | `run.sh:343-355` |

Die Versionsnummer wird nicht hartkodiert, sondern aus `lucent-hub.yml` gelesen
(`run.sh:14-16`) — dieselbe Quelle wie `tools/build_release.py`.

## 4. Entwicklungs-Launcher unter scripts/

Zusätzlich zum Root-`run.sh` liegen unter `scripts/` zwei weitere, unabhängige Launcher —
beide für den lokalen Entwicklungsalltag, nicht für Release/Auslieferung:

- **`scripts/run.sh`** — interaktives Menü (`./scripts/run.sh`, Fallback ohne Terminal nicht
  vorgesehen). Menüpunkte 1–8: Setup, Server starten, Tests (alle/unit/integration/e2e),
  Migrationen (migrate/makemigrations/showmigrations), **Demo-Daten laden** (`manage.py seed`,
  `scripts/run.sh:339`), Django-Shell, Django-Check, Tailwind-CSS-Build (`scripts/run.sh:291-439`).
- **`scripts/cmp.sh`** — zweiter, aufgabenorientierter Launcher („Unified menu for starting
  backend, CSS watch, docs, or all", `scripts/cmp.sh:1-6`), an das Flask-Schwesterprojekt
  angelehnt.
- **`scripts/fix_databases.sh`** — legt die PostgreSQL-Rolle `cmp` und die DBs
  `cmp_django_dev`/`cmp_django_test` neu an; braucht `sudo` (PostgreSQL-Superuser-Operationen,
  `scripts/fix_databases.sh:1-9`).

Drei Skripte mit ähnlichem Zweck sind eine reale Unschärfe im Repo — bei Unklarheit ist
`scripts/run.sh` das umfassendere Menü.

## 5. Seed — Demo-Daten laden

Kein eigenständiges Skript, sondern ein Django-Management-Kommando:
`cmp/apps/accounts/management/commands/seed.py`. Aufruf von der Projektwurzel:

```bash
venv/bin/python3 cmp/manage.py seed
```

(`manage.py` setzt `config.settings.development` als Default, wenn `DJANGO_SETTINGS_MODULE`
nicht gesetzt ist — `cmp/manage.py:7`; mit `--help` real geprüft, das Kommando ist unter
diesem Aufruf erreichbar.) Es seedet Nutzer, Service-Templates, Genehmigungsregeln,
Bestellungen, Audit-Logs und Benachrichtigungen in einem Lauf (`seed.py:17-23`) — nur beim
allerersten Lauf vollständig, danach nur noch die Templates, falls sie fehlen. Daneben
existiert `seed_users.py` im selben `commands/`-Ordner als schmaleres Kommando nur für
Nutzer-Stammdaten.

## 6. Doku-Werkzeuge unter cmp-docs/

Die Doku-Toolchain lebt in einem eigenen venv (`cmp-docs/.venv-docs/`), unabhängig vom
Projekt-venv:

| Werkzeug | Aufruf | Zweck |
|---|---|---|
| `run_cmp_docs.sh` | `./cmp-docs/run_cmp_docs.sh [--port=P\|--build\|--check\|--clean]` | legt `.venv-docs` an, installiert Zensical hinein, startet Live-Server oder Build (`run_cmp_docs.sh:1-13`) |
| `build_docs.py` | `.venv-docs/bin/python3 cmp-docs/build_docs.py [--serve\|--check\|--no-mermaid\|--no-activity\|--ci]` | volle Pipeline: Mermaid extrahieren → rendern → Activity-JSON → Zensical-Build nach `site/` (`build_docs.py:10-18`) |
| `tools/extract_mermaid_blocks.py` | `.venv-docs/bin/python3 cmp-docs/tools/extract_mermaid_blocks.py` | zieht Mermaid-Codeblöcke aus `.md` nach `mermaid-sources/*.mmd` und ersetzt sie durch eine Bild-Referenz (`extract_mermaid_blocks.py:1-13`) — läuft normalerweise automatisch als erster Schritt von `build_docs.py` |
| `tools/render_mermaid.sh` | `./cmp-docs/tools/render_mermaid.sh [name-praefix]` | rendert `.mmd` → `.svg` via `npx @mermaid-js/mermaid-cli` (Node, kein Python-venv); Gantt-Diagramme bekommen mehr Breite (`render_mermaid.sh:1-30`) |
| `tools/generate_project_activity.py` | `.venv-docs/bin/python3 cmp-docs/tools/generate_project_activity.py` | liest `git log`, schreibt Tages-Aggregate für die Aktivitäts-Heatmap-Seite (`generate_project_activity.py:1-16`) |
| `verify_docs.sh` | `./cmp-docs/verify_docs.sh [--no-build]` | **Doku-Abnahme-Gate**: 12 Regeln (R-BUILD, R-PFLICHT, R-VERSION, R-APPLOOK, R-HOME, R-DIAGRAMME, R-NO-PLACEHOLDER, R-NO-CDN, R-STALE, R-DOCS-ZIP, R-AP-SYNC, R-APPRUN — `verify_docs.sh:39-249`); exit 0 nur bei null Fehlschlägen |
| `deploy_ghpages.sh` | `./cmp-docs/deploy_ghpages.sh [--no-build]` | baut `site/` und pusht es in den `gh-pages`-Branch über einen temporären Git-Worktree (`deploy_ghpages.sh:1-13`) |

`build_docs.py` selbst ruft die drei Tool-Skripte bei Bedarf als Unterschritte auf
(`cmp-docs/build_docs.py:114-145`) — der eigenständige Aufruf ist nur für einen gezielten
Einzelschritt nötig (z. B. nur ein Diagramm neu rendern).

## 7. deploy/install.sh — Ziel-VM-Installation

Aufruf **auf der Ziel-VM**, im entpackten Release-Bundle, als root:

```bash
sudo ./deploy/install.sh                 # Menü (am Terminal)
sudo ./deploy/install.sh --install       # direkt installieren, ohne Menü
sudo ./deploy/install.sh --check         # nur prüfen, ändert nichts
sudo ./deploy/install.sh --restart       # Dienste neu starten
```

(`deploy/install.sh:9-13`, real gelesen — nicht auf einer VM ausgeführt, da dieses Repo kein
Zielsystem ist). Zusatzoptionen: `--with-packages` (Systempakete aus dem Netz nachladen,
bewusst kein Default, `deploy/install.sh:16-17`), `--skip-nginx` (Reverse-Proxy/TLS
überspringen, `deploy/install.sh:18`). Logik liegt in `deploy/lib.sh` (System-Erkennung,
PostgreSQL-Variante, systemd-Units, Zertifikat), das Prüf-Panel in `deploy/ui.sh` — beide
sind unit-getestet (`tests/unit/test_install_*.py`, sieben Dateien). Näher erklärt in
Kapitel 11.2 (ADR-0001).

## 8. Zusammenfassung

Für den Alltag reichen drei Einstiegspunkte: `scripts/run.sh` (lokale Entwicklung: Server,
Tests, Migrationen, Seed), `cmp-docs/run_cmp_docs.sh` bzw. `build_docs.py` (Doku bauen/
prüfen) und `./run.sh <kommando>` (Release, AppImage, Docs-ZIP). Für die Ziel-VM kommt
`deploy/install.sh` hinzu. Die durchgängige Regel dabei: Werkzeuge über den
venv-Interpreter aufrufen (`venv/bin/python3 -m …`), nicht über die kaputten
Konsolen-Skripte — das gilt projektweit, nicht nur für einzelne Tools.

> Quelle: `run.sh:14-16,117-223,225,343-409`, `scripts/run.sh:291-439`, `scripts/cmp.sh:1-6`, `scripts/fix_databases.sh:1-9`, `cmp/apps/accounts/management/commands/seed.py:1-23`, `cmp/manage.py:7`, `cmp-docs/run_cmp_docs.sh:1-13`, `cmp-docs/build_docs.py:10-18,32,114-156`, `cmp-docs/tools/extract_mermaid_blocks.py:1-13`, `cmp-docs/tools/render_mermaid.sh:1-30`, `cmp-docs/tools/generate_project_activity.py:1-16`, `cmp-docs/verify_docs.sh:39-249`, `cmp-docs/deploy_ghpages.sh:1-13`, `deploy/install.sh:9-18` — am Code geprüft 2026-07-22
