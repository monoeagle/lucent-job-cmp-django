# 03 — Rollen & Rechte

> **In diesem Kapitel:** Nicht jede Person, die sich am CMP anmeldet, darf
> dasselbe tun. Wer nur bestellen soll, soll nicht gleich den Django-Admin
> bedienen können. Dieses Kapitel zeigt dir, welche Rollen es gibt, wie sie
> zueinander stehen und wo im Code das geprüft wird.
>
> **Das lernst du:**
> - Welche vier Rollen es im CMP gibt und was sie im Alltag bedeuten
> - Dass die Rollen **hierarchisch** sind — eine höhere Rolle schließt die
>   niedrigeren Rechte ein
> - Wie neue Nutzer überhaupt ins System kommen (Stichwort: kein Self-Service)
> - Wo genau im Code eine Rollenprüfung stattfindet
>
> **Voraussetzung:** [03 — Die Fachdomäne](03-fachdomaene.md) (die Begriffe
> Bestellung, Genehmigung, Genehmigungsregel solltest du kennen).

---

## Warum überhaupt Rollen?

Stell dir vor, jede und jeder könnte im CMP alles: bestellen, genehmigen,
Nutzer anlegen, Genehmigungsregeln ändern. Das wäre praktisch — und ein
Sicherheitsalbtraum. Deshalb hat jede Person im CMP genau **eine** Rolle, die
festlegt, was sie darf.

💡 **Merke:** Die Rolle einer Person steckt in genau einem Feld: `User.role`.
Kein Geflecht aus Gruppen und Permissions — ein Wort sagt dir, was jemand darf.

---

## Die vier Rollen auf einen Blick

Im CMP gibt es vier Rollen, definiert als `UserRole` (ein `TextChoices`-Enum)
in [`cmp/core/domain/enums.py`](../../cmp/core/domain/enums.py):

| Rolle | Klartext | Typische Rechte/Aufgaben |
|-------|----------|---------------------------|
| `requester` | Bestellt aus dem Katalog | Katalog durchsuchen, Bestellungen anlegen und abschicken, eigene Bestellungen und Abos einsehen |
| `approver` | Genehmigt oder lehnt ab | Alles, was `requester` darf — zusätzlich: offene Genehmigungsanfragen einsehen, gemäß `ApprovalRule.approver_role` zustimmen oder ablehnen |
| `admin` | Verwaltet das Portal | Alles, was `approver` darf — zusätzlich: Katalog, Genehmigungsregeln und Nutzer über den Django-Admin verwalten |
| `superadmin` | Höchste Stufe | Alles, was `admin` darf — zusätzlich: uneingeschränkter Zugriff auf alle Verwaltungsfunktionen |

Diese Tabelle liest sich bewusst **kumulativ** — das ist der zentrale Punkt
des ganzen Kapitels.

---

## Die Rollen sind eine Hierarchie, keine Kategorien

Die vier Rollen stehen nicht gleichberechtigt nebeneinander wie Farben oder
Tags. Sie bilden eine **Rangfolge**:

```
requester  <  approver  <  admin  <  superadmin
```

Wer als `admin` eingetragen ist, kann alles, was ein `approver` kann — und
alles, was ein `requester` kann. Die Hierarchie steht als einfache Liste
(`ROLE_HIERARCHY`) in
[`cmp/apps/accounts/services.py`](../../cmp/apps/accounts/services.py),
und die Prüfung übernimmt eine einzige Methode:

```python
AccountService.is_at_least_role(user_role, minimum_role)
```

Sie schaut nach, an welcher Position beide Rollen in der Liste stehen, und
vergleicht die Positionen. Steht `user_role` an derselben Stelle oder weiter
rechts als `minimum_role`, ist die Bedingung erfüllt.

💡 **Merke:** Willst du im Code prüfen „darf diese Person mindestens X?",
schreibst du nie einen eigenen Rollenvergleich. Du rufst
`AccountService.is_at_least_role(user.role, "X")` auf. Das ist die **eine**
Stelle, die weiß, wie die Hierarchie sortiert ist.

⚠️ **Achtung:** Eine Rollenprüfung fragt fast immer „mindestens Rolle X",
nicht „genau Rolle X". Ein `superadmin` soll schließlich auch das dürfen, was
ein `approver` darf.

---

## Wie kommen Nutzer überhaupt ins System?

Anders als viele Webportale hat das CMP **keinen** Self-Service-Signup. In den
Settings steht:

```python
ACCOUNT_SIGNUP_ENABLED = False
```

