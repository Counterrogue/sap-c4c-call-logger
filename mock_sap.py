"""Local simulated CRM; no SAP connection."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

PAGE='''<!doctype html><html><head><meta charset="utf-8"><title>Mock CRM</title>
<style>body{font:16px system-ui;max-width:550px;margin:3em auto;color:#223}input,textarea{display:block;width:100%;box-sizing:border-box;padding:9px;margin:6px 0 15px;border:1px solid #bbb;border-radius:5px}button{padding:10px;background:#0b5cab;color:white;border:0;border-radius:5px}label{font-weight:bold}</style></head>
<body><h2>Mock CRM — New Phone Call</h2><p>Local simulator only. No SAP connection.</p><form id="f">
<input id="record_id" type="hidden">
<label>Account</label><input id="account" required>
<label>Contact</label><input id="contact" required>
<label>Date</label><input id="date" type="date" required>
<label>Start Time</label><input id="start_time" type="time" required>
<label>Subject</label><input id="subject" required>
<label>Notes</label><textarea id="notes" required></textarea>
<label>Next steps</label><textarea id="next_steps"></textarea>
<button type="submit">Save</button></form><p role="status"></p>
<script>document.querySelector('#f').addEventListener('submit',async e=>{
e.preventDefault();let data={};
for(const k of ['record_id','account','contact','date','start_time','subject','notes','next_steps']){data[k==='record_id'?'id':k]=document.getElementById(k).value;}
let r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let j=await r.json();
document.querySelector('[role="status"]').textContent=r.ok?'Saved: '+j.id:'Error: '+j.error;
});</script></body></html>'''
records={}
lock=threading.RLock()
server=None
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_json(self,status,obj):
        raw=json.dumps(obj).encode()
        self.send_response(status);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if urlparse(self.path).path=="/":
            raw=PAGE.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
        elif urlparse(self.path).path=="/records":
            with lock:self.send_json(200,list(records.values()))
        else:self.send_json(404,{"error":"Not found"})
    def do_POST(self):
        if urlparse(self.path).path=="/reset":
            with lock: records.clear()
            return self.send_json(200,{"ok":True})
        if urlparse(self.path).path!="/save":return self.send_json(404,{"error":"Not found"})
        length=int(self.headers.get("Content-Length","0"))
        if length<=0 or length>65536:return self.send_json(413,{"error":"Invalid request length"})
        try: obj=json.loads(self.rfile.read(length))
        except (ValueError,UnicodeDecodeError):return self.send_json(400,{"error":"Invalid JSON"})
        required=["id","account","contact","date","start_time","subject","notes"]
        if any(not str(obj.get(k,"")).strip() for k in required):return self.send_json(400,{"error":"Missing required fields"})
        with lock:
            duplicate=obj["id"] in records
            if not duplicate:records[obj["id"]]=obj
        self.send_json(200,{"id":obj["id"],"duplicate":duplicate})
def start_mock_server():
    global server
    with lock:
        if server is None:
            server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}"
