"""ESG 메트릭 추출.

sections + 기존 scan 결과에서 E/S/G 각 pillar 점수를 계산한다.
기존 governance/workforce/capital 스캔 결과를 G/S 축에 재사용.
환경(E)은 sections 텍스트에서 키워드 매칭으로 추출.
"""

from __future__ import annotations

import polars as pl

from dartlab.engines.analysis.esg.taxonomy import (
    ENVIRONMENT_KEYWORDS,
    SOCIAL_KEYWORDS,
    TOPIC_TO_PILLAR,
)
from dartlab.engines.analysis.esg.types import EsgPillar, EsgResult, _grade_from_score


def analyze_esg(company: object) -> EsgResult | None:
    """단일 기업의 ESG 종합 분석.

    Args:
        company: dartlab Company 객체.

    Returns:
        EsgResult 또는 데이터 부족 시 None.
    """
    stock_code = getattr(company, "stockCode", "")
    corp_name = getattr(company, "corpName", None)

    # sections에서 ESG topic 존재 여부 + 키워드 매칭
    sections = getattr(company, "sections", None)

    e_pillar = _extract_environment(sections, company)
    s_pillar = _extract_social(sections, company)
    g_pillar = _extract_governance(company)

    # 가중 평균 (E 30%, S 30%, G 40%)
    total_score = e_pillar.score * 0.3 + s_pillar.score * 0.3 + g_pillar.score * 0.4

    return EsgResult(
        stockCode=stock_code,
        corpName=corp_name,
        environment=e_pillar,
        social=s_pillar,
        governance=g_pillar,
        totalScore=round(total_score, 1),
        totalGrade=_grade_from_score(total_score),
    )


def _extract_environment(
    sections: pl.DataFrame | None,
    company: object,
) -> EsgPillar:
    """환경(E) pillar 추출 — sections 텍스트 키워드 매칭."""
    metrics: dict = {}
    details: list[str] = []
    score = 0.0

    if sections is None:
        return EsgPillar(
            name="E",
            label="환경",
            score=0,
            grade="E",
            metrics={},
            details=["sections 데이터 없음"],
        )

    # 1. ESG 환경 topic 존재 여부 (20점)
    topic_col = "topic" if "topic" in sections.columns else None
    env_topics_found = []
    if topic_col:
        all_topics = sections.get_column(topic_col).unique().to_list()
        for t in all_topics:
            if TOPIC_TO_PILLAR.get(t) == "E":
                env_topics_found.append(t)

    if env_topics_found:
        score += min(len(env_topics_found) * 10, 20)
        metrics["envTopics"] = env_topics_found
        details.append(f"환경 관련 topic {len(env_topics_found)}개 공시")

    # 2. 환경 키워드 매칭 (40점)
    keyword_hits = _count_keywords_in_sections(sections, ENVIRONMENT_KEYWORDS)
    total_hits = sum(keyword_hits.values())
    if total_hits > 0:
        kw_score = min(total_hits * 4, 40)
        score += kw_score
        metrics["keywordHits"] = keyword_hits
        for category, count in keyword_hits.items():
            if count > 0:
                details.append(f"{category}: 키워드 {count}건 발견")

    # 3. 탄소/에너지 정량 데이터 존재 (40점)
    quant_found = 0
    for cat in ["carbonEmission", "energyUsage", "waterUsage", "wasteManagement"]:
        if keyword_hits.get(cat, 0) >= 2:
            quant_found += 1
    if quant_found > 0:
        score += min(quant_found * 10, 40)
        details.append(f"정량 환경 데이터 {quant_found}개 카테고리")

    score = min(score, 100)

    return EsgPillar(
        name="E",
        label="환경",
        score=round(score, 1),
        grade=_grade_from_score(score),
        metrics=metrics,
        details=details if details else ["환경 공시 정보 미확인"],
    )