Das heißt: Niemand kann sich selbst registrieren. Stattdessen legt eine
Person mit Admin-Rechten jeden Account über den **Django-Admin** an — inklusive
der passenden Rolle. Angemeldet wird sich klassisch per Username und Passwort,
über [django-allauth](https://docs.allauth.org/), session-basiert (kein Token,
kein API-Login).

🔍 **Im Code nachsehen:** Das Custom-User-Model liegt in
`cmp/apps/accounts/models.py` und erweitert `AbstractUser` um genau das eine
zusätzliche Feld `role`. In den Settings ist es über
`AUTH_USER_MODEL = "accounts.User"` als das aktive User-Model eingetragen.

> 🚧 **Ausblick — geplant, noch nicht gebaut:** Heute sind alle Nutzer
> **portal-intern** — ein Admin legt sie von Hand an, und die Rolle steht direkt
> am `User`. Eine Anbindung an ein **Active Directory (AD)** gibt es (Stand
> v1.5.0) noch nicht: kein `django-auth-ldap`, kein Gruppen-Mapping.
>
> Die Zielrichtung ist, Nutzer künftig aus dem AD zu übernehmen und ihre
> **AD-Gruppen auf CMP-Rollen abzubilden** — wer in einer bestimmten Gruppe ist,
> bekommt die zugehörige Rolle und deren Rechte (wer z. B. in der Gruppe
> „Modifier" ist, bekommt Modifier-Rechte; die anderen Gruppen analog).
>
> Das heutige 4-Rollen-Modell ist dafür das **Fundament**, kein Hindernis: Eine
> zusätzliche Rolle — etwa ein **Modifier**, der bestehende Subscriptions ändern
> oder kündigen darf — ließe sich später ergänzen, indem man `UserRole` erweitert,
> ihre Rechte definiert und die AD-Gruppe darauf mappt. Die Prüf-Logik
> (`is_at_least_role`, die Mixins) bliebe davon unberührt.

---

## Rollenprüfung auf View-Ebene: die Mixins

Kurz vorweg — **was ist überhaupt ein Mixin?** Ein Mixin ist eine kleine Klasse,
die eine *einzelne* Fähigkeit beisteuert und dafür gedacht ist, per
Mehrfachvererbung in andere Klassen „hineingemischt" zu werden (engl. *to mix
in*). Ein Mixin läuft nicht allein — es ist ein **Aufsatz**, den du an eine
„richtige" Basisklasse dranklemmst. In Django hängst du damit eine Zusatzprüfung
vor eine View:

```python
class OrderListView(RequesterRequiredMixin, ListView):
    ...
```

`ListView` liefert die eigentliche Listen-Logik; `RequesterRequiredMixin` klemmt
die Rollenprüfung davor (die Reihenfolge zählt: Mixins stehen *vor* der
Basisklasse). Der Vorteil: Die Prüfung steht **einmal** im Mixin und wird von
jeder View wiederverwendet, statt in jeder View neu geschrieben zu werden. Django
selbst nutzt dasselbe Prinzip, z. B. mit `LoginRequiredMixin`.

Bevor überhaupt ein Service aufgerufen wird, blockt meist schon die View die
falsche Rolle ab. Dafür gibt es in [`cmp/core/mixins.py`](../../cmp/core/mixins.py)
vier Mixins, die jeweils eine Mindestrolle verlangen:

| Mixin | Erlaubte Rollen |
|-------|------------------|
| `RequesterRequiredMixin` | `requester`, `approver`, `admin`, `superadmin` (also: jede angemeldete Person) |
| `ApproverRequiredMixin` | `approver`, `admin`, `superadmin` |
| `AdminRequiredMixin` | `admin`, `superadmin` |
| `SuperadminRequiredMixin` | nur `superadmin` |

Passt die Rolle nicht, gibt es **keinen** stillen Redirect zur Startseite —
das Mixin wirft direkt `PermissionDenied`, was Django in eine HTTP-**403**-
Antwort umwandelt:

```python
if self.required_roles and request.user.role not in self.required_roles:
    raise PermissionDenied
```

💡 **Merke:** Ein 403 bedeutet im CMP immer „angemeldet, aber die Rolle reicht
nicht". Ein nicht angemeldeter Zugriff führt dagegen zum Login (via
`LoginRequiredMixin`-Verhalten), nicht zum 403.

---

## Rollen im Alltag: ein Beispiel

Ben hat die Rolle `approver`. Er kann:

- den Katalog durchsuchen und selbst etwas bestellen (das darf jede Rolle ab `requester`)
- offene Genehmigungsanfragen einsehen und entscheiden — sofern die jeweilige
  `ApprovalRule` genau `approver` (oder niedriger) verlangt

