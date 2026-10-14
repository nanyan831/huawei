import logging
import re
import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-HistoryGuide-Request-Id"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_logger = logging.getLogger("historyguide.request")


async def attach_request_context(request: Request, call_next: Callable[[Request], Response]) -> Response:
    request_id = _request_id_from_header(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    started_at = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers[REQUEST_ID_HEADER] = request_id
    _logger.info(
        "request completed request_id=%s method=%s path=%s status_code=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        extra={
            "event": "http_request_completed",
            "request_id": request_id,
            "http_method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


def _request_id_from_header(value: str | None) -> str:
    if value and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())
