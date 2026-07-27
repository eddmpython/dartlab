"""costStructure.py 심층 calc 분리 — 비용 본성 + 원재료 분해.

분리 이유: costStructure.py 741 줄. calcCostByNatureAnalysis (198) +
calcRawMaterialBreakdown (131) 약 329 줄. costStructure.py 의 facade (비용 구성·
영업레버리지·BEP·플래그) 책임 유지.

BC: costStructure 모듈에서 두 calc 모두 import 가능 (re-export).
"""

from __future__ import annotations

from typing import Any

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safePct as _pct
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_MAX_YEARS = 8

# 성격별 분류: 주요 비용 카테고리 매핑
_COST_CATEGORY_KEYWORDS = {
    "원재료": ["원재료", "재료비", "원자재"],
    "상품매입": ["상품", "상품매입"],
    "인건비": ["종업원급여", "급여", "인건비", "퇴직급여", "복리후생"],
    "감가상각": ["감가상각", "상각비", "무형자산상각"],
    "외주비": ["외주", "용역"],
    "기타": [],
}


def _splitTotalAndDetailRows(rawRows: list[dict]) -> tuple[dict | None, list[dict]]:
    """합계 행과 세부 행을 가른다. 합계는 처음 만난 하나만 쓴다.

    Parameters
    ----------
    rawRows : list[dict]
        costByNature 주석 표 행 목록.

    Returns
    -------
    tuple[dict | None, list[dict]]
        (합계 행, 세부 행 목록).
    """
    totalRow = None
    detailRows = []
    for row in rawRows:
        item = str(row.get("항목", "")).strip()
        if any(kw in item for kw in ("합계", "총계", "계")):
            if totalRow is None:
                totalRow = row
        else:
            detailRows.append(row)
    return totalRow, detailRows


def _accumulateCostCategories(detailRows: list[dict], periodCols: list[str]) -> dict[str, dict[str, float]]:
    """세부 행을 카테고리별로 접어 기간별 금액을 누적한다.

    Parameters
    ----------
    detailRows : list[dict]
        세부 비용 행.
    periodCols : list[str]
        기간 컬럼 (최신 먼저).

    Returns
    -------
    dict[str, dict[str, float]]
        {카테고리: {기간: 금액}}. 삽입 순서는 행 등장 순서.
    """
    from dartlab.core.utils.helpers import parseNumStr

    categories: dict[str, dict[str, float]] = {}
    for row in detailRows:
        item = str(row.get("항목", "")).strip()
        if not item:
            continue

        # 카테고리 매칭
        matched = "기타"
        for catName, keywords in _COST_CATEGORY_KEYWORDS.items():
            if any(kw in item for kw in keywords):
                matched = catName
                break

        if matched not in categories:
            categories[matched] = {}
        for col in periodCols:
            v = parseNumStr(row.get(col))
            if v is not None:
                categories[matched][col] = categories[matched].get(col, 0) + v
    return categories


def _costTotalsByPeriod(
    totalRow: dict | None,
    categories: dict[str, dict[str, float]],
    periodCols: list[str],
) -> dict[str, float]:
    """기간별 총비용. 합계 행이 없거나 못 쓰면 카테고리 합으로 대체한다.

    Parameters
    ----------
    totalRow : dict | None
        합계 행.
    categories : dict[str, dict[str, float]]
        카테고리별 기간 금액.
    periodCols : list[str]
        기간 컬럼.

    Returns
    -------
    dict[str, float]
        {기간: 총비용}. 양수만 담는다.
    """
    from dartlab.core.utils.helpers import parseNumStr

    totals: dict[str, float] = {}
    if totalRow:
        for col in periodCols:
            v = parseNumStr(totalRow.get(col))
            if v is not None and v > 0:
                totals[col] = v
    if not totals:
        for col in periodCols:
            s = sum(cats.get(col, 0) for cats in categories.values())
            if s > 0:
                totals[col] = s
    return totals


