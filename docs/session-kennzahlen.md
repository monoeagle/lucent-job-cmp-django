# Session-Kennzahlen — MPP Django

Eine Zeile pro Session (Schema aus `session-handoff-kpi.pattern`, Python-adaptiert:
`flutter test` → `venv/bin/python3 -m pytest`, `pubspec`-Version → `changelog.md`/`zensical.toml`,
`flutter analyze` → `ruff`).

| # | Datum | Modell | Tokens gesamt | Commits (Merges) | Tests (von→bis, Δ) | Version (von→bis) | Subagent-Dispatches | Features / APs | Dateien angefasst | feat/fix-Commits | Review-Bugs | Notiz |
|---|-------|--------|---------------|------------------|--------------------|-------------------|---------------------|----------------|-------------------|------------------|-------------|-------|
| 1 | 2026-06-18 | Opus 4.8 (1M) | ~310k (31% von 1M) | 0 (0) | 228→230 (+2, Doku-Korrektur; Code unverändert) | v1.0.0→v1.0.0 | 0 | Doku-Sync + **App-Look-Umbau** (JS-Suite, Mermaid-Pipeline, Home-Layout) + **TDD-Gate** `verify_docs.sh` (12 Regeln, grün) + AP-Roadmap (Flowchart/Gantt) + §H-AppRun (Ephemeral-Port/Chromium) | 26 (ohne generiertes `site/`) | 0/0 | 9 (Doku-Drift: Tests/Services/E2E/DashboardService; +Pattern-Gaps: count_tests-venv-Bug, Google-Fonts-CDN, fixer AppImage-Port, xdg-open) | Große Session über 4 Nachrichten: Sync → App-Look → TDD-Gate → §H. „Doku fertig" jetzt = Gate exit 0. Noch nicht committet. |

## Ableitbare KPIs (über die Zeilen — ab Session 2 sinnvoll)

- Tokens/Commit, Tests-Δ je 100k Tokens, Doc-vs-Code-LOC-Anteil
- Fix-vs-Feat-Quote (Rework-Anteil), Fang-Quote (Review-Bugs / (Review + Laufzeit-Bugs))
- Code-Health-Trend: `ruff`-Issues von→bis je Session
