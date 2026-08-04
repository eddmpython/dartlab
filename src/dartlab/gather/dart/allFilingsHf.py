"""allFilings HF 폴백 상태·오류 타입과 재동기화 게이트.

`allFilingsCollector` 의 HF 관심사 분할 모듈 (룰 3 LoC 분할). 조달 로직
(`_ensureFromHf`)과 저장 경로(`_allFilingsDir`)는 collector 소유이므로 DI 로
주입받는다 (collector 상향 import 금지: cycle 없는 단방향 유지).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


class HfFallbackStatus(str, Enum):
    """allFilings HF fallback의 정상 결과."""

    LOCAL = "local"
    DOWNLOADED = "downloaded"
    NOT_FOUND = "not_found"


class AllFilingsHfError(RuntimeError):
    """allFilings HF fallback 기반 오류."""

    def __init__(self, message: str, *, period: str | None) -> None:
        self.period = period
        super().__init__(message)


class AllFilingsHfUnavailableError(AllFilingsHfError):
    """HF fallback을 현재 실행 환경에서 사용할 수 없음."""


class AllFilingsHfDownloadError(AllFilingsHfError):
    """HF fallback 원격 조회·다운로드가 실패함."""


class AllFilingsHfListingError(AllFilingsHfError):
    """HF 원격 artifact 목록 조회가 실패함."""


class AllFilingsHfUploadError(AllFilingsHfError):
    """HF artifact 업로드가 일부 또는 전부 실패함."""

    def __init__(self, message: str, *, uploadedFiles: int, totalFiles: int) -> None:
        self.uploadedFiles = uploadedFiles
        self.totalFiles = totalFiles
        super().__init__(message, period=None)


# HF 재동기화 TTL. allFilings 는 HF 에 매일(당일분은 장중 증분) 갱신되므로 존재
# 확인만으로 끝내면 로컬이 영구 stale 로 굳는다. 마커 파일 mtime 이 마지막 성공 시각.
_RESYNC_TTL_HOURS = 12
_RESYNC_RECHECK_SECONDS = 900.0  # 프로세스 내 재시도 간격 (오프라인 반복 지연 방지)
_resyncCheckedAt: dict[str, float] = {}


def _maybeResyncFromHf(
    period: str | None,
    *,
    ensureFromHf: Callable[..., object],
    allFilingsDir: Callable[[], Path],
) -> None:
    """로컬 artifact 존재 시 TTL 게이트 후 HF 재동기화 (신규 일자·증분 catch-up).

    조달이 아니라 갱신이므로 모든 실패는 로컬 유지로 강등한다. `DARTLAB_NO_HF_DOWNLOAD`
    ·`DARTLAB_NO_REFRESH` 존중. snapshot_download 는 변경분만 받아 증분으로 동작한다.

    Args:
        period: 특정 일자(YYYYMMDD) 또는 None(디렉토리 전체).
        ensureFromHf: collector `_ensureFromHf` (refresh 키워드 지원) DI 주입.
        allFilingsDir: collector `_allFilingsDir` DI 주입.
    """
    import os
    import time

    if os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        return
    if os.environ.get("DARTLAB_NO_REFRESH") == "1":
        return
    key = period or "_ALL_"
    last = _resyncCheckedAt.get(key)
    now = time.monotonic()
    if last is not None and now - last < _RESYNC_RECHECK_SECONDS:
        return
    marker = allFilingsDir() / f".hfSynced_{key}"
    try:
        if time.time() - marker.stat().st_mtime < _RESYNC_TTL_HOURS * 3600:
            return
    except OSError:
        pass  # 마커 없음: 구세대 로컬. 재동기화 필요.
    _resyncCheckedAt[key] = now
    try:
        ensureFromHf(period, refresh=True)
    except Exception as exc:  # noqa: BLE001 - 갱신 실패는 로컬 유지 (조달 계약과 다름)
        _log.warning("allFilings HF 재동기화 실패. 로컬 유지 (%s): %s", key, exc)
        return
    marker.touch()
