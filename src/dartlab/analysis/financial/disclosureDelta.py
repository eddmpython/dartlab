"""5-2 공시변화감지 -- 이 회사의 공시가 뭐가 달라졌는가.

sections diff 인프라를 활용하여 기간간 공시 텍스트 변화를 정량화한다.
"""

from __future__ import annotations


# ── 공시변화 종합 요약 ──


def calcDisclosureChangeSummary(company, *, basePeriod: str | None = None) -> dict | None:
    """전체 topic 변화 요약 -- 변화량 상위 topic + 총 변화 건수.

    company.diff() DataFrame에서 changeRate 기준으로
    가장 많이 바뀐 topic을 추출한다.
    """
    diffResult = _safeDiffResult(company)
    if diffResult is None:
        return None

    summaries = diffResult.summaries
    if not summaries:
        return None

    topChanged = diffResult.topChanged(10)
    totalChanges = diffResult.totalChanges
    totalTopics = len(summaries)
    changedTopics = sum(1 for s in summaries if s.changedCount > 0)

    top = []
    for s in topChanged:
        if s.changedCount == 0:
            continue
        top.append({
            "topic": s.topic,
            "chapter": s.chapter,
            "totalPeriods": s.totalPeriods,
            "changedCount": s.changedCount,
            "changeRate": round(s.changeRate, 3),
        })

    return {
        "totalChanges": totalChanges,
        "totalTopics": totalTopics,
        "changedTopics": changedTopics,
        "unchangedTopics": totalTopics - changedTopics,
        "topChanged": top,
    } if top else None


# ── 핵심 공시 변화 추적 ──


_KEY_TOPICS = [
    "businessOverview",
    "riskFactors",
    "accountingPolicy",
    "contingencies",
    "relatedPartyTransactions",
    "segmentInfo",
]


def calcKeyTopicChanges(company, *, basePeriod: str | None = None) -> dict | None:
    """핵심 공시 topic 변화 추적.

    사업개요/리스크/회계정책/우발부채/특수관계자/사업부문 등
    분석적으로 중요한 topic의 변화를 추적한다.
    """
    diffResult = _safeDiffResult(company)
    if diffResult is None:
        return None

    summaryMap = {s.topic: s for s in diffResult.summaries}
    topicsAttr = getattr(company, "topics", None)
    if topicsAttr is not None and hasattr(topicsAttr, "get_column"):
        availableTopics = set(topicsAttr.get_column("topic").to_list())
    elif isinstance(topicsAttr, list):
        availableTopics = set(topicsAttr)
    else:
        availableTopics = set(summaryMap.keys())

    results = []
    for topic in _KEY_TOPICS:
        if topic not in availableTopics:
            continue
        s = summaryMap.get(topic)
        if s is None:
            continue
        results.append({
            "topic": topic,
            "chapter": s.chapter,
            "totalPeriods": s.totalPeriods,
            "changedCount": s.changedCount,
            "stableCount": s.stableCount,
            "changeRate": round(s.changeRate, 3),
        })

    return {"keyTopics": results} if results else None


# ── 변화 크기 분석 ──


def calcChangeIntensity(company, *, basePeriod: str | None = None) -> dict | None:
    """변화 크기(바이트) 분석 -- 어떤 topic이 얼마나 크게 바뀌었나.

    diff entries에서 바이트 변화량 기준 top topic을 추출한다.
    """
    diffResult = _safeDiffResult(company)
    if diffResult is None:
        return None

    entries = diffResult.entries
    if not entries:
        return None

    # topic별 누적 변화량
    topicDelta: dict[str, int] = {}
    for e in entries:
        delta = abs(e.toLen - e.fromLen)
        topicDelta[e.topic] = topicDelta.get(e.topic, 0) + delta

    if not topicDelta:
        return None

    ranked = sorted(topicDelta.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "topByDelta": [
            {"topic": topic, "totalDeltaBytes": delta}
            for topic, delta in ranked
        ],
        "totalDeltaBytes": sum(topicDelta.values()),
    }


# ── 플래그 ──


def calcDisclosureDeltaFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """공시변화감지 경고/기회 플래그."""
    flags: list[tuple[str, str]] = []

    summary = calcDisclosureChangeSummary(company)
    if summary is None:
        return flags

    # 변화 없는 회사
    if summary["changedTopics"] == 0:
        flags.append(("전 기간 공시 텍스트 변화 없음 -- 보일러플레이트 가능성", "warning"))
        return flags

    # 핵심 topic 변화 감지
    keyChanges = calcKeyTopicChanges(company)
    if keyChanges and keyChanges["keyTopics"]:
        for kt in keyChanges["keyTopics"]:
            topic = kt["topic"]
            rate = kt["changeRate"]
            if rate >= 0.8:
                flags.append((f"{topic}: 변화율 {rate:.0%} -- 빈번한 공시 변경", "warning"))
            elif rate == 0:
                if kt["totalPeriods"] >= 3:
                    flags.append((f"{topic}: {kt['totalPeriods']}기 연속 무변화", "warning"))

    # 상위 변화 topic
    topChanged = summary.get("topChanged", [])
    if topChanged:
        top = topChanged[0]
        if top["changeRate"] >= 0.8:
            flags.append(
                (f"최다 변화 topic: {top['topic']} (변화율 {top['changeRate']:.0%})", "warning")
            )

    # 회계정책 변경 감지
    if keyChanges and keyChanges["keyTopics"]:
        acctPolicy = next(
            (kt for kt in keyChanges["keyTopics"] if kt["topic"] == "accountingPolicy"),
            None,
        )
        if acctPolicy and acctPolicy["changedCount"] > 0:
            flags.append(("회계정책 공시 변경 감지 -- 정책 변경 여부 확인 필요", "warning"))

    return flags


# ── 내부 헬퍼 ──


def _safeDiffResult(company):
    """company.docs.sections에서 DiffResult를 안전하게 얻는다.

    결과를 company._cache에 저장하여 4개 calc 함수가 공유.
    """
    cache = getattr(company, "_cache", None)
    _KEY = "_diffResult"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    result = None
    try:
        docsSections = company.docs.sections
        if docsSections is not None:
            from dartlab.core.docs.diff import sectionsDiff
            result = sectionsDiff(docsSections)
    except (AttributeError, ValueError, KeyError, TypeError, ImportError):
        pass

    if cache is not None:
        cache[_KEY] = result
    return result
