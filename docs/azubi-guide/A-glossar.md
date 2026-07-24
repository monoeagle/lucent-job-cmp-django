# A — Glossar

> **In diesem Anhang:** Alle wichtigen Begriffe aus dem Guide alphabetisch
> sortiert und in einem Satz erklärt — zum schnellen Nachschlagen, wenn du
> mitten in einem Kapitel über einen Begriff stolperst.

| Begriff | Kurz erklärt |
|---------|--------------|
| **Abo / Subscription** | Das Ergebnis einer erfolgreich durchgelaufenen Bestellung — ein aktiver Zugriff, den ein Requester nutzt (Model `Subscription`). |
| **ADR** | *Architecture Decision Record* — ein Dokument, das eine Architekturentscheidung samt Begründung festhält, z. B. ADR-0001 „nativ statt Container" in `cmp-docs/`. |
| **allauth (django-allauth)** | Das Auth-Package, das Login/Logout im CMP übernimmt — Session-basiert, ohne eigene Signup-Seite. |
| **Approval / Approver** | Genehmigung bzw. die Person mit Rolle `approver` (oder höher), die eine Bestellung zustimmt oder ablehnt, siehe [Kapitel 04](04-rollen-und-rechte.md). |
| **ApprovalRule / ApprovalRequest** | `ApprovalRule` legt fest, wann und von wem eine Bestellung genehmigt werden muss; `ApprovalRequest` ist die konkrete, offene Anfrage dazu (Models in `cmp/apps/approvals/models.py`). |
| **Audit-Log** | Protokoll aller wichtigen Aktionen im System (z. B. `order.approved`), geschrieben von `AuditService.log()` — siehe [Kapitel 05](05-bestell-lebenszyklus.md). |
| **AvailabilityRule** | Legt pro `ServiceTemplate` fest, ob es an einem bestimmten Standort und/oder Mandanten bestellbar ist (App `cmdb`), siehe [Kapitel 03](03-fachdomaene.md). |
| **Celery** | Task-Queue für asynchrone Arbeit (z. B. Provisioning im Hintergrund), läuft in Dev/Test im **EAGER**-Modus synchron mit. |
| **Channels (GEPLANT, nicht implementiert — AP-12)** | Django Channels für WebSocket-Updates ist im Architektur-Vokabular erwähnt und für später vorgesehen (Arbeitspaket AP-12) — aktuell existieren keine `consumers.py`, siehe [Kapitel 07](07-async-und-provisioning.md). |
| **CmdbStubClient** | Stub-Client, der Kontextdaten (Standorte, Netze, Mandanten) statt aus einem echten CMDB-System aus YAML-Dateien in `cmp/stubs/cmdb/` liest — `cmp/apps/cmdb/clients.py`. |
| **CMP** | Kurzform für **CloudMan Portal**, den Projektnamen des hier dokumentierten Self-Service-Portals. |
| **ContextRestriction** | Schränkt pro `ServiceTemplate` einzelne Bestellparameter auf bestimmte, vom Kontext abhängige Werte ein (App `cmdb`), siehe [Kapitel 03](03-fachdomaene.md). |
| **ContextService** | Service in der App `cmdb`, der Verfügbarkeit und Parameter-Einschränkungen für Kontexte auswertet (`is_template_available()`, `get_available_templates()`, `get_parameter_restrictions()`, `get_user_tenants()`), siehe [Kapitel 03](03-fachdomaene.md). |
| **DaisyUI** | Komponenten-Bibliothek auf Basis von Tailwind CSS, liefert fertige UI-Bausteine (Buttons, Cards, …) fürs Frontend. |
| **DispatchLog** | Protokolliert pro `OrderItem` den Versuch, es bereitzustellen — Model in `cmp/apps/provisioning/models.py`. |
| **django-environ** | Package, über das Produktionssettings ihre Werte (z. B. `SECRET_KEY`, `DATABASE_URL`) aus Umgebungsvariablen statt aus Code lesen. |
| **DEBUG (Prod: fatal)** | Django-Setting für Debug-Ausgaben. `DEBUG=True` in Produktion ist ein fataler Fehler und darf nie deployt werden. |
| **EAGER (CELERY_TASK_ALWAYS_EAGER)** | Setting, das Celery-Tasks synchron im selben Prozess statt über einen echten Worker ausführt — in Dev und Test aktiv, in Produktion aus. |
| **Gunicorn** | WSGI-Server, der Django in Produktion tatsächlich ausführt (siehe [Kapitel 12](12-wie-es-in-produktion-laeuft.md)). |
| **HTMX** | JavaScript-Bibliothek für partielle Seiten-Updates ohne Full-Page-Reload — Basis des CMP-Frontends. |
| **Katalog / ServiceTemplate** | Die Liste bestellbarer Dienste; jeder Eintrag ist ein `ServiceTemplate` mit Parametern und Schema. |
| **Kontext** | Die Kombination aus Standort, Mandant und Sicherheitszone, gegen die eine Bestellung geprüft wird (z. B. über `AvailabilityRule` und `ContextRestriction`), siehe [Kapitel 03](03-fachdomaene.md). |
| **Lucent-Theme** | Das projekteigene DaisyUI-Theme mit dem Namen „Lucent", das die visuelle Gestaltung des Portals bestimmt. |
| **Order / OrderItem** | Eine Bestellung (`Order`) und ihre einzelnen Positionen (`OrderItem`), Models in `cmp/apps/orders/models.py` — siehe [Kapitel 05](05-bestell-lebenszyklus.md). |
| **PostgreSQL** | Die einzige unterstützte Datenbank für Dev, Test und Produktion. |
| **Provisioning** | Der eigentliche Bereitstellungsschritt einer Bestellung (aktuell simuliert), siehe [Kapitel 07](07-async-und-provisioning.md). |
| **GitLab-Stub (GitLabStubClient)** | Simuliert eine GitLab-Pipeline, statt wirklich eine auszulösen — der aktuelle „Provisioning-Backend", `cmp/apps/provisioning/clients.py`. |
| **Redis** | Message-Broker für Celery in Produktion; in Dev/Test wegen EAGER-Modus nicht zwingend nötig. |
| **Requester** | Die niedrigste Rolle (`requester < approver < admin < superadmin`) — kann den Katalog durchsuchen und selbst bestellen, siehe [Kapitel 04](04-rollen-und-rechte.md). |
| **Rolle (requester\<approver\<admin\<superadmin)** | Die vier hierarchischen Rollen im CMP; eine höhere Rolle schließt die Rechte der niedrigeren mit ein. |
| **„Service = Daten, kein Code"** | Ein bestellbarer Service ist kein eigenes Stück Code, sondern schlicht ein `ServiceTemplate`-Datensatz mit Parametern und Schema. |
| **Service-Layer (services.py)** | Die Schicht, in der die eigentliche Fachlogik lebt — Views bleiben dünn (Thin View) und rufen nur Services auf. |
| **StatusMachine / OrderStatus** | `StatusMachine.validate_transition()` prüft erlaubte Zustandswechsel gegen die `TRANSITIONS`-Tabelle in `cmp/core/domain/value_objects.py`, siehe [Kapitel 05](05-bestell-lebenszyklus.md). |
| **TERMINAL_STATES** | Die drei Endzustände einer Bestellung — `done`, `failed`, `rejected` — aus denen kein weiterer Übergang führt. |
| **Thin View** | Architekturprinzip: Views enthalten möglichst wenig Logik, die eigentliche Arbeit passiert im Service-Layer. |
| **transition() / transitions.py** | Die eine zentrale Funktion, über die `order.status` verändert werden darf — prüft, setzt und protokolliert in einem Schritt, `cmp/apps/orders/transitions.py`, siehe [Kapitel 05](05-bestell-lebenszyklus.md). |
| **UserTenantAssignment** | Ordnet einen User einem Mandanten zu, damit `ContextService.get_user_tenants()` seine erlaubten Mandanten ermitteln kann (App `cmdb`), siehe [Kapitel 03](03-fachdomaene.md). |
| **Wheelhouse** | Ein lokales Verzeichnis mit vorab heruntergeladenen `.whl`-Paketen, aus dem `pip` bei der Installation auf einer air-gapped (offline) VM ohne PyPI-Zugriff installiert (`pip install --no-index --find-links=…`). |
| **Worker (Celery)** | Der Prozess, der Celery-Tasks in Produktion tatsächlich abarbeitet (in Dev/Test durch den EAGER-Modus ersetzt). |

---

⟵ [13 — Rundgang](13-rundgang.md) · [📖 Übersicht](README.md) · [B — Spickzettel](B-spickzettel.md) ⟶
