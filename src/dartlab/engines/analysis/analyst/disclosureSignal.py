"""DART 공시 정성 신호 추출 — sections diff 기반 규칙 기반 tone 분석."""

from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from dartlab.engines.common.docs.diff import sectionsDiff, topicDiff


@dataclass
class DisclosureSignal:
    """공시 텍스트 기반 매출 정성 신호."""

    toneScore: float = 0.0  # -1.0 ~ +1.0
    changeIntensity: float = 0.0  # 0.0 ~ 1.0
    topicSignals: dict[str, float] = field(default_factory=dict)
    keyPhrases: list[str] = field(default_factory=list)
    impliedGrowthAdj: float = 0.0  # ±_MAX_ADJ cap
    confidence: str = "low"  # "high" | "medium" | "low"


# ── 설정 ──

_MAX_ADJ = 3.0  # 최대 성장률 조정 (%p)

# topic별 가중치 (tier A/B/C)
_TOPIC_WEIGHTS: dict[str, float] = {
    "businessOverview": 0.40,
    "majorContractsAndRnd": 0.25,
    "riskDerivative": 0.15,
    "riskFactors": 0.10,
    "contingentLiabilities": 0.05,
    "investmentInOtherCompanies": 0.05,
}

_POSITIVE = [
    "증가", "성장", "확대", "호조", "개선", "수요증가", "신규수주",
    "수출증가", "진출", "확장", "신사업", "출시", "수주", "계약체결",
    "증설", "흑자전환", "흑자", "호전", "상승", "신제품",
]

_NEGATIVE = [
    "감소", "축소", "부진", "하락", "둔화", "수요감소", "수출감소",
    "철수", "중단", "손실", "구조조정", "폐쇄", "적자전환", "적자",
    "악화", "소송", "제재", "과징금", "규제", "불확실", "위험증가",
]


