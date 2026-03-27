"""market Super Tool — 시장 데이터 통합 dispatcher.

통합 대상: get_current_price, get_consensus, get_fund_flow, get_price_history,
screen_market, benchmark_sector
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import format_tool_value


def registerMarketTool(registerTool: Callable) -> None:
    """market Super Tool 등록."""

    def _price(code: str = "", **_kw) -> str:
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            from dartlab.gather.naver import getCurrentPrice

            result = getCurrentPrice(code)
            return format_tool_value(result, max_rows=5, max_chars=1000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 현재가 조회 실패: {e}. 네트워크 연결을 확인하세요."

    def _consensus(code: str = "", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.gather.naver import getConsensus

            result = getConsensus(code)
            return format_tool_value(result, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return (
                f"[오류] 컨센서스 조회 실패: {e}. 대안: analyze(action='valuation')으로 자체 밸류에이션을 확인하세요."
            )

    def _history(code: str = "", days: str = "365", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.gather.naver import getPriceHistory

            result = getPriceHistory(code, days=int(days))
            return format_tool_value(result, max_rows=30, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 주가 이력 조회 실패: {e}. 네트워크 연결을 확인하세요."

    def _screen(criteria: str = "", **_kw) -> str:
        if not criteria:
            return "criteria(조건)를 지정하세요."
        try:
            from dartlab.ai.tools.defaults.scan import _screen_market_impl

            return _screen_market_impl(criteria)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 스크리닝 실패: {e}"

    def _scan(code: str = "", **_kw) -> str:
        """종목 시장 포지셔닝 조회 (ratio 기반 경량 판정)."""
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            import dartlab

            c = dartlab.Company(code)
            from dartlab.ai.context.company_adapter import get_headline_ratios

            r = get_headline_ratios(c)
            if r is None:
                return f"[데이터 없음] {code} 재무비율 계산 불가."
            lines = [f"## {getattr(c, 'corpName', code)} 시장 포지셔닝"]

            # 시총 순위
            try:
                from dartlab.analysis.comparative.rank import getRank

                rank = getRank(code)
                if rank is not None:
                    pctile = getattr(rank, "percentile", None)
                    if pctile is not None:
                        lines.append(f"- 시총순위: 상위 {pctile:.0f}%")
            except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError):
                pass

            # 핵심 지표 요약
            if r.roe is not None:
                lines.append(f"- ROE: {r.roe:.1f}%")
            if r.debtRatio is not None:
                lines.append(f"- 부채비율: {r.debtRatio:.1f}%")
            if r.currentRatio is not None:
                lines.append(f"- 유동비율: {r.currentRatio:.1f}%")
            pf = getattr(r, "piotroskiFScore", None)
            if pf is not None:
                lines.append(f"- Piotroski F-Score: {pf}/9")
            az = getattr(r, "altmanZScore", None)
            if az is not None:
                zone = "안전" if az > 2.99 else ("회색" if az >= 1.81 else "부실위험")
                lines.append(f"- Altman Z-Score: {az:.2f} ({zone})")
            if r.fcf is not None:
                from dartlab.ai.context.formatting import _format_won

                lines.append(f"- FCF: {_format_won(r.fcf)}")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 포지셔닝 조회 실패: {e}"

    def _peer(code: str = "", **_kw) -> str:
        """동종업 피어 비교."""
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            from dartlab.analysis.comparative.peer.discover import discover

            result = discover(code, topK=5)
            return format_tool_value(result, max_rows=10, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 피어 발견 실패: {e}. 대안: analyze(action='sector')로 업종 정보를 확인하세요."

    def _financials(code: str = "", statement: str = "IS", **_kw) -> str:
        """code 기반 재무제표 조회 (company 없이 즉석 로드)."""
        if not code:
            return "code(종목코드)를 지정하세요."
        stmt = statement.upper()
        if stmt not in ("BS", "IS", "CF", "CIS"):
            return f"statement는 BS/IS/CF/CIS 중 하나: {statement}"
        try:
            import dartlab

            c = dartlab.Company(code)
            df = getattr(c, stmt, None)
            if df is None or len(df) == 0:
                return f"[데이터 없음] {code} {stmt} 재무제표 없음."
            return format_tool_value(df, max_rows=40, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] {stmt} 조회 실패: {e}. 종목코드가 정확한지 system(action='searchCompany', keyword='종목명')으로 확인하세요."

    def _ratios(code: str = "", **_kw) -> str:
        """code 기반 재무비율 조회 (company 없이 즉석 로드)."""
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            import dartlab

            c = dartlab.Company(code)
            r = c.ratios
            if r is None:
                return f"[데이터 없음] {code} 재무비율 계산 불가."
            return format_tool_value(r, max_rows=30, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 재무비율 조회 실패: {e}. 종목코드가 정확한지 system(action='searchCompany', keyword='종목명')으로 확인하세요."

    _ACTIONS = {
        "price": _price,
        "consensus": _consensus,
        "history": _history,
        "screen": _screen,
        "scan": _scan,
        "peer": _peer,
        "financials": _financials,
        "ratios": _ratios,
    }

    def market(action: str, code: str = "", days: str = "365", criteria: str = "", statement: str = "IS") -> str:
        """시장 데이터 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(code=code, days=days, criteria=criteria, statement=statement)

    registerTool(
        "market",
        market,
        "시장/주가/재무 데이터 조회 — 현재가, 컨센서스, 주가이력, 포지셔닝, 피어, 재무제표, 재무비율.\n"
        "\n"
        "✓ company가 로드되지 않아도 code만으로 모든 종목의 재무/시장 데이터 조회 가능.\n"
        "✓ 비교 분석: 여러 종목을 각각 조회 후 비교 테이블 구성.\n"
        "\n"
        "action별 동작:\n"
        "- price: 현재 주가 (code 필수). 예: market(action='price', code='005930')\n"
        "- consensus: 애널리스트 컨센서스 (code 필수)\n"
        "- history: 주가 이력 (code 필수, days 선택)\n"
        "- screen: 시장 스크리닝 (criteria 필수)\n"
        "- scan: 종목 시장 포지셔닝 (시총순위, 핵심지표, 부실점수). code 필수\n"
        "- peer: TF-IDF 사업유사도 기반 경쟁사 발견. code 필수\n"
        "- financials: 재무제표 조회 (code, statement='BS'/'IS'/'CF'/'CIS')\n"
        "- ratios: 핵심 재무비율 조회 (code 필수)\n"
        "\n"
        "주가 데이터는 외부 소스(Naver Finance)입니다. 재무 데이터와 시점이 다를 수 있습니다.\n"
        "\n"
        "반환: 마크다운 텍스트 (주가, 테이블). 조회 실패 시 '[오류]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["price", "consensus", "history", "screen", "scan", "peer", "financials", "ratios"],
                    "description": "price=현재가, consensus=컨센서스, history=주가이력, screen=스크리닝, scan=포지셔닝, peer=경쟁사발견, financials=재무제표, ratios=재무비율",
                },
                "code": {
                    "type": "string",
                    "description": "종목코드 (예: 005930)",
                    "default": "",
                },
                "days": {
                    "type": "string",
                    "description": "주가이력 기간(일). 기본 365",
                    "default": "365",
                },
                "criteria": {
                    "type": "string",
                    "description": "스크리닝 조건 (action=screen일 때)",
                    "default": "",
                },
                "statement": {
                    "type": "string",
                    "description": "재무제표 종류 (action=financials일 때): BS/IS/CF/CIS",
                    "default": "IS",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("투자", "종합"),
        priority=70,
    )
