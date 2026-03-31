"""strategy 빌더 공통 유틸."""

from __future__ import annotations

import re
from dataclasses import dataclass

import polars as pl

_TRIANGLE_RE = re.compile(r"[△▲\u25B3\u25B2]")


def parseNumStr(s: str | None) -> float | None:
    """문자열 숫자를 float로 변환. 콤마, △(마이너스), % 처리."""
    if s is None:
        return None
    s = str(s).strip()
    if not s or s == "-":
        return None
    negative = False
    if _TRIANGLE_RE.match(s):
        negative = True
        s = _TRIANGLE_RE.sub("", s)
    s = s.replace(",", "").replace("%", "").strip()
    if not s:
        return None
    try:
        v = float(s)
        return -v if negative else v
    except ValueError:
        return None


def periodCols(df: pl.DataFrame) -> list[str]:
    """DataFrame에서 기간 컬럼만 추출 (최신 먼저)."""
    from dartlab.core.show import isPeriodColumn

    return [c for c in df.columns if isPeriodColumn(c)]


def annualCols(df: pl.DataFrame, maxYears: int = 8) -> list[str]:
    """연도 컬럼만 추출 (Q4 또는 연도)."""
    cols = periodCols(df)
    annual = [c for c in cols if "Q" not in c]
    if annual:
        return annual[:maxYears]
    return [c for c in cols if c.endswith("Q4")][:maxYears]


def quarterlyCols(df: pl.DataFrame, maxQuarters: int = 8) -> list[str]:
    """분기 컬럼만 추출 (최신 먼저)."""
    cols = periodCols(df)
    return [c for c in cols if "Q" in c][:maxQuarters]


def fetchNotesDetail(company, noteKeys: list[str]) -> dict[str, list[dict]]:
    """company.notes에서 noteKeys의 DataFrame을 dict 리스트로 반환.

    실패 시 해당 키를 건너뜀 (안전). to_dicts()로 즉시 변환하여
    DataFrame 참조를 해제.
    """
    result: dict[str, list[dict]] = {}
    notesAccessor = getattr(company, "_notesAccessor", None) or getattr(company, "notes", None)
    if notesAccessor is None:
        return result
    for key in noteKeys:
        try:
            df = getattr(notesAccessor, key, None)
            if df is not None and hasattr(df, "to_dicts"):
                result[key] = df.to_dicts()
        except (AttributeError, FileNotFoundError, ValueError, KeyError):
            pass
    return result


MAX_RATIO_YEARS = 8


def getRatioSeries(company) -> tuple[dict, list[str]] | None:
    """ratioSeries를 안전하게 가져온다."""
    try:
        result = company.finance.ratioSeries
        if result is None:
            return None
        return result
    except (ValueError, KeyError, AttributeError):
        return None


def buildTimeline(data: dict, field: str, years: list[str]) -> list[dict]:
    """시계열 데이터를 [{period, value}, ...] 형태로 변환."""
    vals = data.get("RATIO", {}).get(field, [])
    n = min(len(vals), len(years), MAX_RATIO_YEARS)
    if n == 0:
        return []
    return [{"period": years[i], "value": vals[i]} for i in range(len(years) - n, len(years))]


def mergeRows(primary: dict | None, fallback: dict | None) -> dict:
    """두 행을 merge. primary의 값이 None이면 fallback 값 사용."""
    if primary is None and fallback is None:
        return {}
    if primary is None:
        return fallback or {}
    if fallback is None:
        return primary
    merged = dict(primary)
    for k, v in fallback.items():
        if merged.get(k) is None and v is not None:
            merged[k] = v
    return merged


def getRatios(company):
    """ratios 객체를 안전하게 가져온다."""
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


