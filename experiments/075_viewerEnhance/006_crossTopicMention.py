"""
실험 ID: 006
실험명: topic간 상호 참조 그래프

목적:
- sections 텍스트에서 다른 topic의 키워드 출현으로 topic 연결 그래프를 구축
- InsightDashboard의 하드코딩 RELATED_TOPICS를 데이터 기반으로 대체 가능한지 검증

가설:
1. topic→키워드 사전으로 50개 topic 이상 커버 가능
2. topic 그래프에서 평균 degree 2+ (각 topic이 최소 2개 다른 topic과 연결)
3. 5개사에서 일관된 허브 topic 존재 (businessOverview, riskFactors 등)

방법:
1. topic→키워드 사전 구축 (registry label + 한국어 키워드)
2. 전 topic 텍스트에서 다른 topic 키워드 출현 카운트
3. 임계값(3회+) 이상인 연결만 남겨서 인접 행렬 구축
4. degree 분포, 허브 topic 분석

결과 (v2 — non-period 필터 정규식 수정 후):
- 키워드 사전: 33개 topic 커버
- 삼성전자: 94엣지, 36노드, avg_degree=5.22
- 현대차: 113엣지, 38노드, avg_degree=5.95
- 카카오: 90엣지, 35노드, avg_degree=5.14
- SK하이닉스: 74엣지, 31노드, avg_degree=4.77
- LG화학: 75엣지, 32노드, avg_degree=4.69
- 허브 일관성: fsSummary 5/5사, businessOverview 5/5사
- 기간 정규식 `^\d{4}(Q[1-4])?$`로 메타 컬럼 오염 완전 제거
- v1 대비 엣지 수 30~60% 감소 (메타 컬럼 텍스트의 거짓 매칭 제거)

결론:
- 가설 1 부분채택: 33개 topic 커버 (50개 미달이지만 핵심 topic은 포함)
  → 사전 확장으로 해결 가능
- 가설 2 채택: 평균 degree 4.69~5.95 (2+ 목표 초과, v1보다 보수적이지만 더 정확)
- 가설 3 채택: fsSummary/businessOverview 5/5사 공통 허브
- v1→v2 변화: 메타 컬럼 오염 제거로 엣지 30~60% 감소, 더 정확한 그래프
- 흡수: common/docs/topicGraph.py 모듈 → 서버에서 "관련 topic" 반환
  → UI RELATED_TOPICS 하드코딩 대체
- 개선: 재무제표 허브를 제외하고 서술형 topic 간 연결만 추출하면
  실질적 "관련 topic" 추천 가능

실험일: 2026-03-20
"""

import polars as pl

import dartlab

