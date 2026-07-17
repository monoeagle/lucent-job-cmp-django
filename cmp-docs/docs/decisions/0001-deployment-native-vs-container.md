# ADR-0001 — Deployment: native systemd-Installation vs. Container

- **Status:** Akzeptiert · 2026-06-27
- **Kontext-Version:** v1.3.0
- **Betrifft:** AP-11 (Container-Setup)

## Kontext

Das CloudMan Portal läuft als **eine einzelne AlmaLinux/Rocky-9-VM**, häufig
**air-gapped** (kein Internet). Der native Deployment-Pfad ist bereits gebaut und
verifiziert: `deploy/install.sh` + Offline-**Wheelhouse** (32 cp312/manylinux
Wheels), systemd-Units (gunicorn + Celery), nginx + TLS, PostgreSQL 16, Redis,
SELinux/firewalld — dokumentiert in `vm-installation.md` (online) und
`vm-installation-offline.md` (air-gapped).

AP-11 war ursprünglich als **Docker-Setup** geplant. Diese ADR hält fest, ob/wann
containerisiert wird.

## Entscheidung

**Die native systemd-Installation bleibt der Default** für das air-gapped
Single-VM-Ziel. Containerisierung wird **optional** und — falls umgesetzt — mit
**Podman + Quadlets** (RHEL-nativ, rootless, systemd-integriert) realisiert, **nicht
mit Docker-CE**.

Container lohnen sich erst, wenn **mindestens eines** zutrifft:

1. mehrere Umgebungen/Hosts (Dev/Test/Prod oder mehrere Kunden),
2. Bedarf an unveränderlichen Artefakten + 1-Klick-Rollback + Dev-Prod-Parität,
3. die VM erlaubt eine Container-Engine und ist nicht streng air-gapped.

## Abwägung (Native vs. Container)

| Achse | Native (systemd + Wheelhouse) | Container (Podman/Quadlets) |
|---|---|---|
| **Wartbarkeit** | Eine Patch-Ebene (Host-OS via `dnf`/Wheels); Rollback = altes App-Tar + Wheelhouse. OS-gekoppelt. | Unveränderliches Image, sauberer Tag-Rollback, App/Host-Trennung — **aber zwei** Patch-Ebenen (Host + Base-Image). |
| **Konfigurationsaufwand** | Hoch im Detail, **aber bereits in `install.sh` automatisiert**. Viele Berührungspunkte. | Zentral in Quadlets/`podman-compose`; dafür Containerfile-Authoring, Volumes, Secrets, SELinux-`:Z`, TLS-Terminierung. |
| **Bedienbarkeit** | Standard `systemctl`/`journalctl`/`psql` — vertraut für RHEL-Admins, keine Abstraktion. | Einheitlich, starke Dev-Prod-Parität; mit Quadlets bleibt `systemctl`/`journalctl` erhalten; Abstraktions-/Debug-Ebene kommt hinzu. |

### Entscheidende Projekt-Faktoren

- **Air-gapped:** nativ gelöst (`pip --no-index` aus Wheelhouse). Container
  air-gapped = Images per `podman save`/`load` transportieren **plus Base-Image
  offline spiegeln** → mehr bewegliche Teile.
- **Single-VM:** Dockers/Container-Kernstärken (Skalierung, Orchestrierung,
  Multi-Host) greifen auf einer VM kaum; Compose ist dort nur ein schwererer
  Prozess-Manager als systemd.
- **RHEL-Familie:** AlmaLinux liefert **Podman** (daemonless, rootless), nicht
  Docker — Docker-CE arbeitet gegen das OS-Modell.

## Konsequenzen

**Positiv**

- Kein zusätzlicher Pflege-/Transportaufwand für das aktuelle Ziel; der fertige
  native Pfad wird genutzt.
- Bedienbarkeit bleibt im vertrauten RHEL-Admin-Werkzeug.

**Negativ / Risiken**

- Reproduzierbarkeit hängt an „Staging-Host == Ziel-VM" statt an einem Image.
- Bei künftigem Multi-Host-Bedarf muss Container-Arbeit nachgeholt werden (AP-11).

## Verworfene Alternative

- **Docker-CE + docker-compose:** nicht RHEL-nativ; auf air-gapped/gehärteten VMs
  oft eingeschränkt; Daemon-Modell + Rootful entgegen dem Podman-Standard von
  AlmaLinux. → Falls containerisiert, Podman/Quadlets.

## Folgearbeit

AP-11 in `todo.md` ist entsprechend auf **„Container-Setup (Podman/Quadlets,
optional)"** umgeschrieben (DoD: `podman-compose up` bzw. Quadlets, 328 Tests grün
im Container, Offline-Image-Transport).
