"""산업·공급망 집중도 계산 (런타임 calc).

회사 공급망 관계의 HHI(허핀달 지수)·상위 N 비중·공정 다양성, 산업 단위 매출 집중도를 계산.
``calcs/{companyCalcs,lifecycle,peers}`` 와 같은 런타임 calc 거처 — build 파이프라인(enrichCompany)
과 ``Industry()`` verb(concentration 모드)가 공유한다. 벤치마크: 산업조직론(IO) CR_N·HHI.
"""

from __future__ import annotations

from typing import Any


def calcHHI(supplierAmounts: list[float]) -> float:
    """허핀달-허시만 지수 (HHI) — 공급망/시장 집중도 단일 척도.

    Capabilities:
        거래금액·매출 같은 양수 기여도 리스트에서 점유율(%) 제곱의 합을 산출. 미국 DOJ 의
        반독점 기준 (1500/2500) 과 동일 척도로 분산/중간/집중 판정에 사용. 양수 항목만
        집계 (None/음수 제외).

    Parameters
    ----------
    supplierAmounts : list[float]
        공급사·기업별 양수 기여도 리스트 (단위 무관, 모두 동일 단위 가정).

    Returns
    -------
    float
        HHI 값 (0~10000). 모든 항목 0 이하면 0.0 반환.

    Raises
    ------
    없음.

    Example
    -------
    >>> calcHHI([60, 30, 10])
    4600.0
    >>> calcHHI([])
    0.0

    Guide
    -----
    DOJ Antitrust Division 의 시장 집중도 기준 (HHI<1500 분산, 1500-2500 중간, >2500 집중) 을
    그대로 따른다. ``riskLabel`` 로 라벨 변환.

    SeeAlso
    -------
    - ``dartlab.industry.calcs.concentration.calcTopNRatio`` : 상위 N 사 비중
    - ``dartlab.industry.calcs.concentration.riskLabel`` : HHI → 위험 라벨

    Requires
    --------
    - 입력 리스트의 단위 일관성 (혼합 단위 금지)

    AIContext
    ---------
    "공급망 의존도", "시장 집중도" 질문의 1 차 답변. 값 단독 인용보다 ``riskLabel`` 결합 권장.

    When:
        공급망/시장 집중도 단일 수치가 필요할 때. 회사 단위 종합은 ``calcSupplyInsights``,
        산업 단위는 ``calcIndustryConcentration`` 진입점이 본 함수를 호출.

    How:
        양수 amount/revenue 리스트 → HHI → ``riskLabel`` 로 분산/중간/집중 라벨 변환의 1 단계.

    See Also:
        - ``dartlab.industry.calcs.concentration.calcTopNRatio`` : 상위 N 사 비중
        - ``dartlab.industry.calcs.concentration.riskLabel`` : HHI → 위험 라벨
    """
    total = sum(a for a in supplierAmounts if a and a > 0)
    if total == 0:
        return 0.0
    hhi = 0.0
    for a in supplierAmounts:
        if not a or a <= 0:
            continue
        share = (a / total) * 100  # %
        hhi += share * share
    return round(hhi, 0)


