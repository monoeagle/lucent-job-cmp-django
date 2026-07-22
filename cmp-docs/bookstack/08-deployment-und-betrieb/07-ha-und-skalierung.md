# HA und Skalierung

Was CMPs Architektur an Hochverfügbarkeit und Skalierung hergibt — und was
davon tatsächlich erprobt ist. Dieses Kapitel verspricht keine Skalierbarkeit,
die niemals getestet wurde.

## 1. Ziel des Kapitels

Wer über Hochverfügbarkeit oder Mehrfach-Instanzen nachdenkt, soll hier eine
ehrliche Einordnung finden: nicht „HA-fähig", sondern eine präzise Aussage
darüber, was die Architektur zulässt, was bereits genutzt wird, und was nie
gebaut oder erprobt wurde.

## 2. Die Ist-Topologie in einem Satz

`install.sh` installiert CMP als **eine** Maschine: nginx, gunicorn, PostgreSQL,
Redis und der Celery-Worker laufen alle auf demselben Host, die meisten davon
ausschließlich auf `127.0.0.1` gebunden (Details in Kapitel 2.3). Das ist kein
Zufall, sondern das erklärte Zielbild: eine air-gapped Single-VM-Installation
(`ADR-0001`, `cmp-docs/docs/decisions/0001-deployment-native-vs-container.md:9-21`).

## 3. Was schon heute horizontal geht

| Voraussetzung für Skalierung | Status | Beleg |
|---|---|---|
| Mehrere Celery-Worker | ✅ | Celery skaliert horizontal, sobald der Broker (Redis) extern erreichbar ist — die Worker-Anzahl ist nicht architektonisch begrenzt |
| Zustandslose Dateien | ✅ | `STATIC_ROOT` + `collectstatic`, keine nutzergenerierten Uploads im Dateisystem (`cmp/config/settings/production.py:52`) |
| Externe DB/Redis über Konfiguration | 🟡 | `DATABASE_URL`/`CELERY_BROKER_URL` sind reine Umgebungsvariablen (`production.py:43,47`) — technisch auf einen anderen Host verweisbar, aber nie in dieser Topologie erprobt |
| Stateless App (Sessions) | 🟡 | Sessions liegen per Django-Default in der Datenbank, nicht in Redis — bei mehreren Web-Instanzen funktioniert das (gemeinsame DB), ein Redis-Session-Store wäre die naheliegendere Wahl, existiert aber nicht |

## 4. Was heute nicht geht

| Voraussetzung | Status | Warum |
|---|---|---|
| Load Balancer / mehrere Web-Knoten | ❌ | `install.sh` kennt genau eine Maschine — ein Lauf installiert nginx, gunicorn und die Datenbank auf demselben Host, es gibt keinen Modus für „nur App-Knoten ohne lokale DB" |
| Mehrere gunicorn-Instanzen hinter einem gemeinsamen Proxy | ❌ | Die systemd-Unit bindet exakt einen gunicorn-Prozess mit 3 Workern an `127.0.0.1:8001` (`deploy/lib.sh:177`); ein zweiter Knoten bräuchte eine eigene Installation plus externen Load Balancer, den `install.sh` nicht kennt |
| PostgreSQL-Replikation / Failover | ❌ | `cmp_pg_ensure()` legt Rolle und Datenbank lokal an (`deploy/lib.sh:218-236`), keine Replikations- oder Failover-Konfiguration im Installer |
| Redis-Hochverfügbarkeit (Sentinel/Cluster) | ❌ | `cmp_ensure_redis()` startet einen einzelnen lokalen Redis-Dienst (`deploy/lib.sh:245-268`), keine Sentinel-/Cluster-Anbindung |
| Fester Celery-Concurrency-Wert | 🟡 | Die Unit startet mit `--concurrency=2` fest verdrahtet (`deploy/lib.sh:205`) — mehr Kapazität bedeutet heute: die Zeile von Hand ändern und den Dienst neu starten, kein Skalierungsparameter des Installers |

## 5. Warum das für das Zielbild kein Mangel ist

Für eine air-gapped Single-VM-Installation greifen die Kernstärken von HA und
Skalierung ohnehin kaum: Es gibt keine zweite VM, die ausfallen könnte, und
keinen Bedarf, Traffic auf mehrere Knoten zu verteilen. Der ehrliche Satz dafür
lautet **„nicht gebaut, nicht erprobt, aber nicht verbaut"** — die Architektur
(Umgebungsvariablen statt hartcodierter Hosts, zustandslose Static-Files,
horizontal skalierender Celery-Broker) verhindert eine spätere Erweiterung
nicht, sie ist nur nie in diese Richtung getestet worden.

## 6. Der Pfad zu Multi-Host, falls nötig

Sobald mindestens eine dieser Bedingungen zutrifft — mehrere Umgebungen/Hosts,
Bedarf an unveränderlichen Artefakten mit Rollback, oder eine VM, die eine
Container-Engine erlaubt und nicht air-gapped ist — sieht `ADR-0001` **Podman +
Quadlets** als den vorgesehenen Weg vor, nicht Docker-CE (RHEL-nativ, rootless).
Das ist als **AP-11** vorgemerkt und bewusst optional
(`cmp-docs/docs/decisions/0001-deployment-native-vs-container.md:21-30`,
`todo.md:6-15`). Air-gapped bliebe auch dort eine zusätzliche Aufgabe:
Container-Images müssten per `podman save`/`load` transportiert und das
Base-Image separat gespiegelt werden — mehr bewegliche Teile als die aktuelle
Wheelhouse.

## 7. Zusammenfassung

CMP läuft heute als eine einzelne, native VM-Installation ohne Load Balancer,
ohne DB-Replikation und ohne Redis-Hochverfügbarkeit — für das air-gapped
Single-VM-Zielbild eine bewusste, keine zufällige Grenze. Celery skaliert
architektonisch am ehesten horizontal, sobald der Broker extern erreichbar
wäre; alles andere (mehrere Web-Knoten, DB-Failover) ist weder gebaut noch
erprobt. Ein dokumentierter, aber optionaler Pfad zu Multi-Host existiert über
Podman/Quadlets (AP-11, ADR-0001).

> Quelle: deploy/install.sh, deploy/lib.sh, cmp/config/settings/production.py, cmp-docs/docs/decisions/0001-deployment-native-vs-container.md, todo.md (AP-11), analyse/analyse-bestellportal.md (Abschnitt 2.9) — am Code geprüft 2026-07-22
