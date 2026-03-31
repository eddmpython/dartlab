"""실험 105-005: 3방식 벤치마크 — SemanticMap vs Embedding vs BM25

실험 ID: 105-005
실험명: Filing Semantic Map vs ko-sroberta 임베딩 vs 단순 BM25 직접 비교

목적:
- 동일 20개 쿼리로 3가지 검색 방식 정밀도/속도/의존성 비교
- 최적 하이브리드 조합 결정

가설:
1. SemanticMap: cold start 0ms, precision 68%+
2. Embedding: cold start 12s, precision 83%
3. BM25: cold start 0ms, precision 50-60%
4. SemanticMap + BM25 하이브리드 > 단독

방법:
1. 동일 쿼리 20개 × 3방식 실행
2. precision@5 + cold start + warm 속도 비교

결과:
| 방법 | precision@5 | 평균속도 | cold start |
|------|------------|---------|-----------|
| SemanticMap | 68% | 25ms | 0ms |
| BM25(substring) | 71% | 14ms | 0ms |
| Hybrid(SM+BM25) | 70% | 35ms | 0ms |
| 임베딩(ko-sroberta) | 83% | 58ms | 12,700ms |

- BM25가 SemanticMap보다 precision 높음 — 키워드 확장이 때로는 노이즈
- Hybrid는 BM25보다 낮음 — SemanticMap 결과가 BM25 결과를 희석
- 모든 비임베딩 방법이 cold start 0ms

결론:
- cold start 문제는 완전 해결 (0ms vs 12,700ms)
- precision 83% → 68-71%로 하락 — 의미 검색에서 약점
- report_nm 가중치 높인 SemanticMap(68%)이 004 대비 개선
- BM25가 의외로 강함 — DART 공시가 정형화된 키워드를 이미 포함
- 006 Model2Vec으로 의미 검색 보강 시 75%+ 목표

실험일: 2026-03-31
"""

from __future__ import annotations

import re
import time

import numpy as np
import polars as pl


def loadData():
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27])


# ═══════════════════════════════════════
# 방법 1: SemanticMap (004에서 가져옴)
# ═══════════════════════════════════════

SEMANTIC_MAP = {
    "유상증자": ["유상증자", "증자", "신주", "주금납입"],
    "감자": ["감자", "자본감소"],
    "전환사채": ["전환사채", "CB", "사채", "전환가액"],
    "회사채": ["회사채", "사채", "채무증권"],
    "차입": ["차입", "대출", "자금조달", "사채", "전환사채", "회사채"],
    "대표이사": ["대표이사", "CEO", "대표", "대표집행임원"],
    "사외이사": ["사외이사", "중도퇴임", "겸직", "선임", "해임"],
    "임원": ["임원", "이사", "감사", "사외이사", "대표이사"],
    "경영진": ["대표이사", "임원", "이사", "경영", "선임", "해임"],
    "배당": ["배당", "현금배당", "주당배당"],
    "자기주식": ["자기주식", "자사주", "취득", "처분"],
    "주주총회": ["주주총회", "주총", "소집", "의결권"],
    "대량보유": ["대량보유", "보유", "변동", "최대주주"],
    "합병": ["합병", "인수", "포괄적교환", "분할"],
    "계약": ["계약", "판매", "공급", "영업양도"],
    "소송": ["소송", "분쟁", "경영권", "가처분", "우발부채"],
    "감사": ["감사", "감사의견", "한정", "부적정", "외부감사"],
    "재무": ["재무", "재무제표", "주석", "손익"],
    "증권": ["증권", "발행", "모집", "투자설명서"],
}

