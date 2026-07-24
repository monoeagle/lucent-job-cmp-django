# 00 — Willkommen

> **In diesem Kapitel:** Bevor es um Code, Diagramme oder Architektur geht,
> lernst du erstmal in einfachen Worten kennen, was das CloudMan Portal
> überhaupt ist — und wie dieser Guide dich Schritt für Schritt dorthin
> bringt, den Code wirklich zu verstehen.
>
> **Das lernst du:**
> - Was CMP macht — in einem Satz, ohne Fachchinesisch
> - Für wen dieser Guide gedacht ist und wie du ihn liest
> - Was du dafür mitbringen solltest (und was nicht)
> - Wie es im nächsten Kapitel weitergeht
>
> **Voraussetzung:** keine — das ist dein Startpunkt.

---

## Herzlich willkommen

Schön, dass du da bist! Du stehst gerade am Anfang deiner Einarbeitung ins
**CloudMan Portal**, kurz **CMP**. Dieser Guide ist genau dafür gemacht: dich
als Einsteiger von null auf ein Verständnis zu bringen, mit
dem du dich im Projekt zurechtfindest — und irgendwann selbstbewusst deinen
ersten eigenen Code-Beitrag leistest.

Kein Vorwissen über CMP nötig. Wir fangen bei den Grundbegriffen an und bauen
von dort aus alles auf.

---

## Was ist CMP eigentlich?

In einem Satz: **CMP ist ein Self-Service-Portal, über das Mitarbeitende sich
selbst IT-Ressourcen bestellen können** — zum Beispiel eine virtuelle Maschine
oder einen anderen IT-Service aus einem Katalog.

Stell es dir vor wie einen internen Online-Shop, nur dass die „Produkte" keine
Pakete sind, sondern IT-Leistungen:

1. Ein Nutzer sucht sich im **Katalog** aus, was er braucht (z. B. „Linux-VM,
   4 GB RAM").
2. Er **bestellt** — je nach Regel muss das erst noch **genehmigt** werden.
3. Ist alles freigegeben, wird die Ressource automatisch **bereitgestellt**
   (Provisioning) — ganz ohne dass jemand von Hand einen Server anlegt.
4. Am Ende hat der Nutzer ein aktives **Abo** für seine Ressource.

💡 **Merke:** CMP automatisiert genau diesen Weg von „Ich brauche etwas" bis
„Ich habe es" — inklusive Genehmigung, wo sie nötig ist.

Technisch ist CMP ein **Django-6-Projekt** mit klassischem **Server-Rendering**:
Django liefert fertige HTML-Seiten aus, **HTMX** macht sie dort interaktiv, wo es
nötig ist, und **DaisyUI** (im eigenen „Lucent"-Theme) sorgt fürs Aussehen. CMP
läuft auf Port 8000 und nutzt PostgreSQL sowie Celery+Redis für alles, was im
Hintergrund laufen muss. Angemeldet wird sich über django-allauth, aber es gibt
**keine** Selbstregistrierung — neue Nutzer legt ausschließlich ein Admin über
das Django-Admin an.

Was das im Detail bedeutet, und warum diese Entscheidungen so getroffen
wurden, siehst du in den nächsten Kapiteln. Für den Moment reicht: CMP ist ein
Bestell- und Bereitstellungs-Portal, serverseitig gerendert, mit Django als
Rückgrat.

---

## Für wen ist dieser Guide — und wie liest du ihn?

Dieser Guide ist als **Lernpfad** aufgebaut: Die Kapitel bauen aufeinander
auf und sind in Teile gegliedert, vom großen Überblick über die Fachdomäne
bis hin zu deinem ersten eigenen Beitrag. Arbeite sie am besten der Reihe
nach durch — jedes Kapitel sagt dir am Anfang, was du danach kannst und was
du vorher wissen solltest.

Damit du dich schnell zurechtfindest, nutzt der Guide ein paar wiederkehrende
Marker:

- 💡 **Merke** — etwas, das du dir einprägen solltest
- ⚠️ **Achtung** — ein typischer Fehler oder Stolperstein
- 🔍 **Im Code nachsehen** — wo du das Beschriebene selbst im Repo findest
- 🚧 **Status: Gerüst** — dieses Kapitel ist noch in Arbeit

> **Ein Wort zur Abgrenzung:** Dieser Guide steht bewusst *neben* der
> ausführlichen Referenzdokumentation unter [`cmp-docs/`](../../cmp-docs/).
> Die ist zum *Nachschlagen* gedacht. Dieser Guide hier ist zum *Lernen* —
> du liest ihn einmal durch und verstehst danach, wie alles zusammenhängt.

---

## Was du mitbringen solltest

Du musst kein Django-Profi sein, um hier einzusteigen. Es hilft aber, wenn du
Folgendes schon mitbringst:

- **Python-Grundlagen** — du solltest mit Funktionen, Klassen und Modulen
  vertraut sein
- **Ein bisschen Django-Neugier** — projektspezifische Dinge erklären wir dir,
  aber die Grundfrage „Was ist ein Model/View/Template?" solltest du bei
  Bedarf selbst nachschlagen können
- **Git-Basics** — clone, branch, commit, push

Kein Vorwissen brauchst du dagegen zu Celery, HTMX, dem Provisioning-Ablauf
oder der Deployment-Umgebung des Portals — das ist genau der Stoff, den
dieser Guide dir vermittelt.

---

## Wie es weitergeht

Im nächsten Kapitel bekommst du das **große Bild**: einmal das gesamte
CMP-Portal in einem Diagramm, damit du eine Landkarte im Kopf hast, bevor wir
ins Detail gehen. Danach geht es Schritt für Schritt tiefer — von der
Fachdomäne über die Technik bis zu deinem ersten eigenen Code-Beitrag.

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Was bestellt ein Nutzer über CMP, und was passiert danach automatisch?
2. Warum solltest du die Kapitel dieses Guides eher der Reihe nach lesen als
   querbeet?

<details>
<summary>Antworten anzeigen</summary>

1. Er bestellt eine IT-Ressource aus einem Katalog (z. B. eine VM). Danach
   wird die Bestellung — falls nötig — genehmigt und anschließend automatisch
   bereitgestellt (Provisioning), bis am Ende ein aktives Abo entsteht.
2. Weil die Kapitel aufeinander aufbauen: Jedes Kapitel setzt die Begriffe und
   Konzepte der vorherigen voraus, damit später nichts unklar bleibt.

</details>

---

[📖 Übersicht](README.md) · [01 — Das große Bild](01-das-grosse-bild.md) ⟶
