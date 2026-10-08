"""Playwright automation for the LOCAL mock only. No SAP connection."""
import json
import os
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from mock_sap import start_mock_server

SELECT_FIELDS = (
    "reason_for_conversation", "type_of_contact",
    "reason_for_contact", "product_level_3"
)

def submit_to_mock(calls):
    """Submit and independently read back every mapped field before marking verified."""
    url = start_mock_server()
    verified, errors = [], []
    with sync_playwright() as p:
        visible = os.getenv("SHOW_BROWSER") == "1"
        browser = p.chromium.launch(headless=not visible, slow_mo=300 if visible else 0)
        try:
            page = browser.new_page()
            for call in calls:
                try:
                    expected = call.sap_fields()
                    if not expected["account_number"] or not expected["primary_contact"] or not expected["sales_territory"]:
                        raise ValueError("Account Number, Primary Contact and Sales Territory are required")
                    page.goto(url, wait_until="domcontentloaded")
                    page.locator("#record_id").evaluate("(element,value)=>element.value=value", call.id)
                    for field, value in expected.items():
                        control = page.locator("#" + field)
                        if field in SELECT_FIELDS:
                            # MOCK ONLY: dynamically add the configured label so the
                            # simulator can test choices not present in its tiny list.
                            # Real SAP must select a valid option already in C4C.
                            control.evaluate("""(select, value) => {
                                if (![...select.options].some(o => o.value === value)) {
                                    select.add(new Option(value, value));
                                }
                            }""", str(value))
                            control.select_option(value=str(value))
                        else:
                            control.fill(str(value))
                    page.get_by_role("button", name="Save draft activity").click()
                    page.get_by_role("status").get_by_text("Saved: " + call.id, exact=True).wait_for(timeout=5000)
                    # A successful click is NOT enough: read back every field.
                    with urlopen(url + "/records", timeout=5) as response:
                        stored = {obj["id"]: obj for obj in json.load(response)}
                    if call.id not in stored:
                        raise ValueError("Save acknowledged, but record not found")
                    mismatches = [key for key, value in expected.items()
                                  if stored[call.id].get(key) != value]
                    if mismatches:
                        raise ValueError("Read-back mismatch: " + ", ".join(mismatches))
                    verified.append(call.id)
                except Exception as error:
                    errors.append(f"{call.contact}: {error}")
        finally:
            browser.close()
    return verified, errors, url
