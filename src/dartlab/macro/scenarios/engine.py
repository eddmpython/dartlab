"""시나리오 실행 + 비교 엔진.

프리셋 → overrides → dartlab.macro("종합") → 결과 비교.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def runScenario(
    name: str,
    *,
    severity: str | None = None,
    market: str = "US",
    compare: bool = True,
) -> dict:
    """시나리오 실행.

    Capabilities:
        프리셋 시나리오 (역사적/DFAST/현대/구조/유형/KR 6 카탈로그) overrides 를
        analyzeSummary 에 적용하고, baseline (현재 상태) 과 score/cycle/crisis/
        sentiment delta 까지 단일 dict 합성.

    Args:
        name: 시나리오 이름 (``"2008 금융위기"``, ``"금리 충격 + 유가 충격"``).
        severity: ``"mild"``/``"moderate"``/``"severe"``/``"extreme"``.
        market: ``"US"`` | ``"KR"``.
        compare: True 면 baseline + delta 포함.

    Returns:
        dict — scenario(analyzeSummary 결과)/baseline/delta/meta(name·description·
        type·severity·transmission·reference·outcome·overrides).

    Example:
        >>> r = runScenario("2008 금융위기", market="US")
        >>> r["delta"]["score"]["change"]
        -3.5

    Guide:
        compare=False 면 baseline 호출 절약 (단순 시나리오 결과만 필요할 때).
        delta.summary 1 줄 인용으로 변화 요약 가능.

    When:
        AI 시나리오 답변 1 차 진입점. CLI macro scenario subcommand.

    How:
        getScenario → overrides → analyzeSummary (시나리오) → 옵션 baseline
        호출 → _computeDelta.

    Requires:
        FRED + KOSIS provider 활성. analyzeSummary 호출 가능.

    Raises:
        ValueError — 시나리오 이름 매칭 실패.

    See Also:
        - compareScenarios : 여러 시나리오 동시 비교
        - getScenario : 단일 룩업
        - analyzeSummary : 적용 대상 매크로 종합

    AIContext:
        delta.summary 1 줄 + meta.outcome 인용으로 한 단락 답변 완성. baseline
        대비 변화량을 절대값 아닌 change 로 표시.

    LLM Specifications:
        AntiPatterns:
            - 시나리오 이름 추측 (listAllScenarios 로 사전 확정)
            - compare=True 2 회 호출 (baseline 재사용 캐싱 책임은 호출자)
            - severity 옵션 누락 (유형별 시나리오는 필수)
        OutputSchema:
            ``{scenario, baseline, delta, meta}``.
        Prerequisites: 매크로 provider 활성.
        Freshness: baseline 은 real-time fetch.
        Dataflow: name → preset 룩업 → overrides 적용 → analyzeSummary →
            baseline + delta.
        TargetMarkets: US (DFAST 풀세트), KR (KR_SCENARIOS).
    """
    from .presets import getScenario

    preset = getScenario(name, severity=severity, market=market)
    if preset is None:
        msg = f"시나리오 '{name}'을 찾을 수 없습니다. dartlab.macro.scenarios.scenario()로 목록을 확인하세요."
        raise ValueError(msg)

    overrides = preset["overrides"]

    # 시나리오 적용 실행
    from dartlab.macro.summary import analyzeSummary

    scenario_result = analyzeSummary(market=market, overrides=overrides)

    result: dict = {
        "scenario": scenario_result,
        "meta": {
            "name": name,
            "description": preset.get("description"),
            "type": preset.get("type"),
            "severity": preset.get("severity"),
            "transmission": preset.get("transmission"),
            "reference": preset.get("reference"),
            "outcome": preset.get("outcome"),
            "overrides": overrides,
        },
    }

    # baseline 비교
    if compare:
        baseline_result = analyzeSummary(market=market)
        result["baseline"] = baseline_result
        result["delta"] = _computeDelta(baseline_result, scenario_result)

    return result


def compareScenarios(
    scenarios: list[str],
    *,
    severity: str | None = None,
    market: str = "US",
) -> dict:
    """여러 시나리오 동시 비교.

    Capabilities:
        시나리오 N 개 동시 실행 → baseline 대비 score/cycle/crisis 비교 테이블.
        포트폴리오 스트레스 테스트 + AI 다중 시나리오 답변 진입점.

    Args:
        scenarios: 시나리오 이름 리스트.
        severity: 모든 시나리오 공통 적용 심각도.
        market: ``"US"`` | ``"KR"``.

    Returns:
        dict — baseline(score/overall)/scenarios(dict per name)/comparison(list:
        scenario/severity/type/score/score_delta/overall/cycle_phase/crisis_zone/
        transmission/outcome).

    Example:
        >>> r = compareScenarios(["2008 금융위기", "금리 충격"])
        >>> r["comparison"][0]["score_delta"]
        -4.2

    Guide:
        score_delta 가 가장 음수인 시나리오 = 최악 케이스. crisis_zone 변화
        동반 시 위기 신호 강함.

    When:
        포트폴리오 스트레스 테스트 + AI "여러 시나리오 비교" 답변.

    How:
        analyzeSummary baseline 1 회 → 각 시나리오 runScenario(compare=False) →
        comparison 테이블 합성.

    Requires:
        매크로 provider 활성. analyzeSummary 1+N 회 호출.

    Raises:
        없음 — 시나리오 매칭 실패는 warning 후 skip.

    See Also:
        - runScenario : 단일 시나리오 실행
        - listAllScenarios : 카탈로그

    AIContext:
        comparison 정렬 후 최악/최선 시나리오 1~2 건 + score_delta 인용으로
        다중 시나리오 답변 완성.

    LLM Specifications:
        AntiPatterns:
            - 시나리오 5+ 개 동시 호출 (FRED rate limit + polars 힙 압박)
            - severity 누락한 채 유형별 시나리오 호출
        OutputSchema:
            ``{baseline, scenarios, comparison}``.
        Prerequisites: 매크로 provider 활성.
        Freshness: baseline real-time.
        Dataflow: baseline → 시나리오 N 회 → comparison.
        TargetMarkets: US, KR.
    """
    from dartlab.macro.summary import analyzeSummary

    baseline = analyzeSummary(market=market)
    results: dict[str, dict] = {}

    for name in scenarios:
        try:
            r = runScenario(name, severity=severity, market=market, compare=False)
            results[name] = r
        except ValueError:
            log.warning("시나리오 '%s' 실행 실패", name)
            continue

    # 비교 테이블
    comparison: list[dict] = []
    baseline_score = baseline.get("score", 0)
    baseline_overall = baseline.get("overall", "neutral")

    for name, r in results.items():
        sc = r["scenario"]
        comparison.append(
            {
                "scenario": name,
                "severity": r["meta"].get("severity", ""),
                "type": r["meta"].get("type", ""),
                "score": sc.get("score", 0),
                "score_delta": round(sc.get("score", 0) - baseline_score, 2),
                "overall": sc.get("overall", ""),
                "cycle_phase": (sc.get("cycle") or {}).get("phase", ""),
                "crisis_zone": ((sc.get("crisis") or {}).get("recessionDashboard") or {}).get("zone", ""),
                "transmission": r["meta"].get("transmission", ""),
                "outcome": r["meta"].get("outcome", ""),
            }
        )

    return {
        "baseline": {
            "score": baseline_score,
            "overall": baseline_overall,
        },
        "scenarios": results,
        "comparison": comparison,
    }


def _computeDelta(baseline: dict, scenario: dict) -> dict:
    """baseline vs scenario 주요 지표 변화량.

    Parameters
    ----------
    baseline : dict
        현재 상태 매크로 종합 결과.
    scenario : dict
        시나리오 적용 매크로 종합 결과.

    Returns
    -------
    dict
        score : dict — 종합 점수 변화
            baseline : float — 기존 점수 (점)
            scenario : float — 시나리오 점수 (점)
            change : float — 변화량 (점)
        overall : dict — 종합 판정 변화
            baseline : str — 기존 판정
            scenario : str — 시나리오 판정
        cycle_phase : dict — 경기 국면 변화
            baseline : str — 기존 국면
            scenario : str — 시나리오 국면
            changed : bool — 변화 여부
        crisis_zone : dict — 위기 수준 변화
            baseline : str — 기존 수준
            scenario : str — 시나리오 수준
            changed : bool — 변화 여부
        fear_greed : dict — 공포·탐욕 지수 변화
            baseline : float | None — 기존 점수 (점)
            scenario : float | None — 시나리오 점수 (점)
            change : float | None — 변화량 (점)
        historical_risk : dict — 역사적 리스크 수준 변화
            baseline : str — 기존 수준
            scenario : str — 시나리오 수준
            changed : bool — 변화 여부
        summary : str — 변화 종합 서술
    """
    delta: dict = {}

    # score
    b_score = baseline.get("score", 0)
    s_score = scenario.get("score", 0)
    delta["score"] = {
        "baseline": round(b_score, 2),
        "scenario": round(s_score, 2),
        "change": round(s_score - b_score, 2),
    }

    # overall
    delta["overall"] = {
        "baseline": baseline.get("overall", ""),
        "scenario": scenario.get("overall", ""),
    }

    # cycle phase
    b_cycle = (baseline.get("cycle") or {}).get("phase", "")
    s_cycle = (scenario.get("cycle") or {}).get("phase", "")
    delta["cycle_phase"] = {
        "baseline": b_cycle,
        "scenario": s_cycle,
        "changed": b_cycle != s_cycle,
    }

    # crisis zone
    b_crisis = ((baseline.get("crisis") or {}).get("recessionDashboard") or {}).get("zone", "")
    s_crisis = ((scenario.get("crisis") or {}).get("recessionDashboard") or {}).get("zone", "")
    delta["crisis_zone"] = {
        "baseline": b_crisis,
        "scenario": s_crisis,
        "changed": b_crisis != s_crisis,
    }

    # sentiment
    b_fg = ((baseline.get("sentiment") or {}).get("fearGreed") or {}).get("score")
    s_fg = ((scenario.get("sentiment") or {}).get("fearGreed") or {}).get("score")
    delta["fear_greed"] = {
        "baseline": round(b_fg, 1) if b_fg is not None else None,
        "scenario": round(s_fg, 1) if s_fg is not None else None,
        "change": round(s_fg - b_fg, 1) if b_fg is not None and s_fg is not None else None,
    }

    # historicalContext risk
    b_risk = ((baseline.get("crisis") or {}).get("historicalContext") or {}).get("riskLevel")
    s_risk = ((scenario.get("crisis") or {}).get("historicalContext") or {}).get("riskLevel")
    delta["historical_risk"] = {
        "baseline": b_risk,
        "scenario": s_risk,
        "changed": b_risk != s_risk,
    }

    # narrative — Phase C, news headline pulse 기여 (scenarios overrides 는 macro 변수만
    # 강제 가능, narrative 는 *과거 데이터 기반*이라 override 불가. baseline narrative 만
    # 활용 + scenario 결과는 similarPastPeriods 인용 — 사용자 의도 매칭).
    b_narr = baseline.get("narrative") or {}
    s_narr = scenario.get("narrative") or {}
    similar = b_narr.get("similarPastPeriods") or []
    delta["narrative_signal"] = {
        "baseline_score": b_narr.get("score"),
        "baseline_label": b_narr.get("label"),
        "regime_shift_delta": (b_narr.get("regimeShift") or {}).get("delta"),
        "scenario_score_from_similar": similar[0].get("score") if similar else None,
        "similar_period_cited": similar[0].get("period") if similar else None,
        "topic_pulse_top1": (b_narr.get("topicPulse") or [{}])[0].get("topic_label")
        if b_narr.get("topicPulse")
        else None,
        # 신규 narrative 축 미실행 또는 scenario narrative 동일 시 baseline 값 그대로 반환.
        "scenario_score": s_narr.get("score"),
    }

    # 종합 서술
    changes: list[str] = []
    if delta["score"]["change"] < -2:
        changes.append(f"종합 점수 {delta['score']['change']:+.1f} (심각한 악화)")
    elif delta["score"]["change"] < -1:
        changes.append(f"종합 점수 {delta['score']['change']:+.1f} (악화)")
    elif delta["score"]["change"] > 1:
        changes.append(f"종합 점수 {delta['score']['change']:+.1f} (개선)")

    if delta["cycle_phase"]["changed"]:
        changes.append(f"경기 국면: {b_cycle} → {s_cycle}")
    if delta["crisis_zone"]["changed"]:
        changes.append(f"위기 수준: {b_crisis} → {s_crisis}")

    delta["summary"] = ". ".join(changes) if changes else "유의미한 변화 없음"

    return delta
