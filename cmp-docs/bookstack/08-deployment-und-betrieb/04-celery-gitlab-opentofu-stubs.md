# Celery, GitLab und OpenTofu — was echt ist und was Stub

Die Provisioning-Kette läuft heute gegen simulierte externe Systeme. Dieses
Kapitel trennt genau, was Celery als Infrastruktur wirklich tut, was der
GitLab-Client tatsächlich simuliert, und was von „OpenTofu" im Code überhaupt
existiert — nämlich nicht mehr als ein Feldname.

## 1. Ziel des Kapitels

Wer die Provisioning-Kette in Produktion betreibt oder die Ablösung der Stubs
plant (AP-20), soll hier den geprüften Ist-Stand finden statt der Vermutung
„läuft schon gegen echtes GitLab/OpenTofu".

## 2. Die Kette im Überblick

```
Order (APPROVED)
   |
   v  (heute: kein automatischer Trigger — siehe Abschnitt 5)
dispatch_provisioning.delay(order_id)      [Celery-Task, echt]
   |
   v
ProvisioningService.dispatch_order()       [cmp/apps/provisioning/services.py]
   |
   v
GitLabStubClient.trigger_pipeline()        [In-Memory-Stub, kein HTTP]
   |
   v
DispatchLog (status="running")
   |
   v  (heute: sofort, kein echter Rückkanal — siehe Abschnitt 6)
complete_provisioning.delay(...)           [Celery-Task, echt]
   |
   v
ProvisioningService.complete_dispatch()    -> Order DONE/FAILED
```

## 3. Celery selbst ist echte Infrastruktur, kein Stub

Die beiden Tasks sind reguläre `@shared_task`-Funktionen, die die
Service-Methoden aufrufen — keine Simulation:

```python
# cmp/apps/provisioning/tasks.py:7-16
@shared_task
def dispatch_provisioning(order_id):
    ProvisioningService.dispatch_order(order_id)

@shared_task
def complete_provisioning(dispatch_log_id, success=True):
    ProvisioningService.complete_dispatch(dispatch_log_id, success=success)
```

In Produktion läuft das über einen echten Celery-Worker gegen einen echten
Redis-Broker (`CELERY_TASK_ALWAYS_EAGER = False`, `production.py:49`) — Details
zu Prozess und Port siehe Kapitel 2.3. Nur das **Ziel** der Tasks (der
GitLab-Client) ist simuliert, nicht der Transportweg dorthin.

## 4. `GitLabStubClient` — was er wirklich tut

```python
# cmp/apps/provisioning/clients.py:5-25
class GitLabStubClient:
    def __init__(self):
        self._pipelines = {}

    def trigger_pipeline(self, template_name, parameters):
        pipeline_id = uuid.uuid4().hex[:12]
        self._pipelines[pipeline_id] = "running"
        return {"pipeline_id": pipeline_id, "status": "running"}
    ...
```

Kein HTTP-Aufruf, kein `python-gitlab`, keine Netzwerkabhängigkeit — die
Pipeline-ID ist eine zufällige UUID, der Status lebt nur im Prozessspeicher des
Worker-Prozesses und verschwindet mit ihm. `ProvisioningService.dispatch_order`
importiert diese Klasse **fest** (`from apps.provisioning.clients import
GitLabStubClient`, `cmp/apps/provisioning/services.py:5`) — es gibt aktuell
keine Einstellung, die den Client austauscht.

Ein echter Client (`python-gitlab`, echter API-Aufruf, Token via systemd
`EnvironmentFile=`) ist als **AP-20** vorgemerkt und setzt AP-13 voraus
(`todo.md:122-132`).

## 5. Die Kette ist nicht verdrahtet — AP-13

