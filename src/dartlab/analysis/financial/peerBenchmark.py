"""5-3 비교분석 -- 이 회사는 시장에서 어디에 서 있는가.

scan 데이터에서 해당 종목의 백분위/순위를 계산하여
기존 재무 지표에 시장 맥락을 더한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf

# 비교할 핵심 비율 목록 (scanRatio name → 표시 label)
# 기준 기간으로 채택할 최소 채움 비율 (가장 잘 찬 기간 대비). scan/io/calendar 의
# 연도 선택과 같은 문턱이다. 갓 시작한 분기는 이 선을 못 넘는다.
_PERIOD_COMPLETENESS = 0.8

_BENCHMARK_RATIOS = [
    ("roe", "ROE"),
    ("roa", "ROA"),
    ("operatingMargin", "영업이익률"),
    ("netMargin", "순이익률"),
    ("debtRatio", "부채비율"),
    ("currentRatio", "유동비율"),
    ("revenueGrowth", "매출성장률"),
    ("totalAssetTurnover", "총자산회전율"),
]


# ── 핵심 비율 백분위 ──


@memoizedCalc
def calcPeerRanking(company, *, basePeriod: str | None = None) -> dict | None:
    """핵심 재무비율 시장 내 백분위 순위.

    scan 데이터에서 최신 기간 기준 백분위(percentile)와
    순위(rank)를 계산한다. 결과는 company._cache에 저장하여 재활용.

    Capabilities:
        - 8 개 핵심 비율의 시장 내 percentile/rank 산출.

    Guide:
        company 단일 종목을 전 시장 횡단면과 대조.

    When:
        "이 회사는 시장에서 어디?" 묻는 비교 분석 시점.

    How:
        Company.fromCode → calcPeerRanking(c) → rankings 리스트 소비.

    Requires:
        scan parquet (전 종목 ratio) + company.stockCode.

    Raises:
        없음 (데이터 부재 시 None 반환).

    Example:
        >>> calcPeerRanking(c)
        {"rankings": [{"ratioName": "roe", "percentile": 72.5, ...}, ...]}

    See Also:
        - calcRiskReturnPosition : 수익/위험 사분면

    AIContext:
        AI 답변에서 "동종 대비 ROE 상위 X%" 인용에 사용.

    Returns
    -------
    dict
        rankings : list[dict] — 비율별 순위 정보
            ratioName : str — 비율 ID (roe, debtRatio 등)
            label : str — 표시명
            value : float — 해당 종목 값
            percentile : float — 시장 내 백분위 (%)
            rank : int — 순위 (1 = 최상위)
            total : int — 전체 종목 수
            period : str — 기준 기간
    """
    cache = getattr(company, "_cache", None)
    _KEY = "_peerRanking"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    stockCode = _getStockCode(company)
    if stockCode is None:
        return None

    rankings = []
    for ratioName, label in _BENCHMARK_RATIOS:
        result = _calcPercentile(stockCode, ratioName, label)
        if result is not None:
            rankings.append(result)

    out = {"rankings": rankings} if rankings else None
    if cache is not None:
        cache[_KEY] = out
    return out


# ── 수익성 vs 안정성 포지션 ──


@memoizedCalc
def calcRiskReturnPosition(company, *, basePeriod: str | None = None) -> dict | None:
    """수익-위험 매트릭스 포지션.

    ROE(수익) x 부채비율(위험)에서 시장 내 사분면 위치를 결정한다.
    calcPeerRanking 캐시가 있으면 재활용.

    Capabilities:
        - ROE x 부채비율 4 분면 라벨링 + 평가 코멘트.

    Guide:
        고수익-저위험 = 우량, 저수익-고위험 = 구조 개선 필요.

    When:
        "수익성과 안정성 동시 평가" 의도가 들어왔을 때.

    How:
        calcPeerRanking 캐시 재사용 → 사분면 판정.

    Requires:
        peerRanking 데이터 또는 scan parquet 직접 조회.

    Raises:
        없음 (데이터 부재 시 None).

    Example:
        >>> calcRiskReturnPosition(c)
        {"quadrant": "고수익-저위험", "assessment": "우량", ...}

    See Also:
        - calcPeerRanking : 백분위 산출 원본
        - calcPeerBenchmarkFlags : 사분면 기반 플래그

    AIContext:
        AI 가 회사 포지션 한 단어 평가 시 "우량/구조 개선 필요" 인용.

    Returns
    -------
    dict
        roe : float — ROE 값 (%)
        roePercentile : float — ROE 시장 백분위 (%)
        debtRatio : float — 부채비율 값 (%)
        debtRatioPercentile : float — 부채비율 시장 백분위 (%)
        quadrant : str — 사분면 ("고수익-저위험" | "고수익-고위험" | "저수익-저위험" | "저수익-고위험")
        assessment : str — 평가 ("우량" | "레버리지 의존" | "보수적" | "구조 개선 필요")
    """
    # ranking 캐시에서 roe/debtRatio 추출 시도
    ranking = calcPeerRanking(company)
    roeR = _findRanking(ranking, "roe") if ranking else None
    debtR = _findRanking(ranking, "debtRatio") if ranking else None

    if roeR and debtR:
        roeVal = roeR["value"]
        roePctile = roeR["percentile"]
        debtVal = debtR["value"]
        debtPctile = debtR["percentile"]
    else:
        # ranking 없으면 직접 조회
        stockCode = _getStockCode(company)
        if stockCode is None:
            return None
        roeData = _getLatestValue(stockCode, "roe")
        debtData = _getLatestValue(stockCode, "debtRatio")
        if roeData is None or debtData is None:
            return None
        roeVal, roePctile = roeData
        debtVal, debtPctile = debtData

    # 사분면 결정 (ROE 높/낮 x 부채 높/낮)
    highRoe = roePctile >= 50
    highDebt = debtPctile >= 50

    if highRoe and not highDebt:
        quadrant = "고수익-저위험"
        assessment = "우량"
    elif highRoe and highDebt:
        quadrant = "고수익-고위험"
        assessment = "레버리지 의존"
    elif not highRoe and not highDebt:
        quadrant = "저수익-저위험"
        assessment = "보수적"
    else:
        quadrant = "저수익-고위험"
        assessment = "구조 개선 필요"

    return {
        "roe": roeVal,
        "roePercentile": roePctile,
        "debtRatio": debtVal,
        "debtRatioPercentile": debtPctile,
        "quadrant": quadrant,
        "assessment": assessment,
    }


# ── 플래그 ──


@memoizedCalc
def calcPeerBenchmarkFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """비교분석 경고/기회 플래그.

    Capabilities:
        - 백분위 극단값에서 warning/opportunity 코멘트 산출.

    Guide:
        상위/하위 10% 임계로 시장 내 두드러진 항목만 노출.

    When:
        "이 회사의 시장 내 약점/강점 한 줄?" 요청 시.

    How:
        calcPeerRanking 결과 소비 → 임계 필터 → 사분면 보강.

    Requires:
        calcPeerRanking 가 None 아니어야 동작.

    Raises:
        없음 (랭킹 부재 시 빈 리스트).

    Example:
        >>> calcPeerBenchmarkFlags(c)
        [("ROE 상위 5% (22.3%)", "opportunity"), ...]

    See Also:
        - calcPeerRanking : flags 의 원천
        - calcRiskReturnPosition : 사분면 라벨

    AIContext:
        AI 가 "강점/약점 한 줄" 요약 카드 생성에 사용.

    Returns
    -------
    list[tuple[str, str]]
        (메시지, 유형) 튜플 목록. 유형은 "warning" | "opportunity".
    """
    flags: list[tuple[str, str]] = []

    ranking = calcPeerRanking(company)
    if ranking is None:
        return flags

    for r in ranking["rankings"]:
        pctile = r.get("percentile")
        label = r.get("label", "")
        value = r.get("value")

        if pctile is None or value is None:
            continue

        # 수익성 지표: 상위 10%면 기회, 하위 10%면 경고
        if label in ("ROE", "ROA", "영업이익률", "순이익률"):
            if pctile >= 90:
                flags.append((f"{label} 상위 {100 - pctile:.0f}% ({value:.1f}%)", "opportunity"))
            elif pctile <= 10:
                flags.append((f"{label} 하위 {pctile:.0f}% ({value:.1f}%)", "warning"))

        # 부채비율: 상위(높은) 10%면 경고
        elif label == "부채비율":
            if pctile >= 90:
                flags.append((f"부채비율 상위 {100 - pctile:.0f}% ({value:.1f}%)", "warning"))
            elif pctile <= 10:
                flags.append((f"부채비율 하위 {pctile:.0f}% -- 매우 건전", "opportunity"))

        # 성장률: 상위 10%면 기회
        elif label == "매출성장률":
            if pctile >= 90:
                flags.append((f"매출성장률 상위 {100 - pctile:.0f}%", "opportunity"))
            elif pctile <= 10:
                flags.append((f"매출성장률 하위 {pctile:.0f}%", "warning"))

    # 사분면 플래그 — ranking에서 이미 구한 roe/debtRatio로 직접 판정
    _roeR = _findRanking(ranking, "roe")
    _debtR = _findRanking(ranking, "debtRatio")
    if _roeR and _debtR:
        quadrant = _quadrantFromPctile(_roeR["percentile"], _debtR["percentile"])
        if quadrant == "고수익-저위험":
            flags.append(("수익-위험 매트릭스: 고수익-저위험 (우량 포지션)", "opportunity"))
        elif quadrant == "저수익-고위험":
            flags.append(("수익-위험 매트릭스: 저수익-고위험 (구조 개선 필요)", "warning"))

    return flags


# ── 내부 헬퍼 ──


def _getStockCode(company) -> str | None:
    """company에서 stockCode를 안전하게 추출."""
    code = getattr(company, "stockCode", None)
    return code if isinstance(code, str) and code else None


def _findRanking(ranking: dict, ratioName: str) -> dict | None:
    """ranking 결과에서 특정 ratio 항목을 찾는다."""
    for r in ranking.get("rankings", []):
        if r.get("ratioName") == ratioName:
            return r
    return None


def _quadrantFromPctile(roePctile: float, debtPctile: float) -> str:
    """백분위로 사분면 결정."""
    highRoe = roePctile >= 50
    highDebt = debtPctile >= 50
    if highRoe and not highDebt:
        return "고수익-저위험"
    if highRoe and highDebt:
        return "고수익-고위험"
    if not highRoe and not highDebt:
        return "저수익-저위험"
    return "저수익-고위험"


def _calcPercentile(stockCode: str, ratioName: str, label: str) -> dict | None:
    """scan 결과에서 해당 종목의 백분위를 계산."""
    try:
        df = _loadScanRatio(ratioName)
    except (ValueError, ImportError, RuntimeError, FileNotFoundError):
        return None

    if isEmptyDf(df):
        return None

    # 최신 기간 컬럼 찾기
    periodCol = _latestPeriodCol(df)
    if periodCol is None:
        return None

    # 해당 종목 값 추출
    codeCol = "stockCode" if "stockCode" in df.columns else "종목코드"
    if codeCol not in df.columns:
        return None

    target = df.filter(pl.col(codeCol) == stockCode)
    if target.is_empty():
        return None

    targetVal = target.row(0, named=True).get(periodCol)
    if targetVal is None:
        return None

    # 전체 분포에서 백분위 계산
    allVals = df[periodCol].drop_nulls().to_list()
    if len(allVals) < 10:
        return None

    nBelow = sum(1 for v in allVals if v < targetVal)
    percentile = round(nBelow / len(allVals) * 100, 1)
    rank = sum(1 for v in allVals if v > targetVal) + 1

    return {
        "ratioName": ratioName,
        "label": label,
        "value": round(targetVal, 2) if isinstance(targetVal, float) else targetVal,
        "percentile": percentile,
        "rank": rank,
        "total": len(allVals),
        "period": periodCol,
    }


def _getLatestValue(stockCode: str, ratioName: str) -> tuple[float, float] | None:
    """scan에서 해당 종목의 (값, 백분위) 튜플 반환."""
    result = _calcPercentile(stockCode, ratioName, "")
    if result is None:
        return None
    return (result["value"], result["percentile"])


def _loadScanRatio(ratioName: str) -> pl.DataFrame:
    """scan("ratio", name) 경유로 비율 DataFrame을 가져온다."""
    import importlib

    Scan = importlib.import_module("dartlab.scan").Scan

    return Scan()("ratio", ratioName)


def _latestPeriodCol(df: pl.DataFrame) -> str | None:
    """DataFrame 에서 값이 실제로 찬 최신 기간 컬럼을 찾는다.

    이름만 보고 첫 열을 고르면 아직 공시가 거의 안 들어온 분기를 집는다. 2026 년 7 월
    기준 ROE 표의 최신 열은 2026Q3 인데 2,812 종목 중 2 종목(0.1%) 만 값이 있었고,
    삼성전자도 비어 있어 시장 백분위가 어느 회사에서도 나오지 않았다. 비교분석 축
    셋이 통째로 None 이던 원인이다.

    가장 잘 찬 열의 채움 수를 기준으로 문턱을 잡고, 그 이상 찬 열 중 최신을 고른다.
    절대 비율이 아니라 상대 기준이라 표마다 다른 수집 진도를 그대로 따라간다.
    """
    from dartlab.core.utils.helpers import periodCols

    cols = periodCols(df)
    if not cols:
        return None
    counts = {col: df[col].drop_nulls().len() for col in cols}
    fullest = max(counts.values(), default=0)
    if fullest == 0:
        return None
    floor = fullest * _PERIOD_COMPLETENESS
    return next((col for col in cols if counts[col] >= floor), None)
