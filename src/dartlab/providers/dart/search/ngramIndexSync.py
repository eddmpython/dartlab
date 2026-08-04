"""ngramIndex HF Hub 동기화 — ngramIndex.py 분할 (규칙 3 LoC).

`ngramIndex.py` 862 LoC 가 규칙 3 임계 (>800) 위반. push / pull / iter helper
(~120 줄) 를 본 모듈로 분리. 호출자 호환 — ngramIndex.py 재내보내기.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.logger import getLogger

_log = getLogger(__name__)


def _stemIndexDir() -> Path:
    d = Path(_cfg.dataDir) / DATA_RELEASES["stemIndex"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def pushStemIndex(*, token: str | None = None) -> str:
    """stemIndex를 HuggingFace에 업로드.

    Args:
        token: 인자.

    Raises:
        없음.

    Example:
        >>> pushStemIndex(...)

    Returns:
        str — 결과 문자열.
    """
    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import HF_REPO

    outDir = _stemIndexDir()
    hfDir = DATA_RELEASES["stemIndex"]["dir"]

    api = HfApi(token=token)
    api.upload_folder(
        repo_id=HF_REPO,
        folder_path=str(outDir),
        path_in_repo=hfDir,
        repo_type="dataset",
    )

    url = f"https://huggingface.co/datasets/{HF_REPO}/tree/main/{hfDir}"
    _log.info(f"[stemIndex] HF 업로드 완료: {url}")
    return url


# stemIndex freshness 재확인 간격. 로컬 npz 존재 시 pull 자체가 스킵되어
# HF 재빌드를 영구히 못 따라가던 결함의 수리 지점. 마커 mtime = 마지막 동기화.
_STEM_REFRESH_TTL_HOURS = 12
_STEM_RECHECK_SECONDS = 900.0
_stemResyncCheckedAt: dict[str, float] = {}


def _stemRefreshDue(outDir: Path) -> bool:
    """로컬 stemIndex 의 TTL 재동기화 필요 여부 (env·memo·마커 게이트)."""
    import os
    import time

    if os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        return False
    if os.environ.get("DARTLAB_NO_REFRESH") == "1":
        return False
    last = _stemResyncCheckedAt.get("stem")
    now = time.monotonic()
    if last is not None and now - last < _STEM_RECHECK_SECONDS:
        return False
    marker = outDir / ".hfSyncedAt"
    try:
        if time.time() - marker.stat().st_mtime < _STEM_REFRESH_TTL_HOURS * 3600:
            return False
    except OSError:
        pass  # 마커 없음: 구세대 로컬. 재동기화 필요.
    _stemResyncCheckedAt["stem"] = now
    return True


def _touchStemSyncMarker(outDir: Path) -> None:
    """동기화 성공 시각 마커 갱신 (실패해도 다음 TTL 재확인으로 자연 복구)."""
    try:
        outDir.mkdir(parents=True, exist_ok=True)
        (outDir / ".hfSyncedAt").touch()
    except OSError:
        pass


def pullStemIndex(*, token: str | None = None, force: bool = False) -> Path:
    """HuggingFace에서 stemIndex 다운로드 → 즉시 검색 가능.

    로컬 인덱스가 있어도 TTL(12h) 게이트 후 증분 재동기화한다 (HF 재빌드 추적).
    재동기화 실패는 로컬 유지로 강등한다.

    Args:
        token: HF 토큰 (private repo 접근 시).
        force: True 면 로컬 존재·TTL 무시하고 즉시 pull.

    Raises:
        OSError, RuntimeError, ValueError: 최초 조달(로컬 부재) 다운로드 실패 시.

    Example:
        >>> pullStemIndex(...)

    Returns:
        Path: 저장 경로.
    """
    from huggingface_hub import snapshot_download

    from dartlab.core.dataConfig import HF_REPO
    from dartlab.core.messaging import emit

    outDir = _stemIndexDir()
    hfDir = DATA_RELEASES["stemIndex"]["dir"]

    refreshing = False
    if not force:
        npzPath = outDir / "stemIndex.npz"
        if npzPath.exists():
            from dartlab.providers.dart.search.ngramIndex import ngramStats as _ngramStats

            stats = _ngramStats()
            if stats["documents"] > 0:
                if not _stemRefreshDue(outDir):
                    emit("stemindex:local", path=str(outDir))
                    return outDir
                # TTL 만료: 아래 pull 로 증분 재동기화. 실패는 로컬 유지로 강등.
                refreshing = True

    emit("stemindex:hf_start", repo=HF_REPO)
    _log.info("[cyan]⬇ HF[/] stemIndex (%s/%s)", HF_REPO, hfDir)
    try:
        from dartlab.core.hfRetry import retryHfCall

        retryHfCall(  # HF read SSOT(core.hfRetry): 429/503/504 단일 백오프
            snapshot_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            allow_patterns=f"{hfDir}/**",
            local_dir=str(outDir.parent.parent.parent),
            token=token,
        )
    except (OSError, RuntimeError, ValueError) as e:
        emit("stemindex:hf_fail", error=str(e))
        if refreshing:
            _log.warning("stemIndex 재동기화 실패. 로컬 인덱스 유지: %s", e)
            return outDir
        _log.warning("[red]✗[/] stemIndex 다운로드 실패: %s", e)
        raise
    _touchStemSyncMarker(outDir)
    _log.info("[green]✓[/] stemIndex 다운로드 완료")

    global _cachedIndex, _cachedMeta
    _cachedIndex = None
    _cachedMeta = None

    from dartlab.providers.dart.search.ngramIndex import ngramStats as _ngramStats

    stats = _ngramStats()
    sizeStr = f"{stats['sizeMb']}MB ({stats['documents']:,}문서)"
    emit("stemindex:hf_done", sizeStr=sizeStr)
    return outDir


def iterNgram(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    limit: int = 10,
):
    """``searchNgram`` 의 iterator pair (룰 10).

    Args:
        query: 자연어 쿼리.
        corpCode: corp_code 필터.
        stockCode: 종목코드 필터.
        limit: 반환 건수.

    Yields:
        검색 결과 row dict.

    Example:
        >>> for row in iterNgram("유상증자", limit=5):
        ...     print(row.get("rcept_no"))

    Raises:
        없음.
    """
    from dartlab.providers.dart.search.ngramIndex import searchNgram

    df = searchNgram(query, corpCode=corpCode, stockCode=stockCode, limit=limit)
    if df is None or df.is_empty():
        return
    yield from df.iter_rows(named=True)