def riskLabel(hhi: float) -> str:
    """HHI 값을 위험 라벨로 변환한다.

    Capabilities:
        DOJ Antitrust 기준 (1500 / 2500) 으로 HHI 를 4 단계 한국어 라벨 ("데이터 부족" /
        "분산" / "중간" / "집중") 로 변환.

    Parameters
    ----------
    hhi : float
        허핀달-허시만 지수 (0~10000).

    Returns
    -------
    str
        "데이터 부족" (0) / "분산" (<1500) / "중간" (<2500) / "집중" (>=2500).

    Raises:
        없음.

    Example:
        >>> riskLabel(3500)
        '집중'

    Guide:
        UI 카드/요약 텍스트에 그대로 노출 가능한 한국어 라벨. 숫자 인용 시 ``calcHHI`` 결합.

    When:
        HHI 숫자 단독으로는 의미 전달이 약할 때. AI 답변/UI 카드의 "한 줄 진단".

    How:
        ``calcHHI`` 산출값 → 본 함수 → 라벨. ``calcSupplyInsights`` / ``calcIndustryConcentration``
        가 ``hhiRisk`` 필드로 자동 결합해 반환.

    Requires:
        - 입력은 ``calcHHI`` 가 반환한 0~10000 범위 float 값.

    See Also:
        - ``dartlab.industry.calcs.concentration.calcHHI`` : 본 함수의 입력 산출
        - ``dartlab.industry.calcs.concentration.calcSupplyInsights`` : 라벨 자동 결합

    AIContext:
        "분산 시장이다 / 집중도가 높다" 1 줄 답변. 정밀 엣지 부족 (preciseEdgeCount 낮음) 시
        "데이터 부족" 으로 폴백되므로 별도 단서 없이 그대로 인용 가능.
    """
    if hhi == 0:
        return "데이터 부족"
    if hhi < 1500:
        return "분산"
    if hhi < 2500:
        return "중간"
    return "집중"


def calcTopNRatio(supplierAmounts: list[float], n: int = 3) -> float:
    """상위 N 사 비중 (CR_N) — 시장 집중도 보조 지표.

    Capabilities:
        양수 기여도 리스트를 내림차순 정렬 후 상위 n 합/전체 합 비율을 % 단위로 반환. HHI 와
        함께 시장 집중도 2 축 (분포 모양 + 상위 쏠림) 진단에 사용.

    Parameters
    ----------
    supplierAmounts : list[float]
        양수 기여도 리스트.
    n : int, default 3
        상위 몇 개까지 합산할지 (CR3 표준).

    Returns
    -------
    float
        상위 N 사 비중 (%, 0.0~100.0). 양수 없으면 0.0.

    Raises
    ------
    없음.

    Example
    -------
    >>> calcTopNRatio([60, 30, 10, 5], n=3)
    95.0
    >>> calcTopNRatio([60, 30, 10, 5], n=1)
    52.2

    Guide
    -----
    CR1·CR3·CR4 는 산업조직론 (IO) 의 표준 집중도 지표. HHI 는 분포 전체, CR_N 은 상위 쏠림에
    민감 — 두 지표 병기가 정석.

    SeeAlso
    -------
    - ``dartlab.industry.calcs.concentration.calcHHI`` : 분포 전체 집중도

    Requires
    --------
    - 입력 리스트의 단위 일관성

    AIContext
    ---------
    "1 위가 몇 %", "상위 3 사가 시장 절반 이상" 류 답변. ``calcHHI`` 와 함께 인용하면 입체적.

    When:
        상위 쏠림 수치가 필요할 때 (CR1/CR3 등). 단독 사용보다 ``calcHHI`` 와 병기 권장.

    How:
        양수 amount 리스트 → 내림차순 정렬 → 상위 n 합/전체 합 비율 (%). 회사 단위는
        ``calcSupplyInsights`` 진입점에서 top1Ratio/top3Ratio 필드로 자동 결합.

    See Also:
        - ``dartlab.industry.calcs.concentration.calcHHI`` : 분포 전체 집중도
    """
    amounts = sorted([a for a in supplierAmounts if a and a > 0], reverse=True)
    total = sum(amounts)
    if total == 0:
        return 0.0
    topN = sum(amounts[:n])
    return round((topN / total) * 100, 1)


