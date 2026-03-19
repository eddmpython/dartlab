"""
실험 ID: 006
실험명: sections dict 조립 최적화 (프로파일링)

목적:
- sections() 파이프라인(~2.7s)에서 dict→DataFrame 조립 단계 비중 측정
- 조립 단계가 유의미하면 list comprehension으로 최적화

가설:
1. dict 조립은 전체의 ~15% (~0.45s)
2. list comprehension + records 패턴으로 30% 절감 가능

방법:
1. sections() 함수 내부 단계별 시간 측정
2. 조립 단계 단독 시간 확인
3. 최적화 가치 판단

결과 (실험 후 작성):
- 전체 sections 빌드: 2.79s avg
- dict→DataFrame 변환: 0.011s
- append 루프: 0.069s
- 조립 추정 합계: 0.08s (전체의 2.9%)
- listcomp→DataFrame 대안: 0.10s (오히려 느림)

결론:
- **기각**. dict 조립은 전체의 2.9%에 불과하여 최적화 가치 없음
- sections 파이프라인의 진짜 병목은 _reportRowsToTopicRows + _expandStructuredRows의
  행별 텍스트 파싱 (97%)이며, 이는 Python 문자열 처리 자체의 한계
- Rust 마이그레이션 대상 (장기 과제)

실험일: 2026-03-19
"""

import time
import sys
sys.path.insert(0, "src")


def main():
    import polars as pl
    import dartlab
    from dartlab.engines.dart.docs.sections import pipeline

    # sections 함수를 monkey-patch해서 단계별 시간 측정
    original_sections = pipeline.sections

    # 1) 전체 시간 측정
    times = []
    for i in range(3):
        c = dartlab.Company("005930")
        t0 = time.perf_counter()
        sec = c.docs.sections
        t1 = time.perf_counter()
        times.append(t1 - t0)
        print(f"  전체 #{i+1}: {t1-t0:.4f}s  shape={sec.shape}")

    print(f"  전체 avg: {sum(times)/len(times):.4f}s")

    # 2) dict 조립 단계만 측정
    # sections() 내부를 분해해서 조립 루프만 시간 측정하기는 어려움
    # 대신: DataFrame 생성 직전의 dataColumns dict를 시뮬레이션
    # 간접 측정: 8,109행 × 70컬럼 dict → DataFrame 변환 시간
    sec = dartlab.Company("005930").docs.sections
    nRows = sec.height
    nCols = len(sec.columns)

    # 시뮬레이션: 유사 크기 dict → DataFrame
    sample_data = {col: [f"value_{i}" if sec[col].dtype == pl.Utf8 else i for i in range(nRows)]
                   for col in sec.columns[:30]}  # 메타 컬럼 30개
    # period 컬럼
    for col in sec.columns[30:]:
        sample_data[col] = [f"text content {i}" if i % 3 != 0 else None for i in range(nRows)]

    t0 = time.perf_counter()
    for _ in range(10):
        _ = pl.DataFrame(sample_data)
    t1 = time.perf_counter()
    dict_to_df_time = (t1 - t0) / 10
    print(f"\n  dict→DataFrame 변환: {dict_to_df_time:.4f}s ({nRows}행 × {nCols}컬럼)")

    # 3) append 루프 시뮬레이션 (25컬럼 × 8K행)
    t0 = time.perf_counter()
    for _ in range(10):
        cols = {f"col_{j}": [] for j in range(30)}
        for i in range(nRows):
            for j in range(30):
                cols[f"col_{j}"].append(f"val_{i}")
    t1 = time.perf_counter()
    append_time = (t1 - t0) / 10
    print(f"  append 루프: {append_time:.4f}s (30컬럼 × {nRows}행)")

    # 4) list comprehension 비교
    t0 = time.perf_counter()
    for _ in range(10):
        records = [{f"col_{j}": f"val_{i}" for j in range(30)} for i in range(nRows)]
        _ = pl.DataFrame(records)
    t1 = time.perf_counter()
    listcomp_time = (t1 - t0) / 10
    print(f"  listcomp→DataFrame: {listcomp_time:.4f}s")

    total_assembly_est = append_time + dict_to_df_time
    total_avg = sum(times) / len(times)
    print(f"\n  조립 추정: {total_assembly_est:.4f}s / 전체 {total_avg:.4f}s = {total_assembly_est/total_avg:.1%}")


if __name__ == "__main__":
    main()
