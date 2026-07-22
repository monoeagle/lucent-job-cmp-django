# Objektbezogene Sichtbarkeit

Rollen entscheiden, welche View ein Benutzer erreicht (Kapitel 4.3). Diese Seite
prüft die zweite Ebene: filtert die View innerhalb dieser Rolle nach dem
anfragenden Benutzer, oder sieht/bearbeitet jeder Rolleninhaber jedes Objekt? Jede
Aussage stützt sich auf den tatsächlichen `get_queryset()`- bzw. `get_object()`-Code.

## 1. Ziel des Kapitels

Wer eine neue Liste oder Detailansicht baut, soll hier sehen, welches Filterpuster
für vergleichbare Objekte bereits verwendet wird — und wo aktuell keines existiert.

## 2. Bestellungen (Order)

`OrderListView.get_queryset` filtert im Standardfall auf den anfragenden Benutzer;
nur bei Tab `all` und Rolle ≥ `approver` wird ungefiltert geliefert
(`cmp/apps/orders/views.py:39-50`, `_can_see_all` in `30-37`):

```python
if tab == "all" and self._can_see_all():
    qs = Order.objects.select_related("user").all()
else:
    qs = Order.objects.filter(user=self.request.user).select_related("user")
```

`OrderDetailView.get_object` filtert dagegen **nicht** nach Benutzer — es ruft direkt
`OrderService.get_order(pk)` auf, das jede Bestellung per ID liefert, unabhängig vom
Ersteller (`cmp/apps/orders/views.py:66-70`; `cmp/apps/orders/services.py:17-22`).
Dieselbe ungefilterte Grundlage nutzen auch die Schreib-Operationen einer
Bestellung — `OrderAddItemView`, `OrderRemoveItemView` und `OrderSubmitView`
(`cmp/apps/orders/views.py:375-440`) rufen `OrderService.add_item`, `.remove_item`
und `.submit_order` auf, die alle über `get_order(order_id)` bzw. eine direkte
`pk`-Abfrage gehen, ohne den Benutzer zu vergleichen
(`cmp/apps/orders/services.py:30-76`). Praktisch heißt das: Jeder angemeldete
Benutzer (ab `requester`) kann eine fremde Bestellung per bekannter oder erratener
ID ansehen, ihr Positionen hinzufügen/entfernen und sie einreichen — die einzige
Schranke ist `RequesterRequiredMixin`, also die Rolle, nicht der Besitz des Objekts.

## 3. Subscriptions

`SubscriptionListView.get_queryset` filtert korrekt über
`SubscriptionService.list_user_subscriptions(user_id)`, das intern
`Subscription.objects.filter(user_id=user_id)` verwendet
(`cmp/apps/subscriptions/views.py:14-23`; `cmp/apps/subscriptions/services.py:30-35`).

`SubscriptionDetailView.get_object` und `SubscriptionCancelView.post` filtern nicht:
beide gehen über `SubscriptionService.get_subscription(sub_id)` bzw. `.cancel(sub_id)`,
die per `pk` ohne Benutzerabgleich zugreifen (`cmp/apps/subscriptions/views.py:26-47`;
`cmp/apps/subscriptions/services.py:38-55`). Wie bei Bestellungen: Liste ist
gescoped, Detail und Aktion (hier: Kündigen) sind es nicht.

## 4. Notifications

`NotificationListView.get_queryset` filtert korrekt auf
`Notification.objects.filter(user=self.request.user)`
(`cmp/apps/notifications/views.py:11-20`). `NotificationMarkAllReadView` filtert
ebenfalls korrekt über `NotificationService.mark_all_read(user_id)`
(`cmp/apps/notifications/views.py:37-41`; `cmp/apps/notifications/services.py:24-27`).

`NotificationMarkReadView.post` filtert **nicht**: `NotificationService.mark_read`
aktualisiert per `pk`, ohne den Benutzer zu prüfen
(`cmp/apps/notifications/views.py:31-34`; `cmp/apps/notifications/services.py:20-21`):

```python
Notification.objects.filter(pk=notification_id).update(is_read=True)
```

