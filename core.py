"""Local-only C4C activity model and formatting. No SAP connection."""
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta
from uuid import uuid4
import re

DEFAULT_NOTE = "General discussion/Check in"
DEFAULT_REASON_FOR_CONVERSATION = "Without opportunity reference"
DEFAULT_TYPE_OF_CONTACT = "In Person Meeting"
DEFAULT_REASON_FOR_CONTACT = "(New-) Product Presentation"
DEFAULT_PRODUCT_LEVEL_3 = "210 General Lab consumables"
MEETING_DURATION_MINUTES = 30

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
    reason_for_conversation: str = DEFAULT_REASON_FOR_CONVERSATION
    type_of_contact: str = DEFAULT_TYPE_OF_CONTACT
    reason_for_contact: str = DEFAULT_REASON_FOR_CONTACT
    product_level_3: str = DEFAULT_PRODUCT_LEVEL_3
    opportunity: str = ""
    product_level_4: str = ""
    organizer: str = ""
    sales_territory: str = ""

    @property
    def end_datetime(self):
        return datetime.combine(date.fromisoformat(self.date),
                                time.fromisoformat(self.start_time)) + timedelta(minutes=MEETING_DURATION_MINUTES)

    @property
    def end_date(self):
        return self.end_datetime.date().isoformat()

    @property
    def end_time(self):
        return self.end_datetime.strftime("%H:%M")

    @property
    def sap_notes(self):
        """SAP screenshot has one Notes field, not a separate Next Steps field."""
        notes = self.notes.strip() or DEFAULT_NOTE
        steps = self.next_steps.strip()
        if steps and steps.casefold() not in notes.casefold():
            return notes + "\n\nNext steps: " + steps
        return notes

    def sap_fields(self):
        """Fields visible in the supplied C4C form; Campaign intentionally excluded."""
        return {
            "account": self.account.strip(),
            "primary_contact": self.contact.strip(),
            "subject": self.subject.strip() or DEFAULT_NOTE,
            "reason_for_conversation": self.reason_for_conversation,
            "opportunity": self.opportunity,
            "type_of_contact": self.type_of_contact,
            "reason_for_contact": self.reason_for_contact,
            "product_level_3": self.product_level_3,
            "product_level_4": self.product_level_4,
            "start_date": self.date,
            "start_time": self.start_time,
            "end_date": self.end_date,
            "end_time": self.end_time,
            "organizer": self.organizer,
            "sales_territory": self.sales_territory,
            "notes": self.sap_notes,
        }

    def as_dict(self):
        fields = asdict(self)
        fields.update({"end_date": self.end_date, "end_time": self.end_time})
        return fields

def make_bulk_calls(attendees, meeting_date: date, first_time: time,
                    default_account="", organizer="", sales_territory=""):
    rows = [r for r in attendees if str(r.get("contact") or "").strip()]
    start = first_time.hour * 60 + first_time.minute
    # Keep both start AND end date on the user-selected day.
    if rows and start + ((len(rows) - 1) // 2) * 30 + MEETING_DURATION_MINUTES >= 1440:
        raise ValueError("Meeting end times extend past midnight; choose an earlier start")
    calls = []
    for i, row in enumerate(rows):
        minute = start + (i // 2) * 30
        notes = str(row.get("notes") or "").strip() or DEFAULT_NOTE
        subject = str(row.get("subject") or "").strip() or (
            DEFAULT_NOTE if notes == DEFAULT_NOTE else "Sales discussion"
        )
        calls.append(Call(
            id=str(uuid4()),
            account=str(row.get("account") or "").strip() or default_account.strip(),
            contact=str(row["contact"]).strip(),
            date=meeting_date.isoformat(),
            start_time=f"{minute // 60:02d}:{minute % 60:02d}",
            subject=subject,
            notes=notes,
            next_steps=str(row.get("next_steps") or "").strip(),
            organizer=organizer.strip(),
            sales_territory=sales_territory.strip(),
        ))
    return calls

def parse_pasted_attendees(text):
    result = []
    for line in text.splitlines():
        parts = [p.strip() for p in (line.split("\t") if "\t" in line else line.split("|", 2))]
        if not parts or not parts[0] or parts[0].lower() in {"name", "contact", "contact name"}:
            continue
        result.append({"contact": parts[0], "notes": parts[1] if len(parts)>1 else "",
                       "next_steps": parts[2] if len(parts)>2 else ""})
    return result

def local_notes_draft(notes):
    clean = re.sub(r"\s+", " ", notes).strip()
    if not clean:
        raise ValueError("Enter notes first")
    steps = [s.strip() for s in re.split(r"(?<=[.!?])\s+", notes)
             if re.search(r"\b(send|follow[ -]?up|schedule|quote|provide|ship|email|next step|pricing|sample)\b", s, re.I)]
    return {"subject": clean[:75], "notes": notes.strip(), "next_steps": " ".join(steps)[:600]}
