"""analysis Super Tool -- 단일기업 심층분석 dispatcher.

dartlab analysis() 14축 전략분석 + insight/valuation/distress 통합.
analyze.py를 대체한다.
"""

from __future__ import annotations

from typing import Any

from ..defaults.helpers import format_tool_value


def registerAnalysisTool(company: Any, registerTool) -> None:
    """analysis Super Tool 등록."""

    # ── 14축 전략분석 (strategy registry 기반) ──

    def _strategy(axis: str, **_kw) -> str:
        """14축 전략분석 실행."""
        try:
            from dartlab.analysis.strategy import analysis

            result = analysis(axis, company)
            return format_tool_value(result, max_rows=40, max_chars=6000)
        except ValueError as e:
            return f"[오류] {e}"
        except (ImportError, AttributeError, KeyError, TypeError, FileNotFoundError, OSError) as e:
            return f"[오류] analysis('{axis}') 실패: {e}"

    # ── 기존 분석 기능 (insight/valuation/distress 등) ──

    def _insight(**_kw) -> str:
        """7영역 인사이트 등급."""
        try:
            from dartlab.analysis.financial.insight.pipeline import analyze as insightAnalyze

            stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
            result = insightAnalyze(stockCode, company=company)
            if result is None:
                return "인사이트 데이터를 생성할 수 없습니다. 대안: finance(action='ratios')로 개별 재무비율을 확인하세요."
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
            return f"[오류] 리서치 리포트 생성 실패: {e}. 대안: analysis(action='insight')로 인사이트 등급을 확인하세요."

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

    # ── 14축 이름 목록 ──

    _STRATEGY_AXES = [
        "수익구조", "자금조달", "자산구조", "현금흐름",
        "수익성", "성장성", "안정성", "효율성", "종합평가",
        "이익품질", "비용구조", "자본배분", "투자효율", "재무정합성",
    ]

    # ── action dispatch ──

    _ACTIONS: dict[str, object] = {}
    # 14축 전략분석
    for axis in _STRATEGY_AXES:
        _ACTIONS[axis] = lambda _a=axis, **_kw: _strategy(_a, **_kw)
    # 기존 분석
    _ACTIONS["insight"] = _insight
    _ACTIONS["sector"] = _sector
    _ACTIONS["rank"] = _rank
    _ACTIONS["valuation"] = _valuation
    _ACTIONS["changes"] = _changes
    _ACTIONS["audit"] = _audit
    _ACTIONS["research"] = _research
    _ACTIONS["distress"] = _distress
    _ACTIONS["watch"] = _watch

    def analysis(action: str) -> str:
        """단일기업 심층분석 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler()

    # action enum
    strategyDesc = ", ".join(f"{a}=전략분석" for a in _STRATEGY_AXES[:3]) + ", ..."
    allActions = _STRATEGY_AXES + [
        "insight", "sector", "rank", "valuation", "changes",
        "audit", "research", "distress", "watch",
    ]

    registerTool(
        "analysis",
        analysis,
        "단일기업 심층분석 -- 14축 전략분석 + 인사이트/밸류에이션/부실예측.\n"
        "\n"
        "## 14축 전략분석 (analysis() 공개 API 1:1 대응)\n"
        "- 수익구조: 이 회사는 무엇으로 돈을 버는가\n"
        "- 자금조달: 돈을 어디서 조달하는가\n"
        "- 자산구조: 조달한 돈으로 뭘 준비했는가\n"
        "- 현금흐름: 실제로 현금은 어떻게 흘렀는가\n"
        "- 수익성: 이 회사는 얼마나 잘 벌고 있는가\n"
        "- 성장성: 이 회사는 얼마나 빨리 성장하는가\n"
        "- 안정성: 이 회사는 망하지 않는가\n"
        "- 효율성: 자산을 효율적으로 쓰는가\n"
        "- 종합평가: 재무 종합 평가\n"
        "- 이익품질: 이익이 진짜인가\n"
        "- 비용구조: 비용이 어떻게 움직이는가\n"
        "- 자본배분: 번 돈을 어디에 쓰는가\n"
        "- 투자효율: 투자가 가치를 만드는가\n"
        "- 재무정합성: 재무제표 간 정합성\n"
        "\n"
        "## 기존 분석 기능\n"
        "- insight: 7영역 인사이트 등급 (수익성, 안정성, 성장성, 효율성, 배당, 밸류에이션, 거버넌스)\n"
        "- sector: WICS 섹터 정보 + 업종 비교\n"
        "- rank: 시가총액 순위\n"
        "- valuation: DCF/상대가치 밸류에이션\n"
        "- changes: 공시 텍스트 변화 감지\n"
        "- audit: 재무 감사 이상치 분석\n"
        "- research: 기관급 종합 리서치 리포트\n"
        "- distress: 부도 예측 4모델 종합\n"
        "- watch: 현재 기업 공시 변화 점수화\n"
        "\n"
        "반환: 마크다운 텍스트. 분석 불가 시 '[데이터 없음]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": allActions,
                    "description": (
                        "14축 전략분석: 수익구조/자금조달/자산구조/현금흐름/수익성/성장성/안정성/효율성/"
                        "종합평가/이익품질/비용구조/자본배분/투자효율/재무정합성. "
                        "기존: insight=등급, sector=섹터, rank=순위, valuation=밸류에이션, "
                        "changes=변화, audit=감사, research=리서치, distress=부도예측, watch=공시변화"
                    ),
                },
            },
            "required": ["action"],
        },
        category="analysis",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "지배구조", "투자", "종합"),
        priority=80,
    )
