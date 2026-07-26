"""corporate 신호 4 종 (Disclosure / Inventory / Announcement / SupplyChain).

calcDisclosureDelta / calcInventoryDivergence / calcAnnouncementTiming / calcSupplyChainSignal
+ _getLinkedCompanies + _loadGrowthMap. 공시 텍스트·재고·공시 시점·공급망 4 도메인의 예측 신호.

predictionSignals.py 의 calc 5/6/7/8 분리.
"""

from __future__ import annotations

import logging

from dartlab.analysis.financial._predictionUtils import _DIRECTION_SCORES, _bayesUpdate, _clamp
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

log = logging.getLogger(__name__)

_getF = _getF2 = _getF3 = _get

_MAX_YEARS = 8


def _getStockCode(company) -> str | None:
    return getattr(company, "stockCode", None)


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


# ══════════════════════════════════════
# calc 5: 공시 변화 신호
# ══════════════════════════════════════


@memoizedCalc
def calcDisclosureDelta(company, *, basePeriod: str | None = None) -> dict | None:
    """공시 변화 신호 — diff 결과를 예측 신호로 변환.

    공시 텍스트 변화량을 방향성 신호로 해석한다.
    FinBERT 등 톤 분석은 미적용 — 변화 크기만 사용.

    Capabilities:
        - 공시 텍스트 변화율을 방향성 신호로 환산.

    Returns
    -------
    dict
        overallChangeRate : float — 전체 공시 변화율 (%)
        riskChangeRate : float — 리스크 관련 토픽 변화율 (%)
        businessChangeRate : float — 사업 관련 토픽 변화율 (%)
        revenueRelatedChange : float — 매출 관련 토픽 변화율 (%)
        signalDirection : str — 방향성 ("positive" | "negative" | "neutral")
        signalStrength : str — 신호 강도 ("strong" | "moderate" | "weak")
        topChangedTopics : list[dict] — 변화율 상위 5개 토픽 (topic, changeRate)

    Guide:
        리스크 토픽 변화율 우선, 사업 토픽 변화는 보조.

    When:
        분기 공시 갱신 직후 텍스트 변화 모니터링.

    How:
        company.diff() 토픽 changeRate 를 가중 분류.

    Requires:
        company.diff() 가능 (텍스트 diff 캐시).

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> calcDisclosureDelta(company)
        {'signalDirection': 'negative', ...}

    See Also:
        - calcAnnouncementTiming : 공시 시점 패턴.

    AIContext:
        리스크 토픽 변화율이 30% 이상이면 부정 신호로 인용.
    """
    try:
        diffResult = company.diff()
    except (AttributeError, TypeError):
        return None

    if diffResult is None:
        return None

    overallChangeRate = getattr(diffResult, "changeRate", None) or 0.0

    # 토픽별 변화율 추출
    riskChangeRate = 0.0
    businessChangeRate = 0.0
    revenueChangeRate = 0.0
    topChangedTopics = []

    riskTopics = {"riskFactors", "riskDerivative", "contingentLiabilities"}
    businessTopics = {"businessOverview", "businessContent"}
    revenueTopics = {"revenue", "salesSegment", "productionStatus"}

    topicChanges = getattr(diffResult, "topicChanges", None) or []
    for tc in topicChanges:
        topic = getattr(tc, "topic", "")
        changeRate = getattr(tc, "changeRate", 0) or 0

        if topic in riskTopics:
            riskChangeRate = max(riskChangeRate, changeRate)
        elif topic in businessTopics:
            businessChangeRate = max(businessChangeRate, changeRate)
        elif topic in revenueTopics:
            revenueChangeRate = max(revenueChangeRate, changeRate)

        if changeRate > 20:
            topChangedTopics.append({"topic": topic, "changeRate": round(changeRate, 1)})

    # 방향성 신호 판단
    if riskChangeRate > 60:
        signalDirection = "negative"
        signalStrength = "strong"
    elif riskChangeRate > 30:
        signalDirection = "negative"
        signalStrength = "moderate"
    elif overallChangeRate < 10:
        signalDirection = "neutral"
        signalStrength = "weak"
    elif businessChangeRate > 40 and riskChangeRate < 20:
        signalDirection = "positive"
        signalStrength = "moderate"
    else:
        signalDirection = "neutral"
        signalStrength = "weak"

    # 변화 큰 토픽 정렬
    topChangedTopics.sort(key=lambda x: x["changeRate"], reverse=True)

    return {
        "overallChangeRate": round(overallChangeRate, 1),
        "riskChangeRate": round(riskChangeRate, 1),
        "businessChangeRate": round(businessChangeRate, 1),
        "revenueRelatedChange": round(revenueChangeRate, 1),
        "signalDirection": signalDirection,
        "signalStrength": signalStrength,
        "topChangedTopics": topChangedTopics[:5],
    }


