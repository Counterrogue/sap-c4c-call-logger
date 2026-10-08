from datetime import date, time
import pytest
from core import (
    Call, DEFAULT_NOTE, DEFAULT_REASON_FOR_CONVERSATION, DEFAULT_REASON_FOR_CONTACT,
    DEFAULT_TYPE_OF_CONTACT, DEFAULT_PRODUCT_LEVEL_3, make_bulk_calls,
    parse_pasted_attendees, validate_activity_defaults, local_notes_draft,
)

DEMO_NUMBER = "000123456"

def batch(attendees, at=time(9, 0), **kwargs):
    return make_bulk_calls(
        attendees, date(2026, 10, 8), at, "Demo University",
        default_account_number=DEMO_NUMBER, **kwargs
    )

def test_two_per_block_and_end_times():
    calls = batch([{"contact": f"Person {i}"} for i in range(16)],
                  organizer="Demo Organizer", sales_territory="Demo Territory")
    assert [c.start_time for c in calls] == [
        f"{9+(i//2)//2:02d}:{'30' if (i//2)%2 else '00'}" for i in range(16)
    ]
    assert [c.end_time for c in calls[:6]] == [
        "09:30", "09:30", "10:00", "10:00", "10:30", "10:30"
    ]
    assert {c.date for c in calls} == {"2026-10-08"}
    assert {c.end_date for c in calls} == {"2026-10-08"}
    assert all(c.notes == DEFAULT_NOTE for c in calls)
    assert all(c.account_number == DEMO_NUMBER for c in calls)

def test_new_c4c_defaults_and_excluded_campaign():
    call = batch([{"contact": "Dr A"}], time(13, 0),
                 sales_territory="Demo Territory")[0]
    fields = call.sap_fields()
    assert fields["account_number"] == DEMO_NUMBER
    assert fields["primary_contact"] == "Dr A"
    assert fields["reason_for_conversation"] == DEFAULT_REASON_FOR_CONVERSATION
    assert fields["type_of_contact"] == DEFAULT_TYPE_OF_CONTACT
    assert fields["reason_for_contact"] == DEFAULT_REASON_FOR_CONTACT
    assert fields["product_level_3"] == DEFAULT_PRODUCT_LEVEL_3
    assert fields["start_time"] == "13:00" and fields["end_time"] == "13:30"
    assert fields["opportunity"] == "" and fields["product_level_4"] == ""
    assert "campaign" not in fields
    assert fields["sales_territory"] == "Demo Territory"

def test_next_steps_appended_to_single_notes_field():
    call = batch([{"contact":"A","notes":"Discussed pipette tips",
                   "next_steps":"Send samples"}])[0]
    assert call.sap_fields()["notes"] == "Discussed pipette tips\n\nNext steps: Send samples"

def test_blanks_do_not_consume_slots():
    calls = batch([{"contact":"A"},{"contact":" "},{"contact":"B"},{"contact":"C"}])
    assert [c.start_time for c in calls] == ["09:00","09:00","09:30"]

def test_paste_and_notes():
    data = parse_pasted_attendees("Name\nDr. A | Testing | Send samples\nDr. B")
    assert len(data) == 2 and data[0]["next_steps"] == "Send samples"
    assert "Send pricing" in local_notes_draft(
        "Discussed tips. Send pricing next week."
    )["next_steps"]

def test_midnight_guard():
    with pytest.raises(ValueError, match="midnight"):
        batch([{"contact":"A"},{"contact":"B"},{"contact":"C"}], time(23,45))

def test_custom_activity_defaults_apply_to_bulk_and_retain_time_rules():
    custom = {
        "reason_for_conversation": "Custom conversation",
        "type_of_contact": "Custom contact method",
        "reason_for_contact": "Custom reason",
        "product_level_3": "Custom product category",
    }
    calls = batch([{"contact":"Dr A"},{"contact":"Dr B"},{"contact":"Dr C"}],
                  organizer="Demo Organizer", sales_territory="Demo Territory",
                  activity_defaults=custom)
    for call in calls:
        for key, value in custom.items():
            assert call.sap_fields()[key] == value
    assert [c.start_time for c in calls] == ["09:00","09:00","09:30"]
    assert [c.end_time for c in calls] == ["09:30","09:30","10:00"]

def test_activity_defaults_reject_blank_and_unknown_values():
    with pytest.raises(ValueError, match="Fill in"):
        validate_activity_defaults({"type_of_contact":"  "})
    with pytest.raises(ValueError, match="Unsupported"):
        validate_activity_defaults({"campaign":"None"})

def test_account_number_overrides_default_and_preserves_leading_zeroes():
    calls = batch([
        {"contact":"Dr A"},
        {"contact":"Dr B", "account_number":"000009999", "account":"Different account"},
        {"contact":"Dr C", "account_number":"  00120  "}
    ])
    assert [c.account_number for c in calls] == [
        "000123456","000009999","00120"
    ]
    assert calls[1].sap_fields()["account"] == "Different account"
    assert calls[2].start_time == "09:30"

def test_account_name_does_not_substitute_for_missing_id():
    with pytest.raises(ValueError, match="Account Number is required"):
        make_bulk_calls([{"contact":"Dr A", "account":"Named University"}],
                        date(2026,10,8), time(9,0), "Named University")

def test_account_name_optional_when_number_supplied():
    calls = make_bulk_calls([{"contact":"Dr A"}], date(2026,10,8),
                            time(9,0), default_account_number="000010")
    assert calls[0].account == ""
    assert calls[0].sap_fields()["account_number"] == "000010"
