"""macro 엔진 공통 헬퍼."""

from __future__ import annotations

from datetime import datetime, timedelta


def recent_timeseries(df, months: int = 6, value_col: str = "value") -> list[dict] | None:
    """gather DataFrame에서 최근 N개월분을 slice해서 [{date, value}] 리스트로 반환.

    gather가 반환하는 Polars DataFrame(date, value 컬럼)을 소비.
    """
    if df is None or len(df) == 0:
        return None

    try:
        cutoff = datetime.now() - timedelta(days=months * 30)
        filtered = df.filter(df["date"] >= cutoff).sort("date")
        if len(filtered) == 0:
            return None

        dates = filtered.get_column("date").to_list()
        vals = filtered.get_column(value_col).to_list()

        return [
            {
                "date": str(d)[:10] if hasattr(d, "isoformat") else str(d)[:10],
                "value": float(v) if v is not None else None,
            }
            for d, v in zip(dates, vals)
            if v is not None
        ]
    except Exception:
        return None
