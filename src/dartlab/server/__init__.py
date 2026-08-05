"""DartLab Web Server: FastAPI + SSE 스트리밍.

dartlab ai 명령으로 실행:
    dartlab ai              # http://localhost:8400
    dartlab ai --port 9000  # 커스텀 포트
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import dartlab
from dartlab.ai.trace import installProgressCapture
from dartlab.core.logger import getLogger as _bootstrapLogger

from .api import (
    agent_router,
    ai_router,
    analysis_router,
    ask_router,
    company_router,
    dart_router,
    data_router,
    dataHub_router,
    dl_router,
    macro_router,
    price_events_router,
    room_router,
    runtime_router,
    uiQa_router,
)
from .embed import router as embed_router
from .runtime import ensurePort, runServer  # noqa: F401, re-exported
from .security import AdminBoundaryMiddleware, RequestBudgetMiddleware
from .web import registerSpa

logger = logging.getLogger(__name__)


async def _prewarmVizCatalog() -> None:
    """viz catalog cold import (quant/finance/portfolio... 8 도메인) 을 startup 으로 흡수.

    `/api/viz/layout/quant/{stockCode}` 첫 호출 시 dartlab.viz.catalog import chain
    이 ~30s + 가 걸려 frontend useQuery timeout → 퀀트 탭 스피너 무한. background
    thread 로 미리 import 시켜두면 사용자 첫 화면 진입 시 import cache hit.
    """
    try:
        await asyncio.to_thread(lambda: __import__("dartlab.viz.layout", fromlist=["planTabLayout"]))
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        logger.debug("viz catalog prewarm 실패", exc_info=exc)


async def _prewarmRuntimeCenter() -> None:
    """Runtime Center 가 쓸 CLI 실측을 사용자 진입 전에 시작한다.

    Runtime Center 는 제품의 현관문이라 서버가 뜨면 곧 조회된다. 첫 조회 때 비로소
    엔진을 만들고 probe 를 예약하면 그 비용을 사용자가 화면 앞에서 기다린다(실측
    2026-08-05: 차가운 서버 첫 호출 432ms, 정착 후 15~33ms). 부팅 때 비차단 스냅샷을
    한 번 떠 두면 같은 실측이 사용자가 앱을 여는 동안 끝난다. 기다리지 않으므로
    서버 기동을 늦추지 않는다.
    """
    try:
        from dartlab.ai.runtime import getRuntimeEngine

        await asyncio.to_thread(lambda: getRuntimeEngine().status(refresh=False, blocking=False))
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        logger.debug("Runtime Center prewarm 실패", exc_info=exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """앱 수명주기 관리 -- 데이터 시각화 prewarm, 런타임과 룸 생성/정리."""
    _doPrewarm = os.environ.get("DARTLAB_PREWARM", "").strip().lower() in {"1", "true", "yes"}
    viz_prewarm_task = asyncio.create_task(_prewarmVizCatalog()) if _doPrewarm else None
    # 제품 서버로 뜬 실행만 CLI 를 미리 두드린다. 테스트 클라이언트는 표식이 없어 건드리지 않는다.
    runtime_prewarm_task = (
        asyncio.create_task(_prewarmRuntimeCenter()) if os.environ.get("DARTLAB_SERVER_ENTRY") == "1" else None
    )

    # 채널 모드: 협업 룸 자동 생성 + 백그라운드 정리
    from .room import roomManager

    if os.environ.get("DARTLAB_CHANNEL") == "1":
        roomManager.createRoom()
        roomManager.startBackgroundCleanup()

    try:
        yield
    finally:
        from .services.channelRuntime import channelRuntime
        from .services.devChannelRuntime import devChannelRuntime

        devChannelRuntime.shutdown()
        channelRuntime.shutdownAll()
        roomManager.stopBackgroundCleanup()
        roomManager.destroyRoom()
        from dartlab.ai.runtime import getRuntimeEngine

        getRuntimeEngine().close()
        for task in (viz_prewarm_task, runtime_prewarm_task):
            if task is not None and not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError):
                if task is not None:
                    await task


# dartlab logger 초기화 후 tool 진행 라인을 SSE 로 흘리기 위한 capture 설치.
# idempotent. 여러 worker / reload 시 안전.
_bootstrapLogger()
installProgressCapture()

app = FastAPI(title="DartLab", version=dartlab.__version__, lifespan=lifespan)


def _corsOrigins() -> list[str]:
    raw = os.environ.get("DARTLAB_CORS_ORIGINS")
    if raw:
        raw = raw.strip()
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]
    # 터널과 배포 UI도 같은 서버 origin을 쓰므로 CORS wildcard가 필요하지 않다.
    # 분리 배포한 frontend만 DARTLAB_CORS_ORIGINS로 정확한 origin을 명시한다.
    return [
        "http://127.0.0.1:8400",
        "http://localhost:8400",
        "http://127.0.0.1:5400",
        "http://localhost:5400",
    ]


class _SecurityHeadersMiddleware:
    """보안 헤더 (X-Content-Type-Options 등) 를 모든 응답에 부착.

    회귀 가드: 옛 BaseHTTPMiddleware 구현이 StreamingResponse 의 chunk 를 buffer
    → /api/viz/layout-stream NDJSON 첫 chunk 가 *모든* 카드 build 완료 후 도착
    → 사용자 화면 cold start 1~3 분 무한 spinner. pure ASGI 로 재작성. http.response.start
    message 만 가로채 헤더 추가, body chunk 는 그대로 통과 (streaming 보존).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                _existing = {k.lower() for k, _ in headers}
                for k, v in (
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                ):
                    if k not in _existing:
                        headers.append((k, v))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, _send)


app.add_middleware(_SecurityHeadersMiddleware)
app.add_middleware(RequestBudgetMiddleware)
app.add_middleware(AdminBoundaryMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

_origins = _corsOrigins()
if _origins == ["*"]:
    logger.warning("CORS allow_origins='*'. 프로덕션에서는 명시적 origin을 설정하세요")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Room-Member", "X-Tunnel-Skip-AntiPhishing-Page-Redirect", "*"],
)

app.include_router(ai_router)
app.include_router(agent_router)
app.include_router(analysis_router)
app.include_router(ask_router)
app.include_router(company_router)
app.include_router(data_router)
app.include_router(dataHub_router)
app.include_router(dl_router)
app.include_router(macro_router)
app.include_router(price_events_router)
app.include_router(room_router)
app.include_router(runtime_router)
app.include_router(uiQa_router)
app.include_router(dart_router)
app.include_router(embed_router)

# ── MCP SSE 마운트 (HF Spaces 또는 명시적 활성화 시) ──
if os.environ.get("SPACE_ID") or os.environ.get("DARTLAB_MCP_HTTP") == "1":
    try:
        from dartlab.mcp import createSseApp

        _mcp_sse = createSseApp()
        app.mount("/mcp", _mcp_sse)
        logger.info("MCP SSE 엔드포인트 활성화: /mcp/sse")
    except ImportError:
        logger.info("MCP SDK 미설치. MCP SSE 비활성")

registerSpa(app)
