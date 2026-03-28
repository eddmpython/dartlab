"""analyze Super Tool — 심층 분석 통합 dispatcher.

통합 대상: get_insight, run_audit, get_sector_info, get_rank,
get_disclosure_changes, run_valuation, run_forecast, run_stress_test
"""

from __future__ import annotations

from typing import Any

from ..defaults.helpers import format_tool_value


def registerAnalyzeTool(company: Any, registerTool) -> None:
    """analyze Super Tool 등록."""

    def _insight(**_kw) -> str:
        """7영역 인사이트 등급."""
        try:
            from dartlab.analysis.financial.insight.pipeline import analyze as insightAnalyze

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = insightAnalyze(stockCode, company=company)
            if result is None:
                return (
                    "인사이트 데이터를 생성할 수 없습니다. 대안: finance(action='ratios')로 개별 재무비율을 확인하세요."
                )
            return format_tool_value(result, max_rows=30, max_chars=5000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 인사이트 분석 실패: {e}. 대안: finance(action='ratios')로 재무비율을 직접 조회하세요."

    def _sector(**_kw) -> str:
        """WICS 섹터 정보."""
        try:
            from dartlab.analysis.comparative.sector import classify

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = classify(stockCode)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 섹터 정보 조회 실패: {e}"

    def _rank(**_kw) -> str:
        """시가총액 순위."""
        try:
            from dartlab.scan.rank import getRank

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = getRank(stockCode)
            return format_tool_value(result, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 순위 조회 실패: {e}"

    def _valuation(**_kw) -> str:
        """밸류에이션 분석."""
        try:
            from dartlab.analysis.valuation.analyst import fullValuation

            result = fullValuation(company)
            return format_tool_value(result, max_rows=20, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 밸류에이션 실패: {e}. 대안: finance(action='ratios')로 PER/PBR을 직접 확인하세요."

    def _changes(**_kw) -> str:
        """공시 변화 감지."""
        try:
            from dartlab.analysis.watch import scan_company

            result = scan_company(company)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 변화 감지 실패: {e}. 대안: explore(action='diff')로 공시 텍스트 변화를 직접 확인하세요."

    def _audit(**_kw) -> str:
        """재무 감사 분석."""
        try:
            from dartlab.analysis.financial.insight.pipeline import analyzeAudit

            result = analyzeAudit(company)
            if not result:
                return "감사 이상치가 발견되지 않았습니다."
            lines = []
            for a in result[:10]:
                lines.append(f"- [{a.severity}] {a.column} {a.year}: {a.description}")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 감사 분석 실패: {e}. 대안: finance(action='anomalies', module='IS')로 이상치를 탐지하세요."

    def _research(**_kw) -> str:
        """기관급 리서치 리포트 생성."""
        try:
            from dartlab.analysis.financial.research.orchestrator import generateResearch

            result = generateResearch(company)
            return format_tool_value(result, max_rows=50, max_chars=8000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 리서치 리포트 생성 실패: {e}. 대안: analyze(action='insight')로 인사이트 등급을 확인하세요."

    def _distress(**_kw) -> str:
        """부도 예측 모델 4종 종합 스코어카드."""
        try:
            from dartlab.ai.context.company_adapter import get_headline_ratios
            from dartlab.analysis.financial.insight.distress import calcDistress
            from dartlab.analysis.financial.insight.pipeline import analyzeAudit

            ratios = get_headline_ratios(company)
            if ratios is None:
                return "[데이터 없음] 재무비율 계산 불가."
            anomalies = analyzeAudit(company) or []
            result = calcDistress(ratios._inner, anomalies)
            return format_tool_value(result, max_rows=30, max_chars=5000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 부실 예측 실패: {e}. 대안: finance(action='ratios')에서 Altman Z-Score를 확인하세요."

    # ── 추가 분석 액션 ──

    def _watch(**_kw) -> str:
        """현재 기업 공시 변화 감지 (scored 변화 목록)."""
        try:
            from dartlab.scan.watch import scan_company

            result = scan_company(company)
            if result is None:
                return "[데이터 없음] 공시 변화를 감지할 수 없습니다 (sections 데이터 부족)."
            lines = [f"## {getattr(company, 'corpName', '?')} 공시 변화 감지"]
            if hasattr(result, "scored") and result.scored:
                for s in result.scored[:15]:
                    score = getattr(s, "score", "?")
                    topic = getattr(s, "topic", "?")
                    reason = getattr(s, "reason", "")
                    lines.append(f"- [{score:.0f}점] {topic}: {reason}")
            else:
                lines.append("변화가 감지되지 않았습니다.")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 공시 변화 감지 실패: {e}. 대안: explore(action='diff')로 직접 확인하세요."

    def _digest(**_kw) -> str:
        """전종목 공시 변화 다이제스트 (상위 변화 종목)."""
        try:
            from dartlab.scan.watch.scanner import scan_market

            df = scan_market(top_n=20, min_score=10.0, verbose=False)
            if df is None or len(df) == 0:
                return "[데이터 없음] 전종목 공시 변화 데이터 없음."
            from ..defaults.helpers import df_to_md

            return "## 전종목 공시 변화 다이제스트 (상위 20)\n" + df_to_md(df, max_rows=20, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, FileNotFoundError, OSError) as e:
            return f"[오류] 다이제스트 생성 실패: {e}"

    _ACTIONS = {
        "insight": _insight,
        "sector": _sector,
        "rank": _rank,
        "valuation": _valuation,
        "changes": _changes,
        "audit": _audit,
        "research": _research,
        "distress": _distress,
        # 추가 액션
        "watch": _watch,
        "digest": _digest,
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
        "기업 심층 분석 — 인사이트 등급, 섹터, 밸류에이션, 변화감지 등.\n"
        "\n"
        "## 단일 기업 분석 (company 필요)\n"
        "- insight: 7영역 인사이트 등급 (수익성, 안정성, 성장성, 효율성, 배당, 밸류에이션, 거버넌스)\n"
        "- sector: WICS 섹터 정보 + 업종 비교\n"
        "- rank: 시가총액 순위\n"
        "- valuation: DCF/상대가치 밸류에이션\n"
        "- changes: 공시 텍스트 변화 감지\n"
        "- audit: 재무 감사 이상치 분석\n"
        "- research: 기관급 종합 리서치 리포트\n"
        "- distress: 부도 예측 4모델 종합\n"
        "- watch: 현재 기업 공시 변화 점수화 (scored changes)\n"
        "\n"
        "## 전종목 분석\n"
        "- digest: 전종목 공시 변화 다이제스트 (상위 변화 종목)\n"
        "\n"
        "반환: 마크다운 텍스트. 분석 불가 시 '[데이터 없음]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "insight",
                        "sector",
                        "rank",
                        "valuation",
                        "changes",
                        "audit",
                        "research",
                        "distress",
                        "watch",
                        "digest",
                    ],
                    "description": (
                        "insight=등급, sector=섹터, rank=순위, valuation=밸류에이션, "
                        "changes=변화, audit=감사, research=리서치, distress=부도예측, "
                        "watch=공시변화점수, digest=전종목변화"
                    ),
                },
            },
            "required": ["action"],
        },
        category="analysis",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "지배구조", "투자", "종합"),
        priority=80,
    )
