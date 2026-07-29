"""재무비율 엔진이 공유하는 안전 연산, 업종 정책, 입력 선택기."""

from __future__ import annotations

from dartlab.core.ratios.models import RatioResult
from dartlab.core.utils.calc import safeDiv as _safeDiv
from dartlab.core.utils.calc import safePct as _safePct
from dartlab.core.utils.calc import safePctPositive as _safePctPositive
from dartlab.core.utils.extract import getLatest, getTTM

_ARCHETYPES = frozenset({"general", "insurance", "bank", "securities", "financial"})


def _safeRound(v: float | None, n: int = 2) -> float | None:
    if v is None:
        return None
    return round(v, n)


def _sumComplete(*values: float | None) -> float | None:
    """모든 구성값이 있을 때만 합계를 반환한다."""
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def _calcNetDebt(
    shortTermBorrowings: float | None,
    longTermBorrowings: float | None,
    bonds: float | None,
    cash: float | None,
) -> float | None:
    """공시된 차입금 세 항목과 현금이 모두 있을 때만 순차입금을 계산한다."""
    totalBorrowings = _sumComplete(shortTermBorrowings, longTermBorrowings, bonds)
    if totalBorrowings is None or cash is None:
        return None
    return totalBorrowings - cash


def _calcEbitdaValue(
    operatingIncome: float | None,
    depreciationExpense: float | None,
) -> float | None:
    """보고된 영업이익과 감가상각비로만 EBITDA를 계산한다."""
    if operatingIncome is None or depreciationExpense is None:
        return None
    return operatingIncome + depreciationExpense


def yoyPct(cur: float | None, prev: float | None) -> float | None:
    """전년 대비 증감률(%). 부호 전환 시 None 반환.

    - 양수→양수 또는 음수→음수: 정상 계산
    - 부호 전환(흑자↔적자): None (단순 비교 불가)
    - 분모 0 또는 None: None
    """
    if cur is None or prev is None or prev == 0:
        return None
    if prev > 0 and cur >= 0:
        return round(((cur - prev) / prev) * 100, 2)
    if prev < 0 and cur < 0:
        return round(((cur - prev) / abs(prev)) * 100, 2)
    return None


def _yoy(vals: list[float | None], i: int, lag: int = 1) -> float | None:
    if i < lag:
        return None
    return yoyPct(vals[i], vals[i - lag])


def _get(series: dict, sjDiv: str, snakeId: str) -> list[float | None]:
    return series.get(sjDiv, {}).get(snakeId, [])


def _detectArchetype(series: dict[str, dict[str, list[float | None]]]) -> str:
    """점수 기반 업종 분류. 하이브리드 기업도 정확히 분류.

    각 archetype의 시그니처 계정 존재 여부로 점수를 매기고,
    가장 높은 점수의 archetype을 반환. 복수 archetype이 비슷하면 "financial" 반환.
    """
    isKeys = {key for key, values in series.get("IS", {}).items() if any(value is not None for value in values)}
    bsKeys = {key for key, values in series.get("BS", {}).items() if any(value is not None for value in values)}

    scores: dict[str, int] = {
        "insurance": 0,
        "bank": 0,
        "securities": 0,
    }

    # 보험 시그니처
    _INSURANCE_IS = {
        "insurance_revenue",
        "assumed_reinsurance_premiums",
        "benefit_payments",
        "insurance_service_expense",
        "net_insurance_finance_expense",
    }
    scores["insurance"] = len(_INSURANCE_IS.intersection(isKeys))

    # 은행 시그니처
    _BANK_IS = {"interest_income", "net_interest_income"}
    _BANK_BS = {"loans", "cash_and_deposits", "debt_securities_at_amortized_cost", "deposits_from_customers"}
    scores["bank"] = len(_BANK_IS.intersection(isKeys)) + len(_BANK_BS.intersection(bsKeys))

    # 증권 시그니처
    _SEC_IS = {"commission_income", "fee_and_commission_income"}
    _SEC_BS = {
        "financial_assets_at_fv_through_profit",
        "financial_assets_at_fv_through_oci",
        "financial_assets_at_amortized_cost",
    }
    scores["securities"] = len(_SEC_IS.intersection(isKeys)) + len(_SEC_BS.intersection(bsKeys))

    # 일반 기업 시그니처 -- 매출/매출원가/판관비/영업비용이 있으면 general 우세
    # NAVER 같은 IT/플랫폼은 매출원가 없이 operating_expenses 단일 사용
    _GENERAL_IS = {
        "sales",
        "revenue",
        "cost_of_sales",
        "selling_and_administrative_expenses",
        "operating_expenses",
    }
    generalSignals = len(_GENERAL_IS.intersection(isKeys))

    # 일반 기업 BS 시그니처 (재고/매출채권/유형자산) -- IT/플랫폼은 재고 없을 수 있어 1개로 충분
    _GENERAL_BS = {"inventories", "trade_and_other_receivables", "tangible_assets", "intangible_assets"}
    generalSignalsBs = len(_GENERAL_BS.intersection(bsKeys))

    # 최고 점수 archetype 선택
    max_score = max(scores.values())
    if max_score == 0:
        return "general"

    # 일반 기업 시그니처가 충분하면 (IS 2+ 또는 IS 1 + BS 2+) 금융업 오분류 방지.
    # securities 처럼 financial_assets_* 만 점수에 잡히는 hybrid 도 제외.
    if max_score < 4 and (generalSignals >= 2 or (generalSignals >= 1 and generalSignalsBs >= 2)):
        return "general"

    top = [k for k, v in scores.items() if v == max_score]

    # 복수 archetype이 동점이면 "financial" (하이브리드)
    if len(top) > 1:
        return "financial"

    return top[0]


