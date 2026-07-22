# TLS und Zugriff — Zertifikatsbeschaffung und Betriebsdetails

Kapitel 2.3 beschreibt bereits, dass ohne passendes Zertifikat kein
443-Listener existiert und der Zugriff immer über den FQDN läuft, nie über die
IP. Dieses Kapitel wiederholt das nicht, sondern vertieft die Betriebsseite:
woher das Zertifikat kommt, was SELinux/firewalld dafür tun müssen, und wie das
Panel die tatsächliche Erreichbarkeit anzeigt statt sie zu behaupten.

## 1. Ziel des Kapitels

Wer ein Zertifikat beschaffen, einspielen oder eine „Portal nicht erreichbar"-
Meldung diagnostizieren muss, findet hier den konkreten Weg für online und
air-gapped VMs sowie die Systemänderungen, die `install.sh` beim Umschalten auf
HTTPS vornimmt.

## 2. `install.sh` erzeugt kein Zertifikat — es sucht nur danach

Der Installer selbst ruft weder certbot noch `openssl req` auf. Er prüft in
Schritt 1/8 lediglich, ob unter `/etc/pki/cmp/cmp.crt` ein Zertifikat mit
passendem SAN liegt (`cmp_cert_matches_fqdn()`, `deploy/lib.sh:280-289`) und
leitet daraus den Modus ab (`deploy/install.sh:204-209`). Die Beschaffung selbst
läuft **außerhalb** von `install.sh`, auf zwei unterschiedlichen Wegen:

| Umgebung | Weg | Quelle |
|---|---|---|
| VM mit Internetzugang | certbot + Let's Encrypt (`--nginx`-Plugin, automatischer Renew-Timer) | `docs/deployment/vm-installation.md:462-479` |
| air-gapped VM | interne Unternehmens-CA (empfohlen) **oder** self-signed per `openssl req -x509` | `docs/deployment/vm-installation-offline.md:520-539` |

Beide Wege enden gleich: `cmp.crt` (inkl. Zwischenzertifikaten) + `cmp.key`
landen unter `/etc/pki/cmp/`, danach `install.sh` erneut ausführen — der
Installer erkennt das Zertifikat und schaltet auf HTTPS um.

## 3. Nur installer-eigene Zertifikate werden ersetzt

`cmp_cert_is_self_signed()` prüft, ob Issuer gleich Subject ist
(`deploy/lib.sh:291-300`). Nur solche Zertifikate gelten als vom Installer
selbst erzeugt und dürfen automatisch überschrieben werden. Ein von der internen
CA ausgestelltes Zertifikat (Issuer ≠ Subject) fasst `install.sh` nie an — ein
erneuter Lauf löscht kein eingespieltes CA-Zertifikat.

## 4. SELinux und firewalld je nach Modus

Schritt 8/8 setzt zusätzlich zur nginx-Konfiguration die SELinux- und
Firewall-Regeln, **abhängig vom gewählten Modus** (`deploy/install.sh:301-314`):

```bash
setsebool -P httpd_can_network_connect on              # nginx darf zu gunicorn (8001) verbinden
semanage fcontext -a -t httpd_sys_content_t "…/staticfiles(/.*)?"
restorecon -Rv …/staticfiles

firewall-cmd --permanent --add-service=http            # immer geöffnet
# nur im HTTPS-Modus zusätzlich:
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

Im HTTP-Modus bleibt Port 443 also in firewalld **geschlossen** — nicht nur
ungenutzt, sondern aktiv nicht freigegeben. Das ist derselbe Grund, warum ein
`https://`-Aufruf ohne Zertifikat mit *Connection refused* endet und nicht mit
einer Zertifikatswarnung (Kapitel 2.3, Abschnitt 4).

## 5. HSTS: beide Modi setzen `SECURE_HSTS_SECONDS=0`

`cmp_env_security_lines()` schreibt in **beiden** Zweigen (HTTP wie HTTPS)
`SECURE_HSTS_SECONDS=0` in die Umgebungsdatei (`deploy/lib.sh:313-325`) — auch
im HTTPS-Modus, nicht nur im HTTP-Modus. Der Grund: Ein selbst erzeugtes oder
internes Zertifikat rechtfertigt noch keinen langen HSTS-Wert, der Clients bei
einem späteren Zertifikatsproblem dauerhaft aussperren würde
(`docs/deployment/vm-installation-offline.md:586-589`). Bei einer echten,
vertrauenswürdigen CA lässt sich der Wert manuell erhöhen:

```bash
sudo vim /etc/cmp/cmp.env               # SECURE_HSTS_SECONDS=31536000
sudo systemctl restart cmp-web
```

Der Produktions-Default ohne diese Zeile wäre ohnehin ein Jahr
(`cmp/config/settings/production.py:21`) — die Installer-Zeile überschreibt ihn
bewusst auf `0`, bis jemand das manuell ändert.

## 6. Das Panel zeigt den tatsächlichen Zustand, nicht die Absicht

`cmp_portal_proto()` liest nicht den gewünschten Modus, sondern die **tatsächlich
geschriebene** nginx-Konfigurationsdatei: Steht dort `listen 443`, meldet die
Funktion `https 443`, sonst `http 80`, ohne Konfigurationsdatei keine Ausgabe
(`deploy/lib.sh:368-382`, Kommentar: „nichts erfinden"). Der Prüfbereich von
`install.sh --check` zeigt also den Zustand des gerenderten nginx-Blocks, nicht
den zuletzt eingegebenen FQDN oder eine angenommene URL.

## 7. Zertifikatswarnung trotz vermeintlich passendem Zertifikat

Zwei häufige Ursachen, wenn der Browser trotz laufendem HTTPS-Modus warnt:

- **Self-signed / interne CA nicht im Trust-Store des Clients** — das
  Zertifikat muss auf dem aufrufenden Rechner importiert werden, das Portal
  selbst kann das nicht erzwingen (`docs/deployment/vm-installation-offline.md:541-542`).
- **SAN passt nicht exakt zum aufgerufenen Namen** — `cmp_cert_matches_fqdn()`
  vergleicht den eingegebenen FQDN wörtlich gegen die SAN-Liste
  (`deploy/lib.sh:280-289`); ein Zertifikat für `<fqdn>` deckt den reinen
  Kurznamen ohne Domain-Anteil nicht ab.

## 8. Zusammenfassung

`install.sh` entscheidet den TLS-Modus anhand eines vorhandenen Zertifikats,
erzeugt aber selbst keins — Beschaffung läuft über certbot (online) oder
interne CA/self-signed (air-gapped), beide münden in `/etc/pki/cmp/`. SELinux-
und firewalld-Regeln folgen dem gewählten Modus, Port 443 bleibt im HTTP-Modus
aktiv geschlossen. Beide Modi setzen HSTS zunächst auf 0 — ein bewusst
vorsichtiger Default, der sich bei vertrauenswürdiger CA manuell erhöhen lässt.
Das Panel liest den tatsächlichen Zustand aus der geschriebenen Konfiguration,
nicht aus der zuletzt getroffenen Auswahl.

> Quelle: deploy/lib.sh, deploy/install.sh, docs/deployment/vm-installation.md, docs/deployment/vm-installation-offline.md, cmp/config/settings/production.py — am Code geprüft 2026-07-22
