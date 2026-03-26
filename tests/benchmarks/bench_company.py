"""Company 성능 기준치 측정.

직접 실행:
    uv run python tests/benchmarks/bench_company.py

측정 항목:
- Company init (DART)
- index 접근
- show("BS")
- show("companyOverview") — docs topic
- diff()
"""

import statistics
import time

SAMSUNG = "005930"
ROUNDS = 3


def _median(fn, rounds=ROUNDS):
    times = []
    result = None
    for _ in range(rounds):
        start = time.perf_counter()
        result = fn()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.median(times), result


def main():
    from dartlab.providers.dart.company import Company

    print("=" * 60)
    print(f"Company 성능 기준치 ({ROUNDS}회 median)")
    print("=" * 60)

    # 1. init
    t, c = _median(lambda: Company(SAMSUNG))
    print(f"  Company('{SAMSUNG}') init : {t:.3f}s")

    # 2. index
    t, _ = _median(lambda: c.index)
    print(f"  c.index                   : {t:.3f}s")

    # 3. show("BS")
    t, _ = _median(lambda: c.show("BS"))
    print(f"  c.show('BS')              : {t:.3f}s")

    # 4. show("companyOverview")
    t, _ = _median(lambda: c.show("companyOverview"))
    print(f"  c.show('companyOverview') : {t:.3f}s")

    # 5. diff()
    t, _ = _median(lambda: c.diff())
    print(f"  c.diff()                  : {t:.3f}s")

    print("=" * 60)


if __name__ == "__main__":
    main()
