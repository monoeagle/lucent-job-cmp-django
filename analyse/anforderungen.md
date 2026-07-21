-   Installer idempotent machen, nicht nur den Installzweig sondern auch das abräumen für die Testumgebung
-   Das Logging muss granularer werden, also die Einzelschritte(z.B. die seeds) auch ausgeben und ins Log schreiben
-   Dev und Test Umgebung per Schalter konfigurierbar machen
-   Dokumentation ist aktuell noch auf DRF, die muss auf API First neu aufgebaut werden
-   Erst im *-docs Format und danach muss es sauber als MD für Bookstack aufbereitet werden

Zu Lernzwecken müssen folgende Dinge umgesetzt werden:

-   granulare Erklärungen sämtlicher sourcen
-   Szenarien:
    -   Wie wird ein neuer Service erstellt?
        -   Welche Kapslerung?
        -   Welche Ports und Verbindungen zwischen den einzelnen Komponenten sind aufzubauen?
    -   Open Tofu Export detailliert erklären!
    -   Schnittstelle zum Gitlab detailliert erklären!
-   Entwicklungsschritte erklären für die Weiterentwicklung
    -   Projekt im Repo
        -   Testumgebung zieht Repo
            -   Branch erstellen
            -   Features implementieren
            -   Features testen
            -   Branch einchecken/Mergen?
        -   QR Umgebung zieht neuen Stand
            -   Testen der Funktionälität?
        -   Produktivumgebung zieht neuen Stand
            -   Einspielen im Wartungszeitfenster?
            -   Wie umschalten von Betrieb nach „Under Construktion“? Einfach nur Dienste deaktivieren? Nginx liefert nur „Wartung“ aus?
            -   Einspielen
            -   Automatisierten Test
            -   Manuellen Test
            -   Wartung deaktivieren à Produktiv!
            -   Freigabe
-   Mermaid für diese ganzen Prozessualen Schritte
-   Wie bringen wir HA und Skalierungsthemen unter?

-   Nach der Installation muss ein Protokoll generiert werden mit sämtlichen wichtigen Informationen.
-   Für die ganzen generierenden Dinge die Tools benötigen diese mit im Repo bereitstellen inkl. Detaildoku für die Bedienung

-   Welche Dinge müssen wie abgesichert werden?


-   Welche Fallstricke gibt es bei HTMX?
-   Was kann über JS gelöst werden?
-   Wie muss beides abgesichert werden? à Detailliert dokumentieren!
-   Was ist der unterschied zwischen .env und uv?

zu den django bild

-   Was davon ist für CMP relevant?
-   Ggf. kleine Beispiele Snippets/Tutorials erstellen die wir im CMP benutzen könnten.

