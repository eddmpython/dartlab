"""industry(L2) calc 함수 - 회사·섹터 단위 산업 분석.

nodes.json + scan + macro 데이터를 조합하여 dict/숫자만 반환.
story(L3)가 블록으로 소비한다. 해석/서사는 하지 않는다.
"""

from __future__ import annotations

import math
from typing import Any

from dartlab.core.logger import getLogger
from dartlab.industry.calcs.sectorTables import sectorMetricTables

_log = getLogger(__name__)

# 업종 내 위치를 재는 축. (지표 이름, 분포 키, 백분위 키).
# 분포 키와 백분위 키는 바깥에서 쓰는 정본 이름이라 바꾸지 않는다.
_SECTOR_AXES: tuple[tuple[str, str, str], ...] = (
    ("opMargin", "opmDistribution", "myOpmPercentile"),
    ("revenueCagr", "cagrDistribution", "myCagrPercentile"),
    ("roe", "roeDistribution", "myRoePercentile"),
    # 재무 건전성 질문은 수익성 축으로 답할 수 없다. 실측(2026-08-06)에서 부채와 유동성을
    # 물은 질문이 업종 기준을 하나도 못 받고 끝났다. 그 구멍을 여기서 막는다.
    ("debtRatio", "debtRatioDistribution", "myDebtRatioPercentile"),
    ("currentRatio", "currentRatioDistribution", "myCurrentRatioPercentile"),
)


def calcChainPosition(company: Any) -> dict | None:
    """이 회사의 산업 가치사슬 위치 + 동일 공정 peers.

    Capabilities:
        종목코드 → industry/build 의 primary 노드 매핑을 조회하고, 동일 산업·공정 단계 안의
        다른 회사를 confidence 내림차순으로 묶어 반환. 어느 단계 (upstream/midstream/downstream)
        + 어느 역할 (제조/도매/소매/연구/서비스) 인지 단일 진입점으로 확인.

    Parameters
    ----------
    company : Any
        Company 객체. `stockCode` 속성 필수 (없으면 None).

    Returns
    -------
    dict | None
        industry : str - 산업 ID (taxonomy key)
        industryName : str - 산업명 (한글)
        stage : str - 공정 단계 key (예: "fabrication")
        stageName : str - 공정명 (한글)
        role : str - 역할 ("제조" | "도매" | "소매" | "연구" | "서비스")
        stream : str - 가치사슬 위치 ("upstream" | "midstream" | "downstream")
        confidence : float - 매핑 신뢰도 (0~1)
        source : str - 매핑 소스 (예: "manual", "auto")
        peers : list[dict] - 같은 공정의 다른 회사 최대 10 개 (confidence 내림차순)
        primary 노드 없거나 stage 미지정 시 None.

    Raises
    ------
    없음 (조회 실패 시 None 반환).

    Example
    -------
    >>> from dartlab import Company
    >>> c = Company("005930")
    >>> c.industry("chainPosition")
    {'industry': 'semiconductors', 'stage': 'fabrication', 'role': '제조', ...}

    Guide
    -----
    industry/build 의 노드 데이터에 primary=True 로 등록된 회사만 조회된다.
    매핑 보강은 운영자가 industry/build/data 의 JSON 을 직접 갱신 후 pipeline 재실행.

    SeeAlso
    -------
    - ``dartlab.industry.taxonomy.getIndustry`` : 산업 정의 조회
    - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 섹터 단위 지표

    Requires
    --------
    - L1.5 frame: industry/build/pipeline.loadNodes() 결과
    - L0 taxonomy: industry.taxonomy 등록된 산업

    AIContext
    ---------
    회사의 산업 위치를 한 줄로 답변할 때 가장 먼저 호출. peers 목록은 비교 대상 회사 선정에 사용.

    When:
        "이 회사 가치사슬 위치", "동일 공정 경쟁사" 류 1 차 답변. ``Company.industry()`` 진입점이
        본 함수를 호출.

    How:
        loadNodes → primary 노드 매칭 → taxonomy stage 메타 조회 → 동일 industry+stage peers 정렬.

    See Also:
        - ``dartlab.industry.taxonomy.getIndustry`` : 산업 정의 조회
        - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 섹터 단위 지표
    """
    from dartlab.industry.build.pipeline import loadNodes
    from dartlab.industry.taxonomy import getIndustry

    stockCode = getattr(company, "stockCode", "")
    if not stockCode:
        return None

    nodes = loadNodes()

    # 해당 종목의 primary 노드 찾기
    myNode = None
    for n in nodes:
        if n.stockCode == stockCode and n.primary:
            myNode = n
            break

    if myNode is None or not myNode.stage:
        return None

    ind = getIndustry(myNode.industry)
    if ind is None:
        return None

    stageInfo = ind.stageByKey(myNode.stage)

    # 같은 공정 peer
    peers = [
        {"stockCode": n.stockCode, "corpName": n.corpName, "confidence": n.confidence}
        for n in nodes
        if n.industry == myNode.industry and n.stage == myNode.stage and n.stockCode != stockCode
    ]
    peers.sort(key=lambda p: p["confidence"], reverse=True)

    return {
        "industry": myNode.industry,
        "industryName": ind.name,
        "stage": myNode.stage,
        "stageName": stageInfo.name if stageInfo else myNode.stage,
        "role": myNode.role,
        "stream": myNode.stream,
        "confidence": myNode.confidence,
        "source": myNode.source,
        "updatedAt": myNode.updatedAt,
        "mappingUpdatedAt": myNode.updatedAt,
        "financialPeriod": myNode.revenuePeriod,
        "peers": peers[:10],
    }


