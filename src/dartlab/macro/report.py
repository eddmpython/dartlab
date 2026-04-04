"""macro 경제분석 보고서 — 3막 서사 체계.

review의 Block/Section/Review 시스템을 재사용하여
macro 엔진 출력을 구조화된 보고서로 변환한다.

사용:
    dartlab.macro.report()              # Rich 터미널
    dartlab.macro.report(fmt="html")    # HTML
    dartlab.macro.report(fmt="markdown") # 마크다운
    dartlab.macro.report(market="KR")   # 한국 경제
"""

from __future__ import annotations

from dartlab.review.blocks import TextBlock
from dartlab.review.section import Section

from .mbuilders import (
    build_allocation_blocks,
    build_causation_blocks,
    build_dashboard_blocks,
    build_outlook_blocks,
    build_phase_blocks,
)
from .mcatalog import SECTIONS
from .narrative import generate_act_transition, generate_circulation_summary, generate_so_what, narrate_overall_story


def _detect_template(summary: dict) -> str:
    """상황별 템플릿 결정."""
    market = summary.get("market", "US")
    if market == "KR":
        return "kr"
    cycle = (summary.get("cycle") or {}).get("phase", "")
    crisis_zone = ((summary.get("crisis") or {}).get("creditGap") or {}).get("zone", "")
    if cycle == "contraction" or crisis_zone in ("warning", "danger"):
        return "crisis"
    if cycle == "slowdown":
        return "transition"
    return "normal"


def macroReport(
    *,
    market: str = "US",
    as_of: str | None = None,
    fmt: str | None = "rich",
):
    """경제분석 보고서 생성.

    Args:
        market: "US" | "KR"
        as_of: 백테스트 날짜 (YYYY-MM-DD)
        fmt: "rich" | "html" | "markdown" | "json" | None(Review 객체 반환)

    Returns:
        str (fmt 지정 시) 또는 Review 객체
    """
    from dartlab.macro.summary import analyze_summary

    summary = analyze_summary(market=market, as_of=as_of)
    template = _detect_template(summary)

    # ── 섹션 조립 ──
    meta = {s.key: s for s in SECTIONS}

    sections = []

    # 0. 신호등 대시보드
    m = meta["dashboard"]
    dashboard_blocks = build_dashboard_blocks(summary)
    sections.append(Section(
        key=m.key, partId=m.partId, title=m.title,
        blocks=dashboard_blocks, helper=m.helper, aiGuide=m.aiGuide,
    ))

    # 1. 제1막: 국면 진단
    m = meta["phase"]
    phase_blocks = build_phase_blocks(summary)
    transition_1 = generate_act_transition(1, summary)
    if transition_1:
        phase_blocks.append(TextBlock(transition_1, style="transition"))
    sections.append(Section(
        key=m.key, partId=m.partId, title=m.title,
        blocks=phase_blocks, helper=m.helper, aiGuide=m.aiGuide,
    ))

    # 2. 제2막: 인과 역추적
    m = meta["causation"]
    causation_blocks = build_causation_blocks(summary)
    transition_2 = generate_act_transition(2, summary)
    if transition_2:
        causation_blocks.append(TextBlock(transition_2, style="transition"))
    sections.append(Section(
        key=m.key, partId=m.partId, title=m.title,
        blocks=causation_blocks, helper=m.helper, aiGuide=m.aiGuide,
    ))

    # 3. 제3막: 전망과 리스크
    m = meta["outlook"]
    outlook_blocks = build_outlook_blocks(summary)
    sections.append(Section(
        key=m.key, partId=m.partId, title=m.title,
        blocks=outlook_blocks, helper=m.helper, aiGuide=m.aiGuide,
    ))

    # 4. 자산배분 시사점
    m = meta["allocation"]
    allocation_blocks = build_allocation_blocks(summary)
    so_what = generate_so_what(summary)
    if so_what:
        allocation_blocks.append(TextBlock(so_what, style="sowhat"))
    sections.append(Section(
        key=m.key, partId=m.partId, title=m.title,
        blocks=allocation_blocks, helper=m.helper, aiGuide=m.aiGuide,
    ))

    # ── Review 조립 ──
    from dartlab.review import Review

    review = Review(
        stockCode="MACRO",
        corpName=f"{market} 경제",
        sections=sections,
        circulationSummary=narrate_overall_story(summary) or generate_circulation_summary(summary, template),
    )

    if fmt is None:
        return review
    return review.render(fmt)
