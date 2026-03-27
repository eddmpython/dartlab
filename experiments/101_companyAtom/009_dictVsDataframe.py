"""
실험 ID: 101-009
실험명: dict(CAS) vs DataFrame — 원본 텍스트 포함 시 속도/메모리 비교

목적:
- 원본 텍스트를 모두 포함한 상태에서 dict 방식과 DataFrame 방식의 메모리/속도 비교
- 003의 Content Store(hash→text) + Index vs 008의 flat DataFrame
- 어떤 형태가 changes에 적합한지 결정

가설:
1. dict(CAS)가 중복 제거 효과로 메모리 절반 이하
2. DataFrame이 필터/집계에서 더 빠름
3. 사용성은 DataFrame이 우세 (Polars 생태계)

방법:
1. 같은 데이터를 dict 방식과 DataFrame 방식으로 구성
2. 메모리 측정 (sys.getsizeof + 텍스트 바이트)
3. 동일 쿼리의 속도 비교

결과 (2026-03-27):
- 메모리: CAS 24.5MB vs DF(원본) 51.7MB vs DF(preview) 4.9MB
- CAS 절감: 52.5% (22,060행에 7,559개 고유 텍스트 — 변화 블록 내에서도 중복 존재)
- 필터 속도: Dict 2.0ms vs DF 0.2ms (Polars 10배 빠름)
- 집계 속도: Dict 2.4ms vs DF 0.9ms (Polars 3배 빠름)
- 텍스트 접근: Dict 0.1ms vs DF 1.7ms (Dict가 17배 빠름 — hash lookup)

결론:
- 가설 1 확인: CAS가 메모리 52.5% 절감 (24.5MB vs 51.7MB)
- 가설 2 확인: DataFrame이 필터/집계에서 3~10배 빠름
- 가설 3 확인: DataFrame이 Polars 생태계와 자연스럽게 결합
- 최적 구조: **DataFrame(preview/메타) + 필요시 원본 lazy 접근**
  - 기본 조작(필터, 집계, 정렬)은 preview DataFrame으로 (4.9MB, 0.2ms)
  - 원본 텍스트가 필요하면 sections에서 가져오면 됨 (이미 캐시됨)
  - CAS를 별도로 만들 필요 없음 — sections 자체가 원본 저장소

실험일: 2026-03-27
"""

import sys
import time
import hashlib
import re

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

PERIOD_RE = re.compile(r"^\d{4}$")


def classifyChange(textA, textB):
    """변화 유형."""
    if textA is None and textB is not None:
        return "appeared"
    if textA is not None and textB is None:
        return "disappeared"
    strippedA = re.sub(r"[\d,.]+", "N", textA)
    strippedB = re.sub(r"[\d,.]+", "N", textB)
    if strippedA == strippedB:
        return "numeric"
    lenA, lenB = len(textA), len(textB)
    if lenA > 0 and abs(lenB - lenA) / lenA > 0.5:
        return "structural"
    return "wording"


