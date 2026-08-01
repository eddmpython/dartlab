"""Dilution + 종합 anomaly — calcDilutionTrend · calcQualityAnomalies."""

from __future__ import annotations

from dartlab.analysis.financial._earningsQualityCalcs import _beneishUnavailable
from dartlab.analysis.financial._earningsQualityDeepProxies import (
    _calcEarningsQualityFlagsBase,
    detectAuditFlags,
)
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import toDictBySnakeId

_MAX_YEARS = 8


@memoizedCalc
def calcDilutionTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """기본 EPS vs 희석 EPS 괴리율 시계열 — 스톡옵션/전환사채 희석 리스크.

    notes.eps에서 기본주당이익과 희석주당이익을 추출하여
    희석 괴리율(%)의 추세를 추적한다.
    괴리율이 5% 이상이면 잠재 희석 리스크.

    Returns
    -------
    dict
        history : list[dict] — 기간별 EPS 희석 시계열
            period : str — 회계연도
            basicEps : float | None — 기본주당이익 (원)
            dilutedEps : float | None — 희석주당이익 (원)
            dilutionPct : float | None — 희석 괴리율 (%)
        latestDilution : float | None — 최신 기간 희석 괴리율 (%)
        trend : str | None — 희석 추세 (희석 증가/희석 감소/안정)

    Capabilities:
        - notes.eps 에서 basic vs diluted EPS 시계열 추출 + 괴리율 추세 분류
        - 5% 이상 = 잠재 희석 리스크 식별

    Guide:
        희석 괴리율 추세 ↑ = 신주발행/CB 등 dilution 압력 ↑. 5% 임계 보수적.

    When:
        희석 리스크 + AI EPS dilution 답변.

    How:
        notesDetail.eps → basic/diluted 매칭 → 시계열 계산.

    Requires:
        notes.eps 가용.

    Raises:
        없음.

    Example:
        >>> calcDilutionTrend(company)["latestDilution"]
        3.2

    See Also:
        - calcNonOperatingBreakdown : 영업외
        - companyContext.fetchNotesDetail

    AIContext:
        "EPS 희석 압력" 답변 시 latestDilution + trend 인용.
    """
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesData = fetchNotesDetail(company, ["eps"])
    epsDf = notesData.get("eps")
    if not epsDf:
        return None

    basicRow = None
    dilutedRow = None
    for row in epsDf:
        item = str(row.get("항목", "")).strip()
        if "희석" in item:
            dilutedRow = row
        elif "기본" in item or "주당" in item:
            if basicRow is None:
                basicRow = row

    if basicRow is None:
        return None

    periodCols = [k for k in basicRow if k not in ("항목",) and k.isdigit()]
    periodCols.sort(reverse=True)
    if not periodCols:
        return None

    from dartlab.core.utils.helpers import parseNumStr

    history = []
    for col in periodCols[:_MAX_YEARS]:
        basic = parseNumStr(basicRow.get(col))
        diluted = parseNumStr(dilutedRow.get(col)) if dilutedRow else None

        dilutionPct = None
        if basic is not None and diluted is not None and basic != 0:
            dilutionPct = round((basic - diluted) / abs(basic) * 100, 2)

        history.append(
            {
                "period": col,
                "basicEps": basic,
                "dilutedEps": diluted,
                "dilutionPct": dilutionPct,
            }
        )

    if not history:
        return None

    latestDilution = history[0]["dilutionPct"]

    trend = None
    dilutionVals = [h["dilutionPct"] for h in history if h["dilutionPct"] is not None]
    if len(dilutionVals) >= 2:
        diff = dilutionVals[0] - dilutionVals[-1]
        if diff > 2:
            trend = "희석 증가"
        elif diff < -2:
            trend = "희석 감소"
        else:
            trend = "안정"

    return {
        "history": history,
        "latestDilution": latestDilution,
        "trend": trend,
    }


