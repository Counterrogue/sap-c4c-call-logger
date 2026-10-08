"""Local simulated C4C activity form. No company systems or SAP access."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

FORM_FIELDS = (
    "account", "primary_contact", "subject", "reason_for_conversation",
    "opportunity", "type_of_contact", "reason_for_contact",
    "product_level_3", "product_level_4", "start_date", "start_time",
    "end_date", "end_time", "organizer", "sales_territory", "notes"
)
REQUIRED = (
    "account", "primary_contact", "subject", "reason_for_conversation",
    "type_of_contact", "reason_for_contact", "product_level_3", "sales_territory",
    "start_date", "start_time", "end_date", "end_time"
)

PAGE = '''<!doctype html>
<html><head><meta charset="utf-8"><title>Local C4C Activity Simulator</title>
<style>body{font:16px system-ui;max-width:820px;margin:2em auto;padding:0 1em;color:#223}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px 25px}label{font-weight:600;display:block}
input,textarea,select{display:block;box-sizing:border-box;width:100%;padding:10px;border:1px solid #bdc9da;
border-radius:6px;margin:6px 0 10px;font:inherit}button{background:#1261a0;color:white;padding:12px 22px;
border:0;border-radius:5px;cursor:pointer}textarea{min-height:110px}.hint{color:#637189}
@media(max-width:650px){.grid{grid-template-columns:1fr}}</style></head>
<body><h2>Local Mock CRM — New Activity</h2>
<p class="hint">Simulated C4C fields. Saving here does NOT contact SAP or submit for approval.</p>
<form id="f"><input type="hidden" id="record_id">
<div class="grid">
<div><label for="account">Account *</label><input id="account" required></div>
<div><label for="primary_contact">Primary Contact *</label><input id="primary_contact" required></div>
<div><label for="subject">Subject *</label><input id="subject" required></div>
<div><label for="reason_for_conversation">Reason for Conversation *</label>
<select id="reason_for_conversation" required><option>Without opportunity reference</option><option>With opportunity reference</option></select></div>
<div><label for="opportunity">Opportunity</label><input id="opportunity"></div>
<div><label for="type_of_contact">Type of contact *</label>
<select id="type_of_contact" required><option>In Person Meeting</option></select></div>
<div><label for="reason_for_contact">Reason for contact *</label>
<select id="reason_for_contact" required><option>(New-) Product Presentation</option></select></div>
<div><label for="product_level_3">Product level 3 *</label>
<select id="product_level_3" required><option>210 General Lab consumables</option></select></div>
<div><label for="product_level_4">Product Level 4</label><input id="product_level_4"></div>
<div><label for="start_date">Start Date</label><input id="start_date" type="date" required></div>
<div><label for="start_time">Start Time</label><input id="start_time" type="time" required></div>
<div><label for="end_date">End Date</label><input id="end_date" type="date" required></div>
<div><label for="end_time">End Time</label><input id="end_time" type="time" required></div>
<div><label for="organizer">Organizer</label><input id="organizer"></div>
<div><label for="sales_territory">Sales Territory *</label><input id="sales_territory" required></div>
</div><label for="notes">Notes</label><textarea id="notes"></textarea>
<button type="submit">Save draft activity</button></form>
<p role="status" aria-live="polite"></p>
<p class="hint">Approval is manual and intentionally not simulated.</p>
<script>
document.querySelector('#f').addEventListener('submit', async e => {
  e.preventDefault(); const data = {id:document.getElementById('record_id').value};
  for(const k of ['account','primary_contact','subject','reason_for_conversation','opportunity',
    'type_of_contact','reason_for_contact','product_level_3','product_level_4','start_date',
    'start_time','end_date','end_time','organizer','sales_territory','notes']) {
    data[k]=document.getElementById(k).value;
  }
  try {
    const r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const j=await r.json();
    document.querySelector('[role="status"]').textContent=r.ok?'Saved: '+j.id:'Error: '+j.error;
  } catch(err) {document.querySelector('[role="status"]').textContent='Error: '+err;}
});
</script></body></html>'''

records = {}
lock = threading.RLock()
server = None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def send_json(self, status, obj):
        raw = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            raw = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif path == "/records":
            with lock:
                self.send_json(200, list(records.values()))
        else:
            self.send_json(404, {"error": "Not found"})
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/reset":
            with lock: records.clear()
            return self.send_json(200, {"ok": True})
        if path != "/save":
            return self.send_json(404, {"error": "Not found"})
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65536:
            return self.send_json(413, {"error": "Invalid request length"})
        try:
            obj = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {"error": "Invalid JSON"})
        if any(not str(obj.get(k, "")).strip() for k in (*REQUIRED, "id")):
            return self.send_json(400, {"error": "Missing required fields"})
        with lock:
            existing = records.get(obj["id"])
            if existing and existing != obj:
                return self.send_json(409, {"error": "Conflicting duplicate record ID"})
            if not existing:
                records[obj["id"]] = obj
        self.send_json(200, {"id": obj["id"], "duplicate": bool(existing)})

def start_mock_server():
    global server
    with lock:
        if server is None:
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}"