# ══════════════════════════════════════
# calc 8: 재고/매출채권 괴리 신호
# ══════════════════════════════════════


@memoizedCalc
def calcInventoryDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """재고/매출채권 괴리 — 수요 둔화 선행 지표.

    재고 증가율 > 매출 증가율 = 수요 둔화 (NYU Stern).
    매출채권 증가율 > 매출 증가율 = 회수 악화.
    NOA 급증 = 이익 조작 가능성 (Oler 2024).

    Capabilities:
        - 재고·매출채권 증가율과 매출 증가율 괴리 점수화.

    Returns
    -------
    dict
        history : list[dict] — 연도별 시계열 (inventory, receivables, revenue, inventoryGrowth(%), revenueGrowth(%), divergence(%p), arDivergence(%p), dso(일), dio(일), noa(원))
        inventorySignal : str — 재고 신호 ("building" | "liquidating" | "stable")
        receivableSignal : str — 매출채권 신호 ("deteriorating" | "improving" | "stable")
        noaGrowth : float | None — NOA 성장률 (%)
        riskScore : int — 리스크 점수 (점, 0-100)

    Guide:
        괴리 폭 ≥ 10%p 면 명확 신호, 5~10%p 면 약신호.

    When:
        분기 결산 후 운전자본 변화 감시 시점.

    How:
        BS 재고·매출채권 ÷ IS 매출 증가율 비교 후 점수화.

    Requires:
        BS·IS 다년치 (최소 2 기), snake_id 매핑 완료.

    Raises:
        없음 — 결측 시 None.

    Example:
        >>> calcInventoryDivergence(company)
        {'inventorySignal': 'building', 'riskScore': 65}

    See Also:
        - calcDisclosureDelta : 공시 변화 신호.

    AIContext:
        riskScore ≥ 60 이면 이익 질 의심 근거로 인용.
    """
    bsResult = company.select(
        "BS", ["재고자산", "매출채권및기타채권", "매출채권", "매입채무및기타채무", "매입채무", "자산총계"]
    )
    isResult = company.select("IS", ["매출액", "매출원가"])

    bsParsed = toDictBySnakeId(bsResult)
    isParsed = toDictBySnakeId(isResult)
    if bsParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, _ = isParsed

    invRow = bsData.get("재고자산", {})
    arRow = bsData.get("매출채권및기타채권", bsData.get("매출채권", {}))
    apRow = bsData.get("매입채무및기타채무", bsData.get("매입채무", {}))
    taRow = bsData.get("자산총계", {})
    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if len(yCols) < 3:
        return None

    history = []
    for i, col in enumerate(yCols):
        inv = _get(invRow, col)
        ar = _get(arRow, col)
        ap = _get(apRow, col)
        ta = _get(taRow, col)
        rev = _get(revRow, col)
        cogs = _get(cogsRow, col)

        # DSO / DIO
        dso = (ar / rev * 365) if rev > 0 else None
        dio = (inv / cogs * 365) if cogs > 0 else None

        # YoY 성장률
        invGrowth = None
        revGrowth = None
        arGrowth = None
        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevInv = _get(invRow, prevCol)
            prevRev = _get(revRow, prevCol)
            prevAr = _get(arRow, prevCol)
            if prevInv > 0:
                invGrowth = ((inv - prevInv) / prevInv) * 100
            if prevRev > 0:
                revGrowth = ((rev - prevRev) / prevRev) * 100
            if prevAr > 0:
                arGrowth = ((ar - prevAr) / prevAr) * 100

        divergence = None
        if invGrowth is not None and revGrowth is not None:
            divergence = invGrowth - revGrowth

        arDivergence = None
        if arGrowth is not None and revGrowth is not None:
            arDivergence = arGrowth - revGrowth

        # NOA = (자산 - 현금) - (부채 - 금융부채) ≈ 자산 - 매입채무 - 현금 (간이)
        noa = ta - ap if ta > 0 else None

        history.append(
            {
                "period": col,
                "inventory": inv,
                "receivables": ar,
                "revenue": rev,
                "inventoryGrowth": round(invGrowth, 1) if invGrowth is not None else None,
                "revenueGrowth": round(revGrowth, 1) if revGrowth is not None else None,
                "divergence": round(divergence, 1) if divergence is not None else None,
                "arDivergence": round(arDivergence, 1) if arDivergence is not None else None,
                "dso": round(dso, 1) if dso is not None else None,
                "dio": round(dio, 1) if dio is not None else None,
                "noa": noa,
            }
        )

    if not history:
        return None

    # 재고 신호 판단 (최근 2년)
    recentDiv = [h["divergence"] for h in history[:2] if h["divergence"] is not None]
    if recentDiv:
        avgDiv = sum(recentDiv) / len(recentDiv)
        if avgDiv > 5:
            inventorySignal = "building"
        elif avgDiv < -5:
            inventorySignal = "liquidating"
        else:
            inventorySignal = "stable"
    else:
        inventorySignal = "stable"

    # 매출채권 신호
    recentArDiv = [h["arDivergence"] for h in history[:2] if h["arDivergence"] is not None]
    if recentArDiv:
        avgArDiv = sum(recentArDiv) / len(recentArDiv)
        if avgArDiv > 5:
            receivableSignal = "deteriorating"
        elif avgArDiv < -5:
            receivableSignal = "improving"
        else:
            receivableSignal = "stable"
    else:
        receivableSignal = "stable"

    # NOA 성장률
    noaGrowth = None
    if len(history) >= 2 and history[0]["noa"] and history[1]["noa"] and history[1]["noa"] > 0:
        noaGrowth = ((history[0]["noa"] - history[1]["noa"]) / abs(history[1]["noa"])) * 100

    # 리스크 점수 (0-100)
    riskScore = 30  # 기본
    if inventorySignal == "building":
        riskScore += 25
    if receivableSignal == "deteriorating":
        riskScore += 20
    if noaGrowth is not None and noaGrowth > 20:
        riskScore += 25
    riskScore = min(100, riskScore)

    return {
        "history": history,
        "inventorySignal": inventorySignal,
        "receivableSignal": receivableSignal,
        "noaGrowth": round(noaGrowth, 1) if noaGrowth is not None else None,
        "riskScore": riskScore,
    }