def _costCategoryEntry(
    catName: str,
    vals: dict[str, float],
    periodCols: list[str],
    totals: dict[str, float],
) -> dict[str, Any]:
    """카테고리 하나의 비중 시계열 + 방향 라벨.

    Parameters
    ----------
    catName : str
        카테고리 이름.
    vals : dict[str, float]
        기간별 금액.
    periodCols : list[str]
        기간 컬럼 (최신 먼저).
    totals : dict[str, float]
        기간별 총비용.

    Returns
    -------
    dict
        name / history / latestRatio / direction.
    """
    history = []
    for col in periodCols:
        amt = vals.get(col, 0)
        total = totals.get(col, 0)
        ratio = round(amt / total * 100, 1) if total > 0 else 0
        history.append({"period": col, "amount": amt, "ratio": ratio})

    latestRatio = history[0]["ratio"] if history else 0
    direction = None
    ratios = [h["ratio"] for h in history if h["ratio"] > 0]
    if len(ratios) >= 2:
        diff = ratios[0] - ratios[-1]
        if diff > 3:
            direction = "비중 증가"
        elif diff < -3:
            direction = "비중 감소"
        else:
            direction = "안정"

    return {
        "name": catName,
        "history": history,
        "latestRatio": latestRatio,
        "direction": direction,
    }


def _costStructureInsight(resultCategories: list[dict]) -> str | None:
    """인건비 또는 원재료 비중 증가를 한 줄로 요약.

    Parameters
    ----------
    resultCategories : list[dict]
        _costCategoryEntry 결과 목록.

    Returns
    -------
    str | None
        인사이트 문장. 해당 없으면 None.
    """
    laborCat = next((c for c in resultCategories if c["name"] == "인건비"), None)
    materialCat = next((c for c in resultCategories if c["name"] == "원재료"), None)
    if laborCat and laborCat["direction"] == "비중 증가":
        return f"인건비 비중 {laborCat['latestRatio']:.0f}%로 증가 추세. 노동집약도 심화"
    if materialCat and materialCat["direction"] == "비중 증가":
        return f"원재료비 비중 {materialCat['latestRatio']:.0f}%로 증가. 원가 부담 확대"
    return None


