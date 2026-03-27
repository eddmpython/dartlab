"""
실험 ID: 101-001
실험명: sections 텍스트 중복률 및 컬럼 비중 측정

목적:
- sections DataFrame에서 연도별 텍스트 중복이 실제로 얼마나 되는지 정량화
- 메타/기계용 컬럼 vs 사람이 읽는 컬럼의 메모리 비중 측정
- CAS(Content-Addressable Storage) 방식 적용 시 압축률 예측

가설:
1. 연도별 동일 텍스트 비율이 30% 이상일 것
2. 메타 컬럼이 전체 메모리의 50% 이상을 차지할 것
3. hash dedup만으로도 40%+ 용량 감소 가능할 것

방법:
1. 삼성전자(005930) sections 로드
2. 기간별 텍스트 컬럼 추출 → hash 비교로 동일 텍스트 비율 측정
3. 메타 컬럼 / 기간 컬럼 각각의 메모리 사용량 측정
4. unique hash 개수 vs 전체 셀 수 → CAS 압축률 추정

결과 (2026-03-27):
- 14,158행 × 70열 (8.32 MB Polars 내부 압축)
- 기간 40열, 메타 30열
- Null 87.3% (566,320셀 중 494,143 비어있음)
- non-null 72,177셀 → 고유 텍스트 18,872개 (73.9% 중복)
- 원본 텍스트 97.32MB → CAS 후 50.29MB (48.3% 압축)
- 메타 컬럼이 전체 메모리의 73.2% (6.09MB), 기간 컬럼 26.8% (2.23MB)
- Optional 메타(variants, semantic) 10개가 메타의 78.4% (4.78MB)

결론:
- 가설 1 확인: 중복률 73.9% (30% 이상 가설 대폭 초과)
- 가설 2 확인: 메타 컬럼 73.2% (50% 이상 가설 초과)
- 가설 3 확인: CAS로 48.3% 압축 (40% 가설 초과)
- sections는 "거의 빈 거대한 스프레드시트" — 87% Null, 채워진 곳의 74% 중복

실험일: 2026-03-27
"""

import sys
import hashlib

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")


