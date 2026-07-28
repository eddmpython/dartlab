"""dartlab flow account 합산 — 단일 진실의 원천 (SSOT).

dartlab finance (``c.panel("IS") / c.panel("CIS") / c.panel("CF")``) 의 컬럼은 분기 단독값.
(``pivot.py::_normalizeQ4`` 가 raw 4분기 연간 thstrm_amount 를 standalone 으로 변환.)
calc 가 연간값을 얻으려면 4분기 합산이 필요. 이 모듈이 그 합산의 단일 출처.

두 함수를 export 한다:

- ``synthesizeAnnualFromQuarters(data, periods, topic)``
  → dict ``{snakeId: {period: val}}`` 에 연간 키 ``YYYY`` 를 in-place 합성.
  ``toDict``, ``toDictBySnakeId``, ``_financeToDataFrame`` 모두가 호출.

- ``annualSumFlow(flowData, qCol, allPeriods, withFallback)``
  → 단일 컬럼 기준 합산. credit/metrics 의 fallback 경로 전용.
  누적공시 fallback (배당금 1~2회 이벤트) + credit-mode 부분 합산 지원.

데이터 계약:

- ``synthesizeAnnualFromQuarters`` (analysis 표준 — strict)
  - IS/CIS/CF: **4분기 모두 있을 때만** 단순 합 (부분 합산 금지 → None)
  - BS: Q4 (= 연말잔액). 없으면 그 해 가장 최근 분기.

- ``annualSumFlow`` (credit/legacy — lenient)
  - 3 분기 이상 → 평균 × 4 (연환산)
  - 1~2 분기 + ``withFallback=True`` → Q1·Q2 None + Q4 단독 → Q4 그대로 (누적공시)
  - 1~2 분기 + ``withFallback=False`` → 평균 × 4 (credit 모드 부정확 추정)
"""

from __future__ import annotations

from typing import Iterable

# 이벤트성 계정 — 매 분기 발생하지 않는 항목.
# 배당금은 반기 1~2회, 자사주는 비정기, 차입금 상환도 비정기.
# 이런 항목은 4분기 strict 합산 대신 있는 분기만 합산해야 연간값이 나온다.
_EVENT_ACCOUNTS = frozenset(
    {
        "dividends_paid",  # 배당금지급
        "배당금지급",
        "purchase_of_treasury_stock",  # 자사주 매입
        "자기주식의취득",
        "disposal_of_treasury_stock",  # 자사주 처분
        "자기주식처분",
        "proceeds_from_borrowings",  # 차입금 차입
        "차입금의차입",
        "repayment_of_borrowings",  # 차입금 상환
        "차입금상환",
        "decrease_in_lease_obligations",  # 리스부채 감소
        "exercise_of_stock_options",  # 스톡옵션 행사
        "increase_in_noncontrolling_interests",  # 비지배지분 증가
        "government_grants_received",  # 정부보조금
    }
)


def _isEventAccount(key: str) -> bool:
    """이벤트성 계정인지 판별."""
    return key in _EVENT_ACCOUNTS