# ══════════════════════════════════════
# calc 9: 동종업계 공시 타이밍
# ══════════════════════════════════════


@memoizedCalc
def calcAnnouncementTiming(company, *, basePeriod: str | None = None) -> dict | None:
    """동종업계 공시 타이밍 — 선발 기업 실적으로 후발 예측.

    같은 업종에서 이미 실적을 발표한 기업들의 성장 방향을 집계한다.
    Ramnath 2002, Thomas & Zhang 2008 — 20년+ 검증된 anomaly.

    Capabilities:
        - 선발 발표 피어의 성장 방향을 후발 예측 신호로 변환.

    Returns
    -------
    dict
        sectorKey : str — 업종 키
        sectorPeersReported : int — 실적 발표 동종 기업 수
        sectorPeersTotal : int — 동종 업종 전체 기업 수
        reportedDirection : dict — 방향별 기업 수 (up, down, flat)
        bellwetherSignal : str — 벨웨더 신호 ("positive" | "negative" | "neutral")
        peerConsensus : float — 피어 합의 점수 (-1.0 ~ +1.0)
        confidence : str — 신뢰도 ("high" | "medium" | "low")

    Guide:
        피어 발표 수 5 이상일 때 신뢰도 medium, 10 이상 high.

    When:
        분기 실적 발표 시즌 초중반, 후발 기업 예측 직전.

    How:
        Scan 횡단면 growth → 발표 완료 피어의 up/down 카운트.

    Requires:
        Scan 사용 가능, 업종 분류 매핑.

    Raises:
        없음 — Scan 실패 시 None.

    Example:
        >>> calcAnnouncementTiming(company)
        {'bellwetherSignal': 'positive', ...}

    See Also:
        - calcSupplyChainSignal : 공급망 신호.

    AIContext:
        bellwetherSignal 은 동종 피어 합의로 인용 (단일 기업 예측 아님).
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 업종 정보
    sectorKey = _getSectorKey(company)
    if sectorKey is None:
        return None

    # scan growth에서 동종 업종 성장률 로드
    try:
        from dartlab.scan import Scan

        scan = Scan()
        growthResult = scan("growth")
        if growthResult is None or not hasattr(growthResult, "df"):
            return None

        df = growthResult.df
    except (ImportError, ValueError, AttributeError):
        return None

    # 업종 필터 (sector 컬럼이 있으면 사용, 없으면 전체)
    sectorCol = None
    for col in ("sector", "industry", "industryGroup", "업종"):
        if col in df.columns:
            sectorCol = col
            break

    if sectorCol:
        peerDf = df.filter(df[sectorCol] == sectorKey)
    else:
        return None

    if peerDf.height < 3:
        return None

    # 성장률 방향 집계
    growthCol = None
    for col in ("revenueGrowth", "revenueCagr3y", "growth", "매출성장률"):
        if col in peerDf.columns:
            growthCol = col
            break

    if growthCol is None:
        return None

    codeCol = "stockCode" if "stockCode" in peerDf.columns else peerDf.columns[0]
    directions = {"up": 0, "down": 0, "flat": 0}
    totalPeers = peerDf.height
    selfExcluded = False

    for row in peerDf.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if code == stockCode:
            selfExcluded = True
            continue
        g = row.get(growthCol)
        if g is None:
            continue
        g = float(g)
        if g > 2:
            directions["up"] += 1
        elif g < -2:
            directions["down"] += 1
        else:
            directions["flat"] += 1

    reported = sum(directions.values())
    if reported < 2:
        return None

    # 피어 합의 점수 (-1.0 ~ +1.0)
    peerConsensus = (directions["up"] - directions["down"]) / reported

    # 벨웨더 신호 (다수 방향)
    maxDir = max(directions, key=directions.get)
    if directions[maxDir] / reported >= 0.6:
        bellwetherSignal = "positive" if maxDir == "up" else ("negative" if maxDir == "down" else "neutral")
    else:
        bellwetherSignal = "neutral"

    confidence = "high" if reported >= 5 else ("medium" if reported >= 3 else "low")

    return {
        "sectorKey": sectorKey,
        "sectorPeersReported": reported,
        "sectorPeersTotal": totalPeers - (1 if selfExcluded else 0),
        "reportedDirection": directions,
        "bellwetherSignal": bellwetherSignal,
        "peerConsensus": round(peerConsensus, 3),
        "confidence": confidence,
    }


# ══════════════════════════════════════
# calc 10: 공급망 모멘텀
# ══════════════════════════════════════


@memoizedCalc
def calcSupplyChainSignal(company, *, basePeriod: str | None = None) -> dict | None:
    """공급망 모멘텀 — 관계사 실적이 이 회사를 선행.

    Cohen & Frazzini 2008 (J. Finance) — 고객사 실적이 공급사를 1-2분기 선행.
    DART 투자관계 + 관계사 거래에서 연결 기업을 식별하고,
    상장 관계사의 성장률로 이 회사에 대한 전파 신호를 계산.

    Capabilities:
        - 상장 관계사 성장 시계열로 자사 선행 신호 추정.

    Returns
    -------
    dict
        linkedCompanies : list[dict] — 상장 관계사 목록 (code, name, relationship, revenueGrowth(%))
        networkMomentum : float — 정규화 모멘텀 (-1.0 ~ +1.0)
        nLinkedListed : int — 상장 관계사 수
        supplyChainRisk : str — 공급망 리스크 ("high" | "moderate" | "low")
        confidence : str — 신뢰도 ("high" | "medium" | "low")

    Guide:
        상장 관계사 3 개 이상일 때 medium, 5 개 이상 high.

    When:
        고객·공급망 의존 높은 기업의 분기 결산 예측 직전.

    How:
        DART 투자관계·관계사 거래 → 상장 코드 → growth 가중 평균.

    Requires:
        Scan growth 사용 가능, 관계사 매핑 데이터.

    Raises:
        없음 — 관계사 결측 시 None.

    Example:
        >>> calcSupplyChainSignal(company)
        {'networkMomentum': 0.42, ...}

    See Also:
        - calcAnnouncementTiming : 동종 발표 타이밍.

    AIContext:
        networkMomentum ≥ 0.3 이면 공급망 호조 근거로 인용.
    """
    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    # 관계사 네트워크 추출
    linkedCompanies = _getLinkedCompanies(company, stockCode)
    if not linkedCompanies:
        return None

    # 상장 관계사의 성장률 조회 (scan growth)
    growthMap = _loadGrowthMap()
    if not growthMap:
        return None

    enriched = []
    for lc in linkedCompanies:
        code = lc.get("code", "")
        growth = growthMap.get(code)
        if growth is not None:
            enriched.append(
                {
                    "code": code,
                    "name": lc.get("name", ""),
                    "relationship": lc.get("relationship", ""),
                    "revenueGrowth": round(growth, 1),
                }
            )

    if not enriched:
        return None

    # 가중 평균 모멘텀
    growths = [e["revenueGrowth"] for e in enriched]
    networkMomentum = sum(growths) / len(growths)
    # 정규화 (-1 ~ +1)
    normalizedMomentum = _clamp(networkMomentum / 30)

    # 공급망 리스크
    negCount = sum(1 for g in growths if g < -5)
    if negCount / len(growths) > 0.5:
        supplyChainRisk = "high"
    elif negCount / len(growths) > 0.25:
        supplyChainRisk = "moderate"
    else:
        supplyChainRisk = "low"

    confidence = "high" if len(enriched) >= 5 else ("medium" if len(enriched) >= 2 else "low")

    return {
        "linkedCompanies": enriched[:10],
        "networkMomentum": round(normalizedMomentum, 3),
        "nLinkedListed": len(enriched),
        "supplyChainRisk": supplyChainRisk,
        "confidence": confidence,
    }


def _getLinkedCompanies(company, stockCode: str) -> list[dict]:
    """관계사/투자회사 목록 추출."""
    linked = []

    # 1. 투자관계 (network edges에서)
    try:
        from dartlab.scan.network.edges import buildInvestEdges

        investDf = buildInvestEdges(stockCode)
        if investDf is not None and hasattr(investDf, "height") and investDf.height > 0:
            for row in investDf.iter_rows(named=True):
                toCode = row.get("to_code", "")
                if toCode and row.get("is_listed"):
                    linked.append(
                        {
                            "code": toCode,
                            "name": row.get("to_name", ""),
                            "relationship": "투자",
                        }
                    )
    except (ImportError, ValueError, TypeError):
        pass

    # 2. 관계사 거래 (relatedPartyTx 파이프라인 직접 호출)
    # Company facade namespace 제거(Plan v10 P3) 후 getattr(company, "relatedPartyTx")
    # 는 항상 None 반환하는 dead branch 였음. KRW 6자리 종목에만 호출.
    try:
        stockCode = getattr(company, "stockCode", None)
        if (
            isinstance(stockCode, str)
            and len(stockCode) == 6
            and stockCode.isdigit()
            and getattr(company, "currency", None) == "KRW"
        ):
            from dartlab.analysis.financial.governance import _loadRelatedPartyTx

            rpt = _loadRelatedPartyTx(company)
            if rpt and rpt.revenueTxDf is not None:
                for row in rpt.revenueTxDf.iter_rows(named=True):
                    entity = row.get("entity", "")
                    if entity and entity not in {lc["name"] for lc in linked}:
                        linked.append(
                            {
                                "code": "",
                                "name": entity,
                                "relationship": "거래",
                            }
                        )
    except (
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        FileNotFoundError,
        RuntimeError,  # DART 다운로드 실패 (404 등) — mock/신규 종목에서 발생
        OSError,  # 네트워크 단절
    ):
        pass

    return linked


def _loadGrowthMap() -> dict[str, float]:
    """scan growth에서 전종목 매출 성장률 맵을 로드."""
    try:
        from dartlab.scan import Scan

        scan = Scan()
        result = scan("growth")
        if result is None or not hasattr(result, "df"):
            return {}

        df = result.df
        codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
        growthCol = None
        for col in ("revenueGrowth", "revenueCagr3y", "growth"):
            if col in df.columns:
                growthCol = col
                break
        if growthCol is None:
            return {}

        gmap = {}
        for row in df.iter_rows(named=True):
            code = str(row.get(codeCol, ""))
            g = row.get(growthCol)
            if code and g is not None:
                gmap[code] = float(g)
        return gmap
    except (ImportError, ValueError, AttributeError):
        return {}
    except Exception as exc:
        # scan 결과 schema 가 바뀌면 성장 신호가 통째로 빈 채 내려간다. 흐름은 그대로
        # 두되 원인은 남긴다. 그러지 않으면 신호 부재와 데이터 없음이 구분되지 않는다.
        log.warning("성장 맵 로드 실패로 빈 맵 반환: %s: %s", type(exc).__name__, exc)
        return {}


__all__ = ["calcAnnouncementTiming", "calcDisclosureDelta", "calcInventoryDivergence", "calcSupplyChainSignal"]
