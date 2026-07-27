"""3 방향성 신호 — Consensus / Flow / Revenue (Zacks 연구 기반).

calcConsensusDirection / calcFlowDirection / calcRevenueDirection — 애널리스트 컨센서스 / 자금
흐름 / 매출 방향 3 신호. predictionSignals.py 의 calc 10-12 분리.

Zacks: 컨센서스 방향이 실적 방향의 단일 최강 예측자 (70%).
"""

from __future__ import annotations

import logging

from dartlab.analysis.financial._predictionProbability import _DIRECTION_SCORES, _bayesUpdate, _calibrate
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

log = logging.getLogger(__name__)

_getF = _getF2 = _getF3 = _getF4 = _get


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


import json
from pathlib import Path as _Path

_SECTOR_DATA = json.loads(
    (
        _Path(__file__).resolve().parents[2]
        / "providers"
        / "mappers"
        / "mapperData"
        / "parserMappings"
        / "sectorPriors.json"
    ).read_text(encoding="utf-8")
)
_INDUSTRY_PRIOR: dict[str, float] = _SECTOR_DATA.get("priors", {})
_DEFAULT_PRIOR: float = _SECTOR_DATA.get("_metadata", {}).get("defaultPrior", 0.721)


def _getSectorKey(company) -> str | None:
    try:
        from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY

        sectorInfo = company.sector
        if sectorInfo is not None:
            igName = sectorInfo.industryGroup.name
            return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError, ImportError):
        pass
    return None


# calc 6: 다중 신호 종합
# ══════════════════════════════════════


# ══════════════════════════════════════
# calc 10: 컨센서스 매출 방향
# ══════════════════════════════════════


