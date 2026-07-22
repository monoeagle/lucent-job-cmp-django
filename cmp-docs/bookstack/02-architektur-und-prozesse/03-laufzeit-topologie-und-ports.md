# Laufzeit-Topologie und Ports

Das logische Schichtenbild aus Kapitel 2.1/2.2 sagt nichts über Prozesse und Ports.
Dieses Kapitel beschreibt die Betriebssicht: welcher Dienst nach `install.sh` auf
welchem Port lauscht, wer mit wem spricht, und wie der TLS-Modus zustande kommt.

## 1. Ziel des Kapitels

Wer das Portal auf einer VM installiert oder Verbindungsprobleme diagnostiziert, soll
hier nachschlagen können, welcher Port von außen erreichbar ist und warum ein Aufruf
per IP oder ohne Zertifikat scheitert.

## 2. Fünf Dienste nach `install.sh`

Nach einer Standardinstallation laufen fünf Dienste. Quelle der Wahrheit sind die
Installer-Skripte `deploy/install.sh` und `deploy/lib.sh` sowie
`cmp/config/settings/production.py` — nicht die App selbst, denn Django kennt in
Produktion nur seinen eigenen Prozess.

```
Client
  |  HTTP :80 oder HTTPS :443 (je nach Zertifikat)
  v
nginx (alle Interfaces)
  |  proxy_pass http://127.0.0.1:8001
  v
gunicorn (nur 127.0.0.1:8001, 3 Worker)
  |
  v
Django (Views -> Services -> Models)
  |                              \
  v                               v
PostgreSQL (127.0.0.1:5432)     Redis (localhost:6379) <--> Celery-Worker
```

`gunicorn` bindet laut Unit-Definition ausschließlich an Loopback:
`ExecStart=${venv}/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001
--workers 3 --timeout 60 ...` (`deploy/lib.sh:177`). nginx proxyt in beiden
TLS-Modi auf dieselbe Adresse (`proxy_pass http://127.0.0.1:8001;`,
`deploy/lib.sh:342` und `:358`).

## 3. Wer macht was

| Dienst | Aufgabe | Bindung |
|---|---|---|
| nginx | einziger von außen erreichbarer Dienst; terminiert TLS, liefert `/static/`, puffert langsame Clients | `:80` / `:443`, alle Interfaces |
| gunicorn | führt Django-Code aus (WSGI); Views, Forms, Services, ORM laufen hier | `127.0.0.1:8001` |
| Redis | Broker **und** Result-Backend für Celery, keine Geschäftsdaten | `localhost:6379` |
| Celery | arbeitet Provisioning-Tasks ab, ohne den Request zu blockieren | kein Listener, nur ausgehend |
| PostgreSQL | alle Geschäftsdaten | `127.0.0.1:5432` |

nginx puffert aus einem konkreten Grund: gunicorn hat nur 3 `sync`-Worker, und ein
Worker ist während der gesamten Übertragung an einen langsamen Client belegt. nginx
nimmt den Request vollständig entgegen und reicht ihn in einem Rutsch weiter — der
Python-Worker ist nur für die reine Rechenzeit belegt.

Celery entkoppelt lange Provisioning-Läufe vom Request: Der `ProvisioningService`
legt den Task in Redis ab, die View antwortet sofort, der Worker
(`--concurrency=2`, `deploy/lib.sh:205`) holt den Task und arbeitet ihn asynchron ab.

## 4. TLS-Modus: Zertifikat vorhanden oder nicht

Der Installer erzeugt **kein** self-signed Zertifikat. Er prüft, ob
`/etc/pki/cmp/cmp.crt` existiert und dessen SAN zum FQDN passt
(`cmp_cert_matches_fqdn()`, `deploy/lib.sh:283-290`), und wählt danach den
nginx-Modus. Nur Zertifikate, bei denen Issuer gleich Subject ist, gelten als
installer-eigen und dürfen automatisch ersetzt werden
(`cmp_cert_is_self_signed()`, `deploy/lib.sh:292-300`); ein vom Admin eingespieltes
CA-Zertifikat fasst der Installer nicht an.

| | Zertifikat passt zum FQDN | kein / unpassendes Zertifikat |
|---|---|---|
| Modus | `https` | `http` |
| nginx-Listener | `:80` → 301 auf `:443`, `:443 ssl` | **nur** `:80`, proxyt direkt |
| `CSRF_TRUSTED_ORIGINS` | `https://<fqdn>` | `http://<fqdn>` |
| Cookies | `Secure` | nicht `Secure` (sonst kein Login über HTTP) |

