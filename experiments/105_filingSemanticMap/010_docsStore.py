"""실험 105-010: docs(사업보고서) 전체 → stem ID 역인덱스 store 구축

실험 ID: 105-010
실험명: 2,567종목 사업보고서 490만 섹션을 stem ID 역인덱스로 구축

목적:
- allFilings(수시공시 9K) 뿐 아니라 docs(사업보고서 490만)도 검색 가능하게
- agiPath stem ID + CSR 방식으로 극악 축소
- 490만 행에서 검색 속도 실측

가설:
1. 배치 빌드 (100종목씩) → OOM 방지
2. 인덱스 크기: 490만/9K × 350KB ≈ ~190MB (stemIndex.npz)
3. 검색 속도: < 10ms (CSR numpy 연산)
4. "삼성전자 반도체 설비투자" 같은 사업보고서 내용 검색 가능

방법:
1. docs parquet 100개씩 배치 로드
2. report_type + section_title에서 ngram 추출
3. stem ID 역인덱스 누적 구축
4. 최종 CSR numpy 저장
5. 검색 테스트

결과:
- 구축: 3,991,239문서, 5,585 stems, 218초 (3.6분)
- 인덱스 크기: stemIndex 317.7MB + stemDict 0.1MB + meta 1.1MB = 319MB
- 빌드 메모리: +1,184MB (1.2GB) — OOM 없이 완료
- 검색 속도: 3.5~5.5초 — **느림** (CSR numpy 순회가 400만 docId에서 병목)
- 검색 품질: 동작 — "배당 정책"→배당 섹션, "재무제표 주석"→주석 섹션, "사업의 내용"→정확 매칭
- 문제: 3~5초는 실시간 사용 불가. numpy 순차 루프가 병목.

결론:
- 400만 문서 역인덱스 구축 가능 확인 — 318MB, 3.6분
- 검색 품질은 좋으나 **속도가 병목** (3~5초)
- CSR docIds를 numpy 파이썬 루프로 순회하는 게 원인
- 개선 방향: (A) numpy vectorized 연산으로 교체, (B) bitmap/bitarray, (C) 고빈도 stem 제외
- allFilings(9K)와 달리 docs(400만)는 규모가 근본적으로 다름

실험일: 2026-03-31
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl


def _tokenize(text: str) -> set[str]:
    """bigram + trigram."""
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i: i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i: i + 3] for i in range(len(text) - 2))
    return tokens


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


def expandQuery(query):
    expanded = query
    for phrase, syns in SYNONYMS.items():
        if phrase in query:
            expanded += " " + " ".join(syns)
    return expanded


STORE_DIR = Path("experiments/105_filingSemanticMap/docsStore")
DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="


def buildDocsStore():
    """docs 전체 → stem ID 역인덱스. 배치 처리로 OOM 방지."""
    docsDir = Path("data/dart/docs")
    files = sorted(docsDir.glob("*.parquet"))
    print(f"docs 파일: {len(files)}개")

    stemToId: dict[str, int] = {}
    nextId = 0
    invertedIndex: dict[int, list[int]] = defaultdict(list)

    # 메타 수집 (검색 결과 표시용)
    allMeta: list[dict] = []
    globalDocId = 0
    batchSize = 100

    t0 = time.time()

    for batchStart in range(0, len(files), batchSize):
        batchFiles = files[batchStart: batchStart + batchSize]
        for f in batchFiles:
            try:
                df = pl.read_parquet(f, columns=[
                    "rcept_no", "corp_code", "corp_name", "stock_code",
                    "report_type", "section_title", "section_order",
                ])
            except Exception:
                continue

            for row in df.iter_rows(named=True):
                reportNm = row.get("report_type", "")
                sectionTitle = row.get("section_title", "") or ""
                text = f"{reportNm} {sectionTitle}"

                tokens = _tokenize(text)
                seenStems: set[int] = set()
                for token in tokens:
                    if token not in stemToId:
                        stemToId[token] = nextId
                        nextId += 1
                    stemId = stemToId[token]
                    if stemId not in seenStems:
                        seenStems.add(stemId)
                        invertedIndex[stemId].append(globalDocId)

                allMeta.append({
                    "rcept_no": row["rcept_no"],
                    "corp_code": row.get("corp_code", ""),
                    "corp_name": row.get("corp_name", ""),
                    "stock_code": row.get("stock_code", ""),
                    "report_nm": reportNm,
                    "section_title": sectionTitle,
                    "section_order": row.get("section_order", 0),
                })
                globalDocId += 1

        elapsed = time.time() - t0
        print(f"  [{batchStart + len(batchFiles)}/{len(files)}] "
              f"{globalDocId:,}문서, {nextId:,} stems, {elapsed:.0f}초")

    # CSR 저장
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    offsets = [0]
    flatDocIds = []
    for stemId in range(nextId):
        docList = invertedIndex.get(stemId, [])
        flatDocIds.extend(docList)
        offsets.append(len(flatDocIds))

    np.savez_compressed(
        STORE_DIR / "stemIndex.npz",
        offsets=np.array(offsets, dtype=np.int32),
        docIds=np.array(flatDocIds, dtype=np.int32),
    )

    with open(STORE_DIR / "stemDict.json", "w", encoding="utf-8") as f:
        json.dump(stemToId, f, ensure_ascii=False)

    metaDf = pl.DataFrame(allMeta)
    metaDf.write_parquet(STORE_DIR / "meta.parquet")

    elapsed = time.time() - t0

    npzSize = (STORE_DIR / "stemIndex.npz").stat().st_size / 1024 / 1024
    dictSize = (STORE_DIR / "stemDict.json").stat().st_size / 1024 / 1024
    metaSize = (STORE_DIR / "meta.parquet").stat().st_size / 1024 / 1024
    print(f"\n완료: {globalDocId:,}문서, {nextId:,} stems, {elapsed:.0f}초")
    print(f"stemIndex: {npzSize:.1f}MB, stemDict: {dictSize:.1f}MB, meta: {metaSize:.1f}MB")
    print(f"합계: {npzSize + dictSize + metaSize:.1f}MB")

    return globalDocId


def searchDocsStore(query: str, topK: int = 5):
    """docs store 검색."""
    loaded = np.load(STORE_DIR / "stemIndex.npz")
    offsets = loaded["offsets"]
    docIds = loaded["docIds"]
    with open(STORE_DIR / "stemDict.json", "r", encoding="utf-8") as f:
        stemToId = json.load(f)
    meta = pl.read_parquet(STORE_DIR / "meta.parquet")

    expanded = expandQuery(query)
    tokens = list(_tokenize(expanded))
    queryStems = [stemToId[t] for t in tokens if t in stemToId]
    if not queryStems:
        return pl.DataFrame()

    scores: dict[int, int] = defaultdict(int)
    for stemId in queryStems:
        start = offsets[stemId]
        end = offsets[stemId + 1]
        for did in docIds[start:end]:
            scores[did] += 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    rows = []
    seen: set[str] = set()
    for docId, matchCount in ranked:
        if docId >= meta.height:
            continue
        row = meta.row(docId, named=True)
        rcept = row["rcept_no"]
        if rcept in seen:
            continue
        seen.add(rcept)
        rows.append({
            "score": round(matchCount / len(queryStems), 4),
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
    import psutil

    proc = psutil.Process()
    mem0 = proc.memory_info().rss / 1024 / 1024
    print(f"시작 메모리: {mem0:.0f}MB\n")

    # 빌드
    count = buildDocsStore()

    mem1 = proc.memory_info().rss / 1024 / 1024
    print(f"\n빌드 후 메모리: {mem1:.0f}MB (+{mem1 - mem0:.0f}MB)")

    # 검색 테스트
    print("\n=== docs store 검색 ===")
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
    ]
    for q in queries:
        t0 = time.time()
        r = searchDocsStore(q, topK=3)
        ms = (time.time() - t0) * 1000
        if r.height > 0:
            row = r.row(0, named=True)
            print(f'  "{q}" ({ms:.0f}ms) [{row["score"]:.2f}] {row["corp_name"]} | {row["report_nm"][:25]} | {row["section_title"][:20]}')
        else:
            print(f'  "{q}" ({ms:.0f}ms) 0건')

    mem2 = proc.memory_info().rss / 1024 / 1024
    print(f"\n검색 후 메모리: {mem2:.0f}MB")