Verlangt eine Regel aber `admin`, kann Ben sie **nicht** entscheiden — dafür
reicht seine Rolle nicht aus, egal wie dringend die Bestellung ist. Erst eine
Person mit Rolle `admin` oder `superadmin` darf hier zustimmen oder ablehnen.

⚠️ **Achtung:** Die Genehmigungsregeln selbst (`ApprovalRule`) darf **nicht**
schon `admin` bearbeiten — dafür ist im Admin-Bereich `AdminRulesView`
zuständig, und die verlangt per `SuperadminRequiredMixin` die Rolle
`superadmin`. Ein `admin` sieht in `AdminDashboardView` und `AdminConfigView`
Statistiken und Konfiguration, darf die Regeln aber nur lesen, nicht ändern
(`cmp/apps/dashboard/admin_views.py`).

---

## Mehrstufige Genehmigung heißt „parallel", nicht „nacheinander"

Eine Bestellung kann **mehrere** `ApprovalRule`s gleichzeitig treffen, wenn
mehrere aktive Regeln auf dasselbe Template zutreffen. `ApprovalService.
create_approval_requests()` legt dann für **jede** passende Regel eine eigene
`ApprovalRequest` an — alle auf einmal, alle mit Status `pending`.

💡 **Merke:** Das ist **keine** Reihenfolge wie „erst Team-Lead, dann
Abteilungsleitung". Es gibt kein Vier-Augen-Stufenfeld, keine Sequenz. Alle
offenen Anfragen laufen **parallel**:

- Erst wenn **alle** Anfragen zu einer Order entschieden und keine mehr
  `pending` ist *und* keine `rejected`, springt die Order auf `approved`
  (siehe `ApprovalService.approve()`).
- Eine **einzige** Ablehnung genügt dagegen sofort — `reject()` schickt die
  Order direkt auf `rejected`, ohne auf die übrigen Anfragen zu warten.

Mehr zum Zustandswechsel selbst in [Kapitel 05](05-bestell-lebenszyklus.md).

---

## Vertiefung für Entwickler

<details>
<summary><b>Rollenprüfung bei Genehmigungen</b></summary>

Wer eine Genehmigungsanfrage entscheidet, wird nicht nur auf View-Ebene
geprüft (z. B. über einen Mixin, der die Seite nur für bestimmte Rollen
anzeigt). Zusätzlich prüft der **Service** die Rolle noch einmal selbst —
klassisches *Defense in Depth*: Selbst wenn irgendeine View-Prüfung
durchrutscht, hält der Service dagegen.

Diese zweite Prüfung sitzt im Helper `_load_pending()` in
[`cmp/apps/approvals/services.py`](../../cmp/apps/approvals/services.py), den
sowohl `ApprovalService.approve()` als auch `ApprovalService.reject()` zuerst
aufrufen:

```python
verlangt = req.rule.approver_role
if not AccountService.is_at_least_role(approver.role, verlangt):
    raise ForbiddenError(
        f"Diese Entscheidung verlangt die Rolle '{verlangt}'."
    )
```

`req.rule.approver_role` ist die Rolle, die die jeweilige `ApprovalRule`
verlangt. Reicht die Rolle der entscheidenden Person nicht aus, wirft
`_load_pending()` einen `ForbiddenError` — die Entscheidung wird gar nicht
erst ausgeführt.

**Ein lehrreicher Edge-Case:** Was, wenn eine Regel eine Rolle nennt, die es
gar nicht gibt — etwa weil sich beim Anlegen der Regel ein Tippfehler
eingeschlichen hat? `is_at_least_role()` liefert für unbekannte Rollen still
`False` zurück (das `except ValueError: return False` in
`AccountService.is_at_least_role()`) — und das gilt auch für `superadmin`, die
höchste Rolle im System. Ohne Gegenmaßnahme würde eine solche Anfrage **für
niemanden** entscheidbar sein und ewig auf `pending` hängen bleiben.

Deshalb prüft `_load_pending()` das explizit **vorher** und wirft in diesem
Fall bewusst einen `ConflictError` statt eines `ForbiddenError`:

```python
if verlangt not in UserRole.values:
    # Sonst haengt die Anfrage fuer immer: is_at_least_role liefert fuer
    # unbekannte Werte stumm False, auch fuer den Superadmin.
    raise ConflictError(
        f"Regel {req.rule_id} nennt die unbekannte Rolle '{verlangt}' — "
        "die Anfrage ist so von niemandem entscheidbar."
    )
```

