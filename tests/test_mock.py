import pytest
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import json
from datetime import date, time
from core import make_bulk_calls
from mock_sap import start_mock_server

def test_mock_save_and_readback_account_number():
    url = start_mock_server()
    call = make_bulk_calls([{"contact":"Dr A"}], date(2026,10,8),
                           time(9,0), "Unreliable demo name",
                           default_account_number="000098765",
                           organizer="Demo Organizer", sales_territory="Demo Territory")[0]
    obj = {"id":call.id, **call.sap_fields()}
    request = Request(url+"/save",data=json.dumps(obj).encode(),
                      headers={"Content-Type":"application/json"})
    with urlopen(request) as response:
        assert json.load(response)["id"] == obj["id"]
    with urlopen(url+"/records") as response:
        stored = {entry["id"]:entry for entry in json.load(response)}
    assert stored[call.id] == obj
    assert stored[call.id]["account_number"] == "000098765"

def test_mock_rejects_missing_account_number_even_when_named():
    url = start_mock_server()
    obj = {
        "id":"missing-account-number-01", "account":"Named Demo University",
        "account_number":"", "primary_contact":"Dr Example",
        "subject":"Check In", "reason_for_conversation":"Without opportunity reference",
        "type_of_contact":"In Person Meeting",
        "reason_for_contact":"(New-) Product Presentation",
        "product_level_3":"210 General Lab consumables",
        "sales_territory":"Demo Territory", "start_date":"2026-10-08",
        "start_time":"09:00", "end_date":"2026-10-08", "end_time":"09:30"
    }
    request = Request(url+"/save",data=json.dumps(obj).encode(),
                      headers={"Content-Type":"application/json"})
    with pytest.raises(HTTPError) as error:
        urlopen(request)
    assert error.value.code == 400
