# Session-Kennzahlen — MPP Django

Eine Zeile pro Session (Schema aus `session-handoff-kpi.pattern`, Python-adaptiert:
`flutter test` → `venv/bin/python3 -m pytest`, `pubspec`-Version → `changelog.md`/`zensical.toml`,
`flutter analyze` → `ruff`).

| # | Datum | Modell | Tokens gesamt | Commits (Merges) | Tests (von→bis, Δ) | Version (von→bis) | Subagent-Dispatches | Features / APs | Dateien angefasst | feat/fix-Commits | Review-Bugs | Notiz |
|---|-------|--------|---------------|------------------|--------------------|-------------------|---------------------|----------------|-------------------|------------------|-------------|-------|
| 1 | 2026-06-18 | Opus 4.8 (1M) | ~310k (31% von 1M) | 0 (0) | 228→230 (+2, Doku-Korrektur; Code unverändert) | v1.0.0→v1.0.0 | 0 | Doku-Sync + **App-Look-Umbau** (JS-Suite, Mermaid-Pipeline, Home-Layout) + **TDD-Gate** `verify_docs.sh` (12 Regeln, grün) + AP-Roadmap (Flowchart/Gantt) + §H-AppRun (Ephemeral-Port/Chromium) | 26 (ohne generiertes `site/`) | 0/0 | 9 (Doku-Drift: Tests/Services/E2E/DashboardService; +Pattern-Gaps: count_tests-venv-Bug, Google-Fonts-CDN, fixer AppImage-Port, xdg-open) | Große Session über 4 Nachrichten: Sync → App-Look → TDD-Gate → §H. „Doku fertig" jetzt = Gate exit 0. Noch nicht committet. |
| 2 | 2026-06-19 | Opus 4.8 (1M) | ~205k (21% von 1M, geschätzt) | 6 (1) | 230→238 (+8, echte Code-Tests: `production.py`) | v1.0.0→v1.0.0 (dated changelog, kein Bump) | 0 | **Production-Settings** `config.settings.production` (env/django-environ, `check --deploy` 0 Issues, TDD) + **VM-Deployment-Doku** online (`vm-installation.md`, Rocky 9 Voll-Prod) **+ offline/air-gapped** (`vm-installation-offline.md`, Bundle-Transport/`pip --no-index`/internes TLS) + Repo-Hygiene (AppImages untracked) | ~17 | 1/0 | 0 (kein formaler Review) | AP-11 (Docker) zurückgestellt. Push-Konflikt via **Merge** gelöst (Rebase scheiterte an untracked `site/`-Leftovers). Offen: Repo-Umzug-URL, 85-MB-AppImage in History. |

## Ableitbare KPIs (über die Zeilen — ab Session 2 sinnvoll)

- Tokens/Commit, Tests-Δ je 100k Tokens, Doc-vs-Code-LOC-Anteil
- Fix-vs-Feat-Quote (Rework-Anteil), Fang-Quote (Review-Bugs / (Review + Laufzeit-Bugs))
- Code-Health-Trend: `ruff`-Issues von→bis je Session