# ── 섹터 분석 calc (L2) ──


def _distribution(values: list[float]) -> dict | None:
    """숫자 리스트 → 분포 통계 (p10/p25/median/p75/p90/mean/std/n).

    Parameters
    ----------
    values : list[float]
        None 제외된 유효 숫자 리스트.

    Returns
    -------
    dict | None
        n : int - 표본 수
        p10/p25/median/p75/p90 : float - 백분위 (%)
        mean : float - 평균
        std : float - 표준편차
        표본 < 3 이면 None.
    """
    cleaned = sorted(v for v in values if v is not None)
    n = len(cleaned)
    if n < 3:
        return None

    def _q(q: float) -> float:
        pos = q * (n - 1)
        lo = int(pos)
        hi = min(lo + 1, n - 1)
        frac = pos - lo
        return cleaned[lo] * (1 - frac) + cleaned[hi] * frac

    mean = sum(cleaned) / n
    variance = sum((v - mean) ** 2 for v in cleaned) / n
    return {
        "n": n,
        "p10": round(_q(0.10), 2),
        "p25": round(_q(0.25), 2),
        "median": round(_q(0.50), 2),
        "p75": round(_q(0.75), 2),
        "p90": round(_q(0.90), 2),
        "mean": round(mean, 2),
        "std": round(variance**0.5, 2),
    }


def _percentile(value: float, dist: dict) -> float | None:
    """값의 분포 내 백분위 계산 (선형 보간).

    Parameters
    ----------
    value : float
        대상 값.
    dist : dict
        _distribution() 반환값.

    Returns
    -------
    float | None
        0~100 사이 백분위. dist 없으면 None.
    """
    if not dist or not math.isfinite(value):
        return None
    quantiles = [
        (10, dist["p10"]),
        (25, dist["p25"]),
        (50, dist["median"]),
        (75, dist["p75"]),
        (90, dist["p90"]),
    ]
    if value <= quantiles[0][1]:
        lowerSpan = max(abs(dist["p25"] - dist["p10"]), 1e-12)
        percentile = 10 - 15 * (dist["p10"] - value) / lowerSpan
        return min(10.0, max(0.0, percentile))
    if value >= quantiles[-1][1]:
        upperSpan = max(abs(dist["p90"] - dist["p75"]), 1e-12)
        percentile = 90 + 15 * (value - dist["p90"]) / upperSpan
        return min(100.0, max(90.0, percentile))
    for i in range(len(quantiles) - 1):
        a_q, a_v = quantiles[i]
        b_q, b_v = quantiles[i + 1]
        if a_v <= value <= b_v:
            span = b_v - a_v or 1
            percentile = a_q + (value - a_v) / span * (b_q - a_q)
            return min(100.0, max(0.0, percentile))
    return None