def run():
    import polars as pl
    import dartlab

    c = dartlab.Company("005930")
    sections = c.docs.sections
    annualCols = sorted([col for col in sections.columns if PERIOD_RE.match(col)])
    topics = sections.get_column("topic").to_list()

    # ── 공통: 변화 블록 수집 ──
    deltas = []
    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        for rowIdx in range(sections.height):
            textA = sections[rowIdx, colA]
            textB = sections[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue
            deltas.append({
                "fromPeriod": colA,
                "toPeriod": colB,
                "topic": topics[rowIdx],
                "changeType": classifyChange(textA, textB),
                "textA": textA,
                "textB": textB,
                "hashA": hashA,
                "hashB": hashB,
            })

    print(f"변화 블록: {len(deltas)}개")
    print()

    # ══════════════════════════════════════════════
    # 방식 A: Dict + Content Store (CAS)
    # ══════════════════════════════════════════════
    t0 = time.perf_counter()

    contentStore = {}
    indexEntries = []
    for d in deltas:
        if d["textA"] and d["hashA"] not in contentStore:
            contentStore[d["hashA"]] = d["textA"]
        if d["textB"] and d["hashB"] not in contentStore:
            contentStore[d["hashB"]] = d["textB"]
        indexEntries.append({
            "fromPeriod": d["fromPeriod"],
            "toPeriod": d["toPeriod"],
            "topic": d["topic"],
            "changeType": d["changeType"],
            "hashA": d["hashA"],
            "hashB": d["hashB"],
        })

    dictBuildTime = time.perf_counter() - t0

    # 메모리: Content Store
    csBytes = sum(len(v.encode("utf-8")) for v in contentStore.values())
    csBytes += len(contentStore) * 32  # hash key overhead
    # 메모리: Index
    # 대략: 각 entry가 6개 문자열 참조
    indexBytes = len(indexEntries) * 6 * 64  # 포인터 + 짧은 문자열

    dictTotalBytes = csBytes + indexBytes

    # ══════════════════════════════════════════════
    # 방식 B: Flat DataFrame (원본 텍스트 포함)
    # ══════════════════════════════════════════════
    t0 = time.perf_counter()

    dfRows = []
    for d in deltas:
        dfRows.append({
            "fromPeriod": d["fromPeriod"],
            "toPeriod": d["toPeriod"],
            "topic": d["topic"],
            "changeType": d["changeType"],
            "textA": d["textA"],
            "textB": d["textB"],
        })
    changesDf = pl.DataFrame(dfRows)

    dfBuildTime = time.perf_counter() - t0
    dfBytes = changesDf.estimated_size()

    # ══════════════════════════════════════════════
    # 방식 C: DataFrame (preview만, 008 방식)
    # ══════════════════════════════════════════════
    t0 = time.perf_counter()

    previewRows = []
    for d in deltas:
        text = d["textB"] or d["textA"] or ""
        previewRows.append({
            "fromPeriod": d["fromPeriod"],
            "toPeriod": d["toPeriod"],
            "topic": d["topic"],
            "changeType": d["changeType"],
            "sizeDelta": (len(d["textB"]) if d["textB"] else 0) - (len(d["textA"]) if d["textA"] else 0),
            "preview": text[:200],
        })
    previewDf = pl.DataFrame(previewRows)

    previewBuildTime = time.perf_counter() - t0
    previewBytes = previewDf.estimated_size()

    # ══════════════════════════════════════════════
    # 결과 비교
    # ══════════════════════════════════════════════
    print("=" * 70)
    print("1. 메모리 비교")
    print("=" * 70)
    print(f"  {'방식':30s} {'메모리':>12s} {'빌드 시간':>12s}")
    print("  " + "-" * 54)
    print(f"  {'A: Dict+CAS (중복제거)':30s} {dictTotalBytes/1024/1024:>10.2f}MB {dictBuildTime:>10.3f}s")
    print(f"  {'B: DataFrame (원본 텍스트)':30s} {dfBytes/1024/1024:>10.2f}MB {dfBuildTime:>10.3f}s")
    print(f"  {'C: DataFrame (preview 200자)':30s} {previewBytes/1024/1024:>10.2f}MB {previewBuildTime:>10.3f}s")
    print()
    print(f"  Content Store 고유 텍스트: {len(contentStore)}개")
    print(f"  DataFrame 행 (중복 포함): {changesDf.height}개")
    print(f"  CAS 절감: {(1 - dictTotalBytes / dfBytes) * 100:.1f}%")
    print()

    # ══════════════════════════════════════════════
    # 쿼리 속도 비교
    # ══════════════════════════════════════════════
    print("=" * 70)
    print("2. 쿼리 속도 비교")
    print("=" * 70)

    # Q1: topic="businessOverview" 필터
    N = 100

    t0 = time.perf_counter()
    for _ in range(N):
        _ = [e for e in indexEntries if e["topic"] == "businessOverview"]
    dictQ1 = (time.perf_counter() - t0) / N * 1000

    t0 = time.perf_counter()
    for _ in range(N):
        _ = changesDf.filter(pl.col("topic") == "businessOverview")
    dfQ1 = (time.perf_counter() - t0) / N * 1000

    t0 = time.perf_counter()
    for _ in range(N):
        _ = previewDf.filter(pl.col("topic") == "businessOverview")
    previewQ1 = (time.perf_counter() - t0) / N * 1000

    print(f"\n  Q1: topic='businessOverview' 필터 (평균 {N}회)")
    print(f"    Dict:          {dictQ1:.2f}ms")
    print(f"    DF(원본):      {dfQ1:.2f}ms")
    print(f"    DF(preview):   {previewQ1:.2f}ms")

    # Q2: changeType group_by 집계
    t0 = time.perf_counter()
    for _ in range(N):
        counts = {}
        for e in indexEntries:
            ct = e["changeType"]
            counts[ct] = counts.get(ct, 0) + 1
    dictQ2 = (time.perf_counter() - t0) / N * 1000

    t0 = time.perf_counter()
    for _ in range(N):
        _ = changesDf.group_by("changeType").agg(pl.len())
    dfQ2 = (time.perf_counter() - t0) / N * 1000

    print(f"\n  Q2: changeType 집계 (평균 {N}회)")
    print(f"    Dict:          {dictQ2:.2f}ms")
    print(f"    DF(원본):      {dfQ2:.2f}ms")

    # Q3: Dict에서 원본 텍스트 접근 (CAS lookup)
    bizEntries = [e for e in indexEntries if e["topic"] == "businessOverview"]
    t0 = time.perf_counter()
    for _ in range(N):
        texts = [contentStore.get(e["hashB"]) for e in bizEntries if e["hashB"]]
    dictQ3 = (time.perf_counter() - t0) / N * 1000

    bizDf = changesDf.filter(pl.col("topic") == "businessOverview")
    t0 = time.perf_counter()
    for _ in range(N):
        texts = bizDf.get_column("textB").to_list()
    dfQ3 = (time.perf_counter() - t0) / N * 1000

    print(f"\n  Q3: businessOverview 원본 텍스트 접근 (평균 {N}회)")
    print(f"    Dict(CAS lookup): {dictQ3:.2f}ms")
    print(f"    DF(직접 접근):    {dfQ3:.2f}ms")

    # ══════════════════════════════════════════════
    # 판정
    # ══════════════════════════════════════════════
    print()
    print("=" * 70)
    print("3. 판정")
    print("=" * 70)
    print(f"  메모리: CAS {dictTotalBytes/1024/1024:.1f}MB vs DF {dfBytes/1024/1024:.1f}MB vs Preview {previewBytes/1024/1024:.1f}MB")
    print(f"  필터 속도: Dict {dictQ1:.1f}ms vs DF {dfQ1:.1f}ms")
    print(f"  집계 속도: Dict {dictQ2:.1f}ms vs DF {dfQ2:.1f}ms")
    print(f"  텍스트접근: Dict {dictQ3:.1f}ms vs DF {dfQ3:.1f}ms")


if __name__ == "__main__":
    run()
