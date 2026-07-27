"""Sum-of-the-Parts NAV — Damodaran *Investment Valuation* Ch.16.

지주사 (SK/LG/CJ 등) 전용:
1. c.panel("investedCompany") → 자회사 + 지분율 + 장부가
2. 자회사 장부가액 합산 (보수적 근사 — 상장사 시가총액 반영은 별도 인프라 필요)
3. + 모회사 별도 자산 (잉여현금 / 투자부동산)
4. - 모회사 별도 부채
5. × (1 - holdingDiscount)  # 한국 평균 0.40~0.50

한국 시장 평균 holding discount 51.9% (Damodaran 표준 0.20 + 한국 갭 0.20).
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation.types import opinionFromUpside

_DEFAULT_HOLDING_DISCOUNT = 0.40  # 한국 시장 평균 (Damodaran 0.20 + 한국 갭)


def calcSotpNav(
    company: Any,
    *,
    holdingDiscount: float = _DEFAULT_HOLDING_DISCOUNT,
    overrides: dict | None = None,
) -> dict | None:
    """SOTP NAV — Damodaran Ch.16.

    Capabilities:
        - investedCompany (자회사 장부가) 합산 + 모회사 별도 자산 - 부채
        - 한국 시장 평균 holding discount 40% (Damodaran 20% + 한국 갭 20%)
        - sanity cap (시가총액 × 3) 으로 DART 데이터 중복/단위 보정

    Parameters
    ----------
    company : Company
        지주사 회사.
    holdingDiscount : float
        지주사 할인율 (0.40 기본, [0.0, 0.7] clamp).
    overrides : dict, optional
        가정 override.

    Returns
    -------
    dict | None
        rawNav : float — discount 전 합계 (자회사 장부가 합 + 모회사 자산 - 부채)
        adjustedNav : float — × (1 - holdingDiscount)
        affiliates : list[{name, shareRatio, bookValue, listingFlag}]
        affiliateBookSum : float
        parentNetAsset : float — 모회사 잉여현금 + 투자부동산 - 부채 (별도 추정)
        listedCount, unlistedCount, totalCount
        holdingDiscount, perShare, method
        warnings : list[str]

    Example:
        >>> calcSotpNav(Company("003550"))  # LG
        {"perShare": 85000, "adjustedNav": ..., ...}

    Guide:
        investedCompany 미가용 또는 affiliate_book_sum ≤ 0 시 None. shares
        역산 실패 시 한국 지주 평균 PBR 0.5 기반 fallback.

    When:
        지주사 (SK/LG/CJ 등) dFV 산출 시점 — calcHoldingDFV 가 호출.

    How:
        calcSotpNav(company) 또는 holdingDiscount=0.5 강제.

    Requires:
        company.panel("investedCompany") + company.select("BS", ["자본총계"]).

    Raises:
        없음 — 데이터 부족은 None.

    See Also:
        - calcHoldingDFV : 본 함수의 dFV 진입점 wrapper
        - Damodaran *Investment Valuation* Ch.16

    AIContext:
        지주사 NAV 답변 시 adjustedNav + holdingDiscount 함께 노출.
    """
    overrides = overrides or {}
    warnings: list[str] = []

    # 자회사 데이터 추출
    affiliates: list[dict] = []
    affiliate_book_sum = 0.0
    listed = 0
    unlisted = 0
    try:
        import polars as pl

        from dartlab.providers.dart.panel.text import panelTableRows

        _code = getattr(company, "stockCode", None)
        _r = (
            (panelTableRows(_code, sectionPattern="타법인") or panelTableRows(_code, sectionPattern="출자"))
            if _code
            else []
        )
        inv = pl.DataFrame(_r) if _r else None
        if inv is not None and hasattr(inv, "iter_rows"):
            for row in inv.iter_rows(named=True):
                name = row.get("법인명") or ""
                ratio_raw = row.get("기말잔액(지분율)") or ""
                book_raw = row.get("기말잔액(장부가액)")
                if book_raw is None or book_raw <= 0:
                    continue
                # 지분율 파싱 ("100.00%" → 1.0)
                try:
                    ratio = float(str(ratio_raw).rstrip("%")) / 100.0
                except (ValueError, TypeError):
                    ratio = 0.0
                listing_flag = "비상장" if "(비상장)" in name else "상장"
                if listing_flag == "상장":
                    listed += 1
                else:
                    unlisted += 1
                book_value = float(book_raw)
                affiliate_book_sum += book_value
                affiliates.append(
                    {
                        "name": name.replace("(비상장)", "").strip(),
                        "shareRatio": ratio,
                        "bookValue": book_value,
                        "listingFlag": listing_flag,
                    }
                )
    except (AttributeError, KeyError, TypeError, ValueError):
        return None

    if not affiliates or affiliate_book_sum <= 0:
        return None

    # 모회사 별도 자산 - 부채 (단순 추정: 자본총계 × 30% 잉여현금/투자부동산 비중)
    parent_net = 0.0
    try:
        from dartlab.core.utils.helpers import toDictBySnakeId

        bs = company.select("BS", ["자본총계"])
        parsed = toDictBySnakeId(bs)
        if parsed:
            data, periods = parsed
            if periods:
                eq_row = data.get("total_stockholders_equity") or {}
                eq = eq_row.get(periods[0])
                if eq:
                    # 보수적: 자본의 10% 만 추가 (이중계산 회피, 자회사가 이미 자본에 반영됨)
                    parent_net = float(eq) * 0.10
                    warnings.append("모회사 별도자산은 자본 × 10% 보수적 근사 (이중계산 회피)")
    except (AttributeError, KeyError, TypeError, ValueError):
        pass

    raw_nav = affiliate_book_sum + parent_net
    discount = max(0.0, min(0.7, float(holdingDiscount)))
    adjusted_nav = raw_nav * (1.0 - discount)

    # Sanity cap — DART investedCompany 데이터 중복/단위 혼재 보정
    # 한국 지주사 평균 시장 NAV ≈ 시가총액 × 1.5~2.5 (50% discount 가정)
    cur_price = _getCurrentPriceLight(company)
    if cur_price and cur_price > 0:
        try:
            from dartlab.core.utils.helpers import toDictBySnakeId

            bs_check = company.select("BS", ["자본총계"])
            parsed_check = toDictBySnakeId(bs_check)
            if parsed_check:
                data_c, periods_c = parsed_check
                if periods_c:
                    eq_check = (data_c.get("total_stockholders_equity") or {}).get(periods_c[0])
                    if eq_check and eq_check > 0:
                        # 시가총액 추정: 자본 × PBR 0.5 (한국 지주 평균)
                        estimated_mc = float(eq_check) * 0.5
                        sanity_cap = estimated_mc * 3.0  # 시가총액 × 3 (50% discount 환원)
                        if adjusted_nav > sanity_cap:
                            warnings.append(
                                f"NAV {adjusted_nav / 1e12:.0f}조 → 시가총액 × 3 cap {sanity_cap / 1e12:.0f}조 적용 "
                                f"(DART investedCompany 중복/단위 보정)"
                            )
                            adjusted_nav = sanity_cap
                            raw_nav = sanity_cap / (1.0 - discount)
        except (AttributeError, KeyError, TypeError, ValueError):
            pass

    # shares 역산 — calcDcf 우선, 실패 시 시가총액 / 현재가
    shares: int | None = None
    try:
        from dartlab.analysis.financial.valuation import calcDcf

        dcf_result = calcDcf(company)
        if isinstance(dcf_result, dict):
            eq = dcf_result.get("equityValue")
            ps = dcf_result.get("perShareValue")
            if eq and ps and ps > 0:
                shares = int(eq / ps)
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    if not shares:
        # fallback: 모회사 자본 × 한국 지주 평균 PBR 0.5 → 시총 추정 → shares
        cur_p = _getCurrentPriceLight(company)
        if cur_p and cur_p > 0:
            try:
                from dartlab.core.utils.helpers import toDictBySnakeId

                bs = company.select("BS", ["자본총계"])
                parsed = toDictBySnakeId(bs)
                if parsed:
                    data, periods = parsed
                    if periods:
                        eq = (data.get("total_stockholders_equity") or {}).get(periods[0])
                        if eq and eq > 0:
                            estimated_market_cap = float(eq) * 0.5  # 한국 지주 PBR 0.5
                            shares = int(estimated_market_cap / cur_p)
            except (AttributeError, KeyError, TypeError, ValueError):
                pass

    if not shares:
        return None

    per_share = adjusted_nav / shares
    if per_share <= 0:
        return None

    return {
        "rawNav": round(raw_nav, 0),
        "adjustedNav": round(adjusted_nav, 0),
        "affiliateBookSum": round(affiliate_book_sum, 0),
        "parentNetAsset": round(parent_net, 0),
        "affiliates": affiliates[:20],  # 상위 20 (요약)
        "totalCount": len(affiliates),
        "listedCount": listed,
        "unlistedCount": unlisted,
        "holdingDiscount": discount,
        "perShare": round(per_share, 0),
        "method": "sotp_book_value",
        "warnings": warnings,
    }


def calcHoldingDFV(company: Any, *, basePeriod: str | None = None, overrides: dict | None = None) -> dict | None:
    """지주사 전용 dFV — SOTP NAV 우선.

    Capabilities:
        - calcSotpNav 결과 → calcDFV 호환 스키마 변환
        - scenarios (bull/base/bear) + opinion + confidence 부착
        - primaryModel="sotp" 고정

    Parameters
    ----------
    company : Company
        지주사 회사.
    basePeriod : str, optional
        기준 기간.
    overrides : dict, optional
        가정 override.

    Returns
    -------
    dict | None
        calcDFV 호환 dict (primaryModel="sotp", companyType="지주").

    Example:
        >>> calcHoldingDFV(Company("003550"))
        {"dFV": 85000, "opinion": "매수", "primaryModel": "sotp", ...}

    Guide:
        scenarios = base ± 15%. confidence="medium" 고정 (NAV 변동성 큼).

    When:
        isHoldingCompany True → calcDFV 가 본 함수로 dispatch.

    How:
        calcHoldingDFV(company).

    Requires:
        calcSotpNav + _getCurrentPriceLight + _opinion.

    Raises:
        없음.

    See Also:
        - calcSotpNav : NAV 본체
        - calcDFV : 통합 진입점

    AIContext:
        지주사 적정주가 답변 시 dFV + sotpModel.affiliates 함께 인용.
    """
    overrides = overrides or {}
    sotp = calcSotpNav(company, overrides=overrides)
    if not sotp or not sotp.get("perShare"):
        return None

    per_share = sotp["perShare"]
    currentPrice = _getCurrentPriceLight(company)
    upside = (per_share - currentPrice) / currentPrice * 100 if currentPrice and currentPrice > 0 else None

    bull = per_share * 1.15
    bear = per_share * 0.85

    return {
        "dFV": round(per_share),
        "scenarios": {"bull": round(bull), "base": round(per_share), "bear": round(bear)},
        "currentPrice": round(currentPrice) if currentPrice else None,
        "upside": round(upside, 1) if upside is not None else None,
        "opinion": _opinion(upside),
        "confidence": "medium",
        "primaryModel": "sotp",
        "companyType": "지주",
        "lifeCyclePhase": "matureStable",
        "sotpModel": sotp,
        "qualityWACC": {"baseWACC": 0, "adjustedWACC": 0, "totalSpread": 0, "factors": []},
        "allMethods": {"sotp": round(per_share)},
        "triangulation": {"checks": [], "confidence": "medium"},
    }


def _getCurrentPriceLight(company: Any) -> float | None:
    """현재 주가 추출 — currentPrice 속성 우선, 없으면 gather 경유.

    Returns
    -------
    float | None
        현재 주가 (원). 조회 실패 시 None.
    """
    try:
        price = getattr(company, "currentPrice", None)
        if price:
            return float(price)
        from dartlab.core.di import getMacroProvider

        g = getMacroProvider().getDefaultGather()
        p = g("price", getattr(company, "stockCode", ""))
        if p is not None and hasattr(p, "height") and p.height > 0:
            return float(p["close"][-1])
    except (ImportError, AttributeError, ValueError, TypeError, KeyError):
        pass
    return None


def _opinion(upside: float | None) -> str:
    """상승여력을 투자의견 라벨로 바꾼다. 기준표는 `types.opinionFromUpside` 가 갖는다.

    예전에는 이 표를 세 파일이 글자까지 똑같이 복사해 갖고 있었다. 사용자에게 그대로
    보이는 판정이라 하나만 임계값을 옮기면 같은 회사가 화면마다 다른 의견을 받는다.
    """
    return opinionFromUpside(upside)