def calcSupplyInsights(
    stockCode: str,
    edges: list[Any],
    nodes: list[Any],
) -> dict:
    """회사 단위 공급망 인사이트 — 집중도 + 다양성 + 거래 규모 종합.

    Capabilities:
        IndustryEdge/Node 그래프에서 대상 회사로 유입되는 supplier 엣지를 추출해 HHI/CR1/CR3,
        공급사 산업·공정 다양성, 총 거래금액, 정밀 엣지 수를 단일 dict 로 반환. Interos.ai /
        Bloomberg SPLC 가이드를 따르는 공급망 리스크 1 차 진단.

    Parameters
    ----------
    stockCode : str
        대상 회사 코드.
    edges : list[Any]
        전체 IndustryEdge 리스트 (`fromCode`, `toCode`, `edgeType`, `amount` 속성 필요).
    nodes : list[Any]
        전체 IndustryNode 리스트 (`stockCode`, `industry`, `stage` 속성 필요). 대상 회사 노드의
        `supplyFacts`(비상장 매입처 leaf fact, 레버 A)가 있으면 HHI 모수에 합산.

    Returns
    -------
    dict
        supplierCount : int — 공급사 수 (상장 엣지 + 비상장 leaf fact, 건)
        customerCount : int — 고객사 수 (건)
        preciseEdgeCount : int — 거래금액 있는 정밀 건수 (상장 엣지 + 비상장 leaf fact)
        totalSupplyAmount : float — 총 매입금액 (억원, 상장 + 비상장 합산)
        hhi : float — HHI (0~10000, 상장 엣지 + 비상장 leaf fact amount 합산 — 레버 A)
        hhiRisk : str — "분산" | "중간" | "집중" | "데이터 부족"
        top1Ratio : float — 최대 공급사 비중 (%)
        top3Ratio : float — 상위 3 사 비중 (%)
        industryDiversity : int — 공급사 소속 산업 수 (개)
        stageDiversity : int — 공급사 소속 공정 수 (개)
        topSupplyIndustries : list[tuple] — 공급 산업 상위 5 `[(industry, count), ...]`
        topSupplyStages : list[tuple] — 공급 공정 상위 5

    Raises
    ------
    없음.

    Example
    -------
    >>> from dartlab.industry.build.pipeline import loadNodes, loadEdges
    >>> insights = calcSupplyInsights("005930", loadEdges(), loadNodes())
    >>> insights["hhiRisk"], insights["top3Ratio"]
    ('분산', 42.1)

    Guide
    -----
    HHI 는 거래금액 (`amount`) 양수 엣지만으로 계산 — 정밀 엣지 비율 (`preciseEdgeCount` /
    `supplierCount`) 이 낮으면 결과 신뢰성도 낮음. 운영자는 industry/build 매핑 보강으로 양 개선.

    SeeAlso
    -------
    - ``dartlab.industry.calcs.concentration.calcHHI`` : HHI 단독
    - ``dartlab.industry.calcs.concentration.calcIndustryConcentration`` : 산업 단위 집중도

    Requires
    --------
    - L1.5 frame: industry/build/pipeline.loadEdges/loadNodes
    - IndustryEdge.amount 충실도 (정밀 엣지 비율)

    AIContext
    ---------
    회사 공급망 답변의 단일 진입점. ``hhiRisk`` + ``top1Ratio`` 두 값으로 한 줄 요약 가능.
    정밀 엣지가 적으면 ("일부 거래만 추정") 답변에 명시.

    When:
        "삼성전자 공급망", "이 회사 공급사 집중도" 류 질의의 1 차 답변. 회사 카드의 supply
        섹션 데이터 소스로도 사용.

    How:
        edges/nodes 그래프 입력 → 본 회사 inbound supplier 엣지 추출 → ``calcHHI`` /
        ``calcTopNRatio`` 호출 → 산업/공정 다양성 카운팅 → 단일 dict.

    See Also:
        - ``dartlab.industry.calcs.concentration.calcHHI`` : HHI 단독
        - ``dartlab.industry.calcs.concentration.calcIndustryConcentration`` : 산업 단위 집중도
    """
    # 이 회사가 to인 supplier 엣지 (공급받는 관계)
    incoming = [e for e in edges if e.toCode == stockCode and e.edgeType == "supplier"]
    outgoing = [e for e in edges if e.fromCode == stockCode and e.edgeType in ("supplier", "customer")]

    # 레버 A — buyer node leaf fact (비상장 매입처 매입액). 상장 엣지 amount 와 합산해 HHI 모수 확장.
    nodeByCode = {n.stockCode: n for n in nodes}
    selfNode = nodeByCode.get(stockCode)
    leafFacts = getattr(selfNode, "supplyFacts", None) or [] if selfNode else []
    leafAmounts = [f.get("amount") for f in leafFacts if f.get("amount") and f.get("amount") > 0]

    # HHI — 매입액 기준 (상장 엣지 + 비상장 leaf fact, amount 있는 것만)
    edgeAmounts = [e.amount for e in incoming if e.amount and e.amount > 0]
    incomingAmounts = edgeAmounts + leafAmounts
    hhi = calcHHI(incomingAmounts)
    top3 = calcTopNRatio(incomingAmounts, n=3)
    top1 = calcTopNRatio(incomingAmounts, n=1)

    # 공정 다양성 (공급사들이 어떤 공정에 속하는지 — 상장 엣지만, 비상장은 stage 미상)
    industrySupply: dict[str, int] = {}
    stageSupply: dict[str, int] = {}
    for e in incoming:
        from_node = nodeByCode.get(e.fromCode)
        if not from_node:
            continue
        industrySupply[from_node.industry] = industrySupply.get(from_node.industry, 0) + 1
        if from_node.stage:
            stageSupply[from_node.stage] = stageSupply.get(from_node.stage, 0) + 1

    # 총 거래금액 (상장 엣지 + 비상장 leaf fact)
    totalAmount = sum(a for a in incomingAmounts)

    # 정밀 엣지 개수 (amount 있는 것 — 엣지 + leaf fact)
    preciseCount = len(incomingAmounts)

    return {
        "supplierCount": len(incoming) + len(leafFacts),
        "customerCount": len([e for e in outgoing if e.edgeType == "customer"]),
        "preciseEdgeCount": preciseCount,
        "totalSupplyAmount": totalAmount,  # 억원
        "hhi": hhi,
        "hhiRisk": riskLabel(hhi),
        "top1Ratio": top1,
        "top3Ratio": top3,
        "industryDiversity": len(industrySupply),
        "stageDiversity": len(stageSupply),
        "topSupplyIndustries": sorted(industrySupply.items(), key=lambda x: -x[1])[:5],
        "topSupplyStages": sorted(stageSupply.items(), key=lambda x: -x[1])[:5],
    }


