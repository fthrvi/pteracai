#!/usr/bin/env python3
"""PteracAI local server.

Serves the SPA from static/ and exposes a tiny file-bridge API so the
browser can ask Claude Code (running in the terminal) for follow-up
questions and grading.

Endpoints:
    GET  /                      -> static/index.html
    GET  /static/<path>         -> static asset
    GET  /data/bank.json        -> seed question bank
    POST /api/request           -> append a request to data/requests.jsonl
    GET  /api/responses?since=N -> return responses with id > N
    POST /api/attempt           -> append an attempt to data/attempts.jsonl
"""
from __future__ import annotations

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
STATIC = PUBLIC / "static"
INDEX = PUBLIC / "index.html"
BANK_FILE = PUBLIC / "data" / "bank.json"
DATA = ROOT / "data"
REQUESTS_FILE = DATA / "requests.jsonl"
RESPONSES_FILE = DATA / "responses.jsonl"
ATTEMPTS_FILE = DATA / "attempts.jsonl"

for f in (REQUESTS_FILE, RESPONSES_FILE, ATTEMPTS_FILE):
    f.touch(exist_ok=True)


def _read_jsonl(path: Path) -> list[dict]:
    out = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _append_jsonl(path: Path, obj: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(obj) + "\n")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter logs
        return

    def _json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path
        if path == "/" or path == "/index.html":
            self._file(INDEX, "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            sub = path[len("/static/"):]
            ext = sub.rsplit(".", 1)[-1].lower()
            ct = {
                "js": "application/javascript",
                "css": "text/css",
                "html": "text/html; charset=utf-8",
                "json": "application/json",
                "svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")
            self._file(STATIC / sub, ct)
        elif path == "/data/bank.json":
            self._file(BANK_FILE, "application/json")
        elif path == "/api/responses":
            since = int(parse_qs(url.query).get("since", ["0"])[0])
            responses = [r for r in _read_jsonl(RESPONSES_FILE) if r.get("seq", 0) > since]
            self._json(200, {"responses": responses})
        elif path == "/api/requests":
            # debugging convenience
            self._json(200, {"requests": _read_jsonl(REQUESTS_FILE)})
        else:
            self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        if url.path == "/api/request":
            req = {
                "id": str(uuid.uuid4())[:8],
                "ts": time.time(),
                "status": "pending",
                **payload,
            }
            _append_jsonl(REQUESTS_FILE, req)
            self._json(200, {"ok": True, "id": req["id"]})
        elif url.path == "/api/attempt":
            attempt = {"ts": time.time(), **payload}
            _append_jsonl(ATTEMPTS_FILE, attempt)
            self._json(200, {"ok": True})
        else:
            self.send_error(404)


def main(port: int = 5173) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"PteracAI running at http://127.0.0.1:{port}")
    print("Tell Claude Code in your terminal: 'process pending pterac requests'")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
    main(port)
