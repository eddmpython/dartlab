"""macro 엔진 공통 헬퍼."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

log = logging.getLogger(__name__)


def recent_timeseries(df, months: int = 6, value_col: str = "value") -> list[dict] | None:
    """gather DataFrame에서 최근 N개월분을 [{date, value}] 리스트로 반환."""
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
            {"date": str(d)[:10], "value": float(v) if v is not None else None}
            for d, v in zip(dates, vals)
            if v is not None
        ]
    except (KeyError, ValueError, TypeError):
        return None


def apply_as_of(df, as_of: str | None):
    """as_of 날짜까지만 필터링. 백테스트용."""
    if as_of is None or df is None or len(df) == 0:
        return df
    try:
        cutoff = datetime.strptime(as_of, "%Y-%m-%d").date() if isinstance(as_of, str) else as_of
        return df.filter(df["date"] <= cutoff)
    except (ValueError, TypeError):
        return df


def apply_overrides(data: dict, overrides: dict | None) -> dict:
    """overrides dict를 data에 병합. 시나리오 시뮬레이션용."""
    if overrides:
        data.update(overrides)
    return data


# ══════════════════════════════════════
# 공통 fetch 헬퍼 — 90회 중복 제거
# ══════════════════════════════════════


def get_gather(as_of: str | None = None):
    """gather 인스턴스를 1회만 생성. as_of가 있으면 자동 필터링.

    모든 L2 모듈의 _fetch_* 함수에서 이것을 사용.
    """
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    if as_of is None:
        return g

    _orig = g.macro

    def _filtered(sid):
        return apply_as_of(_orig(sid), as_of)

    import copy

    gc = copy.copy(g)
    gc.macro = _filtered  # type: ignore
    return gc


def fetch_latest(g, series_id: str) -> float | None:
    """시리즈의 최신값 1개를 가져온다. 실패 시 None + 로깅."""
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) > 0:
                return float(vals[-1])
    except Exception as e:
        log.debug("fetch_latest(%s) 실패: %s", series_id, e)
    return None


def fetch_latest_with_prev(g, series_id: str) -> tuple[float | None, float | None]:
    """최신값 + 직전값. 모멘텀 계산용."""
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) >= 2:
                return float(vals[-1]), float(vals[-2])
            if len(vals) == 1:
                return float(vals[-1]), None
    except Exception as e:
        log.debug("fetch_latest_with_prev(%s) 실패: %s", series_id, e)
    return None, None


def fetch_series_list(g, series_id: str) -> list[float] | None:
    """전체 시계열을 float 리스트로. Hamilton/Sahm/FCI 등에 사용."""
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls().to_list()
            if vals:
                return [float(v) for v in vals]
    except Exception as e:
        log.debug("fetch_series_list(%s) 실패: %s", series_id, e)
    return None


def fetch_yoy(g, series_id: str) -> float | None:
    """12개월 전 대비 YoY 변화율 (%)."""
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) >= 13:
                current = float(vals[-1])
                prev = float(vals[-13])
                if prev != 0:
                    return ((current - prev) / abs(prev)) * 100
    except Exception as e:
        log.debug("fetch_yoy(%s) 실패: %s", series_id, e)
    return None


def fetch_change_pct(g, series_id: str, lookback: int = 63) -> float | None:
    """lookback 관측치 전 대비 변화율 (%). 기본 63 ≈ 3개월(일간)."""
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls()
            if len(vals) > lookback:
                current = float(vals[-1])
                old = float(vals[-lookback])
                if old != 0:
                    return ((current - old) / abs(old)) * 100
    except Exception as e:
        log.debug("fetch_change_pct(%s) 실패: %s", series_id, e)
    return None


def fetch_with_history(g, series_id: str) -> dict[str, float | None]:
    """최신, 직전, 6개월전 값을 한 번에. forecast용."""
    result: dict[str, float | None] = {}
    try:
        df = g.macro(series_id)
        if df is not None and len(df) > 0:
            vals = df.get_column("value").drop_nulls().to_list()
            if vals:
                result["current"] = float(vals[-1])
                if len(vals) > 1:
                    result["prev"] = float(vals[-2])
                if len(vals) > 6:
                    result["6m"] = float(vals[-7])
    except Exception as e:
        log.debug("fetch_with_history(%s) 실패: %s", series_id, e)
    return result


def collect_timeseries(g, series_map: dict[str, str]) -> dict[str, list[dict] | None]:
    """여러 시리즈의 최근 시계열을 일괄 수집."""
    ts: dict[str, list[dict] | None] = {}
    for label, sid in series_map.items():
        try:
            ts[label] = recent_timeseries(g.macro(sid))
        except (KeyError, ValueError, TypeError, AttributeError):
            ts[label] = None
    return ts
