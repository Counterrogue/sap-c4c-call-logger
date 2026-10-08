from urllib.request import urlopen, Request
import json
from datetime import date, time
from core import make_bulk_calls
from mock_sap import start_mock_server

def test_mock_save_and_readback():
    url = start_mock_server()
    call = make_bulk_calls([{"contact":"Dr A"}],date(2026,10,8),time(9,0),
                           "Demo University", organizer="Demo Organizer",
                           sales_territory="Demo Territory")[0]
    obj = {"id":call.id, **call.sap_fields()}
    request = Request(url+"/save",data=json.dumps(obj).encode(),
                      headers={"Content-Type":"application/json"})
    with urlopen(request) as response:
        assert json.load(response)["id"] == obj["id"]
    with urlopen(url+"/records") as response:
        stored = {entry["id"]:entry for entry in json.load(response)}
    assert stored[call.id] == obj
