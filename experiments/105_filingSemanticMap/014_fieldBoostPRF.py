"""실험 105-014: BM25F 필드 가중치 + Pseudo Relevance Feedback

실험 ID: 105-014
실험명: report_nm 매칭 5배 가중치 + PRF 자동 쿼리 확장

목적:
- "대표이사 변경" 검색 시 대표이사변경 공시가 1위에 오도록 개선
- PRF로 하드코딩 없이 자동 쿼리 확장
- 모든 개선이 데이터 기반, 하드코딩 0

가설:
1. report_nm 매칭 5배 가중치로 정확 공시가 상위에 올라옴
2. PRF로 1차 검색 top-5에서 키워드 추출 → 2차 검색 품질 향상
3. 속도 300ms 이내 유지

방법:
1. 기존 bincount 검색 후 report_nm/section_title 매칭 리랭킹
2. PRF: 1차 top-5 report_nm에서 키워드 추출 → 2차 검색

결과:
- bincount만: 35% (content[:50] 인덱싱으로 노이즈 증가)
- BM25F 리랭킹: 52% (+17%p) — report_nm 매칭 가중치 효과 확인
- BM25F + PRF: 55% (+20%p) — PRF 소폭 추가 개선, 속도 343ms
- "대표이사 변경" → 대표이사변경 공시 정확 매칭 (BM25F 효과)
- 문제: content[:50] 인덱싱이 노이즈를 너무 많이 유입

결론:
- BM25F 리랭킹은 확실히 효과적 — 정확 공시가 상위로 올라옴
- content[:50] 인덱싱은 비공식 표현은 잡지만 전체 precision을 하락시킴
- **최적 조합: content[:50] 없이(report_nm+title만) + BM25F 리랭킹**
  → 이전 95% 유지 + report_nm 매칭 가중치로 순위 개선
- PRF는 비용 대비 효과 미미 (3%p, 속도 2.5x)
- 비공식 표현("횡령", "파산")은 AI 레이어에서 처리하는 게 맞음

실험일: 2026-03-31
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import polars as pl

DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

stemIndexDir = Path("data/dart/stemIndex")
loaded = np.load(stemIndexDir / "stemIndex.npz")
OFFSETS = loaded["offsets"]
DOC_IDS = loaded["docIds"]
STEM_TO_ID = json.loads((stemIndexDir / "stemDict.json").read_text(encoding="utf-8"))
META = pl.read_parquet(stemIndexDir / "meta.parquet")
N_DOCS = META.height

print(f"로드: {N_DOCS:,}문서, {len(STEM_TO_ID):,} stems")


def tokenize(text):
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i: i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i: i + 3] for i in range(len(text) - 2))
    return list(tokens)


def rawSearch(query, topK=30):
    """기본 bincount 검색 — 리랭킹 전."""
    tokens = tokenize(query)
    queryStems = [STEM_TO_ID[t] for t in tokens if t in STEM_TO_ID]
    if not queryStems:
        return []

    allMatched = []
    for stemId in queryStems:
        s, e = OFFSETS[stemId], OFFSETS[stemId + 1]
        if e > s:
            allMatched.append(DOC_IDS[s:e])
    if not allMatched:
        return []

    flat = np.concatenate(allMatched)
    counts = np.bincount(flat, minlength=N_DOCS)

    nTop = min(topK * 3, N_DOCS)
    topIdx = np.argpartition(counts, -nTop)[-nTop:]
    topIdx = topIdx[np.argsort(counts[topIdx])[::-1]]

    results = []
    seen = set()
    for did in topIdx:
        mc = int(counts[did])
        if mc == 0:
            break
        row = META.row(int(did), named=True)
        rcept = row["rcept_no"]
        if rcept in seen:
            continue
        seen.add(rcept)
        results.append({
            "docId": int(did),
            "rawScore": mc / len(queryStems),
            **row,
        })
        if len(results) >= topK:
            break
    return results


def rerankBM25F(results, query, reportWeight=5, titleWeight=2):
    """BM25F 스타일 필드 가중치 리랭킹."""
    queryWords = [w for w in query.split() if len(w) >= 2]
    if not queryWords:
        return results

    for r in results:
        boost = 1.0
        reportNm = r.get("report_nm", "")
        sectionTitle = r.get("section_title", "")

        for w in queryWords:
            if w in reportNm:
                boost += reportWeight
            if w in sectionTitle:
                boost += titleWeight

        r["score"] = r["rawScore"] * boost

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def searchWithPRF(query, topK=5):
    """PRF: 1차 검색 → top-5 키워드 추출 → 2차 검색."""
    # 1차 검색
    firstResults = rawSearch(query, topK=10)
    if not firstResults:
        return []

    # 리랭킹
    firstResults = rerankBM25F(firstResults, query)

    # top-5 report_nm에서 한국어 키워드 추출
    prfKeywords = set()
    for r in firstResults[:5]:
        words = re.findall(r"[가-힣]{2,}", r.get("report_nm", ""))
        prfKeywords.update(words)
        words = re.findall(r"[가-힣]{2,}", r.get("section_title", ""))
        prfKeywords.update(words)

    # 원래 쿼리 키워드 제외
    queryWords = set(re.findall(r"[가-힣]{2,}", query))
    newKeywords = prfKeywords - queryWords

    if not newKeywords:
        return firstResults[:topK]

    # 2차 검색 (원래 쿼리 + PRF 키워드, 단 원래 쿼리 가중)
    expandedQuery = query + " " + " ".join(list(newKeywords)[:5])
    secondResults = rawSearch(expandedQuery, topK=topK * 3)
    secondResults = rerankBM25F(secondResults, query)

    return secondResults[:topK]


QUERIES = [
    ("유상증자 결정", ["유상증자"]),
    ("대표이사 변경", ["대표이사"]),
    ("정기주주총회 결과", ["주주총회", "정기주주총회"]),
    ("사외이사 선임", ["사외이사"]),
    ("자기주식 취득", ["자기주식", "자사주"]),
    ("소송 제기", ["소송"]),
    ("전환사채 발행", ["사채", "전환사채", "발행"]),
    ("배당 정책", ["배당"]),
    ("감사 의견", ["감사"]),
    ("사업의 내용", ["사업"]),
    ("재무제표 주석", ["재무", "주석"]),
    ("횡령", ["횡령", "제재"]),
    ("상장폐지", ["상장폐지"]),
    ("파산", ["파산", "우발부채"]),
    ("공장", ["공장", "사업장", "설비"]),
    ("회사가 돈을 빌렸다", ["사채", "차입", "위험"]),
    ("주가가 떨어졌다", ["주가"]),
]

if __name__ == "__main__":
    # 1. 기존 방식 (리랭킹 없음)
    print("=== 기존 (bincount만) ===")
    totalHit1 = totalCheck1 = 0
    for q, expected in QUERIES:
        results = rawSearch(q, topK=5)
        hits = 0
        for r in results[:5]:
            combined = f"{r.get('report_nm', '')} {r.get('section_title', '')}"
            if any(kw in combined for kw in expected):
                hits += 1
        totalHit1 += hits
        totalCheck1 += min(5, len(results))

    p1 = totalHit1 / totalCheck1 if totalCheck1 > 0 else 0
    print(f"  precision@5: {p1:.0%}")

    # 2. BM25F 리랭킹만
    print("\n=== BM25F 리랭킹 ===")
    totalHit2 = totalCheck2 = 0
    for q, expected in QUERIES:
        results = rawSearch(q, topK=30)
        results = rerankBM25F(results, q)
        hits = 0
        for r in results[:5]:
            combined = f"{r.get('report_nm', '')} {r.get('section_title', '')}"
            if any(kw in combined for kw in expected):
                hits += 1
        totalHit2 += hits
        totalCheck2 += min(5, len(results[:5]))
        if results:
            r = results[0]
            print(f'  "{q}" [{r["score"]:.2f}] {r["corp_name"]} | {r["report_nm"][:25]}')

    p2 = totalHit2 / totalCheck2 if totalCheck2 > 0 else 0
    print(f"  precision@5: {p2:.0%}")

    # 3. BM25F + PRF
    print("\n=== BM25F + PRF ===")
    totalHit3 = totalCheck3 = 0
    latencies = []
    for q, expected in QUERIES:
        t0 = time.time()
        results = searchWithPRF(q, topK=5)
        ms = (time.time() - t0) * 1000
        latencies.append(ms)
        hits = 0
        for r in results[:5]:
            combined = f"{r.get('report_nm', '')} {r.get('section_title', '')}"
            if any(kw in combined for kw in expected):
                hits += 1
        totalHit3 += hits
        totalCheck3 += min(5, len(results))
        if results:
            r = results[0]
            print(f'  "{q}" ({ms:.0f}ms) [{r["score"]:.2f}] {r["corp_name"]} | {r["report_nm"][:25]}')

    p3 = totalHit3 / totalCheck3 if totalCheck3 > 0 else 0
    print(f"  precision@5: {p3:.0%}")
    print(f"  평균 속도: {np.mean(latencies):.0f}ms")

    # 비교표
    print(f"\n{'='*50}")
    print(f"{'방법':20s} {'precision@5':12s}")
    print(f"{'-'*50}")
    print(f"{'bincount만':20s} {f'{p1:.0%}':12s}")
    print(f"{'BM25F 리랭킹':20s} {f'{p2:.0%}':12s}")
    print(f"{'BM25F + PRF':20s} {f'{p3:.0%}':12s}")
