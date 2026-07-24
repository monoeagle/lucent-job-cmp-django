# 02 — Ziele & Anforderungen

> **In diesem Kapitel:** Du kennst aus [Kapitel 01](01-das-grosse-bild.md) jetzt
> das große Bild — Katalog, Bestellung, Genehmigung, Provisioning, Subscription.
> Dieses Kapitel geht einen Schritt zurück und fragt: **Welches Problem löst
> CMP eigentlich, und was genau soll das System können?**
>
> **Das lernst du:**
> - Welches reale Problem CMP ersetzt
> - Die Kernprinzipien, nach denen CMP gebaut ist — und warum
> - Welche Anwendungsfälle es je Rolle grob gibt (Details in Kapitel 04)
> - Welche funktionalen und nicht-funktionalen Anforderungen in **v1.5.0**
>   bereits umgesetzt sind — und welche noch offen sind
>
> **Voraussetzung:** [01 — Das große Bild](01-das-grosse-bild.md)

---

## Das Problem, das CMP löst

Ohne ein Portal wie CMP läuft die Beschaffung einer IT-Ressource — einer
virtuellen Maschine, einer Datenbank, eines Containers — heute typischerweise
über Ticket- oder Mail-Prozesse: Jemand schreibt eine Anfrage, ein Kollege aus
dem Ops-Team liest sie irgendwann, prüft sie manuell, klickt sich durch ein
internes Tool und meldet sich zurück. Das dauert, ist fehleranfällig und lässt
sich kaum nachvollziehen.

CMP ersetzt diesen Ablauf durch vier Bausteine, die ineinandergreifen: einen
**Katalog** mit parametrischen Service-Vorlagen, einen **Bestellassistenten**,
einen **regelbasierten Genehmigungs-Workflow** und **automatisiertes
Provisioning** am Ende der Kette.

💡 **Merke:** CMP macht aus einem manuellen, mail-basierten Prozess einen
Self-Service-Ablauf — der Mensch bestellt, das System prüft, genehmigt (falls
nötig) und setzt um.

---

## Was CMP ist

CMP ist ein **Self-Service-IT-Provisioning-Portal**: Nutzer wählen einen
Service aus einem Katalog, füllen ein aus dem Service-Schema dynamisch
erzeugtes Formular aus und reichen eine Bestellung ein. Je nach hinterlegter
Regel durchläuft die Bestellung eine Genehmigung, bevor die Ressource
aufgebaut wird.

| Baustein | Zweck |
|---|---|
| Service-Katalog | Vorlagen mit parametrischem JSON-Schema (`ServiceTemplate`) |
| Bestellwizard | Dynamische Formulare aus den Template-Parametern |
| Approval-Workflow | Regelbasierte Genehmigung durch die Rolle Approver |
| Provisioning | Asynchrone Ausführung über Celery, Pipeline-Trigger (aktuell **Stub**, siehe [Kapitel 01](01-das-grosse-bild.md)) |
| Subscriptions | Verwaltung laufender, aus Bestellungen entstandener Services |
| Audit-Log | Protokoll von Statuswechseln und Aktionen |

---

## Kernprinzipien

CMP ist als **serverseitig gerenderte Anwendung** gebaut: Django rendert die
komplette Oberfläche als fertiges HTML, HTMX übernimmt punktuelle Updates
(z. B. einen Bestell-Schritt nachladen), ohne dass dafür ein eigener
JSON-Layer nötig wäre. Die Anmeldung läuft session-basiert über
`django-allauth`. Daraus ergeben sich die Prinzipien, an denen sich der
gesamte Code orientiert:

- **Server-Side Rendering** — die Oberfläche funktioniert grundsätzlich ohne
  clientseitiges Framework; HTMX ergänzt sie um punktuelle Interaktivität,
  ersetzt sie aber nicht (mehr dazu in [Kapitel 08](08-frontend-htmx-daisyui.md)).
- **Thin Views** — Geschäftslogik liegt in `services.py`, nicht in Views oder
  Models (`views.py → services.py → models.py`).
- **Django Admin als primäres Admin-Werkzeug** — Katalog, Genehmigungsregeln
  und Nutzer werden bewusst über den eingebauten Django-Admin gepflegt, statt
  eine eigene Verwaltungsoberfläche dafür zu bauen.
- **Kein offenes Self-Signup** — `ACCOUNT_SIGNUP_ENABLED = False`
  (`cmp/config/settings/base.py`). Neue Nutzer legt ausschließlich ein Admin an.
