"""멀티팩터 스크리닝 -- 여러 축 조합으로 종목 필터링.

프리셋:
    value       -- 가치투자 후보 (저PBR + 이익 양호 + 부채 안전)
    dividend    -- 배당 성장 우량주 (연속증가/안정 + 부채 안전)
    growth      -- 균형 성장주 (고성장 + 수익 우수 + 이익 양호)
    risk        -- 위험 기업 (부채 고위험 OR 감사 고위험 OR 유동성 위험)
    quality     -- 퀄리티 팩터 (수익 우수 + 이익 우수 + 효율 우수)
    all         -- 전 프리셋 플래그 통합

사용법::

    dartlab.scan("screen")              # 프리셋 목록
    dartlab.scan("screen", "value")     # 가치투자 후보
    dartlab.scan("screen", "risk")      # 위험 기업
    dartlab.scan("screen", "all")       # 전체 플래그 통합
"""

from __future__ import annotations

import polars as pl

_PRESETS = {
    "value": "가치투자 후보 (저PBR + 이익 양호 + 부채 안전)",
    "dividend": "배당 성장 우량주 (연속증가/안정 + 부채 안전)",
    "growth": "균형 성장주 (고성장 + 수익 우수 + 이익 양호)",
    "risk": "위험 기업 (부채 고위험 OR 감사 고위험 OR 유동성 위험)",
    "quality": "퀄리티 팩터 (수익 우수 + 이익 우수 + 효율 우수)",
    "all": "전 프리셋 플래그 통합",
}


def _loadAxis(name: str) -> pl.DataFrame:
    """scan 축 로드 (lazy import)."""
    import dartlab

    return dartlab.scan(name)


def _screenValue() -> pl.DataFrame:
    """가치투자 후보: 저PBR + 이익 양호+ + 부채 안전/관찰."""
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")
    debt = _loadAxis("debt")
    val = _loadAxis("valuation")

    goodProf = set(prof.filter(pl.col("등급").is_in(["우수", "양호", "보통"]))["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())
    lowPbr = set(
        val.filter((pl.col("PBR").is_not_null()) & (pl.col("PBR") > 0) & (pl.col("PBR") < 0.7))["종목코드"].to_list()
    )

    codes = goodProf & goodQual & safeDbt & lowPbr
    return val.filter(pl.col("종목코드").is_in(list(codes))).sort("PBR")


def _screenDividend() -> pl.DataFrame:
    """배당 성장 우량주: 연속증가/안정/증가 + 부채 안전/관찰."""
    div = _loadAxis("dividendTrend")
    debt = _loadAxis("debt")

    goodDiv = set(div.filter(pl.col("패턴").is_in(["연속증가", "안정", "증가"]))["종목코드"].to_list())
    safeDbt = set(debt.filter(pl.col("위험등급").is_in(["안전", "관찰"]))["종목코드"].to_list())

    codes = goodDiv & safeDbt
    return div.filter(pl.col("종목코드").is_in(list(codes))).sort("DPS성장", descending=True, nulls_last=True)


def _screenGrowth() -> pl.DataFrame:
    """균형 성장주: 고성장 + 수익 양호+ + 이익 양호+."""
    growth = _loadAxis("growth")
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")

    highGrowth = set(growth.filter(pl.col("등급").is_in(["고성장", "성장"]))["종목코드"].to_list())
    goodProf = set(prof.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())

    codes = highGrowth & goodProf & goodQual
    return growth.filter(pl.col("종목코드").is_in(list(codes))).sort("매출CAGR", descending=True, nulls_last=True)


def _screenRisk() -> pl.DataFrame:
    """위험 기업: 부채 고위험 OR 감사 고위험/주의 OR 유동성 위험."""
    debt = _loadAxis("debt")
    audit = _loadAxis("audit")
    liq = _loadAxis("liquidity")

    debtRisk = set(debt.filter(pl.col("위험등급") == "고위험")["종목코드"].to_list())
    auditRisk = set(audit.filter(pl.col("위험등급").is_in(["고위험", "주의"]))["종목코드"].to_list())
    liqRisk = set(liq.filter(pl.col("등급") == "위험")["종목코드"].to_list())

    allRisk = debtRisk | auditRisk | liqRisk

    rows: list[dict] = []
    for code in allRisk:
        flags = []
        if code in debtRisk:
            flags.append("부채")
        if code in auditRisk:
            flags.append("감사")
        if code in liqRisk:
            flags.append("유동성")
        rows.append({"종목코드": code, "위험플래그": "+".join(flags), "위험수": len(flags)})

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).sort("위험수", descending=True)


def _screenQuality() -> pl.DataFrame:
    """퀄리티 팩터: 수익 우수 + 이익 우수/양호 + 효율 우수/양호."""
    prof = _loadAxis("profitability")
    qual = _loadAxis("quality")
    eff = _loadAxis("efficiency")

    goodProf = set(prof.filter(pl.col("등급") == "우수")["종목코드"].to_list())
    goodQual = set(qual.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())
    goodEff = set(eff.filter(pl.col("등급").is_in(["우수", "양호"]))["종목코드"].to_list())

    codes = goodProf & goodQual & goodEff
    return prof.filter(pl.col("종목코드").is_in(list(codes))).sort("ROE", descending=True, nulls_last=True)


def _screenAll() -> pl.DataFrame:
    """전 프리셋 플래그 통합 — 종목별로 어떤 프리셋에 해당하는지."""
    value = set(_screenValue()["종목코드"].to_list()) if not _screenValue().is_empty() else set()
    dividend = set(_screenDividend()["종목코드"].to_list()) if not _screenDividend().is_empty() else set()
    growth = set(_screenGrowth()["종목코드"].to_list()) if not _screenGrowth().is_empty() else set()
    risk = set(_screenRisk()["종목코드"].to_list()) if not _screenRisk().is_empty() else set()
    quality = set(_screenQuality()["종목코드"].to_list()) if not _screenQuality().is_empty() else set()

    allCodes = value | dividend | growth | risk | quality
    rows: list[dict] = []
    for code in allCodes:
        flags = []
        if code in value:
            flags.append("value")
        if code in dividend:
            flags.append("dividend")
        if code in growth:
            flags.append("growth")
        if code in quality:
            flags.append("quality")
        if code in risk:
            flags.append("risk")
        rows.append({"종목코드": code, "프리셋": "+".join(flags), "프리셋수": len(flags)})

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).sort("프리셋수", descending=True)


_DISPATCH = {
    "value": _screenValue,
    "dividend": _screenDividend,
    "growth": _screenGrowth,
    "risk": _screenRisk,
    "quality": _screenQuality,
    "all": _screenAll,
}


def scanScreen(target: str | None = None, *, verbose: bool = True) -> pl.DataFrame:
    """멀티팩터 스크리닝.

    target 없으면 프리셋 목록 반환. target 지정하면 해당 프리셋 실행.
    """
    if target is None:
        rows = [{"preset": k, "description": v} for k, v in _PRESETS.items()]
        return pl.DataFrame(rows)

    key = target.lower().strip()
    if key not in _DISPATCH:
        available = ", ".join(_PRESETS.keys())
        raise ValueError(f"알 수 없는 screen 프리셋: '{target}'. 가용: {available}")

    if verbose:
        print(f"screen({key}): 실행 중...")
    result = _DISPATCH[key]()
    if verbose:
        print(f"screen({key}): {result.shape[0]}종목")
    return result


__all__ = ["scanScreen"]
