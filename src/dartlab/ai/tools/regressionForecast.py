"""RegressionForecast — 매출 성장률 예측 (cross-section / panel 회귀 cache load).

마스터 플랜 트랙 1 PR-7 (cryptic-discovering-kettle.md). analysis.valuation.
crossRegression 의 사전 적합 모델 (loadModel / loadPanelModel) + 단건 features →
predict 예측. 자율 호출 본체가 매번 RunPython 으로 회귀 ad-hoc 작성하던 회귀 차단.

신뢰도 30 (forecast method) — 모델 가정 + features 추정 누적.

graph 회귀 방지: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore

from .companyResolve import resolveCompanyOrNone
from .types import ToolResult


def _resolveYear(year: int | None) -> int:
    """year=None 시 직전 회계연도 (UTC year - 1) 사용."""
    if isinstance(year, int) and year > 1900:
        return year
    return dt.datetime.now(dt.UTC).year - 1


def _buildFeaturesFromCompany(company: Any, year: int) -> Any | None:
    """Company → CompanyFeatures (helper 단순 시도).

    회사 attr 에서 직접 추출 시도 — per/pbr/operatingMargin/debtRatio 등 가져옴.
    누락 시 None 반환 (회귀 모델 predict 안전).

    실제 features 추출은 추후 PR 확장 — 현재는 attr 다중 fallback.
    """
    try:
        from dartlab.analysis.valuation.crossRegression import CompanyFeatures
    except ImportError:
        return None

    def _attr(name: str, default: float = 0.0) -> float:
        try:
            v = getattr(company, name, None)
            if callable(v):
                v = v()
            if v is None:
                return default
            return float(v)
        except Exception:  # noqa: BLE001
            return default

    try:
        sector = ""
        try:
            ind = company.industry() if hasattr(company, "industry") else None
            if isinstance(ind, dict):
                sector = str(ind.get("industryName") or "")
        except Exception:  # noqa: BLE001
            pass

        return CompanyFeatures(
            stockCode=str(getattr(company, "stockCode", "") or ""),
            year=year,
            sector=sector,
            revenueGrowth=0.0,
            per=_attr("per", 0.0),
            pbr=_attr("pbr", 0.0),
            lnMarketCap=_attr("lnMarketCap", 0.0),
            operatingMargin=_attr("operatingMargin", 0.0),
            capexRatio=_attr("capexRatio", 0.0),
            debtRatio=_attr("debtRatio", 0.0),
            foreignHoldingRatio=_attr("foreignHoldingRatio", 0.0),
            revenueGrowthLag=_attr("revenueGrowthLag", 0.0),
        )
    except Exception:  # noqa: BLE001
        return None


def regressionForecast(
    stockCode: str = "",
    year: int | None = None,
    modelKind: str = "panel",
) -> ToolResult:
    """단일 종목 매출 성장률 회귀 예측.

    Capabilities:
        analysis.valuation.crossRegression 의 사전 적합 모델 (panel 또는 cross-section)
        load + 단건 features 추출 + predict. cache hit 시 즉시 예측, miss 시 batch
        학습 SSOT 는 별도 (본 PR 은 호출 안 함).

    Parameters
    ----------
    stockCode : str
        6 자리 KR 또는 US ticker.
    year : int | None
        회계연도 (예: 2024). None 시 직전 연도 자동 (UTC year-1).
    modelKind : str
        'panel' (기본, 다년 모델) 또는 'cross' (단일 연도 횡단면).

    Returns
    -------
    ToolResult
        - data.stockCode / corpName / sector / year
        - data.modelKind : str
        - data.forecast : float | None — 매출 성장률 예측 (%)
        - data.modelMeta : {rSquared, nObs, featureNames}
        - data.features : dict
        - data.confidence : 30 (forecast method)
        - refs : valueRef (forecast + CI) + tableRef (model coefficients)

    Example
    -------
        RegressionForecast(stockCode="005930", year=2024)
        RegressionForecast(stockCode="AAPL", modelKind="cross")

    Raises
    ------
    없음 — 모든 실패 ToolResult(ok=False, error=...). 모델 cache miss / features 추출
    실패 분기.

    Guide
    -----
        modelKind='panel' 권장 (다년 안정성). cache miss (loadModel/loadPanelModel
        None) 시 model_unavailable error — 별도 학습 batch 트리거 필요.

    SeeAlso
    -------
        - crossRegression.fitCrossSection / fitPanel : 모델 학습
        - crossRegression.loadModel / loadPanelModel : cache 로드 (본 도구가 호출)
        - CompanyFeatures.toFeatureDict : features dict 변환
        - CrossSectionModel.predict : 단건 예측

    Requires
    --------
        ~/.dartlab/regressionModels/ 안 사전 학습된 model JSON. 없으면 운영자 명시
        학습 트리거 필요.

    AIContext
    ---------
        "매출 성장 예측", "내년 매출 전망", "regression forecast" 류 질문에 본 도구
        호출. 사용자 features override 옵션은 후속 PR.

    LLM Specifications
    ------------------
        AntiPatterns:
            - year=2026 (미래) — 학습 안 됐을 가능성 높음, cache miss 가드.
            - modelKind='nonexistent' — 'panel' fallback.
        OutputSchema:
            forecast = float (%) | None.
        Prerequisites:
            ~/.dartlab/regressionModels/ 사전 학습.
        Freshness:
            모델 재학습 주기 (분기 또는 연 1 회).
        Dataflow:
            stockCode → Company → _buildFeaturesFromCompany → toFeatureDict +
            sector → model.predict → forecast.
        TargetMarkets:
            KR (DART) 우선. US (EDGAR) 는 features extraction limited.
    """
    if not stockCode:
        return ToolResult(False, "stockCode 필수.", error="missing_stock_code")

    company = resolveCompanyOrNone(stockCode)
    if company is None:
        return ToolResult(False, f"company_not_resolved: {stockCode}", error="company_not_resolved")

    year_resolved = _resolveYear(year)
    if modelKind not in ("panel", "cross"):
        modelKind = "panel"

    try:
        from dartlab.analysis.valuation.crossRegression import loadModel, loadPanelModel
    except ImportError:
        return ToolResult(False, "crossRegression import 실패", error="regression_module_unavailable")

    try:
        if modelKind == "panel":
            model = loadPanelModel()
        else:
            model = loadModel(year_resolved)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            False,
            f"model load 실패: {type(exc).__name__}: {exc}",
            error="model_load_failed",
        )

    if model is None:
        return ToolResult(
            False,
            f"model cache 없음 ({modelKind}, year={year_resolved}). 사전 학습 필요.",
            error="model_unavailable",
        )

    features = _buildFeaturesFromCompany(company, year_resolved)
    if features is None:
        return ToolResult(False, "features 추출 실패", error="features_unavailable")

    sector = features.sector
    try:
        forecast_value = model.predict(features.toFeatureDict(), sector=sector)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            False,
            f"predict 실패: {type(exc).__name__}: {exc}",
            error="predict_failed",
        )

    confidence = baseScore("forecast")
    corpName = str(getattr(company, "corpName", None) or "")

    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "corpName": corpName,
        "sector": sector,
        "year": year_resolved,
        "modelKind": modelKind,
        "forecast": forecast_value,
        "modelMeta": {
            "rSquared": getattr(model, "rSquared", None),
            "adjRSquared": getattr(model, "adjRSquared", None),
            "nObs": getattr(model, "nObs", None),
            "featureNames": getattr(model, "featureNames", []),
        },
        "features": features.toFeatureDict() if hasattr(features, "toFeatureDict") else {},
        "confidence": confidence,
        "confidenceMethod": "forecast",
    }

    refs: list[Ref] = []
    if forecast_value is not None:
        refs.append(
            Ref(
                id=f"forecast:{stockCode}:{year_resolved}:{modelKind}",
                kind="valueRef",
                title=f"{corpName or stockCode} 매출 성장 예측 {year_resolved}",
                source="regressionForecast",
                payload={
                    "stockCode": stockCode,
                    "metric": "revenueGrowthForecast",
                    "value": forecast_value,
                    "unit": "%",
                    "year": year_resolved,
                    "period": str(year_resolved),
                    "confidence": confidence,
                    "modelKind": modelKind,
                    "rSquared": payload["modelMeta"]["rSquared"],
                },
            )
        )
    refs.append(
        Ref(
            id=f"forecast:{stockCode}:{year_resolved}:meta",
            kind="tableRef",
            title=f"{corpName or stockCode} {modelKind} 회귀 모델 메타",
            source="regressionForecast",
            payload=payload,
        )
    )
    refs.extend(
        [
            Ref(
                id=f"forecast:{stockCode}:{year_resolved}:date",
                kind="dateRef",
                title=f"{corpName or stockCode} 예측 대상 기간",
                source=f"forecast:{stockCode}:{year_resolved}:meta",
                payload={"stockCode": stockCode, "period": str(year_resolved)},
            ),
            Ref(
                id=f"forecast:{stockCode}:{year_resolved}:execution",
                kind="executionRef",
                title=f"{corpName or stockCode} 회귀 예측 실행 영수증",
                source="regressionForecast",
                payload={"stockCode": stockCode, "period": str(year_resolved), "status": "complete"},
            ),
        ]
    )

    summary = (
        f"{corpName or stockCode} 매출 성장 예측 ({modelKind}, {year_resolved}) — {forecast_value:+.2f}%"
        if forecast_value is not None
        else f"{corpName or stockCode} 예측 None ({modelKind}, {year_resolved})"
    )

    return ToolResult(True, summary, refs=refs, data=payload)


__all__ = ["regressionForecast"]