def _resolveArchetype(
    series: dict[str, dict[str, list[float | None]]],
    override: str | None,
) -> str:
    """명시된 업종 정책을 검증하고 없으면 입력 계정에서 판별한다."""
    if override is None:
        return _detectArchetype(series)
    if override not in _ARCHETYPES:
        allowed = ", ".join(sorted(_ARCHETYPES))
        raise ValueError(f"archetypeOverride must be one of: {allowed}")
    return override


def _setNone(result: RatioResult, *fieldNames: str) -> None:
    for fieldName in fieldNames:
        setattr(result, fieldName, None)


def _applyArchetypePolicyResult(result: RatioResult, archetype: str) -> None:
    if archetype == "general":
        return

    _setNone(
        result,
        "debtRatio",
        "currentRatio",
        "quickRatio",
        "cashRatio",
        "interestCoverage",
        "netDebt",
        "netDebtRatio",
        "noncurrentRatio",
        "workingCapital",
        "inventoryTurnover",
        "fixedAssetTurnover",
        "receivablesTurnover",
        "payablesTurnover",
        "operatingCycle",
        "operatingCfMargin",
        "operatingCfToNetIncome",
        "operatingCfToCurrentLiab",
        "capexRatio",
        "fcf",
        "fcfToOcfRatio",
    )

    _setNone(
        result,
        "ccc",
        "dso",
        "dio",
        "dpo",
        "roic",
        "debtToEbitda",
        "piotroskiFScore",
        "altmanZScore",
        "altmanZppScore",
        "springateSScore",
        "zmijewskiXScore",
        "sloanAccrualRatio",
    )

    if archetype in {"bank", "financial"}:
        _setNone(
            result,
            "operatingMargin",
            "netMargin",
            "preTaxMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
            "roce",
        )


def _pickFirst(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeIds: list[str],
    annual: bool = False,
    maxTrailingNones: int | None = None,
) -> float | None:
    def _getTtmValue(
        targetSeries: dict[str, dict[str, list[float | None]]],
        targetSjDiv: str,
        targetSnakeId: str,
    ) -> float | None:
        return getTTM(targetSeries, targetSjDiv, targetSnakeId, maxTrailingNones=maxTrailingNones)

    if annual:
        getter = getLatest
    else:
        getter = _getTtmValue
    for snakeId in snakeIds:
        val = getter(series, sjDiv, snakeId)
        if val is not None:
            return val
    return None


def _pickSeries(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeIds: list[str],
) -> list[float | None]:
    for snakeId in snakeIds:
        values = _get(series, sjDiv, snakeId)
        if any(v is not None for v in values):
            return values
    return []


def _averageLatest(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeIds: list[str],
    lag: int,
) -> float | None:
    """최신값과 전년 동기값의 평균을 반환하고 시작값이 없으면 최신값을 쓴다."""
    values = _pickSeries(series, sjDiv, snakeIds)
    currentIndex = next((index for index in range(len(values) - 1, -1, -1) if values[index] is not None), None)
    if currentIndex is None:
        return None
    current = values[currentIndex]
    if current is None:
        return None
    previousIndex = currentIndex - lag
    if previousIndex < 0:
        return current
    previous = values[previousIndex]
    if previous is None:
        return current
    return (current + previous) / 2