Wichtiger als der Stub selbst: Der Aufruf `dispatch_provisioning.delay(...)`
passiert im laufenden Betrieb **nirgends automatisch**. Das Genehmigen einer
Bestellung über die Oberfläche löst heute keinen Celery-Task aus — die
entsprechende Verdrahtung ist als offene Lücke in AP-13 vermerkt
(`todo.md:49-50`, „Lücke 2: Ende `ApprovalService.approve` … →
`transaction.on_commit(lambda: dispatch_provisioning.delay(order.pk))`").
Die Tasks selbst sind fertig und getestet, werden aber im Produktivbetrieb
bisher nur aus Tests heraus aufgerufen, nicht aus der Genehmigungs-View.

## 6. `complete_dispatch` schließt sofort ab — kein echter Rückkanal

`GitLabStubClient.complete_pipeline()` markiert eine Pipeline synchron als
erfolgreich oder fehlgeschlagen (`clients.py:21-25`) — es gibt keinen
Polling- oder Webhook-Mechanismus, der den tatsächlichen Fortschritt einer
echten Pipeline abfragt. AP-13 vermerkt das als „Lücke 3: Rückmeldung →
`complete_dispatch`; Stub schließt sofort ab (echter Rückkanal: AP-20)"
(`todo.md:51`). Ein echter GitLab-Client müsste diesen Sofort-Abschluss durch
einen Polling-Task ersetzen (`todo.md:129`).

## 7. `CmdbStubClient` — dasselbe Muster, andere Domäne

Nicht Teil der Dispatch-Kette, aber nach demselben Prinzip gebaut: Der
CMDB-Stub liefert Standorte, Netzwerke und Mandanten aus lokalen YAML-Dateien
(`cmp/apps/cmdb/clients.py`, Daten unter `cmp/stubs/cmdb/`), ohne eine echte
CMDB anzusprechen. Er wird beim Aufbau von Katalog-Parametern verwendet (etwa
für Standort-/Netzwerk-Auswahl), nicht beim Provisioning-Dispatch selbst.

## 8. „OpenTofu" existiert im Code nur als Feldname

Eine gezielte Suche nach `opentofu` im Anwendungscode ergibt **keinen** Treffer
(`grep -rni opentofu cmp/`) — es gibt keinen OpenTofu-Client, kein CLI-Aufruf,
kein HTTP-Call gegen eine OpenTofu-/Terraform-API. Was existiert, ist ein
Metadatenfeld `tofu_variable_name` in der Parameter-Definition jedes
Katalog-Feldes (`cmp/apps/catalog/services.py`, z. B. Zeilen 19, 167, 213) — es
benennt, wie ein Formularfeld später einmal auf eine OpenTofu-Variable
gemappt werden soll, wird aber von keinem Code konsumiert. Die Doku zu einem
echten „OpenTofu-Export" soll laut AP-20 bewusst **erst nach** dem Bau
geschrieben werden, „vorher wäre es abgeschrieben statt geprüft"
(`todo.md:131`).

## 9. Umschaltung Stub → Live ist heute ein Konzept, kein Mechanismus

`cmp-docs/docs/betrieb/stubs-mocks.md` beschreibt den Wechsel als drei Schritte
(Live-Client mit gleichem Interface bauen, Setting ergänzen). Der zweite Teil —
eine konfigurierbare Client-Auswahl — existiert im Code noch nicht: der Import
in `services.py` ist hart verdrahtet, kein `settings.py`-Wert oder
Factory-Funktion wählt zwischen Stub und Live-Client. Das ist Teil dessen, was
AP-20 liefern soll.

## 10. Zusammenfassung

Celery ist reale, produktiv laufende Infrastruktur mit echtem Redis-Broker —
nur ihr heutiges Ziel, der GitLab-Client, ist ein reiner In-Memory-Stub ohne
Netzwerkaufruf. OpenTofu ist im Code nicht als Integration vorhanden, sondern
nur als Namenskonvention in den Katalog-Parametern. Die größere Lücke liegt vor
dem Stub: Die Genehmigung einer Bestellung löst den Dispatch-Task heute nicht
automatisch aus (AP-13), und der Rückkanal wird nur simuliert (ebenfalls
AP-13/AP-20). Ein Stub-zu-Live-Wechsel ist konzeptionell beschrieben, aber ohne
Settings-Umschaltung noch nicht baubar, ohne den Import in `services.py` von
Hand zu ändern.

> Quelle: cmp/apps/provisioning/clients.py, cmp/apps/provisioning/tasks.py, cmp/apps/provisioning/services.py, cmp/apps/cmdb/clients.py, cmp/apps/catalog/services.py, cmp-docs/docs/betrieb/stubs-mocks.md, todo.md (AP-13, AP-20) — am Code geprüft 2026-07-22
