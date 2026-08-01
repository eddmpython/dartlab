"""story 블록 빌더 — governance 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _meta,
    _tupleFlags,
    pl,
)

# ── 5-1 지배구조 ──


def ownershipTrendBlock(data: dict) -> list:
    """calcOwnershipTrend 결과 -> 지분 추이 테이블 + 주주 구성."""
    if not data:
        return []
    blocks: list = []

    history = data.get("history", [])
    if history:
        rows = []
        for h in history:
            row: dict = {"연도": h["year"]}
            row["지분율(%)"] = h["ratio"]
            row["변동(%p)"] = h.get("change")
            rows.append(row)
        blocks.append(
            HeadingBlock(
                _meta("ownershipTrend").label,
                level=2,
                helper="연도별 최대주주 지분율 추이",
            )
        )
        blocks.append(TableBlock("", pl.DataFrame(rows)))

    holders = data.get("latestHolders", [])
    if holders:
        hRows = []
        for h in holders[:5]:
            hRows.append(
                {
                    "성명": h.get("name", ""),
                    "관계": h.get("relate", ""),
                    "지분율(%)": h.get("ratio"),
                }
            )
        blocks.append(TableBlock("최근 주요 주주", pl.DataFrame(hRows)))

    return blocks


def boardCompositionBlock(data: dict) -> list:
    """calcBoardComposition 결과 -> 이사회 구성 메트릭."""
    if not data:
        return []
    metrics = [
        ("전체 임원", f"{data['totalCount']}명"),
        ("사내이사", f"{data['registeredCount']}명"),
        ("사외이사", f"{data['outsideCount']}명"),
    ]
    outsideRatio = data.get("outsideRatio")
    if outsideRatio is not None:
        metrics.append(("사외이사비율", f"{outsideRatio:.1f}%"))
    return [
        HeadingBlock(
            _meta("boardComposition").label,
            level=2,
            helper="사외이사비율로 이사회 독립성을 판단한다",
        ),
        MetricBlock(metrics),
    ]


def auditOpinionTrendBlock(data: dict) -> list:
    """calcAuditOpinionTrend 결과 -> 감사의견 시계열."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []
    rows = []
    for h in history:
        opinion = h.get("opinion")
        if opinion is None:
            opinion = "판정불가" if h.get("status") == "ambiguous" else "자료부족"
        row: dict = {"연도": h["year"], "감사의견": opinion}
        auditor = h.get("auditor", "")
        if auditor:
            row["감사인"] = auditor
        if h.get("auditorChanged"):
            row["변경"] = "Y"
        rows.append(row)
    return [
        HeadingBlock(
            _meta("auditOpinionTrend").label,
            level=2,
            helper="감사의견과 감사인 변경을 추적한다",
        ),
        TableBlock("", pl.DataFrame(rows)),
    ]


def governanceFlagsBlock(flags: list[tuple[str, str]]) -> list:
    """calcGovernanceFlags 결과 -> FlagBlock."""
    return _tupleFlags(flags)


def executivePayDivergenceBlock(data: dict | None) -> list:
    """임원보수 5Y CAGR vs 매출/순이익 CAGR 괴리 시각화."""
    if not data:
        return []

    cagr = data.get("cagr", {}) or {}
    divergence = data.get("divergence")

    metrics: list[tuple[str, str]] = []
    if cagr.get("execPay") is not None:
        metrics.append(("임원보수 5Y CAGR", f"{cagr['execPay']:+.1f}%"))
    if cagr.get("revenue") is not None:
        metrics.append(("매출 5Y CAGR", f"{cagr['revenue']:+.1f}%"))
    if cagr.get("netIncome") is not None:
        metrics.append(("순이익 5Y CAGR", f"{cagr['netIncome']:+.1f}%"))
    if divergence is not None:
        verdict = "주의 (보수↑ > 매출↑)" if divergence > 5 else "정렬" if abs(divergence) <= 5 else "억제"
        metrics.append(("괴리 (보수 - 매출)", f"{divergence:+.1f}%p ({verdict})"))

    if not metrics:
        return []

    return [
        HeadingBlock(
            _meta("executivePayDivergence").label,
            level=2,
            helper="보수 증가율이 매출/순이익 증가율을 크게 상회하면 대리인 비용 신호",
        ),
        MetricBlock(metrics),
    ]


