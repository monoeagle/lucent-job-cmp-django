# Wartungsmodus

Ein Wartungsmodus für geplante Ausfallfenster ist für CMP **entworfen, aber
nicht gebaut**. Dieses Kapitel beschreibt den Plan als Plan — nicht als
Funktion, die es heute gibt.

## 1. Ziel des Kapitels

Wer ein Wartungsfenster plant und nach einem Schalter für „Portal zeigt eine
Wartungsseite" sucht, soll hier erfahren, dass es diesen Schalter noch nicht
gibt, warum ein einfaches Stoppen der Dienste nicht reicht, und wie der
bestehende Entwurf aussieht.

## 2. Ist-Stand: nicht umgesetzt

Eine gezielte Suche nach einer Wartungsmodus-Implementierung im Deployment-Code
ergibt keinen Treffer:

```bash
grep -rniE "maintenance" deploy/
```

Die von `install.sh` gerenderte nginx-Konfiguration (`cmp_render_nginx()`,
`deploy/lib.sh:334-366`) kennt keine Marker-Datei-Prüfung und keinen
`error_page 503`-Block — sie proxyt in beiden TLS-Modi ausschließlich direkt auf
`gunicorn`. Es gibt auch **kein** `install.sh --maintenance`-Flag: Die
Argument-Verarbeitung des Installers kennt nur `--install`, `--check`,
`--restart`, `--with-packages`, `--skip-nginx` (`deploy/install.sh:63-73`).

Im offenen Rückstand (`todo.md`) ist einem Wartungsmodus außerdem **kein**
Arbeitspaket zugeordnet — es taucht dort nicht auf.

## 3. Warum bloßes Stoppen der Dienste nicht reicht

Werden `cmp-web` und `cmp-celery` einfach gestoppt, während nginx weiterläuft,
liefert nginx `502 Bad Gateway` — für Nutzerinnen und Nutzer sieht das wie ein
ungeplanter Ausfall aus und erzeugt Support-Anfragen, nicht wie ein
angekündigtes Wartungsfenster. Das fachlich richtige Signal ist `503 Service
Unavailable`: Monitoring und Suchmaschinen verstehen „vorübergehend nicht
verfügbar" statt „kaputt".

## 4. Der bestehende Entwurf

Der einzige bisher ausgearbeitete Vorschlag liegt in der eigenen Analyse zur
Fremddoku-Struktur, noch nicht als Arbeitspaket, nur als Konzept. Idee: eine
Marker-Datei auf der VM, die nginx per `if`-Bedingung prüft, bevor es an
gunicorn weiterreicht.

```nginx
location / {
    if (-f /opt/cmp/MAINTENANCE) { return 503; }
    proxy_pass http://127.0.0.1:8001;
}
error_page 503 /maintenance.html;
location = /maintenance.html { root /opt/cmp/static-maintenance; internal; }
```

Ein- und Ausschalten wäre dann `touch`/`rm` der Marker-Datei — als
naheliegender Kandidat für ein künftiges `install.sh --maintenance on|off`, das
es aber noch nicht gibt.

## 5. Wo das Wartungsfenster in die Release-Kette passen soll

Der Entwurf ordnet den Wartungsmodus in eine größere Kette ein: Feature-Branch
im Repo, Testumgebung, QR-Umgebung, dann erst das eigentliche Wartungsfenster
in Produktion. Als Ablaufskizze (kein Code, nur die geplante Reihenfolge):

```
Feature-Branch --> Testumgebung --> Tests grün? --nein--> zurück zum Branch
                                        |
                                       ja
                                        v
                                 Merge nach main --> QR-Umgebung
                                        |
                              Funktionaltest QR bestanden?
                                   |            |
                                  nein          ja
                                   |            v
                              zurück zum   Wartungsfenster geplant
                                Branch          |
                                                v
                                    Wartungsmodus an (503)
                                                |
                                    Dienste stoppen, Backup, install.sh --install
                                                |
                                       automatisierter Test grün?
                                          |              |
                                         nein            ja
                                          |              v
                                   Rollback: Vorversion   manueller Test
                                   + DB-Backup                |
                                          |                    v
                                          |            Wartungsmodus aus
                                          |                    |
                                          +-------> zurück zum Wartungsfenster
                                                            |
                                                            v
                                                        Freigabe
```

Der Schritt „Backup" in dieser Kette setzt ein automatisiertes Backup-Verfahren
voraus, das ebenfalls noch nicht existiert (Kapitel 8.5) — der Entwurf ist
insofern von zwei noch offenen Bausteinen abhängig, nicht nur von der
nginx-Konfiguration selbst.

## 6. Offener Punkt

Weder die Marker-Datei-Logik noch das `--maintenance`-Flag noch die
Backup-Kopplung sind bisher als Arbeitspaket im Rückstand (`todo.md`)
eingeplant. Bis dahin ist die einzige verfügbare Option ein manuell
angepasster nginx-Block nach demselben Muster wie oben, von Hand gepflegt und
nicht Teil von `install.sh`.

## 7. Zusammenfassung

Ein Wartungsmodus ist als Konzept ausgearbeitet — Marker-Datei, `503` statt
`502`, Einbettung in eine Test→QR→Wartungsfenster-Kette — aber weder im
Installer noch in der gerenderten nginx-Konfiguration umgesetzt und im
Rückstand noch keinem Arbeitspaket zugeordnet. Wer heute ein Wartungsfenster
braucht, muss die nginx-Konfiguration manuell um den beschriebenen Block
ergänzen; ein eingebauter Schalter existiert nicht.

> Quelle: deploy/install.sh, deploy/lib.sh, analyse/analyse-bestellportal.md (Abschnitt 2.10), todo.md — am Code geprüft 2026-07-22
