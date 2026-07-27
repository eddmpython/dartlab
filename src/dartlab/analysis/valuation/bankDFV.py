"""은행/금융지주 전용 dFV — Damodaran Ch.21 Bank Excess Return 통합.

detection: c.sector.sector == "금융" 또는 industryGroup in {"은행","금융지주","증권","보험"}
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.valuation.types import opinionFromUpside

_FINANCIAL_SECTOR_KEYWORDS = ("금융", "Financial", "FINANCIALS", "Bank")
_FINANCIAL_GROUP_KEYWORDS = (
    "은행",
    "금융지주",
    "증권",
    "보험",
    "신용카드",
    "BANK",
    "INSURANCE",
    "BROKERAGE",
    "Bank",
    "Insurance",
)


def isFinancialCompany(company: Any) -> bool:
    """sector/industryGroup 기반 금융업 검출 (Enum/str 모두 처리).

    Capabilities:
        - sector.sector 키워드 매칭 (금융/Financial/Bank 등)
        - industryGroup 키워드 (은행/금융지주/증권/보험/카드)
        - 종목명 fallback 매칭

    Parameters
    ----------
    company : Company
        판별 대상 기업.

    Returns
    -------
    bool
        금융업이면 True.

    Example:
        >>> isFinancialCompany(Company("055550"))  # 신한지주
        True

    Guide:
        calcDFV 가 본 함수로 금융업 분기 → calcBankDFV 로 dispatch.

    When:
        dFV 진입 시 금융업 분기 판정 단계.

    How:
        isFinancialCompany(company) 직접 호출.

    Requires:
        company.sector + (optional) industryGroup + corpName/name.

    Raises:
        없음 — 누락 속성은 falsy 처리.

    See Also:
        - calcBankDFV : 본 함수 True 시 호출되는 금융업 dFV
        - calcDFV : 분기 진입점

    AIContext:
        금융업 분기 근거 — 사용자 회사가 금융인지 설명 시 인용.
    """
    sector = getattr(company, "sector", None)
    if sector is None:
        return False
    sec_raw = getattr(sector, "sector", "")
    grp_raw = getattr(sector, "industryGroup", "")
    sec_str = str(sec_raw) if sec_raw is not None else ""
    grp_str = str(grp_raw) if grp_raw is not None else ""
    for kw in _FINANCIAL_SECTOR_KEYWORDS:
        if kw in sec_str:
            return True
    for kw in _FINANCIAL_GROUP_KEYWORDS:
        if kw in grp_str:
            return True
    # 종목명 fallback
    name = getattr(company, "corpName", "") or getattr(company, "name", "") or ""
    return any(kw in name for kw in ("금융", "은행", "증권", "보험", "카드"))


def calcBankDFV(company: Any, *, basePeriod: str | None = None, overrides: dict | None = None) -> dict | None:
    """은행 전용 dFV — Excess Return Model.

    Capabilities:
        - Book Equity + ROE + CoE → Damodaran Excess Return Model
        - calcDFV 호환 스키마 (dFV/scenarios/upside/opinion/confidence)
        - 한국 은행 평균 beta 0.95 + Damodaran ERP 기반 CoE

    Parameters
    ----------
    company : Company
        대상 금융업 회사.
    basePeriod : str, optional
        기준 기간 (미사용 — BS 최신 자동).
    overrides : dict, optional
        countryCode/terminalGrowth 등 override.

    Returns
    -------
    dict (calcDFV 호환 스키마)
        dFV, scenarios, currentPrice, upside, opinion, confidence
        primaryModel : "bankExcessReturn"
        bankModel : detail dict (impliedPBR, excessReturn, ...)

    Example:
        >>> calcBankDFV(Company("055550"))
        {"dFV": 48000, "opinion": "보유", ...}

    Guide:
        Book Equity ≤ 0 또는 net income ≤ 0 시 None. shares 역산 실패 시 한국
        은행 평균 PBR 0.85 fallback.

    When:
        isFinancialCompany True 인 회사의 dFV 계산 시점.

    How:
        calcBankDFV(company) 또는 overrides 로 가정 주입.

    Requires:
        company.select(BS, [자본총계]), select(IS, [당기순이익]) 가용 +
        bankValuation.calcBankExcessReturn + synth.overrides + riskPremiums.

    Raises:
        없음 — ImportError/속성 누락은 None 반환.

    See Also:
        - calcBankExcessReturn : Excess Return 본 수식
        - isFinancialCompany : 분기 게이트
        - calcDFV : 통합 진입점

    AIContext:
        은행/금융지주 적정주가 답변 시 dFV/impliedPBR/excessReturn 인용.
        일반 DCF 대신 본 모델 사용 이유 (CapEx 부재) 설명.
    """
    try:
        from dartlab.analysis.valuation.bankValuation import calcBankExcessReturn
        from dartlab.core.utils.helpers import toDictBySnakeId
        from dartlab.synth.overrides import applyOverride
        from dartlab.synth.riskPremiums import loadDamodaranERP
    except ImportError:
        return None

    overrides = overrides or {}

    # Book Equity 추출 (BS)
    book_equity: float | None = None
    shares: int | None = None
    try:
        bs = company.select("BS", ["자본총계"])
        parsed = toDictBySnakeId(bs)
        if parsed:
            data, periods = parsed
            if periods:
                latest = periods[0]
                eq_row = data.get("total_stockholders_equity") or {}
                v = eq_row.get(latest)
                if v and v > 0:
                    book_equity = float(v)
    except (AttributeError, KeyError, TypeError, ValueError):
        pass

    if not book_equity:
        return None

    # ROE 추출 (당기순이익 / 자본총계)
    net_income: float | None = None
    try:
        income = company.select("IS", ["당기순이익"])
        is_parsed = toDictBySnakeId(income)
        if is_parsed:
            is_data, is_periods = is_parsed
            if is_periods:
                ni_row = is_data.get("net_profit") or is_data.get("net_income") or {}
                v = ni_row.get(is_periods[0])
                if v:
                    net_income = float(v)
    except (AttributeError, KeyError, TypeError, ValueError):
        pass

    if not net_income or net_income <= 0:
        return None

    roe_pct = net_income / book_equity * 100  # 한국 은행 일반 5~12%

    # Cost of Equity (CAPM, 은행 beta 0.95 기본)
    currency = getattr(company, "currency", "KRW")
    country = applyOverride(None, "countryCode", overrides)
    erp = loadDamodaranERP(countryCode=country, currency=currency)
    rf = erp["riskFreeRate"]
    market_erp = erp["totalERP"]
    bank_beta = 0.95  # Damodaran 한국 은행 평균
    ke = rf + bank_beta * market_erp

    # 영구성장률 — Damodaran 권고 GDP 근접 2%
    g = applyOverride(2.0, "terminalGrowth", overrides)

    # Excess Return Model 호출
    bank = calcBankExcessReturn(
        bookEquity=book_equity,
        roe=roe_pct,
        costOfEquity=ke,
        growthRate=g,
        excessReturnYears=10,
    )

    if bank.get("method") == "skip" or not bank.get("equityValue"):
        return None

    # shares 역산 — calcDcf 우선, 실패 시 calcRelativeValuation/시가총액
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
        try:
            from dartlab.analysis.financial.valuation import calcRelativeValuation

            rel = calcRelativeValuation(company)
            if isinstance(rel, dict):
                cur_p = rel.get("currentPrice")
                if cur_p and cur_p > 0:
                    # market cap 추정: relative consensusValue × shares = book proxy
                    # → shares = book_equity / (book per share). 보수적: 발행주식수 = book × PBR_target / current_price
                    # 더 단순: gather price 결과 시총 / current_price
                    pass
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    # 주식수를 주가로 만들어 내던 fallback 을 없앤다. 가정 PBR 로 시총을 추정한 뒤
    # 주가로 나눠 주식수를 얻으면, 그 주식수로 계산한 주당가치와 주가의 비율에서 주가가
    # 약분된다. 그래서 상승여력이 주가와 무관한 상수가 됐다. 주가가 10 배 움직여도 같은
    # 값이 나오는 목표가는 회사가 싼지 비싼지 영영 말할 수 없다.
    #
    # 판단 대상인 주가로 판단 근거를 만들지 않는다. 주식수를 모르면 값을 내지 않는다.
    if not shares or shares <= 0:
        return None

    per_share = bank["equityValue"] / shares
    if per_share <= 0:
        return None

    # 현재가 + upside
    currentPrice = _getCurrentPriceLight(company)
    upside = (per_share - currentPrice) / currentPrice * 100 if currentPrice and currentPrice > 0 else None

    opinion = _opinion(upside)
    # 상승여력을 못 구한 경우를 `abs(None or 0) < 30` 으로 처리하면 하필 'medium' 이
    # 된다. 검증할 수 없을 때 가장 높은 신뢰도가 붙는 셈이라 반대로 둔다.
    confidence = "low" if upside is None else ("medium" if abs(upside) < 30 else "low")

    bull = per_share * 1.15
    bear = per_share * 0.85

    return {
        "dFV": round(per_share),
        "scenarios": {"bull": round(bull), "base": round(per_share), "bear": round(bear)},
        "currentPrice": round(currentPrice) if currentPrice else None,
        "upside": round(upside, 1) if upside is not None else None,
        "opinion": opinion,
        "confidence": confidence,
        "primaryModel": "bankExcessReturn",
        "companyType": "금융",
        "lifeCyclePhase": "matureStable",
        "bankModel": {
            "bookEquity": book_equity,
            "roe": round(roe_pct, 2),
            "costOfEquity": round(ke, 2),
            "impliedPBR": bank["impliedPBR"],
            "excessReturn": bank["excessReturn"],
            "pvExplicit": bank["pvExplicit"],
            "pvTerminal": bank["pvTerminal"],
            "warnings": bank["warnings"],
        },
        "qualityWACC": {"baseWACC": ke, "adjustedWACC": ke, "totalSpread": 0, "factors": []},
        "allMethods": {"bankExcessReturn": round(per_share)},
        "triangulation": {"checks": [], "confidence": confidence},
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