Das ist keine Bug-Behebung, sondern eine bewusste, im Code dokumentierte
Design-Entscheidung: lieber sofort ein klarer Fehler mit Ursache, als eine
Anfrage, die stillschweigend nie wieder auftaucht.

</details>

<details>
<summary><b>Das <code>_for_user</code>-Muster: zwei Ebenen der Sichtbarkeit</b></summary>

Mehrere Services im CMP bieten **zwei** Varianten derselben Methode an — eine
schlanke ohne Prüfung und eine mit Sichtbarkeits-Check:

| Service | Ohne Prüfung (service-intern) | Mit Prüfung (für Views) |
|---------|-------------------------------|--------------------------|
| `OrderService` | `get_order(order_id)` | `get_order_for_user(order_id, user)` |
| `SubscriptionService` | `get_subscription(sub_id)` | `get_subscription_for_user(sub_id, user)` |
| `SubscriptionService` | `cancel(sub_id)` | `cancel_for_user(sub_id, user)` |
| `NotificationService` | `mark_read(notification_id)` | `mark_read_for_user(notification_id, user)` |

Die schlanke Variante holt einfach den Datensatz (oder wirft `NotFoundError`,
wenn die ID nicht existiert) — sie kennt keinen Nutzer und prüft nichts.
Andere Services rufen sie zum Beispiel innerhalb einer Transition auf, wo der
Zugriff längst geklärt ist.

Die `_for_user`-Variante prüft zusätzlich, **wer** fragt:

```python
@staticmethod
def get_order_for_user(order_id, user):
    order = OrderService.get_order(order_id)
    if order.user_id == user.pk:
        return order
    if AccountService.is_at_least_role(user.role, UserRole.APPROVER):
        return order
    raise NotFoundError(f"Order with id={order_id} not found.")
```

