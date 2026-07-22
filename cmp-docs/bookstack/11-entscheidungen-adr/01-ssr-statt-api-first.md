# 11.1 SSR statt API-First

CMP existiert zweimal: als serverseitig gerenderte Django-Anwendung (dieses Projekt) und als
API-First-Variante mit React-SPA (Schwesterprojekt). Diese Seite hält fest, warum CMP Django
bewusst gegen DRF/React entschieden hat, was das kostet, und was CMP dadurch nicht kann.

## 1. Kontext

CMP wird zweimal gebaut, um denselben fachlichen Fall — ein Self-Service-IT-Provisioning-Portal
— mit zwei gegensätzlichen Rendering-Strategien durchzuspielen: **CMP Django** (dieses Projekt,
`lucent-job-mpp-TDD-Django`) rendert HTML auf dem Server. Das Schwesterprojekt `lucent-job-CMP`
liefert ein Headless-JSON-Backend (Flask) an eine React-SPA. `CLAUDE.md` benennt das explizit als
Projektzweck: „Bewusstes Gegenstück zu mpp-TDD: kein API-First, kein React, kein DRF."

Am Code von CMP Django frisch geprüft (2026-07-22): Kein View liefert `JsonResponse`
(`grep -rl "JsonResponse" cmp/apps/*/views.py` — 0 Treffer), es existieren 30 Server-Templates
unter `cmp/templates/` (`find cmp/templates -name "*.html"`), und `django_htmx` ist projektweit
als Middleware verfügbar (`cmp/config/settings/base.py:17,43`), wird aber aktuell nur in 2 von 30
Templates tatsächlich genutzt (`grep -rl "hx-get\|hx-post\|hx-target\|hx-swap" cmp/templates/`).

Die Kennzahlen zum Schwesterprojekt (API-Layer, Routes, Tests) stammen aus
`cmp-docs/docs/referenz/architektur-vergleich.md`, dort laut eigener Angabe „per grep/find am
echten Code beider Repos erhoben (Stand 2026-07-15)". Das Schwesterrepo liegt nicht in diesem
Arbeitsverzeichnis — diese Zahlen sind hier nicht neu nachgeprüft, sondern aus der bestehenden,
selbst code-geprüften Referenzseite übernommen.

## 2. Entscheidung

CMP Django rendert bei jedem Request fertiges HTML über Django-Templates (`render()` /
`TemplateView`). Es gibt keinen JSON-API-Layer, kein DRF, keine Serializer-Schicht. Authentifizierung
läuft über Server-Session (django-allauth), nicht über Token/JWT. HTMX wird punktuell eingesetzt,
um einzelne Seitenbereiche ohne Vollseiten-Reload zu aktualisieren — die Entscheidung dazu fällt
pro View über `request.htmx` (`django_htmx`), nicht als projektweites SPA-Muster.

## 3. Konsequenzen

**Positiv**

- Ein Prozess, eine Sprache (Python + Django-Template-Sprache) — kein zweites Build-Toolchain
  für ein JS-Frontend, kein separates Frontend-Repo/-Deployment.
- Schnelleres First-Paint, weil der Server bereits fertiges HTML schickt statt einer leeren
  SPA-Shell, die erst Daten nachladen muss.
- Kernfunktionen bleiben ohne JavaScript nutzbar (HTMX ist Progressive Enhancement, kein
  Fundament); aktuell betrifft das ohnehin nur 2 von 30 Templates.
- Kein API-Contract zu pflegen (Versionierung, Schema-Drift, Client-Kompatibilität entfallen).

**Negativ — was CMP durch SSR bewusst NICHT kann**

- **Kein wiederverwendbarer API-Layer.** Anders als das Schwesterprojekt (laut
  `architektur-vergleich.md` ein versioniertes `app/api/v1/` mit Blueprints und Routes) hat CMP
  Django keinen JSON-Endpoint, den eine Mobile-App, ein Skript oder ein Drittsystem ansprechen
  könnte. Jede Interaktion läuft über eine HTML-Antwort an genau diesen einen Browser.
- **Interaktivität hängt an Server-Roundtrips.** Ohne eigenen Client-State muss jede dynamische
  Änderung — und sei sie noch so klein — einen Request an den Server schicken. Reiche,
  latenzfreie Client-Interaktion (wie sie eine SPA mit eigenem State bieten kann) ist damit
  strukturell nicht vorgesehen.
- **Kein getrenntes Frontend-Team/-Deployment möglich.** Rendering-Logik und Backend laufen im
  selben Prozess auf Port 8000; Frontend und Backend lassen sich nicht unabhängig versionieren
  oder ausrollen.
- **Progressive Enhancement ist heute Stückwerk.** `django_htmx` steht projektweit bereit, wird
  aber erst in 2 von 30 Templates genutzt — der große Rest arbeitet mit klassischen
  Vollseiten-Requests und Redirects. Wer volle SPA-artige Dynamik erwartet, findet sie nicht.

## 4. Alternativen

- **DRF zusätzlich zu den Templates betreiben** (verworfen): zwei Contracts (HTML + JSON) parallel
  zu pflegen widerspricht dem Zweck des Experiments, gerade *keinen* API-Layer zu bauen, und hätte
  den Vergleich mit dem Schwesterprojekt verwässert.
- **API-First wie das Schwesterprojekt** (verworfen, da genau das die Vergleichsvariante ist,
  nicht die eigene Wahl): Flask + React + JWT bringt FE/BE-Entkopplung und Mobile-Tauglichkeit,
  kostet aber laut `architektur-vergleich.md` zwei Deployments/Toolchains und einen zu pflegenden
  API-Contract — das ist der Trade-off, den CMP Django bewusst nicht eingeht.
- **HTMX sofort projektweit ausrollen** (nicht getan): Die Middleware ist verfügbar, wird aber
  schrittweise nur dort eingesetzt, wo ein Vollseiten-Reload spürbar stört (aktuell Katalog- und
  Audit-Ansicht) — kein Big-Bang-Umbau aller 30 Templates.

## 5. Status

Akzeptiert und unverändert seit Projektbeginn — es handelt sich um die Gründungsentscheidung des
Projekts (`CLAUDE.md`), keine Revision ist geplant. Der Umfang von HTMX-Einsatz (Punkt 3, letzter
Absatz) ist der einzige Teil, der sich mit wachsender Oberfläche noch verschiebt.

> Quelle: `CLAUDE.md`, `cmp-docs/docs/referenz/architektur-vergleich.md`, `cmp/config/settings/base.py:17,43`, `cmp/apps/*/views.py`, `cmp/templates/` — am Code geprüft 2026-07-22
