from datetime import date,time
import pytest
from core import make_bulk_calls,parse_pasted_attendees,DEFAULT_NOTE,local_notes_draft

def test_two_per_block():
    calls=make_bulk_calls([{"contact":f"Person {i}"} for i in range(16)],date(2026,10,8),time(9,0),"Demo U")
    assert [c.start_time for c in calls]==[f"{9+(i//2)//2:02d}:{'30' if (i//2)%2 else '00'}" for i in range(16)]
    assert {c.date for c in calls}=={"2026-10-08"}
    assert all(c.notes==DEFAULT_NOTE for c in calls)

def test_ignores_blank_rows():
    calls=make_bulk_calls([{"contact":"A"},{"contact":" "},{"contact":"B"},{"contact":"C"}],date(2026,10,8),time(9,0),"Demo U")
    assert [c.start_time for c in calls]==["09:00","09:00","09:30"]

def test_paste_and_notes():
    data=parse_pasted_attendees("Name\nDr. A | Testing | Send samples\nDr. B")
    assert len(data)==2 and data[0]["next_steps"]=="Send samples"
    assert "Send pricing" in local_notes_draft("Discussed tips. Send pricing next week.")["next_steps"]

def test_midnight_guard():
    with pytest.raises(ValueError,match="midnight"):
        make_bulk_calls([{"contact":"A"},{"contact":"B"},{"contact":"C"}],date(2026,10,8),time(23,45),"Demo U")
