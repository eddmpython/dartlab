"""DCFValuation tool — Damodaran DCF 내재가치 밴드 (bear/base/bull) 자율 호출 도구.

내부 자산 100% 재사용 — ``analysis.valuation.dcf.dcfValuation`` 3 회 호출 (base/bull/bear).
discountRate ± 100bps + terminalGrowth ± 50bps 표준 변형
(``analysis.forecast._forecastScenario`` 패턴 모방).

신뢰도 30 (dcf method) — 가정 다중 누적. UI 답변 본문에 [conf:30] 인용 권장.

graph 회귀 방지: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.

마스터 플랜 트랙 1 PR-1 (cryptic-discovering-kettle.md).
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore
from dartlab.core.market import detectMarket

from .companyResolve import resolveCompanyOrNone
from .types import ToolResult

_DEFAULT_SECTOR = {
    "discountRate": 10.0,
    "growthRate": 3.0,
    "perMultiple": 15,
    "pbrMultiple": 1.2,
    "evEbitdaMultiple": 8,
    "label": "기타",
}


def _resolveSectorParams(company: Any) -> Any:
    """Company → SectorParams. 실패 시 기본값 (discountRate 10%, growthRate 3%)."""
    from dartlab.frame.sector import SectorParams

    if company is not None:
        try:
            sp = getattr(company, "sectorParams", None)
            if sp is not None:
                return sp
        except Exception:  # noqa: BLE001
            pass
        try:
            sp = getattr(company, "sector", None)
            if sp is not None and hasattr(sp, "discountRate"):
                return sp
        except Exception:  # noqa: BLE001
            pass
    return SectorParams(**_DEFAULT_SECTOR)


def _resolveSeries(company: Any) -> dict | None:
    """Company → finance.timeseries dict (BS/IS/CF). 실패 시 None."""
    if company is None:
        return None
    try:
        fin = getattr(company, "finance", None)
        if fin is not None:
            ts = getattr(fin, "timeseries", None)
            if isinstance(ts, dict) and ts:
                return ts
    except Exception:  # noqa: BLE001
        pass
    return None


def _resolveShares(company: Any) -> int | None:
    """Company → 발행주식수. 여러 attr 후보 순차 시도."""
    if company is None:
        return None
    for attr in ("sharesOutstanding", "shares", "totalShares"):
        try:
            v = getattr(company, attr, None)
            if callable(v):
                v = v()
            if v:
                return int(v)
        except Exception:  # noqa: BLE001
            continue
    return None


def _resolveCurrentPrice(company: Any) -> float | None:
    """Company → 현재 주가. 여러 attr 후보 순차 시도."""
    if company is None:
        return None
    for attr in ("currentPrice", "price"):
        try:
            v = getattr(company, attr, None)
            if callable(v):
                v = v()
            if v:
                return float(v)
        except Exception:  # noqa: BLE001
            continue
    return None


def _scenarioDict(dcf: Any, name: str) -> dict[str, Any]:
    """DCFResult → 시나리오 요약 dict (8 키)."""
    return {
        "scenario": name,
        "discountRate": getattr(dcf, "discountRate", None),
        "growthRateInitial": getattr(dcf, "growthRateInitial", None),
        "terminalGrowth": getattr(dcf, "terminalGrowth", None),
        "enterpriseValue": getattr(dcf, "enterpriseValue", None),
        "equityValue": getattr(dcf, "equityValue", None),
        "perShareValue": getattr(dcf, "perShareValue", None),
        "marginOfSafety": getattr(dcf, "marginOfSafety", None),
    }


def dcfValuationTool(
    stockCode: str = "",
    wacc: float | None = None,
    terminalGrowthRate: float | None = None,
    projectionYears: int = 5,
    scenarios: list[str] | None = None,
) -> ToolResult:
    """단일 종목 DCF 내재가치 — bear/base/bull 3 시나리오.

    Capabilities:
        Damodaran 2-stage DCF (FCF 5 년 명시적 + Gordon terminal) 를 3 시나리오
        (bear/base/bull) 로 계산해 내재가치 밴드 + marginOfSafety 산출. LLM 이
        매번 RunPython 으로 ad-hoc DCF 코드 작성하던 회귀 차단 (token 30% 절감).

    Parameters
    ----------
    stockCode : str
        종목 코드 (6 자리 KR 또는 US ticker). 필수.
    wacc : float | None
        할인율 (%). None 시 sectorParams.discountRate.
    terminalGrowthRate : float | None
        영구성장률 (%). None 시 ``min(sectorGrowth, 3.0)``.
    projectionYears : int
        초기 고성장 구간 (년). 기본 5.
    scenarios : list[str] | None
        ``["bear", "base", "bull"]`` 중 선택. 기본 전체.

    Returns
    -------
    ToolResult
        - data.scenarios : dict[name → 8 키 요약]
        - data.assumptions : waccBase / terminalGrowthRateBase / projectionYears / shares / sectorLabel
        - data.confidence : 30 (dcf method)
        - refs : ``valueRef`` × N + ``tableRef`` (시나리오 매트릭스)

    Raises
    ------
    없음 — 모든 실패 경로는 ``ToolResult(ok=False, error=...)`` 로 반환.
    Company 생성/시계열 추출/DCF 계산 실패는 error 라벨 분기 (missing_stock_code /
    company_not_resolved / series_unavailable / dcf_all_failed).

    Example
    -------
        DCFValuation(stockCode="005930")
        DCFValuation(stockCode="AAPL", wacc=9.0, terminalGrowthRate=2.5)

    Guide
    -----
        Company.finance.timeseries 추출 실패 시 series_unavailable error. 발행주식수
        없으면 perShareValue None — equityValue 만 활용.

    SeeAlso
    -------
        - analysis.valuation.dcf.dcfValuation : 본 도구가 호출하는 본체
        - analysis.forecast._forecastScenario : 동일 패턴 base/bull/bear
        - SensitivityAnalysis tool : WACC × growth grid

    Requires
    --------
        company.finance.timeseries (BS/IS/CF 최소 3 년).

    AIContext
    ---------
        "삼성전자 적정가격", "AAPL 내재가치", "DCF 평가", "공정가치 알려줘" 같은
        질문에 본 도구 호출. wacc / terminalGrowthRate 사용자 명시 시 override.

    LLM Specifications
    ------------------
        AntiPatterns:
            - wacc=0 or terminalGrowthRate ≥ wacc — DCF 가정 위반 (자동 보정되나 신뢰도 0).
            - scenarios=[] — 빈 list 시 base 만 fallback.
        OutputSchema:
            scenarios[name] = {scenario, discountRate, growthRateInitial,
            terminalGrowth, enterpriseValue, equityValue, perShareValue,
            marginOfSafety}.
        Prerequisites:
            DART/EDGAR 사전 다운로드 (자동). finance.timeseries 비어있으면 실패.
        Freshness:
            분기 결산 발표 후 갱신. 연 4 회.
        Dataflow:
            stockCode → Company → series + sectorParams → dcfValuation × 3
            → valueRef × 3 + tableRef.
        TargetMarkets:
            KR (DART) · US (EDGAR). JP (EDINET) 미가용.
    """
    from dartlab.analysis.valuation.dcf import dcfValuation

    if not stockCode:
        return ToolResult(
            False,
            "stockCode 필수 (6 자리 KR 또는 US ticker).",
            error="missing_stock_code",
        )

    company = resolveCompanyOrNone(stockCode)
    if company is None:
        return ToolResult(
            False,
            f"company_not_resolved: {stockCode}",
            error="company_not_resolved",
        )

    series = _resolveSeries(company)
    if not series:
        return ToolResult(
            False,
            f"finance.timeseries 추출 실패: {stockCode}",
            error="series_unavailable",
        )

    sp = _resolveSectorParams(company)
    shares = _resolveShares(company)
    currentPrice = _resolveCurrentPrice(company)

    waccBase = float(wacc) if wacc is not None else float(getattr(sp, "discountRate", 10.0))
    sectorGrowth = float(getattr(sp, "growthRate", 3.0))
    tgBase = float(terminalGrowthRate) if terminalGrowthRate is not None else min(sectorGrowth, 3.0)

    requested = list(scenarios) if scenarios else ["bear", "base", "bull"]
    requested = [s for s in requested if s in ("bear", "base", "bull")] or ["base"]

    scenarioDefs = {
        "bear": (waccBase + 1.0, max(tgBase - 0.5, 0.5)),
        "base": (waccBase, tgBase),
        "bull": (max(waccBase - 1.0, 5.0), tgBase + 0.5),
    }

    results: dict[str, dict[str, Any]] = {}
    warnings_acc: list[str] = []
    for name in ("bear", "base", "bull"):
        if name not in requested:
            continue
        dr, tg = scenarioDefs[name]
        try:
            dcf = dcfValuation(
                series,
                shares=shares,
                sectorParams=sp,
                currentPrice=currentPrice,
                discountRate=dr,
                terminalGrowth=tg,
                projectionYears=projectionYears,
            )
        except Exception as exc:  # noqa: BLE001
            warnings_acc.append(f"{name} scenario 계산 실패: {type(exc).__name__}")
            continue
        results[name] = _scenarioDict(dcf, name)
        warns = getattr(dcf, "warnings", None) or []
        for w in warns:
            warnings_acc.append(f"[{name}] {w}")

    if not results:
        return ToolResult(
            False,
            f"DCF 계산 실패 — 모든 시나리오 오류: {stockCode}",
            error="dcf_all_failed",
            data={"warnings": warnings_acc},
        )

    # core/confidence.py SSOT — "forecast" = 30 (DCF/예측 가정 기반).
    # "dcf" subtype 라벨은 confidenceMethod 에만 노출, 점수는 forecast 사용.
    confidence = baseScore("forecast")
    corpName = str(getattr(company, "corpName", None) or "")
    unit = "KRW" if detectMarket(stockCode) == "KR" else "USD"

    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "corpName": corpName,
        "currentPrice": currentPrice,
        "scenarios": results,
        "assumptions": {
            "waccBase": waccBase,
            "terminalGrowthRateBase": tgBase,
            "projectionYears": projectionYears,
            "shares": shares,
            "sectorLabel": getattr(sp, "label", None),
        },
        "warnings": warnings_acc,
        "confidence": confidence,
        "confidenceMethod": "dcf",
        "unit": unit,
    }

    refs: list[Ref] = []
    for name, s in results.items():
        if s.get("perShareValue") is None:
            continue
        refs.append(
            Ref(
                id=f"dcf:{stockCode}:{name}",
                kind="valueRef",
                title=f"{corpName or stockCode} DCF {name}",
                source="dcfValuation",
                payload={
                    "stockCode": stockCode,
                    "metric": f"intrinsicValue_{name}",
                    "value": s["perShareValue"],
                    "unit": unit,
                    "confidence": confidence,
                    "axis": "valuation",
                    "scenario": name,
                    "discountRate": s["discountRate"],
                    "terminalGrowth": s["terminalGrowth"],
                },
            )
        )

    refs.append(
        Ref(
            id=f"dcf:{stockCode}:matrix",
            kind="tableRef",
            title=f"{corpName or stockCode} DCF 시나리오 매트릭스 ({len(results)} 종)",
            source="dcfValuation",
            payload=payload,
        )
    )

    perBase = results.get("base", {}).get("perShareValue")
    perBear = results.get("bear", {}).get("perShareValue")
    perBull = results.get("bull", {}).get("perShareValue")
    mosBase = results.get("base", {}).get("marginOfSafety")
    parts = [f"{corpName or stockCode} DCF"]
    if perBase is not None:
        parts.append(f"base={perBase:,.0f}")
    if perBear is not None and perBull is not None:
        parts.append(f"range={perBear:,.0f}~{perBull:,.0f}")
    if mosBase is not None:
        parts.append(f"MoS={mosBase:+.1f}%")

    return ToolResult(True, " · ".join(parts), refs=refs, data=payload)


__all__ = ["dcfValuationTool"]
