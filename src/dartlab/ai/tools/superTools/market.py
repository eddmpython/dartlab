"""market Super Tool — 시장 데이터 통합 dispatcher.

3갈래 중 '전종목 비교' 축 담당:
- 주가/컨센서스 (외부)
- scanAccount/scanRatio (전종목 재무)
- governance/workforce/capital/debt (전종목 스캔)
- signal/benchmark/screen (전종목 분석)
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import df_to_md, format_tool_value


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
                from dartlab.scan.screen import getRank

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
            from dartlab.scan.peer.discover import discover

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

    # ── 전종목 비교 액션 (scan/ parquet 기반, Company 객체 불필요) ──

    def _scanAccount(code: str = "", snakeId: str = "", **_kw) -> str:
        """전종목 단일 계정 시계열 (scan/finance.parquet 직접 조회)."""
        if not snakeId:
            return "snakeId(계정ID)를 지정하세요. 예: sales, operatingIncome, totalAssets"
        try:
            from dartlab.providers.dart.finance.scanAccount import scanAccount

            df = scanAccount(snakeId)
            if df is None or len(df) == 0:
                return f"[데이터 없음] snakeId='{snakeId}' 전종목 데이터 없음."
            # 특정 종목 필터링
            if code:
                codes = [c.strip() for c in code.split(",")]
                df = df.filter(df["stockCode"].is_in(codes))
                if len(df) == 0:
                    return f"[데이터 없음] {code}의 {snakeId} 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] scanAccount 실패: {e}"

    def _scanRatio(code: str = "", ratioName: str = "", **_kw) -> str:
        """전종목 단일 비율 시계열 (scan/finance.parquet 직접 조회)."""
        if not ratioName:
            return "ratioName(비율명)을 지정하세요. 예: roe, debtRatio, operatingMargin, currentRatio"
        try:
            from dartlab.providers.dart.finance.scanAccount import scanRatio

            df = scanRatio(ratioName)
            if df is None or len(df) == 0:
                return f"[데이터 없음] ratioName='{ratioName}' 전종목 데이터 없음."
            if code:
                codes = [c.strip() for c in code.split(",")]
                df = df.filter(df["stockCode"].is_in(codes))
                if len(df) == 0:
                    return f"[데이터 없음] {code}의 {ratioName} 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] scanRatio 실패: {e}"

    def _scanRatioList(**_kw) -> str:
        """사용 가능한 비율 목록 조회."""
        try:
            import importlib.util

            if importlib.util.find_spec("dartlab.providers.dart.finance.scanAccount") is None:
                return "[오류] scanAccount 모듈을 찾을 수 없습니다."

            # roe로 한번 호출해서 컬럼 구조 확인하는 것보다 직접 목록 제공
            ratios = [
                "roe",
                "roa",
                "ros",
                "operatingMargin",
                "netMargin",
                "debtRatio",
                "currentRatio",
                "quickRatio",
                "interestCoverage",
                "assetTurnover",
                "inventoryTurnover",
                "receivableTurnover",
                "per",
                "pbr",
                "psr",
                "pcr",
                "evEbitda",
                "dividendYield",
                "payoutRatio",
                "salesGrowth",
                "operatingIncomeGrowth",
                "netIncomeGrowth",
            ]
            return "## 사용 가능한 비율 목록\n" + "\n".join(f"- {r}" for r in ratios)
        except (ImportError, AttributeError) as e:
            return f"[오류] 비율 목록 조회 실패: {e}"

    def _governance(**_kw) -> str:
        """전종목 지배구조 스캔."""
        try:
            from dartlab.scan.governance import scan_governance

            df = scan_governance(verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 지배구조 스캔 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 지배구조 스캔 실패: {e}"

    def _workforce(**_kw) -> str:
        """전종목 인력/급여 스캔."""
        try:
            from dartlab.scan.workforce import scan_workforce

            df = scan_workforce(verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 인력 스캔 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 인력 스캔 실패: {e}"

    def _capital(**_kw) -> str:
        """전종목 주주환원 스캔."""
        try:
            from dartlab.scan.capital import scan_capital

            df = scan_capital(verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 자본환원 스캔 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 자본환원 스캔 실패: {e}"

    def _debt(**_kw) -> str:
        """전종목 부채구조 스캔."""
        try:
            from dartlab.scan.debt import scan_debt

            df = scan_debt(verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 부채 스캔 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 부채 스캔 실패: {e}"

    def _signal(keyword: str = "", **_kw) -> str:
        """전종목 키워드 트렌드 (공시 텍스트 기반)."""
        try:
            from dartlab.scan.signal import scan_signal

            df = scan_signal(keyword=keyword or None, verbose=False)
            if df is None or len(df) == 0:
                msg = f"keyword='{keyword}'" if keyword else "전체"
                return f"[데이터 없음] {msg} 시그널 데이터 없음."
            return df_to_md(df, max_rows=30, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 시그널 조회 실패: {e}"

    def _benchmark(code: str = "", **_kw) -> str:
        """섹터별 비율 벤치마크 (P10/중위/P90)."""
        try:
            # benchmark = 전종목 주요 비율 통계
            from dartlab.providers.dart.finance.scanAccount import scanRatio

            df = scanRatio("roe")
            if df is None or len(df) == 0:
                return "[데이터 없음] 벤치마크 데이터 없음."
            # 최신 기간 컬럼의 통계
            periodCols = [c for c in df.columns if c not in ("stockCode", "corpName")]
            if not periodCols:
                return "[데이터 없음] 기간 데이터 없음."
            latest = periodCols[-1]
            import polars as pl

            stats = df.select(
                pl.lit("ROE").alias("지표"),
                pl.col(latest).mean().alias("평균"),
                pl.col(latest).median().alias("중위"),
                pl.col(latest).quantile(0.1).alias("P10"),
                pl.col(latest).quantile(0.9).alias("P90"),
                pl.col(latest).count().alias("종목수"),
            )
            return f"## 전종목 ROE 벤치마크 ({latest})\n" + df_to_md(stats, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 벤치마크 조회 실패: {e}"

    def _groupHealth(**_kw) -> str:
        """기업집단 재무건전성."""
        try:
            from dartlab.scan.governance import scan_governance

            df = scan_governance(verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 기업집단 데이터 없음."
            # 지배구조 점수 기준 하위 종목 추출
            if "총점" in df.columns:
                bottom = df.sort("총점").head(20)
                return "## 지배구조 취약 종목 (하위 20)\n" + df_to_md(bottom, max_rows=20, max_chars=3000)
            return df_to_md(df.head(20), max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 기업집단 건전성 조회 실패: {e}"

    _ACTIONS = {
        # 기존 액션
        "price": _price,
        "consensus": _consensus,
        "history": _history,
        "screen": _screen,
        "scan": _scan,
        "peer": _peer,
        "financials": _financials,
        "ratios": _ratios,
        # 전종목 비교 액션 (scan/ parquet 기반)
        "scanAccount": _scanAccount,
        "scanRatio": _scanRatio,
        "scanRatioList": _scanRatioList,
        "governance": _governance,
        "workforce": _workforce,
        "capital": _capital,
        "debt": _debt,
        "signal": _signal,
        "benchmark": _benchmark,
        "groupHealth": _groupHealth,
    }

    def market(
        action: str,
        code: str = "",
        days: str = "365",
        criteria: str = "",
        statement: str = "IS",
        snakeId: str = "",
        ratioName: str = "",
        keyword: str = "",
    ) -> str:
        """시장 데이터 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(
            code=code,
            days=days,
            criteria=criteria,
            statement=statement,
            snakeId=snakeId,
            ratioName=ratioName,
            keyword=keyword,
        )

    registerTool(
        "market",
        market,
        "시장/주가/재무 데이터 조회 + 전종목 비교 분석.\n"
        "\n"
        "company 로드 없이 code만으로 모든 종목 데이터 조회 가능.\n"
        "기업간 비교: scanAccount/scanRatio로 전종목 데이터에서 필터링.\n"
        "\n"
        "## 단일 종목\n"
        "- price: 현재 주가 (code 필수)\n"
        "- consensus: 애널리스트 컨센서스 (code 필수)\n"
        "- history: 주가 이력 (code, days)\n"
        "- scan: 종목 포지셔닝 (시총순위, 핵심지표). code 필수\n"
        "- peer: TF-IDF 사업유사도 경쟁사 발견. code 필수\n"
        "- financials: 재무제표 (code, statement=BS/IS/CF/CIS)\n"
        "- ratios: 재무비율 (code 필수)\n"
        "\n"
        "## 전종목 비교 (scan/ parquet, Company 객체 불필요)\n"
        "- scanAccount: 전종목 단일 계정 시계열. snakeId 필수 (예: sales, operatingIncome). code로 특정 종목 필터링 가능 (쉼표 구분)\n"
        "- scanRatio: 전종목 단일 비율 시계열. ratioName 필수 (예: roe, debtRatio). code로 필터링 가능\n"
        "- scanRatioList: 사용 가능한 비율 목록\n"
        "- governance: 전종목 지배구조 스캔 (지분율, 사외이사, 보수, 감사의견)\n"
        "- workforce: 전종목 인력/급여 스캔 (직원수, 평균급여, 근속년수)\n"
        "- capital: 전종목 주주환원 스캔 (배당, 자사주, 증자)\n"
        "- debt: 전종목 부채구조 스캔 (사채, 부채비율, ICR)\n"
        "- signal: 전종목 키워드 트렌드 (keyword 선택)\n"
        "- benchmark: 전종목 비율 통계 (P10/중위/P90)\n"
        "- groupHealth: 지배구조 취약 종목 조회\n"
        "- screen: 프리셋 스크리닝 (criteria 필수)\n"
        "\n"
        "기업 비교 패턴: scanAccount(snakeId='sales', code='005930,000660')으로 두 종목 매출 비교.\n"
        "\n"
        "반환: 마크다운 텍스트. 조회 실패 시 '[오류]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "price",
                        "consensus",
                        "history",
                        "screen",
                        "scan",
                        "peer",
                        "financials",
                        "ratios",
                        "scanAccount",
                        "scanRatio",
                        "scanRatioList",
                        "governance",
                        "workforce",
                        "capital",
                        "debt",
                        "signal",
                        "benchmark",
                        "groupHealth",
                    ],
                    "description": (
                        "price=현재가, consensus=컨센서스, history=주가이력, screen=스크리닝, "
                        "scan=포지셔닝, peer=경쟁사, financials=재무제표, ratios=재무비율, "
                        "scanAccount=전종목계정, scanRatio=전종목비율, scanRatioList=비율목록, "
                        "governance=지배구조, workforce=인력, capital=주주환원, debt=부채, "
                        "signal=키워드트렌드, benchmark=벤치마크, groupHealth=집단건전성"
                    ),
                },
                "code": {
                    "type": "string",
                    "description": "종목코드 (예: 005930). scanAccount/scanRatio에서 쉼표 구분으로 복수 종목 필터링 가능",
                    "default": "",
                },
                "snakeId": {
                    "type": "string",
                    "description": "계정ID (action=scanAccount). 예: sales, operatingIncome, totalAssets, netIncome",
                    "default": "",
                },
                "ratioName": {
                    "type": "string",
                    "description": "비율명 (action=scanRatio). 예: roe, debtRatio, operatingMargin, currentRatio, per, pbr",
                    "default": "",
                },
                "keyword": {
                    "type": "string",
                    "description": "키워드 (action=signal). 예: ESG, AI, 탄소중립",
                    "default": "",
                },
                "days": {
                    "type": "string",
                    "description": "주가이력 기간(일). 기본 365",
                    "default": "365",
                },
                "criteria": {
                    "type": "string",
                    "description": "스크리닝 조건 (action=screen)",
                    "default": "",
                },
                "statement": {
                    "type": "string",
                    "description": "재무제표 종류 (action=financials): BS/IS/CF/CIS",
                    "default": "IS",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("투자", "종합"),
        priority=70,
    )
