"""Streamlit interface to a LOCAL simulated C4C activity form."""
from datetime import date, time
import json
from uuid import uuid4
import pandas as pd
import streamlit as st
from core import (
    Call, DEFAULT_NOTE, DEFAULT_ACTIVITY_FIELDS, validate_activity_defaults,
    make_bulk_calls, parse_pasted_attendees,
)
from settings import DEFAULT_SETTINGS, load_settings, save_settings, reset_settings
from ai_processing import extract_call
from browser_automation import submit_to_mock

st.set_page_config(page_title="C4C Call Logger — LOCAL Demo", page_icon="📋", layout="wide")
st.title("C4C Sales Call Logger")
st.caption("LOCAL prototype. No SAP connection or approval submission.")

if "settings_initialized" not in st.session_state:
    for name, value in load_settings().items():
        st.session_state["setting_" + name] = value
    st.session_state.settings_initialized = True

def restore_activity_defaults():
    reset_settings()
    for name, value in DEFAULT_SETTINGS.items():
        st.session_state["setting_" + name] = value

with st.sidebar:
    st.subheader("Editable activity defaults")
    st.text_input("Type of contact *", key="setting_type_of_contact")
    st.text_input("Reason for Conversation *", key="setting_reason_for_conversation")
    st.text_input("Reason for contact *", key="setting_reason_for_contact")
    st.text_input("Product level 3 *", key="setting_product_level_3")
    st.caption("Enter the exact labels used by your C4C dropdowns. These are free-text in the local prototype.")
    st.divider()
    st.subheader("Account settings")
    organizer = st.text_input("Organizer", key="setting_organizer")
    territory = st.text_input("Sales Territory *", key="setting_sales_territory")
    if st.button("Save settings on this computer"):
        try:
            save_settings({
                key: st.session_state["setting_" + key]
                for key in DEFAULT_SETTINGS
            })
            st.success("Saved locally. Not uploaded to GitHub.")
        except (ValueError, OSError) as error:
            st.error(str(error))
    st.button("Restore built-in defaults", on_click=restore_activity_defaults)
    st.caption("Edits apply to newly created activities. Existing queued entries do not change.")

activity_defaults = {
    key: st.session_state["setting_" + key]
    for key in DEFAULT_ACTIVITY_FIELDS
}

if "queue" not in st.session_state:
    st.session_state.queue = []
if "rows" not in st.session_state:
    st.session_state.rows = [
        {"contact":"","account":"","notes":"","next_steps":"","subject":""}
        for _ in range(16)
    ]
if "editor_key" not in st.session_state:
    st.session_state.editor_key = 0

notes_tab, bulk_tab, queue_tab = st.tabs([
    "Meeting notes", "University call day", "Review & local mock upload"
])
with notes_tab:
    st.subheader("Meeting transcript or handwritten notes")
    col1, col2 = st.columns(2)
    account = col1.text_input("Account", key="single_account", placeholder="Demo University")
    contact = col2.text_input("Primary Contact", key="single_contact", placeholder="Dr. Example")
    col1, col2 = st.columns(2)
    meeting_date = col1.date_input("Start Date", date.today(), key="single_date")
    meeting_time = col2.time_input("Start Time", time(9,0), key="single_time", step=1800)
    st.caption("End Date/Time is automatically 30 minutes after Start Date/Time.")
    transcript = st.text_area("Transcript / typed notes", height=160)
    photo = st.file_uploader("Optional handwritten note image (AI mode only)",
                             type=["png","jpeg","jpg","webp"])
    use_ai = st.checkbox("Use AI (synthetic notes only until IT approval)", value=False)
    if use_ai:
        st.warning("AI sends notes and images to an external provider. Use synthetic demo data only.")
    if st.button("Prepare activity", key="prepare", type="primary"):
        try:
            if not account.strip() or not contact.strip():
                raise ValueError("Enter Account and Primary Contact")
            draft = extract_call(transcript,
                                 photo.getvalue() if photo else None,
                                 photo.type if photo else "image/jpeg",
                                 use_ai)
            st.session_state.draft = {
                "account":account, "contact":contact,
                "date":meeting_date.isoformat(),
                "start_time":meeting_time.strftime("%H:%M"), **draft
            }
        except Exception as error:
            st.error(str(error))
    if "draft" in st.session_state:
        draft = st.session_state.draft
        with st.form("review_notes"):
            subject = st.text_input("Subject", value=draft.get("subject") or DEFAULT_NOTE)
            clean_notes = st.text_area("Notes", value=draft.get("notes") or DEFAULT_NOTE)
            next_steps = st.text_area("Next steps (appended to Notes in C4C)",
                                      value=draft.get("next_steps") or "")
            if st.form_submit_button("Add to queue"):
                try:
                    defaults = validate_activity_defaults(activity_defaults)
                    if not territory.strip():
                        raise ValueError("Sales Territory is required")
                    call = Call(
                        id=str(uuid4()), account=draft["account"], contact=draft["contact"],
                        date=draft["date"], start_time=draft["start_time"],
                        subject=subject, notes=clean_notes, next_steps=next_steps,
                        source="meeting-notes", organizer=organizer, sales_territory=territory,
                        **defaults,
                    )
                    st.session_state.queue.append(call)
                    del st.session_state.draft
                    st.success("Activity added to review queue")
                except ValueError as error:
                    st.error(str(error))

