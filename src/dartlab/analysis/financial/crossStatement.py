"""재무제표 간 교차검증 — IS-CF 괴리, IS-BS 괴리, 종합 이상 점수.

3개 재무제표가 서로 맞는지, 비정상 패턴이 있는지를 시계열로 추적한다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import annualColsFromPeriods as _annualColsFromPeriods

_MAX_YEARS = 8


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _getFirst(data: dict, keys: list[str], col: str) -> float:
    for k in keys:
        row = data.get(k, {})
        v = row.get(col) if row else None
        if v is not None and v != 0:
            return v
    return 0


# ── IS-CF 괴리 ──


def calcIsCfDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """IS-CF 괴리 시계열 — 순이익 vs 영업CF.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "netIncome": float,
                    "ocf": float,
                    "divergence": float | None,
                    "direction": str | None,
                    "nonRecurringDistortion": bool,
                },
                ...
            ],
        }
    """
    isResult = company.select("IS", ["당기순이익", "영업이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    if isParsed is None or cfParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed

    niRow = isData.get("당기순이익", {})
    opRow = isData.get("영업이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})

    yCols = _annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ni = _get(niRow, col)
        ocf = _get(ocfRow, col)
        opIncome = _get(opRow, col)

        divergence = None
        direction = None
        if ni != 0:
            divergence = (ni - ocf) / abs(ni) * 100
            if ni > ocf:
                direction = "이익과대"
            elif ni < ocf:
                direction = "보수적"
            else:
                direction = "일치"

        # 일회성 왜곡 판정: 영업이익 대비 순이익이 극단적으로 작으면
        # 영업외 일회성 항목(중단사업손실, 대규모 손상 등)이 순이익을 지배
        nonRecurring = False
        if opIncome != 0 and abs(ni) < abs(opIncome) * 0.3:
            nonRecurring = True

        history.append(
            {
                "period": col,
                "netIncome": ni,
                "ocf": ocf,
                "divergence": divergence,
                "direction": direction,
                "nonRecurringDistortion": nonRecurring,
            }
        )

    return {"history": history} if history else None


# ── IS-BS 괴리 ──


def calcIsBsDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """IS-BS 괴리 시계열 — 매출 성장 vs 매출채권/재고 성장.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "revenueGrowth": float | None,
                    "receivableGrowth": float | None,
                    "inventoryGrowth": float | None,
                    "revRecGap": float | None,
                    "revInvGap": float | None,
                },
                ...
            ],
        }
    """
    isResult = company.select("IS", ["매출액"])
    bsResult = company.select("BS", ["매출채권및기타채권", "재고자산"])

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    revRow = isData.get("매출액", {})
    invRow = bsData.get("재고자산", {})

    _REC_KEYS = ["매출채권및기타채권"]

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for i, col in enumerate(yCols):
        rev = _get(revRow, col)
        rec = _getFirst(bsData, _REC_KEYS, col)
        inv = _get(invRow, col)

        revenueGrowth = None
        receivableGrowth = None
        inventoryGrowth = None

        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevRev = _get(revRow, prevCol)
            prevRec = _getFirst(bsData, _REC_KEYS, prevCol)
            prevInv = _get(invRow, prevCol)

            if prevRev > 0:
                revenueGrowth = (rev - prevRev) / prevRev * 100
            if prevRec > 0:
                receivableGrowth = (rec - prevRec) / prevRec * 100
            if prevInv > 0:
                inventoryGrowth = (inv - prevInv) / prevInv * 100

        revRecGap = None
        if revenueGrowth is not None and receivableGrowth is not None:
            revRecGap = receivableGrowth - revenueGrowth

        revInvGap = None
        if revenueGrowth is not None and inventoryGrowth is not None:
            revInvGap = inventoryGrowth - revenueGrowth

        history.append(
            {
                "period": col,
                "revenueGrowth": revenueGrowth,
                "receivableGrowth": receivableGrowth,
                "inventoryGrowth": inventoryGrowth,
                "revRecGap": revRecGap,
                "revInvGap": revInvGap,
            }
        )

    return {"history": history} if history else None


# ── 종합 이상 점수 ──


def calcAnomalyScore(company, *, basePeriod: str | None = None) -> dict | None:
    """종합 이상 점수 시계열 — 교차검증 결과 종합.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "score": float,
                    "components": dict,
                },
                ...
            ],
        }
    """
    isCf = calcIsCfDivergence(company, basePeriod=basePeriod)
    isBs = calcIsBsDivergence(company, basePeriod=basePeriod)

    if isCf is None:
        return None

    # 발생액 정보 (earningsQuality에서 가져오기)
    from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis, calcBeneishTimeline

    accrual = calcAccrualAnalysis(company, basePeriod=basePeriod)
    beneish = calcBeneishTimeline(company, basePeriod=basePeriod)

    # 기간별 데��터 매핑
    isCfMap = {h["period"]: h for h in isCf["history"]} if isCf else {}
    isBsMap = {h["period"]: h for h in isBs["history"]} if isBs else {}
    accrualMap = {h["period"]: h for h in accrual["history"]} if accrual else {}
    beneishMap = {h["period"]: h for h in beneish["history"]} if beneish else {}

    periods = list(isCfMap.keys())
    if not periods:
        return None

    history = []
    for period in periods:
        score = 0
        components = {}

        # 1. IS-CF 괴리 (0~30점)
        cf = isCfMap.get(period, {})
        div = cf.get("divergence")
        if div is not None:
            cfScore = min(30, abs(div) / 100 * 30)
            # 일회성 왜곡(중단사업손실 등)이면 점수 절반 감쇄
            if cf.get("nonRecurringDistortion"):
                cfScore = cfScore * 0.5
            score += cfScore
            components["isCfDivergence"] = cfScore

        # 2. IS-BS 괴리: 매출채권 (0~20점)
        bs = isBsMap.get(period, {})
        recGap = bs.get("revRecGap")
        if recGap is not None and recGap > 0:
            recScore = min(20, recGap / 50 * 20)
            score += recScore
            components["receivableGap"] = recScore

        # 3. IS-BS 괴리: 재고 (0~20점)
        invGap = bs.get("revInvGap")
        if invGap is not None and invGap > 0:
            invScore = min(20, invGap / 50 * 20)
            score += invScore
            components["inventoryGap"] = invScore

        # 4. 발생액 (0~15점)
        acc = accrualMap.get(period, {})
        sar = acc.get("sloanAccrualRatio")
        if sar is not None:
            accScore = min(15, abs(sar) / 0.15 * 15)
            score += accScore
            components["accrualRatio"] = accScore

        # 5. Beneish M-Score (0~15점)
        ben = beneishMap.get(period, {})
        ms = ben.get("mScore")
        if ms is not None and ms > -2.22:
            # -2.22~-1.78 = 회색, -1.78+ = 위험
            mScoreNorm = min(15, max(0, (ms + 2.22) / 0.88 * 15))
            score += mScoreNorm
            components["beneishMScore"] = mScoreNorm

        history.append(
            {
                "period": period,
                "score": min(100, score),
                "components": components,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def calcCrossStatementFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """교차검증 경고 신호."""
    flags = []

    isCf = calcIsCfDivergence(company, basePeriod=basePeriod)
    if isCf and isCf["history"]:
        h0 = isCf["history"][0]
        div = h0.get("divergence")
        if div is not None and abs(div) > 50:
            suffix = " (일회성 영업외항목 왜곡)" if h0.get("nonRecurringDistortion") else ""
            flags.append(f"IS-CF 괴리 {div:.0f}% — 순이익 대비 현금흐름 극심한 차이{suffix}")

    isBs = calcIsBsDivergence(company, basePeriod=basePeriod)
    if isBs and isBs["history"]:
        h0 = isBs["history"][0]
        recGap = h0.get("revRecGap")
        if recGap is not None and recGap > 20:
            flags.append(f"매출채��� 성장이 매출 성장보다 {recGap:.0f}%p 빠름 — 매출 인식 의심")
        invGap = h0.get("revInvGap")
        if invGap is not None and invGap > 20:
            flags.append(f"재고 성장이 매출 성장보다 {invGap:.0f}%p 빠름 — 재고 적체 또는 부풀리기")

    anomaly = calcAnomalyScore(company, basePeriod=basePeriod)
    if anomaly and anomaly["history"]:
        h0 = anomaly["history"][0]
        if h0["score"] > 70:
            flags.append(f"종합 이상점수 {h0['score']:.0f} — 재무제표 신뢰성 주의")

    return flags
