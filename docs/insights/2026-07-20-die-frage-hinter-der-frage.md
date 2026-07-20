# Die Frage hinter der Frage — und drei Annahmen, die beim Prüfen fielen

**Session 7 · 2026-07-20 · v1.3.1 → v1.3.2**

## Der Auslöser

„Bitte einmal die Doku starten im Chrome." Danach: „haben wir kein Mermaid wo wir die
Zusammenhänge sehen zwischen redis, gunicorn, celery, postgresql?"

Die ehrliche Antwort war **nein** — und zwar aus einem Grund, der erst beim Nachsehen
sichtbar wurde. Es gab ein Architektur-Diagramm, aber das beantwortet „**was ruft was**":
UI → Web-Layer → Service-Layer → Daten-Layer. Darin kommen nginx und gunicorn nicht vor,
weil sie keine Business-Logik aufrufen — sie *hosten* den Web-Layer. Redis und Celery
waren zu einem einzigen Kasten „Celery + Redis" verdichtet.

Die Frage „wo ist gunicorn?" war also kein fehlendes Detail, sondern eine **fehlende
Sicht**. Ein logisches Schichtenbild kann die Betriebsfrage prinzipiell nicht beantworten.
Die Lösung war nicht, das bestehende Diagramm zu erweitern (das hätte beide Sichten
verwaschen), sondern eine zweite Seite mit einer klar anderen Frage.

**Merkmal für „fehlende Sicht" statt „fehlendes Detail":** Wenn die naheliegende Ergänzung
das bestehende Artefakt unschärfer machen würde, ist es eine eigene Sicht.

## Drei Annahmen, die beim Prüfen gefallen sind

Alle drei klangen plausibel. Alle drei waren falsch. Alle drei kosteten je einen Befehl.

### 1. „v1.3.1 ist nicht getaggt"

`git tag --sort=-v:refname | head -3` zeigte `v1.3.0` als neuesten Tag, obwohl ein
Commit `release: v1.3.1` existierte. Daraus wurde die Aussage „vorbestehende Lücke,
Tag fehlt" — und ein Angebot, ihn nachzuziehen.

Real: Der Tag existierte **remote**. Das lokale Repo hatte die Tags nur nie geholt. Der
Push lief prompt auf „Tag existiert bereits im Remote-Repository".

Der Fehler ist nicht der fehlende Fetch, sondern der **Schluss von der lokalen Sicht auf
den Zustand der Welt**. `git tag` beantwortet „welche Tags kenne ich", nicht „welche Tags
gibt es". Bei verteilten Systemen ist die lokale Sicht per Konstruktion veraltet.

### 2. „R-STALE scheitert an den kaputten venv-Shebangs"

Das Doku-Gate meldete „Testzahl nicht ermittelbar (pytest --collect-only)". Im
Projekt-Memory steht ein Eintrag über kaputte venv-Shebangs nach einem Verschieben.
Passt perfekt — also zweimal so behauptet und ein Fix angeboten.

Real: Die Regel rief längst korrekt `venv/bin/python3 -m pytest` auf. Sie lief nur mit
`cwd=cmp-docs`, und von dort findet pytest die `pytest.ini` im Projekt-Root nicht:
`no tests collected`. Ein `cd "$PROJECT_DIR"` reichte.

Das Gefährliche war die **Passgenauigkeit der falschen Erklärung**. Ein vorhandener
Memory-Eintrag lieferte eine Ursache, die das Symptom vollständig erklärte — deshalb
wurde nicht weitergesucht. Ein zutreffend klingender Kontext ist kein Beleg.

### 3. „Rolle `admin` und `is_staff` werden getrennt vergeben"

In `cmp/apps/accounts/models.py` gibt es keine Kopplung — also in die Doku geschrieben,
Django Admin hänge nicht an der CMP-Rolle.

Real: `AccountService.seed_stub_users()` setzt `is_staff` sehr wohl aus der Rolle
(`role in (ADMIN, SUPERADMIN)`). Die Aussage stimmt nur für **manuell angelegte** Nutzer.
Geprüft wurde eine Datei, behauptet wurde etwas über das System.

## Was der Nutzer korrigiert hat

Zwischendurch entstand ein Missverständnis: Auf „wenn wir in der Produktion nginx,
gunicorn etc. brauchen, dann soll das auch in der Testumgebung so aufgebaut werden"
folgte eine Rückfrage nach Podman/Quadlets, lokaler Installation und Dev-Loop-Strategie —
inklusive `AskUserQuestion` mit vier Optionen.

