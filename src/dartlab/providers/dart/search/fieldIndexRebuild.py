"""fieldIndex content 인덱스 빌드/배포 — fieldIndex.py 분할 (룰 3 LoC).

`fieldIndex.py` 824 LoC 가 룰 3 임계 (>800) 위반. rebuildMain / rebuildDelta /
pushContentIndex / pullContentIndex / _clearDelta (~360 줄) 를 본 모듈로 분리.
caller compat — fieldIndex.py 가 re-export.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import time
from pathlib import Path

import numpy as np
import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.logger import getLogger
from dartlab.providers.dart.search.freshness import DEFAULT_DATE_COLUMNS, firstSearchDate, periodToDataAsOf

# content_raw(DART XML/HTML) → 검색용 평문. 색인 토큰화엔 정밀 파서(BeautifulSoup, XML당 ~100ms)가
# 불필요·과부하 — regex tag-strip 으로 222파일/수억 토큰 빌드시간을 시간→분 단위로 단축.
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# style/script 는 태그만 걷으면 CSS 규칙·JS 본문이 평문에 남는다(".xforms { font-family... }" 류
# 색인·스니펫 노이즈) — 블록 *내용째* 제거.
_BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)


def _stripTags(raw: str, *, limit: int) -> str:
    """XML/HTML 태그 제거(style/script 는 내용째) + entity unescape + 공백 정규화 → 검색용 평문."""
    if not raw:
        return ""
    raw = raw[: limit * 6]  # 태그 제거 전 과대 입력 캡 (regex 비용 가드)
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html.unescape(_BLOCK_RE.sub(" ", raw)))).strip()[:limit]


# fieldIndex ↔ fieldIndexRebuild 양방향 import 회피 — 함수 본문 lazy import.
# fieldIndex.py 가 본 모듈의 rebuildMain / rebuildDelta 외 7 항목을 re-export 하므로
# module-level `from fieldIndex import ...` 시 direct import 가 partially initialized
# 로 실패. fieldIndex 항목 (CONTENT_LIMIT · _contentIndexDir · _getSegments ·
# _IncrementalBuilder · buildContentSegment · clearCache · loadSegment · writeSegmentCompanions ·
# searchContent) 사용은 모두 함수 본문 안 → 각 함수 시작 lazy import.

_log = getLogger(__name__)

EVIDENCE_TEXT_LIMIT = 4000
EDGAR_DATE_COLUMNS: tuple[str, ...] = DEFAULT_DATE_COLUMNS


def rebuildMain(
    *,
    includeAllFilings: bool = True,
    includePanel: bool = True,
    includeEdgarPanel: bool = False,
    includeNews: bool = False,
    contentLimit: int | None = None,
    panelLimit: int = 4000,
    newsLimit: int = 800,
    tier: str = "full",
    sinceDate: str | None = None,
    whitelist: set[str] | list[str] | None = None,
    showProgress: bool = True,
) -> int:
    """main 세그먼트 풀리빌드 — panel + allFilings (+ 옵션 EDGAR panel).

    스트리밍 빌드: 파일 단위로 읽고 즉시 빌더에 feed 후 해제 (메모리 안전).
    시간 오래 걸림 (4M 문서 기준 약 18분). 월 1회 실행 권장.

    includePanel=True 면 "완전한 DART 문서" 색인: panel 정규화 본문을 filing(rceptNo) 단위로 롤업해
    1 문서로 추가하고, 같은 rceptNo 의 allFilings 원문은 skip (panel 본문 우선). 표시 메타(corp_name/
    report_nm/rcept_dt)는 allFilings 메타 dict 에서 채운다.

    배포 tier — ``tier="full"`` 은 flat ``contentIndex/`` 에 전량(기존 동작). ``tier="lite"`` 는
    ``contentIndex/lite/`` 에 ``sinceDate``(rcept_dt 하한)·``whitelist``(종목코드 한정)로 축소 색인
    → pip 사용자 기본 다운로드(경량). 둘은 별 디렉터리라 공존(상호 무효화 0).

    Args:
        includeAllFilings: True 면 전체 공시 (수시 포함).
        includePanel: True 면 panel 정규화 본문을 filing 롤업으로 추가.
        includeEdgarPanel: True 면 EDGAR panel(미국, 동일 16-col 스키마)도 filing 롤업으로 추가.
            full tier 전용 권장(lite 는 DART 날짜 prune 의미라 기본 제외).
        includeNews: True 면 뉴스 헤드라인 포함.
        contentLimit: allFilings 본문 최대 문자 수.
        panelLimit: panel filing 롤업 본문 최대 문자 수.
        newsLimit: 뉴스 본문 최대 문자 수.
        tier: ``"full"`` (flat 전량) / ``"lite"`` (서브디렉터리 축소). 출력 경로 결정.
        sinceDate: lite 색인 rcept_dt 하한 (YYYYMMDD). None 이면 무제한.
        whitelist: lite 색인에 포함할 종목코드 집합. None 이면 전체.
        showProgress: True 면 progress 로그.

    Returns:
        int — 인덱스 빌드 건수.

    Raises:
        없음 (파일별 read 오류는 skip).

    Example:
        >>> rebuildMain(includePanel=True)  # doctest: +SKIP
        >>> rebuildMain(tier="lite", sinceDate="20241201", whitelist={"005930"})  # doctest: +SKIP
    """
    import gc

    from dartlab.core.dartClient import allFilingsDir as _allFilingsDir
    from dartlab.core.dartClient import allFilingsMetaSuffix

    _META_SUFFIX = allFilingsMetaSuffix()
    from dartlab.providers.dart.search.fieldIndex import (
        CONTENT_LIMIT,
        _contentIndexDir,
        _IncrementalBuilder,
        clearCache,
    )

    if whitelist is not None and not isinstance(whitelist, set):
        whitelist = set(whitelist)
    saveDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)

    if contentLimit is None:
        contentLimit = CONTENT_LIMIT
    builder = _IncrementalBuilder()
    metaRecs: list[dict] = []
    totalDocs = 0

    # panel 통합 시 allFilings 메타(content_raw 제외 경량)를 먼저 dict 로 — panel 롤업 문서의 표시 메타 보강용.
    afMeta: dict[str, dict] = {}
    panelRcepts: set[str] = set()
    if includePanel and includeAllFilings:
        afMeta = _buildAfMeta(showProgress=showProgress)

    # allFilings 는 content_raw (DART XML/HTML 태그 보존) — regex tag-strip 으로 평문화 (빌드시간 가드).
    def feedDf(df: pl.DataFrame, source: str, *, contentColumn: str, skipRcepts: set[str] | None = None) -> int:
        """parquet DataFrame 의 각 row 를 builder 에 추가 + meta record 동행 — 빌드 건수 반환.

        Args:
            df: parquet DataFrame.
            source: 인덱스 라벨 (예 ``"main"`` / ``"delta"``).
            contentColumn: 본문 컬럼명. ``"content_raw"`` 이면 regex tag-strip 평문화,
                그 외 컬럼은 이미 평문화된 텍스트로 보고 그대로 사용.

        Returns:
            추가된 doc 수.

        Raises:
            없음.

        Example:
            >>> feedDf(df, "allFilings", contentColumn="content_raw")  # doctest: +SKIP
        """
        added = 0
        for row in df.iter_rows(named=True):
            if skipRcepts and (row.get("rcept_no") or "") in skipRcepts:
                continue
            # 컬럼키 정규화 — allFilings 는 rcept_dt/report_nm 를 쓰되, 과거 합성 fixture 호환을 위해
            # rcept_date/report_type 도 coalesce 한다.
            rdt = str(row.get("rcept_dt") or row.get("rcept_date") or "")
            rnm = row.get("report_nm") or row.get("report_type") or ""
            # lite tier 축소 — 종목 whitelist / rcept_dt 하한.
            if whitelist is not None and (row.get("stock_code") or "") not in whitelist:
                continue
            if sinceDate and rdt < sinceDate:
                continue
            raw = row.get(contentColumn) or ""
            if contentColumn == "content_raw":
                content = _stripTags(raw, limit=contentLimit)
            else:
                content = raw[:contentLimit]
            builder.addDoc(content)
            metaRecs.append(  # noqa: F821
                {
                    "rcept_no": row.get("rcept_no") or "",
                    "section_order": int(row.get("section_order") or 0),
                    "corp_code": row.get("corp_code") or "",
                    "corp_name": row.get("corp_name") or "",
                    "stock_code": row.get("stock_code") or "",
                    "rcept_dt": rdt,
                    "report_nm": rnm,
                    "section_title": row.get("section_title") or "",
                    "text": content[:500],
                    "evidenceText": content[:EVIDENCE_TEXT_LIMIT],
                    "source": source,
                    "sourceDataAsOf": row.get("sourceDataAsOf") or row.get("source_data_as_of") or rdt,
                    "contentLen": len(content),
                    "url": "",  # 공시는 빈값 — dartUrl 은 rcept_no 로 조합
                }
            )
            added += 1
        return added

    t0 = time.perf_counter()

    if includePanel:
        totalDocs += _feedPanelRollup(
            builder, metaRecs, afMeta, panelRcepts, panelLimit, showProgress, whitelist=whitelist, sinceDate=sinceDate
        )
        if showProgress:
            _log.info(f"[main] panel 롤업 완료: {len(panelRcepts):,} filing, {time.perf_counter() - t0:.0f}초")

    if includeEdgarPanel:
        edgarRcepts: set[str] = set()  # accession — allFilings(rcept_no) 와 충돌 없음, skip 셋 분리
        totalDocs += _feedPanelRollup(
            builder,
            metaRecs,
            {},
            edgarRcepts,
            panelLimit,
            showProgress,
            whitelist=whitelist,
            base=_edgarPanelDir(),
            source="edgar-panel",
            market="us",
        )
        if showProgress:
            _log.info(f"[main] EDGAR panel 롤업 완료: {len(edgarRcepts):,} filing, {time.perf_counter() - t0:.0f}초")

    if includeNews:
        totalDocs += _feedNews(builder, metaRecs, newsLimit, showProgress, sinceDate=sinceDate)

    if includeAllFilings:
        import os

        afDir = _allFilingsDir()
        files = sorted(f for f in afDir.glob("*.parquet") if _META_SUFFIX not in f.stem)
        if sinceDate:  # lite — 일자 sharded(YYYYMMDD.parquet) 파일 레벨 하한 prune
            files = [f for f in files if f.stem >= sinceDate]
        _afl = int(os.environ.get("DARTLAB_SEARCH_AF_FILES", "0"))  # 테스트용 제한(0=무제한)
        if _afl > 0:
            files = files[-_afl:]
        if showProgress:
            _log.info(f"[main] allFilings 스트리밍: {len(files)}개 파일 (panel skip {len(panelRcepts):,})")
        for i, f in enumerate(files):
            try:
                df = pl.read_parquet(f).filter(pl.col("fetch_status") == "ok")
            except (pl.exceptions.PolarsError, OSError):
                continue
            totalDocs += feedDf(df, "allFilings", contentColumn="content_raw", skipRcepts=panelRcepts)
            del df
            if (i + 1) % 50 == 0:
                gc.collect()
                if showProgress:
                    elapsed = time.perf_counter() - t0
                    _log.info(f"  allFilings {i + 1}/{len(files)}: {totalDocs:,} 문서, {elapsed:.0f}초")

    if showProgress:
        _log.info(f"[main] 축적 완료: {totalDocs:,} 문서, finalize 시작")

    idx = builder.finalize()
    meta = pl.DataFrame(metaRecs)
    del metaRecs
    gc.collect()

    saveSegmentWithSidecar(idx, meta, "main", saveDir)
    clearCache()
    writeIndexManifest(saveDir, tier=tier, buildCommand="rebuildMain")

    if showProgress:
        elapsed = time.perf_counter() - t0
        _log.info(f"[main] 저장 완료(tier={tier}, {saveDir.name}). 총 {elapsed / 60:.1f}분, {idx['nDocs']:,} 문서.")

    return idx["nDocs"]


def rebuildMainFromCatalog(
    catalogRows: pl.DataFrame,
    *,
    tier: str = "full",
    showProgress: bool = True,
) -> int:
    """main 세그먼트를 source catalog snapshot 에서 빌드한다.

    Args:
        catalogRows: Source manifest snapshot 에서 합쳐진 catalog rows.
        tier: ``"full"`` 또는 ``"lite"`` 출력 tier.
        showProgress: True 면 progress 로그.

    Returns:
        int — 인덱스 빌드 건수.

    Raises:
        OSError: 세그먼트 파일을 저장할 수 없을 때.

    Example:
        >>> callable(rebuildMainFromCatalog)
        True
    """
    import gc

    from dartlab.providers.dart.search.fieldIndex import (
        CONTENT_LIMIT,
        _contentIndexDir,
        _IncrementalBuilder,
        clearCache,
    )

    saveDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    builder = _IncrementalBuilder()
    metaRecs: list[dict] = []
    for row in catalogRows.iter_rows(named=True):
        if bool(row.get("deleted")):
            continue
        content = str(row.get("searchText") or "")[:CONTENT_LIMIT]
        builder.addDoc(content)
        source = str(row.get("source") or "")
        metaRecs.append(
            {
                "docKey": str(row.get("docKey") or ""),
                "rcept_no": str(row.get("rceptNo") or row.get("sourceRef") or ""),
                "section_order": int(row.get("sectionOrder") or 0),
                "corp_code": str(row.get("corpCode") or ""),
                "corp_name": str(row.get("companyName") or ""),
                "stock_code": str(row.get("stockCode") or row.get("ticker") or ""),
                "rcept_dt": str(row.get("date") or ""),
                "report_nm": str(row.get("reportName") or ""),
                "section_title": str(row.get("title") or row.get("sectionKey") or ""),
                "text": content[:500],
                "evidenceText": str(row.get("searchText") or "")[:EVIDENCE_TEXT_LIMIT],
                "source": _runtimeSourceFromCatalog(source),
                "sourceRef": str(row.get("sourceRef") or ""),
                "sourceDataAsOf": str(row.get("sourceDataAsOf") or row.get("date") or ""),
                "contentLen": len(content),
                "url": str(row.get("url") or "") if source == "newsPublic" else "",
                "deleted": False,
            }
        )
    if not metaRecs:
        writeIndexManifest(saveDir, tier=tier, buildCommand="rebuildMain.catalog.empty")
        return 0
    idx = builder.finalize()
    meta = pl.DataFrame(metaRecs)
    saveSegmentWithSidecar(idx, meta, "main", saveDir)
    writeIndexManifest(saveDir, tier=tier, buildCommand="rebuildMain.catalog")
    clearCache()
    del metaRecs, meta
    gc.collect()
    return idx["nDocs"]


def rebuildDeltaFromCatalog(
    deltaRows: pl.DataFrame,
    *,
    tier: str = "full",
) -> int:
    """main 기준 누적 변경분을 단일 delta 세그먼트로 다시 쓴다.

    deltaRows는 월간 main snapshot과 현재 catalog의 차이다. 일별 delta를 계속 쌓지 않고
    매 실행마다 작은 누적 L0 하나로 교체하므로 세그먼트 수와 검색 fan-out이 고정된다.
    삭제 행도 빈 문서 tombstone으로 보존해 main의 이전 문서를 가린다.

    Args:
        deltaRows: main 기준 신규, 변경, 삭제 tombstone 행.
        tier: full 또는 lite 출력 tier.

    Returns:
        작성한 delta 문서와 tombstone 수.

    Raises:
        OSError: 세그먼트 파일을 쓸 수 없을 때.

    Example:
        >>> callable(rebuildDeltaFromCatalog)
        True
    """
    import gc

    from dartlab.providers.dart.search.fieldIndex import (
        CONTENT_LIMIT,
        _contentIndexDir,
        _IncrementalBuilder,
        clearCache,
    )

    saveDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    _removeSegmentArtifacts(saveDir, "delta")
    if deltaRows.is_empty():
        clearCache()
        return 0

    builder = _IncrementalBuilder()
    metaRecs: list[dict] = []
    for row in deltaRows.iter_rows(named=True):
        deleted = bool(row.get("deleted"))
        content = "" if deleted else str(row.get("section_content") or row.get("searchText") or "")[:CONTENT_LIMIT]
        builder.addDoc(content)
        metaRecs.append(
            {
                "docKey": str(row.get("docKey") or ""),
                "rcept_no": str(row.get("rcept_no") or row.get("rceptNo") or row.get("sourceRef") or ""),
                "section_order": int(row.get("section_order") or row.get("sectionOrder") or 0),
                "corp_code": str(row.get("corp_code") or row.get("corpCode") or ""),
                "corp_name": str(row.get("corp_name") or row.get("companyName") or ""),
                "stock_code": str(row.get("stock_code") or row.get("stockCode") or row.get("ticker") or ""),
                "rcept_dt": str(row.get("rcept_dt") or row.get("date") or ""),
                "report_nm": str(row.get("report_nm") or row.get("reportName") or ""),
                "section_title": str(row.get("section_title") or row.get("title") or row.get("sectionKey") or ""),
                "text": content[:500],
                "evidenceText": str(row.get("section_content") or row.get("searchText") or "")[:EVIDENCE_TEXT_LIMIT],
                "source": _runtimeSourceFromCatalog(str(row.get("source") or "")),
                "sourceRef": str(row.get("sourceRef") or ""),
                "sourceDataAsOf": str(row.get("sourceDataAsOf") or row.get("rcept_dt") or row.get("date") or ""),
                "contentLen": len(content),
                "url": str(row.get("url") or ""),
                "deleted": deleted,
            }
        )
    idx = builder.finalize()
    meta = pl.DataFrame(metaRecs)
    saveSegmentWithSidecar(idx, meta, "delta", saveDir)
    clearCache()
    del metaRecs, meta
    gc.collect()
    return idx["nDocs"]


def _removeSegmentArtifacts(base: Path, segment: str) -> None:
    for name in [*_segmentFiles(base, segment, requireExists=False), f"{segment}.npz"]:
        path = base / name
        if path.exists():
            path.unlink()


def clearDeltaSegment(*, tier: str = "full") -> None:
    """지정 tier의 delta artifact를 제거한다.

    Args:
        tier: full 또는 lite 출력 tier.

    Returns:
        None.

    Raises:
        OSError: 기존 artifact를 제거할 수 없을 때.

    Example:
        >>> callable(clearDeltaSegment)
        True
    """
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir, clearCache

    base = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    _removeSegmentArtifacts(base, "delta")
    clearCache()


def _runtimeSourceFromCatalog(source: str) -> str:
    return {"dartPanel": "panel", "edgarPanel": "edgar-panel", "newsPublic": "news"}.get(source, source)


def _buildAfMeta(*, showProgress: bool = True) -> dict[str, dict]:
    """allFilings 메타(content_raw 제외 경량) → {rcept_no: {corp_code,corp_name,stock_code,rcept_dt,report_nm}}.

    panel 롤업 문서의 표시 메타 보강용. content_raw 미로드라 빠르다.
    """
    from dartlab.core.dartClient import allFilingsDir as _allFilingsDir
    from dartlab.core.dartClient import allFilingsMetaSuffix

    _META_SUFFIX = allFilingsMetaSuffix()

    cols = ["rcept_no", "corp_code", "corp_name", "stock_code", "rcept_dt", "report_nm"]
    out: dict[str, dict] = {}
    files = sorted(f for f in _allFilingsDir().glob("*.parquet") if _META_SUFFIX not in f.stem)
    for f in files:
        try:
            df = pl.read_parquet(f, columns=cols)
        except (pl.exceptions.PolarsError, OSError):
            continue
        for row in df.iter_rows(named=True):
            rn = row.get("rcept_no") or ""
            if rn and rn not in out:
                out[rn] = {
                    "corp_code": row.get("corp_code") or "",
                    "corp_name": row.get("corp_name") or "",
                    "stock_code": row.get("stock_code") or "",
                    "rcept_dt": str(row.get("rcept_dt") or ""),
                    "report_nm": row.get("report_nm") or "",
                }
        del df
    if showProgress:
        _log.info(f"[main] allFilings 메타 dict: {len(out):,} filing")
    return out


def _panelDir():
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "dart" / "panel"


def _edgarPanelDir():
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "edgar" / "panel"


def _periodToReportName(period: str) -> str:
    """panel period(YYYYQn) → DART 정기보고서명 추정."""
    if not period:
        return ""
    if period.endswith("Q4"):
        return "사업보고서"
    if period.endswith("Q2"):
        return "반기보고서"
    if period.endswith("Q1") or period.endswith("Q3"):
        return "분기보고서"
    return period


def _panelEntries(base: Path) -> list[tuple[str, list[Path]]]:
    """flat/nested panel artifact 를 종목 단위로 열거."""
    if not base.exists():
        return []
    flat = {p.stem: [p] for p in base.glob("*.parquet") if not p.name.startswith("_")}
    entries: dict[str, list[Path]] = dict(flat)
    for d in base.iterdir():
        if not d.is_dir() or d.name in entries:
            continue
        files = sorted(f for f in d.glob("*.parquet") if not f.name.startswith("_"))
        if files:
            entries[d.name] = files
    return sorted(entries.items())


def _feedPanelRollup(
    builder,
    metaRecs,
    afMeta,
    panelRcepts,
    panelLimit,
    showProgress,
    *,
    whitelist=None,
    sinceDate=None,
    base=None,
    source="panel",
    market="kr",
) -> int:
    """panel 정규화 본문을 filing(rceptNo) 단위 롤업해 빌더에 추가 — "완전한 문서" 색인.

    종목별 parquet 스트리밍(read+del+gc) → rceptNo 별 contentRaw concat → get_text → addDoc 1 문서.
    DART(market="kr")는 표시 메타를 afMeta(allFilings)에서 보강하고 추가 rceptNo 를 panelRcepts 에
    기록(allFilings 패스 skip 용). EDGAR(market="us", base=_edgarPanelDir)는 동일 16-col 스키마라
    같은 롤업 코어를 공유하되 rceptNo=SEC accession 이라 rcept_dt 유도·DART 메타 보강 없이 색인.
    lite tier — whitelist(종목 한정)는 codeDir 단위, sinceDate(rcept_dt 하한)는 afMeta 기준 filing 단위.
    """
    import gc
    import os
    import re

    if base is None:
        base = _panelDir()
    if not base.exists():
        if showProgress:
            _log.info(f"[main] {source} 디렉토리 없음 — 롤업 skip")
        return 0
    entries = _panelEntries(base)
    if whitelist is not None:  # lite — 종목 한정
        entries = [(code, files) for code, files in entries if code in whitelist]
    _codeLimit = int(os.environ.get("DARTLAB_SEARCH_PANEL_CODES", "0"))  # 테스트용 제한(0=무제한)
    if _codeLimit > 0:
        entries = entries[:_codeLimit]

    perSection = 2000  # 섹션당 raw 캡 (메모리·시간 가드)
    rawCap = panelLimit * 4
    added = 0
    for ci, (code, files) in enumerate(entries):
        try:
            schema = pl.scan_parquet(files).collect_schema().names()
            schemaSet = set(schema)
            requiredCols = ["rceptNo", "contentRaw"]
            if not all(col in schemaSet for col in requiredCols):
                continue
            readCols = [
                col
                for col in ["rceptNo", "period", "contentRaw", "sectionLeaf", *EDGAR_DATE_COLUMNS]
                if col in schemaSet
            ]
            df = pl.read_parquet(files, columns=readCols)
            for col in ("period", "sectionLeaf"):
                if col not in df.columns:
                    df = df.with_columns(pl.lit("").alias(col))
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.height == 0:
            del df
            continue
        # 벡터 group_by — 섹션 raw 캡 후 rceptNo 별 list 수집. Python 섹션 루프 회피(8.7M row 직접순회 금지).
        try:
            rolled = (
                df.with_columns(pl.col("contentRaw").cast(pl.Utf8).str.slice(0, perSection))
                .group_by("rceptNo", maintain_order=True)
                .agg(
                    pl.col("contentRaw").alias("parts"),
                    pl.col("sectionLeaf").first().alias("leaf"),
                    pl.col("period").first().alias("period"),
                    *[pl.col(col).first().alias(col) for col in EDGAR_DATE_COLUMNS if col in df.columns],
                )
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        del df
        for row in rolled.iter_rows(named=True):
            rn = row["rceptNo"]
            if not rn:
                continue
            m = afMeta.get(rn, {})
            if market == "us":
                # EDGAR accession 은 날짜가 아니므로 date 컬럼 우선, 없으면 period(YYYYQn) 분기말을 freshness 로 쓴다.
                rdt = firstSearchDate(row, EDGAR_DATE_COLUMNS) or periodToDataAsOf(row.get("period"))
                reportNm = str(row.get("leaf") or row.get("period") or "")
            else:
                rdt = str(m.get("rcept_dt") or (rn[:8] if len(rn) >= 8 else ""))
                reportNm = m.get("report_nm") or _periodToReportName(str(row.get("period") or ""))
            if market == "kr" and sinceDate and rdt < sinceDate:  # lite — rcept_dt 하한(DART 날짜 의미)
                continue
            parts = row["parts"] or []
            raw = " ".join(p for p in parts if p)[:rawCap]
            text = _WS_RE.sub(" ", _TAG_RE.sub(" ", _BLOCK_RE.sub(" ", raw))).strip()[:panelLimit]
            if not text:
                continue
            builder.addDoc(text)
            metaRecs.append(
                {
                    "rcept_no": rn,
                    "section_order": 0,
                    "corp_code": m.get("corp_code", ""),
                    "corp_name": m.get("corp_name", ""),
                    "stock_code": m.get("stock_code", "") or code,
                    "rcept_dt": rdt,
                    "report_nm": reportNm,
                    "section_title": row.get("leaf") or "",
                    "text": text[:500],
                    "evidenceText": text[:EVIDENCE_TEXT_LIMIT],
                    "source": source,
                    "sourceDataAsOf": rdt,
                    "contentLen": len(text),
                    "url": "",
                }
            )
            panelRcepts.add(rn)
            added += 1
        del rolled
        if (ci + 1) % 200 == 0:
            gc.collect()
            if showProgress:
                _log.info(f"  panel {ci + 1}/{len(entries)}: {added:,} filing")
    return added


def _newsHeadlinesDir():
    # dataConfig SSOT 파생 — visibility-first taxonomy (news/public/rss) drift 차단.
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / DATA_RELEASES["newsHeadlines"]["dir"]


def _newsKey(url: str, date: str) -> tuple[str, int]:
    """뉴스 dedup 키 — url sha1 로 (rcept_no, section_order) 슬롯 점유.

    DART rcept_no 는 14 자리 숫자라 ``news:`` 접두 문자열과 절대 겹치지 않음 → 공시-뉴스 dedup 분리.

    Args:
        url: 기사 url.
        date: 기사 날짜(미사용, 시그니처 호환).

    Returns:
        tuple[str, int] — (``"news:"+sha1(url)[:16]``, 0).

    Raises:
        없음.

    Example:
        >>> _newsKey("http://x", "2026-05-28")[0].startswith("news:")
        True
    """
    h = hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:16]
    return (f"news:{h}", 0)


def _feedNews(builder, metaRecs, newsLimit, showProgress, *, sinceDate=None) -> int:
    """뉴스 헤드라인(news/headlines/**/*.parquet)을 검색 인덱스에 추가 — source='news'.

    본문 = title + query(시장 맥락어, BM25 recall 보강). rcept_no 슬롯은 _newsKey(url) 로 점유,
    dartUrl 은 기사 url(_resolveResultUrl 분기). 뉴스 parquet 부재 시 0 반환(graceful).

    Args:
        builder: _IncrementalBuilder 인스턴스.
        metaRecs: meta dict 누적 리스트(공시와 동일 11 키 emit).
        newsLimit: 뉴스 본문 최대 문자 수.
        showProgress: True 면 progress 로그.

    Returns:
        int — 추가된 뉴스 doc 수.

    Raises:
        없음 (파일별 read 오류는 skip).

    Example:
        >>> _feedNews(builder, [], 800, False)  # doctest: +SKIP
    """
    import gc

    base = _newsHeadlinesDir()
    if not base.exists():
        if showProgress:
            _log.info("[main] news/headlines 없음 — 뉴스 skip")
        return 0
    files = sorted(base.rglob("*.parquet"))
    added = 0
    for i, f in enumerate(files):
        try:
            df = pl.read_parquet(f, columns=["title", "query", "url", "date", "source"])
        except (pl.exceptions.PolarsError, OSError):
            continue
        for row in df.iter_rows(named=True):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            if sinceDate and str(row.get("date") or "").replace("-", "") < sinceDate:  # lite — 날짜 하한
                continue
            text = f"{title} {(row.get('query') or '').strip()}".strip()[:newsLimit]
            builder.addDoc(text)
            rn, so = _newsKey(row.get("url") or "", str(row.get("date") or ""))
            metaRecs.append(
                {
                    "rcept_no": rn,
                    "section_order": so,
                    "corp_code": "",
                    "corp_name": "",
                    "stock_code": "",
                    "rcept_dt": str(row.get("date") or "").replace("-", ""),
                    "report_nm": "",
                    "section_title": row.get("source") or "",
                    "text": title[:500],
                    "evidenceText": text[:EVIDENCE_TEXT_LIMIT],
                    "source": "news",
                    "sourceDataAsOf": str(row.get("date") or "").replace("-", ""),
                    "contentLen": len(text),
                    "url": row.get("url") or "",
                }
            )
            added += 1
        del df
        if (i + 1) % 50 == 0:
            gc.collect()
    if showProgress:
        _log.info(f"[main] 뉴스 {added:,} 헤드라인 색인")
    return added


# 일간 변경은 rebuildDeltaFromCatalog가 월간 main 기준 누적 L0 하나로 쓴다.


# ── HF 동기화 ──


_HF_CONTENTINDEX_ATTEMPTED = False


def ensureContentIndex(tier: str | None = None) -> None:
    """content 인덱스(main.*) 부재 시 HF lazy 다운로드 — 1회, graceful. (panel ensurePanelFromHf 미러)

    pip 사용자 진입점: `dartlab.search()` 첫 호출 시 인덱스를 HF 에서 자동 fetch. 배포 전략:
    - flat ``contentIndex/main.postings.bin`` 가 로컬에 있으면(sidecar SSOT) 즉시 반환(no-op).
    - 없으면 tier(기본 lite, env ``DARTLAB_SEARCH_TIER``) 서브디렉터리를 HF 에서 pull
      (``contentIndex/{tier}/*``) — 사용자 다운로드 부담 격감(최근·주요종목 경량).
    - tier 가 아직 HF 에 미배포(전환기)면 flat ``contentIndex/*`` 로 fallback(기존 full 보호).
    `DARTLAB_NO_HF_DOWNLOAD=1` skip. 세션 1회만 시도(재검색 폭주 방지). pyodide 는 즉시 반환.

    Args:
        tier: 받을 tier ("lite"/"full"). None 이면 env ``DARTLAB_SEARCH_TIER`` 또는 "lite".

    Returns:
        None — 부작용으로 `data/dart/contentIndex/[{tier}/]` 를 채운다. 이미 있으면 무동작.

    Raises:
        없음 — 모든 예외 graceful 흡수.

    Example:
        >>> ensureContentIndex()  # doctest: +SKIP
    """
    import os

    global _HF_CONTENTINDEX_ATTEMPTED
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir, _hasMainPostings
    from dartlab.providers.dart.search.localUpdate import downloadAndActivateContentIndex, resolveActiveIndexDir

    base = _contentIndexDir()
    if resolveActiveIndexDir(base) is not None:
        return
    if _hasMainPostings(base):
        return  # flat 로컬 존재(sidecar SSOT) — no-op
    if os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        return
    if _HF_CONTENTINDEX_ATTEMPTED:
        return
    _HF_CONTENTINDEX_ATTEMPTED = True
    tier = (tier or os.environ.get("DARTLAB_SEARCH_TIER") or "lite").strip()
    result = downloadAndActivateContentIndex(tier=tier, baseDir=base)
    if result.get("activated"):
        return
    try:
        from huggingface_hub import snapshot_download

        from dartlab.core.dataConfig import DATA_RELEASES, repoFor
        from dartlab.core.hfRetry import retryHfCall

        ciDir = DATA_RELEASES["contentIndex"]["dir"]
        repo = repoFor("contentIndex")
        # 1) tier 서브디렉터리 우선 pull (경량 배포). HF read SSOT(core.hfRetry) 경유.
        retryHfCall(
            snapshot_download,
            repo_id=repo,
            repo_type="dataset",
            allow_patterns=[f"{ciDir}/{tier}/*"],
            local_dir=str(Path(_cfg.dataDir)),
        )
        if _hasMainPostings(base / tier):
            return
        # 2) 전환기 fallback — tier 미배포 시 flat(legacy full) pull (기존 사용자 동작 보호).
        retryHfCall(
            snapshot_download,
            repo_id=repo,
            repo_type="dataset",
            allow_patterns=[f"{ciDir}/*"],
            local_dir=str(Path(_cfg.dataDir)),
        )
    except Exception:  # noqa: BLE001 — 자동로드 실패는 빈 결과(graceful)
        pass


def indexInfo() -> dict:
    """검색 인덱스 메타(dataAsOf/nDocs/라우터 가용) 반환 — freshness 노출용.

    Args:
        (없음).

    Returns:
        dict — {available, dataAsOf, nDocs, hasRouter, hasDelta, schemaVersion, compatible}.
        인덱스 부재 시 available=False. ``schemaVersion`` = 받은 인덱스 포맷 버전(없으면 0=legacy),
        ``compatible`` = 코드 INDEX_SCHEMA_VERSION 이상으로 읽을 수 있는지(인덱스 ver ≤ 코드 ver).

    Raises:
        없음.

    Example:
        >>> indexInfo()  # doctest: +SKIP
    """
    from dartlab.providers.dart.search.fieldIndex import INDEX_SCHEMA_VERSION, _activeIndexDir
    from dartlab.providers.dart.search.manifest import indexInfoFromManifest, loadSearchManifest

    base = _activeIndexDir()  # 실제 로드되는 인덱스(flat/tier) 기준
    info: dict = {
        "available": False,
        "dataAsOf": None,
        "nDocs": 0,
        "hasRouter": False,
        "hasDelta": False,
        "schemaVersion": 0,
        "compatible": True,
        "sourceDataAsOf": {},
        "nDocsBySource": {},
        "nDocsByTier": {},
        "manifestValid": False,
        "manifestErrors": [],
    }
    manifest = loadSearchManifest(base)
    if manifest is not None:
        info.update(indexInfoFromManifest(manifest, codeSchemaVersion=INDEX_SCHEMA_VERSION, indexDir=base))
    mainInfo = base / "main_info.json"
    if manifest is None and mainInfo.exists():
        try:
            d = json.loads(mainInfo.read_text(encoding="utf-8"))
            info["available"] = True
            info["dataAsOf"] = d.get("builtAt")
            info["nDocs"] = int(d.get("nDocs", 0))
            info["schemaVersion"] = int(d.get("schemaVersion", 0))  # 없으면 legacy(0)
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    # 받은 인덱스가 코드보다 신버전이면 비호환(라이브러리 업그레이드 필요). 동버전 이하는 읽기 가능.
    if manifest is None:
        info["compatible"] = info["schemaVersion"] <= INDEX_SCHEMA_VERSION
    # hasRouter 는 파일 *존재* 가 아니라 *이벤트 비어있지 않음* — 빈 산출물이 업로드되면 라우팅이 죽은
    # plain-only degraded 인데 파일은 존재. 존재만 보면 degraded 를 healthy 로 거짓보고한다(429 사고 교훈).
    from dartlab.providers.dart.search.router import loadRouterModel

    model = loadRouterModel(base)
    info["hasRouter"] = bool(model and model.get("events"))
    info["hasDelta"] = bool(info.get("hasDelta")) or (base / "delta.postings.bin").exists()
    return info


_SEARCH_SIDECAR_SUFFIXES: tuple[str, ...] = (
    ".postings.bin",
    ".terms.bin",
    ".docLengths.bin",
    ".meta.bin",
    ".metaOffsets.bin",
    ".search_meta.json",
)


def _searchSidecarNames(segment: str) -> list[str]:
    """range-fetch sidecar 파일명(segment 별 6종) — 존재 여부 무관 후보 목록."""
    return [f"{segment}{suf}" for suf in _SEARCH_SIDECAR_SUFFIXES]


# 인덱스 동반 공용 산출물(세그먼트 무관) — manifest 는 publish 가 별도로 끝에 붙인다.
_INDEX_COMMON_FILES: tuple[str, ...] = (
    "router.json",
    "catalog_snapshot.parquet",
    "main_catalog_snapshot.parquet",
    "source_manifest_set.json",
)


def _segmentFiles(base: str | Path, segment: str = "main", *, requireExists: bool = True) -> list[str]:
    """세그먼트 파일 SSOT — stems/info/parquet + STORED sidecar 6종. **npz 제외**(sidecar=SSOT).

    파일명 열거의 단일 출처. manifest/push/pull 이 전부 이 helper 만 호출(흩어진 리터럴 제거).

    Args:
        base: 인덱스 디렉터리.
        segment: 세그먼트 이름("main").
        requireExists: True 면 로컬 존재분만(빌드/publish), False 면 후보 전체(pull tolerant).

    Returns:
        list[str] — 파일명 목록.

    Raises:
        없음.

    Example:
        >>> _segmentFiles(".", "main", requireExists=False)[:3]
        ['main_stems.json', 'main_info.json', 'main_meta.parquet']
    """
    names = [f"{segment}_stems.json", f"{segment}_info.json", f"{segment}_meta.parquet", *_searchSidecarNames(segment)]
    if segment == "delta":
        names.append("delta_overrides.json")
    if not requireExists:
        return names
    base = Path(base)
    return [n for n in names if (base / n).exists()]


def indexPublishNames(base: str | Path, *, requireExists: bool = True) -> list[str]:
    """publish/pull 파일 SSOT - main, 선택적 delta, 공용 산출물, manifest.

    Args:
        base: 인덱스 디렉터리.
        requireExists: True 면 로컬 존재분만, False 면 후보 전체(pull tolerant).

    Returns:
        list[str] — publish 대상 파일명(manifest.json 포함, 순서는 publish 가 정규화).

    Raises:
        없음.

    Example:
        >>> "main.postings.bin" in indexPublishNames(".", requireExists=False)
        True
    """
    from dartlab.providers.dart.search.entityGraph import ENTITY_GRAPH_CATALOG_NAME

    base = Path(base)
    names = [
        *_segmentFiles(base, "main", requireExists=requireExists),
        *_segmentFiles(base, "delta", requireExists=requireExists),
    ]
    extras = [*_INDEX_COMMON_FILES, ENTITY_GRAPH_CATALOG_NAME, "manifest.json"]
    if requireExists:
        extras = [n for n in extras if (base / n).exists()]
    return names + extras


def _buildSearchSidecar(idx: dict, meta: pl.DataFrame, name: str, saveDir: Path | None = None) -> None:
    """range-fetch sidecar 동거 생성 — 실패해도 엔진 인덱스 빌드는 보존(additive·fail-safe)."""
    from dartlab.providers.dart.search.fieldIndex import saveShardedSegment

    try:
        saveShardedSegment(idx, meta, name, saveDir)
    except Exception as exc:  # noqa: BLE001 — sidecar 실패가 엔진 빌드를 깨면 안 됨(검색 range-fetch만 비활성)
        _log.warning("[sidecar] %s 빌드 실패(검색 range-fetch 비활성): %s", name, exc)


def saveSegmentWithSidecar(idx: dict, meta: pl.DataFrame, name: str = "main", saveDir: Path | None = None) -> None:
    """세그먼트 저장 **단일 choke point**(유일 writer) — 동반물(stems/info/parquet) + STORED sidecar.

    compact-only(P2): postings SSOT = sidecar 단독(npz 폐기). 빌드 경로(rebuildMain/rebuildMainFromCatalog)·
    드릴·round-trip 은 이 함수만 호출 — postings 표현이 흩어지지 않게 한곳.

    Args:
        idx: 인덱스 dict.
        meta: doc 순 meta DataFrame.
        name: 세그먼트 이름("main").
        saveDir: 출력 디렉터리.

    Returns:
        None.

    Raises:
        없음 (sidecar 실패는 fail-safe).

    Example:
        >>> callable(saveSegmentWithSidecar)
        True
    """
    from dartlab.providers.dart.search.fieldIndex import writeSegmentCompanions

    writeSegmentCompanions(idx, meta, name, saveDir)  # stems/info/meta.parquet (npz 없음)
    _buildSearchSidecar(idx, meta, name, saveDir)  # postings/terms/docLengths/meta.bin (=SSOT)


def writeIndexManifest(indexDir: str | Path, *, tier: str = "full", buildCommand: str = "") -> dict:
    """Write `manifest.json` for the current content index directory.

    Args:
        indexDir: Content index directory containing main/delta segment files.
        tier: Search artifact tier name.
        buildCommand: Build command label stored for operator diagnostics.

    Returns:
        dict: Manifest payload that was written.

    Raises:
        OSError: If manifest cannot be written.

    Example:
        >>> callable(writeIndexManifest)
        True
    """
    from dartlab.providers.dart.search.entityGraph import ENTITY_GRAPH_CATALOG_NAME
    from dartlab.providers.dart.search.fieldIndex import INDEX_SCHEMA_VERSION
    from dartlab.providers.dart.search.manifest import writeSearchManifest

    base = Path(indexDir)
    sourceCounts: dict[str, int] = {}
    sourceDataAsOf: dict[str, str] = {}
    requiredFiles: list[str] = []
    mainDataAsOf = ""
    deltaDataAsOf = ""
    mainDocs = 0
    deltaDocs = 0
    segmentMeta: dict[str, pl.DataFrame] = {}

    for segment in ("main", "delta"):
        # meta.parquet = 세그먼트 앵커(항상 존재·canary 입력). requiredFiles 는 stems/info/parquet + sidecar(존재분, npz 제외=SSOT).
        if not (base / f"{segment}_meta.parquet").exists():
            continue
        requiredFiles.extend(_segmentFiles(base, segment))
        meta = _readManifestMeta(base / f"{segment}_meta.parquet")
        segmentMeta[segment] = meta
        info = json.loads((base / f"{segment}_info.json").read_text(encoding="utf-8"))
        nDocs = int(info.get("nDocs", meta.height) or 0)
        if segment == "main":
            mainDocs = nDocs
        else:
            deltaDocs = nDocs
        segmentDataAsOf = _segmentDataAsOf(meta)
        if segment == "main":
            mainDataAsOf = segmentDataAsOf
        else:
            deltaDataAsOf = segmentDataAsOf
    if (base / "router.json").exists():
        requiredFiles.append("router.json")
    if (base / "catalog_snapshot.parquet").exists():
        requiredFiles.append("catalog_snapshot.parquet")
    if (base / "main_catalog_snapshot.parquet").exists():
        requiredFiles.append("main_catalog_snapshot.parquet")
    sourceManifestSet = _loadSourceManifestSet(base / "source_manifest_set.json")
    if sourceManifestSet:
        requiredFiles.append("source_manifest_set.json")
    entityGraphCatalog = _entityGraphCatalogSummary(base / ENTITY_GRAPH_CATALOG_NAME)
    if entityGraphCatalog:
        requiredFiles.append(ENTITY_GRAPH_CATALOG_NAME)
    effectiveMeta = _effectiveSegmentMeta(segmentMeta.get("main"), segmentMeta.get("delta"))
    sourceCounts = _sourceCounts(effectiveMeta)
    sourceDataAsOf = _sourceDataAsOf(effectiveMeta)
    sourceCanaryPack = []
    if effectiveMeta.height:
        from dartlab.providers.dart.search.artifactCanary import CANARY_PACK_VERSION, buildSourceCanaryPackFromMeta

        sourceCanaryPack = buildSourceCanaryPackFromMeta(effectiveMeta)
        canaryPackVersion = CANARY_PACK_VERSION
    else:
        canaryPackVersion = ""

    manifest = {
        "artifactVersion": 1,
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "tokenizerVersion": f"content-bigram-v{INDEX_SCHEMA_VERSION}",
        "normalizerVersion": "fieldIndexRebuild-v1",
        "sourceRefVersion": "v1",
        "builtAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mainDataAsOf": mainDataAsOf,
        "deltaDataAsOf": deltaDataAsOf,
        "sourceDataAsOf": sourceDataAsOf,
        "nDocsBySource": sourceCounts,
        "nDocsByTier": {tier: effectiveMeta.height},
        "newDocs": 0,
        "changedDocs": max(deltaDocs - _deletedCount(segmentMeta.get("delta")), 0),
        "deletedDocs": _deletedCount(segmentMeta.get("delta")),
        "unchangedDocs": max(effectiveMeta.height - deltaDocs, 0),
        "hasDelta": deltaDocs > 0,
        "requiredFiles": requiredFiles,
        "fileHashes": {name: _sha256File(base / name) for name in requiredFiles if (base / name).exists()},
        "canaryPackVersion": canaryPackVersion,
        "sourceCanaryPack": sourceCanaryPack,
        "sourceManifestSetId": sourceManifestSet.get("sourceManifestSetId", ""),
        "sourceManifestSet": _sourceManifestSetSummary(sourceManifestSet),
        "entityGraphCatalog": entityGraphCatalog,
        "qualityReportPath": "",
        "compatibleMinLibraryVersion": "",
        "compatibleMaxSchemaVersion": INDEX_SCHEMA_VERSION,
        "buildCommand": buildCommand,
        "gitSha": "",
    }
    writeSearchManifest(base, manifest)
    return manifest


_MANIFEST_META_COLUMNS: tuple[str, ...] = (
    "sourceRef",
    "rcept_no",
    "section_order",
    "source",
    "sourceDataAsOf",
    "rcept_dt",
    "section_title",
    "text",
    "deleted",
)
_MANIFEST_CANARY_TEXT_LIMIT = 120


def _readManifestMeta(path: Path) -> pl.DataFrame:
    """Stream only manifest columns and keep a bounded canary text prefix."""
    schema = set(pl.read_parquet_schema(path))
    expressions = []
    for column in _MANIFEST_META_COLUMNS:
        if column not in schema:
            continue
        expression = pl.col(column)
        if column == "text":
            expression = expression.cast(pl.Utf8, strict=False).fill_null("").str.slice(0, _MANIFEST_CANARY_TEXT_LIMIT)
        expressions.append(expression.alias(column))
    return pl.scan_parquet(path).select(expressions).collect(engine="streaming")


def _loadSourceManifestSet(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _sourceManifestSetSummary(payload: dict) -> dict:
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    return {
        "schemaVersion": payload.get("schemaVersion", ""),
        "sourceManifestSetId": payload.get("sourceManifestSetId", ""),
        "expectedSources": payload.get("expectedSources") if isinstance(payload.get("expectedSources"), list) else [],
        "combinedCatalogRows": payload.get("combinedCatalogRows"),
        "combinedCatalogSha256": payload.get("combinedCatalogSha256", ""),
        "sources": [
            {
                "source": item.get("source", ""),
                "dataAsOf": item.get("dataAsOf", ""),
                "snapshotScope": item.get("snapshotScope", ""),
                "totalRows": item.get("totalRows"),
                "catalogRows": item.get("catalogRows"),
                "manifestSha256": item.get("manifestSha256", ""),
                "catalogSha256": item.get("catalogSha256", ""),
                "producer": item.get("producer", ""),
            }
            for item in sources
            if isinstance(item, dict)
        ],
    }


def _entityGraphCatalogSummary(path: Path) -> dict:
    if not path.exists():
        return {}
    catalog = pl.read_parquet(path)
    stockCodeCount = 0
    if catalog.height and "stockCode" in catalog.columns:
        stockCodeCount = int(catalog.select(pl.col("stockCode").cast(pl.Utf8).n_unique()).item() or 0)
    return {
        "schemaVersion": "searchEntityGraphCatalog.v1",
        "path": path.name,
        "nEntities": catalog.height,
        "stockCodeCount": stockCodeCount,
        "dataAsOf": _entityGraphCatalogDataAsOf(catalog),
        "columns": catalog.columns,
    }


def _entityGraphCatalogDataAsOf(catalog: pl.DataFrame) -> str:
    if catalog.height == 0:
        return ""
    for column in ("dataAsOf", "generatedAt"):
        if column not in catalog.columns:
            continue
        values = [str(value or "") for value in catalog.get_column(column).to_list()]
        values = [value for value in values if value]
        if values:
            return max(values)
    return ""


def pushContentIndex(token: str | None = None, *, tier: str = "full", promoteCurrent: bool | None = None) -> dict:
    """content 인덱스 (main + delta) 를 HF staging 후 current manifest pointer 로 publish.

    Args:
        token: HF write 토큰.
        tier: ``"full"`` (flat ``dart/contentIndex/``) / ``"lite"`` (``dart/contentIndex/lite/``).

        promoteCurrent: True promotes the current manifest pointer. False
            stages a candidate manifest only. None reads
            ``DARTLAB_SEARCH_PROMOTE_CURRENT`` and defaults to True.

    Returns:
        Publish summary.

    Raises:
        없음.

    Example:
        >>> pushContentIndex(tier="lite")  # doctest: +SKIP
    """
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    outDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    # publish 파일 SSOT - main + 선택적 delta sidecar, 공용 파일, manifest.
    names = indexPublishNames(outDir)
    if promoteCurrent is None:
        promoteCurrent = _envFlag("DARTLAB_SEARCH_PROMOTE_CURRENT", default=True)
    return publishContentIndexFiles(
        token=token,
        indexDir=outDir,
        files=names,
        tier=tier,
        promoteCurrent=promoteCurrent,
    )


def _envFlag(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "n"}


def pullContentIndex(tier: str = "full") -> int:
    """HF에서 content 인덱스 다운로드 (main + delta) — tier 별 경로 + repoFor 라우팅.

    Args:
        tier: ``"full"`` (flat ``dart/contentIndex/``) / ``"lite"`` (``dart/contentIndex/lite/``).

    Returns:
        int — 다운로드 성공한 파일 수.

    Raises:
        없음.

    Example:
        >>> pullContentIndex(tier="lite")  # doctest: +SKIP
    """
    from huggingface_hub import hf_hub_download

    from dartlab.core.dataConfig import repoFor
    from dartlab.core.dataLoader import _getDataRoot
    from dartlab.providers.dart.search.entityGraph import ENTITY_GRAPH_CATALOG_NAME
    from dartlab.providers.dart.search.fieldIndex import _contentIndexDir, clearCache

    outDir = _contentIndexDir() if tier == "full" else _contentIndexDir(tier)
    outDir.mkdir(parents=True, exist_ok=True)
    dataDir = _getDataRoot()  # dart/contentIndex/ 앞의 루트
    ciDir = DATA_RELEASES["contentIndex"]["dir"]
    repoPrefix = ciDir if tier == "full" else f"{ciDir}/{tier}"
    repo = repoFor("contentIndex")

    # 런타임 필요분만 pull(per-file tolerant·404 무시) — segment sidecar + manifest/router/entityGraph.
    # catalog snapshot은 빌드 provenance라 일반 runtime pull에서 제외한다.
    names = [
        *_segmentFiles(outDir, "main", requireExists=False),
        *_segmentFiles(outDir, "delta", requireExists=False),
        "manifest.json",
        "router.json",
        ENTITY_GRAPH_CATALOG_NAME,
    ]
    ok = 0
    from dartlab.core.hfRetry import retryHfCall

    _log.info("[cyan]⬇ HF[/] contentIndex (%d 파일, tier=%s)", len(names), tier)
    for name in names:
        try:
            retryHfCall(  # HF read SSOT(core.hfRetry) — 429/503/504 단일 백오프
                hf_hub_download,
                repo_id=repo,
                repo_type="dataset",
                filename=f"{repoPrefix}/{name}",
                local_dir=str(dataDir),
            )
            ok += 1
        except (OSError, ConnectionError, ValueError):
            # HF Hub 다운로드 실패 (네트워크 / 인증 / 파일 부재) — 다음 파일 진행.
            continue
    clearCache()
    _log.info("[green]✓[/] contentIndex (%d/%d 파일)", ok, len(names))
    return ok


def _shadowKeyExpr(meta: pl.DataFrame) -> pl.Expr:
    def _value(primary: str, fallback: str = "") -> pl.Expr:
        if primary in meta.columns:
            return pl.col(primary).cast(pl.Utf8).fill_null("")
        if fallback and fallback in meta.columns:
            return pl.col(fallback).cast(pl.Utf8).fill_null("")
        return pl.lit("")

    return pl.concat_str(
        [_value("sourceRef", "source"), _value("rcept_no"), _value("section_order")],
        separator="\u001f",
    )


def _effectiveSegmentMeta(main: pl.DataFrame | None, delta: pl.DataFrame | None) -> pl.DataFrame:
    if main is None and delta is None:
        return pl.DataFrame()
    if delta is None or delta.is_empty():
        return main if main is not None else pl.DataFrame()
    deltaWithKey = delta.with_columns(_shadowKeyExpr(delta).alias("__shadowKey"))
    deltaKeys = deltaWithKey.select("__shadowKey").unique()
    activeDelta = deltaWithKey
    if "deleted" in activeDelta.columns:
        activeDelta = activeDelta.filter(~pl.col("deleted").fill_null(False))
    if main is None or main.is_empty():
        return activeDelta.drop("__shadowKey")
    activeMain = (
        main.with_columns(_shadowKeyExpr(main).alias("__shadowKey"))
        .join(deltaKeys, on="__shadowKey", how="anti")
        .drop("__shadowKey")
    )
    return pl.concat([activeDelta.drop("__shadowKey"), activeMain], how="diagonal_relaxed")


def _deletedCount(meta: pl.DataFrame | None) -> int:
    if meta is None or meta.is_empty() or "deleted" not in meta.columns:
        return 0
    return int(meta.select(pl.col("deleted").fill_null(False).sum()).item() or 0)


def _sourceCounts(meta: pl.DataFrame) -> dict[str, int]:
    if meta.height == 0 or "source" not in meta.columns:
        return {}
    out: dict[str, int] = {}
    for row in meta.group_by("source").len().iter_rows(named=True):
        source = str(row.get("source") or "unknown")
        out[source] = int(row.get("len") or 0)
    return out


def _sourceDataAsOf(meta: pl.DataFrame) -> dict[str, str]:
    if meta.height == 0:
        return {}
    out: dict[str, str] = {}
    for row in meta.iter_rows(named=True):
        source = str(row.get("source") or "unknown")
        dataAsOf = str(row.get("sourceDataAsOf") or row.get("rcept_dt") or "")
        if dataAsOf > out.get(source, ""):
            out[source] = dataAsOf
    return out


def _segmentDataAsOf(meta: pl.DataFrame) -> str:
    values = _sourceDataAsOf(meta).values()
    return max(values) if values else ""


def _sha256File(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ── 통계 ──


def contentStats() -> dict:
    """content 인덱스 통계.

    Args:
        (인자 자동 생성).

    Raises:
        없음.

    Example:
        >>> contentStats(...)

    Returns:
        dict — 결과 통계.
    """
    from dartlab.providers.dart.search.fieldIndex import _getSegments

    segments = _getSegments()
    out: dict = {}
    for name, (idx, meta) in segments.items():
        out[name] = {
            "nDocs": idx["nDocs"],
            "nStems": len(idx["stemDict"]),
            "nPostings": int(idx["offsets"][-1]),
            "avgDocLength": idx["avgDocLength"],
        }
    return out


def iterContent(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    limit: int = 10,
):
    """``searchContent`` 의 iterator pair (룰 10).

    Args:
        query: 자연어 쿼리.
        corpCode: corp_code 필터.
        stockCode: 종목코드 필터.
        limit: 반환 건수.

    Yields:
        검색 결과 row dict.

    Example:
        >>> for row in iterContent("매출", limit=5):
        ...     print(row.get("rcept_no"))

    Raises:
        없음.
    """
    from dartlab.providers.dart.search.fieldIndex import searchContent

    df = searchContent(query, corpCode=corpCode, stockCode=stockCode, limit=limit)
    if df is None or df.is_empty():
        return
    yield from df.iter_rows(named=True)
