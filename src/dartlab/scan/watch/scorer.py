"""변화 중요도 스코어링.

DiffResult에서 각 topic의 변화에 점수를 부여한다.
기본 changeRate에 키워드 매칭, 텍스트 크기 변화, topic 유형 가중치를 곱한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from dartlab.core.docs.diff import DiffEntry, DiffResult, DiffSummary

# 변화 스코어링용 기본 키워드
_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "트렌드": ["AI", "ESG", "반도체", "바이오", "전기차"],
    "리스크": ["환율", "금리", "소송", "감사의견", "파산"],
    "기회": ["수출", "M&A", "특허", "신약"],
}


# 고가중 topic (경영 핵심)
_HIGH_WEIGHT_TOPICS = frozenset(
    {
        "riskManagement",
        "riskFactors",
        "businessOverview",
        "companyOverview",
        "investmentRisk",
        "regulatoryRisk",
        "majorContract",
        "contingentLiability",
        "auditOpinion",
        "relatedPartyTransaction",
        # EDGAR
        "10-K::item1ARiskFactors",
        "10-K::item7MDA",
        "10-K::item1Business",
    }
)

# 저가중 topic (정형/반복적)
_LOW_WEIGHT_TOPICS = frozenset(
    {
        "boardDiversity",
        "employeeWelfare",
        "facilityOverview",
    }
)


@dataclass
class ScoredChange:
    """중요도 점수가 부여된 변화."""

    topic: str
    chapter: str | None
    changeRate: float
    score: float  # 0~100
    latestFromPeriod: str | None
    latestToPeriod: str | None
    deltaBytes: int  # 최근 변화의 바이트 크기 변화
    reason: str  # 점수 주요 근거


def score_changes(
    diff_result: DiffResult,
    *,
    sections: pl.DataFrame | None = None,
) -> list[ScoredChange]:
    """DiffResult의 각 topic에 중요도 점수를 부여한다.

    스코어링 요소:
    1. changeRate (기본 50%)
    2. topic 가중치 — 핵심 경영 topic 가중
    3. 텍스트 크기 변화율 — 큰 변화일수록 중요
    4. 키워드 매칭 (sections 제공 시) — 트렌드/리스크 키워드 포함 여부

    Args:
        diff_result: sectionsDiff() 결과.
        sections: (선택) 키워드 매칭에 사용할 sections DataFrame.

    Returns:
        ScoredChange 리스트 (score 내림차순 정렬).
    """
    summary_map: dict[str, DiffSummary] = {s.topic: s for s in diff_result.summaries}

    # entries에서 topic별 최근 변화 추출
    latest_entry: dict[str, DiffEntry] = {}
    for entry in diff_result.entries:
        prev = latest_entry.get(entry.topic)
        if prev is None or entry.toPeriod > prev.toPeriod:
            latest_entry[entry.topic] = entry

    # 키워드 매칭 준비
    keywords = _SIGNAL_KEYWORDS
    all_keywords = []
    for kw_list in keywords.values():
        all_keywords.extend(kw_list)

    # 최근 텍스트에서 키워드 카운트 (sections 제공 시)
    topic_keyword_hits: dict[str, int] = {}
    if sections is not None and all_keywords:
        periods = [
            c
            for c in sections.columns
            if c not in ("topic", "chapter", "blockType", "textNodeType", "sourceBlockOrder")
        ]
        if periods:
            latest_period = periods[0]  # 최신 기간 (역순 정렬 가정)
            if "topic" in sections.columns and latest_period in sections.columns:
                for row in sections.iter_rows(named=True):
                    text = str(row.get(latest_period) or "")
                    if not text:
                        continue
                    topic = row.get("topic", "")
                    hits = sum(1 for kw in all_keywords if kw in text)
                    if hits > 0:
                        topic_keyword_hits[topic] = topic_keyword_hits.get(topic, 0) + hits

    scored: list[ScoredChange] = []

    for summary in diff_result.summaries:
        topic = summary.topic
        change_rate = summary.changeRate

        # 1. 기본 점수 = changeRate × 50
        base_score = change_rate * 50.0

        # 2. topic 가중치
        topic_weight = 1.0
        reason_parts = []
        if topic in _HIGH_WEIGHT_TOPICS:
            topic_weight = 1.5
            reason_parts.append("핵심 경영 topic")
        elif topic in _LOW_WEIGHT_TOPICS:
            topic_weight = 0.6

        # 3. 텍스트 크기 변화율
        entry = latest_entry.get(topic)
        delta_bytes = 0
        delta_score = 0.0
        if entry is not None:
            delta_bytes = entry.toLen - entry.fromLen
            if entry.fromLen > 0:
                abs_rate = abs(delta_bytes) / entry.fromLen
                delta_score = min(abs_rate * 30.0, 30.0)  # 최대 30점
                if abs_rate > 0.5:
                    reason_parts.append(f"텍스트 {abs_rate:.0%} 변화")

        # 4. 키워드 가중치
        kw_hits = topic_keyword_hits.get(topic, 0)
        kw_score = min(kw_hits * 2.0, 20.0)  # 최대 20점
        if kw_hits >= 3:
            reason_parts.append(f"트렌드/리스크 키워드 {kw_hits}건")

        # 합산
        raw_score = (base_score + delta_score + kw_score) * topic_weight
        final_score = min(raw_score, 100.0)

        if not reason_parts:
            if change_rate > 0.5:
                reason_parts.append(f"변화율 {change_rate:.0%}")
            elif change_rate > 0:
                reason_parts.append("소폭 변화")
            else:
                reason_parts.append("변화 없음")

        scored.append(
            ScoredChange(
                topic=topic,
                chapter=summary.chapter,
                changeRate=round(change_rate, 3),
                score=round(final_score, 1),
                latestFromPeriod=entry.fromPeriod if entry else None,
                latestToPeriod=entry.toPeriod if entry else None,
                deltaBytes=delta_bytes,
                reason=" / ".join(reason_parts),
            )
        )

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def scored_to_dataframe(scored: list[ScoredChange]) -> pl.DataFrame:
    """ScoredChange 리스트를 DataFrame으로 변환."""
    if not scored:
        return pl.DataFrame(
            schema={
                "topic": pl.Utf8,
                "score": pl.Float64,
                "changeRate": pl.Float64,
                "deltaBytes": pl.Int64,
                "latestPeriod": pl.Utf8,
                "reason": pl.Utf8,
            }
        )
    return pl.DataFrame(
        [
            {
                "topic": s.topic,
                "score": s.score,
                "changeRate": s.changeRate,
                "deltaBytes": s.deltaBytes,
                "latestPeriod": f"{s.latestFromPeriod}→{s.latestToPeriod}" if s.latestFromPeriod else "",
                "reason": s.reason,
            }
            for s in scored
        ]
    )
