"""story 블록 빌더 — forecast 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _fmtEstimate,
    _meta,
    pl,
)


def proFormaHighlightsBlock(data: dict) -> list:
    """calcProFormaHighlights -> IS 요약 전망 테이블."""
    if not data:
        return []
    years = data.get("years", [])
    if not years:
        return []

    cur = data.get("currency", "KRW")
    blocks: list = [
        HeadingBlock(
            _meta("proFormaHighlights").label,
            level=2,
            helper="매출 성장 경로에 따른 IS/CF 핵심 전망",
        ),
    ]

    # WACC + 성장률
    metrics = []
    if data.get("wacc") is not None:
        metrics.append(("WACC", f"{data['wacc']:.1f}%"))
    grPath = data.get("revenueGrowthPath", [])
    if grPath:
        metrics.append(("성장률 경로", " -> ".join(f"{g:+.1f}%" for g in grPath)))
    if metrics:
        blocks.append(MetricBlock(metrics))

    # 전망 테이블
    rows = []
    for yr in years:
        rows.append(
            {
                "연차": f"+{yr['yearOffset']}년",
                "매출": _fmtEstimate(yr.get("revenue"), cur),
                "영업이익": _fmtEstimate(yr.get("operatingIncome"), cur),
                "순이익": _fmtEstimate(yr.get("netIncome"), cur),
                "FCF": _fmtEstimate(yr.get("fcf"), cur),
            }
        )
    blocks.append(TableBlock("[추정] Pro-Forma IS 요약", pl.DataFrame(rows)))

    for w in data.get("warnings", []):
        blocks.append(TextBlock(f"-- {w}", style="dim"))
    return blocks


def scenarioImpactBlock(data: dict) -> list:
    """calcScenarioImpact -> 매크로 시나리오 비교 그리드."""
    if not data:
        return []
    scenarios = data.get("scenarios", {})
    if not scenarios:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("scenarioImpact").label,
            level=2,
            helper="거시경제 시나리오별 매출/마진 영향 비교",
        ),
    ]

    rows = []
    for name, sc in scenarios.items():
        rows.append(
            {
                "시나리오": sc.get("label", name),
                "매출변화": (f"{sc['revenueChangePct']:+.1f}%" if sc.get("revenueChangePct") is not None else "-"),
                "마진변화": (f"{sc['marginChangeBps']:+.0f}bps" if sc.get("marginChangeBps") is not None else "-"),
            }
        )
    blocks.append(TableBlock("[추정] 매크로 시나리오 영향", pl.DataFrame(rows)))
    return blocks


def forecastMethodologyBlock(data: dict) -> list:
    """calcForecastMethodology -> 소스 가중치 + 가정."""
    if not data:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("forecastMethodology").label,
            level=2,
            helper="예측 방법론 투명성 공개",
        ),
    ]

    # 소스 가중치
    weights = data.get("sourceWeights", {})
    if weights:
        metrics = [(src, f"{w:.0%}") for src, w in weights.items()]
        blocks.append(MetricBlock(metrics))

    # 가정
    assumptions = data.get("assumptions", [])
    if assumptions:
        for a in assumptions:
            blocks.append(TextBlock(f"- {a}", style="dim"))

    # 경고
    for w in data.get("warnings", []):
        blocks.append(TextBlock(f"-- {w}", style="dim"))

    return blocks


def forecastFlagsBlock(data: dict) -> list:
    """calcForecastFlags -> FlagBlock."""
    if not data:
        return []
    flags = data.get("flags", [])
    if not flags:
        return []
    messages = [msg for _, msg in flags]
    return [FlagBlock(messages, kind="warning")]


def creditScenarioBlock(base: dict | None, scenario: dict | None, overrides: dict | None) -> list:
    """base vs 시나리오 credit 등급 비교 블록.

    Parameters
    ----------
    base : dict
        calcCreditScore(company) 기본 결과.
    scenario : dict
        calcCreditScore(company, overrides=overrides) 시나리오 결과.
    overrides : dict
        적용된 시나리오 가정.

    Returns
    -------
    list[Block]
        HeadingBlock + MetricBlock(base/scenario 비교) + TextBlock(해석).
    """
    if not base or not scenario:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("creditScenario").label,
            level=2,
            helper="시나리오별 신용등급 변화 — 부채비율/ICR 가정 교체 시 등급 영향",
        )
    ]

    base_grade = base.get("grade", "-")
    base_score = base.get("score")
    sc_grade = scenario.get("grade", "-")
    sc_score = scenario.get("score")

    metrics: list[tuple[str, str]] = [
        ("기본 등급", f"{base_grade} (점수 {base_score:.1f})" if base_score is not None else str(base_grade)),
        (
            "시나리오 등급",
            f"{sc_grade} (점수 {sc_score:.1f})" if sc_score is not None else str(sc_grade),
        ),
    ]
    if overrides:
        for k, v in overrides.items():
            metrics.append((f"가정: {k}", str(v)))
    blocks.append(MetricBlock(metrics))

    if base_score is None or sc_score is None:
        blocks.append(TextBlock("점수 근거가 없어 시나리오 등급 차이를 계산하지 않았습니다.", style="dim"))
        return blocks

    diff = sc_score - base_score
    if abs(diff) < 0.3:
        interpretation = "등급 변화 미미 — 해당 시나리오에 대한 내성이 강함."
    elif diff < 0:
        interpretation = f"등급 {abs(diff):.1f}점 하락 — 해당 시나리오에 취약."
    else:
        interpretation = f"등급 {diff:.1f}점 상승 — 해당 시나리오에서 오히려 개선."
    blocks.append(TextBlock(interpretation))

    return blocks