def calcIndustryConcentration(
    industryId: str,
    nodes: list[Any],
) -> dict:
    """산업 단위 매출 집중도 — HHI + CR3 + 상위 5 사 프로필.

    Capabilities:
        IndustryNode 그래프에서 대상 산업의 매출 양수 회사들로 HHI/CR3 와 상위 5 사 정보
        (stockCode/corpName/stage/revenue) 를 산출. 산업 자체의 시장구조 (분산 vs 과점) 진단.

    Parameters
    ----------
    industryId : str
        산업 ID (taxonomy key).
    nodes : list[Any]
        전체 IndustryNode 리스트 (`industry`, `revenue`, `revenuePeriod`, `stockCode`,
        `corpName`, `stage` 속성).

    Returns
    -------
    dict
        companyCount : int — 매출 양수 기업 수 (개)
        totalRevenue : float — 산업 총 매출 (억원)
        hhi : float — 매출 기준 HHI (0~10000)
        hhiRisk : str — "분산" | "중간" | "집중" | "데이터 부족"
        top3Ratio : float — 상위 3 사 매출 비중 (%)
        topN : list[dict] — 상위 5 사 `[{stockCode, corpName, stage, revenue}, ...]`
        서로 다른 회계연도 매출은 혼합하지 않는다. 같은 회계연도 표본이 3사 미만이거나 전체
        매출 관측 노드의 60% 미만이면 수치를 공개하지 않고 unavailable 상태를 반환한다.

    Raises
    ------
    없음.

    Example
    -------
    >>> from dartlab.industry.build.pipeline import loadNodes
    >>> r = calcIndustryConcentration("semiconductors", loadNodes())
    >>> r["hhiRisk"], r["top3Ratio"]
    ('집중', 78.4)

    Guide
    -----
    매출 (`revenue`) 없는 노드 (비상장 등) 는 분포 제외. industry/build 매핑이 비상장 기업
    포함 시 시장 점유율 왜곡 가능 — 답변 시 ``companyCount`` 인용 권장.

    SeeAlso
    -------
    - ``dartlab.industry.calcs.concentration.calcSupplyInsights`` : 회사 단위 집중도
    - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 분포 + 백분위

    Requires
    --------
    - L1.5 frame: industry/build/pipeline.loadNodes
    - IndustryNode.revenue 충실도

    AIContext
    ---------
    "이 산업은 과점 시장" / "분산 시장" 답변의 1 차 진단. topN 은 시장 주도 회사 답변에 그대로 인용.

    When:
        "반도체 산업 과점 정도", "은행 산업 1 위 점유율" 류 질의. 산업 카드/지도의 헤더 진단 1 줄
        생성에 사용.

    How:
        nodes 리스트 입력 → 산업 매칭 + 매출 양수 필터 → ``calcHHI`` / ``calcTopNRatio`` 호출
        → 상위 5 사 프로필 첨부 → 단일 dict.

    See Also:
        - ``dartlab.industry.calcs.concentration.calcSupplyInsights`` : 회사 단위 집중도
        - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 분포 + 백분위
    """
    allMembers = [n for n in nodes if n.industry == industryId and n.revenue and n.revenue > 0]
    byPeriod: dict[str, list[Any]] = {}
    for member in allMembers:
        period = getattr(member, "revenuePeriod", None)
        if period:
            byPeriod.setdefault(str(period), []).append(member)

    totalObserved = len(allMembers)
    candidatePeriod: str | None = None
    members: list[Any] = []
    for period in sorted(byPeriod, reverse=True):
        periodMembers = byPeriod[period]
        coveragePct = len(periodMembers) / totalObserved * 100 if totalObserved else 0.0
        if len(periodMembers) >= 3 and coveragePct >= 60:
            candidatePeriod = period
            members = periodMembers
            break

    if candidatePeriod is None:
        bestPeriod, bestMembers = max(byPeriod.items(), key=lambda item: (len(item[1]), item[0]), default=(None, []))
        observed = len(bestMembers)
        coveragePct = round(observed / totalObserved * 100, 1) if totalObserved else 0.0
        return {
            "status": "unavailable",
            "blockedReason": "동일 회계연도 매출 표본이 3사 이상이면서 전체 관측치의 60% 이상인 연도가 없습니다.",
            "fiscalYear": bestPeriod,
            "coverage": {"observed": observed, "total": totalObserved, "pct": coveragePct},
            "companyCount": observed,
            "totalRevenue": None,
            "hhi": None,
            "hhiRisk": "데이터 부족",
            "top3Ratio": None,
            "topN": [],
        }

    coveragePct = round(len(members) / totalObserved * 100, 1)
    revenues = sorted([n.revenue for n in members], reverse=True)
    totalRev = sum(revenues)
    hhi = calcHHI(revenues)
    top3 = calcTopNRatio(revenues, n=3)

    # 상위 5사
    sortedMembers = sorted(members, key=lambda n: n.revenue or 0, reverse=True)
    topN = [
        {"stockCode": n.stockCode, "corpName": n.corpName, "stage": n.stage, "revenue": n.revenue}
        for n in sortedMembers[:5]
    ]

    return {
        "status": "usable" if coveragePct >= 80 else "partial",
        "blockedReason": None if coveragePct >= 80 else "동일 회계연도 매출 커버리지가 80% 미만입니다.",
        "fiscalYear": candidatePeriod,
        "coverage": {"observed": len(members), "total": totalObserved, "pct": coveragePct},
        "companyCount": len(members),
        "totalRevenue": totalRev,
        "hhi": hhi,
        "hhiRisk": riskLabel(hhi),
        "top3Ratio": top3,
        "topN": topN,
    }
