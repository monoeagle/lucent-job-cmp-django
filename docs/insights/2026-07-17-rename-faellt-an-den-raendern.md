# Ein Projekt-Rename fällt an den Rändern, nicht im Kern

**Session 2026-07-17 — MPP Django → CloudMan Portal (CMP), v1.3.0.**

Die Angst vor einem projektweiten Rename (`mpp` → `cmp`, 168 Dateien) war größer
als die Sache. Der **Kern war trivial**: Der Django-Applikationscode ist über
`apps.*` und `config.*` organisiert — **kein einziger Python-Import hieß `mpp`**.
Der Ordner `mpp/` war nur eine Container-Hülle. Die vorab per `grep` erhobene
Inventur (statt geraten) hat das gezeigt und die ganze Planung entspannt.

Die Arbeit — und die Gefahr — lag ausschließlich an den **Rändern**, dort wo
`mpp` etwas anderes bedeutet als „dieses Projekt". Ein blindes `sed 's/mpp/cmp/'`
hätte jede dieser Stellen zerstört:

- **`mpp-TDD`** — das **Flask-Schwesterprojekt**. Steht in `CLAUDE.md`, in
  `scripts/fix_databases.sh` (das BEIDE Projekte anfasst: Django-DBs `cmp_django_*`
  vs. Flask-DBs `mpp_dev`/`mpp_test`), und in den **agent-memory-Pfaden** von
  `.claude/agents/*.md` (`…/lucent-app-mpp-TDD-Django/…`).
- **Repo-URLs** `github.com/monoeagle/…MPP_Django` — das Repo heißt real noch so
  (Redirect greift beim Push). URL umschreiben = tote Links.
- **`scripts/`** war ein **funktionaler Nachzügler**, den der Code-Rename zuerst
  übersah: `MPP_DIR="$PROJECT_DIR/mpp"` zeigte nach dem `git mv` ins Leere — also
  bereits *kaputt*, nicht nur „unschön".
- **Historische Docs** (Handoffs/Insights/Plans) — beschreiben korrekt die
  Vergangenheit; umschreiben = Historie fälschen. Nur die aktuelle Stand-Zeile ziehen.

**Technik:** `sed` mit **Masking** (`lucent-job-MPP_Django`→`@@R@@`→zurück), pro
Datei-Gruppe, danach `grep` gegen die geschützten Muster als Beleg — nicht die
Abwesenheit von Fehlern behaupten, sondern zeigen, dass `mpp-TDD` und die Repo-URLs
noch stehen.

## Zwei Nebenbefunde, beide „prüfen statt raten"

1. **Die versteckte zweite Ursache.** „Portal aus dem Subnetz nicht erreichbar"
   war nicht nur das fehlende Zertifikat. Am Code (`production.py`) gelesen:
   `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` waren **hart** `True` und
   `SECURE_SSL_REDIRECT` default `True` — über reines HTTP wäre der Login
   **unmöglich** gewesen (Cookies kommen nie an, Django redirectet auf ein 443,
   das es ohne Zert nicht gibt). Die naheliegende Erklärung („kein Zert") war nur
   die halbe Wahrheit; die andere Hälfte stand im Settings-Modul.

2. **Das Gate prüft nicht alles.** `R-VERSION` deckt 4 Versionsstellen ab —
   `seed.py` (`system_startup`) und die `todo-erledigt.md`-Stand-Zeile **nicht**.
   Beide hingen beim v1.3.0-Schnitt noch auf **v1.1.0** (waren schon bei v1.2.0
   liegengeblieben). Gefunden nur, weil die Versionierungs-Policy im Memory sie
   namentlich auflistet — das Gate hätte sie durchgewunken. Ein grünes Gate ist
   kein Beweis für vollständige Konsistenz, nur für die geprüften Regeln.

## Nachtrag (v1.3.1): selbst in die Falle getappt

Ironie zum Mitschreiben: Genau die oben beschriebene Ränder-Falle habe ich in
derselben Session **selbst** ausgelöst. Der `mpp→cmp`-Sweep änderte in
`oberflaeche.md` die Bild-**Referenzen** (`Screenshot_NN_cmp.png`), ließ aber die
**Dateien** (`_mpp.png`) unangetastet → 14 tote Bilder in der Doku-Galerie, erst
vom Nutzer bemerkt. Das Fazit oben („Referenz ohne referenzierte Datei") war also
keine Theorie. **Verschärfte Lehre:** Wenn ein Text-Sweep auf **Binärdateien** zeigt
(Bilder, Assets), reicht „kein altes Wort mehr im Text" nicht — es braucht einen
grep der **Referenz gegen die real existierende Datei**. Der Fix war ohnehin besser
als reines Umbenennen: die alten Screenshots trugen das Alt-Branding, also 14 neue
per Selenium — reproduzierbar als `tools/make_screenshots.py`.

Kleiner Zusatzbefund derselben Session: Das Installer-Panel hatte eine **feste**
Breite (46) und kürzte lange Pfade/URLs mit „..". Fester Rahmen + variabler Inhalt
= abgeschnittene Wahrheit; die Breite muss dem Inhalt folgen (Minimum statt Fixwert).
