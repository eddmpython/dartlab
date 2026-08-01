"""story 블록 빌더 — credit 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _meta,
    pl,
)

# ── 3-6 신용평가 빌더 ──


def creditMetricsBlock(data: dict) -> list:
    """calcCreditMetrics 결과 → 핵심 지표 시계열 테이블."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "EBITDA/이자": f"{h['ebitdaInterestCoverage']:.1f}x"
                if h.get("ebitdaInterestCoverage") is not None
                else "-",
                "Debt/EBITDA": f"{h['debtToEbitda']:.1f}x" if h.get("debtToEbitda") is not None else "-",
                "FFO/Debt": f"{h['ffoToDebt']:.0f}%" if h.get("ffoToDebt") is not None else "-",
                "부채비율": f"{h['debtRatio']:.0f}%" if h.get("debtRatio") is not None else "-",
                "유동비율": f"{h['currentRatio']:.0f}%" if h.get("currentRatio") is not None else "-",
                "OCF/매출": f"{h['ocfToSales']:.1f}%" if h.get("ocfToSales") is not None else "-",
            }
        )

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("creditMetrics").label,
            level=2,
            helper="ICR>10 AA급 | Debt/EBITDA<1.5 A급 | FFO/Debt>40% 양호",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(rows)))
    return blocks


def creditScoreBlock(data: dict) -> list:
    """calcCreditScore 결과 → 등급 종합 메트릭."""
    if not data:
        return []

    grade = data.get("grade")
    desc = data.get("gradeDescription", "")
    score = data.get("score")
    pd_est = data.get("pdEstimate")
    ecr = data.get("eCR", "?")
    outlook = data.get("outlook", "N/A")
    sector = data.get("sector", "")
    # 부도확률을 못 구했을 때 0 으로 채우면 "부도확률 0.00%" 가 찍힌다. 결측을 하필 가장
    # 안심되는 값으로 바꾸는 셈이고, 이 숫자는 사람이 그대로 믿고 행동하는 자리다.
    # 종합 점수는 반대로 0/100 이 되어 가장 나쁜 회사로 보인다. 둘 다 안 적는 게 맞다.
    pdText = "미산출" if pd_est is None else f"{pd_est:.2f}%"
    scoreText = "미산출" if score is None else f"{score:.1f}/100"
    investment_grade = data.get("investmentGrade")
    if investment_grade is True:
        inv = "투자적격"
    elif investment_grade is False:
        inv = "투기등급"
    else:
        inv = "등급 미판정"
    gradeText = "미산출" if grade is None else f"{grade} ({desc})"

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("creditScore").label,
            level=2,
            helper=f"등급 {gradeText} | {inv} | PD {pdText}",
        )
    )
    blocks.append(
        MetricBlock(
            [
                ("신용등급", gradeText),
                ("종합 점수", scoreText),
                ("부도확률(1Y)", pdText),
                ("현금흐름등급", ecr),
                ("등급 전망", outlook),
                ("업종", sector),
            ]
        )
    )

    # 5축 상세
    axes = data.get("axes", [])
    if axes:
        axisRows = []
        for a in axes:
            axisRows.append(
                {
                    "축": a.get("name", ""),
                    "점수": f"{a['score']:.1f}" if a.get("score") is not None else "-",
                    "비중": f"{a.get('weight', 0)}%",
                    "지표수": str(len(a.get("metrics", []))),
                }
            )
        blocks.append(TableBlock("5축 가중평균 상세", pl.DataFrame(axisRows)))

    return blocks


def creditHistoryBlock(data: dict) -> list:
    """calcCreditHistory 결과 → 등급 시계열."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "등급": h.get("grade", "?"),
                "점수": f"{h['score']:.1f}" if h.get("score") is not None else "-",
                "PD": f"{h['pdEstimate']:.2f}%" if h.get("pdEstimate") is not None else "-",
            }
        )

    stable = "안정적" if data.get("stable") else "변동 있음"

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("creditHistory").label,
            level=2,
            helper=f"등급 안정성: {stable}",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(rows)))
    return blocks


def creditPeerPositionBlock(data: dict) -> list:
    """calcCreditPeerPosition 결과 → 업종 내 위치."""
    if not data:
        return []

    metrics = data.get("metrics", {})
    if not metrics:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("creditPeerPosition").label,
            level=2,
        )
    )
    metricList = []
    for k, v in metrics.items():
        if v is not None:
            metricList.append((k, f"{v:.1f}"))
    if metricList:
        blocks.append(MetricBlock(metricList))
    return blocks


def creditFlagsBlock(data: dict) -> list:
    """calcCreditFlags 결과 → 경고/기회 플래그."""
    if not data:
        return []
    flagList = data.get("flags", [])
    if not flagList:
        return []

    warnings = [f"{f['signal']}: {f['detail']}" for f in flagList if f.get("type") == "warning"]
    opportunities = [f"{f['signal']}: {f['detail']}" for f in flagList if f.get("type") == "opportunity"]

    blocks: list = []
    if warnings:
        blocks.append(FlagBlock(warnings, kind="warning"))
    if opportunities:
        blocks.append(FlagBlock(opportunities, kind="opportunity"))
    return blocks


def creditNarrativeBlock(data: dict) -> list:
    """calcCreditNarrative 결과 → 7축 신용 서사 (severity별)."""
    if not data:
        return []

    axes = data.get("axes", [])
    if not axes:
        return []

    grade = data.get("grade", "?")
    grade_desc = data.get("gradeDescription", "")

    blocks: list = [
        HeadingBlock(
            _meta("creditNarrative").label,
            level=2,
            helper=f"등급 {grade} ({grade_desc}) — 7축 서사",
        ),
    ]

    severity_label = {
        "strong": "🟢 우수",
        "adequate": "🟡 양호",
        "weak": "🟠 주의",
        "critical": "🔴 위험",
    }

    for axis in axes:
        label = severity_label.get(axis.get("severity", ""), "")
        title = f"{axis.get('axisName', '?')} {label}".strip()
        summary = axis.get("summary", "")
        details = axis.get("details", [])

        text = f"**{title}** — {summary}"
        if details:
            details_text = " · ".join(d for d in details[:3] if d)
            if details_text:
                text += f"\n  {details_text}"
        blocks.append(TextBlock(text))

    return blocks
