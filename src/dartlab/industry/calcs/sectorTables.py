"""업종 분포 계산이 쓰는 횡단면 표를 프로세스 안에서 한 번만 읽는다.

왜 필요한가. 업종 내 위치를 재려면 시장 전체 횡단면이 필요하고, 그 횡단면은 회사와 무관하다.
그런데 지금까지는 회사를 물을 때마다 같은 표를 처음부터 다시 읽었다. 실측(2026-08-06)으로
따뜻한 상태에서도 수익성 2.5 초, 성장 3.8 초, 유동성 2.3 초, 부채 4.5 초다. 회사 두 곳을
물으면 13 초를 그대로 다시 낸다.

표는 회사가 아니라 시장에 속한다. 한 번 읽어 프로세스 안에 들고 있으면 두 번째 회사부터는
공짜다. 공시가 갱신될 때만 바뀌는 값이라 한 세션 동안 들고 있어도 사실이 흐려지지 않는다.

DataFrame 을 들고 있지 않는다. 읽자마자 필요한 열만 {종목코드: 실수} 로 뽑고 원본은 버린다.
축 다섯 개를 다 합쳐도 실측 3MB 다(2026-08-06). Company 하나가 200~500MB 인 이 저장소에서
수천 행 DataFrame 을 들고 있으면 압력 관리 캐시가 곧바로 되돌려 놓는다. 실제로 처음에
`BoundedCache` 로 원본을 들었더니 예열 16 초 뒤에도 다음 호출이 14 초를 다시 냈다.
쫓겨나서 다시 읽은 것이다. 그래서 **작게 만들어 놓는 쪽**을 택했다. 이 방식은 오늘보다
최대 메모리도 낮다. 호출마다 DataFrame 을 새로 만들지 않기 때문이다.
"""

from __future__ import annotations

import importlib
import threading
import time
from typing import Any, Callable

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# 공시가 갱신될 때만 바뀌는 값이라 한 시간은 안전하다.
_TABLE_TTL_SECONDS = 3600.0
_lock = threading.RLock()
_distilled: dict[str, dict[str, float]] = {}
_loadedAt = 0.0

# (지표 이름, 스캐너 모듈, 스캐너 함수, 그 스캐너가 쓰는 컬럼 이름).
# 지표 이름은 이 모듈 밖에서 쓰는 정본 키다.
_SOURCES: tuple[tuple[str, str, str, str], ...] = (
    ("opMargin", "dartlab.scan.financial.profitability", "scanProfitability", "opMargin"),
    ("roe", "dartlab.scan.financial.profitability", "scanProfitability", "roe"),
    ("revenueCagr", "dartlab.scan.financial.growth", "scanGrowth", "revenueCagr"),
    ("currentRatio", "dartlab.scan.financial.liquidity", "scanLiquidity", "currentRatio"),
    ("debtRatio", "dartlab.scan.debt.scanner", "scanDebtMix", "부채비율"),
)


def _load(moduleName: str, functionName: str) -> Any:
    """스캐너 하나를 부른다. 실패는 None 이고 나머지 축은 살린다."""
    try:
        scanner: Callable[[], Any] = getattr(importlib.import_module(moduleName), functionName)
        return scanner()
    except Exception as exc:
        _log.warning("횡단면 표 로드 실패 %s.%s: %s: %s", moduleName, functionName, type(exc).__name__, exc)
        return None


def _rowsByStockCode(table: Any) -> dict[str, dict[str, Any]]:
    """스캐너 결과를 종목코드 색인으로 통일한다. DataFrame 도 dict 도 같은 모양으로 나온다."""
    if table is None:
        return {}
    if isinstance(table, dict):
        return {str(code): row for code, row in table.items() if isinstance(row, dict)}
    if hasattr(table, "is_empty"):
        if table.is_empty() or "stockCode" not in getattr(table, "columns", []):
            return {}
        return {str(row["stockCode"]): row for row in table.iter_rows(named=True)}
    return {}


def sectorMetricTables() -> dict[str, dict[str, float]]:
    """지표별 {종목코드: 값} 표를 모아 준다.

    Capabilities:
        업종 분포에 필요한 다섯 축(영업이익률·ROE·매출 성장률·유동비율·부채비율)의 시장
        전체 횡단면을 지표 이름으로 색인해 돌려준다. 프로세스 캐시를 거치므로 두 번째
        호출부터는 읽기 비용이 없다.

    Returns
    -------
    dict[str, dict[str, float]]
        지표 이름 → {종목코드: 값}. 스캐너가 실패한 축은 빈 dict 다.

    Raises
    ------
    없음 (축별로 실패를 흡수하고 나머지 축은 살린다).

    Example
    -------
    >>> tables = sectorMetricTables()
    >>> tables["debtRatio"]["005930"]
    30.1

    Guide
    -----
    새 축은 ``_SOURCES`` 에 (지표 이름, 모듈, 함수, 컬럼) 한 줄을 더하면 된다. 스캐너 자체는
    L1.5 scan 이 소유하므로 여기서 지표를 다시 계산하지 않는다.

    When
    ----
    ``calcSectorMetrics`` 가 분포를 만들기 직전에 부른다. 단독 호출은 드물다.

    How
    ---
    축마다 스캐너를 캐시로 부르고 종목코드 색인으로 바꾼 뒤 해당 컬럼만 뽑는다.

    Requires
    --------
    - L1.5 scan 의 profitability / growth / liquidity / debt 산출물.

    See Also
    --------
    - ``dartlab.industry.calcs.companyCalcs.calcSectorMetrics`` : 유일한 소비자

    AIContext
    ---------
    값이 없는 회사는 키 자체가 없다. 분포에서 빠질 뿐 0 으로 채우지 않는다. 0 으로 채우면
    부채가 없는 회사와 데이터가 없는 회사가 같아진다.
    """
    global _distilled, _loadedAt
    with _lock:
        if _distilled and time.monotonic() - _loadedAt < _TABLE_TTL_SECONDS:
            return _distilled
        out: dict[str, dict[str, float]] = {}
        indexed: dict[str, dict[str, dict[str, Any]]] = {}
        for metric, moduleName, functionName, column in _SOURCES:
            sourceKey = f"{moduleName}.{functionName}"
            if sourceKey not in indexed:
                indexed[sourceKey] = _rowsByStockCode(_load(moduleName, functionName))
            values: dict[str, float] = {}
            for code, row in indexed[sourceKey].items():
                raw = row.get(column)
                if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                    continue
                values[code] = float(raw)
            out[metric] = values
        # 원본 표는 여기서 놓는다. 실수만 남기고 DataFrame 은 들고 가지 않는다.
        indexed.clear()
        _distilled = out
        _loadedAt = time.monotonic()
        return _distilled


__all__ = ["sectorMetricTables"]
