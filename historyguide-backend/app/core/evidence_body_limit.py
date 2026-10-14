from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


MAX_EVIDENCE_BODY_BYTES = 8 * 1024 * 1024


class EvidenceBodyLimitMiddleware:
    """Bound JSON intake before parsing, including requests without Content-Length."""

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_EVIDENCE_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (scope["type"] != "http" or scope["method"] != "POST"
                or not scope["path"].startswith("/api/evidence/")):
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                response = JSONResponse(
                    {"detail": "Evidence upload exceeds the 8 MiB limit."},
                    status_code=413, headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        delivered = False

        async def buffered_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, buffered_receive, send)
