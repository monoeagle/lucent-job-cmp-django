# Glossar

Dieses Kapitel erklärt die Fachbegriffe, die in Kapitel 1 und den folgenden Kapiteln
wiederkehren — je Begriff mit einer kurzen Definition und der Codestelle, die ihn
tatsächlich abbildet.

## 1. Ziel des Kapitels

Wer beim Lesen über einen Begriff stolpert, den er nicht zuordnen kann, soll hier
nachschlagen können, welches Modell, welche Klasse oder welches Konzept dahinter steht
— statt einer Umschreibung eine konkrete `datei.py:zeile`-Stelle.

## 2. Bestellung, Bestellposition und Mehrfachbestellung

**Bestellung / Order** ist der Kopf einer Anfrage mit Status und Ersteller. Sie durchläuft
eine Statuskette von `draft` bis `done`/`failed`/`rejected`
(`cmp/core/domain/value_objects.py:5-14`, `OrderStatus`) und ist als Klasse `Order`
abgebildet (`cmp/apps/orders/models.py:9`).

**OrderItem** ist eine einzelne Position innerhalb einer Order — ein bestelltes
`ServiceTemplate` mit den dazu befüllten Parametern (`cmp/apps/orders/models.py:51`).
Eine Order kann mehrere OrderItems enthalten.

`OrderItemGroup` bündelt mehrere gleichartige OrderItems mit gemeinsamen Parametern und
einer Anzahl (`quantity`), z. B. bei einer Mehrfachbestellung derselben VM-Größe
(`cmp/apps/orders/models.py:32-45`).

## 3. ServiceTemplate und Parameter

**ServiceTemplate** ist ein Katalogeintrag — Name, Kategorie und ein JSON-Parameterschema,
aus dem das Bestellformular zur Laufzeit erzeugt wird (`cmp/apps/catalog/models.py:14`).

**Parameter** ist ein einzelner Eintrag in diesem JSON-Schema, kein eigenes Datenbankfeld.
Jeder Parameter trägt mindestens `key`, `label`, `type` und `required`, dazu optional
`default`, `group`, `display_order`, `constraints.options`, `depends_on`,
`affects_options_of` und `tofu_variable_name` — die vorgegebene Liste `SHARED_PARAMS` in
`cmp/apps/catalog/services.py:15-28` zeigt alle diese Felder an einem echten Beispiel
(`system_type`). `ServiceTemplate.parameters` selbst ist ein `JSONField(default=list)`
(`cmp/apps/catalog/models.py:18`); zur Laufzeit baut `OrderParameterForm` daraus die
Formularfelder (`cmp/apps/orders/forms.py:12-30`).

## 4. Genehmigung: ApprovalRule und ApprovalRequest

**ApprovalRule** legt fest, unter welcher Bedingung (`condition`, JSON) ein Template eine
Genehmigung durch welche Rolle (`approver_role`) benötigt (`cmp/apps/approvals/models.py:7`).

**ApprovalRequest** ist die einzelne Genehmigungsentscheidung zu einer konkreten Order —
mit Status, verweisender Regel und dem entscheidenden Benutzer (`decided_by`)
(`cmp/apps/approvals/models.py:27`). Genehmigt/abgelehnt wird sie über
`ApprovalService.approve`/`ApprovalService.reject`
(`cmp/apps/approvals/services.py:49`, `:75`).

## 5. Provisioning

**Provisioning** bezeichnet den (Ziel-)Schritt, aus einer genehmigten Bestellung eine
laufende Ressource aufzubauen. Im Code existiert dafür `DispatchLog` als Protokoll eines
Pipeline-Dispatch je Bestellposition (`cmp/apps/provisioning/models.py:7-19`) sowie der
`GitLabStubClient`, der einen Pipeline-Trigger simuliert statt ihn real auszuführen
(`cmp/apps/provisioning/clients.py:5`). Der automatische Übergang von einer genehmigten
Order zu einem Dispatch ist aktuell nicht verdrahtet (AP-13, siehe Kapitel 3).

## 6. Subscription