def _extract_social(
    sections: pl.DataFrame | None,
    company: object,
) -> EsgPillar:
    """사회(S) pillar 추출 — workforce 스캔 + sections 키워드."""
    metrics: dict = {}
    details: list[str] = []
    score = 0.0

    # 1. 기존 workforce 데이터 활용 (50점)
    try:
        show_fn = getattr(company, "show", None)
        if show_fn:
            emp_data = show_fn("employeeOverview")
            if emp_data is not None and hasattr(emp_data, "height") and emp_data.height > 0:
                score += 20
                metrics["hasEmployeeData"] = True
                details.append("직원 현황 데이터 존재")

            welfare_data = show_fn("employeeWelfare")
            if welfare_data is not None and hasattr(welfare_data, "height") and welfare_data.height > 0:
                score += 15
                metrics["hasWelfareData"] = True
                details.append("복리후생 정보 존재")

            accident_data = show_fn("industrialAccident")
            if accident_data is not None and hasattr(accident_data, "height") and accident_data.height > 0:
                score += 15
                metrics["hasAccidentData"] = True
                details.append("산업재해 정보 존재")
    except (AttributeError, TypeError, ValueError):
        pass

    # 2. sections 키워드 매칭 (30점)
    if sections is not None:
        keyword_hits = _count_keywords_in_sections(sections, SOCIAL_KEYWORDS)
        total_hits = sum(keyword_hits.values())
        if total_hits > 0:
            score += min(total_hits * 5, 30)
            metrics["socialKeywords"] = keyword_hits
            for category, count in keyword_hits.items():
                if count > 0:
                    details.append(f"{category}: 키워드 {count}건")

    # 3. 사회 관련 topic 존재 (20점)
    if sections is not None and "topic" in sections.columns:
        all_topics = sections.get_column("topic").unique().to_list()
        social_topics = [t for t in all_topics if TOPIC_TO_PILLAR.get(t) == "S"]
        if social_topics:
            score += min(len(social_topics) * 5, 20)
            metrics["socialTopics"] = social_topics

    score = min(score, 100)

    return EsgPillar(
        name="S",
        label="사회",
        score=round(score, 1),
        grade=_grade_from_score(score),
        metrics=metrics,
        details=details if details else ["사회 공시 정보 미확인"],
    )


def _extract_governance(company: object) -> EsgPillar:
    """지배구조(G) pillar 추출 — 기존 governance scan 결과 재사용."""
    metrics: dict = {}
    details: list[str] = []
    score = 0.0

    # insight.analyzeGovernance 결과 활용
    try:
        insights = getattr(company, "insights", None)
        if insights is not None:
            gov_insight = getattr(insights, "governance", None)
            if gov_insight is not None:
                # InsightResult → grade + details 활용
                grade_map = {"A": 90, "B": 70, "C": 50, "D": 30, "F": 10}
                gov_grade_str = getattr(gov_insight, "grade", "N")
                score = grade_map.get(gov_grade_str, 0)
                metrics["insightGrade"] = gov_grade_str

                gov_details = getattr(gov_insight, "details", [])
                details.extend(gov_details[:5])

                gov_risks = getattr(gov_insight, "risks", [])
                for r in gov_risks[:3]:
                    details.append(f"[{getattr(r, 'level', 'info')}] {getattr(r, 'text', '')}")
    except (AttributeError, TypeError):
        pass

    # insight가 없으면 기본 채점
    if score == 0:
        try:
            # report에서 직접 추출 시도
            report = getattr(company, "report", None)
            if report is not None:
                # 감사의견
                audit = getattr(report, "auditOpinion", None)
                if audit is not None:
                    score += 25
                    metrics["hasAudit"] = True
                    details.append("감사의견 데이터 존재")

                # 최대주주
                holder = getattr(report, "majorHolder", None)
                if holder is not None:
                    score += 25
                    metrics["hasHolder"] = True
                    details.append("최대주주 데이터 존재")
        except (AttributeError, TypeError):
            pass

    score = min(score, 100)

    return EsgPillar(
        name="G",
        label="지배구조",
        score=round(score, 1),
        grade=_grade_from_score(score),
        metrics=metrics,
        details=details if details else ["지배구조 정보 미확인"],
    )


def _count_keywords_in_sections(
    sections: pl.DataFrame,
    keywords: dict[str, list[str]],
) -> dict[str, int]:
    """sections 텍스트에서 카테고리별 키워드 매칭 횟수."""
    periods = [
        c for c in sections.columns if c not in ("topic", "chapter", "blockType", "textNodeType", "sourceBlockOrder")
    ]
    if not periods:
        return {cat: 0 for cat in keywords}

    # 최신 기간의 텍스트를 합침
    latest_period = periods[0]
    if latest_period not in sections.columns:
        return {cat: 0 for cat in keywords}

    all_text = ""
    for row in sections.iter_rows(named=True):
        cell = str(row.get(latest_period) or "")
        if cell:
            all_text += " " + cell

    if not all_text:
        return {cat: 0 for cat in keywords}

    result: dict[str, int] = {}
    for category, kw_list in keywords.items():
        hits = sum(1 for kw in kw_list if kw in all_text)
        result[category] = hits

    return result


def esg_to_dataframe(result: EsgResult) -> pl.DataFrame:
    """EsgResult를 DataFrame으로 변환."""
    return pl.DataFrame(
        [
            {
                "stockCode": result.stockCode,
                "corpName": result.corpName or "",
                "E_score": result.environment.score,
                "E_grade": result.environment.grade,
                "S_score": result.social.score,
                "S_grade": result.social.grade,
                "G_score": result.governance.score,
                "G_grade": result.governance.grade,
                "total_score": result.totalScore,
                "total_grade": result.totalGrade,
            }
        ]
    )
