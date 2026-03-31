"""실험 105-004: 자연어 → 그래프 쿼리 변환 + 통합 검색

실험 ID: 105-004
실험명: Taxonomy + CofilingGraph + SectionMap 통합 → 자연어 검색

목적:
- 3가지 의미 구조(유형분류, 동반공시, 섹션클러스터)를 결합한 검색
- 모델 로딩 없이 의미 검색 동작 확인
- cold start 시간 + precision@5 실측

가설:
1. cold start < 100ms (그래프 로딩만)
2. precision@5 ≥ 70% (임베딩 83% 대비)
3. "회사가 돈을 빌렸다" 같은 자연어도 관련 공시 반환

방법:
1. 001 Taxonomy + 003 SectionMap 키워드 확장
2. report_nm + section_title에서 Polars 필터
3. 매칭 점수 = report_nm 매칭(3점) + section_title 매칭(2점) + content 매칭(1점)
4. 기존 임베딩 검색과 동일 20개 쿼리로 precision@5 비교

결과:
- cold start: 0ms (그래프는 Python dict, 로딩 불필요)
- precision@5: 68% (20개 쿼리, 100검사)
- 검색 속도: 평균 21ms, p50=10ms, p95=87ms, 최소 2ms
- 강한 쿼리: 주주총회/사외이사/배당/계약/감사/증권 → 100%
- 약한 쿼리: 유상증자(0%), 합병(20%), 소송(20%) → 키워드 확장이 너무 넓거나 좁음
- 문제: report_nm에 "유상증자"가 있는데 score가 section_content 매칭에 묻힘

결론:
- 모델 없이 의미 검색 동작 확인 — cold start 0ms, 검색 21ms
- precision 68%는 목표 70% 살짝 미달 — 점수 체계 개선으로 해결 가능
- report_nm 매칭 가중치를 높이면 정밀도 10%p+ 향상 예상
- 채택: 005 벤치마크 + 006 Model2Vec 보강으로 75%+ 목표

실험일: 2026-03-31
"""

from __future__ import annotations

import re
import time
from collections import defaultdict

import polars as pl


def loadData():
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27])


# ═══════════════════════════════════════
# 의미 그래프 — 001 + 003 통합
# ═══════════════════════════════════════

# 자연어 → 공시 키워드 매핑 (동의어 확장)
SEMANTIC_MAP = {
    # 자본변동
    "유상증자": ["유상증자", "증자", "신주", "주금납입", "실권주"],
    "감자": ["감자", "자본감소", "주식병합"],
    "전환사채": ["전환사채", "CB", "사채", "전환가액"],
    "신주인수권": ["신주인수권", "BW", "워런트"],
    "회사채": ["회사채", "사채", "채무증권", "사채원리금"],
    "차입": ["차입", "대출", "자금조달", "사채", "전환사채", "회사채"],

    # 경영진
    "대표이사": ["대표이사", "CEO", "대표", "대표집행임원"],
    "사외이사": ["사외이사", "중도퇴임", "겸직", "선임", "해임"],
    "임원": ["임원", "이사", "감사", "사외이사", "대표이사"],
    "경영진": ["대표이사", "임원", "이사", "경영", "선임", "해임"],

    # 주주
    "배당": ["배당", "현금배당", "주당배당", "배당수익률"],
    "자기주식": ["자기주식", "자사주", "취득", "처분", "소각"],
    "주주총회": ["주주총회", "주총", "소집", "의결권", "위임장"],
    "대량보유": ["대량보유", "5%", "보유", "변동", "최대주주"],

    # 거래/계약
    "합병": ["합병", "인수", "M&A", "포괄적교환", "분할"],
    "계약": ["계약", "판매", "공급", "영업양도", "영업양수"],
    "투자": ["투자", "시설투자", "유형자산", "출자", "금전대여"],

    # 리스크
    "소송": ["소송", "분쟁", "경영권", "가처분", "우발부채"],
    "감사": ["감사", "감사의견", "한정", "부적정", "거절", "외부감사"],

    # 재무
    "재무": ["재무", "재무제표", "주석", "대차대조표", "손익", "현금흐름"],
    "수익": ["매출", "영업이익", "순이익", "수익", "매출액"],
    "부채": ["부채", "차입", "사채", "이자", "부채비율"],
}