def calcSectorMetrics(company: Any) -> dict | None:
    """동종 산업 분포 + 백분위 - 수익성 3 축 + 건전성 2 축 (한국 시장).

    Capabilities:
        scan 횡단면 데이터에서 동일 industry 의 모든 primary 회사를 모아 OPM/매출 CAGR/ROE/
        부채비율/유동비율 분포 (p10/p25/median/p75/p90/mean/std) 를 산출하고, 대상 회사의
        분포 내 백분위를 반환. "업종 내 어느 위치냐" 질문의 단일 진입점.

    Parameters
    ----------
    company : Any
        Company 객체. stockCode + industry 매핑 필요.

    Returns
    -------
    dict | None
        industryId : str - 산업 ID
        industryName : str - 산업명
        peerCount : int - 동종사 수
        opmDistribution : dict - {n, p10, p25, median, p75, p90, mean, std} (%)
        cagrDistribution : dict - 동일 구조 (%, YoY 매출 CAGR)
        roeDistribution : dict - 동일 구조 (%)
        debtRatioDistribution : dict - 동일 구조 (%, 총부채/자본)
        currentRatioDistribution : dict - 동일 구조 (%, 유동자산/유동부채)
        myOpmPercentile : float | None - 대상 회사 OPM 백분위 (%)
        myCagrPercentile : float | None - CAGR 백분위 (%)
        myRoePercentile : float | None - ROE 백분위 (%)
        myDebtRatioPercentile : float | None - 부채비율 백분위 (%, 낮을수록 안전)
        myCurrentRatioPercentile : float | None - 유동비율 백분위 (%)
        scan 데이터 부재 회사는 분포 제외. 동종 3 사 미만이면 None.

    Raises
    ------
    없음 (데이터 미흡 시 None 반환).

    Example
    -------
    >>> c = Company("005930")
    >>> m = c.industry("sectorMetrics")
    >>> m["opmDistribution"]["median"]
    2.5
    >>> m["myOpmPercentile"]
    85.3

    Guide
    -----
    L1.5 scan SSOT 호출만으로 동종 분포가 계산되도록 설계. 분포 정의는 scan.profitability /
    scan.growth 컬럼 schema 와 직결되며, 새 지표 추가는 scan 측에 반영 후 본 함수 확장.

    SeeAlso
    -------
    - ``dartlab.scan.profitability`` : 횡단면 OPM/ROE 산출
    - ``dartlab.scan.growth`` : 횡단면 매출 CAGR 산출
    - ``dartlab.industry.calcs.companyCalcs.calcSectorCycle`` : 업종 사이클 위치

    Requires
    --------
    - L1.5 scan: profitability/growth 횡단면 결과
    - L1.5 frame: industry/build/pipeline.loadNodes() primary 매핑
    - 동종 회사 ≥ 3 (백분위 신뢰성 확보)

    AIContext
    ---------
    "이 회사 OPM 이 업종 내 어디" 질문에 대한 1 차 답변 데이터. peerCount 가 작으면 분포
    해석에 보수적으로 답변. 백분위 None 은 본 회사 데이터 미흡 (분포에는 정상 회사 포함).

    When:
        업종 내 상대 위치 답변. ``Company.industry()`` 진입점이 본 함수를 sectorMetrics 키로 호출.

    How:
        loadNodes → industry 매칭 peers → scan.profitability/scan.growth 횡단면 호출 → 분포
        (p10~p90/mean/std) 계산 → 대상 회사 백분위.

    See Also:
        - ``dartlab.scan.profitability`` : 횡단면 OPM/ROE 산출
        - ``dartlab.scan.growth`` : 횡단면 매출 CAGR 산출
        - ``dartlab.industry.calcs.companyCalcs.calcSectorCycle`` : 업종 사이클 위치
    """
    from dartlab.industry.build.pipeline import loadNodes
    from dartlab.industry.taxonomy import getIndustry

    stockCode = getattr(company, "stockCode", "")
    if not stockCode:
        return None

    nodes = loadNodes()
    myNode = next((n for n in nodes if n.stockCode == stockCode and n.primary), None)
    if not myNode:
        return None

    ind = getIndustry(myNode.industry)
    if not ind:
        return None

    try:
        tables = sectorMetricTables()
    except Exception as exc:
        _log.warning("섹터 지표 산출 실패로 None 반환: %s: %s", type(exc).__name__, exc)
        return None

    peerCodes = [n.stockCode for n in nodes if n.industry == myNode.industry and n.primary]
    out: dict = {
        "industryId": myNode.industry,
        "industryName": ind.name,
        "peerCount": len(peerCodes),
    }
    found = False
    for metric, distributionKey, percentileKey in _SECTOR_AXES:
        values = tables.get(metric) or {}
        distribution = _distribution([values[c] for c in peerCodes if c in values])
        mine = values.get(stockCode)
        out[distributionKey] = distribution
        out[percentileKey] = _percentile(mine, distribution) if mine is not None and distribution else None
        found = found or bool(distribution)
    return out if found else None


