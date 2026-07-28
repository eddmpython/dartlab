"""topic간 상호 참조 그래프.

sections 텍스트에서 다른 topic의 키워드 출현으로 topic 연결 그래프를 구축한다.
075-006 실험으로 검증 (5사 avg_degree 4.69~5.95, 허브 일관성 확인).

사용법::

    from dartlab.reference.docs.topicGraph import (
        build_mention_matrix, analyze_graph, get_related_topics,
    )

    matrix = build_mention_matrix(sections)
    analysis = analyze_graph(matrix["adjacency"])
    related = get_related_topics(sections, "businessOverview")
"""

from __future__ import annotations

import re

import polars as pl

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")

# topic → 한국어 키워드 매핑 (33개 topic)
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "businessOverview": ["사업의 개요", "사업개요", "사업 내용", "주요 사업"],
    "companyOverview": ["회사의 개요", "회사개요", "설립일", "본점 소재지"],
    "companyHistory": ["회사의 연혁", "연혁"],
    "capitalChange": ["자본금 변동", "증자", "감자", "자본금"],
    "shareCapital": ["주식의 총수", "발행주식", "수권주식"],
    "dividend": ["배당", "배당금", "주당배당", "배당수익률", "배당성향"],
    "salesOrder": ["수주", "수주잔고", "수주현황", "수주상황"],
    "productService": ["매출", "제품", "서비스", "매출액", "매출구성", "매출비중"],
    "rawMaterial": ["원재료", "원자재", "부자재"],
    "majorContractsAndRnd": ["연구개발", "R&D", "특허", "연구비"],
    "riskManagement": ["위험", "리스크", "위험관리"],
    "riskDerivative": ["파생상품", "통화 위험", "금리 위험", "헤지"],
    "tangibleAsset": ["유형자산", "설비", "건물", "토지"],
    "employee": ["직원", "종업원", "임직원", "인력"],
    "executive": ["임원", "이사", "사외이사", "대표이사"],
    "executivePay": ["보수", "급여", "보상", "스톡옵션"],
    "audit": ["감사", "회계감사", "감사의견", "감사보수"],
    "majorShareholder": ["최대주주", "주주", "지분", "특수관계인"],
    "affiliateGroup": ["계열사", "계열회사", "관계회사", "종속회사"],
    "relatedPartyTx": ["특수관계자", "특수관계자 거래", "관계자 거래"],
    "investorProtection": ["투자자 보호", "집단소송", "주주 권리"],
    "segments": ["부문", "영업부문", "사업부문", "부문별"],
    "financialStatements": ["재무제표", "재무상태표", "손익계산서"],
    "consolidatedStatements": ["연결재무제표", "연결", "연결대상"],
    "fundraising": ["자금조달", "차입금", "사채", "회사채"],
    "contingentLiability": ["우발채무", "소송", "채무보증"],
    "articlesOfIncorporation": ["정관", "이사회", "주주총회"],
    "costByNature": ["비용", "인건비", "감가상각", "판관비"],
    "subsidiaryDetail": ["종속기업", "자회사"],
    "investmentInOtherDetail": ["투자", "지분법", "장기투자"],
    "treasuryStock": ["자사주", "자기주식"],
    "corporateBond": ["사채", "회사채", "사채미상환", "채권"],
    "cashflow": ["현금흐름", "영업활동", "투자활동", "재무활동"],
}


def _topicKeyFor(sectionName: str, topicKeywords: dict[str, list[str]]) -> str:
    """공시 섹션 이름을 topic 키로 맞춘다. 못 맞추면 이름 그대로 둔다.

    인접 행렬의 출발점과 도착점은 같은 이름 공간이어야 그래프를 따라갈 수 있다. 그런데
    `panelTextWide` 는 `topic` 열에 공시 섹션 제목("4. 매출 및 수주상황")을 그대로 싣고,
    도착점은 `TOPIC_KEYWORDS` 의 영문 키("productService")다. 그대로 두면 출발점 여든둘과
    도착점 서른셋이 섞인 그래프가 나오고, 화면에서는 어느 간선도 이어지지 않는다.

    가장 긴 키워드가 이긴다. 섹션 제목 하나에 여러 키워드가 걸릴 때 (예 "매출 및 수주상황")
    더 구체적인 쪽을 고르기 위해서다.
    """
    if sectionName in topicKeywords:
        return sectionName
    best, bestLen = sectionName, 0
    for key, keywords in topicKeywords.items():
        for keyword in keywords:
            if keyword in sectionName and len(keyword) > bestLen:
                best, bestLen = key, len(keyword)
    return best


