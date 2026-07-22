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
(`cmp/apps/approvals/services.py:14-22`, `:24-46`) ermitteln zunächst die
`template_id`-Werte aller `OrderItem`-Zeilen der Bestellung und filtern dann:

```python
ApprovalRule.objects.filter(template_id__in=template_ids, is_active=True)
```

Das ist die gesamte Zuordnungslogik. Es gibt keinen weiteren Filter — weder auf
Bestellwert, Menge noch Abteilung. Das Feld `condition`
(`apps/approvals/models.py:15`) existiert für genau solche Zusatzkriterien,
wird aber an keiner Stelle ausgewertet — das ist bereits in
[Kapitel 3.4 Abschnitt 5](../03-domaenenmodell-und-apps/04-genehmigung-approvalrequest.md)
belegt und gilt unverändert für diese Seite: „wer genehmigt was" hängt heute
ausschließlich am Template, nicht an Regeln, die von den Bestelldaten abhängen.

## 3. `approver_role` — eine Beschreibung, keine Durchsetzung

`approver_role` ist ein `CharField(max_length=20)` ohne `choices=`
(`apps/approvals/models.py:16`) — ein Freitext-Wert wie z. B. `"approver"`, den
niemand gegen eine feste Werteliste prüft. Entscheidend ist aber, was mit diesem
Wert *nach* der Regel-Erzeugung passiert: **nichts.**

`grep -rn "approver_role" cmp --include=*.py` (Stand 2026-07-22) findet den Wert
nur an vier Stellen: der Modell-Definition selbst, der Admin-Konfiguration
(`apps/approvals/admin.py:8-9`, nur `list_display`/`list_filter`), der Migration
und dem Seed-Kommando. Keine dieser Fundstellen liest `approver_role`, um zu
entscheiden, wer eine konkrete `ApprovalRequest`-Zeile bearbeiten darf.

Die tatsächliche Zugriffsprüfung läuft ausschließlich über die Nutzerrolle
(`core/domain/enums.py:5-9`, `UserRole`: `requester`, `approver`, `admin`,
`superadmin`) und `ApproverRequiredMixin`
(`core/mixins.py:70-76`, akzeptiert `APPROVER`, `ADMIN`, `SUPERADMIN`).
`ApprovalQueueView.get_queryset` (`apps/approvals/views.py:16-23`) filtert
ausschließlich nach `status` (Query-Parameter, Default `pending`) — nicht nach
`rule.approver_role` und nicht nach dem eingeloggten Nutzer.

## 4. Die Konsequenz — grob statt fein

„Wer genehmigt was" beantwortet der Code heute nur grob: **jeder Nutzer mit
Rolle `approver`, `admin` oder `superadmin` sieht und entscheidet jede offene
`ApprovalRequest`**, unabhängig davon, welchen `approver_role`-Wert die
zugehörige Regel trägt. Ein `approver_role="netzwerk"` und ein
`approver_role="security"` landen in derselben Warteschlange und sind für
denselben Personenkreis sichtbar. Das Feld dokumentiert eine Absicht, setzt sie
aber nicht durch.

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
und `is_active` — `condition` ist unbenutzt. `approver_role` beschreibt eine
Zuständigkeit in Textform, wird aber von keiner View oder keinem Service
geprüft: Zugriff auf die Genehmigungs-Warteschlange hängt allein an der
Nutzerrolle (`approver`/`admin`/`superadmin`), nicht am Inhalt der Regel. Mehrere
aktive Regeln je Template sind vom Datenmodell her zulässig und im laufenden
Betrieb möglich.

> Quelle: cmp/apps/approvals/models.py, cmp/apps/approvals/services.py, cmp/apps/approvals/views.py, cmp/apps/approvals/admin.py, cmp/apps/approvals/migrations/0001_initial.py, cmp/core/mixins.py, cmp/core/domain/enums.py — am Code geprüft 2026-07-22
