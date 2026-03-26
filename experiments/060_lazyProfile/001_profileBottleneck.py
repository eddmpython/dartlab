"""
실험 ID: 060-001
실험명: _buildProfile 병목 정밀 측정

목적:
- _buildProfile이 71개 topic을 eager show()로 로드할 때 어디서 시간이 걸리는지 정밀 측정
- topic별 소요 시간 분포 파악
- sections 수평화 vs 개별 파서 vs ratios 비용 분리

가설:
1. 전체 35초 중 business/mdna 같은 대형 텍스트 파서가 80% 이상 차지할 것
2. sections 수평화 자체는 1초 미만
3. finance/report topic은 캐시 덕분에 거의 0초

방법:
1. Company("005930") 생성
2. _boardTopics() 목록 추출
3. 각 topic별 show() 시간 개별 측정
4. 카테고리별(finance/docs/report/sections) 집계

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

import sys
import time

sys.path.insert(0, "src")


def measure():
    from dartlab.providers.dart.company import Company

    t0 = time.perf_counter()
    c = Company("005930")
    t1 = time.perf_counter()
    print(f"__init__: {t1 - t0:.3f}s")

    t2 = time.perf_counter()
    sec = c.docs.sections
    t3 = time.perf_counter()
    print(f"docs.sections: {t3 - t2:.3f}s  shape={sec.shape if sec is not None else None}")

    topics = c._boardTopics()
    print(f"\n_boardTopics: {len(topics)}개")
    print("-" * 70)

    timings = []
    for topic in topics:
        ts = time.perf_counter()
        try:
            result = c.show(topic)
            te = time.perf_counter()
            elapsed = te - ts
            rtype = type(result).__name__ if result is not None else "None"
            if hasattr(result, "shape"):
                detail = f"shape={result.shape}"
            elif isinstance(result, list):
                detail = f"len={len(result)}"
            elif isinstance(result, str):
                detail = f"len={len(result)}"
            else:
                detail = ""
            timings.append((topic, elapsed, rtype, detail))
        except Exception as e:
            te = time.perf_counter()
            timings.append((topic, te - ts, "ERROR", str(e)[:60]))

    timings.sort(key=lambda x: x[1], reverse=True)

    total = sum(t[1] for t in timings)
    print(f"\n{'topic':<40} {'time':>8} {'type':<12} detail")
    print("=" * 90)
    for topic, elapsed, rtype, detail in timings:
        pct = elapsed / total * 100 if total > 0 else 0
        marker = " ***" if elapsed > 1.0 else ""
        print(f"{topic:<40} {elapsed:>7.3f}s {rtype:<12} {detail}{marker}")

    print("=" * 90)
    print(f"{'TOTAL':<40} {total:>7.3f}s")

    slow = [t for t in timings if t[1] > 1.0]
    fast = [t for t in timings if t[1] <= 0.01]
    mid = [t for t in timings if 0.01 < t[1] <= 1.0]

    print(f"\n> 1초 (느림): {len(slow)}개, 합계 {sum(t[1] for t in slow):.3f}s ({sum(t[1] for t in slow)/total*100:.1f}%)")
    print(f"0.01~1초 (보통): {len(mid)}개, 합계 {sum(t[1] for t in mid):.3f}s")
    print(f"< 0.01초 (빠름): {len(fast)}개, 합계 {sum(t[1] for t in fast):.3f}s")


if __name__ == "__main__":
    measure()
