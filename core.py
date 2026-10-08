"""Local prototype; no SAP connection."""
from dataclasses import dataclass, asdict
from datetime import date, time
from uuid import uuid4
import re

DEFAULT_NOTE = "General discussion/Check in"

@dataclass
class Call:
    id: str
    account: str
    contact: str
    date: str
    start_time: str
    subject: str
    notes: str
    next_steps: str = ""
    source: str = "bulk"

    def as_dict(self):
        return asdict(self)

def make_bulk_calls(attendees, meeting_date: date, first_time: time, default_account=""):
    rows = [r for r in attendees if str(r.get("contact") or "").strip()]
    first = first_time.hour * 60 + first_time.minute
    if rows and first + ((len(rows)-1)//2)*30 >= 1440:
        raise ValueError("Meeting times extend past midnight")
    output = []
    for i, r in enumerate(rows):
        mins = first + (i//2)*30
        notes = str(r.get("notes") or "").strip() or DEFAULT_NOTE
        subject = str(r.get("subject") or "").strip() or (DEFAULT_NOTE if notes == DEFAULT_NOTE else "Sales discussion")
        output.append(Call(str(uuid4()), str(r.get("account") or "").strip() or default_account.strip(),
            str(r["contact"]).strip(), meeting_date.isoformat(), f"{mins//60:02d}:{mins%60:02d}",
            subject, notes, str(r.get("next_steps") or "").strip()))
    return output

def parse_pasted_attendees(text):
    result = []
    for line in text.splitlines():
        parts = [p.strip() for p in (line.split("\t") if "\t" in line else line.split("|",2))]
        if not parts or not parts[0] or parts[0].lower() in {"name","contact","contact name"}:
            continue
        result.append({"contact": parts[0], "notes":parts[1] if len(parts)>1 else "",
                       "next_steps":parts[2] if len(parts)>2 else ""})
    return result

def local_notes_draft(notes):
    clean = re.sub(r"\s+"," ",notes).strip()
    if not clean:
        raise ValueError("Enter notes first")
    next_steps = [s.strip() for s in re.split(r"(?<=[.!?])\s+",notes) if re.search(r"\b(send|follow[ -]?up|schedule|quote|provide|ship|email|next step|pricing|sample)\b",s,re.I)]
    return {"subject":clean[:75],"notes":notes.strip(),"next_steps":" ".join(next_steps)[:600]}
