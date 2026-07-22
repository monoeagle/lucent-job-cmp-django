# Wer genehmigt was — ApprovalRule

`ApprovalRule` entscheidet, ob eine Bestellung überhaupt eine Genehmigung
braucht, und `approver_role` beschreibt, wer sie erteilen soll. Dieses Kapitel
prüft am Code, wie weit „soll" und „wird durchgesetzt" hier auseinanderliegen.

## 1. Ziel des Kapitels

Wer eine neue Genehmigungsregel anlegt, muss wissen, nach welchem Kriterium sie
tatsächlich greift — und wer eine Genehmigungs-Warteschlange betreut, muss
wissen, ob ein Nutzer dort nur „seine" Anträge sieht oder alle. Die Feldreferenz
selbst steht in [Kapitel 3.4](../03-domaenenmodell-und-apps/04-genehmigung-approvalrequest.md)
und wird hier nicht wiederholt.

## 2. Das einzige harte Kriterium: `template_id`

`ApprovalService.needs_approval` und `.create_approval_requests`
(`cmp/apps/approvals/services.py:15-24`, `:26-48`) ermitteln zunächst die
`template_id`-Werte aller `OrderItem`-Zeilen der Bestellung und filtern dann:

```python
ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True)
```

Das ist die gesamte Zuordnungslogik. Es gibt keinen weiteren Filter — weder auf
Bestellwert, Menge noch Abteilung. Das Feld `condition`
(`apps/approvals/models.py:16`) existiert für genau solche Zusatzkriterien,
wird aber an keiner Stelle ausgewertet — das ist bereits in
[Kapitel 3.4 Abschnitt 5](../03-domaenenmodell-und-apps/04-genehmigung-approvalrequest.md)
belegt und gilt unverändert für diese Seite: „wer genehmigt was" hängt heute
ausschließlich am Template, nicht an Regeln, die von den Bestelldaten abhängen.

## 3. `approver_role` — seit AP-22 durchgesetzt beim Entscheiden

`approver_role` war bis kurz nach AP-22 ein `CharField(max_length=20)` ohne
`choices=` — ein Freitext-Wert wie z. B. `"approver"`. Bis AP-22 fand sich der
Wert nur an vier Stellen im Code (Modell-Definition, Admin-Konfiguration,
Migration, Seed-Kommando), aber keine davon las ihn, um zu entscheiden, wer eine
konkrete `ApprovalRequest`-Zeile bearbeiten darf.

Seit AP-22 tut das eine fünfte Stelle: `ApprovalService._load_pending`
(`apps/approvals/services.py:51-80`), die sowohl `approve` als auch `reject`
zuerst aufrufen. Sie lädt die Anfrage inklusive `rule` und vergleicht die Rolle
des Entscheiders gegen `req.rule.approver_role`:

```python
verlangt = req.rule.approver_role
if not AccountService.is_at_least_role(approver.role, verlangt):
    raise ForbiddenError(
        f"Diese Entscheidung verlangt die Rolle '{verlangt}'."
    )
```

Reicht die Rolle nicht, wirft die Methode `ForbiddenError`
(`core/exceptions.py:24-25`), die beide Views neben `ConflictError` und
`NotFoundError` abfangen (`apps/approvals/views.py:38`, `:53`).

Eine zweite, spätere Korrektur schließt eine Lücke, die diese Rollenprüfung
selbst mitbrachte: `approver_role` ist inzwischen kein Freitext mehr, sondern
trägt `choices=UserRole.choices` (`apps/approvals/models.py:20-22`, Migration
`0002_alter_approvalrule_approver_role.py`), und `_load_pending` weist einen
Regelwert außerhalb der vier Rollen vor der eigentlichen Rollenprüfung mit
`ConflictError` als Konfigurationsfehler zurück (`services.py:68-75`) — die in
[Seite 3](03-ein-und-mehrstufige-genehmigung.md) beschriebene, für niemanden
entscheidbare Regel kann so nicht mehr entstehen.

Unverändert bleibt, wer die Warteschlange überhaupt **sieht**: Die Zugriffsprüfung
auf `/approvals/` selbst läuft weiterhin über die Nutzerrolle
(`core/domain/enums.py:5-9`, `UserRole`: `requester`, `approver`, `admin`,
`superadmin`) und `ApproverRequiredMixin`
(`core/mixins.py:70-76`, akzeptiert `APPROVER`, `ADMIN`, `SUPERADMIN`).
`ApprovalQueueView.get_queryset` (`apps/approvals/views.py:18-25`) filtert nach
wie vor ausschließlich nach `status` (Query-Parameter, Default `pending`) — nicht
nach `rule.approver_role` und nicht nach dem eingeloggten Nutzer. Ein Approver mit
Rolle `approver` sieht also weiterhin auch die Anfragen, die laut Regel eigentlich
`superadmin` verlangen — er kann sie nur nicht mehr **entscheiden**.

## 4. Die Konsequenz — Sichtbarkeit bleibt grob, Entscheidung ist jetzt fein

„Wer genehmigt was" beantwortet der Code seit AP-22 zweistufig: **Wer die
Warteschlange sieht**, bestimmt weiterhin nur die grobe Rolle (`approver`, `admin`,
`superadmin`) — ein `approver_role="admin"` und ein `approver_role="approver"`
landen weiterhin in derselben Warteschlange und sind für denselben Personenkreis
sichtbar. **Wer eine Anfrage tatsächlich entscheiden darf**, prüft
`_load_pending` jetzt gegen genau den `approver_role`-Wert dieser Regel — eine zu
schwache Rolle bekommt beim Versuch `ForbiddenError` statt einer stillen
Ausführung. Das Feld dokumentierte bis AP-22 nur eine Absicht; seit AP-22 setzt es
sie bei der Entscheidung durch, nicht aber bei der Sichtbarkeit der Queue.

## 5. Mehrere Regeln je Template

Weder `models.py` noch `apps/approvals/migrations/0001_initial.py` enthalten
eine `unique_together`- oder `UniqueConstraint`-Angabe auf `template` — geprüft
per `grep -n "unique_together\|UniqueConstraint" apps/approvals/models.py
apps/approvals/migrations/0001_initial.py` (kein Treffer). Zwei aktive
`ApprovalRule`-Zeilen mit demselben `template` sind also ohne Weiteres möglich
und erzeugen bei `create_approval_requests` zwei parallele
`ApprovalRequest`-Zeilen für dieselbe Bestellung. Was das für den Ablauf
bedeutet, vertieft [Seite 3](03-ein-und-mehrstufige-genehmigung.md).

## 6. Zusammenfassung

`ApprovalRule` bestimmt „braucht Genehmigung" ausschließlich über `template_id`
und `is_active` — `condition` ist unbenutzt. `approver_role` wird seit AP-22 bei
jeder Entscheidung geprüft (`ApprovalService._load_pending`), aber weiterhin nicht
beim Zugriff auf die Warteschlange selbst: Wer `/approvals/` sehen darf, hängt nach
wie vor allein an der Nutzerrolle (`approver`/`admin`/`superadmin`), nicht am
Inhalt der Regel. Mehrere aktive Regeln je Template sind vom Datenmodell her
zulässig und im laufenden Betrieb möglich.

> Quelle: cmp/apps/approvals/models.py, cmp/apps/approvals/migrations/0001_initial.py, cmp/apps/approvals/migrations/0002_alter_approvalrule_approver_role.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/approvals/admin.py, cmp/core/mixins.py, cmp/core/domain/enums.py, cmp/core/exceptions.py, cmp/apps/accounts/services.py — am Code geprüft 2026-07-22
