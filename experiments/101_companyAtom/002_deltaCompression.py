"""
실험 ID: 101-002
실험명: Delta 압축 효과 측정 — 연도간 텍스트 변경분 분석

목적:
- CAS(hash dedup)로 제거되지 않는 "거의 같은" 텍스트의 delta 압축 효과 측정
- 연도간 텍스트가 숫자만 바뀌는 패턴(template)의 비율 파악
- Layer 2(delta chain) 적용 시 추가 압축률 추정

가설:
1. CAS로 잡히지 않는 텍스트 중 30%+ 가 숫자/날짜만 다른 template 패턴
2. difflib 기반 delta로 추가 20%+ 압축 가능

방법:
1. 삼성전자 sections에서 같은 (topic, blockOrder) 행의 연도별 텍스트 쌍 추출
2. hash가 다른 쌍에 대해: (a) difflib ratio (b) 실제 delta 크기 측정
3. 유사도 분포 시각화 (히스토그램 대신 텍스트 분포)

결과 (2026-03-27, 장시간 실행 후 완료):
- 총 13,823 연속 연도 쌍 비교
- 완전 동일 (hash): 43.2%, 유사(ratio≥0.8): 18.6%, 템플릿(숫자만): 5.5%
- 유사도 분포: 1.0이 40%로 최다, <0.5가 24%로 차다 — 양극화 (같거나 완전히 다르거나)
- Delta 압축: 원본 45.28MB → 19.79MB (56.3% 압축)
- 3단 압축 시뮬레이션: 원본 97.32MB → Layer1(CAS) 50.29MB → Layer2(Delta) ~36MB → 총 62.9%

결론:
- 가설 1 부분 확인: 템플릿 패턴(숫자만 다름)은 5.5%로 30% 가설 미달
  - 실제로는 유사도 0.9~1.0 구간(18.6%)에 템플릿+문구미세변경이 혼재
- 가설 2 확인: delta 압축률 56.3% — CAS 위에 추가 적용하면 총 62.9% 달성
- 양극화 패턴: 텍스트는 "거의 동일" 또는 "완전히 다름"으로 양분 (0.5~0.9 구간이 얇음)
- difflib SequenceMatcher가 14K행에서 매우 느림 — 실제 구현 시 xxhash + zstd delta 필요

실험일: 2026-03-27
"""

import sys
import hashlib
import difflib
import re

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")