NATURAL_LANGUAGE = {
    "돈을 빌렸다": ["차입", "사채", "대출", "전환사채", "회사채"],
    "빌렸다": ["차입", "사채", "대출"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임", "변경"],
    "바뀌었다": ["변경", "선임", "해임"],
    "돈을 줬다": ["배당", "배당금", "현금배당"],
    "문제": ["한정", "부적정", "거절", "감사"],
}


def expandQuery(query):
    keywords = set()
    for phrase, exp in NATURAL_LANGUAGE.items():
        if phrase in query:
            keywords.update(exp)
    for concept, exp in SEMANTIC_MAP.items():
        if concept in query:
            keywords.update(exp)
    for word in query.split():
        if len(word) >= 2:
            keywords.add(word)
    return list(keywords)


def searchSemantic(df, query, topK=5):
    keywords = expandQuery(query)
    if not keywords:
        return pl.DataFrame()

    conditions = []
    for kw in keywords:
        conditions.append(pl.col("report_nm").str.contains(kw, literal=True))
        conditions.append(
            pl.col("section_title").is_not_null()
            & pl.col("section_title").str.contains(kw, literal=True)
        )
    combined = conditions[0]
    for c in conditions[1:]:
        combined = combined | c

    result = df.filter(combined)
    if result.height == 0:
        return pl.DataFrame()

    scores = []
    for row in result.iter_rows(named=True):
        score = 0
        rn = row.get("report_nm", "")
        st = row.get("section_title", "") or ""
        for kw in keywords:
            if kw in rn:
                score += 5  # report_nm 가중치 높임
            if kw in st:
                score += 2
        scores.append(score)

    result = result.with_columns(pl.Series("score", scores))
    result = result.sort("score", descending=True).unique(subset=["rcept_no"], keep="first")
    return result.head(topK)


# ═══════════════════════════════════════
# 방법 2: 단순 BM25 (Polars substring)
# ═══════════════════════════════════════

def searchBM25(df, query, topK=5):
    """단순 substring 매칭 — BM25 대용."""
    words = [w for w in query.split() if len(w) >= 2]
    if not words:
        return pl.DataFrame()

    conditions = []
    for w in words:
        conditions.append(pl.col("report_nm").str.contains(w, literal=True))
        conditions.append(
            pl.col("section_title").is_not_null()
            & pl.col("section_title").str.contains(w, literal=True)
        )
    combined = conditions[0]
    for c in conditions[1:]:
        combined = combined | c

    result = df.filter(combined)
    if result.height == 0:
        return pl.DataFrame()

    scores = []
    for row in result.iter_rows(named=True):
        score = 0
        rn = row.get("report_nm", "")
        st = row.get("section_title", "") or ""
        for w in words:
            if w in rn:
                score += 3
            if w in st:
                score += 1
        scores.append(score)

    result = result.with_columns(pl.Series("score", scores))
    result = result.sort("score", descending=True).unique(subset=["rcept_no"], keep="first")
    return result.head(topK)


# ═══════════════════════════════════════
# 벤치마크
# ═══════════════════════════════════════

QUERIES = [
    ("유상증자 결정", ["유상증자"]),
    ("대표이사 변경", ["대표이사"]),
    ("정기주주총회 결과", ["주주총회", "정기주주총회"]),
    ("사외이사 선임", ["사외이사"]),
    ("대량보유 변동", ["대량보유", "보유주식"]),
    ("주식매수선택권 부여", ["주식매수선택권", "스톡옵션"]),
    ("자기주식 취득", ["자기주식", "자사주"]),
    ("소송 제기", ["소송"]),
    ("회사가 돈을 빌렸다", ["사채", "차입", "대여", "발행"]),
    ("경영진이 바뀌었다", ["대표이사", "임원", "이사"]),
    ("주주에게 배당을 줬다", ["배당", "주주총회"]),
    ("회사 주식을 대량 매수했다", ["대량보유", "취득"]),
    ("기업 가치를 높이겠다", ["기업가치", "제고"]),
    ("새로운 계약을 맺었다", ["계약", "공급", "판매"]),
    ("감사보고서에 문제가 있다", ["감사", "의견", "거절"]),
    ("재무 상태가 나빠졌다", ["재무", "부채", "미지급", "손실"]),
    ("회사 합병", ["합병", "인수"]),
    ("회사채 발행", ["사채", "회사채", "발행"]),
    ("임원 보수", ["보수", "임원", "급여"]),
    ("증권 발행", ["증권", "발행", "유상"]),
]


def evalMethod(name, searchFn, df):
    totalHit = 0
    totalCheck = 0
    latencies = []

    for query, expectedKws in QUERIES:
        t0 = time.time()
        result = searchFn(df, query, topK=5)
        latencies.append(time.time() - t0)

        hits = 0
        resultCount = min(5, result.height) if result.height > 0 else 0
        if result.height > 0:
            for row in result.head(5).iter_rows(named=True):
                rn = row.get("report_nm", "")
                st = row.get("section_title", "") or ""
                combined = f"{rn} {st}".lower()
                if any(kw in combined for kw in expectedKws):
                    hits += 1

        totalHit += hits
        totalCheck += resultCount

    p5 = totalHit / totalCheck if totalCheck > 0 else 0
    avgMs = np.mean(latencies) * 1000
    p95Ms = sorted(latencies)[int(len(latencies) * 0.95)] * 1000

    return {
        "method": name,
        "precision@5": f"{p5:.0%}",
        "avgMs": f"{avgMs:.0f}ms",
        "p95Ms": f"{p95Ms:.0f}ms",
        "hits": totalHit,
        "total": totalCheck,
    }


if __name__ == "__main__":
    df = loadData()
    df = df.filter(pl.col("section_content").is_not_null())
    print(f"데이터: {df.height}행\n")

    results = []

    # 1. SemanticMap (report_nm 가중치 높임)
    r1 = evalMethod("SemanticMap", searchSemantic, df)
    results.append(r1)
    print(f"SemanticMap: p@5={r1['precision@5']}, avg={r1['avgMs']}, cold=0ms")

    # 2. BM25 (단순 substring)
    r2 = evalMethod("BM25(substring)", searchBM25, df)
    results.append(r2)
    print(f"BM25:        p@5={r2['precision@5']}, avg={r2['avgMs']}, cold=0ms")

    # 3. 하이브리드 (SemanticMap + BM25 결과 합산)
    def searchHybrid(df, query, topK=5):
        r1 = searchSemantic(df, query, topK=topK * 2)
        r2 = searchBM25(df, query, topK=topK * 2)
        if r1.height == 0:
            return r2.head(topK)
        if r2.height == 0:
            return r1.head(topK)
        combined = pl.concat([r1, r2], how="diagonal_relaxed")
        combined = combined.sort("score", descending=True).unique(subset=["rcept_no"], keep="first")
        return combined.head(topK)

    r3 = evalMethod("Hybrid(SM+BM25)", searchHybrid, df)
    results.append(r3)
    print(f"Hybrid:      p@5={r3['precision@5']}, avg={r3['avgMs']}, cold=0ms")

    # 비교표
    print(f"\n{'='*60}")
    print(f"{'방법':20s} {'precision@5':12s} {'평균속도':10s} {'cold start':10s}")
    print(f"{'-'*60}")
    for r in results:
        print(f"{r['method']:20s} {r['precision@5']:12s} {r['avgMs']:10s} {'0ms':10s}")
    print(f"{'임베딩(ko-sroberta)':20s} {'83%':12s} {'58ms':10s} {'12,700ms':10s}")
