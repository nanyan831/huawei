"""Exercise a migrated loopback instance without using the configured database."""

from __future__ import annotations

import json
import os
from pathlib import Path
from contextlib import contextmanager
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
HTTP = build_opener(ProxyHandler({}))


@contextmanager
def _isolated_directory():
    directory = Path(tempfile.mkdtemp(prefix="historyguide-runtime-smoke-")).resolve()
    if directory.parent != Path(tempfile.gettempdir()).resolve() or not directory.name.startswith(
        "historyguide-runtime-smoke-"
    ):
        raise RuntimeError("temporary smoke directory is outside the expected parent")
    try:
        yield directory
    finally:
        for attempt in range(15):
            try:
                shutil.rmtree(directory)
                break
            except PermissionError:
                if attempt == 14:
                    raise
                time.sleep(0.2)


def _isolated_env(database_path: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("HISTORYGUIDE_")}
    env.update({
        "HISTORYGUIDE_DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
        "HISTORYGUIDE_SCHEMA_MODE": "migrated",
        "HISTORYGUIDE_API_KEY": secrets.token_urlsafe(32),
        "HISTORYGUIDE_OPERATOR_API_KEY": secrets.token_urlsafe(32),
        "HISTORYGUIDE_VISITOR_SIGNING_KEY": secrets.token_urlsafe(32),
        "HISTORYGUIDE_VISITOR_GATEWAY_ENABLED": "true",
        "HISTORYGUIDE_LOG_LEVEL": "WARNING",
    })
    return env


def _available_loopback_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(
    base_url: str, path: str, *, method: str = "GET",
    payload: dict | None = None, headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        base_url + path, data=body, method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with HTTP.open(request, timeout=2) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, json.load(exc)


def _expect_status(actual: int, expected: int, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected HTTP {expected}, got {actual}")


def run_smoke() -> None:
    with _isolated_directory() as directory:
        env = _isolated_env(directory / "staging.db")
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        port = _available_loopback_port()
        base_url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise RuntimeError("isolated server stopped before readiness")
                try:
                    status, _ = _request(base_url, "/ready")
                    if status == 200:
                        break
                except (URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("isolated server did not become ready")
                time.sleep(0.1)

            _expect_status(_request(base_url, "/openapi-genios-answers.json")[0], 200, "answer-tool schema")
            _expect_status(_request(base_url, "/openapi-genios-sources.json")[0], 200, "source-search schema")
            state_payload = {
                "session_id": "isolated-smoke-session", "visitor_type": "tourist",
                "current_exhibit": None, "visited_history": [], "interest": [], "remaining_time": 20,
            }
            _expect_status(
                _request(base_url, "/api/visitor-states", method="POST", payload=state_payload)[0],
                401, "business route without key",
            )
            business_headers = {"X-HistoryGuide-Api-Key": env["HISTORYGUIDE_API_KEY"]}
            search_payload = {"keywords": ["南开"]}
            _expect_status(
                _request(base_url, "/api/genios/sources/search", method="POST", payload=search_payload)[0],
                401, "approved-source search without key",
            )
            status, search = _request(
                base_url, "/api/genios/sources/search", method="POST",
                payload=search_payload, headers=business_headers,
            )
            _expect_status(status, 200, "approved-source search on empty staging database")
            if search.get("matches") != []:
                raise RuntimeError("empty staging database returned historical source matches")
            _expect_status(
                _request(base_url, "/api/visitor-states", method="POST", payload=state_payload,
                         headers=business_headers)[0],
                201, "create visitor session",
            )
            status, grant = _request(
                base_url, "/api/visitor/grants", method="POST",
                payload={"session_id": state_payload["session_id"]}, headers=business_headers,
            )
            _expect_status(status, 201, "grant visitor token")
            visitor_headers = {"Authorization": f"Bearer {grant['access_token']}"}
            _expect_status(_request(base_url, "/api/visitor/me", headers=visitor_headers)[0], 200, "visitor read")
            status, revoked = _request(
                base_url, "/api/visitor/grants/revoke", method="POST",
                payload={"session_id": state_payload["session_id"]}, headers=business_headers,
            )
            _expect_status(status, 200, "revoke visitor session")
            if revoked.get("revoked_count") != 1:
                raise RuntimeError("revoke visitor session did not affect exactly one grant")
            _expect_status(
                _request(base_url, "/api/visitor/me", headers=visitor_headers)[0],
                401, "revoked visitor token",
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    run_smoke()
    print("Isolated migrated runtime smoke passed; temporary database and keys were removed.")
