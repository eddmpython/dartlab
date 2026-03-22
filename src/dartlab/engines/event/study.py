"""Event Study 핵심 분석.

공시 발표일 전후 주가 비정상 수익률(CAR)을 계산한다.

사용법::

    from dartlab.engines.event.study import analyze_events

    result = analyze_events(company)
    result = analyze_events(company, event_type="사업보고서")
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import polars as pl

from dartlab.engines.event.types import (
    EventImpact,
    EventStudyResult,
    EventWindow,
)


def _parse_date(d: str) -> date:
    """YYYYMMDD 또는 YYYY-MM-DD → date."""
    d = d.replace("-", "")
    return date(int(d[:4]), int(d[4:6]), int(d[6:8]))


def _compute_abnormal_returns(
    stock_returns: pl.DataFrame,
    market_returns: pl.DataFrame,
    event_date: date,
    window: EventWindow,
) -> dict | None:
    """단일 이벤트에 대한 비정상 수익률 계산.

    Market Model: AR_t = R_t - R_m,t (단순 시장 조정 모델)

    Args:
        stock_returns: date, returns 컬럼.
        market_returns: date, returns 컬럼.
        event_date: 이벤트 날짜.
        window: EventWindow.

    Returns:
        car, bhar, pre_car, post_car, t_stat, p_value dict 또는 None.
    """
    # 주가 데이터에서 이벤트 날짜의 인덱스 찾기
    stock_dates = stock_returns.get_column("date").to_list()

    # 이벤트 날짜와 가장 가까운 거래일 찾기
    event_idx = None
    for i, d in enumerate(stock_dates):
        if d >= event_date:
            event_idx = i
            break

    if event_idx is None:
        return None

    # 윈도우 범위
    start_idx = event_idx - window.pre
    end_idx = event_idx + window.post

    if start_idx < 0 or end_idx >= len(stock_dates):
        return None

    # 윈도우 내 수익률 추출
    window_stock = stock_returns.slice(start_idx, window.total)
    window_dates = window_stock.get_column("date").to_list()

    # 시장 수익률과 조인
    merged = window_stock.join(
        market_returns.select(
            pl.col("date"),
            pl.col("returns").alias("market_returns"),
        ),
        on="date",
        how="left",
    )

    # 결측값 처리
    merged = merged.with_columns(
        pl.col("returns").fill_null(0.0),
        pl.col("market_returns").fill_null(0.0),
    )

    # 비정상 수익률 = 주식 수익률 - 시장 수익률
    merged = merged.with_columns(
        (pl.col("returns") - pl.col("market_returns")).alias("ar"),
    )

    ar_values = merged.get_column("ar").to_list()
    stock_ret = merged.get_column("returns").to_list()
    market_ret = merged.get_column("market_returns").to_list()

    if not ar_values:
        return None

    # CAR (Cumulative Abnormal Return)
    car = sum(ar_values)

    # BHAR (Buy-and-Hold Abnormal Return)
    stock_cumul = 1.0
    market_cumul = 1.0
    for sr, mr in zip(stock_ret, market_ret):
        stock_cumul *= 1.0 + sr
        market_cumul *= 1.0 + mr
    bhar = stock_cumul - market_cumul

    # Pre/Post 분리
    pre_ar = ar_values[: window.pre]
    post_ar = ar_values[window.pre + 1 :]  # 이벤트 당일 제외

    pre_car = sum(pre_ar) if pre_ar else 0.0
    post_car = sum(post_ar) if post_ar else 0.0

    # t-통계량
    n = len(ar_values)
    if n > 1:
        mean_ar = sum(ar_values) / n
        var_ar = sum((a - mean_ar) ** 2 for a in ar_values) / (n - 1)
        std_ar = math.sqrt(var_ar) if var_ar > 0 else 1e-10
        t_stat = (car / n) / (std_ar / math.sqrt(n))
    else:
        t_stat = 0.0

    # 간이 p-value (정규분포 근사)
    p_value = _approx_pvalue(abs(t_stat))

    return {
        "car": car,
        "bhar": bhar,
        "pre_car": pre_car,
        "post_car": post_car,
        "t_stat": t_stat,
        "p_value": p_value,
    }


def _approx_pvalue(t: float) -> float:
    """정규분포 근사 양측 p-value."""
    # Abramowitz and Stegun 근사
    p = 0.2316419
    b1, b2, b3, b4, b5 = 0.319381530, -0.356563782, 1.781477937, -1.821255978, 1.330274429
    a = abs(t)
    t_val = 1.0 / (1.0 + p * a)
    phi = math.exp(-a * a / 2.0) / math.sqrt(2.0 * math.pi)
    cdf = 1.0 - phi * (b1 * t_val + b2 * t_val**2 + b3 * t_val**3 + b4 * t_val**4 + b5 * t_val**5)
    return 2.0 * (1.0 - cdf)


def analyze_events(
    company: object,
    *,
    event_type: str | None = None,
    window: EventWindow | None = None,
    min_events: int = 1,
) -> EventStudyResult | None:
    """단일 기업의 전체 공시 → 주가 영향 분석.

    Args:
        company: dartlab Company 객체.
        event_type: 공시 유형 필터 (예: "사업보고서", "분기보고서"). None이면 전체.
        window: 이벤트 윈도우 설정. None이면 기본값 (-10, +20).
        min_events: 최소 이벤트 수 (미달 시 None 반환).

    Returns:
        EventStudyResult 또는 None.
    """
    if window is None:
        window = EventWindow()

    stock_code = getattr(company, "stockCode", "")
    corp_name = getattr(company, "corpName", None)
    market = getattr(company, "market", "KR")

    # 1. 공시 발표일 목록
    filings_df = company.filings()
    if filings_df is None or filings_df.height == 0:
        return None

    if event_type is not None and "reportType" in filings_df.columns:
        filings_df = filings_df.filter(pl.col("reportType").str.contains(event_type))

    if filings_df.height < min_events:
        return None

    # 발표일 추출
    date_col = "rceptDate" if "rceptDate" in filings_df.columns else "filedDate"
    if date_col not in filings_df.columns:
        return None

    event_dates = []
    type_col = "reportType" if "reportType" in filings_df.columns else "formType"
    for row in filings_df.iter_rows(named=True):
        raw_date = str(row.get(date_col, ""))
        if raw_date and len(raw_date) >= 8:
            try:
                event_dates.append((_parse_date(raw_date), row.get(type_col, "")))
            except (ValueError, IndexError):
                continue

    if len(event_dates) < min_events:
        return None

    # 2. 주가 데이터 로드 (전체 기간)
    event_dates.sort(key=lambda x: x[0])
    earliest = event_dates[0][0] - timedelta(days=window.estimation_days + window.pre * 2)
    latest = event_dates[-1][0] + timedelta(days=window.post * 2)

    from dartlab.engines.event.price import get_market_returns, get_prices

    stock_prices = get_prices(
        stock_code,
        start=earliest.isoformat(),
        end=latest.isoformat(),
        market=market,
    )

    if stock_prices.height < window.total:
        return None

    market_prices = get_market_returns(
        start=earliest.isoformat(),
        end=latest.isoformat(),
        market=market,
    )

    # 3. 각 이벤트별 CAR 계산
    impacts: list[EventImpact] = []

    for event_date, event_tp in event_dates:
        result = _compute_abnormal_returns(
            stock_prices,
            market_prices,
            event_date,
            window,
        )
        if result is None:
            continue

        impacts.append(
            EventImpact(
                eventDate=event_date.isoformat(),
                eventType=event_tp,
                stockCode=stock_code,
                corpName=corp_name,
                car=round(result["car"], 6),
                bhar=round(result["bhar"], 6),
                car_tstat=round(result["t_stat"], 4),
                car_pvalue=round(result["p_value"], 6),
                pre_car=round(result["pre_car"], 6),
                post_car=round(result["post_car"], 6),
                window=window,
            )
        )

    if not impacts:
        return None

    # 4. 집계
    cars = [e.car for e in impacts]
    sorted_cars = sorted(cars)
    mean_car = sum(cars) / len(cars)
    median_car = sorted_cars[len(sorted_cars) // 2]
    significant_count = sum(1 for e in impacts if e.car_pvalue < 0.05)
    pre_leak_count = sum(1 for e in impacts if abs(e.pre_car) > 0.02)

    return EventStudyResult(
        stockCode=stock_code,
        corpName=corp_name,
        eventCount=len(impacts),
        impacts=impacts,
        meanCar=round(mean_car, 6),
        medianCar=round(median_car, 6),
        significantCount=significant_count,
        preLeakageCount=pre_leak_count,
    )


def impacts_to_dataframe(impacts: list[EventImpact]) -> pl.DataFrame:
    """EventImpact 리스트를 DataFrame으로 변환."""
    if not impacts:
        return pl.DataFrame(
            schema={
                "eventDate": pl.Utf8,
                "eventType": pl.Utf8,
                "car": pl.Float64,
                "bhar": pl.Float64,
                "car_tstat": pl.Float64,
                "car_pvalue": pl.Float64,
                "pre_car": pl.Float64,
                "post_car": pl.Float64,
                "significant": pl.Boolean,
            }
        )
    return pl.DataFrame(
        [
            {
                "eventDate": e.eventDate,
                "eventType": e.eventType,
                "car": e.car,
                "bhar": e.bhar,
                "car_tstat": e.car_tstat,
                "car_pvalue": e.car_pvalue,
                "pre_car": e.pre_car,
                "post_car": e.post_car,
                "significant": e.car_pvalue < 0.05,
            }
            for e in impacts
        ]
    )
