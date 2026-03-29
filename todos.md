# MPP Django — Todos

## Phase 0: Projekt-Setup
- [ ] Django-Projekt initialisieren (config/, manage.py)
- [ ] PostgreSQL-Datenbanken anlegen (mpp_dev, mpp_test)
- [ ] Virtual Environment + requirements.txt
- [ ] pytest-django Konfiguration
- [ ] Git-Repository initialisieren

## Phase B1: Identity & Access
- [ ] Custom User Model + Rollen
- [ ] JWT-Auth (simplejwt) + Stub-Mode
- [ ] Auth-Middleware + Permission Classes
- [ ] Login/Logout API

## Phase B2: Service Catalog
- [ ] ServiceTemplate Model + JSONB Parameters
- [ ] Template Validator
- [ ] Catalog Service
- [ ] Catalog API (CRUD + Suche)

## Phase B3: Order Lifecycle
- [ ] Order/OrderItem Models + Status-Machine
- [ ] Order Service (CRUD, Validation, Submission)
- [ ] Order API Endpoints
- [ ] OpenTofu Export

## Phase B4: Context & CMDB
- [ ] CMDB Stub Client (YAML-basiert)
- [ ] Context Service
- [ ] Availability Rules
- [ ] Context API

## Phase B5: Provisioning Engine
- [ ] GitLab Mock Server
- [ ] Provisioning Service
- [ ] Dispatch API + Webhooks

## Phase B6: Approval Workflow
- [ ] Approval Rules + Requests Models
- [ ] Approval Service
- [ ] Approval API

## Phase B7: Cross-Cutting Concerns
- [ ] Audit Logs + DSGVO
- [ ] Notifications (In-App + SSE)
- [ ] Credential Delivery
- [ ] Admin Dashboard

## Phase F1-F7: Frontend
- [ ] React Scaffold + Routing
- [ ] Layout + Navigation
- [ ] Service Catalog UI
- [ ] Order Wizard
- [ ] Approval Queue
- [ ] Admin Panel
- [ ] Dashboard

## Infrastructure
- [ ] Dev-Launcher (scripts/mpp.sh)
- [ ] Docker-Setup
- [ ] Seed-Script (Management Command)
- [ ] Offline-Installer
