"""Credit 대표 제품 결과 조립.

기존 dCR 반환을 보존하고 공통 ``product`` 블록만 추가한다. 등급 계산은
여기서 재구현하지 않으며 ``credit.engine.evaluateCompany`` 결과만 소비한다.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from dartlab.synth.rowAccess import strictFloat as _number


def attachCreditProduct(
    company: Any,
    result: dict[str, Any],
    *,
    basePeriod: str | None = None,
) -> dict[str, Any]:
    """기존 dCR 결과에 비교 시나리오와 Lens Product v1을 붙인다."""
    comparison = None
    if result.get("grade"):
        try:
            from dartlab.credit.engine import evaluateCompany

            if result.get("appliedOverrides"):
                comparison = evaluateCompany(company, detail=False, basePeriod=basePeriod)
            else:
                comparison = evaluateCompany(
                    company,
                    detail=False,
                    basePeriod=basePeriod,
                    overrides={"scenarioStress": "moderate"},
                )
        except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError, RuntimeError, OSError):
            comparison = None

    result["stockCode"] = str(getattr(company, "stockCode", "") or getattr(company, "ticker", "") or "unknown")
    result["market"] = str(getattr(company, "market", "") or "unknown").upper()
    result["product"] = buildCreditProduct(company, result, comparison=comparison, basePeriod=basePeriod)
    return result


def blockedCreditResult(
    company: Any,
    *,
    reason: str,
    basePeriod: str | None = None,
) -> dict[str, Any]:
    """등급을 만들 수 없는 공개 호출도 구조화된 blocked 결과로 반환한다."""
    result: dict[str, Any] = {
        "grade": None,
        "score": None,
        "healthScore": None,
        "outlook": "N/A",
        "latestPeriod": basePeriod,
        "axes": [],
        "metricsHistory": [],
        "narratives": {},
        "blockedReason": reason,
        "stockCode": str(getattr(company, "stockCode", "") or getattr(company, "ticker", "") or "unknown"),
        "market": str(getattr(company, "market", "") or "unknown").upper(),
    }
    result["product"] = buildCreditProduct(company, result, comparison=None, basePeriod=basePeriod)
    return result


def buildCreditProduct(
    company: Any,
    result: dict[str, Any],
    *,
    comparison: dict[str, Any] | None,
    basePeriod: str | None = None,
) -> dict[str, Any]:
    """dCR 결과를 공통 Lens Product v1 문법으로 표현한다."""
    from dartlab.synth.lensContract import validateLensProduct

    target = str(getattr(company, "stockCode", "") or getattr(company, "ticker", "") or "unknown")
    market = str(getattr(company, "market", "") or "unknown").upper()
    today = date.today().isoformat()
    axes = result.get("axes") if isinstance(result.get("axes"), list) else []
    validAxes = [row for row in axes if isinstance(row, dict) and _number(row.get("score")) is not None]
    totalWeight = sum(_number(row.get("weight")) or 0.0 for row in axes if isinstance(row, dict))
    validWeight = sum(_number(row.get("weight")) or 0.0 for row in validAxes)
    coverage = round(validWeight / totalWeight * 100, 1) if totalWeight > 0 else 0.0

    gaps: list[dict[str, Any]] = []
    for row in axes:
        if not isinstance(row, dict) or _number(row.get("score")) is not None:
            continue
        name = str(row.get("name") or "unknown")
        gaps.append(
            {
                "id": f"credit.axis.{name}",
                "status": "missing",
                "reason": f"{name} 축을 계산할 근거가 부족합니다.",
                "sourceRef": f"axes.{name}",
            }
        )

    ignored = result.get("ignoredOverrides")
    if isinstance(ignored, dict):
        for key, reason in ignored.items():
            gaps.append(
                {
                    "id": f"credit.override.{key}",
                    "status": "unsupported",
                    "reason": str(reason),
                    "sourceRef": "ignoredOverrides",
                }
            )

    blockedReason = result.get("blockedReason")
    if blockedReason:
        gaps.append(
            {
                "id": "credit.calibration",
                "status": "blocked",
                "reason": str(blockedReason),
                "sourceRef": "blockedReason",
            }
        )

    grade = result.get("grade")
    if not grade or not validAxes:
        status = "blocked"
    elif coverage < 75:
        status = "partial"
    else:
        status = "usable"

    if status == "blocked" and not gaps:
        gaps.append(
            {
                "id": "credit.grade",
                "status": "blocked",
                "reason": "등급을 산출할 유효 신용 축이 없습니다.",
            }
        )

    score = _number(result.get("score"))
    outlook = str(result.get("outlook") or "N/A")
    if status == "blocked":
        conclusion = {
            "label": "등급 산출 불가",
            "summary": str(blockedReason or "유효 신용 근거가 부족해 등급 결론을 차단했습니다."),
        }
        confidenceLevel = "blocked"
    else:
        scenarioNote = " 시나리오 가정이 적용된 결과입니다." if result.get("appliedOverrides") else ""
        conclusion = {
            "label": str(grade),
            "summary": (
                f"dCR 위험점수 {score:.2f}, 전망 {outlook}, 유효 축 가중치 {coverage:.1f}%입니다.{scenarioNote}"
            ),
        }
        confidenceLevel = "high" if coverage >= 90 else "medium" if coverage >= 75 else "low"

    evidence = [
        {
            "id": f"credit.axis.{row.get('name')}",
            "kind": "creditAxis",
            "sourceRef": f"dartlab://credit/{target}/axes/{row.get('name')}",
            "status": "derived",
            "detail": f"위험점수 {float(row['score']):.2f}, 가중치 {row.get('weight')}%",
        }
        for row in validAxes
    ]

    drivers = _drivers(validAxes)
    scenarios = _scenarioRows(result, comparison)
    latestPeriod = str(result.get("latestPeriod") or basePeriod or "") or None
    blockRefs = [key for key in ("grade", "axes", "metricsHistory", "narratives") if key in result]
    falsifiers = _falsifiers(result, drivers, scenarios)
    claims = _creditClaims(
        result,
        evidence,
        falsifiers,
        asOf=today,
        period=latestPeriod,
    )

    product = {
        "schemaVersion": 1,
        "identity": {
            "target": target,
            "market": market,
            "engine": "credit",
            "axis": "등급",
            "version": str(result.get("methodologyVersion") or "1"),
        },
        "time": {
            "asOf": today,
            "dataAsOf": {"latestPeriod": latestPeriod, "retrievedAt": today},
            "period": latestPeriod,
            "knowledgeBoundary": today,
        },
        "status": status,
        "conclusion": conclusion,
        "confidence": {
            "level": confidenceLevel,
            "score": coverage,
            "method": "validAxisWeightCoverage",
        },
        "drivers": drivers,
        "claims": claims,
        "evidence": evidence,
        "assumptions": _assumptionRows(result.get("appliedOverrides")),
        "gaps": gaps,
        "scenarios": scenarios,
        "falsifiers": falsifiers,
        "payload": {
            "blockRefs": blockRefs,
            "gradeHistory": _gradeHistory(company, result),
            "coverage": {
                "validAxes": len(validAxes),
                "totalAxes": len(axes),
                "validWeight": validWeight,
                "totalWeight": totalWeight,
                "weightCoverage": coverage,
            },
            "eCR": result.get("eCR"),
            "pdEstimate": result.get("pdEstimate"),
            "notchAdjustment": result.get("notchAdjustment"),
            "divergenceExplanation": result.get("divergenceExplanation") or [],
        },
    }
    validateLensProduct(product, legacy=result)
    return product


def _drivers(validAxes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(validAxes, key=lambda row: float(row["score"]))
    strengths = ordered[:2]
    weaknesses = list(reversed(ordered[-2:]))
    rows = []
    used: set[str] = set()
    for direction, candidates in (("positive", strengths), ("negative", weaknesses)):
        for row in candidates:
            name = str(row.get("name") or "unknown")
            if name in used:
                continue
            used.add(name)
            rows.append(
                {
                    "id": f"axis.{name}",
                    "label": name,
                    "value": float(row["score"]),
                    "unit": "riskScore",
                    "direction": direction,
                    "weight": row.get("weight"),
                    "contribution": row.get("contribution"),
                    "sourceRef": f"axes.{name}",
                }
            )
    return rows


def _scenarioRows(result: dict[str, Any], comparison: dict[str, Any] | None) -> list[dict[str, Any]]:
    current = {
        "id": "requestedOverride" if result.get("appliedOverrides") else "base",
        "label": "요청 시나리오" if result.get("appliedOverrides") else "기준",
        "grade": result.get("grade"),
        "score": result.get("score"),
        "assumptions": result.get("appliedOverrides") or {},
    }
    if not isinstance(comparison, dict) or not comparison.get("grade"):
        return [current]

    compared = {
        "id": "baseline" if result.get("appliedOverrides") else "moderateStress",
        "label": "기준" if result.get("appliedOverrides") else "중간 하방 스트레스",
        "grade": comparison.get("grade"),
        "score": comparison.get("score"),
        "assumptions": comparison.get("appliedOverrides") or {},
    }
    return [compared, current] if result.get("appliedOverrides") else [current, compared]


def _falsifiers(
    result: dict[str, Any],
    drivers: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "id": "negativeOutlook",
            "condition": "등급 전망이 부정적으로 전환되면 현재 상환능력 결론을 다시 평가합니다.",
            "sourceRef": "outlook",
        }
    ]
    weak = next((row for row in drivers if row.get("direction") == "negative"), None)
    if weak:
        rows.append(
            {
                "id": "weakAxisDeterioration",
                "condition": f"{weak['label']} 위험점수가 현재보다 10점 이상 상승하면 결론을 다시 평가합니다.",
                "sourceRef": str(weak.get("sourceRef")),
            }
        )
    stress = next((row for row in scenarios if row.get("id") == "moderateStress"), None)
    if stress and stress.get("grade") != result.get("grade"):
        rows.append(
            {
                "id": "stressDowngrade",
                "condition": f"중간 하방 스트레스에서 {stress.get('grade')}로 하락하는 경로가 현실화될 때",
                "sourceRef": "scenarios.moderateStress",
            }
        )
    return rows


def _creditClaims(
    result: dict[str, Any],
    evidence: list[dict[str, Any]],
    falsifiers: list[dict[str, Any]],
    *,
    asOf: str,
    period: str | None,
) -> list[dict[str, Any]]:
    narratives = result.get("narratives")
    axes = narratives.get("axes") if isinstance(narratives, dict) else None
    if not isinstance(axes, list):
        return []
    evidenceById = {str(row.get("id")): row for row in evidence if row.get("id")}
    falsifierIds = {str(row.get("id")) for row in falsifiers if row.get("id")}
    if "negativeOutlook" not in falsifierIds:
        return []
    definitions = {
        "채무상환능력": ("credit.debtService", "debtService"),
        "현금흐름": ("credit.cashConversion", "cashConversion"),
        "자본구조": ("credit.capitalStructure", "capitalStructure"),
        "유동성": ("credit.liquidity", "liquidity"),
    }
    directions = {
        "strong": "supportive",
        "adequate": "neutral",
        "weak": "adverse",
        "critical": "adverse",
    }
    claims = []
    for row in axes:
        if not isinstance(row, dict) or row.get("axis") not in definitions:
            continue
        axis = str(row["axis"])
        evidenceId = f"credit.axis.{axis}"
        evidenceRow = evidenceById.get(evidenceId)
        direction = directions.get(str(row.get("severity")))
        if evidenceRow is None or direction is None or not evidenceRow.get("sourceRef"):
            continue
        claimId, comparisonKey = definitions[axis]
        claims.append(
            {
                "id": claimId,
                "label": str(row.get("summary") or axis),
                "comparisonKey": comparisonKey,
                "basis": "creditNarrative",
                "direction": direction,
                "horizon": "latestPeriod",
                "asOf": asOf,
                "dataAsOf": period,
                "period": period,
                "status": "derived",
                "sourceRef": str(evidenceRow["sourceRef"]),
                "evidenceRefs": [evidenceId],
                "falsifierRefs": ["negativeOutlook"],
            }
        )
    return sorted(claims, key=lambda row: row["id"])


def _assumptionRows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    return [{"id": str(key), "value": item, "source": "userOrScenarioOverride"} for key, item in value.items()]


def _gradeHistory(company: Any, result: dict[str, Any]) -> list[dict[str, Any]]:
    history = result.get("metricsHistory")
    if not isinstance(history, list) or not history:
        return []
    try:
        from dartlab.credit.features.sectorThresholds import getThresholds
        from dartlab.credit.scoring.creditScorecard import mapTo20Grade, scoreMetric

        sectorInfo = getattr(company, "sector", None)
        sector = getattr(sectorInfo, "sector", None) if sectorInfo is not None else None
        industryGroup = getattr(sectorInfo, "industryGroup", None) if sectorInfo is not None else None
        thresholds = getThresholds(sector, industryGroup)
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        return []

    rows = []
    metricThresholds = (
        ("ffoToDebt", "ffo_to_debt"),
        ("debtToEbitda", "debt_to_ebitda"),
        ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
        ("debtRatio", "debt_ratio"),
        ("currentRatio", "current_ratio"),
    )
    for periodRow in history:
        if not isinstance(periodRow, dict):
            continue
        scores = []
        for metric, threshold in metricThresholds:
            value = scoreMetric(periodRow.get(metric), thresholds[threshold])
            if value is not None:
                scores.append(value)
        if not scores:
            continue
        periodScore = round(sum(scores) / len(scores), 2)
        grade, _, pdEstimate = mapTo20Grade(periodScore)
        rows.append(
            {
                "period": periodRow.get("period"),
                "score": periodScore,
                "grade": grade,
                "pdEstimate": pdEstimate,
            }
        )
    return rows


__all__ = ["attachCreditProduct", "blockedCreditResult", "buildCreditProduct"]
