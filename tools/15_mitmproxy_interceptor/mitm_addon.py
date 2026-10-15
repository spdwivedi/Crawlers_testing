"""
tools/15_mitmproxy_interceptor/mitm_addon.py
============================================
Mitmproxy addon that intercepts HTTP/HTTPS requests and responses,
extracting wire headers, timings, payloads, and API signatures into JSONL.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any
from mitmproxy import http


class FlowInterceptorAddon:
    def __init__(self):
        self.output_file = os.environ.get("MITM_FLOWS_JSONL", "intercepted_flows.jsonl")

    def response(self, flow: http.HTTPFlow) -> None:
        if not flow.response or not flow.request:
            return

        req = flow.request
        resp = flow.response

        content_type = resp.headers.get("content-type", "")
        body_preview = ""
        is_textual = any(t in content_type.lower() for t in ["json", "text", "javascript", "xml", "html", "application/x-mpegurl"])

        if is_textual:
            try:
                body_preview = resp.get_text()[:3000]
            except Exception:
                body_preview = "<text-decode-error>"
        else:
            body_preview = f"<binary {len(resp.content)} bytes>"

        dur_ms = 0.0
        if resp.timestamp_end and req.timestamp_start:
            dur_ms = round((resp.timestamp_end - req.timestamp_start) * 1000, 2)

        entry = {
            "timestamp": req.timestamp_start,
            "duration_ms": dur_ms,
            "request": {
                "url": req.url,
                "method": req.method,
                "scheme": req.scheme,
                "host": req.host,
                "port": req.port,
                "path": req.path,
                "headers": dict(req.headers),
            },
            "response": {
                "status_code": resp.status_code,
                "reason": resp.reason,
                "headers": dict(resp.headers),
                "content_type": content_type,
                "content_length": len(resp.content),
                "body_preview": body_preview,
            },
        }

        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            sys.stderr.write(f"[FlowInterceptorAddon] Error logging flow: {e}\n")


addons = [FlowInterceptorAddon()]