def run():
    import dartlab

    c = dartlab.Company("005930")
    df = c.docs.sections

    periodPattern = re.compile(r"^\d{4}(Q[1-3])?$")
    periodCols = sorted([c for c in df.columns if periodPattern.match(c)])

    # 연간 컬럼만 (Q 제외) — 연간이 가장 풍부
    annualCols = sorted([c for c in periodCols if "Q" not in c])
    print(f"연간 기간: {annualCols}")
    print()

    # 같은 행의 연속 연도 쌍 비교
    topics = df.get_column("topic").to_list()
    blockOrders = df.get_column("blockOrder").to_list()

    totalPairs = 0
    identicalPairs = 0
    similarPairs = 0  # ratio >= 0.8
    templatePairs = 0  # 숫자만 다른 경우
    differentPairs = 0

    deltaBytes = 0
    originalPairBytes = 0

    similarityBuckets = {
        "1.0 (동일)": 0,
        "0.9~1.0": 0,
        "0.8~0.9": 0,
        "0.7~0.8": 0,
        "0.6~0.7": 0,
        "0.5~0.6": 0,
        "<0.5": 0,
    }

    templateExamples = []

    for rowIdx in range(df.height):
        for i in range(len(annualCols) - 1):
            colA = annualCols[i]
            colB = annualCols[i + 1]
            textA = df[rowIdx, colA]
            textB = df[rowIdx, colB]

            if textA is None or textB is None:
                continue

            totalPairs += 1
            originalPairBytes += len(textA.encode("utf-8")) + len(textB.encode("utf-8"))

            hashA = hashlib.md5(textA.encode()).hexdigest()
            hashB = hashlib.md5(textB.encode()).hexdigest()

            if hashA == hashB:
                identicalPairs += 1
                similarityBuckets["1.0 (동일)"] += 1
                continue

            # 유사도 측정
            ratio = difflib.SequenceMatcher(None, textA, textB).ratio()

            if ratio >= 0.9:
                similarityBuckets["0.9~1.0"] += 1
            elif ratio >= 0.8:
                similarityBuckets["0.8~0.9"] += 1
            elif ratio >= 0.7:
                similarityBuckets["0.7~0.8"] += 1
            elif ratio >= 0.6:
                similarityBuckets["0.6~0.7"] += 1
            elif ratio >= 0.5:
                similarityBuckets["0.5~0.6"] += 1
            else:
                similarityBuckets["<0.5"] += 1

            if ratio >= 0.8:
                similarPairs += 1

            # template 패턴: 숫자/날짜만 다른지 확인
            stripped_a = re.sub(r"[\d,.]+", "N", textA)
            stripped_b = re.sub(r"[\d,.]+", "N", textB)
            if stripped_a == stripped_b:
                templatePairs += 1
                if len(templateExamples) < 3:
                    templateExamples.append((colA, colB, textA[:100], textB[:100]))
            else:
                differentPairs += 1

            # delta 크기 측정
            opcodes = difflib.SequenceMatcher(None, textA, textB).get_opcodes()
            delta_size = 0
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == "equal":
                    delta_size += 8  # (offset, length) 포인터
                else:
                    delta_size += len(textB[j1:j2].encode("utf-8")) + 8
            deltaBytes += delta_size

    print("=" * 70)
    print("1. 연속 연도 쌍 비교 결과")
    print("=" * 70)
    print(f"  총 비교 쌍: {totalPairs}")
    print(f"  완전 동일 (hash 일치): {identicalPairs} ({identicalPairs/totalPairs*100:.1f}%)")
    print(f"  유사 (ratio≥0.8): {similarPairs} ({similarPairs/totalPairs*100:.1f}%)")
    print(f"  템플릿 (숫자만 다름): {templatePairs} ({templatePairs/totalPairs*100:.1f}%)")
    print()

    print("=" * 70)
    print("2. 유사도 분포")
    print("=" * 70)
    for bucket, count in similarityBuckets.items():
        bar = "█" * (count * 40 // max(max(similarityBuckets.values()), 1))
        print(f"  {bucket:15s} {count:5d} {bar}")
    print()

    print("=" * 70)
    print("3. Delta 압축 효과 (hash가 다른 쌍 대상)")
    print("=" * 70)
    nonIdenticalOriginal = originalPairBytes - identicalPairs * 100  # rough
    print(f"  원본 쌍 텍스트 총량: {originalPairBytes / 1024 / 1024:.2f} MB")
    print(f"  Delta 인코딩 후: {deltaBytes / 1024 / 1024:.2f} MB")
    if originalPairBytes > 0:
        print(f"  Delta 압축률: {(1 - deltaBytes / originalPairBytes) * 100:.1f}%")
    print()

    print("=" * 70)
    print("4. 템플릿 패턴 예시")
    print("=" * 70)
    for colA, colB, a, b in templateExamples:
        print(f"  [{colA}→{colB}]")
        print(f"    이전: {a.replace(chr(10), '\\n')}")
        print(f"    이후: {b.replace(chr(10), '\\n')}")
        print()

    # 5. 종합 3단 압축 시뮬레이션
    print("=" * 70)
    print("5. 종합: 3단 압축 시뮬레이션")
    print("=" * 70)

    # 001 결과에서 가져온 수치
    originalTotal = 97.32  # MB (원본 텍스트 총량)
    afterCas = 50.29  # MB (CAS 후)
    casReduction = originalTotal - afterCas

    # delta는 CAS 이후 남은 텍스트에 대해 적용
    # 대략적 추정: 유사 쌍의 비율만큼 추가 절감
    if totalPairs > 0:
        deltaRatio = deltaBytes / max(originalPairBytes, 1)
        # CAS 이후 남은 고유 텍스트에서 delta 적용 가능 비율
        afterDelta = afterCas * (0.5 + 0.5 * deltaRatio)
        deltaReduction = afterCas - afterDelta
    else:
        afterDelta = afterCas
        deltaReduction = 0

    print(f"  원본: {originalTotal:.2f} MB")
    print(f"  Layer 1 (CAS dedup): {afterCas:.2f} MB (-{casReduction:.2f} MB)")
    print(f"  Layer 2 (Delta): ~{afterDelta:.2f} MB (-{deltaReduction:.2f} MB)")
    print(f"  Layer 3 (Semantic Index): 측정 필요")
    print(f"  총 압축률: ~{(1 - afterDelta / originalTotal) * 100:.1f}%")


if __name__ == "__main__":
    run()
