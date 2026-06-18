# Insight 2026-06-19 — Produktions-Settings & VM-Deployment (online + offline)

## Kontext

Folge-Session nach dem Doku-Sync. Erst der ausstehende Commit (`.tools/` ignorieren,
ein Doku-Commit), dann auf Wunsch **AP-11 (Docker) zurückgestellt** zugunsten einer
**dezidierten VM-Installationsanleitung** — zunächst online (Rocky/AlmaLinux 9, Voll-Produktion),
danach eine zweite **air-gapped** Variante. Dabei fiel auf: es gab gar kein
Production-Settings-Modul, also musste das erst (TDD) entstehen.

## Nicht-offensichtliche Erkenntnisse

1. **`git rebase` scheitert an untracked Leftovers — `git merge` nicht.** Der Push wurde
   abgelehnt (Remote hatte `.claude/`-Untracking-Commits). `git rebase origin/main` brach
   sofort ab: Rebase **checkt zuerst `origin/main` aus**, das `mpp-docs/site/*` + die
   AppImage noch *tracked* — diese lagen aber als **untracked Dateien physisch auf der Disk**
   (wir hatten sie nur aus dem Tracking genommen, nicht gelöscht) → „würde überschrieben,
   Abbruch". `git merge origin/main` lief dagegen **konfliktfrei** durch: das Merge-Ergebnis
   *behält die Löschung* (unsere Seite), also muss git die untracked Dateien nie schreiben.
   **Regel:** Bei divergierter History + untracked Build-Artefakten, die man gerade untrackt
   hat, ist **Merge robuster als Rebase**. (`.gitignore`-Konflikt blieb aus, weil beide Seiten
   an *verschiedenen* Zeilen ergänzt hatten → Auto-Merge.)

2. **`manage.py check --deploy` = 0 Issues ist ein präzises Akzeptanzkriterium.** Die
   Hardening-Flags in `production.py` (`SECURE_SSL_REDIRECT`, HSTS-Trio, secure Cookies,
   `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_PROXY_SSL_HEADER`) sind genau die, die Django im
   Deploy-Check sonst anmahnt. Heißt: nicht „nach Gefühl härten", sondern `check --deploy`
   gegen das Modul laufen lassen, bis es schweigt — reproduzierbar im Test wie auf der VM.

3. **Settings-Modul lässt sich ohne `django.setup()` unit-testen.** `config.settings.production`
   per `importlib.import_module` (nach `sys.modules.pop`) frisch laden, Env via `monkeypatch`
   setzen, dann `DEBUG`/`SECRET_KEY`/`ALLOWED_HOSTS`/`DATABASES` asserten. `from .base import *`
   definiert nur Namen (keine Seiteneffekte), kollidiert also nicht mit den pytest-`testing`-
   Settings. So werden Produktions-Invarianten TDD-fähig, ohne eine echte DB/Env zu brauchen.

4. **Air-gapped killt Let's Encrypt — das ist der eigentliche Unterschied, nicht `dnf`/`pip`.**
   RPMs (`dnf download --resolve --alldeps`) und Wheels (`pip download` → `--no-index`) sind
   reine Beschaffungs-Umstellungen. Der konzeptionelle Bruch ist **TLS**: ACME braucht eine
   Challenge übers Internet → unmöglich offline. Lösung: internes CA-Zertifikat (empfohlen)
   oder self-signed + Client-Trust-Import. Zweitwichtigster Stolperstein: **Staging-Host muss
   OS/Arch/Python der Ziel-VM matchen**, sonst passen `psycopg-binary`-Wheels/RPMs nicht.

5. **`testCount` ist auto-generiert — Prosa anpassen + Build, nie hardcoden.**
   `tools/generate_project_activity.py::count_tests` schreibt `testCount` in
   `project-activity.json` beim Build. Workflow bei Testzahl-Änderung: die *Prosa-Stellen*
   (testing.md-Tabelle, ueberblick.md, arbeitspakete.md, neuer changelog-Eintrag) editieren,
   **historische** changelog-Einträge unangetastet lassen, dann `build_docs.py` → testCount
   springt selbst auf 238, `verify_docs.sh` R-STALE bestätigt.

## Repo-Hygiene-Befund

Im Remote-Push tauchte eine **85-MB-App-AppImage** auf (über GitHubs 50-MB-Empfehlung),
zusätzlich zur Docs-AppImage. Beide via `*.AppImage` + `git rm --cached` untrackt. **Offen:**
beide stecken weiter in der **History** (Klon lädt sie) — echtes Verschlanken bräuchte
`git filter-repo`/BFG + Force-Push. Außerdem meldet GitHub einen **Repo-Umzug**
(`MPP_Django` → `lucent-job-MPP_Django`); `origin` zeigt noch auf die alte URL (Redirect aktiv).

## Entscheidungen

- **AP-11 (Docker) zurückgestellt**, VM-Deployment (online + offline) vorgezogen.
- **Production-Settings env-basiert** (django-environ) statt Inline-Overrides — Projekt-Regel
  („Settings via django-environ") damit erstmals real umgesetzt.
- **Offline-TLS: internes/self-signed Zertifikat** als bewusster Ersatz für Let's Encrypt.
