"""DartLab Tunnel Security — 극강 보안 모듈.

dartlab share 실행 시에만 활성화되는 보안 레이어:
- 2-Layer 토큰 인증 (full + readonly)
- 엔드포인트 화이트리스트
- Rate limiting (슬라이딩 윈도우)
- 감사 로그 (구조화 JSONL)
- 자동 만료 Kill Switch
- 이상 탐지
- 입력 검증
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. 엔드포인트 화이트리스트 — 가장 중요한 방어선
# ---------------------------------------------------------------------------

# 터널 모드에서 허용되는 경로 패턴 (정규식)
_WHITELIST_PATTERNS: list[re.Pattern[str]] = [
    # 상태/검색/스펙
    re.compile(r"^/api/status$"),
    re.compile(r"^/api/search$"),
    re.compile(r"^/api/spec$"),
    re.compile(r"^/api/data/stats$"),
    # 회사 데이터 (GET)
    re.compile(r"^/api/company/[A-Za-z0-9]+$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/(index|sections|toc|init|modules)$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/viewer/[a-zA-Z][a-zA-Z0-9_]*$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/show/[a-zA-Z][a-zA-Z0-9_]*(/all)?$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/trace/[a-zA-Z][a-zA-Z0-9_]*$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/diff(/matrix)?$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/diff/[a-zA-Z][a-zA-Z0-9_]*(/summary)?$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/bridge/[a-zA-Z][a-zA-Z0-9_]*$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/topics/graph$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/search$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/searchIndex$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/insights(/unified)?$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/scan/(management|financial|position)$"),
    re.compile(r"^/api/company/[A-Za-z0-9]+/summary/[a-zA-Z][a-zA-Z0-9_]*$"),
    re.compile(r"^/api/data/sources/[A-Za-z0-9]+$"),
    re.compile(r"^/api/data/preview/[A-Za-z0-9]+/[a-zA-Z][a-zA-Z0-9_]*$"),
    # AI 프로필 (GET — SPA 초기 로딩용, secrets 제외)
    re.compile(r"^/api/ai/profile$"),
    # AI 질문 (POST — full-access 토큰만)
    re.compile(r"^/api/ask$"),
    # 뷰어 배치 (POST)
    re.compile(r"^/api/company/[A-Za-z0-9]+/viewer/batch$"),
]

# POST 허용 경로 (full-access 토큰 필수)
_POST_WHITELIST: set[str] = {"/api/ask"}
_POST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^/api/company/[A-Za-z0-9]+/viewer/batch$"),
]


def _is_whitelisted(path: str) -> bool:
    return any(p.match(path) for p in _WHITELIST_PATTERNS)


def _is_post_allowed(path: str) -> bool:
    if path in _POST_WHITELIST:
        return True
    return any(p.match(path) for p in _POST_PATTERNS)


# ---------------------------------------------------------------------------
# 2. 토큰 관리
# ---------------------------------------------------------------------------


class TokenManager:
    """2-Layer 토큰 생성/검증."""

    def __init__(self, token: str | None = None):
        self.full_token = token or secrets.token_urlsafe(32)
        self.readonly_token = self._derive_readonly(self.full_token)

    @staticmethod
    def _derive_readonly(full_token: str) -> str:
        return hmac.new(full_token.encode(), b"readonly", hashlib.sha256).hexdigest()[:43]

    def validate(self, token: str) -> str | None:
        """토큰 검증. "full" | "readonly" | None 반환."""
        if hmac.compare_digest(token, self.full_token):
            return "full"
        if hmac.compare_digest(token, self.readonly_token):
            return "readonly"
        return None

    def token_hash(self, token: str) -> str:
        """감사 로그용 — 토큰 원본 노출 방지."""
        return hashlib.sha256(token.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# 3. Kill Switch + TTL
# ---------------------------------------------------------------------------


class TunnelKillSwitch:
    """자동 만료 + 긴급 차단."""

    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.start_time = time.monotonic()
        self.active = True

    def check(self) -> bool:
        if not self.active:
            return False
        if time.monotonic() - self.start_time > self.ttl:
            self.active = False
            logger.warning("[SECURITY] 터널 TTL 만료 — 자동 차단")
            return False
        return True

    def kill(self, reason: str = "manual") -> None:
        self.active = False
        logger.warning("[SECURITY] Kill Switch 발동 — 사유: %s", reason)

    @property
    def remaining(self) -> int:
        return max(0, int(self.ttl - (time.monotonic() - self.start_time)))


# ---------------------------------------------------------------------------
# 4. Rate Limiter (슬라이딩 윈도우)
# ---------------------------------------------------------------------------


class SlidingWindowLimiter:
    """경로 카테고리별 슬라이딩 윈도우 Rate Limiter."""

    LIMITS: dict[str, tuple[int, int]] = {
        "ask": (10, 60),  # 10회/분 — LLM 비용
        "company": (30, 60),  # 30회/분 — Polars 메모리
        "search": (60, 60),  # 60회/분 — 가벼움
        "global": (100, 60),  # 전체 100회/분
    }

    MAX_CONCURRENT_SSE = 3

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._sse_count = 0

    def _classify(self, path: str) -> str:
        if "/ask" in path or "/summary/" in path:
            return "ask"
        if "/company/" in path:
            return "company"
        return "search"

    def _clean(self, window: list[float], now: float, period: int) -> list[float]:
        cutoff = now - period
        return [t for t in window if t > cutoff]

    def check(self, path: str) -> bool:
        """요청 허용 여부. False면 429 반환해야 함."""
        now = time.monotonic()
        category = self._classify(path)

        # 카테고리별 제한
        limit, period = self.LIMITS.get(category, (60, 60))
        key = category
        self._windows[key] = self._clean(self._windows[key], now, period)
        if len(self._windows[key]) >= limit:
            return False
        self._windows[key].append(now)

        # 글로벌 제한
        g_limit, g_period = self.LIMITS["global"]
        self._windows["global"] = self._clean(self._windows["global"], now, g_period)
        if len(self._windows["global"]) >= g_limit:
            return False
        self._windows["global"].append(now)

        return True

    def sse_acquire(self) -> bool:
        if self._sse_count >= self.MAX_CONCURRENT_SSE:
            return False
        self._sse_count += 1
        return True

    def sse_release(self) -> None:
        self._sse_count = max(0, self._sse_count - 1)


# ---------------------------------------------------------------------------
# 5. 이상 탐지
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """간단한 휴리스틱 이상 탐지."""

    def __init__(self, kill_switch: TunnelKillSwitch):
        self._kill_switch = kill_switch
        self._recent_requests: list[float] = []
        self._recent_codes: list[str] = []
        self._error_window: list[tuple[float, bool]] = []  # (time, is_error)

    def record(self, path: str, status: int) -> None:
        now = time.monotonic()

        # burst 감지: 10초 내 20+ 요청
        self._recent_requests.append(now)
        self._recent_requests = [t for t in self._recent_requests if now - t < 10]
        if len(self._recent_requests) > 20:
            logger.warning("[SECURITY] Burst 감지 — 10초 내 %d 요청", len(self._recent_requests))

        # 스크래핑 감지: 1분 내 10+ 고유 종목코드
        import re as _re

        code_match = _re.search(r"/company/([A-Za-z0-9]+)", path)
        if code_match:
            self._recent_codes.append(code_match.group(1))
            cutoff = now - 60
            # time tracking이 없으므로 최근 60개만 유지
            if len(self._recent_codes) > 60:
                self._recent_codes = self._recent_codes[-60:]
            unique = len(set(self._recent_codes[-30:]))
            if unique > 10:
                logger.warning("[SECURITY] 스크래핑 의심 — 1분 내 %d개 종목 접근", unique)
                self._kill_switch.kill("scraping_detected")

        # 에러율 감지: 5분 내 50%+ 에러
        is_error = status >= 400
        self._error_window.append((now, is_error))
        self._error_window = [(t, e) for t, e in self._error_window if now - t < 300]
        if len(self._error_window) > 20:
            error_rate = sum(1 for _, e in self._error_window if e) / len(self._error_window)
            if error_rate > 0.5:
                logger.warning(
                    "[SECURITY] 높은 에러율 — %.0f%% (%d/%d)",
                    error_rate * 100,
                    sum(1 for _, e in self._error_window if e),
                    len(self._error_window),
                )
                self._kill_switch.kill("high_error_rate")


# ---------------------------------------------------------------------------
# 6. 감사 로그
# ---------------------------------------------------------------------------

_AUDIT_LOG_PATH: Path | None = None


def _init_audit_log() -> Path:
    global _AUDIT_LOG_PATH  # noqa: PLW0603
    if _AUDIT_LOG_PATH is not None:
        return _AUDIT_LOG_PATH

    env = os.environ.get("DARTLAB_AUDIT_LOG")
    if env:
        _AUDIT_LOG_PATH = Path(env).expanduser()
    else:
        _AUDIT_LOG_PATH = Path.home() / ".dartlab" / "audit.jsonl"

    _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _AUDIT_LOG_PATH


def _write_audit(entry: dict[str, Any]) -> None:
    try:
        path = _init_audit_log()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass  # 로그 실패가 서비스를 멈추면 안 됨


# ---------------------------------------------------------------------------
# 7. 입력 검증
# ---------------------------------------------------------------------------

_STOCK_CODE_RE = re.compile(r"^[A-Za-z0-9]{4,10}$")
_TOPIC_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,50}$")
_PRIVATE_IP_RE = re.compile(
    r"^https?://(10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+|127\.\d+\.\d+\.\d+|0\.0\.0\.0|localhost|\[::1\])"
)
# Ollama 기본 포트는 허용
_OLLAMA_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1):11434")


def validate_stock_code(code: str) -> bool:
    return bool(_STOCK_CODE_RE.match(code))


def validate_topic(topic: str) -> bool:
    return bool(_TOPIC_RE.match(topic))


def validate_base_url(url: str) -> bool:
    """base_url SSRF 방지. Ollama 로컬은 허용."""
    if _OLLAMA_RE.match(url):
        return True
    if _PRIVATE_IP_RE.match(url):
        return False
    return True


# ---------------------------------------------------------------------------
# 8. 통합 미들웨어
# ---------------------------------------------------------------------------


class TunnelSecurityMiddleware(BaseHTTPMiddleware):
    """터널 모드 보안 미들웨어 — 모든 보안 기능을 하나로 통합."""

    def __init__(self, app, *, token_manager: TokenManager, kill_switch: TunnelKillSwitch):
        super().__init__(app)
        self.token_manager = token_manager
        self.kill_switch = kill_switch
        self.rate_limiter = SlidingWindowLimiter()
        self.anomaly_detector = AnomalyDetector(kill_switch)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # OPTIONS는 CORS preflight — 통과
        if method == "OPTIONS":
            return await call_next(request)

        # 정적 파일 (SPA 에셋) — 토큰 없이 허용
        if not path.startswith("/api/"):
            return await call_next(request)

        # --- Kill Switch ---
        if not self.kill_switch.check():
            return JSONResponse(
                {"error": "터널 세션이 만료되었습니다. 서버를 재시작하세요."},
                status_code=401,
            )

        # --- 토큰 인증 ---
        token = self._extract_token(request)
        if not token:
            return JSONResponse({"error": "인증 토큰이 필요합니다."}, status_code=401)

        access_level = self.token_manager.validate(token)
        if access_level is None:
            return JSONResponse({"error": "유효하지 않은 토큰입니다."}, status_code=401)

        # --- 화이트리스트 ---
        if not _is_whitelisted(path):
            return JSONResponse(
                {"error": "이 엔드포인트는 터널 모드에서 접근할 수 없습니다."},
                status_code=403,
            )

        # --- Readonly 토큰의 POST 차단 ---
        if method == "POST" and access_level == "readonly":
            return JSONResponse(
                {"error": "읽기 전용 토큰으로는 이 작업을 수행할 수 없습니다."},
                status_code=403,
            )

        # --- Rate Limiting ---
        if not self.rate_limiter.check(path):
            return JSONResponse(
                {"error": "요청 횟수 제한을 초과했습니다. 잠시 후 다시 시도하세요."},
                status_code=429,
            )

        # --- 요청 처리 ---
        start = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        # --- 감사 로그 ---
        _write_audit(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "method": method,
                "path": path,
                "token_hash": self.token_manager.token_hash(token),
                "access": access_level,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "ip": request.client.host if request.client else "unknown",
            }
        )

        # --- 이상 탐지 ---
        self.anomaly_detector.record(path, response.status_code)

        return response

    @staticmethod
    def _extract_token(request: Request) -> str | None:
        # Authorization 헤더 우선
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        # SSE용 쿼리 파라미터 fallback
        return request.query_params.get("token")


# ---------------------------------------------------------------------------
# 9. 헬퍼 — 서버 초기화에서 사용
# ---------------------------------------------------------------------------


def is_tunnel_mode() -> bool:
    return os.environ.get("DARTLAB_TUNNEL") == "1"


def create_security_components(
    token: str | None = None,
    ttl: int = 3600,
) -> tuple[TokenManager, TunnelKillSwitch, TunnelSecurityMiddleware | None]:
    """보안 컴포넌트 생성. 터널 모드가 아니면 (None, None, None) 반환."""
    if not is_tunnel_mode():
        return None, None, None  # type: ignore[return-value]

    token_manager = TokenManager(token)
    kill_switch = TunnelKillSwitch(ttl)
    # 미들웨어는 app에 추가할 때 생성
    return token_manager, kill_switch, None