def toDict(selectResult, maxPeriods: int = 0) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult → ({계정명: {period: val}}, periodCols).

    maxPeriods=0이면 전체 기간, >0이면 최신 N개만.
    """
    if selectResult is None:
        return None

    df = selectResult.df
    periods = sorted(periodCols(df), reverse=True)
    if maxPeriods > 0:
        periods = periods[:maxPeriods]
    if not periods:
        return None

    labelCol = "계정명" if "계정명" in df.columns else (df.columns[0] if df.columns else None)
    if labelCol is None:
        return None

    data: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        label = str(row.get(labelCol, ""))
        data[label] = {c: row.get(c) for c in periods}
    return (data, periods) if data else None


def toDictBySnakeId(selectResult, maxPeriods: int = 0) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult → ({snakeId: {period: val}}, periodCols).

    toDict와 동일하되, 키를 snakeId 컬럼으로 사용한다.
    snakeId로 select한 뒤 .get()도 snakeId로 접근할 때 사용.
    """
    if selectResult is None:
        return None

    df = selectResult.df
    periods = sorted(periodCols(df), reverse=True)
    if maxPeriods > 0:
        periods = periods[:maxPeriods]
    if not periods:
        return None

    idCol = "snakeId" if "snakeId" in df.columns else None
    if idCol is None:
        return toDict(selectResult, maxPeriods)

    data: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        sid = str(row.get(idCol, ""))
        data[sid] = {c: row.get(c) for c in periods}
    return (data, periods) if data else None


# ── basePeriod 인프라 ──

_QUARTER_RE = re.compile(r"^(\d{4})Q([1-4])$")
_YEAR_RE = re.compile(r"^(\d{4})$")


@dataclass(frozen=True)
class PeriodRange:
    """basePeriod로부터 결정된 분석 기간 범위."""

    basePeriod: str
    annualCols: list[str]
    quarterlyCols: list[str]


def _periodSortKey(p: str) -> str:
    """기간 문자열을 정렬 가능한 키로 변환. "2024" -> "2024Q5", "2024Q3" -> "2024Q3"."""
    if "Q" not in p:
        return p + "Q5"
    return p


def annualColsFromPeriods(
    periods: list[str],
    basePeriod: str | None = None,
    maxYears: int = 8,
) -> list[str]:
    """기간 목록에서 연간 컬럼 추출 — basePeriod 이하만.

    14개 파일의 _annualCols를 대체하는 통합 함수.
    연도("2024") 우선, 없으면 Q4("2024Q4") fallback.
    basePeriod=None이면 전체에서 최신 maxYears개.
    basePeriod="2022Q4"이면 2022Q4 이하에서 maxYears개.
    basePeriod="2022"이면 2022 이하 연도에서 maxYears개.
    """
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if not cols:
        cols = sorted([c for c in periods if c.endswith("Q4")], reverse=True)
    if basePeriod is not None:
        limit = _periodSortKey(basePeriod)
        cols = [c for c in cols if _periodSortKey(c) <= limit]
    return cols[:maxYears]


def annualLabel(period: str) -> str:
    """연간 기간 표시용 라벨. Q4 fallback 컬럼의 접미사를 제거한다.

    "2025Q4" -> "2025", "2025" -> "2025", "2025Q3" -> "2025Q3" (분기는 유지)
    """
    if period.endswith("Q4"):
        return period[:-2]
    return period


def annualLabels(periods: list[str]) -> dict[str, str]:
    """연간 기간 컬럼 → 표시 라벨 매핑. 테이블 렌더링에서 헤더 치환용."""
    return {p: annualLabel(p) for p in periods}


def quarterlyColsFromPeriods(
    periods: list[str],
    basePeriod: str | None = None,
    maxQuarters: int = 8,
) -> list[str]:
    """기간 목록에서 분기 컬럼 추출 — basePeriod 이하만."""
    qs = sorted([c for c in periods if "Q" in c], reverse=True)
    if basePeriod is not None:
        limit = _periodSortKey(basePeriod)
        qs = [c for c in qs if _periodSortKey(c) <= limit]
    return qs[:maxQuarters]


def resolveBasePeriod(
    company,
    basePeriod: str | None = None,
    maxYears: int = 8,
    maxQuarters: int = 8,
) -> PeriodRange:
    """basePeriod를 Company의 실제 기간으로 해석.

    basePeriod=None이면 최신 기간 자동 감지.
    ratioSeries 캐시를 활용하여 속도 우선.
    """
    rs = getRatioSeries(company)
    if rs is not None:
        _, allPeriods = rs
    else:
        allPeriods = []

    if basePeriod is None:
        qs = sorted([p for p in allPeriods if "Q" in p], reverse=True)
        resolved = qs[0] if qs else "9999Q4"
    else:
        resolved = basePeriod

    return PeriodRange(
        basePeriod=resolved,
        annualCols=annualColsFromPeriods(allPeriods, resolved, maxYears),
        quarterlyCols=quarterlyColsFromPeriods(allPeriods, resolved, maxQuarters),
    )
