"""
실험 ID: 001
실험명: availableApiTypes 캐시 적용

목적:
- report.availableApiTypes가 28개 apiType마다 extract() → parquet I/O 수행
- 2회차 이후 호출을 캐시로 즉시 반환하여 반복 접근 비용 제거

가설:
1. 첫 호출은 extract() 28회로 ~0.3-0.5s 소요
2. _cache에 결과를 저장하면 2회차 이후 ~0.001s 이내

방법:
1. 삼성전자(005930) Company 생성
2. report.availableApiTypes 3회 호출, 각각 소요 시간 측정
3. 캐시 적용 후 동일 측정 → before/after 비교
4. 결과 동일성 assert

결과 (실험 후 작성):
- before: 매 호출 ~0.25s (extract 캐시 무효화 시), 22개 apiType 존재
- after 1회차: 0.24s (캐시 빌드 = extract 28회)
- after 2회차+: 0.000001s (캐시 히트)
- 속도 향상: ~200,000x (2회차 이후)
- 결과 동일성 검증 OK

결론:
- **채택**. _cache["_availableApiTypes"]에 결과 저장, 2회차 이후 즉시 반환
- extract() 자체도 개별 캐시가 있으므로, 같은 Company 인스턴스 내에서
  availableApiTypes만 캐시하면 충분

실험일: 2026-03-19
"""

import time
import sys
sys.path.insert(0, "src")

def main():
    import dartlab

    c = dartlab.Company("005930")

    # --- before: 현재 구현 (캐시 없음) ---
    times_before = []
    for i in range(3):
        # extract 캐시를 무효화하기 위해 _cache에서 _extract_ 키 제거
        keys_to_remove = [k for k in c.report._cache if k.startswith("_extract_")]
        for k in keys_to_remove:
            del c.report._cache[k]
        # availableApiTypes 캐시 키도 제거 (있으면)
        c.report._cache.pop("_availableApiTypes", None)

        t0 = time.perf_counter()
        result_before = c.report.availableApiTypes
        t1 = time.perf_counter()
        times_before.append(t1 - t0)
        print(f"  before #{i+1}: {t1-t0:.4f}s  → {len(result_before)} types")

    print(f"  before avg: {sum(times_before)/len(times_before):.4f}s")
    print(f"  결과: {result_before}")

    # --- after: 캐시 적용 시뮬레이션 ---
    # extract 캐시를 다시 무효화
    keys_to_remove = [k for k in c.report._cache if k.startswith("_extract_")]
    for k in keys_to_remove:
        del c.report._cache[k]
    c.report._cache.pop("_availableApiTypes", None)

    # 캐시 로직 시뮬레이션
    def availableApiTypesCached(accessor):
        cacheKey = "_availableApiTypes"
        if cacheKey in accessor._cache:
            return accessor._cache[cacheKey]
        from dartlab.engines.dart.report.types import API_TYPES
        result = [name for name in API_TYPES if accessor.extract(name) is not None]
        accessor._cache[cacheKey] = result
        return result

    times_after = []
    for i in range(3):
        t0 = time.perf_counter()
        result_after = availableApiTypesCached(c.report)
        t1 = time.perf_counter()
        times_after.append(t1 - t0)
        print(f"  after  #{i+1}: {t1-t0:.6f}s  → {len(result_after)} types")

    print(f"  after  avg: {sum(times_after)/len(times_after):.6f}s")

    # 동일성 검증
    assert result_before == result_after, f"결과 불일치: {result_before} != {result_after}"
    print("\n  결과 동일성 확인 OK")

    # 요약
    speedup = times_before[0] / times_after[1] if times_after[1] > 0 else float("inf")
    print(f"\n  1회차: {times_before[0]:.4f}s → {times_after[0]:.4f}s (첫 호출, 캐시 빌드)")
    print(f"  2회차: {times_before[1]:.4f}s → {times_after[1]:.6f}s (캐시 히트)")
    print(f"  속도 향상: {speedup:.0f}x")


if __name__ == "__main__":
    main()
