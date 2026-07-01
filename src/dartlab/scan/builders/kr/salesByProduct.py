"""KR scan 사업부문 매출구성 builder (panel 매출및수주 표 SSOT).

Capabilities:
    - 전 상장사 사업보고서 "매출 및 수주상황" 표에서 사업부문별 매출 leaf 행을 합산해
      부문 mix (비중), 집중도(HHI), 다각화 등급을 종목당 1 행으로 통합한다.

Args:
    Public entry points accept write/output/incremental and logging options.

Returns:
    Generated ``salesByProduct.parquet`` path or the in-memory DataFrame.

Example:
    >>> from dartlab.scan.builders.kr.salesByProduct import buildSalesByProductSafe
    >>> p = buildSalesByProductSafe(verbose=True)

Guide:
    절대 매출은 finance scan (단위·통화 정규화됨) 이 SSOT 다. 본 축은 **단위-불변** 신호
    (부문 비중·집중도) 만 낸다. 회사별 원표 렌더는 터미널 businessTables 가 담당한다.

SeeAlso:
    ``scan.builders.kr.shares`` (동일 panel 순회 패턴) · ``scan.salesByProduct`` (런타임 reader)
    · ``providers.dart.panel.text.parsePanelXmlTables`` (rowspan/colspan 격자전개).

Requires:
    panel artifact (``providers.dart.panel.text`` SSOT). 네트워크 미사용 (offline 안전).

AIContext:
    ``scan("salesByProduct")`` 축의 prebuild source. 회사별 panel 파싱은 콜드 read·OOM
    비용이 커 런타임 불가하므로 prebuild consolidation 으로 종목당 1 행을 굽는다.

LLM Specifications:
    AntiPatterns: 절대 매출 cross-company 비교 금지 (단위 이질). read-time panel 파싱 금지.
    OutputSchema: ``salesByProduct.parquet`` (종목당 1 행, 부문 mix·집중도).
    Prerequisites: 로컬 ``data/dart/panel/{code}.parquet`` (Data Sync/HF 다운로드).
    Freshness: 매 scan prebuild 사이클 재빌드.
    Dataflow: panel 매출및수주 표 -> leaf 부문 합산 -> 비중/HHI -> 종목당 1 행 parquet.
    TargetMarkets: KR DART 정기보고서.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.scan.builders.kr.common import mergeIncremental as _mergeIncremental
from dartlab.scan.builders.kr.common import panelDir as _panelDir
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir

# 부문별 매출 표 거처. 회사마다 "매출및수주상황"(조선·제약) 또는 "주요 제품 및 서비스"(삼성)
# 섹션에 산다. 주석(주석/재무제표) 섹션은 XBRL 영업부문 표라 구조가 달라 제외한다.
_SECTION_PATTERN = r"수주|주요\s*제품|주요\s*서비스"
# 총계·소계 행 마커. 바 "계" (매출및수주 표의 흔한 열 라벨) 는 제외하고 합계/총계/소계/부문 계만.
_TOTAL_RE = re.compile(r"합\s*계|총\s*계|소\s*계|부문\s*계|전\s*체|매출\s*총계")
# 값 열 헤더에서 배제할 파생 열 (행 총계·비중·증감).
_NONVALUE_HDR_RE = re.compile(r"합계|총계|소계|비중|구성비|증감|%|점유")
# 기간 헤더 토큰 (제N기·연도·분기·반기·당기/전기). 값 열·헤더 행 식별 SSOT.
_PERIOD_TOKEN_RE = re.compile(r"제\d+기|19\d{2}|20\d{2}|분기|반기|당기|전기|전전기|기말|당반기")
# 사업부문 표 식별 (헤더에 부문 표기).
_SEGMENT_HDR_RE = re.compile(r"부\s*문")
# 매출실적 표 판별자. "매출유형" 열은 정규 매출실적 표(삼성·조선·제약·LG)의 지문이다.
# 현대차 판매대수 표(헤더 "사업부문|구분|구분")처럼 매출 아닌 표를 배제한다.
_SALES_HDR_RE = re.compile(r"매출유형|매출실적|매출액")

_SBP_COLUMNS = [
    "stockCode",
    "period",
    "nSegments",
    "topSegment",
    "topSharePct",
    "hhi",
    "grade",
    "topSegmentTrend",
    "segments",
    "source",
]
_SBP_SCHEMA = {
    "stockCode": pl.Utf8,
    "period": pl.Utf8,
    "nSegments": pl.Int32,
    "topSegment": pl.Utf8,
    "topSharePct": pl.Float64,
    "hhi": pl.Float64,
    "grade": pl.Utf8,
    "topSegmentTrend": pl.Float64,
    "segments": pl.Utf8,
    "source": pl.Utf8,
}


def _collapse(text: str | None) -> str:
    """공백 전부 제거 (한글 표의 자간 공백 "부 문" -> "부문")."""
    return re.sub(r"\s+", "", text or "")


def _num(cell: str | None) -> float | None:
    """매출 셀(콤마·공백·삼각형 음수) -> float. 비숫자·빈칸·'-'는 None."""
    s = (cell or "").strip()
    if not s or s in {"-", "－"}:
        return None
    neg = s[0] in {"△", "▲", "(", "-", "−"} or s.endswith(")")
    digits = re.sub(r"[^\d.]", "", s)
    if not digits or digits == ".":
        return None
    try:
        val = float(digits)
    except ValueError:
        return None
    return -val if neg else val


def _scanGrid(grid: list[list[str]]) -> tuple[str, list[int], list[list[str]]] | None:
    """격자 -> (headerText, valueCols, dataRows). 기간 헤더가 없으면 None.

    헤더 행은 기간 토큰(제N기·연도·분기 등)을 담은 행으로 명시 식별한다. 연도 헤더
    ("2024년")가 ``_num`` 으로 숫자 파싱돼 데이터 행으로 오인되는 것을 막는다.
    valueCols: 헤더 행에서 기간 토큰을 가진 열 (좌->우 = 최신 먼저). 총계/비중 파생은 배제.
    dataRows: 헤더 행 아래, col0 이 비지 않은 행.
    headerText: 헤더 행 포함 상단 전체 (부문 표 식별용, 공백 제거).
    """
    if not grid:
        return None
    ncol = max((len(r) for r in grid), default=0)
    if ncol < 2:
        return None
    padded = [list(r) + [""] * (ncol - len(r)) for r in grid]

    # 첫 4 행 중 기간 토큰을 담은 마지막 행 = 헤더 행 (다단 헤더면 아래쪽).
    headerIdx = -1
    for i in range(min(4, len(padded))):
        if any(_PERIOD_TOKEN_RE.search(_collapse(c)) for c in padded[i]):
            headerIdx = i
    if headerIdx < 0:
        return None

    headerRow = padded[headerIdx]
    valueCols = [
        c
        for c in range(1, ncol)
        if _PERIOD_TOKEN_RE.search(_collapse(headerRow[c])) and not _NONVALUE_HDR_RE.search(_collapse(headerRow[c]))
    ]
    if not valueCols:
        return None

    dataRows = [r for r in padded[headerIdx + 1 :] if r[0].strip()]
    if not dataRows:
        return None

    headerText = _collapse(" ".join(padded[j][k] for j in range(headerIdx + 1) for k in range(ncol)))
    return headerText, valueCols, dataRows


def _looksLikeSalesTable(grid: list[list[str]]) -> bool:
    """헤더에 '부문' + '매출유형(매출실적)' 지문이 있는 정규 매출실적 표인지.

    매출유형 요건으로 판매대수·가격·수주잔고 표를 배제한다 (매출 아닌 값 혼입 방지).
    """
    scanned = _scanGrid(grid)
    if scanned is None:
        return False
    headerText, _valueCols, _dataRows = scanned
    return bool(_SEGMENT_HDR_RE.search(headerText)) and bool(_SALES_HDR_RE.search(headerText))


def _numericDensity(grid: list[list[str]]) -> int:
    """격자의 숫자 셀 개수 (본문 표 선호용 밀도 점수)."""
    return sum(1 for row in grid for cell in row if _num(cell) is not None)


def _pickSalesTable(grids: list[list[list[str]]]) -> list[list[str]] | None:
    """수주 섹션 표들 중 사업부문 매출 표 (부문 헤더 + 최고 숫자밀도) 하나 선택."""
    candidates = [g for g in grids if _looksLikeSalesTable(g)]
    if not candidates:
        return None
    return max(candidates, key=_numericDensity)


def _sumLeafSegments(dataRows: list[list[str]], valueCol: int, firstVal: int) -> dict[str, float]:
    """총계 마커 없는 leaf 행만 col0 부문으로 합산 (부문 계·합계 행 자동 배제).

    삼성 DS 부문(반도체+DP+기타) 처럼 하위행이 있으면 leaf 만 더해 부문 계와 일치하고,
    조선(수출+국내) 처럼 합계 행이 있으면 leaf 만 더해 이중계상을 피한다.
    """
    seg: dict[str, float] = {}
    for r in dataRows:
        textCells = r[:firstVal]
        if any(_TOTAL_RE.search(_collapse(c)) for c in textCells):
            continue
        name = _collapse(r[0])
        if not name:
            continue
        val = _num(r[valueCol]) if valueCol < len(r) else None
        if val is None:
            continue
        seg[name] = seg.get(name, 0.0) + val
    return seg


def _grade(nSegments: int, hhi: float) -> str:
    """부문 수·HHI -> 다각화 등급 (단위-불변)."""
    if nSegments <= 1:
        return "단일사업"
    if hhi >= 0.6:
        return "집중"
    if hhi >= 0.4:
        return "주력집중"
    if hhi >= 0.25:
        return "균형"
    return "분산"


def _concentration(grid: list[list[str]]) -> dict | None:
    """사업부문 매출 표 격자 -> 부문 mix·집중도 지표 dict. 부적격이면 None.

    Args:
        grid: rowspan/colspan 격자전개된 매출및수주 표 (parsePanelXmlTables 산출).

    Returns:
        {nSegments, topSegment, topSharePct, hhi, grade, topSegmentTrend, segments}
        또는 양수 부문 매출이 없으면 None.

    Raises:
        없음.
    """
    scanned = _scanGrid(grid)
    if scanned is None:
        return None
    _headerText, valueCols, dataRows = scanned
    firstVal = min(valueCols)
    latestCol = valueCols[0]
    prevCol = valueCols[1] if len(valueCols) > 1 else None

    segLatest = _sumLeafSegments(dataRows, latestCol, firstVal)
    positives = {k: v for k, v in segLatest.items() if v > 0}
    total = sum(positives.values())
    if not positives or total <= 0:
        return None

    shares = {k: v / total for k, v in positives.items()}
    topSegment = max(shares, key=lambda k: shares[k])
    topShare = shares[topSegment]
    hhi = round(sum(s * s for s in shares.values()), 4)

    topSegmentTrend: float | None = None
    if prevCol is not None:
        segPrev = _sumLeafSegments(dataRows, prevCol, firstVal)
        prevPos = {k: v for k, v in segPrev.items() if v > 0}
        prevTotal = sum(prevPos.values())
        if prevTotal > 0 and topSegment in prevPos:
            prevShare = prevPos[topSegment] / prevTotal
            topSegmentTrend = round((topShare - prevShare) * 100, 1)

    ranked = sorted(shares.items(), key=lambda kv: kv[1], reverse=True)[:5]
    segments = "|".join(f"{name}:{round(sh * 100)}%" for name, sh in ranked)

    return {
        "nSegments": len(positives),
        "topSegment": topSegment,
        "topSharePct": round(topShare * 100, 1),
        "hhi": hhi,
        "grade": _grade(len(positives), hhi),
        "topSegmentTrend": topSegmentTrend,
        "segments": segments,
    }


def extractSalesByProduct(code: str) -> dict | None:
    """한 종목 panel 매출및수주 표 -> 부문 mix·집중도 dict. 데이터 없으면 None.

    Args:
        code: 6 자리 종목코드.

    Returns:
        _SBP_COLUMNS 스키마 dict (stockCode·period·source 포함) 또는 None.

    Raises:
        없음 (panel 부재·파싱 실패는 None 으로 흡수).

    Example:
        >>> extractSalesByProduct("005930")  # doctest: +SKIP
    """
    from dartlab.providers.dart.panel.text import panelTextRows, parsePanelXmlTables

    texts = panelTextRows(code)
    if texts is None or texts.is_empty() or "sectionLeaf" not in texts.columns:
        return None
    sub = texts.filter(pl.col("sectionLeaf").str.contains(_SECTION_PATTERN))
    if sub.is_empty() or "contentRaw" not in sub.columns:
        return None

    periods = sorted(p for p in sub["period"].unique().to_list() if p)
    if not periods:
        return None
    annual = [p for p in periods if p.endswith("Q4")]
    target = annual[-1] if annual else periods[-1]

    prows = sub.filter(pl.col("period") == target)
    grids: list[list[list[str]]] = []
    for content in prows["contentRaw"].to_list():
        if content and "<TR" in content:
            grids.extend(parsePanelXmlTables(content))
    table = _pickSalesTable(grids)
    if table is None:
        return None
    metrics = _concentration(table)
    if metrics is None:
        return None
    metrics["stockCode"] = code
    metrics["period"] = target
    metrics["source"] = "panel:salesOrder"
    return metrics


def buildSalesByProductScan(
    *, write: bool = True, outputPath: "str | Path | None" = None, incremental: bool = False
) -> pl.DataFrame:
    """전 종목 panel 사업부문 매출구성 scan (panel 매출및수주 표 SSOT).

    Args:
        write: True 면 ``salesByProduct.parquet`` 저장.
        outputPath: 출력 경로. None 이면 ``data/dart/scan/salesByProduct.parquet``.
        incremental: True 면 로컬 panel dir(=변경 종목만 seed) 재계산 행을 기존 parquet 에
            ``stockCode`` 단위로 갈아끼운다 (:func:`mergeIncremental`).

    Returns:
        종목당 1 행 부문 mix DataFrame (_SBP_SCHEMA).

    Raises:
        FileNotFoundError: panel 디렉토리 부재.
        RuntimeError: 추출 결과 0 건.

    Example:
        >>> buildSalesByProductScan(write=False)  # doctest: +SKIP
    """
    panelRoot = _panelDir()
    if not panelRoot.exists():
        raise FileNotFoundError(f"panel 디렉토리 없음: {panelRoot}")
    codes = sorted(p.stem for p in panelRoot.glob("*.parquet"))
    records: list[dict] = []
    for code in codes:
        try:
            metrics = extractSalesByProduct(code)
        except (pl.exceptions.PolarsError, OSError, ValueError):
            metrics = None
        if metrics is not None:
            records.append(metrics)
        if len(codes) and (codes.index(code) + 1) % 200 == 0:
            _releaseNativeMemory()
    if not records:
        raise RuntimeError("사업부문 매출구성 추출 결과 0 건")

    out = pl.DataFrame(records, schema_overrides=_SBP_SCHEMA, infer_schema_length=None).select(_SBP_COLUMNS)
    out = out.sort("stockCode")
    if write:
        if outputPath is None:
            outputPath = _scanDir() / "salesByProduct.parquet"
        outputPath = Path(outputPath)
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        if incremental and outputPath.exists():
            _mergeIncremental(outputPath, out, key="stockCode")
        else:
            out.write_parquet(str(outputPath), compression="zstd")
    _releaseNativeMemory()
    return out


def buildSalesByProductSafe(*, verbose: bool = True, incremental: bool = False) -> Path | None:
    """사업부문 매출구성 풀 빌드 (실패해도 전체 scan 진행).

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.
    incremental : bool
        True 면 변경 종목만 재계산해 기존 parquet 에 ``stockCode`` 단위로 머지.

    Returns
    -------
    Path | None
        생성된 salesByProduct.parquet 경로. 실패 시 None.

    Raises
    ------
    없음 (선택 산출물이라 알려진 실패를 흡수).

    Examples
    --------
    >>> buildSalesByProductSafe(verbose=False) is None
    True

    Capabilities:
        부문 매출구성 산출물을 optional step 으로 만들어, 실패해도 finance/report 등 핵심
        scan 산출물 빌드를 막지 않는다.

    AIContext:
        ``buildScan`` 이 shares 다음 단계로 호출한다. ``scan("salesByProduct")`` 축의 source.

    Guide:
        보호 wrapper 다. 실제 계산은 :func:`buildSalesByProductScan` 가 담당한다.

    When:
        매 scan prebuild 사이클 (KST 03:00 / 15:00), shares 빌드 직후.

    How:
        :func:`buildSalesByProductScan` 실행 후 알려진 런타임/파일 오류를 None 으로 변환한다.

    Requires:
        panel artifact (``providers.dart.panel.text`` SSOT).

    SeeAlso:
        :func:`dartlab.scan.builders.kr.core.buildScan`.
    """
    try:
        if verbose:
            mode = "증분" if incremental else "full"
            _say(f"[salesByProduct] 사업부문 매출구성 {mode} 빌드 시작 (panel 매출및수주 표 SSOT)")
        df = buildSalesByProductScan(incremental=incremental)
        if verbose:
            _say(f"[salesByProduct] 완료: {df.height}종목")
        return _scanDir() / "salesByProduct.parquet"
    except (FileNotFoundError, RuntimeError, OSError, ValueError, pl.exceptions.PolarsError) as exc:
        if verbose:
            _say(f"[salesByProduct] 실패: {exc}")
        return None


__all__ = [
    "buildSalesByProductSafe",
    "buildSalesByProductScan",
    "extractSalesByProduct",
]
