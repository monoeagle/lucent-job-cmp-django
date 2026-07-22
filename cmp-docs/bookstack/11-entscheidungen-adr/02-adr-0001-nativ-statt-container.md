# 11.2 ADR-0001 — Deployment: nativ statt Container

CMP läuft heute als native systemd-Installation auf einer einzelnen AlmaLinux/Rocky-9-VM. Diese
Seite hält fest, warum Containerisierung bewusst nicht der Default ist, und belegt die
Konsequenzen am echten Installer (`deploy/install.sh`, `deploy/lib.sh`).

## 1. Kontext

Das CloudMan Portal läuft als eine einzelne AlmaLinux/Rocky-9-VM, häufig **air-gapped** (kein
Internet). Der native Deployment-Pfad ist bereits gebaut und lauffähig:
`deploy/install.sh` orchestriert Preflight + 8 Schritte (`hdr "0/8 Preflight"` bis
`hdr "8/8 nginx + TLS"`, `deploy/install.sh:135,183,212,227,235,242,258,280,293`), mit einer
Offline-Wheelhouse (`wheels/`, aktuell **32** `.whl`-Dateien, frisch gezählt:
`find wheels -maxdepth 1 -name "*.whl" | wc -l`), systemd-Units für gunicorn und Celery
(`deploy/install.sh:280-291`), nginx + TLS (`deploy/install.sh:293-316`), PostgreSQL 16
(PGDG oder AppStream-Modul, erkannt statt geraten — `deploy/lib.sh:111-115`) und
firewalld/SELinux-Anpassung (`deploy/install.sh:307-315`).

AP-11 (`todo.md`) war ursprünglich als Docker-Setup geplant. Diese Entscheidung hält fest, ob und
wann containerisiert wird. Quelle der ursprünglichen Fassung:
`cmp-docs/docs/decisions/0001-deployment-native-vs-container.md` (Status: Akzeptiert, 2026-06-27).

## 2. Entscheidung

Die native systemd-Installation bleibt der Default für das air-gapped Single-VM-Ziel.
Containerisierung wird optional und — falls umgesetzt — mit **Podman + Quadlets** realisiert
(RHEL-nativ, rootless, systemd-integriert), **nicht mit Docker-CE**. Am Code frisch geprüft
(`grep -rn "podman\|docker" deploy/install.sh deploy/lib.sh deploy/ui.sh`): kein einziger Treffer
— Container-Unterstützung ist im Installer aktuell nicht vorhanden, weder für Podman noch Docker.

Container lohnen sich laut Entscheidung erst, wenn mindestens eines zutrifft: mehrere
Umgebungen/Hosts, Bedarf an unveränderlichen Artefakten mit 1-Klick-Rollback, oder eine VM, die
eine Container-Engine erlaubt und nicht streng air-gapped ist.

## 3. Konsequenzen

**Positiv, am echten Installer belegt**

- Kein zusätzlicher Pflege- oder Transportaufwand für das aktuelle Ziel: der fertige native Pfad
  wird direkt genutzt. `deploy/install.sh` installiert die Wheels offline
  (`--no-index --find-links=$APP_ROOT/wheels`, `deploy/install.sh:229-230`) — keine Registry, kein
  Image-Transport nötig.
- Bedienbarkeit bleibt im vertrauten RHEL-Admin-Werkzeug: `systemctl`, `journalctl`, `psql` direkt
  auf dem Host, keine zusätzliche Abstraktionsebene.
- Das Skript ist idempotent — ein zweiter Lauf aktualisiert die Installation und startet die
  Dienste mit neuem Code neu, ohne SECRET_KEY oder Daten zu verlieren (`deploy/install.sh:23-25`).
- `--check` prüft, ohne etwas zu ändern (`deploy/install.sh:12`, Rückgabewert als Health-Check
  nutzbar, `deploy/install.sh:114`).

**Negativ / Risiken**

- Reproduzierbarkeit hängt an „Staging-Host == Ziel-VM" statt an einem unveränderlichen Image —
  Host-Drift (unterschiedliche `dnf`-Paketstände) wirkt sich direkt auf die Installation aus.
- Bei künftigem Multi-Host-Bedarf muss die Container-Arbeit nachgeholt werden (AP-11 bleibt dafür
  offen); heute existiert dafür kein Code, kein Containerfile, keine Quadlet-Unit im Repo.
- Zwei parallele PostgreSQL-Varianten (PGDG-Paket vs. AppStream-Modul) müssen im Installer selbst
  unterschieden werden (`deploy/lib.sh:111-115` — Service-Namen `postgresql-16.service` vs.
  `postgresql.service`), weil es keine einheitliche Container-Basis gibt, die das wegabstrahiert.

## 4. Alternativen

- **Docker-CE + docker-compose** (verworfen): nicht RHEL-nativ, auf air-gapped/gehärteten VMs oft
  eingeschränkt, Daemon-Modell + Rootful widerspricht dem Podman-Standard von AlmaLinux/Rocky.
- **Podman/Quadlets sofort statt optional** (verworfen für den jetzigen Schnitt): Single-VM-Ziel
  profitiert kaum von Container-Kernstärken (Skalierung, Multi-Host-Orchestrierung) — Compose oder
  Quadlets wären hier nur ein schwererer Prozess-Manager als systemd, für dessen Nutzen die VM
  keine mehreren Umgebungen/Hosts hat.

## 5. Status

Akzeptiert (2026-06-27). Folgearbeit: AP-11 in `todo.md` ist auf „Container-Setup (Podman/Quadlets,
optional)" umgeschrieben, mit eigener Definition-of-Done (`podman-compose up` bzw. Quadlets, Tests
grün im Container, Offline-Image-Transport) — diese Definition-of-Done ist am 2026-07-22 nicht
erfüllt, da im Installer-Code kein Container-Pfad existiert (siehe Grep-Beleg unter Punkt 2).

> Quelle: `cmp-docs/docs/decisions/0001-deployment-native-vs-container.md`, `deploy/install.sh:12,23-25,114,135,183,212,227,229-230,235,242,258,280-291,293-316`, `deploy/lib.sh:111-115`, `wheels/` — am Code geprüft 2026-07-22
