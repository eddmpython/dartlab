"""시장 데이터 도구 — Gather 엔진 래핑."""

from __future__ import annotations

from typing import Any

_gather_instance: Any = None


def _get_gather() -> Any:
    """Gather 인스턴스 lazy singleton."""
    global _gather_instance  # noqa: PLW0603
    if _gather_instance is None:
        from dartlab.engines.gather import Gather

        _gather_instance = Gather()
    return _gather_instance


def register_market_tools(register_tool) -> None:
    """시장 데이터 도구를 등록한다 (company 바인딩 불필요)."""

    # ── get_current_price ──

    def get_current_price(stockCode: str, market: str = "KR") -> str:
        """현재 주가 조회."""
        try:
            g = _get_gather()
            snap = g.price(stockCode, market=market)
            if snap is None:
                return f"{stockCode} 주가 데이터를 가져올 수 없습니다."
            lines = [f"종목: {stockCode}"]
            if hasattr(snap, "price") and snap.price is not None:
                lines.append(f"현재가: {snap.price:,.0f}")
            if hasattr(snap, "change") and snap.change is not None:
                lines.append(f"전일대비: {snap.change:+,.0f}")
            if hasattr(snap, "changePercent") and snap.changePercent is not None:
                lines.append(f"등락률: {snap.changePercent:+.2f}%")
            if hasattr(snap, "volume") and snap.volume is not None:
                lines.append(f"거래량: {snap.volume:,.0f}")
            return "\n".join(lines)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"주가 조회 실패: {e}"

    register_tool(
        "get_current_price",
        get_current_price,
        "종목의 현재 주가, 등락률, 거래량을 조회합니다. "
        "네이버 → 야후 파이낸스 fallback 체인으로 실시간 데이터를 가져옵니다. "
        "사용 시점: '현재 주가', '오늘 주가', '시세', '거래량' 질문.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (예: '005930') 또는 티커 (예: 'AAPL')",
                },
                "market": {
                    "type": "string",
                    "description": "시장 ('KR' 또는 'US')",
                    "default": "KR",
                },
            },
            "required": ["stockCode"],
        },
        category="market",
        questionTypes=("투자", "밸류에이션"),
        priority=80,
    )

    # ── get_consensus ──

    def get_consensus(stockCode: str) -> str:
        """컨센서스 조회."""
        try:
            g = _get_gather()
            data = g.consensus(stockCode)
            if data is None:
                return f"{stockCode} 컨센서스 데이터를 가져올 수 없습니다."
            lines = [f"종목: {stockCode}"]
            if hasattr(data, "targetPrice") and data.targetPrice is not None:
                lines.append(f"목표가: {data.targetPrice:,.0f}")
            if hasattr(data, "rating") and data.rating is not None:
                lines.append(f"투자의견: {data.rating}")
            if hasattr(data, "analystCount") and data.analystCount is not None:
                lines.append(f"분석가 수: {data.analystCount}명")
            return "\n".join(lines)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"컨센서스 조회 실패: {e}"

    register_tool(
        "get_consensus",
        get_consensus,
        "증권사 컨센서스 목표가와 투자의견을 조회합니다. "
        "사용 시점: '목표가', '컨센서스', '증권사 의견', '투자 등급' 질문.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (예: '005930')",
                },
            },
            "required": ["stockCode"],
        },
        category="market",
        questionTypes=("투자", "밸류에이션"),
        priority=75,
    )

    # ── get_fund_flow ──

    def get_fund_flow(stockCode: str) -> str:
        """기관/외국인 수급 조회."""
        try:
            g = _get_gather()
            data = g.flow(stockCode)
            if data is None:
                return f"{stockCode} 수급 데이터를 가져올 수 없습니다."
            lines = [f"종목: {stockCode}"]
            if hasattr(data, "foreignNet") and data.foreignNet is not None:
                lines.append(f"외국인 순매수: {data.foreignNet:+,.0f}")
            if hasattr(data, "institutionNet") and data.institutionNet is not None:
                lines.append(f"기관 순매수: {data.institutionNet:+,.0f}")
            if hasattr(data, "individualNet") and data.individualNet is not None:
                lines.append(f"개인 순매수: {data.individualNet:+,.0f}")
            return "\n".join(lines)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"수급 조회 실패: {e}"

    register_tool(
        "get_fund_flow",
        get_fund_flow,
        "기관, 외국인, 개인의 매매 동향(순매수)을 조회합니다. 사용 시점: '수급', '외국인', '기관 동향', '순매수' 질문.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (예: '005930')",
                },
            },
            "required": ["stockCode"],
        },
        category="market",
        questionTypes=("투자",),
        priority=65,
    )

    # ── get_price_history ──

    def get_price_history(stockCode: str, start: str = "", end: str = "") -> str:
        """기간 주가 이력 조회."""
        try:
            g = _get_gather()
            data = g.history(stockCode, start=start or None, end=end or None)
            if not data:
                return f"{stockCode} 주가 이력을 가져올 수 없습니다."
            lines = ["| 날짜 | 종가 | 변동률 | 거래량 |", "| --- | --- | --- | --- |"]
            for row in data[-20:]:  # 최근 20일
                date = row.get("date", "")
                close = row.get("close", 0)
                change_pct = row.get("changePercent", 0)
                volume = row.get("volume", 0)
                lines.append(f"| {date} | {close:,.0f} | {change_pct:+.2f}% | {volume:,.0f} |")
            if len(data) > 20:
                lines.append(f"\n(전체 {len(data)}일 중 최근 20일만 표시)")
            return "\n".join(lines)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"주가 이력 조회 실패: {e}"

    register_tool(
        "get_price_history",
        get_price_history,
        "기간별 주가 이력(OHLCV)을 조회합니다. 차트 분석, 추세 확인에 사용합니다. "
        "사용 시점: '주가 추이', '차트', '최근 N일 주가' 질문.",
        {
            "type": "object",
            "properties": {
                "stockCode": {
                    "type": "string",
                    "description": "종목코드 (예: '005930')",
                },
                "start": {
                    "type": "string",
                    "description": "시작일 (YYYY-MM-DD, 비워두면 최근 3개월)",
                    "default": "",
                },
                "end": {
                    "type": "string",
                    "description": "종료일 (YYYY-MM-DD, 비워두면 오늘)",
                    "default": "",
                },
            },
            "required": ["stockCode"],
        },
        category="market",
        questionTypes=("투자",),
        priority=60,
    )
