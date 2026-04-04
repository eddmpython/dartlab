"""DartLab Embed — embed.js 서빙.

외부 사이트에서 <script src="host/embed.js" data-code="005930"> 로 임베드.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

router = APIRouter()

_EMBED_PATH = Path(__file__).resolve().parents[3] / "ui" / "web" / "build" / "embed.js"


@router.get("/embed.js")
def serve_embed():
    """위젯 JS 번들 — CORS 전체 허용, 1시간 캐시."""
    if not _EMBED_PATH.exists():
        return PlainTextResponse(
            "console.warn('[DartLab] embed.js not built. Run: cd ui && npm run build:widget');",
            media_type="application/javascript",
            status_code=200,
        )
    return FileResponse(
        _EMBED_PATH,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )
