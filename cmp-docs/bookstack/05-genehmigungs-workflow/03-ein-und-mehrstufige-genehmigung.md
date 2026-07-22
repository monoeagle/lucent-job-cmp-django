# Ein- und mehrstufige Genehmigung

„Mehrstufig" kann zweierlei heißen: mehrere Genehmiger, die alle zustimmen
müssen, oder eine Reihenfolge, in der Stufe 2 einen Antrag erst sieht, wenn
Stufe 1 zugestimmt hat. Dieses Kapitel trennt, was das Datenmodell von CMP
trägt, von dem, was heute tatsächlich verdrahtet ist — beides ist nicht
dasselbe.

## 1. Ziel des Kapitels

Wer plant, eine mehrstufige Freigabe einzuführen (etwa: erst Fachbereich, dann
IT-Leitung), muss wissen, worauf er aufbaut — und worauf nicht. Diese Seite
verhindert die Annahme, ein Sequenz- oder Stufenkonzept sei bereits vorhanden.

## 2. Was das Datenmodell trägt

`ApprovalRequest` (`cmp/apps/approvals/models.py:32-56`) hat kein Feld für
Reihenfolge, Priorität oder Stufe. Geprüft per `grep -n
"stage\|sequence\|order_index\|priority\|level" cmp/apps/approvals/models.py
cmp/apps/approvals/migrations/0001_initial.py` — kein Treffer. Das Modell kennt
ausschließlich `order`, `rule`, `status`, `decided_by`, `decided_at`, `comment`
und die geerbten Zeitstempel (vollständige Referenz:
[Kapitel 3.4](../03-domaenenmodell-und-apps/04-genehmigung-approvalrequest.md)).
`Meta.ordering = ["-created_at"]` sortiert nur die Anzeige, es steuert keine
Ausführungsreihenfolge.

Was das Modell **wohl** trägt: beliebig viele `ApprovalRule`-Zeilen je Template
(kein `unique_together`, siehe [Seite 2](02-wer-genehmigt-was.md)) — und damit
beliebig viele parallele `ApprovalRequest`-Zeilen je Bestellung.

## 3. Was `create_approval_requests` tatsächlich tut

`ApprovalService.create_approval_requests` (`apps/approvals/services.py:26-48`)
iteriert über **alle** aktiven, passenden Regeln in einer einzigen Schleife und
legt für jede sofort einen `ApprovalRequest` mit `status="pending"` an
(`services.py:38-40`). Es gibt keine Bedingung wie „lege Antrag 2 erst an, wenn
Antrag 1 entschieden ist" — alle Anträge einer Bestellung entstehen im selben
Methodenaufruf, gleichzeitig, mit demselben Startstatus.

## 4. Was `approve`/`reject` daraus machen

`ApprovalService.approve` (`services.py:83-97`) lädt die Anfrage seit AP-22
zunächst über `_load_pending` (Kapitel 5.4) — das prüft Status **und**
`rule.approver_role` — und wertet danach den Gesamtzustand der Bestellung aus:

```python
all_reqs = ApprovalRequest.objects.filter(order=order)
if (
    not all_reqs.filter(status="pending").exists()
    and not all_reqs.filter(status="rejected").exists()
):
    order.status = OrderStatus.APPROVED
```

Das ist eine **UND-Verknüpfung ohne Reihenfolge**: Die Order wird erst
`approved`, wenn *alle* zugehörigen Anträge entschieden und *keiner* davon
`rejected` ist — unabhängig davon, in welcher Reihenfolge die Genehmiger das
tun. `ApprovalService.reject` (`services.py:100-109`) lädt ebenfalls über
`_load_pending` und setzt die Order dagegen **sofort** auf `rejected`, sobald
irgendein Antrag abgelehnt wird — auch wenn andere Anträge derselben Bestellung
noch `pending` sind. Die `approver_role`-Prüfung in `_load_pending` ändert daran
nichts: Sie entscheidet nur, *wer* einen einzelnen Antrag entscheiden darf, nicht
*wie* die UND-Verknüpfung über mehrere Anträge funktioniert.

## 5. Einstufig vs. mehrstufig — was der Begriff hier bedeutet

| Fall | Trifft das Datenmodell? | Was passiert |
|---|---|---|
| Ein Template, eine aktive Regel | ja, Standardfall | Ein `ApprovalRequest`, eine Entscheidung ist final |
| Ein Template, mehrere aktive Regeln | ja, technisch zulässig | Mehrere parallele Anträge, alle müssen zustimmen (UND), einer reicht zum Ablehnen |
| Stufe 2 sieht Antrag erst nach Zustimmung von Stufe 1 (sequenziell) | **nein** | Kein Feld, keine Prüfung dafür — `ApprovalQueueView` zeigt alle `pending`-Anträge gleichzeitig (`apps/approvals/views.py:18-25`) |
| Derselbe Genehmiger darf nicht zweimal entscheiden (Vier-Augen-Prinzip) | **nein** | `approve`/`reject` prüfen nur `status != "pending"`, nicht den Entscheider vorheriger Anträge |

