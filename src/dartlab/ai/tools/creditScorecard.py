"""CreditScorecard — dCR + 1Y PD + 7 축 신용 분석 (credit.engine.evaluateCompany wrap).

마스터 플랜 트랙 1 PR-6 (cryptic-discovering-kettle.md). credit.engine 의 결정적 7 축
신용 평가 (채무상환능력/자본구조/유동성/현금흐름/사업안정성/재무신뢰성/공시리스크) 를
한 도구 호출로 답변. RunPython 으로 ad-hoc credit 계산 우회 회귀 차단.

신뢰도 80 (ratio method) — 결정적 비율 계산.

graph 회귀 방지: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore
from dartlab.core.market import detectMarket

from .companyResolve import resolveCompanyOrNone
from .types import ToolResult


def _compileScorecardLayout(result: dict[str, Any]) -> dict[str, Any]:
    """evaluateCompany 결과 → UI 7 축 렌더 spec.

    각 축마다 axis name + 점수 + 주요 metric subset. axes list 가 없으면 빈 dict.
    """
    axes = result.get("axes") or []
    sections: list[dict[str, Any]] = []
    for axis in axes:
        if not isinstance(axis, dict):
            continue
        sections.append(
            {
                "axis": axis.get("name") or axis.get("axisName") or "",
                "score": axis.get("score"),
                "weight": axis.get("weight"),
                "metricCount": len(axis.get("metrics") or []),
                "narrative": axis.get("narrative") or axis.get("summary"),
            }
        )
    return {
        "headline": {
            "grade": result.get("grade"),
            "score": result.get("score"),
            "healthScore": result.get("healthScore"),
            "pdEstimate": result.get("pdEstimate"),
            "outlook": result.get("outlook"),
            "eCR": result.get("eCR"),
            "investmentGrade": result.get("investmentGrade"),
        },
        "sections": sections,
        "adjustments": {
            "chs": result.get("chsAdjustment"),
            "notch": result.get("notchAdjustment"),
        },
    }


def creditScorecard(
    stockCode: str = "",
    basePeriod: str | None = None,
    includeFactors: bool = False,
) -> ToolResult:
    """단일 종목 dCR + 7 축 신용 분석.

    Capabilities:
        credit.engine.evaluateCompany(detail=True) wrap. 비금융은 dCR 등급 (20 단계 AAA~D) +
        1Y PD + 7 축 점수 + 전망. 금융은 유형별 calibration 전 회계 프록시 진단과
        비발행 사유를 반환한다. includeFactors=True 시 Altman 적용성 점수와 Beneish 비발행 상태를 동행한다.

    Parameters
    ----------
    stockCode : str
        6 자리 KR 또는 US ticker. 필수.
    basePeriod : str | None
        평가 기준 분기 ('2024Q4'/'2023' 등). None 시 최신.
    includeFactors : bool
        Altman/Beneish factor 상태 동행 여부 (기본 False — 호출 비용 절감).

    Returns
    -------
    ToolResult
        - data.headline : {grade, score, healthScore, pdEstimate, outlook, eCR, investmentGrade}
        - data.sections : 7 축 list (axis, score, weight, metricCount, narrative)
        - data.adjustments : {chs, notch}
        - data.factors? : {altman, beneish} (includeFactors=True 만)
        - data.confidence : 80 (ratio method)
        - refs : valueRef (grade) + tableRef (7 axes) + valueRef (factors optional)

    Example
    -------
        CreditScorecard(stockCode="005930")
        CreditScorecard(stockCode="000660", basePeriod="2024Q3", includeFactors=True)

    Raises
    ------
    없음 — 모든 실패 ToolResult(ok=False, error=...). Company 미해결 / evaluateCompany None
    / 평가 실패 분기.

    Guide
    -----
        detail=True 권장 (metricsHistory 동반). 7 축 narrative 가 답변 본문 인용에 유용.
        eCR (현금흐름 등급) 은 Track B 금융사 None 가능.

    SeeAlso
    -------
        - credit.engine.evaluateCompany : 본 도구가 호출
        - quant.alphas.altman.calcAltmanFactor : 적용 가능한 단일 모형 factor ranking
        - quant.alphas.beneish.calcBeneishFactor : canonical 입력 비발행 상태
        - DCFValuation : 가치평가

    Requires
    --------
        DART/EDGAR 사전 다운로드. credit.scoring.metrics.calcAllMetrics 정상 동작.

    AIContext
    ---------
        "신용등급", "회사채 등급", "재무 안정성", "AAA 인가" 류 질문에 본 도구 호출.
        includeFactors True 면 Altman 방법론/coverage와 Beneish available 상태 동행.

    LLM Specifications
    ------------------
        AntiPatterns:
            - basePeriod='2023-01' — 분기 단위 ('2023Q1') 또는 연도 ('2023').
            - includeFactors=True 무분별 사용 — 비용 증가, "분식회계/distress" 의도 있을 때만.
        OutputSchema:
            headline 7 키 + sections 7 축 + adjustments + (factors optional).
        Prerequisites:
            DART/EDGAR 사전 다운로드.
        Freshness:
            분기 결산 발표 후 갱신.
        Dataflow:
            stockCode → Company → evaluateCompany(detail=True) → 7 축 분해 +
            (옵션) Altman/Beneish factor → refs.
        TargetMarkets:
            KR (DART) · US (EDGAR).
    """
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

    try:
        from dartlab.credit.engine import evaluateCompany
    except ImportError:
        return ToolResult(
            False,
            "dartlab.credit.engine 모듈 import 실패",
            error="credit_module_unavailable",
        )

    try:
        result = evaluateCompany(company, detail=True, basePeriod=basePeriod)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(
            False,
            f"evaluateCompany 실패: {type(exc).__name__}: {exc}",
            error="evaluate_failed",
        )

    if not result:
        return ToolResult(
            False,
            f"신용 평가 결과 비어있음 — 데이터 부족 ({stockCode})",
            error="empty_evaluation",
        )

    layout = _compileScorecardLayout(result)
    gradePublished = layout["headline"].get("grade") is not None
    confidence = baseScore("ratio") if gradePublished else 0
    corpName = str(getattr(company, "corpName", None) or "")

    factor_data: dict[str, Any] | None = None
    if includeFactors:
        factor_data = {}
        if basePeriod is not None:
            # 횡단 factor는 아직 fiscal/as-of 조회를 지원하지 않는다. 역사적 scorecard에
            # 최신 점수를 섞으면 period mismatch이므로 명시적으로 비발행한다.
            factor_data["status"] = "unavailable"
            factor_data["reasonCode"] = "historical_factor_asof_unsupported"
            factor_data["basePeriod"] = basePeriod
        else:
            market = detectMarket(stockCode)
            try:
                from dartlab.quant.alphas.altman import calcAltmanFactor

                factor_data["altman"] = calcAltmanFactor(market=market, variant="auto", stockCode=stockCode)
            except Exception as exc:  # noqa: BLE001
                factor_data["altman"] = {"error": f"{type(exc).__name__}: {exc}"}
            try:
                from dartlab.quant.alphas.beneish import calcBeneishFactor

                factor_data["beneish"] = calcBeneishFactor(market=market, stockCode=stockCode)
            except Exception as exc:  # noqa: BLE001
                factor_data["beneish"] = {"error": f"{type(exc).__name__}: {exc}"}

    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "corpName": corpName,
        "headline": layout["headline"],
        "sections": layout["sections"],
        "adjustments": layout["adjustments"],
        "confidence": confidence,
        "confidenceMethod": "ratio" if gradePublished else "blocked",
        "basePeriod": basePeriod,
        "assessmentStatus": result.get("assessmentStatus") or ("usable" if gradePublished else "blocked"),
        "blockedReason": result.get("blockedReason"),
        "coverage": result.get("coverage"),
        "auditOpinionEvidence": result.get("auditOpinionEvidence"),
    }
    if factor_data is not None:
        payload["factors"] = factor_data

    refs: list[Ref] = []
    if layout["headline"].get("grade") is not None:
        refs.append(
            Ref(
                id=f"credit:{stockCode}:grade",
                kind="valueRef",
                title=f"{corpName or stockCode} dCR",
                source="creditScorecard",
                payload={
                    "stockCode": stockCode,
                    "metric": "creditGrade",
                    "value": layout["headline"]["grade"],
                    "axis": "credit",
                    "confidence": confidence,
                    "pdEstimate": layout["headline"].get("pdEstimate"),
                    "outlook": layout["headline"].get("outlook"),
                },
            )
        )
    refs.append(
        Ref(
            id=f"credit:{stockCode}:axes",
            kind="tableRef",
            title=f"{corpName or stockCode} " + ("신용 7 축" if gradePublished else "신용 진단"),
            source="creditScorecard",
            payload=payload,
        )
    )

    headline = layout["headline"]
    parts = [f"{corpName or stockCode} 신용"]
    if not gradePublished:
        parts.append("등급·PD 비발행")
    if headline.get("grade"):
        parts.append(f"grade={headline['grade']}")
    if headline.get("pdEstimate") is not None:
        parts.append(f"PD={headline['pdEstimate']:.2f}%")
    if headline.get("outlook") and headline.get("outlook") != "N/A":
        parts.append(f"전망={headline['outlook']}")
    summary = " · ".join(parts)

    return ToolResult(True, summary, refs=refs, data=payload)


__all__ = ["creditScorecard"]
