"""Altman 부실위험 판별 점수 횡단면.

상장 전종목 기본값은 비금융사에 동일한 Z'' 모형을 적용한다. 원본 Z는 제조업
상장사와 같은 회계연도 말 시가총액이 모두 확인된 경우에만 명시적으로 선택할 수
있다. 데이터 결손을 이유로 Z, Z', Z'' 사이를 자동 전환하지 않는다.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Any

import polars as pl

from dartlab.core.market import detectMarket
from dartlab.quant.factor.build import _fetchYearEndMarketcaps, _latestYear
from dartlab.quant.screen.dataAccess import extractAccount, loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)

_VARIANTS = {"auto", "z", "zpp"}
_Z_COEFFICIENTS = {
    "workingCapitalToAssets": 1.2,
    "retainedEarningsToAssets": 1.4,
    "ebitToAssets": 3.3,
    "marketEquityToLiabilities": 0.6,
    "salesToAssets": 1.0,
}
_ZPP_COEFFICIENTS = {
    "workingCapitalToAssets": 6.56,
    "retainedEarningsToAssets": 3.26,
    "ebitToAssets": 6.72,
    "bookEquityToLiabilities": 1.05,
}
_THRESHOLDS = {
    "z": {"distressBelow": 1.81, "safeAbove": 2.99},
    "zpp": {"distressBelow": 1.1, "safeAbove": 2.6},
}
_US_FINANCIAL_TYPES = {"banks", "credit", "securities", "insurance", "holding_other", "fund", "reit"}
_KR_FINANCIAL_TERMS = ("금융", "은행", "보험", "증권", "신탁", "여신", "카드", "투자기관", "기금")


def _zone(z: float, variant: str) -> str:
    thresholds = _THRESHOLDS[variant]
    if z > thresholds["safeAbove"]:
        return "safe"
    if z >= thresholds["distressBelow"]:
        return "grey"
    return "distress"


def _zoneZ(z: float) -> str:
    """원본 Z 임계 분류. 경계 1.81은 grey다."""
    return _zone(z, "z")


def _zoneZpp(z: float) -> str:
    """Z'' 임계 분류. 경계 1.1은 grey다."""
    return _zone(z, "zpp")


def _isFinite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _companyTypeMap(snap: pl.DataFrame, market: str) -> dict[str, str]:
    """공급자가 가진 업종 분류를 종목코드별로 반환한다."""
    if market == "US":
        if "sector" not in snap.columns:
            return {}
        rows = snap.select(["stockCode", "sector"]).drop_nulls("stockCode").unique(subset=["stockCode"])
        return {str(row["stockCode"]): str(row["sector"] or "") for row in rows.iter_rows(named=True)}

    try:
        # KRX 상장 등록부는 KR finance long-form에 없는 업종의 정본이다.
        from dartlab.gather.krx.listing import getKindList

        listing = getKindList()
    except (ImportError, OSError, ValueError, TypeError) as exc:
        log.warning("Altman 업종 목록 로드 실패: %s", type(exc).__name__)
        return {}
    if listing.is_empty() or not {"종목코드", "업종"}.issubset(listing.columns):
        return {}
    return {
        str(row["종목코드"]): str(row["업종"] or "")
        for row in listing.select(["종목코드", "업종"]).iter_rows(named=True)
    }


def _applicabilityReason(companyType: str | None, *, market: str, variant: str) -> str | None:
    """회사 유형 기준 모델 부적격 사유. None이면 적용 가능."""
    if not companyType:
        return "company_type_missing"
    normalized = companyType.strip().lower()
    financial = (
        normalized in _US_FINANCIAL_TYPES
        if market == "US"
        else any(term in companyType for term in _KR_FINANCIAL_TERMS)
    )
    if financial:
        return "financial_company_unsupported"
    if variant == "z":
        manufacturing = normalized == "manufacturing" if market == "US" else "제조업" in companyType
        if not manufacturing:
            return "nonmanufacturing_company_unsupported_for_z"
    return None


def _scoreOne(stock: pl.DataFrame, *, marketCap: float | None, variant: str) -> tuple[float | None, list[str], dict]:
    """선택된 한 Altman 모형만 계산한다. 결측은 다른 모형이나 0으로 대체하지 않는다."""
    values = {
        "totalAssets": extractAccount(stock, "total_assets"),
        "totalLiabilities": extractAccount(stock, "total_liabilities"),
        "currentAssets": extractAccount(stock, "current_assets"),
        "currentLiabilities": extractAccount(stock, "current_liabilities"),
        "retainedEarnings": extractAccount(stock, "retained_earnings"),
        # 공통 scan schema에는 정통 EBIT가 없다. 영업이익 proxy임을 provenance에 공개한다.
        "ebitProxy": extractAccount(stock, "operating_profit"),
        "bookEquity": extractAccount(stock, "total_equity"),
    }
    if variant == "z":
        values["sales"] = extractAccount(stock, "sales")
        values["marketEquity"] = marketCap

    missing = [name for name, value in values.items() if not _isFinite(value)]
    if missing:
        return None, missing, {}

    ta = values["totalAssets"]
    tl = values["totalLiabilities"]
    ca = values["currentAssets"]
    cl = values["currentLiabilities"]
    assert ta is not None and tl is not None and ca is not None and cl is not None
    if ta <= 0:
        return None, ["totalAssets_nonpositive"], {}
    if tl <= 0:
        return None, ["totalLiabilities_nonpositive"], {}
    if ca < 0:
        return None, ["currentAssets_negative"], {}
    if cl < 0:
        return None, ["currentLiabilities_negative"], {}

    re = values["retainedEarnings"]
    ebit = values["ebitProxy"]
    equity = values["bookEquity"]
    assert re is not None and ebit is not None and equity is not None
    components = {
        "workingCapitalToAssets": (ca - cl) / ta,
        "retainedEarningsToAssets": re / ta,
        "ebitToAssets": ebit / ta,
    }
    if variant == "z":
        sales = values["sales"]
        market_equity = values["marketEquity"]
        assert sales is not None and market_equity is not None
        if sales < 0:
            return None, ["sales_negative"], {}
        if market_equity <= 0:
            return None, ["marketEquity_nonpositive"], {}
        components.update(
            {
                "marketEquityToLiabilities": market_equity / tl,
                "salesToAssets": sales / ta,
            }
        )
        coefficients = _Z_COEFFICIENTS
    else:
        # 음수 자기자본은 유효한 distress 관측이다. 결측과 구분해 보존한다.
        components["bookEquityToLiabilities"] = equity / tl
        coefficients = _ZPP_COEFFICIENTS

    score = sum(coefficients[name] * value for name, value in components.items())
    return score, [], components


def _methodology(variant: str, *, year: str) -> dict[str, Any]:
    return {
        "modelName": "Altman Z (1968)" if variant == "z" else "Altman Z''",
        "variantApplied": variant,
        "coefficients": dict(_Z_COEFFICIENTS if variant == "z" else _ZPP_COEFFICIENTS),
        "thresholds": dict(_THRESHOLDS[variant]),
        "financialPeriod": str(year),
        "financeBasis": "annual_consolidated",
        "financeAsOf": None,
        "marketCapPeriod": str(year) if variant == "z" else None,
        "marketCapSource": "KRX_year_end" if variant == "z" else None,
        "ebitSource": "operating_profit_proxy",
        "pointInTime": False,
        "applicability": "listed_manufacturing" if variant == "z" else "nonfinancial",
    }


def _unavailable(*, market: str, stockCode: str | None, reasonCode: str, detail: str) -> dict:
    result = {
        "status": "unavailable",
        "available": False,
        "market": market,
        "reasonCode": reasonCode,
        "detail": detail,
        "score": None,
    }
    if stockCode is not None:
        result["stockCode"] = stockCode
    return result


def calcAltmanFactor(
    *,
    market: str = "auto",
    variant: str = "auto",
    stockCode: str | None = None,
    industryByCode: dict[str, str] | None = None,
    **kwargs,
) -> dict:
    """Altman 부실위험 점수 횡단면.

    ``auto``는 비금융 상장사 전체에 Z''를 적용한다. ``z``는 제조업 상장사만
    대상으로 하며 같은 회계연도 말 KRX 시가총액이 없으면 해당 종목을 제외한다.
    현재 listed factor에서는 Z'를 지원하지 않는다.
    """
    requested_variant = variant.strip().lower() if isinstance(variant, str) else ""
    if requested_variant not in _VARIANTS:
        raise ValueError("variant는 'auto', 'z', 'zpp' 중 하나여야 합니다")
    resolved_variant = "zpp" if requested_variant == "auto" else requested_variant

    requested_market = market.strip().upper() if isinstance(market, str) else ""
    if requested_market == "AUTO":
        resolved_market = detectMarket(stockCode) if stockCode else "KR"
    elif requested_market in {"KR", "US"}:
        resolved_market = requested_market
    else:
        raise ValueError("market은 'auto', 'KR', 'US' 중 하나여야 합니다")

    try:
        lf = loadScanParquet("finance", resolved_market)
        if lf is None:
            return _unavailable(
                market=resolved_market,
                stockCode=stockCode,
                reasonCode="finance_snapshot_missing",
                detail="연간 연결 재무 스냅샷을 사용할 수 없습니다.",
            )
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
        year = _latestYear(snap)
        if year is None:
            return _unavailable(
                market=resolved_market,
                stockCode=stockCode,
                reasonCode="complete_financial_year_missing",
                detail="고유 종목 수 기준의 완전한 회계연도가 없습니다.",
            )
    except (OSError, ValueError, KeyError, AttributeError, pl.exceptions.PolarsError) as exc:
        log.warning("calcAltmanFactor 재무 스냅샷 실패: %s", type(exc).__name__)
        return _unavailable(
            market=resolved_market,
            stockCode=stockCode,
            reasonCode="finance_snapshot_error",
            detail=f"재무 스냅샷 처리 실패: {type(exc).__name__}",
        )

    edgar = isEdgarSchema(snap)
    yearCol = "fy" if edgar else "bsns_year"
    year_val = int(year) if edgar else year
    cur = snap.filter(pl.col(yearCol) == year_val)
    if cur.is_empty():
        return _unavailable(
            market=resolved_market,
            stockCode=stockCode,
            reasonCode="financial_period_empty",
            detail=f"{year} 회계연도 데이터가 비어 있습니다.",
        )

    company_types = dict(industryByCode) if industryByCode is not None else _companyTypeMap(snap, resolved_market)
    market_caps = _fetchYearEndMarketcaps(resolved_market, str(year)) if resolved_variant == "z" else {}
    scores: dict[str, float] = {}
    components_by_code: dict[str, dict] = {}
    excluded: dict[str, str] = {}
    missing_by_code: dict[str, list[str]] = {}

    partitions = cur.partition_by("stockCode", as_dict=True)
    for code_key, stock in partitions.items():
        code = code_key[0] if isinstance(code_key, tuple) else code_key
        if not isinstance(code, str) or stock.is_empty():
            continue
        applicability = _applicabilityReason(
            company_types.get(code),
            market=resolved_market,
            variant=resolved_variant,
        )
        if applicability is not None:
            excluded[code] = applicability
            continue

        score, missing, components = _scoreOne(
            stock,
            marketCap=market_caps.get(code),
            variant=resolved_variant,
        )
        if score is None:
            excluded[code] = "required_input_missing_or_invalid"
            missing_by_code[code] = missing
            continue
        scores[code] = score
        components_by_code[code] = components

    methodology = _methodology(resolved_variant, year=str(year))
    excluded_counts = dict(Counter(excluded.values()))
    missing_input_counts = dict(Counter(name for names in missing_by_code.values() for name in names))
    coverage = {
        "candidates": len(scores) + len(excluded),
        "calculated": len(scores),
        "excluded": len(excluded),
        "excludedByReason": excluded_counts,
        "missingInputsByField": missing_input_counts,
    }
    if not scores:
        reason_code = excluded.get(stockCode, "no_eligible_companies") if stockCode else "no_eligible_companies"
        result = _unavailable(
            market=resolved_market,
            stockCode=stockCode,
            reasonCode=reason_code,
            detail=(
                f"{stockCode}은(는) 선택한 Altman 모형으로 계산할 수 없습니다."
                if stockCode
                else "모형 적용성과 필수 입력을 모두 충족한 종목이 없습니다."
            ),
        )
        result.update(
            {
                "year": str(year),
                "variantRequested": requested_variant,
                "variant": resolved_variant,
                "methodology": methodology,
                "coverage": coverage,
                "missingInputs": missing_by_code.get(stockCode, []) if stockCode else [],
            }
        )
        return result

    zone_fn = _zoneZ if resolved_variant == "z" else _zoneZpp
    counts = {"safe": 0, "grey": 0, "distress": 0}
    for score in scores.values():
        counts[zone_fn(score)] += 1
    total = len(scores)
    zones = {key: {"count": count, "pct": round(100 * count / total, 1)} for key, count in counts.items()}
    sorted_items = sorted(scores.items(), key=lambda item: -item[1])
    thresholds = methodology["thresholds"]

    if stockCode:
        score = scores.get(stockCode)
        if score is None:
            reason = excluded.get(stockCode, "stock_not_in_financial_universe")
            result = _unavailable(
                market=resolved_market,
                stockCode=stockCode,
                reasonCode=reason,
                detail=f"{stockCode}은(는) 선택한 Altman 모형으로 계산할 수 없습니다.",
            )
            result.update(
                {
                    "year": str(year),
                    "variantRequested": requested_variant,
                    "variant": resolved_variant,
                    "missingInputs": missing_by_code.get(stockCode, []),
                    "methodology": methodology,
                    "coverage": coverage,
                }
            )
            return result
        zone = zone_fn(score)
        rank = sum(1 for value in scores.values() if value <= score)
        percentile = round(100 * rank / total, 1)
        return {
            "status": "ok",
            "available": True,
            "stockCode": stockCode,
            "market": resolved_market,
            "year": str(year),
            "variantRequested": requested_variant,
            "variant": resolved_variant,
            "score": round(score, 2),
            "zone": zone,
            "percentile": percentile,
            "universe": total,
            "components": {key: round(value, 6) for key, value in components_by_code[stockCode].items()},
            "missingInputs": [],
            "methodology": methodology,
            "coverage": coverage,
            "interpretation": (
                f"{stockCode} Altman {methodology['modelName']}={round(score, 2)} ({zone}) — "
                f"전종목 {total}개 중 {percentile}백분위. "
                f"distress < {thresholds['distressBelow']}, safe > {thresholds['safeAbove']}."
            ),
        }

    top_safe = [(code, round(score, 2)) for code, score in sorted_items[:10]]
    top_distress = [(code, round(score, 2)) for code, score in sorted_items[-10:]]
    return {
        "status": "ok",
        "available": True,
        "market": resolved_market,
        "year": str(year),
        "variantRequested": requested_variant,
        "variant": resolved_variant,
        "universe": total,
        "scores": {code: round(score, 2) for code, score in scores.items()},
        "zones": zones,
        "topSafe": top_safe,
        "topDistress": top_distress,
        "methodology": methodology,
        "coverage": coverage,
        "interpretation": (
            f"{resolved_market} {year}년 비금융 적격 {total}개 종목의 {methodology['modelName']} 분포. "
            f"distress {zones['distress']['pct']}%, safe {zones['safe']['pct']}%. "
            "점수는 부실확률이 아니라 판별 점수이며 point-in-time 결과가 아니다."
        ),
    }