„Mehrstufig" ist bei CMP also im Sinn von **mehreren parallelen Genehmigern
(UND-Bedingung)** vorhanden, nicht im Sinn einer **sequenziellen Stufenfolge**.
Das ist keine im `todo.md` als eigenes Arbeitspaket geführte Lücke — es ist eine
Grenze des heutigen Datenmodells, die vor einer Erweiterung bekannt sein muss.

## 6. Praxisbeispiel

Zwei aktive `ApprovalRule`-Zeilen für dasselbe Template, `approver_role`
`"admin"` und `"approver"`: `create_approval_requests` legt zwei
`ApprovalRequest`-Zeilen gleichzeitig an, die Order wechselt zu
`pending_approval`. Seit AP-22 prüft `_load_pending` bei jeder Entscheidung
`req.rule.approver_role` gegen die Rolle des Entscheiders — ein Nutzer mit Rolle
`approver` kann also nur noch den Antrag mit `approver_role="approver"`
entscheiden, `ForbiddenError` blockiert ihn beim zweiten mit
`approver_role="admin"`. Erst wenn beide `approved` sind, wechselt die Order zu
`approved`; lehnt einer der beiden ab, wechselt sie sofort zu `rejected`, auch
wenn der andere Antrag noch offen ist.

**Eine Falle, die die Prüfung selbst mitbrachte — inzwischen geschlossen:**
`_load_pending` ruft `AccountService.is_at_least_role(approver.role,
req.rule.approver_role)` auf, das intern `ROLE_HIERARCHY.index(minimum_role)`
nachschlägt (`apps/accounts/services.py:5-9,43-50`) und bei einem `ValueError` —
also bei jedem Wert, der nicht exakt `requester`, `approver`, `admin` oder
`superadmin` ist — `False` zurückgibt. Solange `approver_role` Freitext war,
hätte ein Wert wie das eingangs dieses Abschnitts in einer früheren Fassung
genannte `approver_role="netzwerk"` damit **für jeden Nutzer, einschließlich
`superadmin`,** `ForbiddenError` ausgelöst — der Antrag wäre praktisch von
niemandem mehr entscheidbar gewesen. Eine zweite Korrektur schließt das: Das
Feld trägt jetzt `choices=UserRole.choices` (`apps/approvals/models.py:20-22`,
Migration `0002_alter_approvalrule_approver_role.py`), und `_load_pending`
weist einen Regelwert außerhalb der vier Rollen **vor** der Rollenprüfung mit
`ConflictError` als Konfigurationsfehler zurück (`services.py:68-75`):

```python
verlangt = req.rule.approver_role
if verlangt not in UserRole.values:
    raise ConflictError(
        f"Regel {req.rule_id} nennt die unbekannte Rolle '{verlangt}' — "
        "die Anfrage ist so von niemandem entscheidbar."
    )
```

Ein `approver_role="netzwerk"` ist damit kein unentscheidbarer Antrag mehr,
sondern eine sofort als solche erkennbare, fehlerhafte Regel.

## 7. Zusammenfassung

Das Datenmodell erlaubt mehrere parallele Genehmigungsanträge je Bestellung und
verknüpft sie als UND-Bedingung — alle müssen zustimmen, einer reicht zum
Ablehnen. Eine Reihenfolge oder Stufung zwischen mehreren Anträgen und ein
Vier-Augen-Ausschluss existieren weiterhin nicht. Eine Rollenprüfung existiert
seit AP-22 zusätzlich pro Antrag (`approver_role` gegen die Rolle des
Entscheiders); seit `choices=UserRole.choices` und dem vorgelagerten
`ConflictError` in `_load_pending` kann ein Regelwert außerhalb der vier Rollen
nicht mehr zu einer für alle unentscheidbaren Anfrage führen, sondern nur noch
zu einem klar gemeldeten Konfigurationsfehler. Wer ein echtes mehrstufiges
Freigabekonzept braucht, baut auf einem heute nicht vorhandenen Sequenzfeld auf
— nicht auf `ApprovalRule`/`ApprovalRequest`, wie sie jetzt sind.

> Quelle: cmp/apps/approvals/models.py, cmp/apps/approvals/migrations/0001_initial.py, cmp/apps/approvals/migrations/0002_alter_approvalrule_approver_role.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/accounts/services.py — am Code geprüft 2026-07-22
