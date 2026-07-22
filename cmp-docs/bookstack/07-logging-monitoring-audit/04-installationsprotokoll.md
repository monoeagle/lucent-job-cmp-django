# Installationsprotokoll

`deploy/install.sh` gibt seinen Ablauf ausführlich auf dem Terminal aus, legt
aber aktuell **keine** Protokolldatei an. Diese Seite belegt Format und
Umfang der Terminal-Ausgabe und benennt die fehlende Persistierung als
offenes Arbeitspaket.

## 1. Ziel des Kapitels

Wer nach einer Log-Datei der Installation sucht (`/var/log/...`,
`INSTALL-REPORT`), soll hier den geprüften Befund finden: Es gibt keine.
Alles, was der Installer meldet, geht ausschließlich an das Terminal, in dem
er läuft. Diese Seite zeigt, welches Format das ist, und was stattdessen
geplant, aber noch nicht gebaut ist.

## 2. Format der Terminal-Ausgabe

Vier Ausgabefunktionen bilden das gesamte „Protokoll" des Installers
(`deploy/install.sh:53-57`):

| Funktion | Zeile | Verhalten |
|---|---|---|
| `ok()` | `deploy/install.sh:53` | `echo` mit grünem `✓`-Präfix |
| `info()` | `deploy/install.sh:54` | `echo` mit cyanem `→`-Präfix |
| `warn()` | `deploy/install.sh:55` | `echo` mit gelbem `⚠`-Präfix |
| `die()` | `deploy/install.sh:56` | `echo … >&2` mit rotem `✗`-Präfix, danach `exit 1` |
| `hdr()` | `deploy/install.sh:57` | `echo` einer Abschnittsüberschrift zwischen `═══`-Trennern |

Alle fünf schreiben ausschließlich mit `echo` — auf stdout (bzw. `die()` auf
stderr). Keine der Funktionen öffnet eine Datei, keine leitet nach
`/var/log/` um. Das Skript setzt zudem `set -euo pipefail`
(`deploy/install.sh:35`), sodass ein Fehler in einem Schritt die Ausführung
sofort mit dem entsprechenden `die()`- bzw. Nicht-Null-Exit-Code beendet.

## 3. Gliederung der Ausgabe: acht nummerierte Phasen

Eine Installation (`aktion_installieren`) gliedert sich über `hdr()`-Aufrufe
in acht nummerierte Phasen plus Preflight und Abschluss
(`deploy/install.sh`, Zeilen wie angegeben):

| Zeile | Phase |
|---|---|
| `135` | `0/8  Preflight` |
| `183` | `1/8  Konfiguration` |
| `212` | `2/8  Service-User + App-Code` |
| `227` | `3/8  venv + Wheels (offline, --no-index)` |
| `235` | `4/8  PostgreSQL-Datenbank` |
| `242` | `5/8  Umgebungsdatei $ENV_FILE` |
| `258` | `6/8  Migrationen, Static, Superuser` |
| `280` | `7/8  systemd (gunicorn + Celery)` |
| `293` | `8/8  nginx + TLS` |
| `318` | `FERTIG` |

Innerhalb jeder Phase melden `ok()`/`info()`/`warn()` die Einzelschritte —
das ergibt eine lesbare, aber ausschließlich flüchtige Terminal-Ausgabe.

## 4. Der Prüfbereich (`--check`) folgt demselben Muster

Auch `aktion_pruefen()` (`deploy/install.sh:116-123`, siehe Kapitel 7.3)
gibt ihr Ergebnis nur über `cmp_ui_render` auf dem Terminal aus und meldet
sich zusätzlich über den Exit-Code (0 bei „alles grün", sonst 1) — auch das
ohne jede Datei-Persistierung.

## 5. Was tatsächlich fehlt: keine persistierte Log-Datei

Gezielte Suche über alle drei Installer-Dateien, Stand 2026-07-22:

```
grep -n "/var/log\|INSTALL-REPORT\|tee -a\|logfile" deploy/install.sh deploy/lib.sh deploy/ui.sh
```

Der einzige Treffer außerhalb der bereits in Kapitel 7.3 behandelten
gunicorn-Flags (`--access-logfile -`) ist ein `>>` zum Anhängen an die
Umgebungsdatei (`deploy/install.sh:253`, `cmp_env_security_lines ... >>
"$ENV_FILE"`) — das ist Konfiguration, kein Protokoll. Es gibt keinen Treffer
für `/var/log`, keinen für einen Bericht, keinen für ein dauerhaftes
Log-File. Wer die Installation nachvollziehen will, ist auf die Terminal-
Sitzung angewiesen, in der sie lief — schließt sich das Terminal, ist der
Ablauf nicht mehr rekonstruierbar. Auch das Menü (`deploy/install.sh:329-348`)
kennt aktuell nur drei Punkte (Installieren, Prüfen, Neustarten) — keinen
vierten Menüpunkt zum Entfernen, der ein Protokoll bräuchte.

## 6. Was geplant ist (AP-16, noch nicht gebaut)

Das offene Arbeitspaket **AP-16 · Installer: Abräumzweig + Protokoll**
(`todo.md:82-92`) sieht unter anderem vor:

- Ein Abschlussprotokoll nach `/var/log/cmp/install-<zeitstempel>.log` und
  zusätzlich `/opt/cmp/INSTALL-REPORT.txt`, mit Version, OS, Ports, Units,
  TLS-Modus, DB, Migrationsstand, Seed-Ergebnis und Portal-URL — **ohne
  Secrets**.
- Einen Abräumzweig (`--uninstall`, `--purge`) mit eigenem `--dry-run`, als
  vierter Menüpunkt „4) Entfernen".
- Denselben Anspruch für beide Richtungen: Install → Uninstall → Install
  soll sauber und mit vollständigem Protokoll durchlaufen.

Bis dahin bleibt die Installation nachvollziehbar nur über das, was am
Bildschirm sichtbar war oder was ein Bediener selbst mitschneidet (z. B.
`sudo ./deploy/install.sh 2>&1 | tee install.log`) — das ist keine
Eigenschaft des Skripts, sondern eine manuelle Zusatzmaßnahme.

## 7. Zusammenfassung

`deploy/install.sh` protokolliert seinen Ablauf ausschließlich als
Terminal-Ausgabe in einem festen Vier-Symbol-Format (`✓`/`→`/`⚠`/`✗`),
gegliedert in acht nummerierte Phasen — persistiert wird dabei nichts. Ein
Abschlussbericht und ein Abräumzweig sind als AP-16 geplant, aber noch nicht
umgesetzt; bis dahin existiert kein dauerhaftes Installationsprotokoll außer
dem, was ein Bediener selbst mitschneidet.

> Quelle: deploy/install.sh, deploy/lib.sh, deploy/ui.sh, todo.md (AP-16) — am Code geprüft 2026-07-22
