"""1-4 현금흐름 — 계산만 담당.

CF 3구간(영업/투자/재무) + FCF + 이익의 현금 뒷받침 + CF 패턴.
블록 조립은 review/builders.py가 한다.
"""

from __future__ import annotations

_MAX_YEARS = 8


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult -> ({계정명: {period: val}}, periodCols)."""
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualColsFromPeriods(
    periods: list[str],
    maxYears: int = _MAX_YEARS,
    basePeriod: str | None = None,
) -> list[str]:
    """연도 컬럼만 추출 (basePeriod 지원)."""
    from dartlab.analysis.financial._helpers import annualColsFromPeriods

    return annualColsFromPeriods(periods, maxYears=maxYears, basePeriod=basePeriod)


def _get(row: dict, col: str) -> float:
    """dict에서 안전하게 값 꺼내기 (None -> 0)."""
    v = row.get(col) if row else None
    return v if v is not None else 0


# ── CF 패턴 분류 ──


def _classifyCfPattern(ocf: float, icf: float, fcf: float) -> str | None:
    """영업/투자/재무 CF 부호 조합으로 패턴 분류."""

    def _s(v: float) -> str:
        if v > 0:
            return "+"
        if v < 0:
            return "-"
        return "0"

    patterns = {
        ("+", "-", "-"): "성숙형 — 영업으로 벌어 투자하고 부채 상환",
        ("+", "-", "+"): "확장형 — 영업 + 외부 조달로 적극 투자",
        ("+", "+", "-"): "구조조정형 — 자산 매각하며 부채 상환",
        ("-", "-", "+"): "위기형 — 영업 적자를 외부 차입으로 메움",
        ("-", "+", "+"): "축소형 — 자산 매각 + 차입으로 영업 적자 보전",
        ("-", "+", "-"): "전환형 — 자산 매각으로 부채 상환, 영업 회복 필요",
        # 재무CF가 0(미보고)인 경우 — 영업/투자만으로 부분 분류
        ("+", "-", "0"): "성숙형 — 영업으로 벌어 투자 (재무CF 미보고)",
        ("-", "-", "0"): "위기형 — 영업+투자 모두 유출 (재무CF 미보고)",
        ("+", "+", "0"): "구조조정형 — 자산 매각 진행 (재무CF 미보고)",
        ("-", "+", "0"): "축소형 — 자산 매각으로 영업 적자 보전 (재무CF 미보고)",
    }
    return patterns.get((_s(ocf), _s(icf), _s(fcf)))


# ── 메인: CF 3구간 + FCF ──


def calcCashFlowOverview(company, *, basePeriod: str | None = None) -> dict | None:
    """영업CF/투자CF/재무CF + FCF 시계열.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "ocf": float, "icf": float, "fcf_financing": float,
                    "capex": float, "fcf": float,
                    "pattern": str | None,
                },
                ...
            ],
        }
    """
    cfAccounts = [
        "영업활동현금흐름",
        "투자활동현금흐름",
        "재무활동으로인한현금흐름",
        "유형자산의취득",
        "무형자산의취득",
    ]
    result = company.select("CF", cfAccounts)
    parsed = _toDict(result)
    if parsed is None:
        return None

    data, allPeriods = parsed
    ocfRow = data.get("영업활동현금흐름") or data.get("영업활동으로인한현금흐름")
    if ocfRow is None:
        return None
    icfRow = data.get("투자활동현금흐름") or data.get("투자활동으로인한현금흐름") or {}
    finRow = data.get("재무활동으로인한현금흐름") or data.get("재무활동현금흐름") or {}
    capexRow = data.get("유형자산의취득", {})
    intCapexRow = data.get("무형자산의취득", {})

    yCols = _annualColsFromPeriods(allPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ocf = _get(ocfRow, col)
        icf = _get(icfRow, col)
        fin = _get(finRow, col)
        # CAPEX: CF에서 음수로 나옴 -> abs
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        fcf = ocf - capex

        entry = {
            "period": col,
            "ocf": ocf,
            "icf": icf,
            "fcfFinancing": fin,
            "capex": capex,
            "fcf": fcf,
            "pattern": _classifyCfPattern(ocf, icf, fin),
        }
        history.append(entry)

    if not history:
        return None
    return {"history": history}


# ── 이익의 현금 뒷받침 ──


def calcCashQuality(company, *, basePeriod: str | None = None) -> dict | None:
    """영업CF/순이익, 영업CF/매출 — 이익이 현금으로 뒷받침되는가.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "ocf": float, "netIncome": float, "revenue": float,
                    "ocfToNi": float | None,
                    "ocfMargin": float | None,
                },
                ...
            ],
        }
    """
    cfResult = company.select("CF", ["영업활동현금흐름"])
    isResult = company.select("IS", ["당기순이익", "매출액"])

    cfParsed = _toDict(cfResult)
    isParsed = _toDict(isResult)
    if cfParsed is None or isParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    isData, _ = isParsed

    ocfRow = cfData.get("영업활동현금흐름", {})
    niRow = isData.get("당기순이익", {})
    revRow = isData.get("매출액", {})

    yCols = _annualColsFromPeriods(cfPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ocf = _get(ocfRow, col)
        ni = _get(niRow, col)
        rev = _get(revRow, col)

        ocfToNi = ocf / ni * 100 if ni != 0 else None
        # 극단값 클램핑: ±1000% 초과는 "의미 없는 비율" → None
        if ocfToNi is not None and abs(ocfToNi) > 1000:
            ocfToNi = None
        ocfMargin = ocf / rev * 100 if rev > 0 else None

        history.append(
            {
                "period": col,
                "ocf": ocf,
                "netIncome": ni,
                "revenue": rev,
                "ocfToNi": ocfToNi,
                "ocfMargin": ocfMargin,
            }
        )

    if not history:
        return None
    return {"history": history}


# ── CF 플래그 ──


def calcCashFlowFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """현금흐름 경고 신호."""
    flags = []

    overview = calcCashFlowOverview(company, basePeriod=basePeriod)
    if overview and overview["history"]:
        h0 = overview["history"][0]

        # 영업CF 적자
        if h0["ocf"] < 0:
            flags.append("영업CF 적자 — 본업에서 현금이 나오지 않음")

        # FCF 적자
        if h0["fcf"] < 0 and h0["ocf"] > 0:
            flags.append("FCF 적자 — 영업CF보다 투자가 큼")

        # 위기형/축소형 패턴
        pat = h0.get("pattern", "")
        if pat and ("위기형" in pat or "축소형" in pat):
            flags.append(f"CF 패턴: {pat}")

        # 영업CF 3년 연속 감소
        hist = overview["history"]
        if len(hist) >= 3:
            ocfs = [h["ocf"] for h in hist[:3]]
            if ocfs[0] < ocfs[1] < ocfs[2]:
                flags.append("영업CF 3년 연속 감소")

    quality = calcCashQuality(company, basePeriod=basePeriod)
    if quality and quality["history"]:
        q0 = quality["history"][0]

        # 영업CF/순이익 < 40% (이익 대비 현금 부족)
        ratio = q0.get("ocfToNi")
        if ratio is not None and 0 < ratio < 40:
            flags.append(f"영업CF/순이익 {ratio:.0f}% — 이익의 현금 뒷받침 부족")

        # 영업CF 마진 < 0
        margin = q0.get("ocfMargin")
        if margin is not None and margin < 0:
            flags.append(f"영업CF 마진 {margin:.1f}% — 매출 대비 현금 유출")

    return flags


# ── 영업CF 내부 분해 (BS 변동 기반) ──


def calcOcfDecomposition(company, *, basePeriod: str | None = None) -> dict | None:
    """영업CF를 구성요소로 분해 — 현금흐름의 원천을 파악.

    대부분 기업이 CF에 개별 조정항목을 안 쓰므로 BS 변동으로 간접 추정.

    OCF ≈ 순이익 + 비현금비용(감가상각 추정) + 운전자본 변동
    운전자본 변동 = -(delta_AR) - (delta_Inv) + (delta_AP)

    반환::

        {
            "history": [
                {"period": str, "ni": float, "ocf": float,
                 "depEstimate": float, "wcEffect": float,
                 "arChange": float, "invChange": float, "apChange": float,
                 "residual": float},
                ...
            ],
        }
    """
    isResult = company.select("IS", ["당기순이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select(
        "BS",
        ["매출채권및기타채권", "재고자산", "매입채무", "유형자산"],
    )

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or cfParsed is None or bsParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed
    bsData, _ = bsParsed

    niRow = isData.get("당기순이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    arRow = bsData.get("매출채권및기타채권", {})
    invRow = bsData.get("재고자산", {})
    apRow = bsData.get("매입채무", {})
    ppeRow = bsData.get("유형자산", {})

    from dartlab.analysis.financial._helpers import annualColsFromPeriods

    yCols = annualColsFromPeriods(cfPeriods, basePeriod, 9)
    if len(yCols) < 2:
        return None

    history = []
    for i in range(len(yCols) - 1):
        col = yCols[i]
        prevCol = yCols[i + 1]

        ni = _get(niRow, col)
        ocf = _get(ocfRow, col)
        ppe = _get(ppeRow, col)

        # 감가상각 추정 (유형자산/10)
        depEst = ppe / 10 if ppe > 0 else 0

        # 운전자본 변동 (BS delta)
        arChange = _get(arRow, col) - _get(arRow, prevCol)  # 증가=현금유출
        invChange = _get(invRow, col) - _get(invRow, prevCol)
        apChange = _get(apRow, col) - _get(apRow, prevCol)  # 증가=현금유입
        wcEffect = -arChange - invChange + apChange

        # 잔차 (설명 안 되는 부분: 영업외, 세금, 기타 조정)
        residual = ocf - ni - depEst - wcEffect

        history.append({
            "period": col,
            "ni": ni,
            "ocf": ocf,
            "depEstimate": round(depEst),
            "wcEffect": round(wcEffect),
            "arChange": round(arChange),
            "invChange": round(invChange),
            "apChange": round(apChange),
            "residual": round(residual),
        })

    return {"history": history} if history else None