- **TDD ist Pflicht** — jede Änderung entsteht test-first
  (siehe [Kapitel 10](10-so-arbeiten-wir.md)).

> 🔍 **Im Code nachsehen:** Diese Prinzipien stehen nicht nur so im Kopf der
> Autoren — sie sind in `CLAUDE.md` und `.claude/rules/django.md` schriftlich
> festgehalten und werden dort auch von KI-Werkzeugen als Leitplanke gelesen.

---

## Anwendungsfälle (kurz)

Die typischen Abläufe folgen den drei Rollen aus Kapitel 01:

- Ein **Requester** durchsucht den Katalog, stellt eine Bestellung aus einer
  oder mehreren Positionen zusammen und reicht sie ein.
- Ein **Approver** sieht offene Genehmigungsanfragen in einer Queue und
  entscheidet — zustimmen oder ablehnen.
- Ein **Admin** pflegt Katalog, Genehmigungsregeln und Nutzer über den
  Django-Admin und sieht Auswertungen im Admin-Dashboard.

Wer genau welche Rolle hat, wie die Rollen aufeinander aufbauen und welche
konkreten Views dahinterstehen, ist Thema von
[Kapitel 04 — Rollen & Rechte](04-rollen-und-rechte.md). Hier reicht der
Überblick, um die folgenden Anforderungen einordnen zu können.

---

## Funktionale Anforderungen

Die folgende Tabelle zeigt die wichtigsten funktionalen Anforderungen mit
ihrem Stand in **v1.5.0**. „Umgesetzt" heißt: im Code vorhanden *und* über die
Oberfläche erreichbar. „Teilweise" heißt: der Baustein existiert, deckt den
Anwendungsfall aber nicht vollständig ab. „Geplant" heißt: noch nicht gebaut.

| Anforderung | Status (v1.5.0) |
|---|---|
| Bestellformular aus Katalog-Vorlage anzeigen | Umgesetzt |
| Bestellung einreichen, löst bei Bedarf Genehmigung und danach Provisioning aus | Umgesetzt — siehe [Kapitel 05](05-bestell-lebenszyklus.md) |
| Bestellungsübersicht mit Status und Filter auf eigene Bestellungen | Umgesetzt |
| Bestellung bearbeiten (Positionen hinzufügen/entfernen) | Teilweise — nur Positionen, keine Bearbeitung der Bestellung selbst |
| Bestellung löschen | Geplant — es lässt sich nur eine einzelne Position entfernen, nicht die ganze Bestellung |
| Genehmigungs-Queue, Zustimmen/Ablehnen mit Benachrichtigung des Bestellers | Umgesetzt |
| Produktkatalog: Vorlagen anzeigen | Umgesetzt |
| Produktkatalog: Vorlagen anlegen/bearbeiten/löschen | Umgesetzt — über Django Admin |
| Parameter-Verwaltung als eigene Oberfläche | Teilweise — Parameter sind ein JSON-Feld am Template, keine eigene Verwaltungs-UI |
| Anmeldung mit Session-Authentifizierung, kein Self-Signup | Umgesetzt |
| Nutzerverwaltung (anlegen/bearbeiten/löschen) | Umgesetzt — über Django Admin |
| Anbindung Active Directory | Geplant |
| Systembenachrichtigungen bei Genehmigungsschritten | Umgesetzt |
| Anbindung eines echten Provisioning-Backends (z. B. OpenTofu/GitLab) | Geplant — aktuell simuliert (`GitLabStubClient`) |
| E-Mail-Versand | Geplant |
| Massenbestellung (mehrere Instanzen einer Vorlage) | Umgesetzt — über `OrderItemGroup` |

💡 **Merke:** Die Kette „Bestellung einreichen → Genehmigung anfordern →
provisionieren → Subscription anlegen → protokollieren → benachrichtigen" ist
in v1.5.0 **durchgängig verdrahtet** — `OrderService.submit_order` erzeugt bei
Bedarf Genehmigungsanfragen und benachrichtigt die Approver,
`ApprovalService.approve()` löst nach der letzten Zustimmung automatisch das
Provisioning aus und benachrichtigt den Besteller. Details dazu — inklusive
der Service-Methoden, die jeden Schritt auslösen — findest du in
[Kapitel 05](05-bestell-lebenszyklus.md).

---

## Nicht-funktionale Anforderungen