with bulk_tab:
    st.subheader("University call-day bulk entry")
    a,b,c = st.columns(3)
    default_account = a.text_input("University / default account", placeholder="Demo University")
    day = b.date_input("Start Date", date.today(), key="bulk_date")
    first = c.time_input("First meeting time", time(9,0), key="bulk_time", step=1800)
    st.info("Each pair shares a start time. 9:00–9:30, 9:00–9:30, 9:30–10:00, 9:30–10:00, etc.")
    paste = st.text_area("Paste contacts: one per line, optionally Name | Notes | Next steps")
    if st.button("Fill table from list"):
        parsed = parse_pasted_attendees(paste)
        st.session_state.rows = [
            {"contact":r["contact"],"account":"","notes":r["notes"],
             "next_steps":r["next_steps"],"subject":""} for r in parsed
        ]
        st.session_state.editor_key += 1
        st.session_state.pop("preview", None)
        st.rerun()
    df = pd.DataFrame(st.session_state.rows,
                      columns=["contact","account","notes","next_steps","subject"])
    edited = st.data_editor(df, num_rows="dynamic", hide_index=True,
                            width="stretch",
                            key=f"editor_{st.session_state.editor_key}")
    if st.button("Preview bulk entries", type="primary"):
        try:
            normalized = edited.fillna("").to_dict("records")
            calls = make_bulk_calls(normalized, day, first, default_account,
                                    organizer=organizer, sales_territory=territory,
                                    activity_defaults=activity_defaults)
            if not calls:
                st.warning("Enter at least one contact")
            else:
                st.session_state.preview = calls
                st.session_state.rows = normalized
        except ValueError as error:
            st.error(str(error))
    if "preview" in st.session_state:
        preview = pd.DataFrame([x.sap_fields() for x in st.session_state.preview])
        st.dataframe(preview[[
            "account","primary_contact","subject",
            "start_date","start_time","end_date","end_time",
            "reason_for_conversation","type_of_contact",
            "reason_for_contact","product_level_3","notes"
        ]], hide_index=True)
        if preview["account"].eq("").any():
            st.warning("Some records have no Account; mock upload requires one.")
        if st.button("Add all to queue"):
            st.session_state.queue.extend(st.session_state.preview)
            del st.session_state.preview
            st.success("Activities added to review queue")

with queue_tab:
    st.subheader(f"Review queue ({len(st.session_state.queue)})")
    if st.session_state.queue:
        records = [dict(id=x.id, source=x.source, **x.sap_fields())
                   for x in st.session_state.queue]
        df = pd.DataFrame(records)
        st.dataframe(df[[
            "account","primary_contact","subject","start_date","start_time",
            "end_date","end_time","reason_for_conversation","type_of_contact",
            "reason_for_contact","product_level_3","product_level_4",
            "organizer","sales_territory","notes","source"
        ]], hide_index=True)
        st.download_button("Download CRM-ready CSV", df.to_csv(index=False).encode(),
                           file_name="demo_calls.csv")
        st.download_button("Download JSON", json.dumps(records, indent=2),
                           file_name="demo_calls.json")
        if st.button("Clear queue"):
            st.session_state.queue = []
            st.rerun()
        if st.button("Send queue to LOCAL mock CRM", type="primary"):
            try:
                saved, errors, url = submit_to_mock(st.session_state.queue)
                st.success(f"{len(saved)} records saved and all fields verified in local simulator")
                st.markdown(f"[Open local simulator]({url})")
                for error in errors:
                    st.error(error)
            except Exception as error:
                st.error("Browser test failed: " + str(error) +
                         ". Check Playwright installation: python -m playwright install chromium")
    else:
        st.write("Add records from either entry mode first.")
st.divider()
st.caption("Approval stays manual. Never enter real company/customer information without IT approval.")
