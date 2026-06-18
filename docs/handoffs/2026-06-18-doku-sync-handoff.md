# Handoff 2026-06-18 — Doku-Sync

## Stand

- **Test-Umgebung wiederhergestellt:** Django 6.0.3 + Test-Deps offline aus `.wheels/` ins
  projekt-eigene `venv` installiert. Aufruf immer über `venv/bin/python3 -m …` (Console-Scripts
  haben kaputte Shebangs vom alten Pfad).
- **Suite verifiziert:** `venv/bin/python3 -m pytest` → **230 passed, 0 errors** (Unit 129 ·
  Integration 97 · E2E 4).
- **Doku auf Ist-Stand gezogen** (7 Dateien, noch **nicht committet**):
  `todos.md`, `mpp-docs/docs/entwicklung/changelog.md` + `testing.md`,
  `mpp-docs/docs/grundlagen/installation.md`, `mpp-docs/docs/index.md`,
  `mpp-docs/docs/referenz/services.md`, `mpp-docs/zensical.toml`.
  Tests 228→230, Services 9→10 (`DashboardService` ergänzt), E2E ~28→4, Version in
  `site_description` ergänzt (v1.0.0), `todos.md` an HTMX/allauth-Architektur angeglichen.
- **Insight:** `docs/insights/2026-06-18-doku-sync.md`.
- **KPI-Matrix:** `docs/session-kennzahlen.md` (Zeile #1 angelegt).

## Nächster Schritt

1. Docs-Site zweistufig bauen: `cd mpp-docs && bash run_mpp_docs.sh --build`, dann
   `cd .. && ./run.sh docs-appimage` → `build/Lucent-MPP-Django-Docs-1.0.0-x86_64.AppImage`.
2. Committen (vom Nutzer noch zu bestätigen). **Achtung — Abweichung vom Pattern §D:**
   `.gitignore` ignoriert nur `/site` (Repo-Root), **nicht** `mpp-docs/site/`; `release/` ist
   ebenfalls getrackt. Ein Commit zieht daher die generierten HTMLs **und** die 1,1-MB-AppImage-
   Binary mit. Entscheidung offen: entweder so committen (wie bisher im Repo) oder
   `mpp-docs/site/` + `release/` aus dem Tracking nehmen und ignorieren (pattern-konform).

## Offene Punkte

- **Generate im Git:** `mpp-docs/site/` + `release/*.AppImage` sind versioniert (gegen Pattern §D).
  Aufräumen würde `git rm --cached` + `.gitignore`-Einträge erfordern — bewusst dem Nutzer überlassen.

- **Docker-Setup** ist das einzige offene Infrastruktur-AP (`todos.md`).
- venv-Shebangs zeigen auf alten Pfad — ein `python3 -m venv --upgrade`/Neubau würde die
  Console-Scripts (`pip`, `pytest`, `celery`) reparieren (aktuell via `-m` umgangen).
- factory_boy wirft DeprecationWarnings (`_after_postgeneration` / `skip_postgeneration_save`) —
  funktional unkritisch, vor factory_boy-Major aufräumen.
