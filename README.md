# SAP C4C Call Logger — Local Prototype

**This prototype uses a LOCAL simulated CRM, not SAP, and never submits an approval.** The repository is public. Use fictional data only until IT approves company data and the integration.

## Features

- **Meeting notes:** Convert typed meeting notes or a transcript into editable call fields; optional AI for synthetic handwritten notes.
- **University call day:** Paste 12–16+ contacts. Two activities start at 9:00, two at 9:30, and so on. Each end time is **30 minutes after its start**. All start and end dates stay on the selected day. A bulk entry that would end after midnight is rejected.
- **Save verification:** Playwright fills the *local mock* C4C form and reads back every saved field before marking the activity verified.
- **Approval:** Not automated. The user will review/fix entries and manually submit them in SAP after future authorized integration.

## Activity field mapping from C4C screenshots

| C4C field | Prototype behavior |
|---|---|
| Account | Provided per entry; required |
| Primary Contact | Provided per entry; required |
| Subject | Notes-based or `General discussion/Check in` |
| Reason for Conversation | Sidebar-editable; initially **Without opportunity reference** |
| Opportunity | Blank (optional) |
| Type of contact | Sidebar-editable; initially **In Person Meeting** |
| Reason for contact | Sidebar-editable; initially **(New-) Product Presentation** |
| Product level 3 | Sidebar-editable; initially **210 General Lab consumables** |
| Product Level 4 | Blank (optional) |
| Start Date/Time | Chosen date; pairs of starts at 30-minute increments |
| End Date/Time | Same date; **start + 30 minutes** |
| Organizer | Sidebar-configured; fictional sample value |
| Sales Territory | Sidebar-configured; required; fictional sample value |
| Notes | Notes with next steps appended when needed |
| Campaign | **Ignored** |

### Edit activity defaults

In the sidebar, edit **Type of contact**, **Reason for Conversation**, **Reason for contact**, and **Product level 3**, alongside **Organizer** and **Sales Territory**. New individual and bulk entries use those values. Existing queued entries retain the values they had when created.

Select **Save settings on this computer** to keep them across app restarts. This writes only a local `.local_activity_defaults.json` file, which is ignored by Git. **Restore built-in defaults** clears the saved file and restores the original values.

The LOCAL simulator allows any nonblank dropdown label to make prototype testing possible. **Real SAP C4C requires exact allowed dropdown options**; no live C4C option lookup has been implemented. Later we can infer recommended values from the meeting context.

## Windows installation

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/.
2. Download this repository with **Code → Download ZIP** and extract it.
3. Double-click `setup_windows.bat` to install packages and Playwright Chromium.
4. Double-click `run_visible_windows.bat` to open Streamlit (usually http://localhost:8501) and show the automated browser.
5. Enter fictional data in **University call day**, preview it, add all to the review queue, then select **Send queue to LOCAL mock CRM**. Playwright should fill the simulated form and verify every field.
6. Use `run_windows.bat` for invisible/headless browser automation.

## Optional AI and tests

Offline typed notes and bulk entry require no API key. AI processing sends inputs to an external provider; don't use real employer/customer records without authorization. API usage can cost money.

Run tests on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub Actions runs the Python and Playwright tests on each push.

## Source files

- `app.py`: interface and review queue.
- `core.py`: field mapping and 30-minute scheduling.
- `ai_processing.py`: optional AI-assisted notes.
- `mock_sap.py`: simulated CRM form (localhost only).
- `browser_automation.py`: simulated browser entry and full-field readback.
- `tests/`: automated tests.

**Not yet implemented:** Real SAP field selectors, account/contact lookup IDs, actual server-side saved-record verification, duplicate safeguards for production, or customer/contact creation. These require IT approval and mapping the real browser interface.