@memoizedCalc
def calcCostByNatureAnalysis(company, *, basePeriod: str | None = None) -> dict | None:
    """비용의 성격별 분류(notes) — 인건비/원재료/감가상각 비중 추세.

    Capabilities:
        K-IFRS 주석 "비용의 성격별 분류" 표에서 원재료/인건비/감가상각/
        외주가공/물류 등 카테고리별 금액·비중 시계열 추출 + 비중 방향성
        (증가/감소/안정) 자동 라벨. 173+ 회사 데이터 (금융/REIT/지주는 미공시).
        IS 의 "기능별" 분류 (매출원가/판관비) 와 직교 — 비용 성격 원인 추적.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``categories`` (list[dict]): 카테고리별 (name, history list,
              latestRatio, direction).
            - ``periods`` (list[str]): 회계연도 목록.
            - ``insight`` (str | None): 주요 변화 요약.

    Raises:
        없음.

    Example:
        >>> r = calcCostByNatureAnalysis(Company("005930"))
        >>> r["categories"][0]
        {'name': '원재료', 'latestRatio': 45.2, 'direction': '비중 증가', ...}

    Guide:
        - 원재료비 비중 상승 = commodity 원가 충격 (반도체 wafer/철강 철광석).
        - 인건비 비중 상승 = 자동화 부족 또는 임금 인상.
        - 감가상각 비중 상승 = 대규모 CapEx 후 효과 (반도체 fab).
        매출원가율 (calcCostBreakdown) 상승 원인을 본 표로 분해.

    When:
        매출원가율 변화 원인 분해, 비용 성격 추세 추적 시점.

    How:
        notes costByNature 표 파싱 → 카테고리별 비중 시계열 + direction 라벨.

    SeeAlso:
        - ``calcCostBreakdown``: 기능별 (매출원가/판관비)
        - ``calcRawMaterialBreakdown``: 원재료 세분화 (제조업)
        - ``calcOperatingLeverage``: DOL (고정비/변동비 비중과 연결)

    Requires:
        K-IFRS 주석 "비용의 성격별 분류" 표 — 회사가 공시한 경우만 (금융/
        REIT/지주는 None 반환).

    AIContext:
        카테고리별 direction + latestRatio 함께. 원재료 + 인건비 합계가
        70% 이상이면 변동비 중심 (서비스/유통), 30% 미만이면 고정비 중심
        (반도체/통신). insight 가 자동 생성된 주요 변화 1~2 줄.

    LLM Specifications:
        AntiPatterns:
            - 단년도 비중 인용 — direction (3 년 추세) 함께.
            - 금융업/REIT/지주에 본 함수 호출 — None 반환, 주석 미공시.
        OutputSchema:
            ``{categories: list[dict], periods: list[str], insight: str?}``.
        Prerequisites:
            K-IFRS 주석 본문에서 "비용의 성격별 분류" 표 공시.
        Freshness:
            연간 (주석 본질).
        Dataflow:
            notes (costByNature) → 카테고리 매핑 (원재료/인건비/감가상각/...)
            → 비중 시계열 → direction 라벨 + insight 합성.
        TargetMarkets: KR (K-IFRS 주석 표준), US 는 별도 (10-K natural cost 미공시).
    """
    from dartlab.analysis.financial.companyContext import fetchNotesDetail
    from dartlab.core.utils.helpers import parseNumStr

    notesData = fetchNotesDetail(company, ["costByNature"])
    rawRows = notesData.get("costByNature")
    if not rawRows:
        return None

    # costByNature: [{항목, 2024, 2023, ...}] (항목×연도 테이블)
    # 기간 컬럼 추출
    sampleRow = rawRows[0]
    periodCols = sorted(
        [k for k in sampleRow if k not in ("항목",) and str(k).replace("-", "").isdigit()], reverse=True
    )
    if not periodCols:
        return None

    periodCols = periodCols[:_MAX_YEARS]

    # 총비용 행 찾기 (합계/총계)
    totalRow, detailRows = _splitTotalAndDetailRows(rawRows)

    if not detailRows:
        return None

    categories = _accumulateCostCategories(detailRows, periodCols)

    if not categories:
        return None

    totals = _costTotalsByPeriod(totalRow, categories, periodCols)

    # 카테고리별 결과 생성
    resultCategories = [
        _costCategoryEntry(catName, vals, periodCols, totals) for catName, vals in categories.items() if vals
    ]

    # 비중 기준 정렬 (기타 제외하고 큰 순)
    resultCategories.sort(key=lambda x: (x["name"] == "기타", -x["latestRatio"]))

    return {
        "categories": resultCategories,
        "periods": periodCols,
        "insight": _costStructureInsight(resultCategories),
    }


# ── 원재료 비중 (docs 보강) ──


