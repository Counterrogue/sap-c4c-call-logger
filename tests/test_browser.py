from datetime import date, time
import pytest
from core import make_bulk_calls
from browser_automation import submit_to_mock

def test_playwright_full_field_readback():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright Chromium is not installed: {exc}")
    calls = make_bulk_calls([{"contact":"Dr A"},{"contact":"Dr B"}],
                            date(2026,10,8), time(9,0), "Demo University",
                            organizer="Demo Organizer", sales_territory="Demo Territory")
    saved, errors, _ = submit_to_mock(calls)
    assert not errors and len(saved) == 2
