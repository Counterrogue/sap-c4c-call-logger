from datetime import date,time
import pytest
from core import make_bulk_calls
from browser_automation import submit_to_mock

def test_playwright_mock_save():
    try:
        import subprocess
        from pathlib import Path
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:
        pytest.skip(f"Chromium not installed: {exc}")
    calls=make_bulk_calls([{"contact":"Dr A"},{"contact":"Dr B"}],date(2026,10,8),time(9,0),"Demo U")
    saved,errors,_=submit_to_mock(calls)
    assert not errors and len(saved)==2
