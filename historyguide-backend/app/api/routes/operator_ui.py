from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(include_in_schema=False)
ASSET_ROOT = Path(__file__).resolve().parents[2] / "static" / "operator"
HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    ),
}


@router.get("/operator")
def operator_page() -> FileResponse:
    return FileResponse(ASSET_ROOT / "index.html", media_type="text/html", headers=HEADERS)


@router.get("/operator/app.js")
def operator_script() -> FileResponse:
    return FileResponse(ASSET_ROOT / "app.js", media_type="text/javascript", headers=HEADERS)


@router.get("/operator/styles.css")
def operator_styles() -> FileResponse:
    return FileResponse(ASSET_ROOT / "styles.css", media_type="text/css", headers=HEADERS)
