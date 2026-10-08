"""Playwright mock-only demonstration; does not access SAP."""
import json
import os
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from mock_sap import start_mock_server

def submit_to_mock(calls):
    url=start_mock_server()
    saved,errors=[],[]
    with sync_playwright() as p:
        visible=os.getenv("SHOW_BROWSER")=="1"
        browser=p.chromium.launch(headless=not visible,slow_mo=300 if visible else 0)
        try:
            page=browser.new_page()
            for call in calls:
                try:
                    if not call.account.strip(): raise ValueError("Account required")
                    page.goto(url,wait_until="domcontentloaded")
                    page.locator("#record_id").evaluate("(el,v)=>el.value=v",call.id)
                    for field in ("account","contact","date","start_time","subject","notes","next_steps"):
                        page.locator("#"+field).fill(str(getattr(call,field)))
                    page.get_by_role("button",name="Save").click()
                    page.get_by_role("status").get_by_text("Saved: "+call.id,exact=True).wait_for(timeout=5000)
                    saved.append(call.id)
                except Exception as e: errors.append(f"{call.contact}: {e}")
        finally:browser.close()
    with urlopen(url+"/records",timeout=5) as response:
        ids={r["id"] for r in json.load(response)}
    verified=[id for id in saved if id in ids]
    errors.extend(f"Unverified: {id}" for id in saved if id not in ids)
    return verified,errors,url