def buildMentionMatrix(
    sections: pl.DataFrame,
    topicKeywords: dict[str, list[str]] | None = None,
) -> dict:
    """전 topic 텍스트에서 다른 topic 키워드 카운트 → 인접 행렬.

    Args:
        sections: topic(행) × period(열) sections DataFrame.
        topic_keywords: 커스텀 키워드. None이면 기본 TOPIC_KEYWORDS 사용.

    Returns:
        {adjacency: {(src, tgt): count}, topics_with_text: [...], period: str}
    """
    if topicKeywords is None:
        topicKeywords = TOPIC_KEYWORDS

    periods = [c for c in sections.columns if _PERIOD_RE.fullmatch(c)]
    if not periods:
        return {"adjacency": {}, "topics_with_text": [], "period": None}

    latest = sorted(periods, reverse=True)[0]

    # topic별 텍스트 합치기.
    # 표와 본문을 가르는 `blockType` 은 있을 때만 본다. `panelTextWide` 처럼 XML 을 이미 벗겨
    # 평문으로 주는 생산자는 그 열을 내지 않는다. 예전에는 열이 없으면 polars 가
    # ColumnNotFoundError 를 던져 topic 그래프가 통째로 죽었다. 없는 열을 요구하는 쪽이 아니라
    # 있을 때만 좁히는 쪽이 맞다.
    hasBlockType = "blockType" in sections.columns
    topic_texts: dict[str, str] = {}
    for topic in sections["topic"].unique().to_list():
        rows = sections.filter(pl.col("topic") == topic)
        if hasBlockType:
            rows = rows.filter(pl.col("blockType") == "text")
        if rows.height == 0:
            continue
        texts = rows[latest].drop_nulls().to_list()
        text = "\n".join(str(t) for t in texts if t)
        if len(text) <= 50:
            continue
        key = _topicKeyFor(str(topic), topicKeywords)
        topic_texts[key] = f"{topic_texts[key]}\n{text}" if key in topic_texts else text

    # 인접 행렬
    adjacency: dict[tuple[str, str], int] = {}
    for source_topic, text in topic_texts.items():
        for target_topic, keywords in topicKeywords.items():
            if source_topic == target_topic:
                continue
            count = sum(text.count(kw) for kw in keywords)
            if count > 0:
                adjacency[(source_topic, target_topic)] = count

    return {
        "adjacency": adjacency,
        "topics_with_text": list(topic_texts.keys()),
        "period": latest,
    }


def analyzeGraph(
    adjacency: dict[tuple[str, str], int],
    *,
    threshold: int = 3,
) -> dict:
    """인접 행렬 분석 — 임계값 필터, degree 분포, 허브.

    Args:
        adjacency: build_mention_matrix()의 adjacency.
        threshold: 최소 mention 수 (기본 3).

    Returns:
        {edges, nodes, avg_degree, hubs, degree_dist, top_edges}
    """
    filtered = {k: v for k, v in adjacency.items() if v >= threshold}

    degree: dict[str, int] = {}
    for src, tgt in filtered:
        degree[src] = degree.get(src, 0) + 1
        degree[tgt] = degree.get(tgt, 0) + 1

    if not degree:
        return {
            "edges": 0,
            "nodes": 0,
            "avg_degree": 0,
            "hubs": [],
            "degree_dist": {},
            "top_edges": [],
        }

    avg_degree = sum(degree.values()) / len(degree)
    hubs = sorted(degree.items(), key=lambda x: -x[1])[:5]

    return {
        "edges": len(filtered),
        "nodes": len(degree),
        "avg_degree": round(avg_degree, 2),
        "hubs": hubs,
        "degree_dist": degree,
        "top_edges": sorted(filtered.items(), key=lambda x: -x[1])[:10],
    }


def getRelatedTopics(
    sections: pl.DataFrame,
    topic: str,
    *,
    limit: int = 5,
    threshold: int = 3,
    topicKeywords: dict[str, list[str]] | None = None,
) -> list[str]:
    """특정 topic과 연결된 관련 topic 목록.

    Args:
        sections: sections DataFrame.
        topic: 기준 topic.
        limit: 반환 최대 개수.
        threshold: 최소 mention 수.
        topic_keywords: 커스텀 키워드.

    Returns:
        관련 topic 이름 리스트 (mention 많은 순).
    """
    matrix = buildMentionMatrix(sections, topicKeywords)
    adjacency = matrix.get("adjacency", {})

    # topic에서 나가는 + 들어오는 연결
    related: dict[str, int] = {}
    for (src, tgt), count in adjacency.items():
        if count < threshold:
            continue
        if src == topic:
            related[tgt] = related.get(tgt, 0) + count
        elif tgt == topic:
            related[src] = related.get(src, 0) + count

    return [t for t, _ in sorted(related.items(), key=lambda x: -x[1])[:limit]]