@memoizedCalc
def calcRawMaterialBreakdown(company, *, basePeriod: str | None = None) -> dict | None:
    """주요 원재료 품목별 매입액 비중 — rawMaterial docs 토픽.

    Capabilities:
        DART/EDGAR 사업보고서 "주요 원재료 매입현황" 표에서 품목별 매입액
        + 총매입액 대비 비중 (%) 상위 8 개 (금액 내림차순) 추출. 계층 테이블
        (부문×품목) 도 정상 파싱. % 행 자동 제외 (금액 행만).

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신 (회계연도 기준).

    Returns:
        dict | None:
            - ``segments`` (list[dict]): 최대 8 개 (name, amount, pct)
            - ``totalAmount`` (float): 총매입액
            - ``period`` (str): 기준 회계연도

    Raises:
        없음.

    Example:
        >>> r = calcRawMaterialBreakdown(Company("005930"))
        >>> r["segments"][0]
        {'name': 'wafer', 'amount': 5.2e12, 'pct': 35.0}

    Guide:
        - 단일 품목 > 40% = 단일 원재료 의존도 위험 (commodity 가격 충격
          취약).
        - 반도체 = wafer/chemical, 자동차 = 철강/플라스틱, 화학 = 나프타.
        - 매입액 절대값 + commodity 가격 추세 (FRED) 함께 보면 마진 압박
          예측 가능.

    When:
        원재료 의존도·commodity 노출 평가 시점.

    How:
        rawMaterial 사업보고서 표 → 최신 연도 금액 행 추출 → 상위 8 개 정렬.

    SeeAlso:
        - ``calcCostByNatureAnalysis``: 비용 성격별 (인건/감가/원재료 합계)
        - ``analysis.business.calcSegmentFinancials``: 사업부문 매출 분해
        - ``industry.materials``: 산업 평균 원재료 비중

    Requires:
        DART 사업보고서 "주요 원재료" 섹션 — 제조업만 공시 (금융/서비스 None).

    AIContext:
        품목명 + 비중 함께 인용. 단일 품목 40% 이상이면 risk 신호로 라벨.
        총매입액 / 매출액 = 변동비 비중 추정 가능 (정밀하진 않음).

    LLM Specifications:
        AntiPatterns:
            - 비중 100% 인용 — 본 함수가 총계 행 자동 제외, 상위 8 개만.
            - 금융/서비스에 본 함수 호출 — None 반환.
        OutputSchema:
            ``{segments: list[dict 3키], totalAmount: float, period: str}``.
        Prerequisites:
            DART 사업보고서 "주요 원재료 매입현황" 표.
        Freshness:
            연간 (사업보고서 본질).
        Dataflow:
            rawMaterial topic → 항목×기간 테이블 → 최신 연도 컬럼 → 금액 행
            추출 (%, 소계/총계/합계 제외) → 내림차순 → 상위 8 개.
        TargetMarkets: KR (DART), US 는 별도 (10-K segment 데이터).
    """
    from dartlab.core.utils.helpers import parseNumStr

    result = company.select("rawMaterial", ["매입액"])
    if result is None:
        return None

    import polars as pl

    df = result if isinstance(result, pl.DataFrame) else getattr(result, "df", None)
    if df is None or "항목" not in df.columns:
        return None

    from dartlab.core.utils.helpers import periodCols

    pCols = periodCols(df)
    if not pCols:
        return None

    # 최신 연도 컬럼 사용 (basePeriod 이하, Q 없는 연도 우선)
    annuals = annualColsFromPeriods(pCols, basePeriod, 1)
    latestCol = annuals[0] if annuals else pCols[0]

    labelCol = "항목"
    items = df[labelCol].to_list()
    vals = df[latestCol].to_list()

    # 총계 행 찾기
    totalAmount = None
    for it, v in zip(items, vals):
        if any(k in str(it) for k in ["총계", "합계"]):
            totalAmount = parseNumStr(str(v))
            break

    if totalAmount is None or totalAmount <= 0:
        return None

    # 금액 행만 추출 (소계/총계 제외, % 비중 행 제외)
    segments = []
    for it, v in zip(items, vals):
        it = str(it)
        vStr = str(v).strip()
        if any(k in it for k in ["총계", "합계", "소계"]):
            continue
        if "%" in vStr:
            continue
        parsed = parseNumStr(vStr)
        if parsed is None or parsed <= 0:
            continue
        name = it.replace("_매입액", "").strip()
        if not name:
            continue
        pct = parsed / totalAmount * 100
        if pct < 1:
            continue
        segments.append({"name": name, "amount": parsed, "pct": round(pct, 1)})

    if not segments:
        return None

    segments.sort(key=lambda x: x["amount"], reverse=True)
    return {
        "segments": segments[:8],
        "totalAmount": totalAmount,
        "period": latestCol,
    }


# ── 플래그 ──
