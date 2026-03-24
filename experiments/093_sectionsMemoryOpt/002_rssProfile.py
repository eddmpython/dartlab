"""실험 ID: 093-002
실험명: sections RSS 기반 메모리 프로파일 (Polars Rust 힙 포함)

목적:
- tracemalloc은 Python 힙만 추적하므로 Polars Rust 힙 미포함
- psutil RSS로 실제 프로세스 메모리 사용량을 정확히 측정

가설:
1. projection pushdown으로 parquet 로드 시 RSS 절감
2. generator 전환으로 expansion 피크 RSS 절감

방법:
1. psutil.Process().memory_info().rss로 각 단계 전후 RSS 측정
2. sections 파이프라인 주요 구간에 측정 포인트 삽입
3. 삼성전자(005930) 대상

결과 (실험 후 작성):
| 지표              | Baseline | 최적화 후 | 변화       |
|-------------------|----------|-----------|-----------|
| 소요 시간         | 5.82s    | 5.30s     | -9%       |
| 최종 RSS          | 491.3MB  | 490.1MB   | -1.2MB    |
| DataFrame size    | 97.03MB  | 97.01MB   | -0.02MB   |
| Categorical 메모리| 0.00MB   | 0.13MB    | (신규)    |
| String/Utf8 메모리| 96.50MB  | 96.35MB   | -0.15MB   |

- RSS 490MB 중 ~350MB가 Polars Rust 힙 (Python gc 불가)
- Python 측 최적화 여지: ~90MB (전체의 ~18%)
- 최종 DataFrame 97MB 중 96.35MB가 본문 텍스트 (Utf8)

결론:
- Python 측 메모리 최적화(generator, projection pushdown, Categorical, pop 소비)의
  RSS 절감 효과는 미미하다. 전체 RSS의 72%가 Polars Rust 힙이므로.
- 속도는 9% 향상 (5.82s → 5.30s). generator 전환으로 중간 sorted() 제거 효과.
- Categorical 인코딩은 chapter/blockType/textNodeType/cadenceScope에 적용했으나
  DataFrame 97MB 중 본문 텍스트가 96.35MB(99.3%)이므로 메타 컬럼 압축 효과 미미.
- 근본적인 메모리 절감은 Polars Rust 힙 자체를 줄이는 방향이어야 한다:
  (1) parquet 자체를 줄이거나 (2) 필요한 기간만 로드하거나 (3) Rust 측 streaming.
- 가설 기각: Python 측 최적화만으로는 40% 절감 불가능.


실험일: 2026-03-24
"""

import gc
import os
import sys
import time

sys.path.insert(0, "src")


def getRssMb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def measure(stockCode: str) -> None:
    gc.collect()
    rssStart = getRssMb()
    print(f"[시작] RSS: {rssStart:.1f}MB")

    t0 = time.perf_counter()

    from dartlab.engines.company.dart.docs.sections.pipeline import sections

    rssImport = getRssMb()
    print(f"[import 후] RSS: {rssImport:.1f}MB (+{rssImport - rssStart:.1f}MB)")

    df = sections(stockCode)
    elapsed = time.perf_counter() - t0

    gc.collect()
    rssAfter = getRssMb()

    print(f"\n=== sections({stockCode}) RSS 프로파일 ===")
    print(f"소요 시간: {elapsed:.2f}s")
    print(f"시작 RSS: {rssStart:.1f}MB")
    print(f"import 후 RSS: {rssImport:.1f}MB")
    print(f"sections 완료 후 RSS: {rssAfter:.1f}MB")
    print(f"순 증가: {rssAfter - rssStart:.1f}MB")

    if df is not None:
        print(f"\nDataFrame shape: {df.shape}")
        print(f"DataFrame estimated_size: {df.estimated_size() / 1024 / 1024:.2f}MB")

        # 컬럼별 메모리 사용량 분석
        catSize = 0
        utf8Size = 0
        otherSize = 0
        for col in df.columns:
            colSize = df[col].estimated_size()
            dtype = str(df[col].dtype)
            if "Cat" in dtype:
                catSize += colSize
            elif "String" in dtype or "Utf8" in dtype:
                utf8Size += colSize
            else:
                otherSize += colSize
        print(f"\n컬럼 타입별 메모리:")
        print(f"  Categorical: {catSize / 1024 / 1024:.2f}MB")
        print(f"  String/Utf8: {utf8Size / 1024 / 1024:.2f}MB")
        print(f"  기타 (Int64, Boolean, List): {otherSize / 1024 / 1024:.2f}MB")

        # DataFrame 해제 후 RSS
        del df
        gc.collect()
        rssClean = getRssMb()
        print(f"\nDataFrame 해제 후 RSS: {rssClean:.1f}MB")
        print(f"DataFrame이 차지하던 실제 RSS: {rssAfter - rssClean:.1f}MB")


if __name__ == "__main__":
    stockCode = sys.argv[1] if len(sys.argv) > 1 else "005930"
    measure(stockCode)