Besitzer sehen ihre eigene Order, `approver` und höher sehen alle —
jede:r andere bekommt einen `NotFoundError`, keinen `ForbiddenError`. Eine
fremde Order ist damit von einer nicht-existenten ununterscheidbar (kein
„403 verrät, dass es die Order gibt").

`cancel_for_user()` bricht dieses Muster bewusst an einer Stelle: Stornieren
ist eine **Besitzer-Aktion**. Eine höhere Rolle ersetzt hier die
Eigentümerschaft nicht — nur wer die Subscription selbst besitzt, darf sie
kündigen:

```python
@staticmethod
def cancel_for_user(sub_id, user):
    sub = SubscriptionService.get_subscription(sub_id)
    if sub.user_id != user.pk:
        raise NotFoundError(f"Subscription {sub_id} not found.")
    return SubscriptionService.cancel(sub_id)
```

💡 **Merke:** Views rufen **immer** die `_for_user`-Variante auf, nie die
schlanke Service-zu-Service-Methode direkt — sonst würde jede beliebige
Person jede fremde Order oder Subscription sehen können, solange sie die ID
errät.

</details>

<details>
<summary><b>Django-Admin prüft nur <code>is_staff</code> — nicht die Rolle</b></summary>

⚠️ **Achtung:** Der Django-Admin selbst kennt kein `RoleRequiredMixin` und
fragt nicht nach `User.role`. Er prüft ausschließlich das Standard-Django-Feld
`is_staff` (und für bestimmte Aktionen `is_superuser`).

Der Seed-Befehl setzt das automatisch passend zur Rolle
(`AccountService.seed_stub_users()` in `cmp/apps/accounts/services.py`):

```python
"is_staff": user_data["role"] in (UserRole.ADMIN, UserRole.SUPERADMIN),
"is_superuser": user_data["role"] == UserRole.SUPERADMIN,
```

Wird ein Account dagegen **manuell** im Django-Admin angelegt und bekommt dort
die Rolle `admin` zugewiesen, öffnet das allein den Django-Admin **nicht** —
`is_staff` ist ein eigenes, unabhängiges Feld und muss separat gesetzt werden.
Rolle und Admin-Zugriff sind zwei verschiedene Schalter, die zufällig beim
Seed immer gemeinsam gesetzt werden, aber nicht automatisch zusammenhängen.

</details>

---

## Demo-Zugänge zum Ausprobieren

Der Befehl `python manage.py seed_users` (bzw. der allgemeine `seed`-Befehl)
legt fünf Stub-Nutzer an, mit denen du lokal jede Rolle durchspielen
kannst. Das Passwort ist für alle identisch:

| Benutzername | Rolle | `is_staff` | `is_superuser` |
|---------------|-------|------------|-----------------|
| `test-requester` | `requester` | nein | nein |
| `test-approver` | `approver` | nein | nein |
| `test-multi` | `approver` | nein | nein |
| `test-admin` | `admin` | ja | nein |
| `test-superadmin` | `superadmin` | ja | ja |

**Passwort für alle:** `test123`

🔍 **Im Code nachsehen:** Die Liste `STUB_USERS` und `AccountService.
seed_stub_users()` in `cmp/apps/accounts/services.py`.

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Die vier Rollen (`UserRole`) | `cmp/core/domain/enums.py` |
| Die Hierarchie + `is_at_least_role()` | `cmp/apps/accounts/services.py` |
| Das Custom-User-Model (Feld `role`) | `cmp/apps/accounts/models.py` |
| Rollenprüfung bei Genehmigungen (`_load_pending()`) | `cmp/apps/approvals/services.py` |
| Die View-Mixins (`RequesterRequiredMixin` &amp; Co.) | `cmp/core/mixins.py` |
| Das `_for_user`-Muster | `cmp/apps/orders/services.py`, `cmp/apps/subscriptions/services.py`, `cmp/apps/notifications/services.py` |
| Regel-Verwaltung nur für `superadmin` (`AdminRulesView`) | `cmp/apps/dashboard/admin_views.py` |
| Demo-Zugänge (`STUB_USERS`, `seed_stub_users()`) | `cmp/apps/accounts/services.py` |
| `AUTH_USER_MODEL`, `ACCOUNT_SIGNUP_ENABLED` | `cmp/config/settings/base.py` |

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Warum kann ein `admin` alles tun, was ein `requester` tun kann — obwohl das
   nirgends einzeln aufgelistet ist?
2. Wie werden neue Nutzer im CMP angelegt?
3. Was passiert, wenn eine `ApprovalRule` eine Rolle verlangt, die es gar
   nicht gibt — und warum ist das so gelöst?
4. Ein Nutzer hat im Django-Admin die Rolle `admin` bekommen. Kann er sich
   jetzt im Django-Admin anmelden? Warum (nicht)?
5. Warum ruft `OrderDetailView` `get_order_for_user()` auf statt einfach
   `get_order()`?
6. Zwei `ApprovalRule`s greifen bei derselben Bestellung. Eine Person
   genehmigt, die andere lehnt ab. Was passiert mit der Order?

<details>
<summary>Antworten anzeigen</summary>

1. Weil die Rollen eine **Hierarchie** bilden (`requester < approver < admin <
   superadmin`). `is_at_least_role()` prüft nur, ob die Rolle einer Person
   *mindestens* so weit rechts in dieser Liste steht wie die verlangte Rolle —
   eine höhere Rolle erfüllt damit automatisch jede niedrigere Anforderung.
2. Es gibt keinen Self-Service-Signup (`ACCOUNT_SIGNUP_ENABLED=False`). Eine
   Person mit Admin-Rechten legt jeden Account über den Django-Admin an und
   vergibt dabei die passende Rolle.
3. `_load_pending()` prüft das explizit und wirft dann einen `ConflictError` —
   statt einen `ForbiddenError`, der die Anfrage einfach unentscheidbar
   liegen lassen würde. Grund: `is_at_least_role()` liefert für unbekannte
   Rollen still `False`, selbst für `superadmin`. Ohne diese Prüfung würde die
   Anfrage für immer auf `pending` hängen bleiben.
4. Nicht automatisch. Der Django-Admin prüft nur `is_staff`, nicht `User.role`.
   Bei manuell angelegten Accounts muss `is_staff` separat gesetzt werden —
   nur der Seed-Befehl setzt beides automatisch zusammen.
5. Weil `get_order()` gar nicht prüft, wem die Order gehört — jede beliebige
   ID würde zurückgegeben. `get_order_for_user()` lässt nur den Besitzer oder
   Rollen ab `approver` durch, alles andere gibt (bewusst als `NotFoundError`
   statt `ForbiddenError`) einen 404 zurück.
6. Die Ablehnung entscheidet sofort: Eine einzige Ablehnung reicht, damit die
   Order auf `rejected` springt — unabhängig davon, dass die andere Anfrage
   bereits genehmigt wurde. Es gibt keine „Mehrheit", jede Ablehnung ist
   final.

</details>

---

⟵ [03 — Die Fachdomäne](03-fachdomaene.md) · [📖 Übersicht](README.md) · [05 — Der Bestell-Lebenszyklus](05-bestell-lebenszyklus.md) ⟶