def _pickAccount(rowDict: dict, period: str, *keys: str) -> float | None:
    """계정 별칭을 순서대로 훑어 첫 non-null 값.

    Parameters
    ----------
    rowDict : dict
        {계정키: {기간: 값}}.
    period : str
        기간 컬럼.
    keys : str
        시도할 계정 키 (snakeId 우선, 한국어 라벨 후순위).

    Returns
    -------
    float | None
        값. 없으면 None.
    """
    for k in keys:
        row = rowDict.get(k) or {}
        v = row.get(period)
        if v is not None:
            return float(v)
    return None


def _qualityInputs(isData: dict, bsData: dict, cfData: dict, t: str, t1: str) -> dict[str, float | None]:
    """Beneish/Sloan 계산에 필요한 t·t1 계정을 한 번에 뽑는다.

    Parameters
    ----------
    isData, bsData, cfData : dict
        IS/BS/CF 파싱 결과.
    t, t1 : str
        당기 / 전기 연도.

    Returns
    -------
    dict[str, float | None]
        계정별 값 dict.
    """
    return {
        "salesT": _pickAccount(isData, t, "sales", "매출액"),
        "salesT1": _pickAccount(isData, t1, "sales", "매출액"),
        "cogsT": _pickAccount(isData, t, "cost_of_sales", "매출원가"),
        "cogsT1": _pickAccount(isData, t1, "cost_of_sales", "매출원가"),
        "sgaT": _pickAccount(isData, t, "selling_and_administrative_expenses", "판매비와관리비"),
        "sgaT1": _pickAccount(isData, t1, "selling_and_administrative_expenses", "판매비와관리비"),
        "niT": _pickAccount(isData, t, "net_profit", "net_income", "당기순이익"),
        "assetsT": _pickAccount(bsData, t, "total_assets", "자산총계"),
        "assetsT1": _pickAccount(bsData, t1, "total_assets", "자산총계"),
        "receivablesT": _pickAccount(bsData, t, "trade_receivables", "매출채권"),
        "receivablesT1": _pickAccount(bsData, t1, "trade_receivables", "매출채권"),
        "goodwillT": _pickAccount(bsData, t, "goodwill", "영업권"),
        "liabilitiesT": _pickAccount(bsData, t, "total_liabilities", "부채총계"),
        "liabilitiesT1": _pickAccount(bsData, t1, "total_liabilities", "부채총계"),
        "ppeT": _pickAccount(bsData, t, "tangible_assets", "유형자산"),
        "ppeT1": _pickAccount(bsData, t1, "tangible_assets", "유형자산"),
        "ocfT": _pickAccount(cfData, t, "operating_cashflow"),
    }


def _beneishFromInputs(v: dict[str, float | None]):
    """옛 proxy 입력을 점수로 바꾸지 않고 비발행 사유를 반환한다.

    Parameters
    ----------
    v : dict[str, float | None]
        _qualityInputs 결과.

    Returns
    -------
    dict
        canonical 입력 계약이 없다는 구조화 결과.
    """
    _ = v
    return _beneishUnavailable()


def _collectAuditFlags(company) -> list[dict]:
    """감사의견 본문에서 red flag 키워드를 중복 없이 모은다.

    Parameters
    ----------
    company : Any
        기업 객체 (stockCode 사용).

    Returns
    -------
    list[dict]
        keyword 별 flag dict. 본문이 없으면 빈 목록.
    """
    auditFlags: list[dict] = []
    try:
        import polars as pl

        from dartlab.providers.dart.panel.text import panelTableRows

        code = getattr(company, "stockCode", None)
        rows = (
            (panelTableRows(code, sectionPattern="감사의견") or panelTableRows(code, sectionPattern="감사보고서"))
            if code
            else []
        )
        auditDf = pl.DataFrame(rows) if rows else None
        if auditDf is not None and hasattr(auditDf, "to_dicts"):
            seen: set = set()
            for row in auditDf.to_dicts():
                text = " ".join(str(x) for x in row.values() if isinstance(x, str))
                for f in detectAuditFlags(text):
                    key = f.get("keyword")
                    if key and key not in seen:
                        seen.add(key)
                        auditFlags.append(f)
    except (AttributeError, KeyError, TypeError, ValueError):
        # 원본과 같은 자리에서 삼킨다. 이미 모은 flag 는 그대로 돌려준다.
        pass
    return auditFlags


