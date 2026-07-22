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

Bis AP-22 filterte `OrderDetailView.get_object` nicht nach Benutzer — es rief direkt
`OrderService.get_order(pk)` auf, das jede Bestellung per ID lieferte, unabhängig vom
Ersteller. Seit AP-22 nutzt `OrderDetailView.get_object`
(`cmp/apps/orders/views.py:66-70`) stattdessen
`OrderService.get_order_for_user(order_id, user)`
(`cmp/apps/orders/services.py:27-39`):

```python
order = OrderService.get_order(order_id)
if order.user_id == user.pk:
    return order
if AccountService.is_at_least_role(user.role, UserRole.APPROVER):
    return order
raise NotFoundError(f"Order with id={order_id} not found.")
```

Besitzer sehen ihre eigene Bestellung, Rollen ab `approver` sehen jede — jeder
andere Fall wirft `NotFoundError`, die View übersetzt das in `Http404` (nicht in
`403`), damit eine fremde Bestellung nicht von einer nicht existierenden zu
unterscheiden ist. `get_order(pk)` selbst blieb dabei **unverändert** — es liefert
weiterhin jede Bestellung ohne Benutzerabgleich; die Prüfung sitzt ausschließlich in
der zusätzlichen `*_for_user`-Variante.

Genau das ist auch die Grenze der Korrektur: Die Schreib-Operationen einer
Bestellung — `OrderAddItemView`, `OrderRemoveItemView` und `OrderSubmitView`
(`cmp/apps/orders/views.py:377-440`) — rufen weiterhin `OrderService.add_item`,
`.remove_item` und `.submit_order` auf, die intern `get_order(order_id)` bzw. eine
direkte `pk`-Abfrage auf `OrderItem` nutzen, ohne den Benutzer zu vergleichen
(`cmp/apps/orders/services.py:47-93`). Praktisch heißt das: Ein fremdes Bestell-Detail
lässt sich nicht mehr aufrufen, aber wer die ID einer fremden Draft-Bestellung kennt
oder errät, kann ihr weiterhin Positionen hinzufügen/entfernen und sie einreichen —
dort schützt nach wie vor nur `RequesterRequiredMixin`, also die Rolle, nicht der
Besitz des Objekts. Diese drei Services haben keinen Request-Kontext (sie werden
auch service-zu-service ohne `user` aufgerufen) und wurden deshalb bei AP-22 bewusst
nicht angefasst.

## 3. Subscriptions

`SubscriptionListView.get_queryset` filtert korrekt über
`SubscriptionService.list_user_subscriptions(user_id)`, das intern
`Subscription.objects.filter(user_id=user_id)` verwendet
(`cmp/apps/subscriptions/views.py:14-23`; `cmp/apps/subscriptions/services.py:30-35`).

Bis AP-22 filterten `SubscriptionDetailView.get_object` und
`SubscriptionCancelView.post` nicht: beide gingen über
`SubscriptionService.get_subscription(sub_id)` bzw. `.cancel(sub_id)`, die per `pk`
ohne Benutzerabgleich zugreifen. Seit AP-22 nutzt `SubscriptionDetailView.get_object`
(`cmp/apps/subscriptions/views.py:32-38`)
`SubscriptionService.get_subscription_for_user(sub_id, user)`
(`cmp/apps/subscriptions/services.py:47-60`) — Besitzer oder Rollen ab `approver`,
sonst `NotFoundError` → `Http404`, dieselbe Logik wie bei Bestellungen.
`SubscriptionCancelView.post` (`views.py:44-50`) nutzt
`SubscriptionService.cancel_for_user(sub_id, user)` (`services.py:63-72`), das
bewusst **enger** ist als das Lesen: Kündigen bleibt reine Besitzerhandlung, eine
höhere Rolle genügt hier nicht —

```python
sub = SubscriptionService.get_subscription(sub_id)
if sub.user_id != user.pk:
    raise NotFoundError(f"Subscription {sub_id} not found.")
return SubscriptionService.cancel(sub_id)
```

