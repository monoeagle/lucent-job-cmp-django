# Logging-Ebenen und Konfiguration

Dieses Kapitel dokumentiert, was CMP heute an strukturiertem Anwendungs-Logging
tatsächlich hat — und das ist, geprüft am Code, nichts Projekteigenes. Die Seite
trennt bewusst Djangos eingebautes Default-Verhalten von einer echten,
projekteigenen Konfiguration, die es (noch) nicht gibt.

## 1. Ziel des Kapitels

Wer im Betrieb nach `LOGGING`-Einstellungen oder Logger-Aufrufen sucht, soll
hier den ehrlichen Befund finden statt eines Wunschbilds: keine eigene
Konfiguration, kein einziger `getLogger(__name__)`-Aufruf im Anwendungscode.
Was stattdessen greift, ist Djangos eingebautes Standardverhalten — das ist
etwas anderes als projekteigenes Logging und wird hier getrennt beschrieben.

## 2. Ist-Zustand: keine projekteigene Konfiguration

Zwei Suchen belegen die Lücke vollständig:

```
grep -rn "LOGGING" cmp/config cmp/apps cmp/core
grep -rn "getLogger" cmp/config cmp/apps cmp/core
```

Beide liefern **0 Treffer** (Stand 2026-07-22). In keiner der vier
Settings-Dateien (`cmp/config/settings/base.py`, `development.py`,
`testing.py`, `production.py`) existiert ein `LOGGING`-Dict, und nirgends im
Anwendungscode wird ein Logger instanziiert oder benutzt. Das ist das offene
Arbeitspaket **AP-14 · Logging-Fundament** (`todo.md:63-71`).

## 3. Was ohne eigene Konfiguration trotzdem greift: Djangos Default-Logging

Ohne eigenes `LOGGING`-Dict verschwindet Logging nicht komplett — Django bringt
ein Default-`LOGGING`-Dict mit (`django.utils.log.DEFAULT_LOGGING`), das in
jeder Django-6.0-Installation aktiv ist, sofern eine Settings-Datei es nicht
überschreibt. Geprüft direkt im Projekt-venv gegen die installierte Version:

```
venv/bin/python3 -c "
import django
print(django.VERSION)
from django.utils.log import DEFAULT_LOGGING
import pprint; pprint.pprint(DEFAULT_LOGGING)
"
```

Ergebnis (`Django (6, 0, 3, 'final', 0)`):

| Logger | Handler | Bedingung | Effekt |
|---|---|---|---|
| `django` | `console` (Level `INFO`) | nur wenn `DEBUG=True` (`RequireDebugTrue`-Filter) | Ausgabe auf stdout im Entwicklungsbetrieb |
| `django` | `mail_admins` (Level `ERROR`) | nur wenn `DEBUG=False` (`RequireDebugFalse`-Filter) | Versuch, 500er-Fehler per E-Mail an `ADMINS` zu schicken |
| `django.server` | `django.server`-Handler (Level `INFO`, `propagate=False`) | immer aktiv | Zugriffszeilen des Entwicklungsservers (`runserver`) |

Ein Datei-Handler ist in diesem Default **nicht** enthalten — Django schreibt
von sich aus nirgends in eine Log-Datei.

## 4. Warum der `mail_admins`-Zweig in CMP praktisch wirkungslos ist

Der `mail_admins`-Handler greift zwar (kein eigenes `LOGGING` überschreibt
ihn), läuft aber ins Leere:

- `ADMINS` ist in keiner Settings-Datei gesetzt (`grep -n "ADMINS" cmp/config/settings/*.py` → 0 Treffer) — ohne Empfänger verschickt `AdminEmailHandler` nichts.
- `EMAIL_BACKEND` ist ebenfalls nirgends gesetzt (`grep -n "EMAIL_BACKEND" cmp/config/settings/*.py` → 0 Treffer), was zum offenen AP-18 (E-Mail-Benachrichtigungen, `todo.md:104-111`) passt.

In der Praxis heißt das: In Produktion (`DEBUG=False`,
`cmp/config/settings/production.py:38`) versucht Django bei einem 500er,
Admins zu benachrichtigen — ohne konfigurierte Empfänger passiert dabei
nichts Sichtbares. In der Entwicklung (`DEBUG=True`,
`cmp/config/settings/development.py:3`) landet die `django`-Logger-Ausgabe
auf der Konsole, zusätzlich zur `runserver`-Zugriffszeile.

## 5. Was AP-14 vorsieht (Plan, noch nicht gebaut)

Die folgenden Punkte sind **Plan**, nicht Ist-Zustand — sie stehen so in
`todo.md:63-71` und sind hier absichtlich als Vorhaben markiert:

- Ein eigenes `LOGGING`-Dict in `config/settings/base.py`, Level je Umgebung überschreibbar.
- Eigene Logger je Domäne: `cmp.orders`, `cmp.approvals`, `cmp.provisioning`, `cmp.audit`.
- Ausgabe nach stdout, damit sie unter der systemd-Installation in journald landet (siehe Kapitel 7.3 zu `--access-logfile -`/`--error-logfile -` bei gunicorn); eine Datei nur mit Rotation, falls überhaupt.
- Die Seed-Schritte (`seed.py`) sollen über einen Logger statt über `self.stdout.write` laufen.
- Eine dokumentierte Abgrenzung: Logging ist technisch (Betriebssicht), das Audit-Log ist fachlich (Kapitel 7.2) — keins ersetzt das andere.

## 6. Zusammenfassung

CMP hat aktuell keine projekteigene Logging-Konfiguration und keinen einzigen
Logger-Aufruf im Anwendungscode — grep-belegt mit 0 Treffern in beiden
Suchen. Was ohne eigenes `LOGGING`-Dict trotzdem greift, ist Djangos
eingebautes Default-Logging, das aber wegen fehlender `ADMINS`/
`EMAIL_BACKEND`-Konfiguration in Produktion praktisch nichts zustellt. Ein
eigenes Logging-Fundament ist als AP-14 offen geplant, aber noch nicht
umgesetzt.

> Quelle: cmp/config/settings/base.py, cmp/config/settings/development.py, cmp/config/settings/production.py, cmp/config/settings/testing.py, django.utils.log.DEFAULT_LOGGING (Django 6.0.3, geprüft im Projekt-venv), todo.md (AP-14, AP-18) — am Code geprüft 2026-07-22