| Bereich | Status (v1.5.0) | Detail |
|---|---|---|
| Session-basierte Authentifizierung, kein offenes Self-Signup | Umgesetzt | `django-allauth`, `ACCOUNT_SIGNUP_ENABLED = False` |
| Rollenbasierte Zugriffskontrolle | Umgesetzt | Vier Rollen, vier Mixins — siehe [Kapitel 04](04-rollen-und-rechte.md) |
| Sichere Cookies / TLS-Redirect in Produktion | Umgesetzt | Über `django-environ` konfigurierbar, siehe [Kapitel 12](12-wie-es-in-produktion-laeuft.md) |
| CSP-Header / Rate-Limiting gegen Brute-Force | Geplant | Noch kein `django-csp` oder Rate-Limiting-Paket eingebunden |
| Strukturiertes Anwendungs-Logging | Geplant | Noch keine `LOGGING`-Konfiguration; Prozess-Logs laufen über `journald` |
| Nachvollziehbarkeit über ein Audit-Log | Umgesetzt | Jeder Statuswechsel einer Bestellung schreibt einen Audit-Eintrag zentral über `transition()`, siehe [Kapitel 05](05-bestell-lebenszyklus.md) |
| Konfiguration ohne hardcodierte Secrets | Umgesetzt | Alle sicherheitsrelevanten Werte kommen über `django-environ` aus der Umgebung |
| `DEBUG=True` in Produktion ausgeschlossen | Umgesetzt | `DEBUG` per Default `False`; als FATAL-Regel auch in `CLAUDE.md` festgehalten |
| Asynchrone Provisioning-Tasks blockieren keinen Request | Umgesetzt | Celery + Redis, Details in [Kapitel 07](07-async-und-provisioning.md) |
| Nativer Betrieb ohne Container (Single-VM) | Umgesetzt | systemd-Units, nginx als TLS-Terminierung — Details in [Kapitel 12](12-wie-es-in-produktion-laeuft.md) |
| Dokumentiertes, automatisiertes Datenbank-Backup | Teilweise | Backup als Vorgehen dokumentiert, aber nicht Teil eines automatisierten Zeitplans |
| Testabdeckung als Qualitätssicherung | Umgesetzt | TDD projektweit Pflicht, externe Abhängigkeiten über Stub-Clients ersetzt — siehe [Kapitel 10](10-so-arbeiten-wir.md) |

⚠️ **Achtung:** „Umgesetzt" heißt hier nicht „fertig für jeden denkbaren
Angriff oder jede Betriebssituation" — es heißt, dass die Anforderung im
aktuellen Code nachweisbar erfüllt ist. Wo etwas nur teilweise oder gar nicht
umgesetzt ist, steht das bewusst so da, statt es zu beschönigen.

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Projektprinzipien im Überblick | `CLAUDE.md` |
| Django-, HTMX- und Test-Konventionen | `.claude/rules/django.md`, `.claude/rules/htmx.md`, `.claude/rules/testing.md` |
| Kein Self-Signup | `cmp/config/settings/base.py` (`ACCOUNT_SIGNUP_ENABLED`) |
| Bestellung einreichen, inkl. Genehmigungsanstoß | `cmp/apps/orders/services.py` (`OrderService.submit_order`) |
| Genehmigen, inkl. Provisioning-Anstoß | `cmp/apps/approvals/services.py` (`ApprovalService.approve`) |

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Welches konkrete Problem aus dem Alltag ersetzt CMP?
2. Nenne zwei Kernprinzipien, nach denen CMP gebaut ist.
3. Ist die Kette „Bestellung → Genehmigung → Provisioning" in v1.5.0 bereits
   verdrahtet, oder muss sie erst noch gebaut werden?

<details>
<summary>Antworten anzeigen</summary>

1. Manuelle Ticket- oder Mail-Prozesse für die Beschaffung von IT-Ressourcen
   wie virtuellen Maschinen oder Datenbanken.
2. Zum Beispiel: Server-Side Rendering statt eines eigenen JSON-Layers, Thin
   Views (Logik in Services), Django Admin als primäres Admin-Werkzeug, kein
   offenes Self-Signup, TDD-Pflicht.
3. Sie ist bereits verdrahtet: `submit_order` stößt bei Bedarf die Genehmigung
   an, `approve()` stößt nach der letzten Zustimmung automatisch das
   Provisioning an.

</details>

---

⟵ [01 — Das große Bild](01-das-grosse-bild.md) · [📖 Übersicht](README.md) · [03 — Die Fachdomäne](03-fachdomaene.md) ⟶
