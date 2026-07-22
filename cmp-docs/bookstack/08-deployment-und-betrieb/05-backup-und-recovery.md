# Backup und Recovery

Was es an Backup- und Wiederherstellungsverfahren für CMP tatsächlich gibt —
und was nicht. Dieses Kapitel erfindet kein Verfahren, das nicht existiert.

## 1. Ziel des Kapitels

Wer eine Installation absichern will, soll hier den ehrlichen Ist-Stand finden:
Es gibt eine dokumentierte Empfehlung, aber **kein** automatisiertes Backup und
**keine** dokumentierte Restore-Prozedur. Beide Lücken werden benannt, nicht
kaschiert.

## 2. Was real existiert: eine empfohlene, manuelle Befehlszeile

`docs/deployment/vm-installation.md` nennt unter „Betrieb: Logs, Backups,
Health" einen `pg_dump`-Befehl als Beispiel:

```bash
sudo -u postgres pg_dump -Fc cmp_prod > /var/backups/cmp_prod_$(date +%F).dump
```

(`docs/deployment/vm-installation.md:540-544`). Das ist ausdrücklich als „z. B.
täglich per cron/systemd-Timer" formuliert — ein Vorschlag, kein eingerichteter
Job. Kein Cron-Eintrag, kein systemd-Timer, kein Skript dafür existiert im
Repository; die Zeile ist manuell in ein Terminal einzugeben.

Die Sicherheits-Checkliste derselben Anleitung führt Backups entsprechend als
**manuell abzuhakenden** Punkt, nicht als geprüftes Ergebnis eines Skripts:

```
- [ ] DB-Backups eingerichtet und wiederherstellbar getestet
```

(`docs/deployment/vm-installation.md:588`).

## 3. Was nicht existiert

Eine gezielte Suche nach Backup-Automatisierung im Installer ergibt keinen
Treffer:

```bash
grep -rniE "backup|dump|restore" deploy/
```

Der einzige Treffer im Installer ist `restorecon` (SELinux-Kontext
wiederherstellen, Kapitel 8.3) — kein Datenbank-Bezug. `install.sh` legt vor
einer Migration oder einem Re-Deploy **kein** Backup an; ein fehlgeschlagener
`migrate`-Lauf hat keinen automatischen Rücksprungpunkt.

Ebenso wenig existiert eine dokumentierte **Restore**-Prozedur: Zum
`pg_dump`-Befehl gibt es keinen passenden `pg_restore`-Befehl in der Anleitung
(`grep -rn pg_restore docs/ cmp-docs/docs/ deploy/` ohne Treffer). Wer ein
Backup zurückspielen müsste, hat dafür keine geprüfte Schritt-für-Schritt-
Anleitung, nur die allgemeine PostgreSQL-Dokumentation zu `pg_restore -Fc`.

## 4. Warum das kein automatisch geschlossenes Arbeitspaket ist

Im Rückstand (`todo.md`) existiert kein eigenes Arbeitspaket für „automatisiertes
Datenbank-Backup" — die verwandten Arbeitspakete decken andere Lücken ab:

- **AP-16** (Installer: Abräumzweig + Protokoll) beschreibt `--uninstall` und
  `--purge`, nicht Backup — bei `--purge` würde die Datenbank sogar gelöscht,
  ausdrücklich „mit expliziter Rückfrage" (`todo.md:87`), ein vorheriges Backup
  ist dort nicht Teil der Beschreibung.
- **AP-17** (VM-Verifikation) betrifft die Idempotenz des Installers, nicht das
  Backup-Verfahren.

Die Lücke selbst ist im Handbuch bereits benannt: NFR_BACKUP01 (Kapitel 1,
Abschnitt 5) führt sie als 🟡 „dokumentiert, aber nicht automatisiert". Ein
Arbeitspaket, das genau diese Automatisierung baut, ist im aktuellen Rückstand
noch nicht eingeplant.

## 5. Was das für den Betrieb bedeutet

Bis ein automatisiertes Verfahren existiert, liegt die Verantwortung für
Backup und Restore-Test vollständig beim Betreiber der VM:

- Den `pg_dump`-Befehl selbst per Cron oder systemd-Timer einrichten.
- Das Ziel des Backups (`/var/backups/…`) auf ein von der VM getrenntes
  Speicherziel replizieren — ein lokales Backup auf derselben Platte schützt
  nicht vor einem VM-Totalausfall.
- Einen Restore **vor** dem produktiven Einsatz mindestens einmal tatsächlich
  durchspielen, nicht nur den Dump-Befehl verifizieren.

## 6. Zusammenfassung

Es gibt eine dokumentierte, manuelle `pg_dump`-Empfehlung, aber keinen
automatisierten Backup-Job, kein Restore-Verfahren und kein Arbeitspaket, das
diese Lücke aktuell schließt. Wer CMP produktiv betreibt, muss Backup und
Restore-Test selbst einrichten und verifizieren — der Installer tut hierfür
nichts.

> Quelle: docs/deployment/vm-installation.md, deploy/install.sh, deploy/lib.sh, todo.md (AP-16, AP-17), cmp-docs/bookstack/01-ziel-und-anforderungen/04-nicht-funktionale-anforderungen.md — am Code geprüft 2026-07-22