# 자연어 표현 → 키워드 매핑
NATURAL_LANGUAGE = {
    "돈을 빌렸다": ["차입", "사채", "대출", "전환사채", "회사채", "자금조달"],
    "빌렸다": ["차입", "사채", "대출", "전환사채"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임", "변경"],
    "바뀌었다": ["변경", "교체", "선임", "해임"],
    "주식을 발행했다": ["유상증자", "증자", "신주", "발행"],
    "합쳤다": ["합병", "인수", "교환", "이전"],
    "돈을 줬다": ["배당", "배당금", "현금배당"],
    "소송": ["소송", "분쟁", "가처분"],
    "투자": ["투자", "시설", "출자", "취득"],
    "문제": ["한정", "부적정", "거절", "감사", "리스크"],
}

# DART 뷰어 URL
DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="


def expandQuery(query: str) -> list[str]:
    """자연어 쿼리 → 공시 키워드 확장."""
    keywords = set()

    # 1. 자연어 매핑
    for phrase, expansion in NATURAL_LANGUAGE.items():
        if phrase in query:
            keywords.update(expansion)

    # 2. 의미 맵 매핑
    for concept, expansion in SEMANTIC_MAP.items():
        if concept in query:
            keywords.update(expansion)

    # 3. 원본 단어도 추가 (공백 분리)
    for word in query.split():
        if len(word) >= 2:
            keywords.add(word)

    return list(keywords)


def searchFilingSemantic(
    df: pl.DataFrame,
    query: str,
    topK: int = 5,
) -> pl.DataFrame:
    """Filing Semantic Map 기반 검색.

    점수 체계:
    - report_nm 매칭: 3점/키워드
    - section_title 매칭: 2점/키워드
    - section_content 앞 500자 매칭: 1점/키워드
    """
    keywords = expandQuery(query)
    if not keywords:
        return pl.DataFrame()

    # Polars 필터: 키워드 중 하나라도 매칭
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

    # 점수 계산
    scores = []
    for row in result.iter_rows(named=True):
        score = 0
        reportNm = row.get("report_nm", "")
        sectionTitle = row.get("section_title", "") or ""
        content = (row.get("section_content", "") or "")[:500]

        for kw in keywords:
            if kw in reportNm:
                score += 3
            if kw in sectionTitle:
                score += 2
            if kw in content:
                score += 1

        scores.append(score)

    result = result.with_columns(
        pl.Series("score", scores),
        (pl.lit(DART_VIEWER) + pl.col("rcept_no")).alias("dartUrl"),
    )

    # 중복 제거 (같은 rcept_no의 가장 높은 점수만)
    result = result.sort("score", descending=True)
    result = result.unique(subset=["rcept_no"], keep="first")

    return result.head(topK)


if __name__ == "__main__":
    df = loadData()
    print(f"데이터: {df.height}행\n")

    # ═══════════════════════════════════════
    # 1. cold start 측정
    # ═══════════════════════════════════════
    t0 = time.time()
    _ = expandQuery("유상증자 결정")  # 그래프 로딩
    coldStart = time.time() - t0
    print(f"cold start: {coldStart*1000:.1f}ms\n")

    # ═══════════════════════════════════════
    # 2. 정밀도 테스트 — 20개 쿼리
    # ═══════════════════════════════════════
    queries = [
        # (쿼리, 관련 키워드 — precision 판단용)
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

    totalHit = 0
    totalCheck = 0

    print("=== Filing Semantic Map 검색 정밀도 ===\n")

    for query, expectedKws in queries:
        t0 = time.time()
        result = searchFilingSemantic(df, query, topK=5)
        elapsed = time.time() - t0

        hits = 0
        resultCount = min(5, result.height)

        for row in result.head(5).iter_rows(named=True):
            reportNm = row.get("report_nm", "")
            title = row.get("section_title", "") or ""
            combined = f"{reportNm} {title}".lower()
            if any(kw in combined for kw in expectedKws):
                hits += 1

        precision = hits / resultCount if resultCount > 0 else 0
        totalHit += hits
        totalCheck += resultCount

        print(f'"{query}" ({elapsed*1000:.0f}ms) p@5={precision:.0%} ({hits}/{resultCount})')
        if result.height > 0:
            top = result.row(0, named=True)
            print(f'  → [{top["score"]}] {top["corp_name"]} | {top["report_nm"][:35]}')

    overallP5 = totalHit / totalCheck if totalCheck > 0 else 0
    print(f"\n{'='*50}")
    print(f"전체 precision@5: {overallP5:.1%} ({totalHit}/{totalCheck})")

    # ═══════════════════════════════════════
    # 3. 속도 측정 (100회)
    # ═══════════════════════════════════════
    import numpy as np

    latencies = []
    testQueries = [q for q, _ in queries]
    for _ in range(5):
        for q in testQueries:
            t0 = time.time()
            searchFilingSemantic(df, q, topK=5)
            latencies.append(time.time() - t0)

    latencies.sort()
    print(f"\n=== 속도 (100회) ===")
    print(f"평균: {np.mean(latencies)*1000:.0f}ms")
    print(f"p50:  {latencies[len(latencies)//2]*1000:.0f}ms")
    print(f"p95:  {latencies[int(len(latencies)*0.95)]*1000:.0f}ms")
    print(f"최소: {latencies[0]*1000:.0f}ms")
    print(f"최대: {latencies[-1]*1000:.0f}ms")