Gemeint war etwas viel Einfacheres: *„Das Release bringe ich zur TestVM und installiere
es dort. Von einer Testmaschine aus will ich dann dieses Portal aufrufen."*

Es war keine Architekturfrage, sondern eine **Zugriffsfrage**. Und die Antwort existierte
bereits vollständig: `install.sh` ist dasselbe Skript für Test und Produktion, der einzige
Unterschied ist der automatisch gewählte TLS-Modus. Zu bauen war nichts — nur zu erklären,
dass der Aufruf über den **FQDN** gehen muss (`ALLOWED_HOSTS` enthält nur ihn, IP-Aufruf
endet in `DisallowedHost`) und dass ohne DNS ein hosts-Eintrag nötig ist.

**Muster:** Eine Frage, die nach einer großen Architekturentscheidung klingt, ist oft eine
kleine Betriebsfrage. Vor dem Aufspannen von Optionen prüfen, ob die Antwort schon im Repo
liegt.

## Ein Fund, der fast durchgerutscht wäre

`git status` zeigte vor dem Commit `D cmp-docs/site/.nojekyll`. Der Build löscht `site/`
komplett (`shutil.rmtree`) und riss die getrackte Datei jedes Mal mit — Commit `cb4095e`
hatte sie schon einmal von Hand zurückgeholt.

Ohne `.nojekyll` ignoriert GitHub Pages Unterstrich-Verzeichnisse. `site/_data/project-activity.json`
wäre auf gh-pages tot gewesen, die Aktivitäts-Heatmap leer — **ohne Fehlermeldung**.
Der Deploy hätte funktioniert und die Seite wäre still kaputt gewesen.

Gefunden nur, weil die Löschung im `git status` auffiel. Jetzt legt `step_zensical_build()`
die Datei selbst wieder an. Die eigentliche Lehre: Eine wiederkehrende manuelle Reparatur
(hier: zum zweiten Mal) ist ein Symptom, kein Arbeitsschritt.

## Die Ränder-Falle, erneut

Der Mermaid-Extractor erzeugt `src="../images/mermaid/..."`. Für Unterseiten ist das
falsch — gerenderte URLs sind Verzeichnisse (`/betrieb/laufzeit-topologie/`), es braucht
`../../images/`. Exakt derselbe Fehlertyp wie im v1.3.1-Nachtrag, und exakt die Stelle,
die ein Memory-Eintrag („Doku im Browser verifizieren") bereits benennt.

Gefunden durch Vergleich mit einer bestehenden Seite gleicher Tiefe (`arbeitspakete.md`),
belegt durch `curl` gegen die gerenderte Seite. Ein Build-Erfolg beweist nichts über
Bildpfade — nur ein Abruf tut das.

## Ergebnis

- Neue Seite **Betrieb → Laufzeit-Topologie**: 3 Diagramme (Produktion, Einstiegspunkte
  nach Rolle, Entwicklung), Ports-Tabelle, Dienst-Aufgaben mit Begründung, TLS-Modus-Matrix,
  Client-Zugriff (FQDN/hosts/CSRF).
- **v1.3.2** — reines Doku-Release, App-Artefakt von v1.3.1 bleibt gültig.
- Zwei Build-Fixes: `.nojekyll` überlebt den Build, R-STALE prüft wieder wirklich.
- **Doku-Gate erstmals wieder 12/12 grün** (R-STALE war zuvor dauerhaft rot).
- Querverweise Architektur → Laufzeit-Topologie; **nicht** auf der Startseite, weil
  R-HOME dort Fließtext verbietet — vor dem Eingriff geprüft, nicht danach.

## Übertragbar

1. **Fehlende Sicht ≠ fehlendes Detail.** Wenn die Ergänzung das bestehende Artefakt
   unschärfer machen würde, gehört sie auf eine eigene Seite.
2. **Die lokale Sicht ist nicht die Welt.** Vor Aussagen über Remote-Zustände fetchen.
3. **Eine passende Erklärung ist kein Beleg.** Gerade wenn ein Memory-Eintrag das Symptom
   erklärt, einmal messen — Passgenauigkeit verhindert die Suche nach der echten Ursache.
4. **Eine Datei geprüft ≠ das System geprüft.** Bei „X hängt nicht an Y" auch Seeds,
   Services und Management-Commands durchsuchen.
5. **Wiederholte Handreparatur ist ein Bug.** Beim zweiten Mal das Werkzeug reparieren.
6. **Große Frage, kleine Antwort.** Vor dem Aufspannen von Optionen prüfen, ob die Antwort
   schon im Repo steht.