# topic → 키워드 매핑 사전
# registry label + 한국어 핵심 키워드
TOPIC_KEYWORDS = {
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
    "financialStatements": ["재무제표", "대차대조표", "손익계산서"],
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


def build_mention_matrix(sections_df: pl.DataFrame, topic_keywords: dict) -> dict:
    """전 topic 텍스트에서 다른 topic 키워드 카운트 → 인접 행렬."""
    # 기간 컬럼
    import re as _re
    periods = [c for c in sections_df.columns if _re.match(r"^\d{4}(Q[1-4])?$", c)]

    # 최신 기간만 사용
    latest = sorted(periods, reverse=True)[0] if periods else None
    if not latest:
        return {"error": "no periods"}

    # topic별 텍스트 합치기
    topics_in_data = sections_df["topic"].unique().to_list()
    topic_texts = {}
    for topic in topics_in_data:
        rows = sections_df.filter(
            (pl.col("topic") == topic) &
            (pl.col("blockType") == "text")
        )
        if len(rows) == 0:
            continue
        texts = rows[latest].drop_nulls().to_list()
        text = "\n".join(str(t) for t in texts if t)
        if len(text) > 50:
            topic_texts[topic] = text

    # 인접 행렬 구축
    adjacency = {}  # {(source_topic, target_topic): count}
    for source_topic, text in topic_texts.items():
        for target_topic, keywords in topic_keywords.items():
            if source_topic == target_topic:
                continue
            count = 0
            for kw in keywords:
                count += text.count(kw)
            if count > 0:
                adjacency[(source_topic, target_topic)] = count

    return {
        "adjacency": adjacency,
        "topics_with_text": list(topic_texts.keys()),
        "period": latest,
    }


def analyze_graph(adjacency: dict, threshold: int = 3) -> dict:
    """인접 행렬 분석."""
    # 임계값 필터
    filtered = {k: v for k, v in adjacency.items() if v >= threshold}

    # degree 계산
    degree = {}
    for (src, tgt), count in filtered.items():
        degree[src] = degree.get(src, 0) + 1
        degree[tgt] = degree.get(tgt, 0) + 1

    if not degree:
        return {
            "edges": 0,
            "nodes": 0,
            "avg_degree": 0,
            "hubs": [],
            "isolated": [],
        }

    avg_degree = sum(degree.values()) / len(degree)

    # 허브 (degree 상위 5)
    hubs = sorted(degree.items(), key=lambda x: -x[1])[:5]

    # 고립 (degree 0)
    all_topics = set()
    for src, tgt in filtered:
        all_topics.add(src)
        all_topics.add(tgt)

    return {
        "edges": len(filtered),
        "nodes": len(degree),
        "avg_degree": round(avg_degree, 2),
        "hubs": hubs,
        "degree_dist": degree,
        "top_edges": sorted(filtered.items(), key=lambda x: -x[1])[:10],
    }


if __name__ == "__main__":
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("035720", "카카오"),
        ("000660", "SK하이닉스"),
        ("051910", "LG화학"),
    ]

    print(f"키워드 사전: {len(TOPIC_KEYWORDS)}개 topic 커버")

    all_results = {}

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        c = dartlab.Company(code)
        sections = c.docs.sections.raw

        matrix = build_mention_matrix(sections, TOPIC_KEYWORDS)
        if "error" in matrix:
            print(f"  오류: {matrix['error']}")
            continue

        print(f"  텍스트 있는 topic: {len(matrix['topics_with_text'])}개")
        print(f"  기간: {matrix['period']}")
        print(f"  raw 엣지: {len(matrix['adjacency'])}개")

        # 분석 (임계값 3)
        analysis = analyze_graph(matrix["adjacency"], threshold=3)
        print(f"\n  [그래프 분석 (임계값 ≥ 3)]")
        print(f"  엣지: {analysis['edges']}개")
        print(f"  노드: {analysis['nodes']}개")
        print(f"  평균 degree: {analysis['avg_degree']}")

        if analysis["hubs"]:
            print(f"\n  [허브 topic (degree 상위)]")
            for topic, deg in analysis["hubs"]:
                print(f"    · {topic}: degree {deg}")

        if analysis["top_edges"]:
            print(f"\n  [강한 연결 (mention 상위)]")
            for (src, tgt), count in analysis["top_edges"][:7]:
                print(f"    · {src} → {tgt}: {count}회")

        all_results[name] = {
            "topics_with_text": len(matrix["topics_with_text"]),
            "raw_edges": len(matrix["adjacency"]),
            "filtered_edges": analysis["edges"],
            "nodes": analysis["nodes"],
            "avg_degree": analysis["avg_degree"],
            "hubs": [(t, d) for t, d in analysis["hubs"]],
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합")
    print(f"{'='*60}")
    print(f"  키워드 사전: {len(TOPIC_KEYWORDS)}개 topic")

    for name, r in all_results.items():
        print(f"  {name}: {r['filtered_edges']}엣지, {r['nodes']}노드, avg_degree={r['avg_degree']}")
        hub_str = ", ".join(f"{t}({d})" for t, d in r["hubs"][:3])
        print(f"    허브: {hub_str}")

    # 허브 일관성 분석
    hub_counts = {}
    for r in all_results.values():
        for topic, deg in r["hubs"]:
            hub_counts[topic] = hub_counts.get(topic, 0) + 1

    print(f"\n  [허브 일관성] (5사 중 허브 등장 횟수)")
    for topic, count in sorted(hub_counts.items(), key=lambda x: -x[1]):
        print(f"    · {topic}: {count}/5사")
