"""Engine 공통 후처리 - CHS/Notch/divergence/TS smoothing/OFS blending.

engine.py 분리: 시계열 안정화·OFS 블렌딩·후처리·출력 정규화.
"""

from __future__ import annotations

from dartlab.credit._engineCHS import _calcCHSAdjustment
from dartlab.credit._engineConfig import _CONFIG
from dartlab.credit._engineNotch import _calcNotchAdjustment
from dartlab.credit.scoring.creditScorecard import gradeCategory, mapTo20Grade

_CREDIT_SCORE_LEGEND = (
    "score 는 위험 점수 (0=최우량, 100=최위험) 입니다. "
    "metric 의 실제 측정값은 'value' 필드를 보세요. "
    "예: Debt/EBITDA value=0.55배 (실측), score=1.65 (위험점수, 거의 AAA)."
)


def _explainDivergence(
    grade: str, score: float, axes: list, latest: dict, chsResult: dict, captive: bool, holding: bool
) -> list[str]:
    """등급 결정 근거 + 신평사 등급과의 괴리 원인 자동 설명."""
    explanations: list[str] = []

    validAxes = [a for a in axes if a.get("score") is not None]
    if validAxes:
        worst = max(validAxes, key=lambda a: a["score"])
        if worst["score"] > 30:
            explanations.append(f"{worst['name']} 축이 {worst['score']:.0f}점으로 등급 하방 압력")

    fcf = latest.get("fcf")
    ocf = latest.get("ocf")
    if fcf is not None and fcf < 0:
        if ocf is not None and ocf > 0:
            explanations.append("FCF 음수(OCF 양수) - 대규모 투자(CAPEX) 사이클 중. 투자와 부실을 정량으로 구분 불가")
        else:
            explanations.append("FCF·OCF 모두 음수 - 현금흐름 악화 신호")

    if chsResult and chsResult.get("adjustment", 0) > 1:
        explanations.append(
            f"주가 기반 CHS 모델이 +{chsResult['adjustment']:.1f}점 하향 (PD {chsResult['chsPd']:.2%}). "
            "최근 주가 하락이 반영된 결과"
        )

    de = latest.get("debtToEbitda") or 0
    if de > 10:
        explanations.append(f"D/EBITDA {de:.1f}x - 자본집약 업종 구조적 특성 (CAPEX/리스 부채)")

    if captive:
        explanations.append("캡티브 금융자회사 연결 - 연결 차입금에 금융자회사 대출 원금 포함")
    if holding:
        explanations.append("지주사 연결 구조 - 자회사 부채가 연결 레버리지에 반영")

    explanations.append("dartlab dCR은 공시 정량 데이터 기반. 시장 지위, 경영진, 그룹 지원 등 정성 요소는 미반영")

    return explanations


def _applyPostAdjustments(company, overall, latest, metrics, axes, captive, holding, sepMetrics):
    """CHS + Notch + divergence - Track A/B 공통 후처리."""
    from dartlab.credit.scoring.creditScorecard import estimatePD, notchGrade
    from dartlab.credit.scoring.gradeTable import gradeRank

    chsResult = _calcCHSAdjustment(company, overall)
    if chsResult.get("status") == "ok":
        overall = chsResult["adjustedScore"]

    grade, gradeDesc, pdEstimate = mapTo20Grade(overall)

    notchAdj = _calcNotchAdjustment(company, grade, overall, latest, metrics, holding, captive, sepMetrics)
    if notchAdj["totalNotch"] != 0:
        adjustedGrade = notchGrade(grade, -notchAdj["totalNotch"])
        gateGrade, _, _ = mapTo20Grade(_CONFIG["notch_gate_score"])
        adjustedRank = gradeRank(adjustedGrade)
        gateRank = gradeRank(gateGrade)
        if adjustedRank is not None and gateRank is not None and adjustedRank < gateRank:
            adjustedGrade = gateGrade
            notchAdj["monotonicGate"] = gateGrade
        grade = adjustedGrade
        pdEstimate = estimatePD(grade)
        gradeDesc = gradeCategory(grade) + " (notch 조정)"

    divExpl = _explainDivergence(grade, overall, axes, latest, chsResult, captive, holding)

    return grade, gradeDesc, pdEstimate, overall, chsResult, notchAdj, divExpl


def _applyTimeSeriesSmoothing(currentScore: float, historicalScores: list[float]) -> float:
    """3개년 가중이동평균 - _CONFIG["ts_weights"] 사용."""
    w = _CONFIG["ts_weights"]
    if len(historicalScores) >= 2:
        overall = currentScore * w[0] + historicalScores[0] * w[1] + historicalScores[1] * w[2]
    elif len(historicalScores) == 1:
        overall = currentScore * 0.70 + historicalScores[0] * 0.30
    else:
        overall = currentScore
    return round(overall, 2)


def _blendOFS(consolidated: float | None, separate: float | None) -> float | None:
    """연결/별도 축 점수를 동적 블렌딩.

    별도가 consolidated보다 ofs_advantage_threshold점+ 양호하면 별도 비중 상향.
    """
    if consolidated is None or separate is None:
        return consolidated
    adv = _CONFIG["ofs_advantage_threshold"]
    if separate < consolidated - adv:
        w_sep = _CONFIG["ofs_strong_weight"]
    else:
        w_sep = _CONFIG["ofs_default_weight"]
    return round(consolidated * (1 - w_sep) + separate * w_sep, 2)


def _normalizeMetricsForOutput(metricItems: list) -> list[dict]:
    """축의 metric 항목을 출력용 dict 로 정규화."""
    out: list[dict] = []
    for item in metricItems:
        if isinstance(item, dict):
            entry = {"name": item.get("name", "")}
            if "value" in item:
                entry["value"] = item.get("value")
            entry["score"] = item.get("score")
            if entry.get("value") is None and entry["score"] is None:
                continue
            out.append(entry)
        else:
            name, score = item
            if score is None:
                continue
            out.append({"name": name, "score": score})
    return out
