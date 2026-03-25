"""100_globalFramework 실험 공통 헬퍼."""


def toAnnual(series: dict, periods: list[str], sjDiv: str, snakeId: str) -> dict[str, float]:
    """분기 시계열을 연간으로 집계.

    IS/CF: Q1+Q2+Q3+Q4 합산. BS: Q4값만.
    Returns: { '2016': value, '2017': value, ... }
    """
    vals = series.get(sjDiv, {}).get(snakeId, [])
    if not vals:
        return {}
    result: dict[str, float] = {}
    for i, period in enumerate(periods):
        if i >= len(vals):
            break
        year = period.split("-")[0]
        val = vals[i]
        if val is None:
            continue
        if sjDiv == "BS":
            if period.endswith("Q4"):
                result[year] = val
        else:
            result[year] = result.get(year, 0) + val
    return result


def annualValues(series: dict, periods: list[str], sjDiv: str, snakeId: str) -> list[float]:
    """연간 집계된 값을 연도순 리스트로 반환 (None 제외)."""
    d = toAnnual(series, periods, sjDiv, snakeId)
    return [d[y] for y in sorted(d)]


def annualDict(series: dict, periods: list[str], sjDiv: str, snakeId: str) -> dict[str, float]:
    """연간 집계된 값을 연도순 dict로 반환."""
    d = toAnnual(series, periods, sjDiv, snakeId)
    return dict(sorted(d.items()))


def loadCompany(stockCode: str, name: str):
    """Company 로드 + timeseries 분리."""
    import dartlab

    try:
        c = dartlab.Company(stockCode)
        ts = c.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
        periods = ts[1] if isinstance(ts, tuple) else []
        return series, periods
    except Exception as e:
        print(f"  [{stockCode}] {name}: 로드 실패 — {e}")
        return None, None
