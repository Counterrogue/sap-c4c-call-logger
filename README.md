# SAP C4C Call Logger — Local Prototype

A Python + Streamlit prototype with **two entry modes**:

1. **Meeting notes:** Convert a transcript or typed notes into editable CRM fields. Optional OpenAI processing can handle images of handwritten notes.
2. **University call day:** Enter 12–16 or more contacts in bulk. **Two meetings share each 30-minute start time** (9:00, 9:00, 9:30, 9:30, etc.), and every record keeps the selected date. Empty notes default to `General discussion/Check in`.

**Important: This app only submits calls to a LOCAL simulated CRM, not SAP.** Do not use real customer data or connect to your company's systems until IT approves the workflow.

## Quick Windows setup

1. Install **Python 3.11 or 3.12** from https://www.python.org/downloads/windows/ . Enable the Python launcher.
2. Download the repository (green **Code** button → **Download ZIP**) and extract it.
3. Double-click `setup_windows.bat`. This creates a virtual environment, installs Python packages, and downloads Playwright's Chromium browser.
4. Double-click `run_visible_windows.bat` to start the app with visible Playwright automation. Streamlit normally opens at http://localhost:8501 .
5. Under **University call day**, enter `Demo University`, paste fictional names, choose a date/time, click **Preview bulk entries** → **Add all to review queue**.
6. On **Review & mock upload**, click **Send queue to LOCAL mock CRM**. You should see Chromium fill and save the demo records.

Use `run_windows.bat` for headless (invisible) browser automation. Visible mode sets `SHOW_BROWSER=1`; it also adds a slight delay so actions are easier to observe.

## Manual PowerShell setup (alternative)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If using Python 3.12, replace `py -3.11` with `py -3.12`. For a manual visible session, set `$env:SHOW_BROWSER="1"` before launching Streamlit.

## What's Playwright doing?

`browser_automation.py` uses `page.goto()`, `page.locator(...).fill()`, and `page.get_by_role(...).click()` to control a separate Chromium instance. `mock_sap.py` serves a local sample form; the script fills it, clicks **Save**, and checks that the records were stored.

## Optional AI mode

No API key is required for basic typed notes or bulk entry; without AI, typed notes are processed with simple offline rules. Handwriting image extraction requires an API key. For **synthetic demo data only**, define `OPENAI_API_KEY` in your shell; AI requests send supplied content to an external service and may incur costs. Do not send employer/customer data without privacy and IT approval.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Files

- `app.py`: Streamlit UI and review queue.
- `core.py`: Activity model, two-per-30-minute scheduling, parsing.
- `ai_processing.py`: Optional AI extraction from text or handwriting.
- `mock_sap.py`: Local simulated CRM.
- `browser_automation.py`: Playwright mock form entry and save verification.
- `tests/`: Automated checks.
- `setup_windows.bat`, `run_windows.bat`, `run_visible_windows.bat`: Windows setup/launch scripts.

## Before connecting to SAP

Obtain IT approval for CRM automation and any AI/data handling. Inspect the specific SAP C4C page structure, then create a separate authorized adapter. Add secure account/contact matching, deduplication, save verification, auditing, error recovery, and human approval before writing to production. Never commit passwords, customer data, or API keys to this repository.
