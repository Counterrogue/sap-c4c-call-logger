from urllib.request import urlopen,Request
import json
from mock_sap import start_mock_server

def test_mock_save():
    url=start_mock_server()
    obj={"id":"mock-test-123","account":"Demo U","contact":"Dr A","date":"2026-10-08","start_time":"09:00","subject":"Check in","notes":"General discussion/Check in"}
    req=Request(url+"/save",data=json.dumps(obj).encode(),headers={"Content-Type":"application/json"})
    with urlopen(req) as r:
        assert json.load(r)["id"]==obj["id"]
    with urlopen(url+"/records") as r:
        assert obj["id"] in [v["id"] for v in json.load(r)]
