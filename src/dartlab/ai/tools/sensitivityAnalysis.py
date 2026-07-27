"""SensitivityAnalysis — DCF parameter grid (WACC × growth) → heatmap matrix.

마스터 플랜 트랙 1 PR-4 (cryptic-discovering-kettle.md). dcf.multiStageDcf grid loop —
사용자 명시 ranges (예: WACC 8~12% × growth 0~5%) NxM 매트릭스 한 도구 호출로 답변.
LLM 이 매번 RunPython 으로 grid loop 작성하던 회귀 차단.

신뢰도 30 (forecast method) — DCF 가정 다중 누적.

graph 회귀 방지: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore
from dartlab.core.market import detectMarket

from .companyResolve import resolveCompanyOrNone
from .dcfValuationTool import _resolveSectorParams, _resolveSeries, _resolveShares
from .types import ToolResult

_DEFAULT_WACC_RANGE = (8.0, 12.0, 5)  # min, max, steps
_DEFAULT_GROWTH_RANGE = (1.0, 5.0, 5)
_MAX_GRID_CELLS = 49  # 안전 상한 (7x7)


def _buildAxisValues(low: float, high: float, steps: int) -> list[float]:
    """linear 격자 — (low, high, steps) → list[float]. steps=1 → [low] 단일."""
    if steps <= 1:
        return [low]
    out: list[float] = []
    delta = (high - low) / (steps - 1)
    for i in range(steps):
        out.append(round(low + i * delta, 4))
    return out


def sensitivityAnalysis(
    stockCode: str = "",
    waccRange: list[float] | tuple[float, float, int] | None = None,
    growthRange: list[float] | tuple[float, float, int] | None = None,
    projectionYears: int = 5,
) -> ToolResult:
    """DCF parameter grid 민감도 분석 — WACC × terminalGrowth NxM 매트릭스.

    Capabilities:
        dcf.multiStageDcf 반복 호출 (grid) → 각 셀 perShareValue. heatmap-friendly
        matrix 반환. WACC 8~12% × growth 0~5% 5x5 기본 (25 셀).

    Parameters
    ----------
    stockCode : str
        6 자리 KR 또는 US ticker. 필수.
    waccRange : list[float] | None
        [min, max, steps] (예: [8.0, 12.0, 5]). 기본 [8.0, 12.0, 5].
    growthRange : list[float] | None
        [min, max, steps] (예: [1.0, 5.0, 5]). 기본 [1.0, 5.0, 5].
    projectionYears : int
        초기 고성장 구간 (년). 기본 5.

    Returns
    -------
    ToolResult
        - data.waccValues : list[float]
        - data.growthValues : list[float]
        - data.matrix : list[list[float|None]] — [waccIdx][growthIdx] perShare
        - data.baseAssumption : {fcf, netDebt, shares}
        - data.confidence : 30 (forecast method)
        - refs : tableRef (matrix + axes)

    Example
    -------
        SensitivityAnalysis(stockCode="005930",
                            waccRange=[8.0, 12.0, 5],
                            growthRange=[0.0, 4.0, 5])

    Raises
    ------
    없음 — 모든 실패 ToolResult(ok=False, error=...). 셀 계산 실패는 None 으로 채움.

    Guide
    -----
        grid cells > 49 (7x7) 자동 truncate — multiStageDcf 호출 비용 가드. 셀 1 개당
        다단 phase DCF 1 회 (~수십 ms).

    SeeAlso
    -------
        - DCFValuation : 단일 시나리오 가치평가
        - dcf.multiStageDcf : 본 도구가 호출하는 본체
        - dcf.dcfValuation : DCFValuation 도구가 호출

    Requires
    --------
        DART/EDGAR 사전 다운로드. company.finance.timeseries 정상 추출.

    AIContext
    ---------
        "WACC 민감도", "할인율 변화", "성장률 민감도", "민감도 매트릭스" 류 질문에
        본 도구 호출. waccRange/growthRange 사용자 명시 시 그대로.

    LLM Specifications
    ------------------
        AntiPatterns:
            - waccRange=[12, 8, 5] (역순) — auto-fix.
            - steps > 7 — _MAX_GRID_CELLS=49 cap (자동 truncate).
        OutputSchema:
            matrix[waccIdx][growthIdx] = perShare (float|None).
        Prerequisites:
            DART/EDGAR 사전 다운로드.
        Freshness:
            분기 결산 발표 후 갱신.
        Dataflow:
            stockCode → Company → series + sectorParams → grid loop
            (multiStageDcf × NxM) → matrix.
        TargetMarkets:
            KR (DART) · US (EDGAR).
    """
    from dartlab.analysis.valuation._dcfHelpers import _getNetDebt, _resolveBaseFcf
    from dartlab.analysis.valuation.dcf import multiStageDcf

    if not stockCode:
        return ToolResult(False, "stockCode 필수.", error="missing_stock_code")

    company = resolveCompanyOrNone(stockCode)
    if company is None:
        return ToolResult(False, f"company_not_resolved: {stockCode}", error="company_not_resolved")

    series = _resolveSeries(company)
    if not series:
        return ToolResult(False, f"finance.timeseries 추출 실패: {stockCode}", error="series_unavailable")

    sp = _resolveSectorParams(company)
    shares = _resolveShares(company)

    # baseFcf + netDebt 추출 (DCF 와 동일 SSOT).
    warnings_acc: list[str] = []
    try:
        baseFcf = _resolveBaseFcf(series, warnings_acc)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(False, f"baseFcf 추출 실패: {type(exc).__name__}: {exc}", error="base_fcf_failed")
    if not baseFcf or baseFcf <= 0:
        return ToolResult(False, "baseFcf <= 0 — DCF 적용 불가", error="non_positive_fcf")
    try:
        netDebt = _getNetDebt(series)
    except Exception:  # noqa: BLE001
        netDebt = 0.0

    # 격자 입력 normalize. tuple/list 모두 허용.
    def _normRange(raw: Any, default: tuple[float, float, int]) -> tuple[float, float, int]:
        if raw is None:
            return default
        if isinstance(raw, (list, tuple)) and len(raw) >= 3:
            try:
                lo = float(raw[0])
                hi = float(raw[1])
                steps = int(raw[2])
                if lo > hi:
                    lo, hi = hi, lo
                steps = max(1, min(steps, 7))
                return (lo, hi, steps)
            except (ValueError, TypeError):
                return default
        return default

    waccLo, waccHi, waccSteps = _normRange(waccRange, _DEFAULT_WACC_RANGE)
    growthLo, growthHi, growthSteps = _normRange(growthRange, _DEFAULT_GROWTH_RANGE)

    if waccSteps * growthSteps > _MAX_GRID_CELLS:
        warnings_acc.append(f"grid {waccSteps}x{growthSteps} 초과 — {_MAX_GRID_CELLS} cell 로 truncate")
        # waccSteps 우선 유지 + growthSteps cap
        growthSteps = max(1, _MAX_GRID_CELLS // waccSteps)

    waccValues = _buildAxisValues(waccLo, waccHi, waccSteps)
    growthValues = _buildAxisValues(growthLo, growthHi, growthSteps)

    matrix: list[list[float | None]] = []
    for wacc in waccValues:
        row: list[float | None] = []
        for tg in growthValues:
            try:
                r = multiStageDcf(
                    baseFcf=baseFcf,
                    growthYears=projectionYears,
                    growthRates=tg + 5.0,  # 초기 성장은 terminal 보다 5%p 위 (단순화)
                    terminalGrowthRate=tg,
                    wacc=wacc,
                    netDebt=netDebt,
                    shares=shares,
                )
                row.append(r.get("perShare"))
            except Exception:  # noqa: BLE001
                row.append(None)
        matrix.append(row)

    confidence = baseScore("forecast")
    corpName = str(getattr(company, "corpName", None) or "")
    unit = "KRW" if detectMarket(stockCode) == "KR" else "USD"

    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "corpName": corpName,
        "waccValues": waccValues,
        "growthValues": growthValues,
        "matrix": matrix,
        "baseAssumption": {
            "baseFcf": baseFcf,
            "netDebt": netDebt,
            "shares": shares,
            "projectionYears": projectionYears,
        },
        "unit": unit,
        "warnings": warnings_acc,
        "confidence": confidence,
        "confidenceMethod": "forecast",
    }

    refs: list[Ref] = [
        Ref(
            id=f"sensitivity:{stockCode}:matrix",
            kind="tableRef",
            title=f"{corpName or stockCode} DCF 민감도 {waccSteps}x{growthSteps}",
            source="sensitivityAnalysis",
            payload=payload,
        )
    ]
    valid_cells = [c for row in matrix for c in row if c is not None]
    summary_parts = [f"{corpName or stockCode} 민감도 {waccSteps}x{growthSteps}"]
    if valid_cells:
        summary_parts.append(f"range={min(valid_cells):,.0f}~{max(valid_cells):,.0f}")
    summary_parts.append(f"WACC {waccLo:.1f}~{waccHi:.1f}%")
    summary_parts.append(f"g {growthLo:.1f}~{growthHi:.1f}%")

    return ToolResult(True, " · ".join(summary_parts), refs=refs, data=payload)


__all__ = ["sensitivityAnalysis"]
