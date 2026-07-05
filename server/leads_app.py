#!/usr/bin/env python3
"""Holographic Memory — leads service.

Receives partnership/demo form submissions and stores them in SQLite; serves a
password-protected admin page to review them. Standard library only.

Config via env:
  HOLO_DB          path to SQLite db (default /var/lib/holo-leads/leads.db)
  HOLO_ADMIN_USER  admin username (default "admin")
  HOLO_ADMIN_PASS  admin password (required for /admin)
  HOLO_PORT        listen port (default 8787), bound to 127.0.0.1 (behind nginx)
"""
from __future__ import annotations

import base64
import html
import json
import os
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.getenv("HOLO_DB", "/var/lib/holo-leads/leads.db")
ADMIN_USER = os.getenv("HOLO_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("HOLO_ADMIN_PASS", "")
PORT = int(os.getenv("HOLO_PORT", "8787"))
MAX_BODY = 64 * 1024
FIELDS = ("name", "contact", "company", "type", "message")


def init_db() -> None:
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS leads(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER, name TEXT, contact TEXT, company TEXT,
                type TEXT, message TEXT, ip TEXT, ua TEXT)"""
        )


def save_lead(data: dict, ip: str, ua: str) -> int:
    with sqlite3.connect(DB) as c:
        cur = c.execute(
            "INSERT INTO leads(ts,name,contact,company,type,message,ip,ua) VALUES(?,?,?,?,?,?,?,?)",
            (int(time.time()), data.get("name", ""), data.get("contact", ""),
             data.get("company", ""), data.get("type", ""), data.get("message", ""), ip, ua),
        )
        return cur.lastrowid


def all_leads() -> list[sqlite3.Row]:
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        return list(c.execute("SELECT * FROM leads ORDER BY id DESC"))


def check_auth(header: str | None) -> bool:
    if not ADMIN_PASS or not header or not header.startswith("Basic "):
        return False
    try:
        user, _, pw = base64.b64decode(header[6:]).decode("utf-8").partition(":")
    except Exception:
        return False
    return user == ADMIN_USER and pw == ADMIN_PASS


def admin_html() -> str:
    rows = all_leads()
    trs = []
    for r in rows:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["ts"]))
        trs.append(
            "<tr>"
            f"<td class=num>{r['id']}</td><td>{when}</td>"
            f"<td>{html.escape(r['name'] or '')}</td>"
            f"<td>{html.escape(r['contact'] or '')}</td>"
            f"<td>{html.escape(r['company'] or '')}</td>"
            f"<td><span class=tag>{html.escape(r['type'] or '')}</span></td>"
            f"<td class=msg>{html.escape(r['message'] or '')}</td>"
            f"<td class=ip>{html.escape(r['ip'] or '')}</td>"
            "</tr>"
        )
    body = "".join(trs) or "<tr><td colspan=8 class=empty>No leads yet.</td></tr>"
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Leads · Holographic Memory</title>
<style>
:root{{--p:#5b6cff;--p2:#8b5bff;--cy:#3fe0d0;--ink:#171a2b;--muted:#85868a;--line:#eef0f4}}
*{{box-sizing:border-box}}body{{margin:0;font-family:'Fira Sans',system-ui,sans-serif;background:#0b0e26;color:#eef0ff}}
header{{display:flex;align-items:center;gap:10px;padding:16px 22px}}
.dot{{width:22px;height:22px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,var(--cy) 22%,var(--p) 55%,var(--p2));box-shadow:0 0 18px rgba(91,108,255,.7)}}
h1{{font-size:18px;margin:0;font-weight:700}}.count{{margin-left:auto;color:var(--muted);font-size:14px}}
.wrap{{padding:0 22px 40px}}
.card{{background:#fff;color:var(--ink);border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.4);overflow:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px;min-width:900px}}
th,td{{padding:11px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#f6f7fb;font-weight:700;position:sticky;top:0}}
.num,.ip{{color:var(--muted);font-variant-numeric:tabular-nums}}.ip{{font-size:12px}}
.tag{{background:rgba(91,108,255,.12);color:var(--p);font-weight:600;font-size:12px;padding:3px 9px;border-radius:999px}}
.msg{{max-width:340px;white-space:pre-wrap}}.empty{{text-align:center;color:var(--muted);padding:26px}}
</style></head><body>
<header><span class=dot></span><h1>Leads — Holographic Memory</h1><span class=count>{len(rows)} total</span></header>
<div class=wrap><div class=card><table>
<thead><tr><th>#</th><th>When</th><th>Name</th><th>Contact</th><th>Company</th><th>Type</th><th>Message</th><th>IP</th></tr></thead>
<tbody>{body}</tbody></table></div></div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "holo-leads/1.0"

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _client_ip(self) -> str:
        return self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()

    def do_POST(self):
        if self.path.rstrip("/") != "/api/leads":
            return self._send(404, b'{"error":"not found"}')
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0 or n > MAX_BODY:
                return self._send(413, b'{"error":"too large"}')
            data = json.loads(self.rfile.read(n))
        except Exception:
            return self._send(400, b'{"error":"bad json"}')
        clean = {k: str(data.get(k, ""))[:4000] for k in FIELDS}
        if not clean["name"].strip() or not clean["contact"].strip():
            return self._send(422, b'{"error":"name and contact required"}')
        lid = save_lead(clean, self._client_ip(), self.headers.get("User-Agent", "")[:400])
        self._send(200, json.dumps({"ok": True, "id": lid}).encode())

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("/admin", "/api/leads"):
            if not check_auth(self.headers.get("Authorization")):
                return self._send(401, b"auth required", "text/plain",
                                  {"WWW-Authenticate": 'Basic realm="Holo Leads"'})
            if path == "/admin":
                return self._send(200, admin_html().encode(), "text/html; charset=utf-8")
            return self._send(200, json.dumps([dict(r) for r in all_leads()]).encode())
        if path in ("/api/health", "/health"):
            return self._send(200, b'{"ok":true}')
        self._send(404, b'{"error":"not found"}')

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    init_db()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
