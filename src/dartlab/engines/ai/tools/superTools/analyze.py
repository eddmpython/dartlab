"""analyze Super Tool — 심층 분석 통합 dispatcher.

통합 대상: get_insight, run_audit, get_sector_info, get_rank, get_esg,
get_supply_chain, get_disclosure_changes, run_valuation, run_forecast,
run_stress_test
"""

from __future__ import annotations

from typing import Any

from ..defaults.helpers import format_tool_value


def registerAnalyzeTool(company: Any, registerTool) -> None:
    """analyze Super Tool 등록."""

    def _insight(**_kw) -> str:
        """7영역 인사이트 등급."""
        try:
            from dartlab.engines.analysis.insight.pipeline import analyze as insightAnalyze

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = insightAnalyze(stockCode, company=company)
            if result is None:
                return (
                    "인사이트 데이터를 생성할 수 없습니다. 대안: finance(action='ratios')로 개별 재무비율을 확인하세요."
                )
            return format_tool_value(result, max_rows=30, max_chars=5000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"인사이트 분석 실패: {e}. 대안: finance(action='ratios')로 재무비율을 직접 조회하세요."

    def _sector(**_kw) -> str:
        """WICS 섹터 정보."""
        try:
            from dartlab.engines.analysis.sector import classify

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = classify(stockCode)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"섹터 정보 조회 실패: {e}"

    def _rank(**_kw) -> str:
        """시가총액 순위."""
        try:
            from dartlab.engines.analysis.rank import getRank

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = getRank(stockCode)
            return format_tool_value(result, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"순위 조회 실패: {e}"

    def _esg(**_kw) -> str:
        """ESG 공시 분석."""
        try:
            from dartlab.engines.analysis.esg import analyze_esg

            result = analyze_esg(company)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"ESG 분석 실패: {e}. 대안: explore(action='search', keyword='ESG')로 공시 원문을 검색하세요."

    def _valuation(**_kw) -> str:
        """밸류에이션 분석."""
        try:
            from dartlab.engines.analysis.analyst import fullValuation

            result = fullValuation(company)
            return format_tool_value(result, max_rows=20, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"밸류에이션 실패: {e}. 대안: finance(action='ratios')로 PER/PBR을 직접 확인하세요."

    def _changes(**_kw) -> str:
        """공시 변화 감지."""
        try:
            from dartlab.engines.analysis.watch import scan_company

            result = scan_company(company)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"변화 감지 실패: {e}. 대안: explore(action='diff')로 공시 텍스트 변화를 직접 확인하세요."

    def _audit(**_kw) -> str:
        """재무 감사 분석."""
        try:
            from dartlab.engines.analysis.insight.pipeline import analyzeAudit

            result = analyzeAudit(company)
            if not result:
                return "감사 이상치가 발견되지 않았습니다."
            lines = []
            for a in result[:10]:
                lines.append(f"- [{a.severity}] {a.column} {a.year}: {a.description}")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"감사 분석 실패: {e}. 대안: finance(action='anomalies', module='IS')로 이상치를 탐지하세요."

    _ACTIONS = {
        "insight": _insight,
        "sector": _sector,
        "rank": _rank,
        "esg": _esg,
        "valuation": _valuation,
        "changes": _changes,
        "audit": _audit,
    }

    def analyze(action: str) -> str:
        """심층 분석 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler()

    registerTool(
        "analyze",
        analyze,
        "기업 심층 분석 — 인사이트 등급, 섹터, 밸류에이션, ESG 등 파생 분석 결과 조회.\n"
        "\n"
        "✓ 이 도구를 쓰는 경우: '투자등급이 뭐야?', '적정주가?', 'ESG?', '업종 대비 위치?' 등 종합 판단 질문\n"
        "✗ 이 도구를 쓰지 않는 경우: 원본 재무 숫자 → finance, 공시 원문 → explore 사용\n"
        "\n"
        "action별 동작:\n"
        "- insight: 7영역 인사이트 등급 (수익성, 안정성, 성장성, 효율성, 배당, 밸류에이션, 거버넌스)\n"
        "- sector: WICS 섹터 정보 + 업종 비교\n"
        "- rank: 시가총액 순위\n"
        "- esg: ESG 공시 분석\n"
        "- valuation: DCF/상대가치 밸류에이션. 예: analyze(action='valuation')\n"
        "- changes: 공시 텍스트 변화 감지\n"
        "- audit: 재무 감사 이상치 분석",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["insight", "sector", "rank", "esg", "valuation", "changes", "audit"],
                    "description": "insight=인사이트등급, sector=섹터정보, rank=순위, esg=ESG, valuation=밸류에이션, changes=변화감지, audit=감사분석",
                },
            },
            "required": ["action"],
        },
        category="analysis",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "지배구조", "투자", "종합"),
        priority=80,
    )
