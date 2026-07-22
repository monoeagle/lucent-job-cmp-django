# Branch- und Umgebungsweg

Wie im Repository tatsächlich gearbeitet wird — Branches, Tags,
Commit-Fluss — und wie sich das zum Zielbild „Test → QS → Prod" verhält,
das in der ausgewerteten Fremddoku vorkommt.

## 1. Ziel des Kapitels

Wer einen Beitrag einreichen will, soll wissen, gegen welchen Branch, und
welche Umgebungsstufen es beim CMP wirklich gibt — ohne ein
Enterprise-Umgebungsmodell zu unterstellen, das es hier nicht gibt.

## 2. Ist-Stand: ein Arbeitsbranch

```bash
git branch -a
```

liefert (2026-07-22):

| Branch | Rolle |
|---|---|
| `main` | einziger Arbeitsbranch — aller Code, alle Doku, alle Releases |
| `gh-pages` | reines Deploy-Ziel der gebauten Doku-Site, kein Code |
| `backup-vor-rewrite` | historische Sicherung vor einem Rewrite, kein aktiver Branch |

`backup-vor-rewrite` liegt an einem gemeinsamen Vorfahren mit `main`
(`git merge-base main backup-vor-rewrite` → `f6686b2`), ist 2 Commits
voraus und 8 Commits zurück — er wird nicht weitergeführt und ist keine
Referenz für neue Arbeit.

Es gibt **keine** Feature-Branches, keinen `develop`- oder `test`-Branch:
Commits gehen direkt auf `main`. Über die 159 Commits auf `main` (Stand
2026-07-22) hinweg ist das durchgehend so geblieben.

## 3. Kein CI/CD

Geprüft am 2026-07-22: kein `.github/workflows/`-Verzeichnis, keine
`.pre-commit-config.yaml`, keine eigenen Git-Hooks unter `.git/hooks/`
(nur die mitgelieferten `.sample`-Dateien). Tests, Linting und das
Doku-Gate (`cmp-docs/verify_docs.sh`) laufen ausschließlich lokal, vor
dem Commit — nicht automatisiert bei Push oder Pull Request.

## 4. `gh-pages`: eigener Pfad nur für die Doku

Die Doku-Site wird über `cmp-docs/deploy_ghpages.sh` gebaut und in den
`gh-pages`-Branch geschoben — über einen temporären `git worktree`, damit
`main` dabei unberührt bleibt:

```bash
./cmp-docs/deploy_ghpages.sh             # voller Build + Deploy
./cmp-docs/deploy_ghpages.sh --no-build  # vorhandenes site/ deployen
```

Dieser Weg betrifft nur die Dokumentation, nicht den Anwendungscode.

## 5. Releases markieren den Fortschritt, nicht Branches

Statt Umgebungs-Branches markieren annotierte Git-Tags den Stand:
`v1.1.0` … `v1.3.3` (Details in Kapitel 9.5). Ein Release ist ein
Commit auf `main` plus Tag, kein Merge aus einem Release-Branch.

## 6. Zielbild „Test → QS → Prod" — nicht angelegt

Die ausgewertete Fremddoku eines Bestellportals sieht einen
Umgebungsweg Test → QS → Prod vor. Im CMP-Repository ist das **nicht**
umgesetzt: ADR-0001 (Kapitel 11) erwähnt „mehrere Umgebungen/Hosts
(Dev/Test/Prod oder mehrere Kunden)" ausdrücklich nur als einen von drei
**hypothetischen Auslösern**, ab denen sich Containerisierung lohnen
würde — nicht als bestehenden Weg. Das reale Deployment-Ziel ist **eine
einzelne** (häufig air-gapped) AlmaLinux/Rocky-9-VM, nativ per systemd
installiert (`deploy/install.sh`, Kapitel 8).

Die einzige tatsächlich vorhandene Umgebungstrennung ist lokal und
datenbankbezogen: `cmp_django_dev` für die Entwicklung,
`cmp_django_test` für die Testsuite (`scripts/run.sh:11-12`), plus die
Django-Settings-Module `development`, `testing`, `production`
(`cmp/config/settings/`). Eine eigene QS-Stufe existiert nicht.

## 7. Praktischer Arbeitsablauf

1. Änderung lokal auf `main` committen (Konvention: `type(scope): ...`, Kapitel 9.2)
2. Tests lokal grün (`venv/bin/python3 -m pytest -q`)
3. Bei Doku-Änderungen: `cmp-docs/verify_docs.sh` grün
4. Bei Release: Version anheben (Kapitel 9.5), Changelog-Eintrag (Kapitel 9.6), Tag setzen
5. Push nach `origin/main`; Doku-Deploy separat über `deploy_ghpages.sh`

## 8. Zusammenfassung

Der reale Weg ist einfacher als das Zielbild aus der Fremddoku: ein
Arbeitsbranch (`main`), kein CI/CD, Releases über annotierte Tags statt
Umgebungs-Branches, ein einziges Deployment-Ziel (Single-VM, nativ). Ein
mehrstufiger Test-QS-Prod-Weg ist als Zielbild in ADR-0001 angelegt,
aber nicht gebaut — das sollte bei Verweisen auf „die Pipeline" nicht
unterstellt werden.

> Quelle: `git branch -a`, `git log --oneline main`, `git merge-base main backup-vor-rewrite`, `cmp-docs/deploy_ghpages.sh`, `cmp-docs/docs/decisions/0001-deployment-native-vs-container.md`, `scripts/run.sh:11-12`, `cmp/config/settings/` — am Code geprüft 2026-07-22
