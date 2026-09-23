"""Local HTTP app for the fictional BBS SG Bank demo site.

Serves the static frontend and a small JSON API over the ledger service.  Uses
only the standard library, binds to localhost by default, and holds no
credentials of any kind: it is a demo, not a banking service.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark  # noqa: E402
import service  # noqa: E402
from service import BankService, LedgerError  # noqa: E402

SITE_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = SITE_ROOT / "frontend"
DEFAULT_PORT = 8770

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
    ".txt": "text/plain; charset=utf-8",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _as_int(value, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError(400, "bad_request", f"expected a whole number, got {value!r}") from None


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "BBSBankDemo/1.0"
    protocol_version = "HTTP/1.1"
    service: BankService

    # --------------------------------------------------------------- plumbing

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/") or "/"
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            if path.startswith("/api/"):
                body = self._read_json() if method == "POST" else {}
                response = self._api(method, path, query, body)
                if isinstance(response, tuple):
                    payload, status = response
                else:
                    payload, status = response, 200
                self._send_json(payload, status=status)
            elif method == "GET":
                self._send_static(path)
            else:
                raise ApiError(405, "method_not_allowed", f"{method} is not supported for {path}")
        except ApiError as exc:
            self._send_json({"error": {"code": exc.code, "message": exc.message}}, status=exc.status)
        except LedgerError as exc:
            self._send_json({"error": {"code": "ledger_error", "message": str(exc)}}, status=exc.status)
        except benchmark.BenchmarkError as exc:
            self._send_json({"error": {"code": "benchmark_error", "message": str(exc)}}, status=exc.status)
        except Exception as exc:  # noqa: BLE001 - the demo should never return a stack trace
            traceback.print_exc()
            self._send_json(
                {"error": {"code": "internal_error", "message": str(exc)}}, status=500
            )

    def _read_json(self) -> dict:
        length = _as_int(self.headers.get("Content-Length"), 0)
        if length <= 0:
            return {}
        if length > 2_000_000:
            raise ApiError(413, "payload_too_large", "request body is too large")
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(400, "invalid_json", f"request body is not valid JSON: {exc}") from None
        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            raise ApiError(400, "invalid_json", "request body must be a JSON object")
        return parsed

    # ------------------------------------------------------------------- API

    def _api(self, method: str, path: str, query: dict, body: dict):
        svc = self.service

        if method == "GET" and path == "/api/health":
            return {"status": "ok", "fictional": True}

        if method == "GET" and path == "/api/meta":
            return {
                "name": "BBS SG Bank",
                "tagline": "Fictional legacy-batch modernisation demo",
                "fictional": True,
                "disclaimer": (
                    "BBS SG Bank is not a real institution. Everything here is synthetic: no real customers, "
                    "accounts, balances, credentials or personal data are used or transmitted anywhere, and all "
                    "transactions are invented."
                ),
                "currency": service.CURRENCY,
                "engine": {
                    "modern": "modern/bank.py (unmodified batch engine)",
                    "legacy": "legacy/bank.cob (mock COBOL nightly batch)",
                    "benchmark_harness": "scripts/benchmark.py",
                },
                "endpoints": [
                    "GET /api/health",
                    "GET /api/meta",
                    "GET /api/summary",
                    "GET /api/accounts",
                    "GET /api/accounts/{id}",
                    "GET /api/audit?limit=&status=&kind=",
                    "GET /api/benchmark?accounts=&operations=&fresh=1",
                    "GET /api/legacy/source",
                    "POST /api/operations",
                    "POST /api/batch",
                    "POST /api/reset",
                ],
            }

        if method == "GET" and path == "/api/summary":
            return svc.summary()

        if method == "GET" and path == "/api/accounts":
            term = (query.get("q") or "").strip().lower()
            accounts = svc.accounts_view()
            if term:
                accounts = [
                    account
                    for account in accounts
                    if term in account["id"].lower() or term in account["name"].lower()
                ]
            return {"accounts": accounts, "count": len(accounts), "currency": service.CURRENCY}

        if method == "GET" and path.startswith("/api/accounts/"):
            account_id = unquote(path.rsplit("/", 1)[-1])
            detail = svc.account_detail(account_id)
            if not detail:
                raise ApiError(404, "not_found", f"no demo account {account_id!r}")
            return detail

        if method == "GET" and path == "/api/audit":
            limit = max(1, min(_as_int(query.get("limit"), 100), 1000))
            status = query.get("status") or None
            kind = query.get("kind") or None
            if status and status not in {"posted", "rejected"}:
                raise ApiError(400, "bad_request", "status must be 'posted' or 'rejected'")
            if kind and kind not in service.KIND_LABELS:
                raise ApiError(400, "bad_request", "kind must be one of D, W, T")
            entries = svc.audit_view(limit=limit, status=status, kind=kind)
            return {"entries": entries, "count": len(entries), "fictional": True}

        if method == "GET" and path == "/api/legacy/source":
            return service.legacy_source_excerpt()

        if method == "GET" and path == "/api/benchmark":
            accounts = _as_int(query.get("accounts"), benchmark.DEFAULT_ACCOUNTS)
            operations = _as_int(query.get("operations"), benchmark.DEFAULT_OPERATIONS)
            repeats = _as_int(query.get("repeats"), benchmark.DEFAULT_REPEATS)
            fresh = query.get("fresh") in {"1", "true", "yes"}
            return benchmark.run_benchmark(accounts, operations, repeats=repeats, fresh=fresh)

        if method == "POST" and path == "/api/operations":
            operations = body.get("operations")
            if operations is None:
                operations = [body.get("operation") or body]
            batch = svc.process(operations, channel=str(body.get("channel") or "site.ui"))
            posted = [op for op in batch["operations"] if op["status"] == "posted"]
            failed = [op for op in batch["operations"] if op["status"] == "rejected"]
            # A rejection is a business outcome, not a transport failure: the row was
            # understood, judged and recorded. 201 only when something was posted.
            status = 201 if posted else 200
            return {"result": batch, "posted": len(posted), "rejected": len(failed)}, status

        if method == "POST" and path == "/api/batch":
            batch = svc.demo_batch(
                _as_int(body.get("operations"), 60),
                include_edge_cases=bool(body.get("include_edge_cases", True)),
                seed=_as_int(body.get("seed"), service.DEMO_SEED),
                max_amount_cents=_as_int(body.get("max_amount_cents"), 25_000),
            )
            return {"result": batch}

        if method == "POST" and path == "/api/reset":
            return {"summary": svc.reset(), "message": "Demo ledger restored to its seeded state."}

        raise ApiError(404, "not_found", f"unknown endpoint {method} {path}")

    # ------------------------------------------------------------ responses

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path: str) -> None:
        relative = "index.html" if path == "/" else unquote(path.lstrip("/"))
        candidate = (FRONTEND_DIR / relative).resolve()
        try:
            candidate.relative_to(FRONTEND_DIR.resolve())
        except ValueError:
            raise ApiError(403, "forbidden", "path escapes the frontend directory") from None
        if not candidate.is_file():
            raise ApiError(404, "not_found", f"no such asset {relative}")
        content_type = CONTENT_TYPES.get(candidate.suffix.lower(), "application/octet-stream")
        body = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:  # keep the console readable
        message = fmt % args if args else fmt
        if "/api/" in message:
            sys.stderr.write("  %s %s\n" % (self.log_date_time_string(), message))


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def build_server(
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    bank: BankService | None = None,
    attempts: int = 12,
) -> DemoServer:
    """Bind the demo server, stepping past ports already in use on this machine."""
    last_error: OSError | None = None
    for offset in range(attempts):
        try:
            server = DemoServer((host, port + offset), DemoHandler)
            break
        except OSError as exc:  # port taken (or unavailable) - try the next one
            last_error = exc
    else:
        raise last_error if last_error else OSError("could not bind a port")
    server.service = bank or BankService()  # type: ignore[attr-defined]
    DemoHandler.service = server.service  # type: ignore[assignment]
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the fictional BBS SG Bank demo site.")
    parser.add_argument("--host", default="127.0.0.1", help="interface to bind (default: localhost only)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default: {DEFAULT_PORT}, 0 picks a free one)")
    parser.add_argument("--open", action="store_true", help="open the site in a browser once it is up")
    args = parser.parse_args()

    server = build_server(args.host, args.port)
    port = server.server_address[1]
    url = f"http://{args.host}:{port}/"
    banner = [
        "BBS SG Bank - fictional demo site",
        "  Fictional only: no real bank, customers, credentials or customer data.",
        f"  Modern engine : {service.MODERN_DIR / 'bank.py'}",
        f"  Legacy mock   : {service.LEGACY_SOURCE}",
        "  GnuCOBOL      : "
        + (
            "available (legacy timings can be measured)"
            if benchmark.environment()["legacy_measurable"]
            else "not found (legacy timings will be reported as unavailable; run scripts/get_cobc.sh to enable)"
        ),
        "  Tests         : cd site && python3 -m unittest discover -s tests",
        f"  Serving       : {url}",
        "  Stop with Ctrl+C",
    ]
    if port != args.port:
        banner.insert(1, f"  Note          : port {args.port} was busy, using {port} instead.")
    for line in banner:
        print(line, flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server.", flush=True)
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