@memoizedCalc
def calcConsensusDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """컨센서스 매출 방향 — 애널리스트 추정 매출 vs 직전 실적.

    네이버 finance/annual에서 isConsensus="Y" 기간의 매출 추정치를 가져와서
    직전 실적 대비 성장/하락 방향을 판단한다.

    Zacks 연구: 컨센서스 방향이 실적 방향의 가장 강력한 단일 예측자 (70%).

    Capabilities:
        - 네이버 컨센서스 추정치와 직전 실적을 방향 신호로 변환.

    Returns
    -------
    dict
        consensusRevenue : float — 컨센서스 추정 매출 (원)
        lastActualRevenue : float — 직전 실적 매출 (원)
        consensusPeriod : str — 컨센서스 기간
        actualPeriod : str — 실적 기간
        expectedGrowthPct : float — 예상 성장률 (%)
        direction : str — 방향 ("up" | "down" | "flat")
        confidence : str — 신뢰도 ("high" | "medium" | "low")

    Guide:
        성장률 절대값 ≥ 10% 면 high, 3~10% medium.

    When:
        다음 연간 실적 예측 직전, 컨센서스 갱신 시점.

    How:
        m.stock.naver finance/annual JSON 파싱 → 매출 행 비교.

    Requires:
        stockCode 매핑, httpx 네트워크 접근.

    Raises:
        없음 — 네트워크/파싱 실패 시 None.

    Example:
        >>> calcConsensusDirection(company)
        {'direction': 'up', 'expectedGrowthPct': 8.5}

    See Also:
        - calcRevenueDirection : 자체 모멘텀.

    AIContext:
        외부 컨센서스 인용은 데이터 출처 명시 (네이버 finance).
    """
    stockCode = _getStockCode(company)
    if not stockCode:
        return None

    try:
        import httpx

        resp = httpx.get(
            f"https://m.stock.naver.com/api/stock/{stockCode}/finance/annual",
            headers={"User-Agent": "dartlab/1.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        fi = data.get("financeInfo", {})
        titles = fi.get("trTitleList", [])
        rows = fi.get("rowList", [])

        # 컨센서스 기간 + 직전 실적 기간 찾기
        cnsKey = None
        realKeys: list[str] = []
        for t in titles:
            if t.get("isConsensus") == "Y" and cnsKey is None:
                cnsKey = t["key"]
            elif t.get("isConsensus") == "N":
                realKeys.append(t["key"])

        if not cnsKey or not realKeys:
            return None

        lastRealKey = realKeys[-1]  # 가장 최신 실적

        # 매출 행 찾기
        for row in rows:
            if row.get("title") != "매출액":
                continue

            cnsValStr = row.get("columns", {}).get(cnsKey, {}).get("value", "")
            realValStr = row.get("columns", {}).get(lastRealKey, {}).get("value", "")
            if not cnsValStr or not realValStr:
                return None

            cnsVal = float(cnsValStr.replace(",", ""))
            realVal = float(realValStr.replace(",", ""))
            if realVal == 0:
                return None

            growthPct = (cnsVal - realVal) / abs(realVal) * 100
            direction = "up" if growthPct > 2 else ("down" if growthPct < -2 else "flat")

            return {
                "consensusRevenue": cnsVal,
                "lastActualRevenue": realVal,
                "consensusPeriod": cnsKey,
                "actualPeriod": lastRealKey,
                "expectedGrowthPct": round(growthPct, 1),
                "direction": direction,
                "confidence": "high" if abs(growthPct) > 10 else ("medium" if abs(growthPct) > 3 else "low"),
            }

    except (ImportError, ValueError, KeyError, TypeError):
        return None

    return None


# ══════════════════════════════════════
# calc 11: 수급 누적 방향
# ══════════════════════════════════════


@memoizedCalc
def calcFlowDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """수급 누적 방향 — 기관/외국인 순매수 분기 집계.

    최근 60거래일 기관+외국인 순매수 합계가 양이면 실적 개선 기대.
    "스마트머니는 실적을 안다" (Park et al., MDPI 2020).

    Capabilities:
        - 기관·외국인 순매수 누적을 실적 선행 신호로 환산.

    Returns
    -------
    dict
        foreignNet60d : int — 외국인 60거래일 순매수 (주)
        institutionNet60d : int — 기관 60거래일 순매수 (주)
        smartMoneyNet : int — 스마트머니 합계 (주)
        direction : str — 방향 ("up" | "down" | "flat")
        days : int — 집계 거래일 수 (일)
        confidence : str — 신뢰도 ("high" | "medium" | "low")

    Guide:
        스마트머니 합 > 100만 주 면 medium, 1000만 주 high.

    When:
        분기 실적 발표 1~2주 전 수급 선행 점검.

    How:
        m.stock.naver integration JSON 의 dealTrendInfos 누적.

    Requires:
        stockCode 매핑, httpx 네트워크 접근.

    Raises:
        없음 — 네트워크 실패 시 None.

    Example:
        >>> calcFlowDirection(company)
        {'direction': 'up', 'smartMoneyNet': 2500000}

    See Also:
        - calcConsensusDirection : 컨센서스 방향.

    AIContext:
        수급 데이터는 단기 변동 크므로 단독 결론 자제.
    """
    stockCode = _getStockCode(company)
    if not stockCode:
        return None

    try:
        import httpx

        resp = httpx.get(
            f"https://m.stock.naver.com/api/stock/{stockCode}/integration",
            headers={"User-Agent": "dartlab/1.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        deals = data.get("dealTrendInfos", [])
        if not deals or len(deals) < 3:
            return None

        # 최근 60거래일 집계
        recent = deals[:60]  # integration은 ~5일, 있는 만큼 사용
        foreignNet = 0
        instNet = 0
        for d in recent:
            fq = d.get("foreignerPureBuyQuant", "0")
            oq = d.get("organPureBuyQuant", "0")
            foreignNet += int(str(fq).replace(",", "").replace("+", ""))
            instNet += int(str(oq).replace(",", "").replace("+", ""))

        smartMoney = foreignNet + instNet
        direction = "up" if smartMoney > 0 else ("down" if smartMoney < 0 else "flat")

        return {
            "foreignNet60d": foreignNet,
            "institutionNet60d": instNet,
            "smartMoneyNet": smartMoney,
            "direction": direction,
            "days": len(recent),
            "confidence": "high" if abs(smartMoney) > 1000000 else ("medium" if abs(smartMoney) > 100000 else "low"),
        }

    except (ImportError, OSError, ValueError, KeyError, TypeError):
        return None


# ══════════════════════════════════════
# calc 12: 매출 모멘텀 (전분기 방향 유지)
# ══════════════════════════════════════


@memoizedCalc
def calcRevenueDirection(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 방향 예측 — 모멘텀 + 영업이익률 확인 + OLS 확인.

    검증 결과:
    - 모멘텀 단독: 72.1% (4825건, 172종목)
    - 모멘텀+영업이익률>0 일치: 76.1% (76% 시점)
    - 모멘텀+OLS 일치: 77.7% (68% 시점)
    - 2연속 모멘텀: 74.7%

    방법론:
    1. 기본: 전분기 YoY 방향 유지 (72.1%)
    2. 확인1: 영업이익률 > 0이면 신뢰도 상승 (76.1%) — API 불필요
    3. 확인2: OLS 외생변수와 일치하면 추가 상승 (77.7%)
    4. 2연속 같은 방향이면 74.7%

    학술 근거: M4/M5 Competition — 단순 방법이 최강.

    Capabilities:
        - 모멘텀+마진+OLS 결합 베이즈 사후확률 산출.

    Returns
    -------
    dict
        latestPeriod : str — 최신 분기
        latestYoyGrowth : float — 최신 분기 YoY 성장률 (%)
        direction : str — 예측 방향 ("up" | "down")
        streak : int — 연속 동일 방향 분기 수
        margin : float | None — 최신 영업이익률 (%)
        marginAgree : bool | None — 마진 방향 일치 여부
        olsAgree : bool | None — OLS 외생변수 방향 일치 여부
        confirms : int — 확인 신호 수 (0-3)
        probability : float — 보정된 베이즈 사후확률 (0.0-1.0)
        rawPosterior : float — 원시 사후확률 (0.0-1.0)
        industryPrior : float — 업종별 모멘텀 사전확률 (0.0-1.0)
        confidence : str — 신뢰도 ("very_high" | "high" | "medium" | "low")
        history : list[dict] — 최근 4분기 YoY 방향 이력

    Guide:
        confirms 2 이상 + streak 2 면 high confidence.

    When:
        분기 결산 직후 다음 분기 매출 방향 추정.

    How:
        IS 분기 YoY → 마진·OLS 일치 가산 → 베이즈 calibrate.

    Requires:
        IS 분기 6 개 이상, 업종 prior 매핑.

    Raises:
        없음 — 데이터 부족 시 None.

    Example:
        >>> calcRevenueDirection(company)
        {'direction': 'up', 'probability': 0.77}

    See Also:
        - calcConsensusDirection : 외부 컨센서스.

    AIContext:
        probability 인용 시 보정 사후확률임을 명시.
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None
    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    oiRow = isData.get("영업이익", {})

    qCols = sorted([p for p in isPeriods if "Q" in p], reverse=True)

    # 최근 분기 YoY
    directions: list[dict] = []
    for col in qCols[:6]:
        prevCol = f"{int(col[:4]) - 1}{col[-2:]}"
        if prevCol not in isPeriods:
            continue
        cur = _get(revRow, col) or None
        prev = _get(revRow, prevCol) or None
        if cur is not None and prev is not None and prev != 0:
            growth = (cur - prev) / abs(prev) * 100
            directions.append({"period": col, "yoyGrowth": round(growth, 1), "positive": growth > 0})

    if not directions:
        return None

    # 모멘텀 방향 (기본 예측: 전분기 방향 유지)
    latest = directions[0]
    direction = "up" if latest["positive"] else "down"

    # 2연속 모멘텀 (74.7%)
    streak = 1
    if len(directions) >= 2 and directions[0]["positive"] == directions[1]["positive"]:
        streak = 2
    if len(directions) >= 3 and streak == 2 and directions[1]["positive"] == directions[2]["positive"]:
        streak = 3

    # 확인1: 영업이익률 > 0 (76.1% — API 불필요, 가장 빠른 확인)
    latestRev = _get(revRow, directions[0]["period"]) or None
    latestOi = _get(oiRow, directions[0]["period"]) or None
    marginPositive = None
    margin = None
    if latestRev and latestOi and latestRev != 0:
        margin = latestOi / latestRev * 100
        marginPositive = margin > 0

    marginAgree = None
    if marginPositive is not None:
        # 매출 성장(+) + 영업이익률 양(+) → 일치
        # 매출 하락(-) + 영업이익률 음(-) → 일치
        marginAgree = latest["positive"] == marginPositive

    # 확인2: OLS 외생변수 (lazy import 로 module 순환 회피)
    from dartlab.analysis.financial.predictionSignals import calcMacroRegression  # noqa: PLC0415

    macroReg = calcMacroRegression(company, basePeriod=basePeriod)
    olsAgree = None
    if macroReg and macroReg.get("betas"):
        olsDirection = macroReg.get("_predictedDirection")
        if olsDirection is not None:
            olsAgree = (olsDirection == "up") == latest["positive"]

    # 베이즈 사후확률 갱신 — 업종별 사전확률에서 시작
    # 슈퍼예측가 원리: 사전확률이 정확할수록 사후확률도 정확
    _getSectorKey(company)
    industry = None
    try:
        from dartlab.gather.mapping.exogenousAxes import _lookupFromKindList

        industry, _ = _lookupFromKindList(_getStockCode(company) or "")
    except (ImportError, TypeError):
        pass
    posterior = _INDUSTRY_PRIOR.get(industry or "", _DEFAULT_PRIOR)

    # 신호 1: streak (2연속 → 74.7%, 3연속 → 더 강함)
    if streak >= 3:
        posterior = _bayesUpdate(posterior, 0.78)
    elif streak >= 2:
        posterior = _bayesUpdate(posterior, 0.747)

    # 신호 2: 영업이익률 (연속 값 — 크기 반영)
    if margin is not None:
        if latest["positive"]:
            # 매출 성장 + 마진 크기에 따라 차등 갱신
            marginEvidence = min(0.85, 0.72 + margin * 0.003) if margin > 0 else max(0.55, 0.72 - abs(margin) * 0.005)
        else:
            # 매출 하락 + 마진 부정이면 하락 확신 강화
            marginEvidence = max(0.55, 0.72 - margin * 0.003) if margin < 0 else min(0.85, 0.72 + abs(margin) * 0.003)
        posterior = _bayesUpdate(posterior, marginEvidence)

    # 신호 3: OLS 외생변수 (일치/불일치)
    if olsAgree is True:
        posterior = _bayesUpdate(posterior, 0.777)
    elif olsAgree is False:
        posterior = _bayesUpdate(posterior, 0.425)  # 불일치 시 하향 (OLS가 42.5%)

    # 보정: 원시 posterior를 실측 기반으로 재보정
    # 원시 78~85% → 실측 62~73%. 선형 보정으로 과신 제거.
    calibrated = _calibrate(posterior)

    # 신뢰도 등급 (보정된 확률 기준)
    if calibrated >= 0.78:
        confidence = "very_high"
    elif calibrated >= 0.73:
        confidence = "high"
    elif calibrated >= 0.65:
        confidence = "medium"
    else:
        confidence = "low"

    # 하위호환: confirms도 유지
    confirms = sum(1 for x in [marginAgree, olsAgree, streak >= 2] if x)

    return {
        "latestPeriod": latest["period"],
        "latestYoyGrowth": latest["yoyGrowth"],
        "direction": direction,
        "streak": streak,
        "margin": round(margin, 1) if margin is not None else None,
        "marginAgree": marginAgree,
        "olsAgree": olsAgree,
        "confirms": confirms,
        "probability": round(calibrated, 3),
        "rawPosterior": round(posterior, 3),
        "industryPrior": round(_INDUSTRY_PRIOR.get(industry or "", _DEFAULT_PRIOR), 3),
        "confidence": confidence,
        "history": directions[:4],
    }


__all__ = ["calcConsensusDirection", "calcFlowDirection", "calcRevenueDirection"]
