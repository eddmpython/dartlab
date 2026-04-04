"""Web/static helpers for the embedded Svelte UI."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# UI 빌드 디렉토리: 환경변수 우선, 없으면 프로젝트 루트/ui/web/build
_UI_DIR = (
    Path(os.environ["DARTLAB_UI_DIR"])
    if os.environ.get("DARTLAB_UI_DIR")
    else Path(__file__).resolve().parents[3] / "ui" / "web" / "build"
)


def register_spa(app: FastAPI) -> None:
    """Svelte SPA 정적 파일 서빙과 fallback 라우트를 등록한다."""
    if _UI_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(_UI_DIR / "assets")), name="assets")
    app.add_api_route("/{path:path}", serve_spa, methods=["GET"])


def serve_spa(path: str = ""):
    """SPA fallback — index.html 반환."""
    if not _UI_DIR.exists():
        return HTMLResponse(
            "<h2>DartLab UI not built</h2><p>Run: <code>cd ui && npm install && npm run build</code></p>",
            status_code=503,
        )

    file = _UI_DIR / path
    if path and file.is_file():
        try:
            file.resolve().relative_to(_UI_DIR.resolve())
        except ValueError:
            return HTMLResponse("Not found", status_code=404)
        return FileResponse(file)

    index = _UI_DIR / "index.html"
    if index.exists():
        return FileResponse(
            index,
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    return HTMLResponse("<h2>index.html not found</h2>", status_code=404)