— ein Approver kann ein fremdes Abo also einsehen, aber nicht kündigen. Wie bei
Bestellungen bleiben die zugrundeliegenden `get_subscription`/`cancel`-Methoden
selbst unverändert; die Prüfung sitzt ausschließlich in den `*_for_user`-Varianten,
die jetzt beide Views verwenden. Liste, Detail und Kündigen sind damit vollständig
gescoped.

## 4. Notifications

`NotificationListView.get_queryset` filtert korrekt auf
`Notification.objects.filter(user=self.request.user)`
(`cmp/apps/notifications/views.py:11-20`). `NotificationMarkAllReadView` filtert
ebenfalls korrekt über `NotificationService.mark_all_read(user_id)`
(`cmp/apps/notifications/views.py:37-41`; `cmp/apps/notifications/services.py:31-34`).

Bis AP-22 filterte `NotificationMarkReadView.post` **nicht**:
`NotificationService.mark_read` aktualisierte per `pk`, ohne den Benutzer zu prüfen
— jeder angemeldete Benutzer konnte eine fremde Benachrichtigung per ID als gelesen
markieren. Seit AP-22 ruft `NotificationMarkReadView.post`
(`cmp/apps/notifications/views.py:32-34`)
`NotificationService.mark_read_for_user(notification_id, user)`
(`cmp/apps/notifications/services.py:24-28`) auf:

```python
Notification.objects.filter(pk=notification_id, user=user).update(is_read=True)
```

Der Filter auf `user=user` sorgt dafür, dass das Update auf eine fremde
Benachrichtigung schlicht keine Zeile trifft — kein Fehler, kein 404, die
Benachrichtigung bleibt einfach ungelesen. Die alte, ungefilterte
`NotificationService.mark_read` (`services.py:19-21`) existiert unverändert weiter,
wird aber von keiner View mehr aufgerufen.

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
| Order | ja, außer Tab „all" ab approver | Detail: ja (seit AP-22); Add-Item/Remove-Item/Submit: nein | `orders/views.py:39-50,66-70,377-440`; `orders/services.py:17-93` |
| Subscription | ja | ja (seit AP-22, Detail und Cancel) | `subscriptions/views.py:14-50`; `subscriptions/services.py:30-72` |
| Notification | ja | ja (seit AP-22, auch Einzel-Mark-Read) | `notifications/views.py:11-41`; `notifications/services.py:16-34` |
| ApprovalRequest (Queue) | nein (Konstruktion) | — | `approvals/views.py:12-23` |
| AuditLog | nein (Konstruktion) | — | `audit/views.py:10-23` |
| ServiceTemplate | nein (geteilte Stammdaten) | — | `catalog/views.py:13-45` |
| Dashboard-Kennzahlen | ja, nach Rolle | — | `dashboard/views.py:18-34`; `dashboard/services.py:65-97` |

Listen filtern in CMP durchgängig nach dem anfragenden Benutzer, sobald das fachlich
Sinn ergibt (Order, Subscription, Notification, Dashboard). Bis AP-22 fehlte dieser
Abgleich zusätzlich bei Order (Detail), Subscription (Detail, Cancel) und beim
Einzel-Mark-Read der Notifications — dort schützte bis dahin ausschließlich die
Rollen-Mixin-Prüfung aus Kapitel 4.3, nicht die Objekt-Zugehörigkeit. Seit AP-22 sind
Subscription und Notification vollständig gescoped; bei Order bleibt eine Lücke:
Das Lesen (`OrderDetailView`) ist gescoped, die drei Schreib-Operationen Add-Item,
Remove-Item und Submit sind es nicht — sie hängen an `OrderService.add_item`,
`.remove_item` und `.submit_order`, die weiterhin ohne Benutzerabgleich per `pk`
zugreifen, weil sie auch service-zu-service ohne Request-Kontext aufgerufen werden.

> Quelle: cmp/apps/orders/views.py, cmp/apps/orders/services.py, cmp/apps/subscriptions/views.py, cmp/apps/subscriptions/services.py, cmp/apps/notifications/views.py, cmp/apps/notifications/services.py, cmp/apps/approvals/views.py, cmp/apps/audit/views.py, cmp/apps/catalog/views.py, cmp/apps/dashboard/views.py, cmp/apps/dashboard/services.py, cmp/apps/accounts/services.py, cmp/core/domain/enums.py — am Code geprüft 2026-07-22