def run():
    import dartlab

    c = dartlab.Company("005930")
    df = c.docs.sections

    print("=" * 70)
    print("1. DataFrame 기본 정보")
    print("=" * 70)
    print(f"  행: {df.height}, 열: {df.width}")
    print(f"  전체 추정 메모리: {df.estimated_size('mb'):.2f} MB")
    print()

    # 기간 컬럼 vs 메타 컬럼 분리
    import re
    periodPattern = re.compile(r"^\d{4}(Q[1-3])?$")
    periodCols = [c for c in df.columns if periodPattern.match(c)]
    metaCols = [c for c in df.columns if c not in periodCols]

    print(f"  기간 컬럼 ({len(periodCols)}개): {periodCols}")
    print(f"  메타 컬럼 ({len(metaCols)}개): {metaCols}")
    print()

    # 2. 메모리 비중
    print("=" * 70)
    print("2. 컬럼별 메모리 비중")
    print("=" * 70)
    metaDf = df.select(metaCols)
    periodDf = df.select(periodCols)
    metaMb = metaDf.estimated_size("mb")
    periodMb = periodDf.estimated_size("mb")
    totalMb = df.estimated_size("mb")

    print(f"  메타 컬럼: {metaMb:.2f} MB ({metaMb/totalMb*100:.1f}%)")
    print(f"  기간 컬럼: {periodMb:.2f} MB ({periodMb/totalMb*100:.1f}%)")
    print(f"  합계: {totalMb:.2f} MB")
    print()

    # 3. 연도별 텍스트 중복률
    print("=" * 70)
    print("3. 연도별 텍스트 중복 분석")
    print("=" * 70)

    allTexts = []  # (row, col, text)
    hashSet = {}   # hash -> text (대표값)
    totalCells = 0
    nonNullCells = 0
    duplicateCells = 0

    for col in periodCols:
        series = df.get_column(col)
        for i, val in enumerate(series.to_list()):
            totalCells += 1
            if val is None:
                continue
            nonNullCells += 1
            h = hashlib.md5(val.encode("utf-8")).hexdigest()
            if h in hashSet:
                duplicateCells += 1
            else:
                hashSet[h] = val
            allTexts.append((i, col, h))

    print(f"  전체 셀: {totalCells}")
    print(f"  비어있지 않은 셀: {nonNullCells}")
    print(f"  Null 셀: {totalCells - nonNullCells} ({(totalCells - nonNullCells)/totalCells*100:.1f}%)")
    print(f"  고유 텍스트 블록: {len(hashSet)}")
    print(f"  중복 텍스트 셀: {duplicateCells} ({duplicateCells/nonNullCells*100:.1f}% of non-null)")
    print()

    # 4. CAS 압축률 추정
    print("=" * 70)
    print("4. CAS 압축률 추정")
    print("=" * 70)
    totalTextBytes = sum(len(t[2].encode("utf-8")) for t in allTexts if t[2])  # hash는 32bytes
    # 원본 텍스트 총 바이트
    originalBytes = 0
    uniqueBytes = 0
    for col in periodCols:
        series = df.get_column(col)
        for val in series.to_list():
            if val is not None:
                originalBytes += len(val.encode("utf-8"))

    for h, text in hashSet.items():
        uniqueBytes += len(text.encode("utf-8"))

    pointerOverhead = nonNullCells * 32  # hash pointer per cell

    print(f"  원본 텍스트 총량: {originalBytes / 1024 / 1024:.2f} MB")
    print(f"  고유 텍스트 총량: {uniqueBytes / 1024 / 1024:.2f} MB")
    print(f"  포인터 오버헤드: {pointerOverhead / 1024:.2f} KB")
    print(f"  CAS 후 예상 크기: {(uniqueBytes + pointerOverhead) / 1024 / 1024:.2f} MB")
    print(f"  압축률: {(1 - (uniqueBytes + pointerOverhead) / originalBytes) * 100:.1f}%")
    print()

    # 5. 중복 패턴 분류
    print("=" * 70)
    print("5. 중복 패턴 TOP 10 (가장 많이 반복되는 텍스트)")
    print("=" * 70)
    from collections import Counter
    hashCounts = Counter()
    for _, _, h in allTexts:
        hashCounts[h] += 1

    for h, count in hashCounts.most_common(10):
        if h in hashSet:
            preview = hashSet[h][:80].replace("\n", "\\n")
            print(f"  [{count}회] {preview}...")
    print()

    # 6. topic별 중복률
    print("=" * 70)
    print("6. topic별 기간간 중복률 (상위 15)")
    print("=" * 70)
    topicCol = "topic" if "topic" in df.columns else None
    if topicCol:
        topics = df.get_column(topicCol).to_list()
        topicStats = {}  # topic -> (total, dup)
        for row_i, col, h in allTexts:
            topic = topics[row_i]
            if topic not in topicStats:
                topicStats[topic] = {"total": 0, "hashes": set(), "dup": 0}
            topicStats[topic]["total"] += 1
            if h in topicStats[topic]["hashes"]:
                topicStats[topic]["dup"] += 1
            else:
                topicStats[topic]["hashes"].add(h)

        ranked = sorted(
            topicStats.items(),
            key=lambda x: x[1]["dup"] / max(x[1]["total"], 1),
            reverse=True,
        )
        for topic, stats in ranked[:15]:
            rate = stats["dup"] / max(stats["total"], 1) * 100
            print(f"  {topic:40s} {stats['dup']:3d}/{stats['total']:3d} ({rate:.0f}%)")

    print()
    print("=" * 70)
    print("7. 메타 컬럼 상세 메모리")
    print("=" * 70)
    for col in metaCols:
        colDf = df.select(col)
        mb = colDf.estimated_size("kb")
        print(f"  {col:40s} {mb:8.1f} KB")


if __name__ == "__main__":
    run()
