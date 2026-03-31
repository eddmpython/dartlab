"""실험 105-007: 트라이그램 인덱스 — 형태소 분석 없는 한국어 검색

실험 ID: 105-007
실험명: 한국어 3글자(trigram) 단위 역인덱스로 부분 매칭 검색

목적:
- 한국어 형태소 분석 없이 trigram 역인덱스로 빠른 부분 매칭
- "증자" → "유상증자", "무상증자", "증자결정" 전부 매칭
- "돈을 빌렸다" → "빌렸" trigram이 포함된 문서 검색

왜 이게 혁신인가:
- BM25는 정확 키워드만 매칭 ("유상증자" OK, "증자" → 안 됨)
- 임베딩은 의미 검색이지만 12초 cold start
- 트라이그램은 부분 매칭 + cold start 0초 + 의존성 0
- 한국어는 교착어라 "유상증자결정" = "유상" + "증자" + "결정" 분리가 어려운데,
  trigram으로 "유상증", "상증자", "증자결", "자결정"으로 쪼개면 어떤 부분이든 매칭

가설:
1. trigram 인덱스 빌드 < 5초 (9,033 섹션)
2. precision@5 ≥ 75% (BM25 71% 초과)
3. "증자", "사채", "이사" 같은 부분 키워드도 매칭

방법:
1. report_nm + section_title에서 trigram 역인덱스 구축
2. 쿼리도 trigram으로 분해 → 역인덱스 교집합
3. 매칭 trigram 수로 스코어링

결과:
(실험 후 작성)

결론:
(실험 후 작성)

실험일: 2026-03-31
"""

from __future__ import annotations

import time
from collections import defaultdict

import numpy as np
import polars as pl


def loadData():
    df26 = pl.read_parquet("data/dart/allFilings/20260326.parquet")
    df27 = pl.read_parquet("data/dart/allFilings/20260327.parquet")
    return pl.concat([df26, df27]).filter(pl.col("section_content").is_not_null())


def trigrams(text: str) -> set[str]:
    """텍스트에서 3글자 trigram 추출."""
    text = text.strip()
    if len(text) < 3:
        return {text} if text else set()
    return {text[i : i + 3] for i in range(len(text) - 2)}


class TrigramIndex:
    """트라이그램 역인덱스."""

    def __init__(self):
        self.index: dict[str, set[int]] = defaultdict(set)  # trigram → doc IDs
        self.docCount = 0

    def add(self, docId: int, text: str) -> None:
        """문서를 인덱스에 추가."""
        for tg in trigrams(text):
            self.index[tg].add(docId)
        self.docCount += 1

    def search(self, query: str, topK: int = 10) -> list[tuple[int, float]]:
        """쿼리 trigram과 매칭되는 문서 검색.

        Returns: [(docId, score), ...] score = 매칭 trigram 비율
        """
        qTrigrams = trigrams(query)
        if not qTrigrams:
            return []

        # 각 문서의 매칭 trigram 수 카운트
        scores: dict[int, int] = defaultdict(int)
        for tg in qTrigrams:
            for docId in self.index.get(tg, set()):
                scores[docId] += 1

        # 매칭 비율 = 매칭 수 / 쿼리 trigram 수
        results = [
            (docId, matchCount / len(qTrigrams))
            for docId, matchCount in scores.items()
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:topK]


def buildIndex(df: pl.DataFrame) -> TrigramIndex:
    """report_nm + section_title로 trigram 인덱스 구축."""
    idx = TrigramIndex()
    for i, row in enumerate(df.iter_rows(named=True)):
        text = f"{row['report_nm']} {row.get('section_title', '') or ''}"
        idx.add(i, text)
    return idx


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


if __name__ == "__main__":
    df = loadData()
    print(f"데이터: {df.height}행\n")

    # 1. 인덱스 구축
    t0 = time.time()
    idx = buildIndex(df)
    buildTime = time.time() - t0
    print(f"trigram 인덱스 구축: {buildTime:.2f}초, {len(idx.index)} trigrams\n")

    # 2. precision@5 측정
    totalHit = totalCheck = 0
    latencies = []

    for query, expectedKws in QUERIES:
        t0 = time.time()
        results = idx.search(query, topK=5)
        elapsed = time.time() - t0
        latencies.append(elapsed)

        hits = 0
        for docId, score in results:
            row = df.row(docId, named=True)
            combined = f"{row['report_nm']} {row.get('section_title', '')}".lower()
            if any(kw in combined for kw in expectedKws):
                hits += 1

        resultCount = min(5, len(results))
        totalHit += hits
        totalCheck += resultCount

        topRow = df.row(results[0][0], named=True) if results else {}
        topScore = results[0][1] if results else 0
        p5 = hits / resultCount if resultCount > 0 else 0
        print(f'"{query}" ({elapsed*1000:.0f}ms) p@5={p5:.0%} [{topScore:.2f}] {topRow.get("corp_name", "-")} | {str(topRow.get("report_nm", ""))[:30]}')

    overallP5 = totalHit / totalCheck if totalCheck > 0 else 0
    print(f"\n전체 precision@5: {overallP5:.0%} ({totalHit}/{totalCheck})")
    print(f"평균 속도: {np.mean(latencies)*1000:.0f}ms")
    print(f"p95 속도: {sorted(latencies)[int(len(latencies)*0.95)]*1000:.0f}ms")

    # 3. 부분 키워드 매칭 테스트
    print("\n=== 부분 키워드 매칭 ===")
    partialQueries = ["증자", "사채", "이사", "합병", "배당"]
    for q in partialQueries:
        results = idx.search(q, topK=3)
        if results:
            topRow = df.row(results[0][0], named=True)
            print(f'  "{q}" → {topRow.get("report_nm", "")[:35]} [{results[0][1]:.2f}]')
        else:
            print(f'  "{q}" → 결과 없음')
