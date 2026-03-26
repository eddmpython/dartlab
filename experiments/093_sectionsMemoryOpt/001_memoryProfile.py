"""실험 ID: 093-001
실험명: sections 파이프라인 메모리 최적화 효과 측정

목적:
- scan_parquet projection pushdown, generator 전환, Categorical 인코딩,
  pop 소비 패턴 적용 후 메모리 사용량 변화 측정

가설:
1. projection pushdown으로 parquet 로드 메모리 30%+ 절감
2. generator 전환으로 text expansion 피크 메모리 30%+ 절감
3. Categorical 인코딩으로 최종 DataFrame 메모리 10-15% 절감
4. 종합 피크 메모리 40%+ 절감

방법:
1. tracemalloc으로 sections() 호출 전후 메모리 스냅샷 비교
2. 삼성전자(005930) 대상 — 가장 큰 docs parquet 중 하나
3. 피크 메모리, 최종 DataFrame 크기, 소요 시간 측정

결과 (실험 후 작성):
- tracemalloc 피크: 333.1MB (baseline 333.2MB와 동일)
- tracemalloc은 Python 힙만 추적 → Polars Rust 힙 미포함
- 40.4MB가 importlib (모듈 로딩), 4.6MB가 Polars Series 생성
- textStructure.py가 3.7MB+2.2MB+1.1MB+1.0MB = ~8MB 기여
- → tracemalloc으로는 최적화 효과 측정 불가. 002_rssProfile.py 참조.

결론:
- tracemalloc은 Polars 기반 파이프라인에서 부적절한 측정 도구.
- Python 힙 기준으로는 baseline과 차이 없음 (333.2 → 333.1MB).
- psutil RSS 기반 측정(002)으로 전환. 거기서도 RSS 차이 미미 확인.


실험일: 2026-03-24
"""

import gc
import sys
import time
import tracemalloc

sys.path.insert(0, "src")


def measureSections(stockCode: str) -> None:
    gc.collect()
    tracemalloc.start()
    snapshotBefore = tracemalloc.take_snapshot()
    memBefore = tracemalloc.get_traced_memory()

    t0 = time.perf_counter()

    from dartlab.providers.dart.docs.sections.pipeline import sections

    df = sections(stockCode)
    elapsed = time.perf_counter() - t0

    memAfter = tracemalloc.get_traced_memory()
    snapshotAfter = tracemalloc.take_snapshot()
    peakMem = memAfter[1]

    print(f"\n=== sections({stockCode}) 메모리 프로파일 ===")
    print(f"소요 시간: {elapsed:.2f}s")
    print(f"피크 메모리 (tracemalloc): {peakMem / 1024 / 1024:.1f}MB")
    print(f"현재 메모리: {memAfter[0] / 1024 / 1024:.1f}MB")

    if df is not None:
        print(f"\nDataFrame shape: {df.shape}")
        estSize = df.estimated_size()
        print(f"DataFrame estimated_size: {estSize / 1024 / 1024:.2f}MB")
        print(f"DataFrame dtypes (처음 10개):")
        for col in df.columns[:10]:
            print(f"  {col}: {df[col].dtype}")

        catCols = [c for c in df.columns if df[c].dtype == "Categorical"]
        utf8Cols = [c for c in df.columns if str(df[c].dtype) == "Utf8"]
        print(f"\nCategorical 컬럼: {len(catCols)}개 {catCols}")
        print(f"Utf8 컬럼: {len(utf8Cols)}개")
    else:
        print("DataFrame: None")

    # top 10 메모리 소비 라인
    stats = snapshotAfter.compare_to(snapshotBefore, "lineno")
    print("\n피크 메모리 기여 top 10:")
    for stat in stats[:10]:
        print(f"  {stat}")

    tracemalloc.stop()


if __name__ == "__main__":
    stockCode = sys.argv[1] if len(sys.argv) > 1 else "005930"
    measureSections(stockCode)
