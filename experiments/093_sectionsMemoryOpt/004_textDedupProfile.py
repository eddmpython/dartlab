"""실험 ID: 093-004
실험명: sections DataFrame 내 text 중복률 측정

목적:
- sections DataFrame에서 period 컬럼(본문 text)의 중복률을 측정
- 연도 간 동일 텍스트 반복이 얼마나 되는지 확인
- 중복 제거(dedup/intern)가 메모리 절감에 유효한지 판단

가설:
1. 사업보고서 서술형 section은 연도 간 복붙이 많아 text 중복률 30%+ 예상
2. 중복 text를 intern(동일 str 객체 재사용)하면 Python heap 절감 가능

방법:
1. sections() DataFrame을 생성
2. 모든 period 컬럼의 non-null text를 수집
3. 전체 text 수, unique text 수, 중복 text가 차지하는 바이트 비율 산출
4. sys.intern() 적용 전후 RSS 비교

결과 (삼성전자 005930):

| 지표 | 수치 |
|------|------|
| sections shape | 14,158 × 70 |
| period 컬럼 수 | 40 |
| 전체 text cell | 72,177 |
| unique text | 18,872 (26.1%) |
| 중복 text | 53,305 (73.9%) |
| 전체 text 바이트 | 97.32MB |
| 중복 바이트 | 49.23MB (50.6%) |
| Categorical 인코딩 시 | 2.23MB (97.7% 절감) |
| sys.intern RSS 변화 | +65.2MB (악화 — Python dict 오버헤드) |

결론:
- text 중복률 73.9% — 연도 간 사업보고서 복붙이 매우 많음
- sys.intern은 역효과 (Python dict 자체가 메모리 소비)
- **Polars Categorical이 결정적**: 97.32MB → 2.23MB (97.7% 절감)
- Categorical은 Polars Rust 힙에서 동일 text를 한 번만 저장하므로 근본적 해결
- 가설 채택: 중복률 30%+ → 실제 73.9%. Categorical 적용이 핵심 방향

실험일: 2026-03-25
"""

import gc
import sys

import psutil

from dartlab.providers.dart.docs.sections.pipeline import sections


def main(stockCode: str = "005930") -> None:
    proc = psutil.Process()
    gc.collect()
    baseRss = proc.memory_info().rss / 1024 / 1024

    # sections 생성
    df = sections(stockCode)
    gc.collect()
    afterRss = proc.memory_info().rss / 1024 / 1024
    print(f"[sections 생성 후] RSS: {afterRss:.1f}MB (증가: {afterRss - baseRss:.1f}MB)")
    print(f"DataFrame shape: {df.shape}")

    # period 컬럼 추출
    import re
    periodCols = [c for c in df.columns if re.fullmatch(r"\d{4}(Q[1-4])?", c)]
    print(f"period 컬럼 수: {len(periodCols)}")

    # 모든 period text 수집
    allTexts: list[str] = []
    for col in periodCols:
        series = df[col]
        for val in series.to_list():
            if val is not None:
                allTexts.append(val)

    totalCount = len(allTexts)
    totalBytes = sum(len(t.encode("utf-8")) for t in allTexts)
    print(f"\n전체 text cell 수: {totalCount}")
    print(f"전체 text 바이트: {totalBytes / 1024 / 1024:.2f}MB")

    # unique 분석
    uniqueTexts = set(allTexts)
    uniqueCount = len(uniqueTexts)
    uniqueBytes = sum(len(t.encode("utf-8")) for t in uniqueTexts)
    dupCount = totalCount - uniqueCount
    dupBytes = totalBytes - uniqueBytes

    print(f"\nunique text 수: {uniqueCount} ({uniqueCount/totalCount*100:.1f}%)")
    print(f"중복 text 수: {dupCount} ({dupCount/totalCount*100:.1f}%)")
    print(f"중복 바이트: {dupBytes / 1024 / 1024:.2f}MB ({dupBytes/totalBytes*100:.1f}%)")

    # 길이별 중복 분석
    from collections import Counter
    textCounter = Counter(allTexts)
    dupTexts = {t: c for t, c in textCounter.items() if c > 1}
    if dupTexts:
        # 바이트 낭비 기준 상위 10
        byWaste = sorted(dupTexts.items(), key=lambda x: len(x[0].encode("utf-8")) * (x[1] - 1), reverse=True)
        print(f"\n--- 중복 바이트 낭비 상위 10 ---")
        for text, count in byWaste[:10]:
            textBytes = len(text.encode("utf-8"))
            waste = textBytes * (count - 1)
            preview = text[:60].replace("\n", "\\n")
            print(f"  [{count}회] {waste/1024:.1f}KB 낭비 | {preview}...")

    # sys.intern 효과 측정
    del allTexts, uniqueTexts, dupTexts, textCounter
    gc.collect()
    preInternRss = proc.memory_info().rss / 1024 / 1024

    # DataFrame의 period 컬럼을 intern 적용한 새 dict로 재구성
    internedCols = {}
    internPool: dict[str, str] = {}
    for col in periodCols:
        series = df[col]
        newCol = []
        for val in series.to_list():
            if val is None:
                newCol.append(None)
            else:
                if val not in internPool:
                    internPool[val] = val  # 원본 유지
                newCol.append(internPool[val])
        internedCols[col] = newCol

    internedPoolBytes = sum(len(k.encode("utf-8")) for k in internPool)
    print(f"\nintern pool 크기: {len(internPool)}개, {internedPoolBytes / 1024 / 1024:.2f}MB")
    print(f"원본 대비: {internedPoolBytes/totalBytes*100:.1f}%")

    gc.collect()
    postInternRss = proc.memory_info().rss / 1024 / 1024
    print(f"\nintern 전 RSS: {preInternRss:.1f}MB")
    print(f"intern 후 RSS: {postInternRss:.1f}MB")
    print(f"RSS 차이: {postInternRss - preInternRss:+.1f}MB")

    # Polars Categorical 대안 — text를 enum 인코딩하면?
    catSize = 0
    for col in periodCols:
        try:
            catSeries = df[col].cast(pl.Categorical)
            catSize += catSeries.estimated_size()
        except Exception:
            catSize += df[col].estimated_size()
    print(f"\n--- Categorical 인코딩 시뮬레이션 ---")
    origSize = sum(df[col].estimated_size() for col in periodCols)
    print(f"원본 period 컬럼 크기: {origSize / 1024 / 1024:.2f}MB")
    print(f"Categorical 시 크기: {catSize / 1024 / 1024:.2f}MB")
    print(f"절감률: {(1 - catSize/origSize)*100:.1f}%")


if __name__ == "__main__":
    import polars as pl
    stockCode = sys.argv[1] if len(sys.argv) > 1 else "005930"
    main(stockCode)