**Subscription** ist ein aktives Abonnement, das aus einem `OrderItem` entsteht und Status
sowie Gültigkeitszeitraum trägt (`cmp/apps/subscriptions/models.py:8-22`). Für eine
`OrderItemGroup` existiert analog `GroupSubscription`
(`cmp/apps/subscriptions/models.py:33-45`). Beide werden aktuell nur über `seed.py`
angelegt, nicht automatisch nach einem abgeschlossenen Provisioning (siehe Kapitel 3).

## 7. Mandant/Tenant und Kontext

**Mandant/Tenant** ordnet einen Benutzer einem Mandanten zu — Modell
`UserTenantAssignment` mit Feld `tenant` (`cmp/apps/cmdb/models.py:41-47`). Getrennt davon
kann eine `AvailabilityRule` ein Template für einen Mandanten sperren, ebenfalls über ein
`tenant`-Feld (`cmp/apps/cmdb/models.py:7-15`). Im Bestellformular taucht „Mandant"
zusätzlich als gewöhnlicher Parameterwert auf (`mandant`-Schlüssel in `SHARED_PARAMS`,
`cmp/apps/catalog/services.py:29-38`) — das ist ein anderes Feld als die
CMDB-Mandantenzuordnung, auch wenn beide denselben deutschen Begriff verwenden.

**Kontext** meint die Kombination aus Standort, Mandant und Sicherheitszone, die vor der
Parametereingabe abgefragt wird — Formular `ContextForm`
(`cmp/apps/orders/forms.py:65-79`), beliefert vom `CmdbStubClient`
(`cmp/apps/cmdb/clients.py:8`).

## 8. HTMX, SSR und Stub

**HTMX** liefert die punktuellen Oberflächen-Updates ohne vollständigen Seiten-Reload.
Es ist als `django_htmx` in `INSTALLED_APPS` sowie als `HtmxMiddleware` eingebunden
(`cmp/config/settings/base.py:17,43`); Views prüfen `request.htmx`, um zwischen
Voll- und Partial-Template zu unterscheiden (`cmp/apps/catalog/views.py:26`).

**SSR** (Server-Side Rendering) bezeichnet das Grundprinzip von CMP: Django rendert
fertiges HTML (`render()`), es gibt keinen JSON-Endpunkt im Anwendungscode — eine Prüfung
aller Views (`grep -rn "JsonResponse" cmp/apps`) findet keinen Treffer. Details und
Abgrenzung zum API-First-Schwesterprojekt stehen in Kapitel 1, Abschnitt 4.

**Stub** bezeichnet einen Ersatz für eine externe Abhängigkeit, der im Prozess bleibt statt
einen echten Netzwerkaufruf zu machen — z. B. `GitLabStubClient`
(`cmp/apps/provisioning/clients.py:5-19`, In-Memory-Dict statt GitLab-API) und
`CmdbStubClient` (`cmp/apps/cmdb/clients.py:8-16`, liest YAML-Dateien statt eine echte
CMDB anzufragen).

## 9. Zusammenfassung

Die Begriffe folgen der Bestellkette: ein `ServiceTemplate` mit `Parameter`n wird über
`Order`/`OrderItem` bestellt, durchläuft optional eine `ApprovalRule`/`ApprovalRequest`,
soll anschließend `Provisioning` auslösen und in einer `Subscription` enden — eingebettet
in `Mandant`/`Kontext`. Technisch trägt `HTMX` die Oberfläche, `SSR` das Rendering-Prinzip,
und `Stub`s ersetzen alle externen Systeme, solange keine echten Anbindungen existieren.

> Quelle: cmp/apps/orders/models.py, cmp/apps/catalog/models.py, cmp/apps/catalog/services.py, cmp/apps/orders/forms.py, cmp/apps/approvals/models.py, cmp/apps/approvals/services.py, cmp/apps/provisioning/models.py, cmp/apps/provisioning/clients.py, cmp/apps/subscriptions/models.py, cmp/apps/cmdb/models.py, cmp/apps/cmdb/clients.py, cmp/config/settings/base.py, cmp/apps/catalog/views.py, cmp/core/domain/value_objects.py — am Code geprüft 2026-07-22
