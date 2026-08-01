"""story 블록 빌더 — calc* 결과(dict) → Block 리스트 변환.

analysis.financial 의 calc* 함수는 dict/숫자만 반환한다.
여기서 그 dict를 Block으로 조립한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.story.blocks import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.story.catalog import BlockMeta, getBlockMeta
from dartlab.story.narrate import (
    narrateCashFlow,
    narrateCashQuality,
    narrateConcentration,
    narrateDistress,
    narrateGrowth,
    narrateLeverage,
    narrateLifeCycle,
    narrateMargin,
    narrateROIC,
    narrateStoryPrecedents,
    narrateStrategy,
    narrateTechnicalVerdict,
    narrateValuation,
    narrateValuationSins,
)


def _meta(key: str) -> BlockMeta:
    """등록된 Story block metadata를 반환하고 catalog drift는 즉시 드러낸다."""

    meta = getBlockMeta(key)
    if meta is None:
        raise KeyError(f"등록되지 않은 Story block key: {key}")
    return meta


from dartlab.story.utils import unifyTableScale

# ── notes enrichment 렌더링 ──


def _notesDetailBlocks(data: dict, keyLabels: dict[str, str]) -> list:
    """notesDetail enrichment → TextBlock + TableBlock 리스트.

    calc 함수가 notesDetail 필드를 반환했을 때, 주석 테이블로 렌더링.
    notes accessor 는 원 단위로 노출되므로(`tableBuilder.buildTableDf`에서 정규화)
    추가 단위 변환 불필요.

    all-null row 제거 — parser 가 sub-row 헤더 (예: "OAT Nego", "Banker's Usance"
    등) 를 데이터 row 로 추출한 노이즈를 차단한다.
    """
    notesDetail = data.get("notesDetail")
    if not notesDetail:
        return []
    blocks: list = []
    for key, rows in notesDetail.items():
        if not rows:
            continue
        # all-null row (항목/snakeId 외 모든 값 None) 제거
        cleaned = []
        for row in rows:
            hasValue = any(
                v is not None and v != ""
                for k, v in row.items()
                if k not in ("항목", "snakeId", "account", "tag", "label")
            )
            if hasValue:
                cleaned.append(row)
        if not cleaned:
            continue
        label = keyLabels.get(key, key)
        try:
            blocks.append(TextBlock(f"▸ 주석: {label}", style="dim", indent="h2"))
            blocks.append(TableBlock("", pl.DataFrame(cleaned)))
        except (ValueError, TypeError):
            pass
    return blocks


_MAX_QUARTERS = 8


def _quarterlyRevenueTable(selectResult) -> TableBlock | None:
    """SelectResult → 최근 N분기 매출 TableBlock."""
    if selectResult is None:
        return None

    df = selectResult.df
    if isEmptyDf(df):
        return None

    # 기간 컬럼만 추출 (Q 포함)
    periodCols = [c for c in df.columns if "Q" in c]
    periodCols = sorted(periodCols, reverse=True)[:_MAX_QUARTERS]
    if not periodCols:
        return None

    labelCol = "항목" if "항목" in df.columns else df.columns[0]
    keepCols = [labelCol] + periodCols

    rows = []
    for row in df.select(keepCols).iter_rows(named=True):
        label = row[labelCol]
        rowDict = {"": label}
        for pc in periodCols:
            rowDict[pc] = row.get(pc)
        rows.append(rowDict)

    if not rows:
        return None

    unified = unifyTableScale(rows, "", periodCols, unit=_unitForCurrency())
    return TableBlock("분기별 매출", pl.DataFrame(unified))


import contextvars

_storyCurrency: contextvars.ContextVar[str] = contextvars.ContextVar("review_currency", default="KRW")


def _unitForCurrency() -> str:
    """현재 통화에 맞는 unifyTableScale unit 반환."""
    return "usd" if _storyCurrency.get() == "USD" else "won"


def _fmtAmtShort(value) -> str:
    """금액 간략 포맷 (KRW: 조/억, USD: B/M)."""
    if value is None or value == 0:
        return "-"
    absVal = abs(value)
    sign = "-" if value < 0 else ""
    if _storyCurrency.get() == "USD":
        if absVal >= 1_000_000_000:
            return f"{sign}${absVal / 1_000_000_000:.1f}B"
        if absVal >= 1_000_000:
            return f"{sign}${absVal / 1_000_000:.0f}M"
        return f"{sign}${absVal:,.0f}"
    if absVal >= 1_0000_0000_0000:
        return f"{sign}{absVal / 1_0000_0000_0000:.1f}조"
    if absVal >= 1_0000_0000:
        return f"{sign}{absVal / 1_0000_0000:.0f}억"
    return f"{sign}{absVal:,.0f}"


# ── 2부: 재무비율 분석 빌더 ──


def _extractSeries(data: dict, field: str) -> list[dict]:
    """history 기반 calc 결과에서 [{"period": p, "value": v}, ...] 추출."""
    history = data.get("history", [])
    if not history:
        return data.get(field, [])
    return [{"period": h["period"], "value": h.get(field)} for h in history if h.get(field) is not None]


def _timelineTable(
    specs: list[tuple[list[dict], str]],
    rowLabels: list[str],
) -> dict[str, list[str]] | None:
    """[{period, value}, ...] 시계열 → 행=지표, 열=기간 dict.

    specs: [(series, fmt), ...] -- series는 buildTimeline 결과, fmt는 f-string 포맷.
    rowLabels: 각 행 라벨 (specs와 동일 순서).
    반환: polars DataFrame으로 변환 가능한 dict. 기간 데이터 없으면 None.
    """
    cols: dict[str, list[str]] = {"": rowLabels}
    for idx, (series, fmt) in enumerate(specs):
        for item in series:
            period = item["period"]
            if period not in cols:
                cols[period] = ["-"] * len(rowLabels)
            v = item["value"]
            cols[period][idx] = fmt.format(v) if v is not None else "-"
    if len(cols) <= 1:
        return None
    return cols


_POSITIVE_KEYWORDS = ("안정", "건전", "양호", "우량", "순현금", "충분", "개선", "고성장")


def _flagsBlock(flags: list[str]) -> list:
    """플래그 리스트 → FlagBlock. 긍정/경고 자동 분류."""
    if not flags:
        return []
    warnings = []
    opportunities = []
    for f in flags:
        if any(kw in f for kw in _POSITIVE_KEYWORDS):
            opportunities.append(f)
        else:
            warnings.append(f)
    result = []
    if warnings:
        result.append(FlagBlock(warnings, kind="warning"))
    if opportunities:
        result.append(FlagBlock(opportunities, kind="opportunity"))
    return result


def _enrichedFlagsBlock(flags: list[str], enrichedFlags: list[dict] | None = None) -> list:
    """플래그 + enrichedFlags → FlagBlock. 정밀도 메타 포함."""
    if not flags:
        return []
    # EnrichedFlag 변환
    efList = None
    if enrichedFlags:
        from dartlab.story.blocks import EnrichedFlag

        efList = [
            EnrichedFlag(
                code=ef.get("code", ""),
                message=ef.get("message", ""),
                precision=ef.get("precision"),
                baseRate=ef.get("baseRate", ""),
                reference=ef.get("reference", ""),
                sectorNote=ef.get("sectorNote", ""),
            )
            for ef in enrichedFlags
        ]
        # enrichedFlags의 메시지에 정밀도 주석 추가
        {ef.get("code") for ef in enrichedFlags}
        augmented = []
        for f in flags:
            matched = next((ef for ef in enrichedFlags if ef.get("message") == f), None)
            if matched and matched.get("precision") is not None:
                p = matched["precision"]
                ref = matched.get("reference", "")
                note = matched.get("sectorNote", "")
                suffix = f" (정밀도 {p:.0%}, {ref})"
                if note:
                    suffix += f" [{note}]"
                augmented.append(f + suffix)
            else:
                augmented.append(f)
        flags = augmented

    warnings = []
    opportunities = []
    for f in flags:
        if any(kw in f for kw in _POSITIVE_KEYWORDS):
            opportunities.append(f)
        else:
            warnings.append(f)
    result = []
    if warnings:
        result.append(FlagBlock(warnings, kind="warning", enrichedFlags=efList))
    if opportunities:
        result.append(FlagBlock(opportunities, kind="opportunity"))
    return result


# ── 3부: 심화 분석 ──


def _historyTable(
    data: dict | None,
    fields: list[tuple[str, str, str]],
) -> dict[str, list[str]] | None:
    """history 기반 시계열 → 행=지표, 열=기간 dict.

    fields: [(key, rowLabel, fmt), ...] -- history item의 key, 행 라벨, 포맷.
    """
    if not data:
        return None
    history = data.get("history", [])
    if not history:
        return None

    rowLabels = [f[1] for f in fields]
    cols: dict[str, list[str]] = {"": rowLabels}
    for h in history:
        period = h["period"]
        vals = []
        for key, _, fmt in fields:
            v = h.get(key)
            if v is None:
                vals.append("-")
            elif fmt == "amt":
                vals.append(_fmtAmtShort(v))
            else:
                vals.append(fmt.format(v))
        cols[period] = vals
    return cols if len(cols) > 1 else None


def _tupleFlags(flags: list[tuple[str, str]]) -> list:
    """(message, kind) 튜플 리스트 -> FlagBlock(s)."""
    if not flags:
        return []
    warnings = [f for f, k in flags if k == "warning"]
    opportunities = [f for f, k in flags if k == "opportunity"]
    blocks: list = []
    if warnings:
        blocks.append(FlagBlock(warnings, kind="warning"))
    if opportunities:
        blocks.append(FlagBlock(opportunities, kind="opportunity"))
    return blocks


# ── 6-1 매출전망 빌더 ──


def _fmtEstimate(value: float | None, currency: str = "KRW") -> str:
    """추정치 포맷팅 (억원/M 단위)."""
    if value is None:
        return "-"
    if currency == "KRW":
        return f"{value / 1e8:,.0f}억(E)"
    return f"${value / 1e6:,.0f}M(E)"


def _hasMeta(key: str) -> bool:
    """catalog 에 해당 key 의 BlockMeta 가 있는지."""
    try:
        _meta(key)
        return True
    except (KeyError, AttributeError):
        return False


# ── Industry (L2) — 밸류체인 내 위치 ──


_STREAM_LABEL = {
    "upstream": "상류(upstream)",
    "midstream": "중류(midstream)",
    "downstream": "하류(downstream)",
}


__all__ = [
    "pl",
    "isEmptyDf",
    "FlagBlock",
    "HeadingBlock",
    "MetricBlock",
    "TableBlock",
    "TextBlock",
    "_meta",
    "narrateCashFlow",
    "narrateCashQuality",
    "narrateConcentration",
    "narrateDistress",
    "narrateGrowth",
    "narrateLeverage",
    "narrateLifeCycle",
    "narrateMargin",
    "narrateROIC",
    "narrateStoryPrecedents",
    "narrateStrategy",
    "narrateTechnicalVerdict",
    "narrateValuation",
    "narrateValuationSins",
    "unifyTableScale",
    "_notesDetailBlocks",
    "_MAX_QUARTERS",
    "_quarterlyRevenueTable",
    "contextvars",
    "_storyCurrency",
    "_unitForCurrency",
    "_fmtAmtShort",
    "_extractSeries",
    "_timelineTable",
    "_POSITIVE_KEYWORDS",
    "_flagsBlock",
    "_enrichedFlagsBlock",
    "_historyTable",
    "_tupleFlags",
    "_fmtEstimate",
    "_hasMeta",
    "_STREAM_LABEL",
]