Jeder angemeldete Benutzer kann also eine fremde Benachrichtigung per ID als
gelesen markieren.

## 5. Bewusst ungescopte Übersichten

Nicht jede ungefilterte Ansicht ist eine Lücke — einige sind so gewollt:

- **Genehmigungs-Queue:** `ApprovalQueueView.get_queryset` liefert allen Nutzern mit
  Rolle ≥ `approver` dieselben offenen Anfragen, unabhängig davon, wer die
  Bestellung aufgegeben hat (`cmp/apps/approvals/views.py:12-23`). Genehmiger müssen
  systembedingt alles sehen, was auf Entscheidung wartet — das ist Konstruktion,
  keine fehlende Filterung.
- **Audit-Log:** `AuditLogListView.get_queryset` liefert allen Admin+/Superadmin
  dieselben, systemweiten Einträge (`cmp/apps/audit/views.py:10-23`). Ein Audit-Log,
  das nur die eigenen Aktionen zeigt, wäre für seinen Zweck (Revision) unbrauchbar.
- **Katalog:** `ServiceTemplate` hat kein Besitzer-Feld — der Katalog ist geteilte
  Stammdaten, für jede Rolle identisch sichtbar (`cmp/apps/catalog/views.py:13-45`).
- **Dashboard:** `DashboardView.get_context_data` wählt bewusst zwischen globalem
  und benutzerbezogenem Scope, je nach Rolle
  (`cmp/apps/dashboard/views.py:18-19,32-34`):

  ```python
  is_admin = AccountService.is_at_least_role(user.role, UserRole.ADMIN)
  scope_user = None if is_admin else user
  ```

  `DashboardService.get_orders_by_status`, `.get_orders_by_month` und
  `.get_recent_orders` nehmen diesen `scope_user` entgegen und filtern nur, wenn er
  gesetzt ist (`cmp/apps/dashboard/services.py:65-97`) — Admin/Superadmin sehen
  systemweite Zahlen, Requester/Approver nur ihre eigenen.

## 6. Zusammenfassung

| Objekt | Liste gescoped? | Detail/Aktion gescoped? | Fundstelle |
|---|---|---|---|
| Order | ja, außer Tab „all" ab approver | nein | `orders/views.py:39-50,66-70,375-440`; `orders/services.py:17-76` |
| Subscription | ja | nein | `subscriptions/views.py:14-47`; `subscriptions/services.py:30-55` |
| Notification | ja | teilweise (mark-all ja, mark-single nein) | `notifications/views.py:11-41`; `notifications/services.py:20-27` |
| ApprovalRequest (Queue) | nein (Konstruktion) | — | `approvals/views.py:12-23` |
| AuditLog | nein (Konstruktion) | — | `audit/views.py:10-23` |
| ServiceTemplate | nein (geteilte Stammdaten) | — | `catalog/views.py:13-45` |
| Dashboard-Kennzahlen | ja, nach Rolle | — | `dashboard/views.py:18-34`; `dashboard/services.py:65-97` |

Listen filtern in CMP durchgängig nach dem anfragenden Benutzer, sobald das fachlich
Sinn ergibt (Order, Subscription, Notification, Dashboard). Bei den zugehörigen
Detail- und Schreib-Operationen fehlt dieser Abgleich bei Order (Detail, Add-Item,
Remove-Item, Submit), Subscription (Detail, Cancel) und beim Einzel-Mark-Read der
Notifications — dort schützt ausschließlich die Rollen-Mixin-Prüfung aus
Kapitel 4.3, nicht die Objekt-Zugehörigkeit.

> Quelle: cmp/apps/orders/views.py, cmp/apps/orders/services.py, cmp/apps/subscriptions/views.py, cmp/apps/subscriptions/services.py, cmp/apps/notifications/views.py, cmp/apps/notifications/services.py, cmp/apps/approvals/views.py, cmp/apps/audit/views.py, cmp/apps/catalog/views.py, cmp/apps/dashboard/views.py, cmp/apps/dashboard/services.py, cmp/apps/accounts/services.py — am Code geprüft 2026-07-22
