# UI-Parität mit Flask-Projekt — Design Specification

**Datum:** 2026-03-29
**Status:** Approved
**Ziel:** Alle Seiten, Menüs und Darstellungsoptionen des Flask/React-Frontends als Django Templates mit HTMX, DaisyUI und Chart.js nachbauen.

---

## 1. Chart.js Integration

Chart.js 4.x via CDN in `base.html`. Zwei Standard-Charts:
- **Order-Status Donut:** draft/submitted/pending_approval/approved/provisioning/done/failed/rejected
- **Order-Timeline Line:** Bestellungen pro Monat (letzte 6 Monate)

Farben analog zum Flask-Projekt:
- draft: #9CA3AF, submitted: #3B82F6, pending_approval: #F59E0B
- approved: #8B5CF6, provisioning: #6366F1, done: #10B981
- failed: #EF4444, rejected: #F97316

---

## 2. Sidebar (erweitert)

Badges für ungelesene Notifications und pending Approvals. Rollenbasierte Sichtbarkeit. Collapsible auf Mobile (bereits via DaisyUI Drawer).

---

## 3. Seiten

### Dashboard (erweitert) — `/`
4 Stat-Cards (Offene Orders, Pending Approvals, Aktive Subscriptions, Templates), 2 Charts, Recent Orders (5), Popular Services (5).

### Shop/Katalog (erweitert) — `/catalog/`
Bestehend + Kategorie-Dropdown und Text-Suche als HTMX-Filter.

### Workspace/Bestellungen (erweitert) — `/orders/`
Tabs (Alle/Meine), Status-Filter-Pills, Tabelle mit Status-Badges.

### Order-Detail (erweitert) — `/orders/<pk>/`
Items-Liste, Add-Item-Button, Submit-Button (nur Draft), Status-Badge.

### Review Requests — `/approvals/`
Status-Tabs (Pending/Approved/Rejected/Alle), expandierbare Cards mit Order-Details, Approve/Reject-Buttons.

### Notifications (erweitert) — `/notifications/`
Tabs (Alle/Ungelesen), Mark-All-Read-Button, Event-Badges mit Farben.

### Admin Dashboard — `/admin-panel/`
System-Stats (alle Order-Status-Counts), Charts, System-Health (DB + CMDB Status).

### Admin Config — `/admin-panel/config/`
Read-only Sections (Auth, CMDB, DB) + Editable (Approval-Settings).

### Admin Rules — `/admin-panel/rules/`
4 Tabs: Approval-Rules, Availability-Rules, Context-Restrictions, Tenant-Assignments.

### Audit Log (erweitert) — `/audit/`
Filter (Action, Entity, Datum), CSV-Export-Button.

---

## 4. Technische Umsetzung

- `DashboardService` in `apps/dashboard/services.py` — Stats-Aggregation
- `core/context_processors.py` — Badge-Counts für Sidebar (in jeder Seite)
- Chart.js via `<script src="cdn">` + inline `<canvas>` + JSON-Daten via `{{ stats|json_script }}`
- HTMX für: Filter, Tabs, Inline-Actions, Badge-Refresh
- Alle Templates in DaisyUI mit bestehendem Theme "Lucent"