Beleg für den http-Zweig in `deploy/lib.sh:311-321`
(`cmp_env_security_lines()`): Im HTTP-Modus werden `SECURE_SSL_REDIRECT`,
`SESSION_COOKIE_SECURE` und `CSRF_COOKIE_SECURE` explizit auf `False` gesetzt —
sonst würde über reines HTTP weder Session- noch CSRF-Cookie gesendet und der Login
schlägt fehl.

**Ohne Zertifikat existiert kein 443-Listener.** Ein Aufruf von `https://<fqdn>/`
läuft im HTTP-Modus ins Leere (Connection refused), nicht in eine
Zertifikatswarnung — der Installer öffnet Port 443 in firewalld im HTTP-Modus gar
nicht erst. Das ist Absicht: Ein self-signed Zertifikat würde Nutzer daran
gewöhnen, Sicherheitswarnungen wegzuklicken, und ein Redirect auf 443 liefe ohne
Zertifikat ohnehin ins Leere (`deploy/lib.sh`, Kommentar zu `cmp_render_nginx()`:
„kein TLS, KEIN Redirect — ein Redirect auf 443 liefe ohne Zertifikat ins Leere").

Ein Zertifikat lässt sich nachträglich einspielen: `cmp.crt` + `cmp.key` nach
`/etc/pki/cmp/` legen, `install.sh` erneut ausführen. Der Modus wird neu bestimmt.

## 5. Ports auf einen Blick

| Port | Dienst | Bindung | Von außen erreichbar |
|---|---|---|---|
| 443 | nginx (TLS) | alle Interfaces | ja — nur im HTTPS-Modus in firewalld freigegeben |
| 80 | nginx | alle Interfaces | ja — Redirect auf 443 im HTTPS-Modus, direkter Proxy im HTTP-Modus |
| 8001 | gunicorn | `127.0.0.1` | nein |
| 6379 | Redis | `localhost` | nein |
| 5432 | PostgreSQL | `127.0.0.1` | nein |
| — | Celery-Worker | kein Listener | nein — spricht nur ausgehend zu Redis + PostgreSQL |

Nur nginx ist exponiert. Alles dahinter lauscht ausschließlich auf Loopback.

## 6. Zugriff vom Client: immer per FQDN, nie per IP

Der Installer fragt den FQDN ab und schreibt ihn wörtlich nach `/etc/cmp/cmp.env`:

```
ALLOWED_HOSTS=<fqdn>
CSRF_TRUSTED_ORIGINS=http://<fqdn>   (oder https://<fqdn> im HTTPS-Modus)
```

`cmp/config/settings/production.py:40` liest `ALLOWED_HOSTS` direkt aus dieser
Env-Variable (`ALLOWED_HOSTS = env("ALLOWED_HOSTS")`), ohne Fallback. Ein Aufruf
über `http://<ip>/` landet deshalb in Djangos `DisallowedHost` (HTTP 400) —
`ALLOWED_HOSTS` enthält die IP nicht, sofern sie nicht nachträglich ergänzt wurde.
Verwendet werden muss exakt der Name, der bei der Installation eingegeben wurde;
existiert in der Testumgebung kein DNS-Eintrag, muss der Client den Namen über
`/etc/hosts` (Linux/macOS) bzw.
`C:\Windows\System32\drivers\etc\hosts` (Windows) selbst auflösen.

## 7. Entwicklung: ohne nginx, ohne gunicorn

In Entwicklung entfallen nginx, gunicorn und ein eigener Worker-Prozess:
`config.settings.development` startet `manage.py runserver` direkt auf Port 8000.
Celery läuft dort mit `CELERY_TASK_ALWAYS_EAGER` synchron im Request — Redis ist
in Dev optional, in Produktion zwingend (`cmp-docs/docs/betrieb/laufzeit-topologie.md`).

## 8. Zusammenfassung

Nach `install.sh` läuft nur nginx exponiert; gunicorn, Redis und PostgreSQL sind auf
Loopback beschränkt und werden vom Client nie direkt angesprochen — die TLS-Frage
stellt sich damit an genau einer Stelle. Ohne ein zum FQDN passendes Zertifikat gibt
es keinen 443-Listener, keine wegklickbare Warnung, nur einen verweigerten Connect.
Der Zugriff muss über den bei der Installation eingegebenen FQDN erfolgen, ein
IP-Aufruf scheitert an `ALLOWED_HOSTS`. In Entwicklung entfällt die gesamte
Prozesslandschaft zugunsten von `runserver` und synchronem Celery.

> Quelle: cmp-docs/docs/betrieb/laufzeit-topologie.md, deploy/install.sh, deploy/lib.sh, cmp/config/settings/production.py — am Code geprüft 2026-07-22
