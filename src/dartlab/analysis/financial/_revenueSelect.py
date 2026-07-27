"""revenue.py 의 docs/select 헬퍼 + 공유 상수.

revenue.py facade + _revenueSegment / _revenueGrowth / _revenueQuality 가 본 모듈을 import.
순환 import 방지를 위해 _revenueComposition 는 함수 내부에서 deferred import.
"""

from __future__ import annotations

import re

from dartlab.core.utils.helpers import (
    parseNumStr as _parseNumStr,
)
from dartlab.core.utils.helpers import (
    toDictBySnakeId as _toDictBySnakeId,
)

# 영업부문 axisPath/라벨 파싱 SSOT 는 panel(L1) 로 이관 — 본 모듈은 하향 재사용(L2→L1).
from dartlab.providers.dart.panel.cell import _isRevenueLabel, _segNameFromAxis

_MAX_SEGMENTS = 8
_MAX_YEARS = 8

_SKIP_KEYWORDS = {"합계", "조정", "내부", "소계", "총계", "부문계", "기타", "국내외"}

# 부문 주석 단위 추론 실패 시 fallback 배율 (백만원 = build.cell._UNIT_SCALE 기본).
_NOTE_UNIT_SCALE = 1_000_000


def _getRatios(company):
    """ratios 객체 (RatioResult) 를 안전하게 가져온다 — internal 사용.

    Returns
    -------
    RatioResult | None
        회사의 재무비율 객체. 데이터 없으면 None.
    """
    try:
        return company._getRatiosInternal()
    except (ValueError, KeyError, AttributeError):
        return None


def _isRevenueForYear(company, year4: str) -> float | None:
    """IS 매출(원) — 단위 추론 기준값. year4 = "YYYY"."""
    try:
        parsed = _toDictBySnakeId(company.select("IS", ["매출액"], strict=False))
    except (ValueError, KeyError, AttributeError):
        return None
    if not parsed:
        return None
    data, _ = parsed
    row = data.get("sales") or data.get("매출액") or {}
    for k, v in row.items():
        m = re.search(r"(\d{4})", str(k))
        if v and m and m.group(1) == year4:
            return v
    return None


def _inferSegUnitScale(company, cells) -> int:
    """부문 주석 raw → 원 배율 추론. 노트 단위가 회사마다 백만원/천원/원으로 달라 magnitude 로 결정.

    최신연도 부문 매출 합 raw × scale 이 IS 총매출의 0.3~5 배(부문합은 내부거래로 연결매출 ±) 면 채택.
    미추론 = 백만원 (codebase 기본).
    """
    revByYear: dict[int, float] = {}
    for r in cells.iter_rows(named=True):
        if (r.get("scope") or "consolidated") != "consolidated":
            continue
        if not _segNameFromAxis(r.get("axisPath")):
            continue
        if not _isRevenueLabel(str(r.get("label") or "")):
            continue
        year, val = r.get("ctxYear"), _parseNumStr(r.get("valueRaw"))
        if year is not None and val and val > 0:
            revByYear[int(year)] = revByYear.get(int(year), 0.0) + val
    if not revByYear:
        return _NOTE_UNIT_SCALE
    ly = max(revByYear)
    rawSum = revByYear[ly]
    totalRev = _isRevenueForYear(company, str(ly))
    if not totalRev or rawSum <= 0:
        return _NOTE_UNIT_SCALE
    for sc in (1, 1_000, 1_000_000):
        if 0.3 <= rawSum * sc / totalRev <= 5:
            return sc
    return _NOTE_UNIT_SCALE


