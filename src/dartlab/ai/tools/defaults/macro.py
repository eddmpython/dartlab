"""매크로 경제지표 도구 — FRED API 기반.

Global 카테고리 (Company 없이 동작).
LLM이 경제지표를 직접 조회·비교·분석할 수 있게 한다.
"""

from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)


def register_macro_tools(register_tool: Callable) -> None:
    """매크로 경제지표 도구를 등록한다."""
    from dartlab.core.capabilities import CapabilityKind

    # ── fred_series ──

    def fred_series(
        series_id: str,
        start: str | None = None,
        end: str | None = None,
        transform: str = "raw",
        window: int = 12,
    ) -> str:
        from dartlab.gather.fred import Fred
        from dartlab.gather.fred.types import FredError

        try:
            f = Fred()
        except FredError as exc:
            return f"FRED API 키 오류: {exc}"

        try:
            if transform == "yoy":
                df = f.yoy(series_id, start=start, end=end)
            elif transform == "mom":
                df = f.mom(series_id, start=start, end=end)
            elif transform == "ma":
                df = f.movingAverage(series_id, window=window, start=start, end=end)
            else:
                df = f.series(series_id, start=start, end=end)
        except FredError as exc:
            return f"FRED 오류: {exc}"

        if df.is_empty():
            return f"'{series_id}' 데이터가 없습니다."

        # 최근 24행만 반환 (토큰 절약)
        recent = df.tail(24)
        meta = f.meta(series_id)
        header = f"**{meta.title}** ({meta.units}, {meta.frequency})\n"
        return header + recent.to_pandas().to_markdown(index=False)

    register_tool(
        "fred_series",
        fred_series,
        "FRED 경제지표 시계열 조회. GDP, 실업률, CPI, 금리 등 80만+ 시리즈 조회 가능. "
        "transform으로 YoY/MoM/이동평균 변환 적용 가능.",
        {
            "type": "object",
            "properties": {
                "series_id": {
                    "type": "string",
                    "description": "FRED 시리즈 ID (예: GDP, UNRATE, CPIAUCSL, FEDFUNDS, SP500)",
                },
                "start": {
                    "type": "string",
                    "description": "시작일 (YYYY-MM-DD). 생략하면 전체 기간.",
                },
                "end": {
                    "type": "string",
                    "description": "종료일 (YYYY-MM-DD). 생략하면 최신까지.",
                },
                "transform": {
                    "type": "string",
                    "enum": ["raw", "yoy", "mom", "ma"],
                    "description": "변환: raw(원본), yoy(전년비%), mom(전월비%), ma(이동평균). 기본: raw.",
                },
                "window": {
                    "type": "integer",
                    "description": "이동평균 윈도우 (transform=ma일 때). 기본: 12.",
                },
            },
            "required": ["series_id"],
        },
        kind=CapabilityKind.DATA,
    )

    # ── fred_search ──

    def fred_search(query: str, limit: int = 10) -> str:
        from dartlab.gather.fred import Fred
        from dartlab.gather.fred.types import FredError

        try:
            f = Fred()
            df = f.search(query, limit=limit)
        except FredError as exc:
            return f"FRED 오류: {exc}"

        if df.is_empty():
            return f"'{query}' 검색 결과가 없습니다."

        return df.select("id", "title", "frequency", "units", "popularity").to_pandas().to_markdown(index=False)

    register_tool(
        "fred_search",
        fred_search,
        "FRED 시리즈 검색. 키워드로 관련 경제지표를 찾습니다. "
        "시리즈 ID를 모를 때 사용하세요. 예: 'inflation', 'unemployment', 'housing'.",
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색 키워드 (영문). 예: 'GDP', 'consumer price', 'unemployment rate'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "최대 결과 수 (기본: 10).",
                },
            },
            "required": ["query"],
        },
        kind=CapabilityKind.DATA,
    )

    # ── fred_compare ──

    def fred_compare(
        series_ids: list[str],
        start: str | None = None,
        end: str | None = None,
        normalize_to: str | None = None,
    ) -> str:
        from dartlab.gather.fred import Fred
        from dartlab.gather.fred import transform as _transform
        from dartlab.gather.fred.types import FredError

        try:
            f = Fred()
            df = f.compare(series_ids, start=start, end=end)
        except FredError as exc:
            return f"FRED 오류: {exc}"

        if df.is_empty():
            return "데이터가 없습니다."

        if normalize_to:
            df = _transform.normalize_multi(df, base_date=normalize_to)

        recent = df.tail(24)
        return recent.to_pandas().to_markdown(index=False)

    register_tool(
        "fred_compare",
        fred_compare,
        "복수 FRED 시계열을 나란히 비교합니다. normalize_to로 기준일=100 정규화하면 단위가 다른 지표도 추세 비교 가능.",
        {
            "type": "object",
            "properties": {
                "series_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": '비교할 시리즈 ID 목록 (예: ["GDP", "UNRATE", "FEDFUNDS"]).',
                },
                "start": {"type": "string", "description": "시작일 (YYYY-MM-DD)."},
                "end": {"type": "string", "description": "종료일 (YYYY-MM-DD)."},
                "normalize_to": {
                    "type": "string",
                    "description": "정규화 기준일 (YYYY-MM-DD). 지정하면 해당 날짜=100 기준.",
                },
            },
            "required": ["series_ids"],
        },
        kind=CapabilityKind.DATA,
    )

    # ── fred_catalog ──

    def fred_catalog(group: str | None = None) -> str:
        from dartlab.gather.fred import Fred
        from dartlab.gather.fred.types import FredError

        try:
            f = Fred()
            df = f.catalog(group)
        except FredError as exc:
            return f"FRED 오류: {exc}"

        if df.is_empty():
            from dartlab.gather.fred.catalog import get_groups

            return f"그룹을 찾을 수 없습니다. 사용 가능: {', '.join(get_groups())}"

        return df.to_pandas().to_markdown(index=False)

    register_tool(
        "fred_catalog",
        fred_catalog,
        "FRED 주요 경제지표 카탈로그 조회. "
        "그룹: growth(성장), inflation(물가), rates(금리), employment(고용), "
        "markets(시장), housing(주택), money(통화). "
        "그룹 미지정 시 전체 ~50개 핵심 지표 목록 반환.",
        {
            "type": "object",
            "properties": {
                "group": {
                    "type": "string",
                    "enum": ["growth", "inflation", "rates", "employment", "markets", "housing", "money"],
                    "description": "카탈로그 그룹. 생략하면 전체 목록.",
                },
            },
        },
        kind=CapabilityKind.DATA,
    )

    # ── fred_correlation ──

    def fred_correlation(
        series_ids: list[str],
        start: str | None = None,
        end: str | None = None,
        lead_lag_pair: list[str] | None = None,
        max_lag: int = 12,
    ) -> str:
        from dartlab.gather.fred import Fred
        from dartlab.gather.fred.types import FredError

        try:
            f = Fred()
        except FredError as exc:
            return f"FRED 오류: {exc}"

        parts: list[str] = []

        # 상관행렬
        if len(series_ids) >= 2:
            try:
                corr = f.correlation(series_ids, start=start, end=end)
                if not corr.is_empty():
                    parts.append("**상관행렬**\n" + corr.to_pandas().to_markdown(index=False))
            except FredError as exc:
                parts.append(f"상관분석 오류: {exc}")

        # 선행/후행 분석
        if lead_lag_pair and len(lead_lag_pair) == 2:
            try:
                ll = f.leadLag(lead_lag_pair[0], lead_lag_pair[1], max_lag=max_lag, start=start, end=end)
                if not ll.is_empty():
                    # 최대 상관 lag 찾기
                    best = ll.filter(pl.col("correlation").is_not_null()).sort("correlation", descending=True).head(1)
                    summary = ""
                    if not best.is_empty():
                        lag_val = best["lag"][0]
                        corr_val = best["correlation"][0]
                        direction = "선행" if lag_val < 0 else "후행" if lag_val > 0 else "동시"
                        summary = f"\n최대 상관: lag={lag_val} (r={corr_val:.4f}, {lead_lag_pair[1]}이 {abs(lag_val)}기간 {direction})"
                    parts.append(f"**선행/후행 분석** ({lead_lag_pair[0]} vs {lead_lag_pair[1]}){summary}")
            except FredError as exc:
                parts.append(f"선행/후행 분석 오류: {exc}")

        return "\n\n".join(parts) if parts else "분석할 데이터가 부족합니다. 시리즈 ID 2개 이상 필요."

    # lead_lag에서 polars 사용
    import polars as pl  # noqa: F811

    register_tool(
        "fred_correlation",
        fred_correlation,
        "FRED 시계열 간 상관분석. "
        "복수 시리즈의 상관행렬, 특정 쌍의 선행/후행(lead-lag) 관계를 분석합니다. "
        "예: 금리와 실업률의 시차 관계, GDP와 S&P500의 선행/후행 구조.",
        {
            "type": "object",
            "properties": {
                "series_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "상관분석할 시리즈 ID 목록 (2개 이상).",
                },
                "start": {"type": "string", "description": "시작일 (YYYY-MM-DD)."},
                "end": {"type": "string", "description": "종료일 (YYYY-MM-DD)."},
                "lead_lag_pair": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": '선행/후행 분석 대상 쌍 (예: ["FEDFUNDS", "UNRATE"]). 선택사항.',
                },
                "max_lag": {
                    "type": "integer",
                    "description": "선행/후행 최대 시차 (기본: 12).",
                },
            },
            "required": ["series_ids"],
        },
        kind=CapabilityKind.DATA,
    )
