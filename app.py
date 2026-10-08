"""Streamlit UI; mock CRM only."""
from datetime import date, time
import json
from uuid import uuid4
import pandas as pd
import streamlit as st
from core import Call, DEFAULT_NOTE, make_bulk_calls, parse_pasted_attendees
from ai_processing import extract_call
from browser_automation import submit_to_mock

st.set_page_config(page_title="SAP C4C Call Logger — Local Demo",page_icon="📋",layout="wide")
st.title("Sales Call Logger")
st.caption("LOCAL prototype only; does not connect to SAP.")
if "queue" not in st.session_state:st.session_state.queue=[]
if "rows" not in st.session_state:st.session_state.rows=[{"contact":"","account":"","notes":"","next_steps":"","subject":""} for _ in range(16)]
if "editor_key" not in st.session_state:st.session_state.editor_key=0
notes_tab,bulk_tab,queue_tab=st.tabs(["Meeting notes","University call day","Review & local mock upload"])
with notes_tab:
    st.subheader("Meeting transcript or handwritten notes")
    a,b=st.columns(2)
    account=a.text_input("Account",key="single_account",placeholder="Sample University")
    contact=b.text_input("Contact",key="single_contact",placeholder="Dr. Example")
    a,b=st.columns(2)
    meeting_date=a.date_input("Date",date.today(),key="single_date")
    meeting_time=b.time_input("Start time",time(9,0),key="single_time",step=1800)
    transcript=st.text_area("Transcript / typed notes",height=160)
    photo=st.file_uploader("Optional handwritten note image (AI mode only)",type=["png","jpeg","jpg","webp"])
    ai=st.checkbox("Use AI (synthetic notes only until IT approval)",value=False)
    if ai:st.warning("AI sends notes and images to an external provider. Use synthetic demo data only.")
    if st.button("Prepare activity",key="prepare",type="primary"):
        try:
            if not account.strip() or not contact.strip():raise ValueError("Enter account and contact")
            draft=extract_call(transcript,photo.getvalue() if photo else None,photo.type if photo else "image/jpeg",ai)
            st.session_state.draft=dict(account=account,contact=contact,date=meeting_date.isoformat(),start_time=meeting_time.strftime("%H:%M"),**draft)
        except Exception as exc:st.error(str(exc))
    if "draft" in st.session_state:
        draft=st.session_state.draft
        with st.form("review_notes"):
            subject=st.text_input("Subject",value=draft.get("subject") or DEFAULT_NOTE)
            clean_notes=st.text_area("CRM Notes",value=draft.get("notes") or DEFAULT_NOTE)
            steps=st.text_area("Next steps",value=draft.get("next_steps") or "")
            if st.form_submit_button("Add to queue"):
                st.session_state.queue.append(Call(str(uuid4()),draft["account"],draft["contact"],draft["date"],draft["start_time"],subject,clean_notes,steps,"meeting-notes"))
                del st.session_state.draft
                st.success("Activity added")
with bulk_tab:
    st.subheader("University call-day bulk entry")
    a,b,c=st.columns(3)
    default_account=a.text_input("University / default account",placeholder="Sample University")
    day=b.date_input("Activity date",date.today(),key="bulk_date")
    first=c.time_input("First meeting time",time(9,0),key="bulk_time",step=1800)
    st.info("Two meetings per 30-minute block: 9:00, 9:00, 9:30, 9:30, etc. Same date for all entries.")
    paste=st.text_area("Paste names: one per line, optionally Name | Notes | Next steps")
    if st.button("Fill table from list"):
        parsed=parse_pasted_attendees(paste)
        st.session_state.rows=[{"contact":r["contact"],"account":"","notes":r["notes"],"next_steps":r["next_steps"],"subject":""} for r in parsed]
        st.session_state.editor_key+=1
        st.session_state.pop("preview",None)
        st.rerun()
    df=pd.DataFrame(st.session_state.rows,columns=["contact","account","notes","next_steps","subject"])
    edited=st.data_editor(df,num_rows="dynamic",hide_index=True,use_container_width=True,key=f"editor_{st.session_state.editor_key}")
    if st.button("Preview bulk entries",type="primary"):
        try:
            normalized=edited.fillna("").to_dict("records")
            calls=make_bulk_calls(normalized,day,first,default_account)
            if not calls:st.warning("Enter at least one contact")
            else:
                st.session_state.preview=calls
                st.session_state.rows=normalized
        except ValueError as exc:st.error(str(exc))
    if "preview" in st.session_state:
        pdview=pd.DataFrame([x.as_dict() for x in st.session_state.preview])
        st.dataframe(pdview[["account","contact","date","start_time","subject","notes","next_steps"]],hide_index=True)
        if pdview["account"].eq("").any():st.warning("Missing account in some records; mock upload requires accounts.")
        if st.button("Add all to queue"):
            st.session_state.queue.extend(st.session_state.preview)
            del st.session_state.preview
            st.success("Added to queue")
with queue_tab:
    st.subheader(f"Review queue ({len(st.session_state.queue)})")
    if st.session_state.queue:
        records=[c.as_dict() for c in st.session_state.queue]
        df=pd.DataFrame(records)
        st.dataframe(df[["account","contact","date","start_time","subject","notes","next_steps","source"]],hide_index=True)
        st.download_button("Download CSV",df.to_csv(index=False).encode(),file_name="demo_calls.csv")
        st.download_button("Download JSON",json.dumps(records,indent=2),file_name="demo_calls.json")
        if st.button("Clear queue"):
            st.session_state.queue=[]
            st.rerun()
        if st.button("Send queue to LOCAL mock CRM",type="primary"):
            try:
                saved,errors,url=submit_to_mock(st.session_state.queue)
                st.success(f"{len(saved)} verified in local mock CRM")
                st.markdown(f"[Open local simulator]({url})")
                for error in errors:st.error(error)
            except Exception as exc:st.error("Browser test failed: "+str(exc)+". Try: python -m playwright install chromium")
    else:st.write("Add records from either entry mode first.")
st.divider()
st.caption("No real customer data, company credentials, or SAP integration in this prototype.")