def independentDirectorQualityBlock(data: dict | None) -> list:
    """외부이사 독립성 — 구성 + 독립성 플래그."""
    if not data:
        return []

    latest = data.get("latest", {}) or {}
    flags = data.get("flags", []) or []

    metrics: list[tuple[str, str]] = []
    if latest.get("total"):
        metrics.append(("전체 임원", f"{latest['total']}명"))
    if latest.get("outside") is not None:
        metrics.append(("외부이사", f"{latest['outside']}명"))
    if latest.get("ratio") is not None:
        metrics.append(("외부이사 비율", f"{latest['ratio']:.0f}%"))

    if not metrics and not flags:
        return []

    blocks: list = [
        HeadingBlock(
            _meta("independentDirectorQuality").label,
            level=2,
            helper="외부이사 비율 33% 이상 = 독립성 기준. 25% 미만 = 취약.",
        ),
    ]
    if metrics:
        blocks.append(MetricBlock(metrics))
    if flags:
        blocks.append(FlagBlock("warning", "\n".join(flags)))
    return blocks


# ── 5-2 공시변화 ──


def disclosureChangeSummaryBlock(data: dict) -> list:
    """calcDisclosureChangeSummary 결과 -> 요약 메트릭 + 상위 변화 테이블."""
    if not data:
        return []
    blocks: list = []

    metrics = [
        ("변화 건수", f"{data['totalChanges']}건"),
        ("변화 topic", f"{data['changedTopics']}/{data['totalTopics']}"),
        ("무변화 topic", f"{data['unchangedTopics']}"),
    ]
    blocks.append(
        HeadingBlock(
            _meta("disclosureChangeSummary").label,
            level=2,
            helper="전체 topic 변화 현황",
        )
    )
    blocks.append(MetricBlock(metrics))

    topChanged = data.get("topChanged", [])
    if topChanged:
        rows = [
            {"topic": t["topic"], "변화횟수": t["changedCount"], "변화율": f"{t['changeRate']:.0%}"}
            for t in topChanged[:5]
        ]
        blocks.append(TableBlock("변화율 상위 topic", pl.DataFrame(rows)))

    return blocks


def keyTopicChangesBlock(data: dict) -> list:
    """calcKeyTopicChanges 결과 -> 핵심 topic 변화 테이블."""
    if not data:
        return []
    keyTopics = data.get("keyTopics", [])
    if not keyTopics:
        return []
    rows = [
        {
            "topic": kt["topic"],
            "기간수": kt["totalPeriods"],
            "변화": kt["changedCount"],
            "변화율": f"{kt['changeRate']:.0%}",
        }
        for kt in keyTopics
    ]
    return [
        HeadingBlock(
            _meta("keyTopicChanges").label,
            level=2,
            helper="핵심 공시 topic의 변화 이력",
        ),
        TableBlock("", pl.DataFrame(rows)),
    ]


def changeIntensityBlock(data: dict) -> list:
    """calcChangeIntensity 결과 -> 변화 크기 테이블."""
    if not data:
        return []
    topByDelta = data.get("topByDelta", [])
    if not topByDelta:
        return []
    rows = [{"topic": t["topic"], "변화량(bytes)": t["totalDeltaBytes"]} for t in topByDelta[:5]]
    return [
        HeadingBlock(
            _meta("changeIntensity").label,
            level=2,
            helper="바이트 기준 변화량 상위 topic",
        ),
        TableBlock("", pl.DataFrame(rows)),
    ]


def disclosureDeltaFlagsBlock(flags: list[tuple[str, str]]) -> list:
    """calcDisclosureDeltaFlags 결과 -> FlagBlock."""
    return _tupleFlags(flags)


def creditAuditBlock(data: dict) -> list:
    """calcCreditAudit 결과 → 외부 신평사 대조."""
    if not data:
        return []

    external = data.get("externalGrades", {})
    notch_diffs = data.get("notchDifferences", {})
    avg_diff = data.get("avgNotchDiff", 0.0)
    agreements = data.get("agreements", [])
    disagreements = data.get("disagreements", [])

    if not external:
        # 외부 등급 데이터 없으면 블록 생략
        return []

    dcr_grade = data.get("dcrGrade", "?")

    blocks: list = [
        HeadingBlock(
            _meta("creditAudit").label,
            level=2,
            helper=f"dCR {dcr_grade} vs 신평사 평균 notch 차이 {avg_diff:+.1f}",
        ),
    ]

    # 외부 등급 비교 테이블
    rows = []
    for agency, grade in external.items():
        diff = notch_diffs.get(agency, 0)
        rows.append(
            {
                "신평사": agency,
                "등급": grade,
                "notch 차이": f"{diff:+d}" if diff != 99 else "비교불가",
            }
        )
    if rows:
        blocks.append(TableBlock("외부 신평사 대조", pl.DataFrame(rows)))

    # 동의/비동의 근거
    if agreements:
        blocks.append(TextBlock("**동의 근거**:\n" + "\n".join(f"- {a}" for a in agreements[:3])))
    if disagreements:
        blocks.append(TextBlock("**비동의 근거**:\n" + "\n".join(f"- {d}" for d in disagreements[:3])))

    return blocks
