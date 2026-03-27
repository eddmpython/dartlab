"""
실험 ID: 101-005
실험명: 다중 기업 검증 — CompanyAtom 패턴의 업종/규모 일반화

목적:
- 삼성전자에서 발견된 CompanyAtom 패턴이 업종/규모 무관하게 성립하는지 검증
- 금융업(신한지주)의 section 구조 특이성 확인
- CAS 압축률, 중복률, 변화 유형 분포의 기업간 비교

가설:
1. Null 비율 80%+, 텍스트 중복률 60%+, CAS 압축률 40%+ 가 업종 무관 성립
2. 금융업은 revenue/매출 관련 topic 부재, 대신 금융 특화 topic 존재
3. 변화 유형 분포(등장/소멸/문구/구조/숫자) 패턴이 5개 기업에서 유사

방법:
1. 5개 기업 순차 로드 (메모리 안전: 1개 처리 후 해제)
2. 각 기업: Null률, 중복률, CAS 압축률, 변화유형 분포, 정보밀도 측정
3. 기업간 비교 테이블 + 금융업 특이성 분석

결과 (2026-03-27):
- 5개 기업 비교:
  | 지표 | 삼성전자 | 신한지주 | 현대차 | 카카오 | LG에너지 |
  |------|---------|---------|--------|--------|---------|
  | 행수 | 14,158 | 26,167 | 18,337 | 24,650 | 8,769 |
  | Null% | 87.3 | 89.2 | 89.0 | 92.6 | 82.3 |
  | 중복률% | 73.9 | 75.4 | 75.4 | 70.9 | 72.0 |
  | CAS압축% | 48.3 | 47.8 | 48.8 | 49.6 | 50.3 |
  | 변화블록 | 22,060 | 40,854 | 25,908 | 34,007 | 10,257 |
  | 정보밀도% | 30.5 | 52.4 | 31.3 | 35.1 | 38.4 |
- 변화유형: 5개 기업 모두 appeared(30-38%)+disappeared(34-40%) 합산 65-77%로 지배적
- 금융업(신한지주): salesOrder/rawMaterial/rndDetail 없음, 대신 방카슈랑스/펀드상품/금융건전성 topic 존재
- 신한지주 정보밀도 52.4%로 최대 — 금융업이 텍스트 갱신 빈도가 높음

결론:
- 가설 1 확인: Null 82-93%, 중복 71-75%, CAS 48-50% — 전 업종 성립
- 가설 2 확인: 금융업은 제조업 topic(salesOrder, rawMaterial) 없고, 금융상품 topic 별도 존재
- 가설 3 확인: 변화유형 5종 분포가 업종 무관 유사 패턴 (appeared+disappeared 지배)
- CompanyAtom 패턴은 **업종/규모 불변 법칙**으로 일반화 가능

실험일: 2026-03-27
"""

import sys
import gc
import hashlib
import re
from collections import defaultdict

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

TARGETS = [
    ("005930", "삼성전자"),
    ("055550", "신한지주"),
    ("005380", "현대차"),
    ("035720", "카카오"),
    ("373220", "LG에너지솔루션"),
]

PERIOD_RE = re.compile(r"^\d{4}(Q[1-3])?$")
ANNUAL_RE = re.compile(r"^\d{4}$")


def classifyChange(textA, textB):
    """변화 유형 분류 (004에서 재사용)."""
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


