from datetime import date, time
import pytest
from core import (Call, DEFAULT_NOTE, DEFAULT_REASON_FOR_CONVERSATION,
                  DEFAULT_REASON_FOR_CONTACT, DEFAULT_TYPE_OF_CONTACT,
                  DEFAULT_PRODUCT_LEVEL_3, make_bulk_calls, parse_pasted_attendees,
                  local_notes_draft)

def test_two_per_block_and_end_times():
    calls = make_bulk_calls([{"contact": f"Person {i}"} for i in range(16)],
                            date(2026,10,8), time(9,0), "Demo University",
                            organizer="Demo Organizer", sales_territory="Demo Territory")
    assert [c.start_time for c in calls] == [
        f"{9+(i//2)//2:02d}:{'30' if (i//2)%2 else '00'}" for i in range(16)
    ]
    assert [c.end_time for c in calls[:6]] == [
        "09:30","09:30","10:00","10:00","10:30","10:30"
    ]
    assert {c.date for c in calls} == {"2026-10-08"}
    assert {c.end_date for c in calls} == {"2026-10-08"}
    assert all(c.notes == DEFAULT_NOTE for c in calls)

def test_new_c4c_defaults_and_excluded_campaign():
    call = make_bulk_calls([{"contact": "Dr A"}], date(2026,10,8),
                           time(13,0), "Demo University", sales_territory="Demo Territory")[0]
    fields = call.sap_fields()
    assert fields["primary_contact"] == "Dr A"
    assert fields["reason_for_conversation"] == DEFAULT_REASON_FOR_CONVERSATION == "Without opportunity reference"
    assert fields["type_of_contact"] == DEFAULT_TYPE_OF_CONTACT == "In Person Meeting"
    assert fields["reason_for_contact"] == DEFAULT_REASON_FOR_CONTACT == "(New-) Product Presentation"
    assert fields["product_level_3"] == DEFAULT_PRODUCT_LEVEL_3 == "210 General Lab consumables"
    assert fields["start_time"] == "13:00" and fields["end_time"] == "13:30"
    assert fields["opportunity"] == "" and fields["product_level_4"] == ""
    assert "campaign" not in fields
    assert fields["sales_territory"] == "Demo Territory"

def test_next_steps_appended_to_single_notes_field():
    call = make_bulk_calls([{"contact":"A","notes":"Discussed pipette tips","next_steps":"Send samples"}],
                           date(2026,10,8),time(9,0),"Demo University")[0]
    assert call.sap_fields()["notes"] == "Discussed pipette tips\n\nNext steps: Send samples"

def test_blanks_do_not_consume_slots():
    calls = make_bulk_calls([{"contact":"A"},{"contact":" "},{"contact":"B"},{"contact":"C"}],
                            date(2026,10,8), time(9,0), "Demo University")
    assert [c.start_time for c in calls] == ["09:00", "09:00", "09:30"]

def test_paste_and_notes():
    data = parse_pasted_attendees("Name\nDr. A | Testing | Send samples\nDr. B")
    assert len(data) == 2 and data[0]["next_steps"] == "Send samples"
    assert "Send pricing" in local_notes_draft("Discussed tips. Send pricing next week.")["next_steps"]

def test_midnight_guard():
    with pytest.raises(ValueError, match="midnight"):
        make_bulk_calls([{"contact":"A"},{"contact":"B"},{"contact":"C"}],
                        date(2026,10,8),time(23,45),"Demo University")