def synthesizeAnnualFromQuarters(
    data: dict[str, dict],
    periods: list[str],
    topic: str | None,
) -> list[str]:
    """분기 컬럼만 있는 dict 에 연간 키를 in-place 합성 (SSOT).

    ``toDict`` / ``toDictBySnakeId`` / ``_financeToDataFrame`` 셋 다 이 함수 호출.
    규칙 변경은 이 한 곳에서만.

    Args:
        data: ``{snakeId: {period: value}}`` 형태. period 는 ``YYYYQN`` 또는 ``YYYY``.
            in-place 수정 — 합성된 연간 키 ``YYYY`` 가 row 에 추가됨.
        periods: 입력 기간 리스트. 분기 + (이미 있는) 연간 모두 포함 가능.
        topic: ``"BS"`` 면 stock 규칙 (Q4 = 연말잔액 alias),
            그 외 (IS/CIS/CF) 는 flow 규칙 (4분기 strict 합).

    Returns:
        합성된 연간 라벨이 추가된 새 periods 리스트 (최신 우선 정렬).
        이미 존재하는 연간 키는 건너뛴다.

    Examples:
        >>> data = {"sales": {"2024Q1": 10, "2024Q2": 12, "2024Q3": 14, "2024Q4": 16}}
        >>> synthesizeAnnualFromQuarters(data, ["2024Q1","2024Q2","2024Q3","2024Q4"], "IS")
        ['2024', '2024Q4', '2024Q3', '2024Q2', '2024Q1']
        >>> data["sales"]["2024"]
        52
    """
    qPeriods = [p for p in periods if "Q" in p and len(p) >= 5]
    if not qPeriods:
        return periods
    yearMap: dict[str, list[str]] = {}
    for q in qPeriods:
        yearMap.setdefault(q[:4], []).append(q)
    isStock = topic == "BS"
    # 값이 실제로 만들어진 해만 기간 목록에 싣는다. 4 분기가 안 찬 해는 아래 strict 규칙이
    # 옳게 None 을 내는데, 예전에는 그 해 라벨을 그래도 실었다. 그러면 `annualColsFromPeriods`
    # 가 그 해를 맨 앞으로 돌려주고 소비자는 최신 연간값 자리에서 None 을 받는다. 2026 년
    # 1 분기만 나온 시점에 전 종목의 최신 연간 매출이 조용히 비었다. pivot 쪽 같은 계산은
    # 이 상황을 "2026Q1" 로 라벨해 full year 와 구분한다. 여기만 그 구분이 없었다.
    yearsWithValue: set[str] = set()
    for key, row in data.items():
        for yr, qs in yearMap.items():
            if yr in row:
                if row[yr] is not None:
                    yearsWithValue.add(yr)
                continue
            if isStock:
                annualVal = None
                for q in sorted(qs, reverse=True):
                    v = row.get(q)
                    if v is not None:
                        annualVal = v
                        break
            else:
                vals = [row.get(q) for q in qs]
                valid = [v for v in vals if v is not None]
                if len(valid) == 4:
                    # 4분기 모두 있으면 단순 합 (strict — 매출/비용/영업이익 등)
                    annualVal = sum(valid)
                elif len(valid) >= 1 and _isEventAccount(key):
                    # 이벤트성 계정 (배당금, 자사주 등)은 있는 분기만 합산
                    # 배당은 보통 반기 1~2회만 지급 → 4분기 strict 적용하면 항상 None
                    annualVal = sum(valid)
                else:
                    annualVal = None
            row[yr] = annualVal
            if annualVal is not None:
                yearsWithValue.add(yr)
    addedYears = [yr for yr in yearMap if yr not in periods and yr in yearsWithValue]
    if not addedYears:
        return periods
    return sorted(periods + addedYears, key=lambda p: p if "Q" in p else p + "Q5", reverse=True)


def annualSumFlow(
    flowData: dict,
    qCol: str,
    allPeriods: Iterable[str],
    *,
    withFallback: bool = True,
) -> float | None:
    """Q4 컬럼 기준 그 해 4분기 합산.

    Args:
        flowData: {col: value} 형태. col 은 "YYYYQN" 또는 "YYYY".
        qCol: 기준 컬럼. "Q" 가 없으면 그대로 `flowData.get(qCol)` 반환 (annual mode).
        allPeriods: 사용 가능한 모든 컬럼 (set/list/tuple 모두 OK).
        withFallback: True (analysis 모드) — `ttmSum` 의 누적공시 fallback 적용.
                      False (credit 모드) — 1~2 분기도 부분 합산 후 연환산.

    Returns:
        연간 합산 float, 결손 시 None.

    Examples:
        >>> data = {"2025Q1": 10, "2025Q2": 12, "2025Q3": 14, "2025Q4": 16}
        >>> annualSumFlow(data, "2025Q4", set(data.keys()))
        52.0   # 10 + 12 + 14 + 16

        >>> data = {"2025Q1": None, "2025Q2": None, "2025Q3": None, "2025Q4": 50}
        >>> annualSumFlow(data, "2025Q4", set(data.keys()), withFallback=True)
        50.0   # 누적공시 fallback (배당금 등)
        >>> annualSumFlow(data, "2025Q4", set(data.keys()), withFallback=False)
        200.0   # credit 모드: 50 * 4 (부정확 추정)
    """
    if "Q" not in qCol:
        return flowData.get(qCol)

    year = qCol[:4]
    quarters = [f"{year}Q{q}" for q in (4, 3, 2, 1)]
    periodsSet = set(allPeriods) if not isinstance(allPeriods, set) else allPeriods
    vals = [flowData.get(q) for q in quarters if q in periodsSet]
    valid = [v for v in vals if v is not None]

    if len(valid) >= 3:
        return sum(valid) / len(valid) * 4

    if withFallback:
        # 누적공시 fallback (analysis 모드): Q1·Q2 모두 None + Q4 존재 → Q4 그대로 = 연간 누적
        q4 = flowData.get(f"{year}Q4")
        if q4 is not None:
            q1 = flowData.get(f"{year}Q1")
            q2 = flowData.get(f"{year}Q2")
            if q1 is None and q2 is None:
                return q4
        return None

    # credit 모드: 1~2 분기도 부분 데이터로 연환산 (부정확)
    if valid:
        return sum(valid) / len(valid) * 4
    return None
