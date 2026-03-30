"""배당 추이 스캔 -- DPS 3개년 시계열 + 패턴 분류."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import parse_num, scan_parquets


def _classifyPattern(
    dps0: float | None,
    dps1: float | None,
    dps2: float | None,
) -> str:
    """3개년 DPS → 패턴 분류.

    dps0=당기, dps1=전기, dps2=전전기.
    """
    has0 = dps0 is not None and dps0 > 0
    has1 = dps1 is not None and dps1 > 0
    has2 = dps2 is not None and dps2 > 0

    if not has0 and not has1 and not has2:
        return "무배당"
    if has0 and not has1:
        return "시작"
    if not has0 and has1:
        return "중단"
    if has0 and has1 and has2:
        if dps0 > dps1 > dps2:
            return "연속증가"
        if dps0 < dps1 < dps2:
            return "연속감소"
        # +-10% 이내 안정
        if dps1 > 0 and abs(dps0 - dps1) / dps1 <= 0.1:
            return "안정"
        if dps0 >= dps1:
            return "증가"
        return "감소"
    if has0 and has1:
        if dps0 > dps1:
            return "증가"
        if dps0 < dps1:
            return "감소"
        return "안정"
    return "불규칙"


def _gradeDividend(pattern: str, dpsGrowth: float | None) -> str:
    """배당 등급."""
    if pattern == "무배당":
        return "무배당"
    if pattern in ("연속증가",):
        return "우수"
    if pattern in ("안정", "증가"):
        return "양호"
    if pattern == "시작":
        return "양호"
    if pattern in ("감소", "연속감소"):
        return "주의"
    if pattern == "중단":
        return "위험"
    return "보통"


def scanDividendTrend(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 배당 추이 스캔 -- DPS 3개년 + 패턴 + 등급."""
    raw = scan_parquets(
        "dividend",
        ["stockCode", "year", "quarter", "se", "thstrm", "frmtrm", "lwfr", "stock_knd"],
    )
    if raw.is_empty():
        return pl.DataFrame()

    if verbose:
        print(f"배당 추이 스캔: {raw.shape[0]}행 로드")

    # 보통주 + 주당 현금배당금 + Q4 우선
    dpsRows = raw.filter((pl.col("se") == "주당 현금배당금(원)") & (pl.col("stock_knd") == "보통주"))

    # 배당수익률
    yieldRows = raw.filter((pl.col("se") == "현금배당수익률(%)") & (pl.col("stock_knd") == "보통주"))

    # 배당성향 (연결 우선)
    payoutRows = raw.filter(pl.col("se") == "(연결)현금배당성향(%)")

    # 최신 연도 기준
    years = sorted(
        [y for y in dpsRows["year"].unique().to_list() if str(y).strip().isdigit()],
        reverse=True,
    )
    if not years:
        return pl.DataFrame()

    # Q4 기준 유효 데이터 500종목 이상인 최신 연도 (결산 완료 연도)
    latestYear = None
    for y in years:
        q4sub = dpsRows.filter((pl.col("year") == y) & (pl.col("quarter") == "4분기"))
        if q4sub["stockCode"].n_unique() >= 500:
            latestYear = y
            break
    if latestYear is None:
        latestYear = years[0]

    if verbose:
        print(f"  기준 연도: {latestYear}")

    rows: list[dict] = []
    allCodes = dpsRows["stockCode"].unique().to_list()

    for code in allCodes:
        codeDps = dpsRows.filter(pl.col("stockCode") == code)

        # Q4 우선, 최신 연도
        yearSub = codeDps.filter(pl.col("year") == latestYear)
        if yearSub.is_empty():
            # 해당 연도 없으면 가장 최근 데이터 사용
            codeYears = sorted(codeDps["year"].unique().to_list(), reverse=True)
            if not codeYears:
                continue
            yearSub = codeDps.filter(pl.col("year") == codeYears[0])

        q4 = yearSub.filter(pl.col("quarter") == "4분기")
        best = q4 if not q4.is_empty() else yearSub
        row = best.row(0, named=True)

        dps0 = parse_num(row.get("thstrm"))
        dps1 = parse_num(row.get("frmtrm"))
        dps2 = parse_num(row.get("lwfr"))

        # 배당수익률
        yieldVal = None
        yieldSub = yieldRows.filter((pl.col("stockCode") == code) & (pl.col("year") == latestYear))
        if not yieldSub.is_empty():
            yq4 = yieldSub.filter(pl.col("quarter") == "4분기")
            yBest = yq4 if not yq4.is_empty() else yieldSub
            yieldVal = parse_num(yBest.row(0, named=True).get("thstrm"))

        # 배당성향
        payoutVal = None
        payoutSub = payoutRows.filter((pl.col("stockCode") == code) & (pl.col("year") == latestYear))
        if not payoutSub.is_empty():
            pq4 = payoutSub.filter(pl.col("quarter") == "4분기")
            pBest = pq4 if not pq4.is_empty() else payoutSub
            payoutVal = parse_num(pBest.row(0, named=True).get("thstrm"))

        # DPS 성장률
        dpsGrowth = None
        if dps0 is not None and dps1 is not None and dps1 > 0:
            dpsGrowth = round((dps0 - dps1) / dps1 * 100, 1)

        pattern = _classifyPattern(dps0, dps1, dps2)

        rows.append(
            {
                "stockCode": code,
                "dpsCurrent": dps0,
                "dpsPrev": dps1,
                "dpsPrev2": dps2,
                "dpsGrowth": dpsGrowth,
                "payoutRatio": payoutVal,
                "yieldCurrent": yieldVal,
                "pattern": pattern,
                "grade": _gradeDividend(pattern, dpsGrowth),
            }
        )

    if verbose:
        print(f"배당 추이 스캔 완료: {len(rows)}종목")

    if not rows:
        return pl.DataFrame()

    schema = {
        "stockCode": pl.Utf8,
        "dpsCurrent": pl.Float64,
        "dpsPrev": pl.Float64,
        "dpsPrev2": pl.Float64,
        "dpsGrowth": pl.Float64,
        "payoutRatio": pl.Float64,
        "yieldCurrent": pl.Float64,
        "pattern": pl.Utf8,
        "grade": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)


__all__ = ["scanDividendTrend"]