def extractSignal(sections: pl.DataFrame) -> DisclosureSignal | None:
    """sections DataFrame에서 공시 정성 신호를 추출한다."""
    if sections is None or sections.height == 0:
        return None

    if "topic" not in sections.columns:
        return None

    # 연간 기간 우선 (분기는 같은 보고서 누적이라 변화 적음)
    annualCols = sorted(
        [c for c in sections.columns if _isAnnualPeriod(c)],
        reverse=True,
    )
    if len(annualCols) >= 2:
        latestPeriod = annualCols[0]
        prevPeriod = annualCols[1]
    else:
        # 연간 없으면 분기 fallback
        periodCols = sorted(
            [c for c in sections.columns if _isPeriodLike(c)],
            reverse=True,
        )
        if len(periodCols) < 2:
            return None
        latestPeriod = periodCols[0]
        prevPeriod = periodCols[1]

    # diff로 변화율 수집
    diffResult = sectionsDiff(sections)
    if not diffResult:
        return None

    # topic별 changeRate
    topicChangeRates: dict[str, float] = {}
    for summary in diffResult.summaries:
        if summary.topic in _TOPIC_WEIGHTS:
            topicChangeRates[summary.topic] = summary.changeRate

    # 변화 있는 topic에서 키워드 분석
    totalPos = 0
    totalNeg = 0
    topicSignals: dict[str, float] = {}
    keyPhrases: list[str] = []

    for topic, weight in _TOPIC_WEIGHTS.items():
        # sections에서 해당 topic 전체 텍스트를 concat (topicDiff는 1행만 비교하므로 직접 처리)
        latestText = _concatTopicText(sections, topic, latestPeriod)
        prevText = _concatTopicText(sections, topic, prevPeriod)

        if not latestText and not prevText:
            continue

        # difflib으로 줄 단위 비교
        import difflib

        latestLines = latestText.splitlines()
        prevLines = prevText.splitlines()
        addedLines: list[str] = []
        removedLines: list[str] = []

        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, prevLines, latestLines,
        ).get_opcodes():
            if tag == "insert":
                addedLines.extend(latestLines[j1:j2])
            elif tag == "delete":
                removedLines.extend(prevLines[i1:i2])
            elif tag == "replace":
                removedLines.extend(prevLines[i1:i2])
                addedLines.extend(latestLines[j1:j2])

        addedText = "\n".join(addedLines)
        removedText = "\n".join(removedLines)

        posCount = _countKeywords(addedText, _POSITIVE)
        negCount = _countKeywords(addedText, _NEGATIVE)

        # removed에서 긍정 구절 제거 = 부정 신호
        removedPosCount = _countKeywords(removedText, _POSITIVE)
        removedNegCount = _countKeywords(removedText, _NEGATIVE)
        negCount += removedPosCount
        posCount += removedNegCount

        totalPos += posCount * weight
        totalNeg += negCount * weight

        # topic 개별 점수
        topicTotal = posCount + negCount
        if topicTotal > 0:
            topicTone = (posCount - negCount) / topicTotal
            topicSignals[topic] = round(topicTone, 2)

        # 핵심 구절 수집 (최대 5개)
        if len(keyPhrases) < 5:
            for line in addedLines[:3]:
                stripped = line.strip()
                if stripped and len(stripped) > 10 and _hasKeyword(stripped, _POSITIVE + _NEGATIVE):
                    keyPhrases.append(stripped[:80])
                    if len(keyPhrases) >= 5:
                        break

    # toneScore 계산
    totalWeighted = totalPos + totalNeg
    toneScore = (totalPos - totalNeg) / max(totalWeighted, 1.0)
    toneScore = max(-1.0, min(1.0, toneScore))

    # changeIntensity: 텍스트 변화 비율 (added+removed / total lines)
    totalLines = 0
    changedLines = 0
    for topic in _TOPIC_WEIGHTS:
        latestText = _concatTopicText(sections, topic, latestPeriod)
        prevText = _concatTopicText(sections, topic, prevPeriod)
        tLines = max(len(latestText.splitlines()), len(prevText.splitlines()), 1)
        totalLines += tLines
        # 키워드 포함 줄만 카운트 (노이즈 줄 제외)
        import difflib
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, prevText.splitlines(), latestText.splitlines(),
        ).get_opcodes():
            if tag in ("insert", "delete", "replace"):
                changedLines += max(i2 - i1, j2 - j1)
    changeIntensity = changedLines / max(totalLines, 1)
    changeIntensity = min(changeIntensity, 1.0)

    # impliedGrowthAdj
    impliedGrowthAdj = toneScore * changeIntensity * _MAX_ADJ
    impliedGrowthAdj = max(-_MAX_ADJ, min(impliedGrowthAdj, _MAX_ADJ))

    # confidence
    totalKeywords = int(totalPos + totalNeg)
    _TIER_A = ["businessOverview", "majorContractsAndRnd"]
    if totalKeywords >= 5 and any(t in topicSignals for t in _TIER_A):
        confidence = "high"
    elif totalKeywords >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return DisclosureSignal(
        toneScore=round(toneScore, 3),
        changeIntensity=round(changeIntensity, 3),
        topicSignals=topicSignals,
        keyPhrases=keyPhrases,
        impliedGrowthAdj=round(impliedGrowthAdj, 2),
        confidence=confidence,
    )


# ── 내부 유틸 ──


def _concatTopicText(sections: pl.DataFrame, topic: str, period: str) -> str:
    """topic의 모든 행에서 특정 기간 텍스트를 concat."""
    if period not in sections.columns:
        return ""
    filtered = sections.filter(pl.col("topic") == topic)
    if filtered.height == 0:
        return ""
    texts = filtered[period].drop_nulls().to_list()
    return "\n".join(str(t) for t in texts if t)


def _isAnnualPeriod(name: str) -> bool:
    """연간 기간 판별 (2024, 2023 등 — Q 없음)."""
    import re
    return bool(re.fullmatch(r"\d{4}", name))


def _isPeriodLike(name: str) -> bool:
    """기간 컬럼명 판별 (2024, 2024Q3 등)."""
    import re
    return bool(re.fullmatch(r"\d{4}(Q[1-4])?", name))


def _countKeywords(text: str, keywords: list[str]) -> int:
    """텍스트에서 키워드 출현 횟수 합산."""
    count = 0
    for kw in keywords:
        count += text.count(kw)
    return count


def _hasKeyword(text: str, keywords: list[str]) -> bool:
    """텍스트에 키워드가 하나라도 있는지."""
    return any(kw in text for kw in keywords)
