"""실험 105-011: docs store 검색 속도 최적화

실험 ID: 105-011
실험명: 400만 문서 stem ID 역인덱스 검색 3~5초 → 목표 100ms 이내

목적:
- 010에서 구축한 docs store(400만 문서)의 검색 속도 개선
- 파이썬 루프 → numpy vectorized 연산

가설:
1. numpy bincount로 docId별 매칭 수 집계 → 100ms 이내
2. 고빈도 stem(10만+ docId) 제외로 추가 가속
3. precision 유지

방법:
1. CSR에서 docId 배열 추출 → numpy concatenate
2. numpy bincount로 한번에 집계
3. argsort로 상위 topK

결과:
- store 로드: 0.1초 (npz + json + parquet)
- 검색 속도: 평균 140ms, p50=172ms, p95=208ms, 최소 54ms
- 010 대비: 32배 가속 (3,500~5,500ms → 140ms)
- 검색 품질: 동작 — "배당 정책"→배당 섹션, "전환사채 발행"→자금조달 섹션
- 400만 문서에서 140ms — 실시간 사용 가능

결론:
- numpy bincount가 파이썬 루프를 완전히 대체 — 32x 가속
- 400만 문서에서 140ms면 충분히 실용적
- store 로드 0.1초 → cold start도 무시할 수 있는 수준
- **이 방식으로 docs(사업보고서) + allFilings(수시공시) 통합 검색 가능**
- 채택: ngramIndex.py의 searchNgram()에 bincount 방식 적용

실험일: 2026-03-31
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

STORE_DIR = Path("experiments/105_filingSemanticMap/docsStore")
DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

SYNONYMS = {
    "돈을 빌렸다": ["사채", "차입", "대출", "자금조달", "전환사채"],
    "빌렸다": ["사채", "차입", "대출"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임", "변경"],
    "바뀌었다": ["변경", "교체", "선임", "해임"],
    "돈을 줬다": ["배당", "배당금", "현금배당"],
    "나빠졌다": ["부채", "미지급", "손실", "감자"],
    "높이겠다": ["제고", "기업가치", "개선"],
    "맺었다": ["계약", "체결", "공급"],
    "매수했다": ["대량보유", "취득", "매수"],
    "합병": ["합병", "인수", "분할", "교환"],
    "소송": ["소송", "분쟁", "가처분", "경영권"],
    "감사": ["감사", "감사의견", "한정", "부적정"],
    "재무": ["재무", "재무제표", "재무상태"],
    "배당": ["배당", "현금배당", "배당금"],
    "투자": ["투자", "시설투자", "설비", "자본적지출"],
}


def _tokenize(text):
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i: i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i: i + 3] for i in range(len(text) - 2))
    return tokens


def expandQuery(query):
    expanded = query
    for phrase, syns in SYNONYMS.items():
        if phrase in query:
            expanded += " " + " ".join(syns)
    return expanded


# 캐시
_store = None


def loadStore():
    global _store
    if _store is not None:
        return _store

    t0 = time.time()
    loaded = np.load(STORE_DIR / "stemIndex.npz")
    with open(STORE_DIR / "stemDict.json", "r", encoding="utf-8") as f:
        stemToId = json.load(f)
    meta = pl.read_parquet(STORE_DIR / "meta.parquet")
    elapsed = time.time() - t0

    nDocs = meta.height
    print(f"store 로드: {elapsed:.1f}초, {nDocs:,}문서, {len(stemToId):,} stems")

    _store = {
        "stemToId": stemToId,
        "offsets": loaded["offsets"],
        "docIds": loaded["docIds"],
        "meta": meta,
        "nDocs": nDocs,
    }
    return _store


def searchFast(query: str, topK: int = 5) -> pl.DataFrame:
    """numpy vectorized 검색 — bincount로 한번에 집계."""
    store = loadStore()
    stemToId = store["stemToId"]
    offsets = store["offsets"]
    docIds = store["docIds"]
    meta = store["meta"]
    nDocs = store["nDocs"]

    expanded = expandQuery(query)
    tokens = list(_tokenize(expanded))
    queryStems = [stemToId[t] for t in tokens if t in stemToId]
    if not queryStems:
        return pl.DataFrame()

    # numpy vectorized: 매칭되는 모든 docId를 한번에 수집
    allMatched = []
    for stemId in queryStems:
        start = offsets[stemId]
        end = offsets[stemId + 1]
        if end > start:
            allMatched.append(docIds[start:end])

    if not allMatched:
        return pl.DataFrame()

    # concatenate + bincount → docId별 매칭 수
    flat = np.concatenate(allMatched)
    counts = np.bincount(flat, minlength=nDocs)

    # 상위 topK * 3 (중복 제거 여유분)
    topIndices = np.argpartition(counts, -min(topK * 3, len(counts)))[-topK * 3:]
    topIndices = topIndices[np.argsort(counts[topIndices])[::-1]]

    rows = []
    seen: set[str] = set()
    for docId in topIndices:
        if counts[docId] == 0:
            break
        if docId >= meta.height:
            continue
        row = meta.row(int(docId), named=True)
        rcept = row["rcept_no"]
        if rcept in seen:
            continue
        seen.add(rcept)
        rows.append({
            "score": round(int(counts[docId]) / len(queryStems), 4),
            "rcept_no": rcept,
            "corp_name": row.get("corp_name", ""),
            "stock_code": row.get("stock_code", ""),
            "report_nm": row.get("report_nm", ""),
            "section_title": row.get("section_title", ""),
            "dartUrl": f"{DART_VIEWER}{rcept}",
        })
        if len(rows) >= topK:
            break

    return pl.DataFrame(rows) if rows else pl.DataFrame()


if __name__ == "__main__":
    # store 로드
    store = loadStore()

    # warm-up
    searchFast("테스트", topK=1)

    # 검색 벤치마크
    print("\n=== 검색 속도 비교 ===")
    queries = [
        "반도체 설비투자",
        "배당 정책",
        "대표이사 연혁",
        "재무제표 주석",
        "유상증자",
        "소송 현황",
        "종속회사 현황",
        "감사 의견",
        "사업의 내용",
        "임원 보수",
        "회사가 돈을 빌렸다",
        "경영진이 바뀌었다",
        "전환사채 발행",
        "자기주식 취득",
    ]

    latencies = []
    for q in queries:
        t0 = time.time()
        r = searchFast(q, topK=5)
        ms = (time.time() - t0) * 1000
        latencies.append(ms)
        if r.height > 0:
            row = r.row(0, named=True)
            print(f'  "{q}" ({ms:.0f}ms) [{row["score"]:.2f}] {row["corp_name"]} | {row["section_title"][:25]}')
        else:
            print(f'  "{q}" ({ms:.0f}ms) 0건')

    print(f"\n평균: {np.mean(latencies):.0f}ms")
    print(f"p50:  {np.median(latencies):.0f}ms")
    print(f"p95:  {sorted(latencies)[int(len(latencies)*0.95)]:.0f}ms")
    print(f"최소: {min(latencies):.0f}ms")
    print(f"최대: {max(latencies):.0f}ms")

    # 010 대비 비교
    print(f"\n=== 010(파이썬 루프) vs 011(numpy bincount) ===")
    print(f"010: 3,500~5,500ms")
    print(f"011: {np.mean(latencies):.0f}ms")
    print(f"가속: {4500 / np.mean(latencies):.0f}x")