def measureCompany(stockCode):
    """한 기업의 sections 핵심 지표 측정."""
    import dartlab

    c = dartlab.Company(stockCode)
    df = c.docs.sections

    periodCols = sorted([col for col in df.columns if PERIOD_RE.match(col)])
    annualCols = sorted([col for col in periodCols if ANNUAL_RE.match(col)])
    metaCols = [col for col in df.columns if col not in periodCols]
    topics = set(df.get_column("topic").to_list()) if "topic" in df.columns else set()

    # 기본 형상
    result = {
        "rows": df.height,
        "cols": df.width,
        "periodCols": len(periodCols),
        "metaCols": len(metaCols),
        "topics": topics,
        "topicCount": len(topics),
    }

    # Null 비율
    totalCells = df.height * len(periodCols)
    nonNullCells = 0
    hashSet = {}
    duplicateCells = 0
    originalBytes = 0

    for col in periodCols:
        series = df.get_column(col)
        for val in series.to_list():
            if val is None:
                continue
            nonNullCells += 1
            originalBytes += len(val.encode("utf-8"))
            h = hashlib.md5(val.encode("utf-8")).hexdigest()
            if h in hashSet:
                duplicateCells += 1
            else:
                hashSet[h] = len(val.encode("utf-8"))

    uniqueBytes = sum(hashSet.values())
    pointerOverhead = nonNullCells * 32

    result["totalCells"] = totalCells
    result["nonNullCells"] = nonNullCells
    result["nullRate"] = (totalCells - nonNullCells) / totalCells * 100 if totalCells > 0 else 0
    result["uniqueBlocks"] = len(hashSet)
    result["dupRate"] = duplicateCells / nonNullCells * 100 if nonNullCells > 0 else 0
    result["originalMB"] = originalBytes / 1024 / 1024
    result["casMB"] = (uniqueBytes + pointerOverhead) / 1024 / 1024
    result["casCompressionRate"] = (1 - (uniqueBytes + pointerOverhead) / originalBytes) * 100 if originalBytes > 0 else 0

    # 변화 유형 분포
    changeCounts = defaultdict(int)
    totalChanges = 0
    totalChangeBytes = 0
    topicList = df.get_column("topic").to_list() if "topic" in df.columns else [None] * df.height

    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        for rowIdx in range(df.height):
            textA = df[rowIdx, colA]
            textB = df[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue
            changeType = classifyChange(textA, textB)
            changeCounts[changeType] += 1
            totalChanges += 1
            if textB:
                totalChangeBytes += len(textB.encode("utf-8"))

    result["totalChanges"] = totalChanges
    result["changeCounts"] = dict(changeCounts)
    result["infoDensity"] = totalChangeBytes / originalBytes * 100 if originalBytes > 0 else 0

    # 명시적 해제
    del df, c
    gc.collect()

    return result


def printComparisonTable(results):
    """기업간 비교 테이블 출력."""
    print("=" * 90)
    print("기업간 비교 테이블")
    print("=" * 90)

    header = f"{'지표':20s}"
    for r in results:
        header += f" {r['name']:>12s}"
    print(header)
    print("-" * 90)

    metrics = [
        ("행수", "rows", "d"),
        ("열수", "cols", "d"),
        ("기간 컬럼", "periodCols", "d"),
        ("topic 수", "topicCount", "d"),
        ("Null 비율(%)", "nullRate", ".1f"),
        ("텍스트 중복률(%)", "dupRate", ".1f"),
        ("원본 텍스트(MB)", "originalMB", ".1f"),
        ("CAS 후(MB)", "casMB", ".1f"),
        ("CAS 압축률(%)", "casCompressionRate", ".1f"),
        ("변화 블록 수", "totalChanges", "d"),
        ("정보 밀도(%)", "infoDensity", ".1f"),
    ]

    for label, key, fmt in metrics:
        row = f"{label:20s}"
        for r in results:
            val = r.get(key, 0)
            row += f" {val:>12{fmt}}"
        print(row)
    print()

    # 변화 유형 분포
    print("=" * 90)
    print("변화 유형 분포 (%)")
    print("=" * 90)
    types = ["appeared", "disappeared", "wording", "structural", "numeric"]
    header = f"{'유형':15s}"
    for r in results:
        header += f" {r['name']:>12s}"
    print(header)
    print("-" * 90)

    for t in types:
        row = f"{t:15s}"
        for r in results:
            total = r["totalChanges"]
            cnt = r["changeCounts"].get(t, 0)
            pct = cnt / total * 100 if total > 0 else 0
            row += f" {pct:>11.1f}%"
        print(row)
    print()


def printFinancialSpecifics(results):
    """금융업 특이성 분석."""
    print("=" * 90)
    print("금융업(신한지주) 특이성")
    print("=" * 90)

    # 삼성전자 vs 신한지주 topic 비교
    samsung = next(r for r in results if r["code"] == "005930")
    shinhan = next(r for r in results if r["code"] == "055550")

    samsungTopics = samsung["topics"]
    shinhanTopics = shinhan["topics"]

    onlyShinhan = shinhanTopics - samsungTopics
    onlySamsung = samsungTopics - shinhanTopics
    common = samsungTopics & shinhanTopics

    print(f"  공통 topic: {len(common)}개")
    print(f"  삼성전자에만: {len(onlySamsung)}개")
    if onlySamsung:
        for t in sorted(onlySamsung):
            print(f"    - {t}")
    print(f"  신한지주에만: {len(onlyShinhan)}개")
    if onlyShinhan:
        for t in sorted(onlyShinhan):
            print(f"    - {t}")
    print()


def run():
    from dartlab.core.memory import get_memory_mb

    results = []
    for code, name in TARGETS:
        memBefore = get_memory_mb()
        print(f"\n{'='*60}")
        print(f"측정 중: {name} ({code}) — Memory: {memBefore:.0f}MB")
        print(f"{'='*60}")

        result = measureCompany(code)
        result["name"] = name
        result["code"] = code
        results.append(result)

        gc.collect()
        memAfter = get_memory_mb()
        print(f"  완료: {result['rows']}행, Null {result['nullRate']:.1f}%, "
              f"중복 {result['dupRate']:.1f}%, CAS {result['casCompressionRate']:.1f}%")
        print(f"  Memory: {memBefore:.0f}MB → {memAfter:.0f}MB")

    print("\n\n")
    printComparisonTable(results)
    printFinancialSpecifics(results)

    # 요약
    print("=" * 90)
    print("패턴 일반화 검증")
    print("=" * 90)
    allNull = [r["nullRate"] for r in results]
    allDup = [r["dupRate"] for r in results]
    allCas = [r["casCompressionRate"] for r in results]
    allDensity = [r["infoDensity"] for r in results]

    print(f"  Null 비율 범위: {min(allNull):.1f}% ~ {max(allNull):.1f}%  (가설: 80%+)")
    print(f"  중복률 범위:    {min(allDup):.1f}% ~ {max(allDup):.1f}%  (가설: 60%+)")
    print(f"  CAS 압축률 범위: {min(allCas):.1f}% ~ {max(allCas):.1f}%  (가설: 40%+)")
    print(f"  정보밀도 범위:  {min(allDensity):.1f}% ~ {max(allDensity):.1f}%")

    allOk = min(allNull) >= 80 and min(allDup) >= 60 and min(allCas) >= 40
    print(f"\n  결론: 패턴 일반화 {'성립 ✓' if allOk else '부분 성립 — 상세 분석 필요'}")


if __name__ == "__main__":
    run()
