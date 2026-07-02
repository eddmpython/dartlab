"""EDGAR 부문별 매출(segment revenue) scan 빌더. DERA notes 데이터셋 차원 사실 → segments.parquet.

KR noteSeries 부문 구성(panel XBRL 셀)의 US 대칭. US 는 10-K/10-Q HTML 표가 레이아웃 이질이라
표 파싱 대신 DERA notes 데이터셋(num.tsv + dim.tsv)의 차원 태그를 직독한다(표 파싱 0, 전 상장사 균일).
실측: AAPL FY2025 Americas 178.4B·Europe 111.0B 등 실제 공시값 그대로(연결합 검증 일치).

축 선별 규칙 (덕지덕지 방지, 태그 기준 기계 판정):
    - segments 문자열의 축 집합 ⊆ {BusinessSegments, ConsolidationItems} (제품·지역 교차축 배제).
    - BusinessSegments= 멤버 필수, ConsolidationItems 있으면 OperatingSegments 만(제거: 내부거래·조정).
    - tag = Revenue 계열, uom=USD, qtrs 1(분기)·4(연간), coreg 없음(모회사), iprx=0(정본 표기).

10-K 는 비교연도 2개를 같이 태깅하므로 최근 zip 몇 개로도 5~6개년 시계열이 나온다.
수집(zip 다운로드·스트리밍)은 gather ``notesBulk`` 위임, 본 모듈은 선별·정형(가공)만.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

SEGMENTS_COLS = {
    "stockCode": pl.Utf8,
    "period": pl.Utf8,  # ddate 달력분기 (panel period 관례와 동일: 20250930 → 2025Q3)
    "year": pl.Utf8,
    "quarter": pl.Utf8,  # "1"~"4" (달력분기) · 연간(qtrs=4) 행도 종료월 분기로 라벨
    "flow": pl.Utf8,  # "Q"(3개월) | "Y"(12개월)
    "segment": pl.Utf8,
    "revenue": pl.Float64,
}

_REVENUE_TAGS = frozenset(
    {
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "RevenuesNetOfInterestExpense",
    }
)
_SEG_AXIS = "BusinessSegments="
_ALLOWED_AXES = {"BusinessSegments", "ConsolidationItems"}
_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def segmentNameFromMember(member: str) -> str:
    """축 멤버명 → 표시명. 접미(Segment/Member) 제거 + camelCase 공백 분리.

    Args:
        member: ``GreaterChinaSegment`` 류 멤버 문자열.

    Returns:
        str. ``Greater China``.

    Raises:
        없음.

    Example:
        >>> segmentNameFromMember("GreaterChinaSegment")
        'Greater China'
    """
    m = re.sub(r"(Segment|Member)s?$", "", member.strip())
    return _CAMEL_RE.sub(" ", m).strip()


def _segmentFromDims(segments: str) -> str | None:
    """dim.tsv segments 문자열 → 부문 멤버명(선별 통과 시) 또는 None."""
    pairs = [p for p in (segments or "").split(";") if p]
    axes = {}
    for p in pairs:
        if "=" not in p:
            return None
        k, v = p.split("=", 1)
        axes[k] = v
    if set(axes) - _ALLOWED_AXES or "BusinessSegments" not in axes:
        return None
    cons = axes.get("ConsolidationItems", "OperatingSegments")
    if "OperatingSegments" not in cons:
        return None  # 내부거래 제거·조정 항목
    return axes["BusinessSegments"]


def segmentRowsFromZip(zipPath: Path, cikToTicker: dict[str, str], *, verbose: bool = False) -> list[dict]:
    """단일 notes zip → 부문 매출 행 목록 (스트리밍, 상수 메모리).

    Args:
        zipPath: notes zip 경로.
        cikToTicker: 0-padded 10자리 CIK → ticker 매핑.
        verbose: 진행 로그.

    Returns:
        list[dict]. SEGMENTS_COLS 행(중복 미제거. 병합·dedup 은 호출측).

    Raises:
        zipfile.BadZipFile: 손상 zip.

    Example:
        >>> rows = segmentRowsFromZip(Path("2025_10_notes.zip"), {"0000320193": "AAPL"})  # doctest: +SKIP

    SeeAlso:
        - ``buildEdgarSegments`` (여러 stem 오케스트레이션)
        - ``dartlab.gather.edgar.notesBulk.iterNotesTsv`` (스트리밍 위임)

    Requires:
        - gather.edgar.notesBulk (수집 SSOT)

    Capabilities:
        - 10-K/10-Q 의 부문별 매출을 차원 태그로 직독(비교연도 포함). 표 파싱 0.

    Guide:
        - dim.tsv 를 먼저 부문 축만 필터해 소형 map 으로 만들고 num.tsv 를 1-pass 조인한다.

    When:
        - segments 백필 runner·edgarSync 월별 갱신.

    How:
        - sub(10-K/10-Q adsh) → dim(부문 dimhash) → num(Revenue×dimh 조인) 순 3 스트림.

    AIContext:
        internal 가공기. AI 직접 호출 X.
    """
    from dartlab.gather.edgar.notesBulk import iterNotesTsv

    adshToTicker: dict[str, str] = {}
    for r in iterNotesTsv(zipPath, "sub.tsv"):
        if r.get("form") in ("10-K", "10-Q"):
            tk = cikToTicker.get(str(r.get("cik") or "").zfill(10))
            if tk:
                adshToTicker[r["adsh"]] = tk

    dimToSegment: dict[str, str] = {}
    for r in iterNotesTsv(zipPath, "dim.tsv"):
        seg = _segmentFromDims(str(r.get("segments") or ""))
        if seg:
            dimToSegment[r["dimhash"]] = seg

    rows: list[dict] = []
    for r in iterNotesTsv(zipPath, "num.tsv"):
        if r.get("tag") not in _REVENUE_TAGS or r.get("adsh") not in adshToTicker:
            continue
        if r.get("uom") != "USD" or r.get("qtrs") not in ("1", "4") or r.get("coreg"):
            continue
        if str(r.get("iprx") or "0") != "0":
            continue
        seg = dimToSegment.get(str(r.get("dimh") or ""))
        if not seg:
            continue
        ddate = str(r.get("ddate") or "")
        val = r.get("value")
        if len(ddate) != 8 or not val:
            continue
        try:
            revenue = float(val)
        except ValueError:
            continue
        if revenue <= 0:
            continue
        q = (int(ddate[4:6]) + 2) // 3
        rows.append(
            {
                "stockCode": adshToTicker[r["adsh"]],
                "period": f"{ddate[:4]}Q{q}",
                "year": ddate[:4],
                "quarter": str(q),
                "flow": "Y" if r["qtrs"] == "4" else "Q",
                "segment": segmentNameFromMember(seg),
                "revenue": revenue,
            }
        )
    if verbose:
        _log.info(f"[segmentsBuild] {zipPath.name}: {len(rows)}행 ({len(adshToTicker)}건 10-K/10-Q)")
    return rows


def buildEdgarSegments(stems: list[str], *, verbose: bool = False) -> pl.DataFrame:
    """notes stem 목록 → 부문 매출 DataFrame (다운로드 위임 + 추출 + dedup).

    발행(HF)은 호출측(runner/CI)이 담당한다. 같은 (stockCode, period, flow, segment) 는 최신 stem
    값이 이긴다(정정 반영. stems 순서와 무관하게 뒤에 준 stem 우선).

    Parameters
    ----------
    stems : list[str]
        처리할 notes stem (``2025_10`` 등). 뒤일수록 우선.
    verbose : bool
        진행 로그.

    Returns
    -------
    pl.DataFrame
        SEGMENTS_COLS 스키마. stems 전체 병합·dedup 본.

    Raises
    ------
    httpx.HTTPStatusError
        미배포 stem 다운로드 실패.

    Examples
    --------
    >>> df = buildEdgarSegments(["2025_10"], verbose=True)  # doctest: +SKIP

    Capabilities:
        - 부문별 매출 시계열 산출(연간+분기 flow 구분). 10-K 비교연도 자동 포함.

    AIContext:
        US noteSeries(부문 구성)의 scan source. 런타임 reportSource 가
        edgar/scan/report/segments.parquet 을 직독.

    Guide:
        - 백필은 최신 stem 부터(터미널 선점등). 당월 stem 은 재실행 시 갱신분만 자연 반영.

    When:
        - 백필 runner(.github/scripts/sync/backfillEdgarSegments.py)·edgarSync 월별 스텝.

    How:
        - stem 별 downloadNotesBulk → segmentRowsFromZip → concat 후 keep=last dedup.

    Requires:
        - gather.edgar.notesBulk / gather.edgar.identity.loadTickers

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.report.proxyBuild.buildEdgarProxyReport` (proxy 4표 동형 트랙)
    """
    from dartlab.gather.edgar.identity import loadTickers
    from dartlab.gather.edgar.notesBulk import downloadNotesBulk

    tickers = loadTickers()
    cikToTicker = dict(zip(tickers["cik"].to_list(), tickers["ticker"].to_list()))
    frames: list[pl.DataFrame] = []
    for stem in stems:
        zp = downloadNotesBulk(stem)
        rows = segmentRowsFromZip(zp, cikToTicker, verbose=verbose)
        if rows:
            frames.append(pl.DataFrame(rows, schema=SEGMENTS_COLS))
    if not frames:
        return pl.DataFrame(schema=SEGMENTS_COLS)
    out = pl.concat(frames, how="vertical_relaxed")
    return out.unique(subset=["stockCode", "period", "flow", "segment"], keep="last").sort(
        ["stockCode", "period", "segment"]
    )


__all__ = ["SEGMENTS_COLS", "buildEdgarSegments", "segmentNameFromMember", "segmentRowsFromZip"]