def calcSectorCycle(company: Any, *, sectorMetrics: dict | None = None) -> dict | None:
    """산업 사이클 판정 - 동종 OPM 중앙값 기반 확장/수축/안정.

    Capabilities:
        scan.profitability 의 동종 업종 OPM 중앙값을 기준으로 사이클 phase 와 방향을 판정.
        단일 연도 데이터에서는 절대값 구간 (>10/>0/≤0) 기반 (확장/안정/수축), 시계열 확장
        시 기울기 기반 (회복/정점 포함) 으로 자연 확장 가능한 구조.

    Parameters
    ----------
    company : Any
        Company 객체. stockCode + industry 매핑 필요.

    Returns
    -------
    dict | None
        industryId : str - 산업 ID
        industryName : str - 산업명
        phase : str - "확장" | "수축" | "안정" (시계열 확장 시 "회복" | "정점" 추가)
        direction : str - "개선" | "악화" | "횡보"
        opmTrend : list[dict] - [{year, median}] (시계열 확장 시)
        confidence : float - 판정 신뢰도 (0~1)
        동종 3 사 미만이면 None.

    Raises
    ------
    없음 (scan 호출 실패 시 None).

    Example
    -------
    >>> c = Company("009540")
    >>> cy = c.industry("sectorCycle")
    >>> cy["phase"], cy["direction"]
    ('확장', '개선')

    Guide
    -----
    현재는 횡단면 (단일 연도) 데이터만 사용. scan finance.parquet 의 연도별 history 채워지면
    3 년 기울기 기반 (회복/정점) 자동 활성화. 임계값 (10/0) 조정은 도메인 워크숍 결과 반영.

    SeeAlso
    -------
    - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 동종 분포 + 백분위
    - ``dartlab.macro.cycles.cycle.analyzeCycle`` : 거시 사이클 (대비)

    Requires
    --------
    - L1.5 scan.financial.profitability 호출 가능
    - 동종 회사 ≥ 3 (중앙값 신뢰성)

    AIContext
    ---------
    "이 회사 업종은 지금 어디" 질문에 대한 1 차 답변. macro cycle 과 결합하면 거시 환경 ×
    업종 사이클 × 회사 위치 3 축 분석.

    When:
        업종 단위 OPM 분위 판정이 필요할 때. ``Company.industry()`` 의 sectorCycle 키로 진입.

    How:
        loadNodes → industry peers → scan.profitability 현재 OPM → 중앙값 → 임계값 (10/0/<0)
        매핑 → phase/direction 결정.

    See Also:
        - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 동종 분포 + 백분위
        - ``dartlab.macro.cycles.cycle.analyzeCycle`` : 거시 사이클 (대비)
    """
    from dartlab.industry.build.pipeline import loadNodes
    from dartlab.industry.taxonomy import getIndustry

    stockCode = getattr(company, "stockCode", "")
    if not stockCode:
        return None

    nodes = loadNodes()
    myNode = next((n for n in nodes if n.stockCode == stockCode and n.primary), None)
    if not myNode:
        return None

    ind = getIndustry(myNode.industry)
    if not ind:
        return None

    metricsDist = sectorMetrics.get("opmDistribution") if isinstance(sectorMetrics, dict) else None
    medianFromMetrics = metricsDist.get("median") if isinstance(metricsDist, dict) else None
    if isinstance(medianFromMetrics, (int, float)) and not isinstance(medianFromMetrics, bool):
        median_opm = float(medianFromMetrics)
    else:
        # 연도별 업종 OPM 중앙값 - scan finance.parquet 직접 접근
        try:
            import importlib

            scanProfitability = importlib.import_module("dartlab.scan.financial.profitability").scanProfitability
            prof = scanProfitability()
        except Exception as exc:
            _log.warning("섹터 사이클 산출 실패로 None 반환: %s: %s", type(exc).__name__, exc)
            return None

        if prof.is_empty():
            return None

        profMap = {r["stockCode"]: r for r in prof.iter_rows(named=True)}
        peerCodes = {n.stockCode for n in nodes if n.industry == myNode.industry and n.primary}

        # 현재 scan 은 단일 연도만 - 시계열 미지원 시 단순 판정
        currentOpms = [
            profMap[c]["opMargin"] for c in peerCodes if c in profMap and profMap[c].get("opMargin") is not None
        ]
        if len(currentOpms) < 3:
            return None

        median_opm = sorted(currentOpms)[len(currentOpms) // 2]

    # 단순 판정 (시계열 데이터 없을 때 현재값 기반)
    if median_opm > 10:
        phase, direction = "확장", "개선"
    elif median_opm > 0:
        phase, direction = "안정", "횡보"
    else:
        phase, direction = "수축", "악화"

    return {
        "industryId": myNode.industry,
        "industryName": ind.name,
        "phase": phase,
        "direction": direction,
        "opmTrend": [{"year": "current", "median": round(median_opm, 2)}],
        "confidence": 0.5,  # 단일 시점 → 낮은 신뢰도
    }


def calcSectorDynamics(company: Any, *, macroPhase: str | None = None) -> dict | None:
    """매크로 국면 × 업종 경기민감도 → 순풍/역풍 + 1 줄 요약.

    Capabilities:
        업종을 high/moderate/defensive 경기민감도로 분류하고, 외부 주입된 macroPhase
        (회복/확장/둔화/침체) 와 교차하여 현재 환경의 tailwind/headwind 리스트와 1 줄 summary
        를 산출. L2↔L2 의존 회피 위해 macroPhase 는 외부 인자.

    Parameters
    ----------
    company : Any
        Company 객체. stockCode + industry 매핑 필요.
    macroPhase : str | None, default None
        매크로 사이클 국면 ("회복" | "확장" | "둔화" | "침체"). None 이면 "미확인" 으로
        fallback (tailwind/headwind 빈 리스트).

    Returns
    -------
    dict | None
        industryId : str - 산업 ID
        industryName : str - 산업명
        tailwind : list[str] - 순풍 요인 (예: ["경기 회복기", "수출 호조"])
        headwind : list[str] - 역풍 요인 (예: ["금리 상승", "원자재 비용"])
        macroPhase : str - 입력 그대로 (또는 "미확인")
        cycleSensitivity : str - "high" | "moderate" | "defensive"
        summary : str - "{업종}: {요인1} · {요인2} → 순풍/역풍"
        매핑 실패 시 None.

    Raises
    ------
    없음 (조회 실패 시 None).

    Example
    -------
    >>> c = Company("005930")
    >>> d = c.industry("sectorDynamics", macroPhase="회복")
    >>> d["summary"]
    '반도체: 경기 회복기 · 수출 호조 → 순풍'

    Guide
    -----
    호출자가 매크로 phase 를 먼저 결정 (예: `c.macro("phase")`) 한 뒤 본 함수에 주입.
    L2↔L2 cross 가드 회피용 패턴. 경기민감도 표준 분류는 본 모듈 내 상수 (HIGH/MODERATE/DEFENSIVE).

    SeeAlso
    -------
    - ``dartlab.macro.cycles.cycle.analyzeCycle`` : macroPhase 산출
    - ``dartlab.industry.calcs.companyCalcs.calcSectorCycle`` : 업종 자체 사이클

    Requires
    --------
    - L1.5 frame: industry 매핑
    - macroPhase 인자 (호출자가 macro 결과를 외부 주입)

    AIContext
    ---------
    회사 환경 진단 1 줄 답변에 적합. macroPhase 명시 안 하면 답변 보수적으로 ("환경 미확인"
    명시). tailwind/headwind 리스트는 비교 답변에도 그대로 인용 가능.

    When:
        매크로 × 업종 교차 진단이 필요할 때. ``Company.industry()`` 의 sectorDynamics 키로 진입.

    How:
        loadNodes → industry 매칭 → 정적 sensitivity 집합 매핑 (HIGH/DEFENSIVE/MODERATE) →
        macroPhase 와 cross-join → tailwind/headwind 리스트 → summary 문장.

    See Also:
        - ``dartlab.macro.cycles.cycle.analyzeCycle`` : macroPhase 산출
        - ``dartlab.industry.calcs.companyCalcs.calcSectorCycle`` : 업종 자체 사이클
    """
    from dartlab.industry.build.pipeline import loadNodes
    from dartlab.industry.taxonomy import getIndustry

    stockCode = getattr(company, "stockCode", "")
    if not stockCode:
        return None

    nodes = loadNodes()
    myNode = next((n for n in nodes if n.stockCode == stockCode and n.primary), None)
    if not myNode:
        return None

    ind = getIndustry(myNode.industry)
    if not ind:
        return None

    industryId = myNode.industry
    industryName = ind.name

    # 경기민감도 분류 (taxonomy 기반 규칙)
    HIGH_SENSITIVITY = {
        "semiconductor",
        "auto",
        "construction",
        "steel",
        "chemical",
        "shipbuilding",
        "machinery",
        "battery",
    }
    DEFENSIVE = {"pharma", "food", "education", "environment"}
    if industryId in HIGH_SENSITIVITY:
        sensitivity = "high"
    elif industryId in DEFENSIVE:
        sensitivity = "defensive"
    else:
        sensitivity = "moderate"

    # 매크로 국면 - 외부 주입 (None 이면 "미확인" fallback)
    phase = macroPhase if macroPhase else "미확인"

    # 순풍/역풍 규칙 기반 판정
    tailwind: list[str] = []
    headwind: list[str] = []

    if phase in ("회복", "확장"):
        if sensitivity == "high":
            tailwind.append("경기 회복기 - 경기민감 업종 수혜")
        elif sensitivity == "moderate":
            tailwind.append("경기 확장기 - 완만한 수혜")
        # defensive 는 경기와 무관
    elif phase in ("둔화", "침체"):
        if sensitivity == "high":
            headwind.append("경기 둔화 - 경기민감 업종 직격")
        elif sensitivity == "defensive":
            tailwind.append("경기 방어주 - 상대적 안정")

    # 요약 문장
    wind = "순풍" if len(tailwind) > len(headwind) else "역풍" if len(headwind) > len(tailwind) else "중립"
    summary = f"{industryName}: {phase} · {wind}"

    return {
        "industryId": industryId,
        "industryName": industryName,
        "tailwind": tailwind,
        "headwind": headwind,
        "macroPhase": phase,
        "cycleSensitivity": sensitivity,
        "summary": summary,
    }


def companyIndustryResult(company: Any, *, detail: bool = False) -> dict[str, Any]:
    """Company facade가 허용된 industry calc 경계로 대표 제품을 호출한다."""
    from dartlab.industry.product import companyIndustryResult as _companyIndustryResult

    return _companyIndustryResult(company, detail=detail)
