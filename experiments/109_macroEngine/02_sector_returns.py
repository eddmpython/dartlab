"""실험 109-02: 사이클-섹터 전략 실효성.

가설: 경제 사이클 국면에 따라 cyclicality별 섹터 수익률 차이가 유의미하다.
- 침체기: defensive > high
- 회복기: high > defensive
- 확장기: high >= moderate
- 둔화기: defensive > high

방법:
1. KOSPI 업종지수 과거 수익률 수집 (gather.price로 지수 데이터)
2. 01_cycle_detection의 사이클 판별 결과로 국면 기간 구분
3. 국면별 cyclicality 그룹 평균 수익률 비교

성공 기준: 사이클 국면에 따라 업종군 간 수익률 차이 >5%p
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.finance.scenario import SECTOR_ELASTICITY, SectorElasticity  # noqa: E402
from dartlab.gather import getDefaultGather  # noqa: E402


# 한국 대표 업종 ETF/종목 (업종 대리 지표)
# cyclicality 분류는 SECTOR_ELASTICITY에서 가져옴
SECTOR_PROXIES = {
    # 종목코드: (이름, SECTOR_ELASTICITY 키)
    "091160": ("삼성반도체 ETF → 반도체 대리", "반도체"),
    "005380": ("현대차 → 자동차", "자동차"),
    "051910": ("LG화학 → 화학", "화학"),
    "005490": ("POSCO → 철강", "철강"),
    "105560": ("KB금융 → 금융/은행", "금융/은행"),
    "030200": ("KT → 통신", "통신"),
    "004170": ("신세계 → 유통", "유통"),
    "097950": ("CJ제일제당 → 식품", "식품"),
    "015760": ("한국전력 → 전력/에너지", "전력/에너지"),
    "068270": ("셀트리온 → 제약/바이오", "제약/바이오"),
}


def main():
    g = getDefaultGather()

    print("=== 109-02: 사이클-섹터 전략 실효성 ===\n")

    # 수동 국면 기간 정의 (NBER + 한은 기준 + 시장 관찰)
    # 실제로는 01_cycle_detection 결과를 사용하지만, 검증용으로 사전 정의
    cycle_periods = [
        # (start, end, phase, label)
        ("2015-01-01", "2015-08-31", "expansion", "2015 확장"),
        ("2015-09-01", "2016-06-30", "slowdown", "중국발 둔화"),
        ("2016-07-01", "2018-01-31", "expansion", "반도체 슈퍼사이클"),
        ("2018-02-01", "2018-12-31", "slowdown", "금리인상+무역전쟁"),
        ("2019-01-01", "2019-12-31", "recovery", "2019 회복"),
        ("2020-01-01", "2020-03-31", "contraction", "COVID 침체"),
        ("2020-04-01", "2021-06-30", "recovery", "COVID 회복"),
        ("2021-07-01", "2022-06-30", "expansion", "2021-22 확장"),
        ("2022-07-01", "2022-12-31", "slowdown", "금리인상 둔화"),
        ("2023-01-01", "2023-12-31", "recovery", "2023 회복"),
        ("2024-01-01", "2024-12-31", "expansion", "2024 확장"),
    ]

    # 업종별 주가 수집
    print("업종 대리 주가 수집 중...\n")
    price_data: dict[str, pl.DataFrame] = {}

    for code, (name, _sector_key) in SECTOR_PROXIES.items():
        try:
            df = g.price(code, start="2015-01-01")
            if df is not None and len(df) > 10:
                price_data[code] = df
                print(f"  {name} ({code}): {len(df)}건")
            else:
                print(f"  {name} ({code}): 데이터 부족")
        except Exception as e:
            print(f"  {name} ({code}): 실패 ({e})")

    if not price_data:
        print("\n주가 데이터 수집 실패.")
        return

    # 국면별 수익률 계산
    print("\n=== 국면별 업종 수익률 ===\n")

    results = []

    for start, end, phase, label in cycle_periods:
        start_dt = pl.date(*[int(x) for x in start.split("-")])
        end_dt = pl.date(*[int(x) for x in end.split("-")])

        period_returns = {}

        for code, df in price_data.items():
            name, sector_key = SECTOR_PROXIES[code]
            elasticity = SECTOR_ELASTICITY.get(sector_key)
            if elasticity is None:
                continue

            # 기간 내 시작가/종가로 수익률 계산
            period_df = df.filter(
                (pl.col("date") >= start_dt) & (pl.col("date") <= end_dt)
            ).sort("date")

            if len(period_df) < 5:
                continue

            # close 컬럼 찾기
            close_col = None
            for col in ["close", "종가", "Close"]:
                if col in period_df.columns:
                    close_col = col
                    break
            if close_col is None:
                continue

            first_price = period_df[close_col][0]
            last_price = period_df[close_col][-1]

            if first_price and first_price > 0:
                ret = (last_price / first_price - 1) * 100
                period_returns[code] = {
                    "name": name.split("→")[0].strip(),
                    "sector_key": sector_key,
                    "cyclicality": elasticity.cyclicality,
                    "return_pct": ret,
                }

        if not period_returns:
            continue

        # cyclicality별 평균 수익률
        cyc_returns: dict[str, list[float]] = {}
        for info in period_returns.values():
            cyc = info["cyclicality"]
            cyc_returns.setdefault(cyc, []).append(info["return_pct"])

        print(f"--- {label} ({phase}, {start}~{end}) ---")
        for cyc in ["high", "moderate", "defensive", "low"]:
            if cyc in cyc_returns:
                avg = sum(cyc_returns[cyc]) / len(cyc_returns[cyc])
                n = len(cyc_returns[cyc])
                print(f"  {cyc:12s}: {avg:+7.1f}% (n={n})")
                results.append({
                    "period": label,
                    "phase": phase,
                    "cyclicality": cyc,
                    "avg_return": avg,
                    "n": n,
                })

        # 개별 종목 상세
        for info in sorted(period_returns.values(), key=lambda x: x["return_pct"], reverse=True):
            print(f"    {info['name']:12s} ({info['cyclicality']:10s}): {info['return_pct']:+7.1f}%")
        print()

    # 종합: 국면별 high vs defensive 차이
    if results:
        print("\n=== 종합: 국면별 high vs defensive 수익률 차이 ===\n")

        result_df = pl.DataFrame(results)
        for phase in ["contraction", "recovery", "expansion", "slowdown"]:
            phase_data = result_df.filter(pl.col("phase") == phase)
            high = phase_data.filter(pl.col("cyclicality") == "high")
            defensive = phase_data.filter(pl.col("cyclicality") == "defensive")

            if len(high) > 0 and len(defensive) > 0:
                high_avg = high["avg_return"].mean()
                def_avg = defensive["avg_return"].mean()
                diff = high_avg - def_avg
                winner = "high" if diff > 0 else "defensive"
                expected = {
                    "contraction": "defensive",
                    "recovery": "high",
                    "expansion": "high",
                    "slowdown": "defensive",
                }
                correct = "O" if winner == expected[phase] else "X"
                print(
                    f"  {phase:12s}: high {high_avg:+6.1f}% vs defensive {def_avg:+6.1f}%"
                    f"  차이 {diff:+6.1f}%p  승자={winner}  예상일치={correct}"
                )

    print("\n실험 완료.")


if __name__ == "__main__":
    main()