def _segmentSeriesFromNote(
    company, kind: str, *, basePeriod: str | None = None
) -> tuple[dict[str, dict[str, float]], list[str]] | None:
    """NT_D871100(부문별정보) 주석 셀 → ``{부문: {연도: 값(원)}}`` + 연도목록.

    구 ``productService``/``salesOrder`` select 경로는 ``showImpl`` finance-only dispatch 로
    항상 None (사망) 이므로, panel 주석 셀(``_noteCellsFromPanel``) 의 ``axisPath`` 부문멤버를
    피벗한다. **축-태깅(OperatingSegmentsMember) 회사만** — 행-라벨/지역별/자회사별/단일축/
    EDGAR(US) 는 None (정직). 노트 단위(백만원/천원)는 IS 매출 대비 magnitude 로 추론 → 원 환산.

    Args:
        company: Company 객체.
        kind: "revenue"(매출/수익) | "opincome"(영업이익/영업손익).
        basePeriod: 기준 연도 — 이후 연도 제외. None 시 전체.

    Returns:
        ``(segData, years)`` 또는 None. segData = ``{부문: {"YYYY": 값(원)}}``,
        years = 최신순 연도 문자열 목록.
    """
    if getattr(company, "market", "KR") != "KR":
        return None  # EDGAR(US) = segment XBRL dimension 부재
    code = getattr(company, "stockCode", None)
    if not code:
        return None
    from dartlab.providers.dart.panel.cell import _noteCellsFromPanel

    cells = _noteCellsFromPanel(code, "NT_D871100")
    if cells is None or not hasattr(cells, "is_empty") or cells.is_empty():
        return None

    scale = _inferSegUnitScale(company, cells)  # 매출·영업이익 동일 단위
    baseYear = None
    if basePeriod:
        m = re.search(r"(\d{4})", str(basePeriod))
        baseYear = int(m.group(1)) if m else None

    segData: dict[str, dict[str, float]] = {}
    for r in cells.iter_rows(named=True):
        if (r.get("scope") or "consolidated") != "consolidated":
            continue
        seg = _segNameFromAxis(r.get("axisPath"))
        if not seg:
            continue
        label = str(r.get("label") or "")
        if kind == "revenue":
            if not _isRevenueLabel(label):
                continue
        elif "영업이익" not in label and "영업손익" not in label:
            continue
        year = r.get("ctxYear")
        if year is None or (baseYear is not None and int(year) > baseYear):
            continue
        val = _parseNumStr(r.get("valueRaw"))
        if val is None:
            continue
        val *= scale
        if kind == "revenue" and val <= 0:
            continue
        ys = str(year)
        cur = segData.setdefault(seg, {})
        if ys not in cur or abs(val) > abs(cur[ys]):  # (부문,연도) 중복 시 전체 연간(절대값 큰 값)
            cur[ys] = val

    if not segData:
        return None
    years = sorted({y for vals in segData.values() for y in vals}, reverse=True)[:_MAX_YEARS]
    return segData, years


def _selectDocsRevenue(
    company, *, basePeriod: str | None = None
) -> tuple[dict[str, dict[str, float]], list[str]] | None:
    """부문별 매출 시계열 — NT_D871100 주석 셀(축-태깅) axisPath 피벗.

    축-태깅 DART 회사만 (``_segmentSeriesFromNote`` 위임). 행-라벨/지역/자회사/단일축/EDGAR = None.

    Returns:
        ``(segData={부문:{"YYYY":매출(원)}}, years)`` 또는 None.
    """
    return _segmentSeriesFromNote(company, "revenue", basePeriod=basePeriod)


def _selectDocsOpIncome(company, yCols: list[str]) -> dict[str, dict[str, float]] | None:
    """부문별 영업이익 시계열 — NT_D871100 주석 셀 (매출 yCols 정합).

    Returns:
        ``{부문: {"YYYY": 영업이익(원)}}`` 또는 None.
    """
    res = _segmentSeriesFromNote(company, "opincome")
    if res is None:
        return None
    opData, _ = res
    if yCols:  # 매출 연도에 맞춰 필터 (계약 유지)
        opData = {seg: {y: v for y, v in vals.items() if y in yCols} for seg, vals in opData.items()}
        opData = {seg: vals for seg, vals in opData.items() if vals}
    return opData or None


def _selectDocsSalesOrder(company, keyword: str | None = None):
    """salesOrder에서 항목별 매출 시계열을 추출.

    Returns
    -------
    SelectResult | None
        select() 결과 객체. 데이터 없으면 None.
    """
    if keyword:
        result = company.select("salesOrder", [keyword])
    else:
        result = company.select("salesOrder", colList=None)
    if result is None:
        return None
    return result