@memoizedCalc
def calcQualityAnomalies(company, *, basePeriod: str | None = None) -> dict | None:
    """Damodaran Ch.4 + Beneish (1999) + Sloan (1996) 학술 표준 회계 품질.

    기존 calcAccrualAnalysis 는 발생액 시계열. 이 함수는 **이상치 감지** 통합:
    - Beneish M-Score (8 변수)
    - Sloan Accrual quintile
    - 5 카테고리 (분식/일회성/매출채권/자본우회/영업권)
    - 감사보고서 키워드 자동 감지 (docs 활용)

    Returns
    -------
    dict
        score : int — 0~100
        flags : list[{category, severity, evidence, damodaranRef}]
        beneish : dict — M-Score + zone
        sloan : dict — 발생액 quintile
        auditFlags : list — 감사보고서 위험 키워드
        period : str

    Capabilities:
        - Beneish + Sloan + 5 카테고리 (분식/일회성/매출채권/자본우회/영업권) + 감사보고서 키워드 통합
        - 0~100 score 산출

    Guide:
        Damodaran reference 기반 종합. score ≥ 70 = 다중 anomaly 의심.

    When:
        Earnings quality 종합 + AI 회계 anomaly 답변.

    How:
        IS+BS+CF + docs → Beneish + Sloan + audit flags + 5 카테고리.

    Requires:
        IS/BS/CF + docs 가용.

    Raises:
        없음.

    Example:
        >>> calcQualityAnomalies(company)["score"]
        45

    See Also:
        - calcBeneishTimeline : Beneish 시계열
        - calcRichardsonAccrual : 발생액 분해

    AIContext:
        "회계 anomaly 종합" 답변 시 score + flags 인용.
    """
    is_result = company.select("IS", ["매출액", "매출원가", "판매비와관리비", "당기순이익"])
    bs_result = company.select("BS", ["자산총계", "매출채권", "부채총계", "유형자산", "영업권"])
    cf_result = company.select("CF", ["영업활동현금흐름"])

    is_parsed = toDictBySnakeId(is_result)
    bs_parsed = toDictBySnakeId(bs_result)
    cf_parsed = toDictBySnakeId(cf_result)
    if is_parsed is None or bs_parsed is None:
        return None

    is_data, is_periods = is_parsed
    bs_data, _ = bs_parsed
    cf_data = cf_parsed[0] if cf_parsed else {}

    annual_years = [p for p in is_periods if p.isdigit() and len(p) == 4]
    if len(annual_years) < 2:
        return None
    t, t1 = annual_years[0], annual_years[1]

    v = _qualityInputs(is_data, bs_data, cf_data, t, t1)

    quality = _calcEarningsQualityFlagsBase(
        salesT=v["salesT"] or 0,
        salesT1=v["salesT1"] or 0,
        receivablesT=v["receivablesT"] or 0,
        receivablesT1=v["receivablesT1"] or 0,
        netIncomeT=v["niT"] or 0,
        ocfT=v["ocfT"] or 0,
        totalAssetsT=v["assetsT"] or 0,
        goodwillT=v["goodwillT"],
    )

    beneish = _beneishFromInputs(v)

    audit_flags = _collectAuditFlags(company)

    return {
        "score": quality["score"],
        "flags": quality["flags"],
        "beneish": beneish,
        "sloan": quality["sloanAccrual"],
        "auditFlags": audit_flags,
        "period": t,
    }
