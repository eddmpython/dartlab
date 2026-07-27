"""Macro 시나리오 오버레이 — Track D (146 preset × 업종 탄성치 → 종목 손익 추정).

scenario preset 의 macro overrides (금리·환율·CPI 등) + dartlab synth.scenario 의 업종 탄성치
(GDP/FX/마진) 결합으로 종목 단위 거친 임팩트 (매출%, 마진bps, cyclicality) 추정.

신뢰도 35 (scenario method) — assumptions 다중 누적. UI 답변 본문에 [conf:35] 인용 권장.

graph 회귀 가드: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore
from dartlab.core.market import detectMarket

from .companyResolve import resolveCompanyOrNone
from .types import ToolResult

# overrides 키 → 거시 충격 추출 (baseline 대비 변화량).
# 단순 휴리스틱 — preset 의 절대값을 baseline 대비 변화로 해석.
_GDP_PROXY_KEY = "indpro_yoy"  # 산업생산 YoY (%) — GDP shock proxy
_FX_KEY = "usdkrw"  # 원달러
_FX_BASELINE = 1350.0  # 평년 baseline (rough)
_RATE_KEY = "fedfunds"
_RATE_BASELINE_US = 4.5


def _sectorKey(company: Any) -> str | None:
    """Company → WICS/GICS sector key (synth.scenario SECTOR_ELASTICITY 조회용)."""
    if company is None:
        return None
    try:
        ind = company.industry() if hasattr(company, "industry") else None
        if isinstance(ind, dict) and ind.get("industryName"):
            return str(ind["industryName"])
    except Exception:
        pass
    try:
        sec = getattr(company, "sector", None)
        if sec is not None:
            return str(getattr(sec, "industryGroup", None) or getattr(sec, "sector", "") or "")
    except Exception:
        pass
    return None


def _estimateImpact(overrides: dict[str, Any], elasticity: Any) -> dict[str, Any]:
    """overrides + elasticity → revenueImpactPct + marginImpactBps + nimImpactBps 거친 추정."""
    if elasticity is None:
        return {}
    gdpShock = overrides.get(_GDP_PROXY_KEY)
    fx = overrides.get(_FX_KEY)
    rate = overrides.get(_RATE_KEY)
    revenueImpactPct = None
    marginImpactBps = None
    nimImpactBps = None
    if isinstance(gdpShock, (int, float)):
        revenueImpactPct = float(elasticity.revenueToGdp) * float(gdpShock)
        marginImpactBps = float(elasticity.marginToGdp) * float(gdpShock)
    if isinstance(fx, (int, float)) and _FX_BASELINE > 0:
        fxShockPct = (float(fx) - _FX_BASELINE) / _FX_BASELINE * 100.0
        addPct = float(elasticity.revenueToFx) * fxShockPct / 10.0  # revenueToFx 는 10% 약세 기준
        revenueImpactPct = (revenueImpactPct or 0.0) + addPct
    if isinstance(rate, (int, float)) and elasticity.nimToRate:
        rateShockPct = float(rate) - _RATE_BASELINE_US
        nimImpactBps = float(elasticity.nimToRate) * rateShockPct
    out: dict[str, Any] = {}
    if revenueImpactPct is not None:
        out["revenueImpactPct"] = round(revenueImpactPct, 2)
    if marginImpactBps is not None:
        out["marginImpactBps"] = round(marginImpactBps, 1)
    if nimImpactBps is not None:
        out["nimImpactBps"] = round(nimImpactBps, 1)
    return out


def scenarioOverlay(scenarioName: str, stockCode: str = "", severity: str = "", market: str = "") -> ToolResult:
    """preset + 업종 탄성치 → 종목 단위 시나리오 임팩트 추정.

    Parameters
    ----------
    scenarioName : str
        ``"asia_crisis"`` · ``"semiconductor_downturn"`` 등 preset 이름.
    stockCode : str
        종목 코드 (006 자리 KR 또는 ticker US). 없으면 macro overrides 만 반환.
    severity : str
        ``"mild"`` / ``"moderate"`` / ``"severe"`` / ``"extreme"`` (preset 별 지원).
    market : str
        ``"KR"`` / ``"US"``. 빈 문자열이면 stockCode 형식 으로 추론.
    """
    from dartlab.macro.scenarios.presets import getScenario
    from dartlab.synth.scenario import getElasticity

    if not scenarioName:
        return ToolResult(False, "scenarioName 필수 — preset 이름 (예: asia_crisis).", error="missing_scenario")
    inferredMarket = market or detectMarket(stockCode)
    preset = getScenario(scenarioName, severity=severity or None, market=inferredMarket)
    if not preset:
        return ToolResult(False, f"preset 없음: {scenarioName}", error="scenario_not_found")
    overrides = dict(preset.get("overrides") or {})
    if inferredMarket == "KR":
        overrides.update(preset.get("kr_overrides") or {})
    company = resolveCompanyOrNone(stockCode)
    sectorKey = _sectorKey(company) if company is not None else None
    elasticity = getElasticity(sectorKey)
    estimates = _estimateImpact(overrides, elasticity) if company is not None else {}
    confidence = baseScore("scenario")
    payload: dict[str, Any] = {
        "scenarioId": scenarioName,
        "scenarioType": preset.get("type"),
        "severity": severity or preset.get("severity"),
        "description": preset.get("description"),
        "outcome": preset.get("outcome"),
        "period": preset.get("period"),
        "market": inferredMarket,
        "overrides": overrides,
        "sectorKey": sectorKey,
        "elasticity": {
            "revenueToGdp": elasticity.revenueToGdp,
            "revenueToFx": elasticity.revenueToFx,
            "marginToGdp": elasticity.marginToGdp,
            "nimToRate": elasticity.nimToRate,
            "cyclicality": elasticity.cyclicality,
        },
        "estimates": estimates,
        "confidence": confidence,
        "confidenceMethod": "scenario",
    }
    ref = Ref(
        id=f"scenario:{scenarioName}:{stockCode or 'macro'}",
        kind="executionRef",
        title=f"{preset.get('description') or scenarioName}",
        source="scenarioOverlay",
        payload=payload,
    )
    parts = [f"scenario={scenarioName}"]
    if sectorKey:
        parts.append(f"sector={sectorKey}")
    if estimates.get("revenueImpactPct") is not None:
        parts.append(f"매출영향={estimates['revenueImpactPct']:+.1f}%")
    if estimates.get("marginImpactBps") is not None:
        parts.append(f"마진={estimates['marginImpactBps']:+.0f}bps")
    return ToolResult(True, " · ".join(parts), refs=[ref], data=payload)


__all__ = ["scenarioOverlay"]
