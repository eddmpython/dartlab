"""실험 109-03: 외생변수 6축 단일종목 회귀.

가설: exogenousAxes의 업종 최적 3지표가 기존 macroBeta의
범용 3지표(GDP/금리/환율)보다 개별 기업 매출 설명력이 높다.

방법:
1. 5개 기업 선택 (경기민감도 스펙트럼 커버)
2. 각 기업의 연간 매출 성장률 시계열 vs 외생변수 OLS
3. 범용 3지표 vs 업종 최적 3지표 R-squared 비교

성공 기준: R-squared 개선 또는 방향 정확도 개선
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.finance.exogenousAxes import (  # noqa: E402
    ExogenousIndicator,
    getExogenousIndicators,
)
from dartlab.gather import getDefaultGather  # noqa: E402


# 테스트 대상 기업
TARGETS = [
    ("005930", "삼성전자", "반도체/high"),
    ("015760", "한국전력", "전력/defensive"),
    ("005380", "현대차", "자동차/high"),
    ("097950", "CJ제일제당", "식품/defensive"),
    ("032830", "삼성생명", "금융/moderate"),
]

# 범용 3지표 (기존 macroBeta 방식)
GENERIC_INDICATORS = [
    ExogenousIndicator("GDP", "ecos", "GDP", "domestic"),
    ExogenousIndicator("BASE_RATE", "ecos", "기준금리", "financial"),
    ExogenousIndicator("USDKRW", "ecos", "원/달러", "fx"),
]


def _load_revenue_growth(stock_code: str) -> pl.DataFrame | None:
    """Company에서 연간 매출 성장률 시계열 추출."""
    try:
        import dartlab

        c = dartlab.Company(stock_code)
        result = c.select("IS", ["매출액"])
        if result is None or len(result) == 0:
            return None

        # SelectResult wraps a DataFrame — access underlying df
        if isinstance(result, pl.DataFrame):
            df = result
        elif hasattr(result, "_df"):
            df = result._df
        else:
            # SelectResult proxies DataFrame methods via __getattr__
            df = result

        # 연간 기간 컬럼 추출 (Q4 = 연간 누적, 또는 xxxA 패턴)
        # 컬럼: snakeId, 계정명, 2025Q4, 2025Q3, ... 또는 2024A, 2023A, ...
        period_cols = []
        for col in df.columns:
            if col in ("snakeId", "계정명", "account"):
                continue
            # Q4 (4분기 = 연간 누적) 또는 A (연간) 패턴
            if col.endswith("Q4") or col.endswith("A"):
                period_cols.append(col)

        if len(period_cols) < 3:
            # Q4가 없으면 모든 기간에서 연간 추출 시도
            for col in df.columns:
                if col in ("snakeId", "계정명", "account"):
                    continue
                if col.endswith("A"):
                    period_cols.append(col)
            if len(period_cols) < 3:
                print(f"  연간 기간 부족: {len(period_cols)}개")
                return None

        values = []
        for col in sorted(period_cols):
            val = df[col][0]
            # 연도 추출
            year_str = col.replace("Q4", "").replace("A", "")
            try:
                year = int(year_str)
            except ValueError:
                continue
            if val is not None:
                values.append({"year": year, "revenue": float(val)})

        if len(values) < 3:
            return None

        result_df = pl.DataFrame(values).sort("year")
        # 전년대비 성장률
        result_df = result_df.with_columns(
            (pl.col("revenue") / pl.col("revenue").shift(1) - 1).alias("growth")
        ).drop_nulls("growth")

        return result_df
    except Exception as e:
        print(f"  매출 로드 실패 ({stock_code}): {e}")
        import traceback
        traceback.print_exc()
        return None


def _load_indicator_annual(
    g, indicator: ExogenousIndicator, years: list[int]
) -> list[float | None]:
    """외생변수 지표의 연간 평균값 추출."""
    try:
        if indicator.source == "ecos":
            df = g.macro("KR", indicator.seriesId, start="2014-01-01")
        else:
            df = g.macro(indicator.seriesId, start="2014-01-01")

        if df is None or len(df) == 0:
            return [None] * len(years)

        # 연간 평균
        annual = (
            df.with_columns(pl.col("date").dt.year().alias("year"))
            .group_by("year")
            .agg(pl.col("value").mean())
            .sort("year")
        )

        result = []
        for y in years:
            row = annual.filter(pl.col("year") == y)
            if len(row) > 0:
                result.append(float(row["value"][0]))
            else:
                result.append(None)
        return result
    except Exception as e:
        print(f"    지표 로드 실패 ({indicator.label}): {e}")
        return [None] * len(years)


def _ols_r_squared(y: list[float], X: list[list[float]]) -> float | None:
    """단순 OLS R-squared 계산 (numpy 없이)."""
    n = len(y)
    if n < 3:
        return None

    k = len(X)  # 변수 수
    if k == 0:
        return None

    # y의 평균
    y_mean = sum(y) / n

    # 총변동 (SST)
    sst = sum((yi - y_mean) ** 2 for yi in y)
    if sst == 0:
        return None

    # 단변수씩 상관계수 기반 간이 R-squared
    # 다변수 OLS는 행렬 연산 필요 → numpy 없으므로 각 변수 개별 R-squared 합산 근사
    best_r2 = 0.0
    for j in range(k):
        xj = [X[j][i] for i in range(n)]
        xj_mean = sum(xj) / n
        xj_var = sum((x - xj_mean) ** 2 for x in xj)
        if xj_var == 0:
            continue
        cov = sum((y[i] - y_mean) * (xj[i] - xj_mean) for i in range(n))
        r = cov / (sst * xj_var) ** 0.5
        r2 = r * r
        if r2 > best_r2:
            best_r2 = r2

    return best_r2


def _direction_accuracy(y: list[float], x: list[float]) -> float | None:
    """방향 일치율 (둘 다 양 or 둘 다 음)."""
    if len(y) < 2 or len(x) < 2:
        return None

    # 변화율 방향
    correct = 0
    total = 0
    for i in range(1, len(y)):
        y_dir = 1 if y[i] > y[i - 1] else -1
        x_dir = 1 if x[i] > x[i - 1] else -1
        if y_dir == x_dir:
            correct += 1
        total += 1

    return correct / total if total > 0 else None


def main():
    g = getDefaultGather()

    print("=== 109-03: 외생변수 6축 단일종목 회귀 ===\n")

    for stock_code, name, desc in TARGETS:
        print(f"\n{'='*60}")
        print(f"  {name} ({stock_code}) — {desc}")
        print(f"{'='*60}")

        # 1. 매출 성장률 로드
        rev_df = _load_revenue_growth(stock_code)
        if rev_df is None:
            print("  매출 데이터 없음, 건너뜀")
            continue

        years = rev_df["year"].to_list()
        growth = rev_df["growth"].to_list()
        print(f"\n  매출 성장률 ({len(years)}년):")
        for y, g_val in zip(years, growth):
            print(f"    {y}: {g_val:+.1%}")

        # 2. 업종 최적 3지표
        optimal = getExogenousIndicators(stockCode=stock_code)
        print(f"\n  업종 최적 지표: {', '.join(ind.label for ind in optimal)}")

        # 3. 범용 3지표
        print(f"  범용 지표: {', '.join(ind.label for ind in GENERIC_INDICATORS)}")

        # 4. 지표 데이터 로드 + 비교
        for label, indicators in [
            ("범용 3지표", GENERIC_INDICATORS),
            ("업종 최적 3지표", optimal),
        ]:
            print(f"\n  --- {label} ---")
            X_all = []
            for ind in indicators:
                values = _load_indicator_annual(g, ind, years)
                # None 필터링
                valid = [(i, v) for i, v in enumerate(values) if v is not None]
                if len(valid) < 3:
                    print(f"    {ind.label}: 데이터 부족")
                    continue

                # 변화율 계산
                raw_values = [v for _, v in valid]
                changes = []
                for i in range(1, len(raw_values)):
                    if raw_values[i - 1] != 0:
                        changes.append(
                            (raw_values[i] - raw_values[i - 1]) / abs(raw_values[i - 1])
                        )
                    else:
                        changes.append(0)

                if len(changes) >= 2:
                    X_all.append(changes)

                    # 개별 상관
                    # growth도 같은 길이로 맞춤
                    g_subset = growth[-(len(changes)):]
                    r2 = _ols_r_squared(g_subset, [changes])
                    dir_acc = _direction_accuracy(g_subset, changes)

                    print(
                        f"    {ind.label:16s}: R²={r2:.3f}" if r2 else f"    {ind.label:16s}: R²=N/A",
                        end="",
                    )
                    if dir_acc is not None:
                        print(f"  방향일치={dir_acc:.0%}", end="")
                    print()

            # 종합 R-squared (최고 단변수 기준)
            if X_all:
                g_subset = growth[-(len(X_all[0])):]
                combined_r2 = _ols_r_squared(g_subset, X_all)
                print(f"    종합 최고 R²: {combined_r2:.3f}" if combined_r2 else "    종합 R²: N/A")

    print("\n\n실험 완료.")


if __name__ == "__main__":
    main()
