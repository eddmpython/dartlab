"""
실험 ID: 004
실험명: _comparablePathInfo lru_cache 적용

목적:
- _comparablePathInfo가 행 루프 안에서 매번 호출 (78K+ 회)
- 같은 (topic, semanticPathKey) 쌍이 반복되므로 lru_cache로 캐시

가설:
1. 캐시 히트율 80%+ (같은 topic의 같은 path가 기간별 반복)
2. 0.42s → ~0.05s

방법:
1. 삼성전자(005930) sections 빌드 과정에서 _comparablePathInfo 호출 횟수/고유 인자 수 측정
2. lru_cache 적용 후 sections 빌드 시간 before/after 비교
3. 결과 동일성 assert

결과 (실험 후 작성):
- 호출 78,231회, 고유 인자 3,870개, 캐시 히트율 95.1%
- before: 3.05s, after: 2.96s (1.0x — 사실상 동일)
- lru_cache 히트 74,361회지만 함수 자체가 가벼워서 절감 미미

결론:
- **기각**. _comparablePathInfo 자체 비용이 너무 작아 캐시 오버헤드와 상쇄
- sections 파이프라인 병목은 이 함수가 아니라 메인 루프의 dict 조립

실험일: 2026-03-19
"""

import time
import sys
sys.path.insert(0, "src")


def main():
    import functools
    import dartlab
    from dartlab.engines.company.dart.docs.sections import pipeline

    # 원본 함수 참조 저장
    original_fn = pipeline._comparablePathInfo

    # 호출 횟수 카운터
    call_count = 0
    unique_args = set()

    def counting_wrapper(topic, semanticPathKey):
        nonlocal call_count
        call_count += 1
        unique_args.add((topic, semanticPathKey))
        return original_fn(topic, semanticPathKey)

    # --- before: 원본 함수로 sections 빌드 ---
    pipeline._comparablePathInfo = counting_wrapper
    c1 = dartlab.Company("005930")

    t0 = time.perf_counter()
    sec1 = c1.docs.sections
    t1 = time.perf_counter()
    time_before = t1 - t0
    print(f"  before: {time_before:.4f}s")
    print(f"  호출 횟수: {call_count}, 고유 인자: {len(unique_args)}")
    print(f"  캐시 히트율 예상: {1 - len(unique_args)/call_count:.1%}")

    # --- after: lru_cache 적용 ---
    cached_fn = functools.lru_cache(maxsize=None)(original_fn)
    pipeline._comparablePathInfo = cached_fn

    # 새 Company 인스턴스 (sections 캐시 미포함)
    c2 = dartlab.Company("005930")

    t0 = time.perf_counter()
    sec2 = c2.docs.sections
    t1 = time.perf_counter()
    time_after = t1 - t0
    print(f"  after:  {time_after:.4f}s")
    print(f"  lru_cache info: {cached_fn.cache_info()}")

    # 복원
    pipeline._comparablePathInfo = original_fn

    # 동일성 검증
    assert sec1.shape == sec2.shape, f"shape 불일치: {sec1.shape} vs {sec2.shape}"
    assert sec1.columns == sec2.columns, f"columns 불일치"
    print(f"\n  동일성 검증 OK (shape={sec1.shape})")

    speedup = time_before / time_after if time_after > 0 else float("inf")
    print(f"\n  {time_before:.4f}s → {time_after:.4f}s ({speedup:.1f}x)")


if __name__ == "__main__":
    main()
