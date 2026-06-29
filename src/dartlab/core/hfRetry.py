"""HuggingFace HTTP 429/503/504 공용 retry helper (L0).

HF 무료 플랜 commit 한도 128/hour — 초과 시 응답 본문에
`"retry this action in X minutes"` 를 돌려준다. 본문 파싱 우선, Retry-After
헤더 2순위, exponential fallback 3순위로 실제 서버 권장 대기시간을 존중.

옛 ``.github/scripts/_hfRetry.py`` 의 L0 승격본 — 라이브러리 코드(`dartlab.pipeline`
업로드 단계)는 ``.github/`` 밑을 import 할 수 없어 core 로 올린다. 가장 미묘한 보존
포인트는 LFS 멀티스레드 업로드가 transient 실패를 ``RuntimeError`` 로 감싸는 것을
``__cause__``/메시지로 풀어 재시도하는 ``_isRetryable`` 이다.

사용 예::

    from dartlab.core.hfRetry import retryHfCall
    retryHfCall(api.create_commit, repo_id=..., operations=..., ...)
    retryHfCall(api.upload_folder, folder_path=..., ...)
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, Callable

_RETRYABLE_STATUS = {429, 502, 503, 504}  # 502 Bad Gateway 포함 — HF /tree 페이지네이션 등 게이트웨이 transient
_BACKOFF_SECONDS_FALLBACK = (60, 300, 900, 1200)  # 60s + 5m + 15m + 20m = 41m
_MAX_SINGLE_WAIT = 1800  # 한 번 backoff 최대 30분
_RETRY_MIN_RE = re.compile(r"retry this action in (\d+)\s*minutes?", re.IGNORECASE)
_RETRY_SEC_RE = re.compile(r"retry this action in (\d+)\s*seconds?", re.IGNORECASE)
# LFS 멀티스레드 업로드(_upload_lfs_files)는 transient(429/S3/네트워크) 실패를 RuntimeError
# "Error while uploading 'X' to the Hub." 로 감싼다 — HfHubHTTPError 가 아니라 과거 재시도 0번이었다.
# 실제 원인은 __cause__ 또는 메시지로 식별해 동일 백오프로 재시도(create_commit 대량 LFS 배치 강건화).
_TRANSIENT_MSG_RE = re.compile(
    r"error while uploading|timed out|timeout|connection|temporarily|throttl|rate.?limit|too many requests",
    re.IGNORECASE,
)


def _envInt(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _maxSingleWait() -> int:
    return _envInt("DARTLAB_HF_RETRY_MAX_SINGLE_WAIT_SECONDS", _MAX_SINGLE_WAIT, minimum=0)


def _retryAttempts() -> int:
    return _envInt("DARTLAB_HF_RETRY_ATTEMPTS", len(_BACKOFF_SECONDS_FALLBACK) + 1, minimum=1)


def _isRetryable(exc: Exception) -> bool:
    """transient 여부 — HTTP 백오프, HF cache miss, LFS 래핑 RuntimeError."""
    from huggingface_hub.errors import HfHubHTTPError, LocalEntryNotFoundError

    if isinstance(exc, LocalEntryNotFoundError):
        return True
    if isinstance(exc, HfHubHTTPError):
        return getattr(getattr(exc, "response", None), "status_code", None) in _RETRYABLE_STATUS
    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, HfHubHTTPError):
        if getattr(getattr(cause, "response", None), "status_code", None) in _RETRYABLE_STATUS:
            return True
    return bool(_TRANSIENT_MSG_RE.search(str(exc)))


def parseRetryWait(exc: Exception, attempt: int) -> int:
    """HF 응답에서 권장 대기시간 (초) 추출.

    Priority:
        1. response.headers['Retry-After'] (RFC 표준)
        2. 메시지 본문 "retry this action in X minutes/seconds" (HF 관례)
        3. _BACKOFF_SECONDS_FALLBACK[attempt] (고정 fallback)

    Args:
        exc: HF 호출에서 발생한 예외.
        attempt: 0-base 재시도 회차.

    Returns:
        대기 초 (_MAX_SINGLE_WAIT 로 clamp).

    Raises:
        없음.

    Example:
        >>> parseRetryWait(RuntimeError("retry this action in 2 minutes"), 0)
        150
    """
    response = getattr(exc, "response", None)
    if response is not None and hasattr(response, "headers"):
        retryAfter = response.headers.get("Retry-After")
        if retryAfter:
            try:
                return min(int(retryAfter), _maxSingleWait())
            except ValueError:
                pass

    msg = str(exc)
    m = _RETRY_MIN_RE.search(msg)
    if m:
        return min(int(m.group(1)) * 60 + 30, _maxSingleWait())  # +30s 여유
    m = _RETRY_SEC_RE.search(msg)
    if m:
        return min(int(m.group(1)) + 10, _maxSingleWait())

    if attempt < len(_BACKOFF_SECONDS_FALLBACK):
        return min(_BACKOFF_SECONDS_FALLBACK[attempt], _maxSingleWait())
    return min(_BACKOFF_SECONDS_FALLBACK[-1], _maxSingleWait())


def retryHfCall(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """HF API 호출을 transient 백오프로 감싼다.

    재시도 대상: (1) HfHubHTTPError 429/503/504, (2) HF Hub cache/metadata
    전파 타이밍의 LocalEntryNotFoundError, (3) LFS 업로드 래핑 RuntimeError
    ("Error while uploading ...") 처럼 원인이 429 이거나 메시지가 transient 인 경우.
    그 외(인증·400 등 fatal)는 즉시 raise.

    Args:
        fn: api.create_commit · api.upload_file · api.upload_folder 등.
        *args: fn 위치 인자.
        **kwargs: fn 키워드 인자.

    Returns:
        fn 의 정상 반환값.

    Raises:
        Exception: 비-transient 예외 또는 마지막 재시도 실패 시 그대로 전파.

    Example:
        >>> retryHfCall(lambda: 1)
        1
    """
    attempts = _retryAttempts()
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — _isRetryable 가 transient 만 선별, 나머지 즉시 raise
            if not _isRetryable(exc) or attempt == attempts - 1:
                raise
            wait = parseRetryWait(exc, attempt)
            label = getattr(getattr(exc, "response", None), "status_code", None) or type(exc).__name__
            print(
                f"[hfRetry] HF {label} on {fn.__name__} — {wait}s 후 재시도 ({attempt + 1}/{attempts - 1})",
                flush=True,
            )
            time.sleep(wait)
    raise RuntimeError("unreachable")
