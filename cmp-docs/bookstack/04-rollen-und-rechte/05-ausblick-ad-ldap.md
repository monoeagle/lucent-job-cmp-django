# Ausblick: AD-/LDAP-Anbindung

Diese Seite beschreibt einen **geplanten**, noch nicht umgesetzten Zustand — im
Unterschied zu den übrigen Seiten dieses Kapitels, die den Ist-Stand belegen.

## 1. Ziel des Kapitels

Wer nach einer AD-/LDAP-Anbindung sucht oder sie einplanen will, soll hier klar
lesen: Es gibt sie heute nicht, und welchen Umfang das zugehörige Arbeitspaket
vorsieht.

## 2. Ist-Zustand: keine AD-/LDAP-Anbindung

CMP meldet Benutzer ausschließlich lokal an, gegen die `User`-Tabelle in
PostgreSQL — es gibt kein Verzeichnisdienst-Backend. Belege:

- `AUTHENTICATION_BACKENDS` enthält nur `ModelBackend` und das
  `allauth`-Standardbackend, kein LDAP-Backend
  (`cmp/config/settings/base.py:93-96`, siehe [Kapitel 4.1](01-authentifizierung.md)).
- Keine der drei Requirements-Dateien führt `django-auth-ldap` (geprüft:
  `grep -in "ldap" requirements.txt requirements/base.txt requirements/production.txt
  requirements/dev.txt cmp/config/settings/*.py` — kein Treffer).
- Die Rolle eines Benutzers ist ein reines Datenbankfeld
  (`cmp/core/domain/enums.py:5-9`, siehe [Kapitel 4.2](02-rollenmodell.md)) — es gibt
  keinen Code-Pfad, der eine Rolle aus einer AD-Gruppenmitgliedschaft ableitet.

Wo AD/LDAP in älterer Fremd-Dokumentation als Anforderung auftaucht, ist das für CMP
als offenes Arbeitspaket erfasst, nicht als vorhandene Funktion.

## 3. Geplanter Umfang

Erfasst als **AP-21 · AD-/LDAP-Anbindung** in `todo.md`, mit folgendem Befund und
Umfang (`todo.md`, Abschnitt AP-21):

> Befund: `grep ldap requirements.txt` → 0 Treffer. Rollen werden heute als Feld
> gepflegt statt aus AD-Gruppen gemappt.

Geplante Schritte:

- `django-auth-ldap` als Abhängigkeit aufnehmen (inklusive Offline-Wheelhouse für
  Python 3.12)
- Konfigurierbares Mapping von AD-Gruppen auf `UserRole`-Werte, synchronisiert bei
  jedem Login
- Definiertes Verhalten für Fehlerfälle: AD nicht erreichbar → Login verweigern;
  Benutzer ohne zugeordnete Rolle → Minimalrechte (`requester`); im AD
  deaktivierter Benutzer → lokal ebenfalls deaktivieren
- Lokaler Fallback-Login bleibt für Entwicklung und Notfälle bestehen — die heutige
  `ModelBackend`/`allauth`-Anmeldung würde nicht ersetzt, sondern ergänzt

Definition of Done laut `todo.md`: Login gegen eine AD-Testumgebung funktioniert,
Rollen kommen aus AD-Gruppen, alle Fehlerfälle sind getestet, und es wird kein
Passwort lokal gespeichert.

## 4. Zusammenfassung

Eine AD-/LDAP-Anbindung existiert in CMP heute nicht — weder als Abhängigkeit noch
als Backend noch als Rollenquelle. Der Umfang für eine spätere Umsetzung ist als
AP-21 in `todo.md` festgehalten und setzt voraus, dass der bestehende lokale
Login-Weg als Fallback erhalten bleibt.

> Quelle: cmp/config/settings/base.py, cmp/core/domain/enums.py, requirements.txt, requirements/base.txt, requirements/production.txt, requirements/dev.txt, todo.md (AP-21) — am Code geprüft 2026-07-22
