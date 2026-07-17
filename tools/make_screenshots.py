#!/usr/bin/env python3
"""Oberflächen-Galerie neu aufnehmen (CloudMan Portal / CMP).

Erzeugt die 14 Screenshots der Doku-Galerie (`cmp-docs/docs/referenz/oberflaeche.md`)
per Selenium gegen ein LAUFENDES Dev-Portal. Full-Page-Aufnahmen via Chrome-CDP.

Voraussetzungen:
  - selenium + chromedriver + google-chrome (im PATH)
  - Dev-DB migriert + geseedet:
        DJANGO_SETTINGS_MODULE=config.settings.development \\
            venv/bin/python3 cmp/manage.py migrate && ... seed
  - Portal läuft auf 127.0.0.1:8000:
        DJANGO_SETTINGS_MODULE=config.settings.development \\
            venv/bin/python3 cmp/manage.py runserver 127.0.0.1:8000 --noreload

Aufruf (aus dem Repo-Root):
        venv/bin/python3 tools/make_screenshots.py

Die 13 Ansichten decken 3 Rollen ab (Requester 01–10, Approver 11, Superadmin
12–13); 05/05b nutzen die Formular-Ansicht (alle Abschnitte + befüllte Summary).
Login-Passwort aller Test-User: test123.
"""
import base64
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "cmp-docs/docs/images/screenshots"
LINUX_VM_TEMPLATE_PK = 1  # aus dem Seed; wird sonst dynamisch aufgelöst

_opts = Options()
for a in ("--headless=new", "--window-size=1600,1200", "--hide-scrollbars",
          "--force-device-scale-factor=1", "--no-sandbox"):
    _opts.add_argument(a)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    driver = webdriver.Chrome(options=_opts)
    driver.set_page_load_timeout(40)

    def shot(name, wait=1.2):
        time.sleep(wait)
        res = driver.execute_cdp_cmd(
            "Page.captureScreenshot", {"captureBeyondViewport": True, "fromSurface": True})
        (OUT / name).write_bytes(base64.b64decode(res["data"]))
        print(f"  OK {name}")

    def logout():
        driver.get(BASE + "/accounts/logout/")
        try:
            if "logout" in driver.page_source.lower() or "abmeld" in driver.page_source.lower():
                driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
                time.sleep(0.6)
        except Exception:
            pass

    def login(user, pw="test123"):
        logout()
        driver.get(BASE + "/accounts/login/")
        driver.find_element(By.NAME, "login").send_keys(user)
        driver.find_element(By.NAME, "password").send_keys(pw)
        driver.find_element(By.CSS_SELECTOR, "button[type=submit],input[type=submit]").click()
        time.sleep(1.4)

    def fill_all():
        """Formular-Ansicht komplett befüllen (best effort)."""
        for sel in driver.find_elements(By.TAG_NAME, "select"):
            try:
                s = Select(sel)
                vals = [o.get_attribute("value") for o in s.options if o.get_attribute("value")]
                if vals:
                    s.select_by_value(vals[-1])
            except Exception:
                pass
        for inp in driver.find_elements(
                By.CSS_SELECTOR, "input[type=text],input[type=number],input[type=email],input:not([type])"):
            try:
                if inp.get_attribute("value"):
                    continue
                t = inp.get_attribute("type")
                inp.send_keys("8" if t == "number" else ("demo@example.com" if t == "email" else "demo"))
            except Exception:
                pass
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type=checkbox]"):
            try:
                if not cb.is_selected():
                    cb.click()
            except Exception:
                pass
        driver.execute_script(
            "document.querySelectorAll('select,input,textarea').forEach("
            "e=>{e.dispatchEvent(new Event('input',{bubbles:true}));"
            "e.dispatchEvent(new Event('change',{bubbles:true}));});")

    tpl = LINUX_VM_TEMPLATE_PK
    try:
        # 01 Login (ausgeloggt)
        logout(); driver.get(BASE + "/accounts/login/"); shot("Screenshot_01_cmp.png")

        # ── Requester (01–10) ──
        login("test-requester")
        driver.get(BASE + "/");                     shot("Screenshot_02_cmp.png")  # Dashboard
        driver.get(BASE + "/catalog/");             shot("Screenshot_03_cmp.png")
        driver.get(BASE + f"/catalog/{tpl}/");      shot("Screenshot_04_cmp.png")  # Linux-VM-Detail
        driver.get(BASE + f"/orders/create/{tpl}/form/"); shot("Screenshot_05_cmp.png")  # Formular leer
        fill_all();                                 shot("Screenshot_05b_cmp.png", wait=2.5)  # ausgefüllt
        driver.get(BASE + "/orders/");              shot("Screenshot_06_cmp.png")
        # jüngste eingereichte Bestellung als Detail
        driver.get(BASE + "/orders/");
        try:
            link = driver.find_element(By.CSS_SELECTOR, "a[href*='/orders/']")
            driver.get(link.get_attribute("href"))
        except Exception:
            driver.get(BASE + "/orders/8/")
        shot("Screenshot_07_cmp.png")
        driver.get(BASE + "/notifications/");       shot("Screenshot_08_cmp.png")
        driver.get(BASE + "/subscriptions/");       shot("Screenshot_09_cmp.png")
        driver.get(BASE + "/accounts/profile/");    shot("Screenshot_10_cmp.png")

        # ── Approver (11) ──
        login("test-approver")
        driver.get(BASE + "/approvals/");           shot("Screenshot_11_cmp.png")

        # ── Superadmin (12–13) ──
        login("test-superadmin")
        driver.get(BASE + "/audit/");               shot("Screenshot_12_cmp.png")
        driver.get(BASE + "/admin/");               shot("Screenshot_13_cmp.png")
        print("FERTIG — 14 Screenshots in", OUT)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
