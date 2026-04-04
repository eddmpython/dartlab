"""도구 라우터 엔진 — 질문 → 도구 선택 + 코드 생성.

3가지 모드:
1. rule: 규칙 기반 (즉시, 모델 불필요)
2. local: 로컬 소형 모델 (Phase 3)
3. hybrid: rule 우선 → 신뢰도 낮으면 local fallback
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """라우팅 결과."""

    tool: str  # analysis, scan, macro, ...
    group: str | None = None  # financial, valuation, ...
    axis: str | None = None  # 수익성, profitability, ...
    code: str = ""  # 실행할 코드
    needs_company: bool = True
    confidence: float = 0.0  # 0.0~1.0
    source: str = "rule"  # rule, local, hybrid

    def to_few_shot(self) -> str:
        """LLM에 주입할 few-shot 블록으로 변환."""
        if not self.code:
            return ""
        return (
            f"\n## 라우터 추천 코드 (자동 선택)\n"
            f"도구: {self.tool}"
            + (f"/{self.group}/{self.axis}" if self.group else "")
            + f" (신뢰도 {self.confidence:.0%})\n"
            f"```python\n{self.code}\n```\n"
            f"위 코드를 기반으로 실행하되, 필요하면 수정하라.\n"
        )


# ── 규칙 기반 라우터 ────────────────────────────────────────

# (패턴, 도구, 그룹, 축, needs_company, 신뢰도)
_RULES: list[tuple[re.Pattern, str, str | None, str | None, bool, float]] = [
    # scan — analysis보다 먼저 매칭 (시장 비교 키워드가 우선)
    (re.compile(r"TOP\s*\d|순위|랭킹|시장.*비교|전종목|좋은.*회사|찾아줘.*회사", re.I), "scan", None, "profitability", False, 0.90),
    (re.compile(r"배당.*많|배당.*높|배당.*순위|배당.*찾", re.I), "scan", None, "capital", False, 0.90),
    (re.compile(r"부채.*위험|부채.*높|debt.*risk|위험.*회사", re.I), "scan", None, "debt", False, 0.90),
    (re.compile(r"지배구조.*좋|governance.*좋", re.I), "scan", None, "governance", False, 0.90),
    # analysis 축 직접 매칭 (높은 신뢰도)
    (re.compile(r"수익성|마진|이익률|영업이익|ROE|ROA", re.I), "analysis", "financial", "수익성", True, 0.95),
    (re.compile(r"성장성|성장률|매출.*증가|CAGR", re.I), "analysis", "financial", "성장성", True, 0.95),
    (re.compile(r"안정성|부채|이자보상|ICR|레버리지|건전", re.I), "analysis", "financial", "안정성", True, 0.95),
    (re.compile(r"현금.*흐름|FCF|OCF|현금전환", re.I), "analysis", "financial", "현금흐름", True, 0.95),
    (re.compile(r"비용.*구조|원가율|판관비|SGA", re.I), "analysis", "financial", "비용구조", True, 0.95),
    (re.compile(r"이익.*품질|발생액|accrual", re.I), "analysis", "financial", "이익품질", True, 0.95),
    (re.compile(r"자본.*배분|배당.*정책|자사주|shareholder", re.I), "analysis", "financial", "자본배분", True, 0.95),
    (re.compile(r"투자.*효율|ROIC|WACC", re.I), "analysis", "financial", "투자효율", True, 0.95),
    (re.compile(r"자산.*구조|유형자산|무형자산", re.I), "analysis", "financial", "자산구조", True, 0.90),
    (re.compile(r"자금.*조달|차입|funding", re.I), "analysis", "financial", "자금조달", True, 0.90),
    (re.compile(r"수익.*구조|매출.*구성|세그먼트", re.I), "analysis", "financial", "수익구조", True, 0.90),
    (re.compile(r"효율성|자산회전|CCC", re.I), "analysis", "financial", "효율성", True, 0.90),
    (re.compile(r"재무.*정합|일관성|consistency", re.I), "analysis", "financial", "재무정합성", True, 0.90),
    (re.compile(r"종합.*평가|재무.*건강|scorecard", re.I), "analysis", "financial", "종합평가", True, 0.90),
    # valuation / forecast
    (re.compile(r"적정.*주가|가치.*평가|DCF|DDM|valuation", re.I), "analysis", "valuation", "가치평가", True, 0.90),
    (re.compile(r"매출.*전망|예측|forecast|방향", re.I), "analysis", "forecast", "매출전망", True, 0.90),
    # credit
    (re.compile(r"신용|등급|credit|dCR|건전도", re.I), "credit", None, None, True, 0.95),
    # (scan은 위에서 analysis보다 먼저 매칭됨)
    (re.compile(r"지배구조|governance", re.I), "scan", None, "governance", False, 0.90),
    # macro
    (re.compile(r"경제.*사이클|사이클|cycle", re.I), "macro", None, "사이클", False, 0.95),
    (re.compile(r"금리.*방향|금리.*전망|interest.*rate", re.I), "macro", None, "금리", False, 0.95),
    (re.compile(r"시장.*심리|VIX|공포|탐욕", re.I), "macro", None, "심리", False, 0.90),
    (re.compile(r"유동성|liquidity|M2", re.I), "macro", None, "유동성", False, 0.90),
    # gather
    (re.compile(r"주가.*추이|차트|stock.*price", re.I), "gather", None, "price", True, 0.90),
    (re.compile(r"수급|외국인|기관|매매", re.I), "gather", None, "flow", True, 0.90),
    # quant
    (re.compile(r"기술적.*분석|매매.*신호|RSI|MACD|볼린저", re.I), "quant", None, None, True, 0.90),
    # search
    (re.compile(r"공시.*검색|유상증자|전환사채|대표이사.*변경", re.I), "search", None, None, False, 0.90),
    # news
    (re.compile(r"뉴스|이슈|소식|동향|최근.*시장", re.I), "news", None, None, False, 0.85),
    # show/select
    (re.compile(r"재무제표|BS|IS|CF|재고자산|주석|notes", re.I), "show", None, None, True, 0.80),
    # 종합 분석 (마지막 — 다른 규칙에 안 걸리면)
    (re.compile(r"분석.*해|어때|괜찮|종합|전반", re.I), "analysis", "financial", "종합", True, 0.75),
    # 비교
    (re.compile(r"(랑|와|과|하고|vs).*비교", re.I), "analysis", "financial", "비교", True, 0.70),
]


def _code_for_route(r: RouteResult, stock_code: str | None = None) -> str:
    """라우팅 결과에 맞는 코드 템플릿 생성."""
    sc = stock_code or "{stockCode}"

    if r.tool == "analysis" and r.axis == "종합":
        return (
            f'c = dartlab.Company("{sc}")\n'
            f'prof = c.analysis("financial", "수익성")\n'
            f'growth = c.analysis("financial", "성장성")\n'
            f'stab = c.analysis("financial", "안정성")\n'
            f'print(prof["marginTrend"]["history"][:3])\n'
            f'print(growth.keys())\n'
            f'print(stab.keys())'
        )

    if r.tool == "analysis":
        group = r.group or "financial"
        axis = r.axis or "수익성"
        return (
            f'c = dartlab.Company("{sc}")\n'
            f'r = c.analysis("{group}", "{axis}")\n'
            f"print(r.keys())"
        )

    if r.tool == "credit":
        return f'c = dartlab.Company("{sc}")\ncr = c.credit(detail=True)\nprint(f"등급: {{cr[\'grade\']}}, 건전도: {{cr[\'healthScore\']}}/100")'

    if r.tool == "scan":
        axis = r.axis or "profitability"
        return f'df = dartlab.scan("{axis}")\nprint(df.columns)\nprint(df.head(10))'

    if r.tool == "macro":
        axis = r.axis or "종합"
        return f'r = dartlab.macro("{axis}")\nprint(r.keys())\nfor k, v in r.items():\n    print(f"{{k}}: {{v}}")'

    if r.tool == "gather":
        axis = r.axis or "price"
        return f'c = dartlab.Company("{sc}")\ndata = c.gather("{axis}")\nif data is not None:\n    print(data.tail(20))\nelse:\n    print("데이터 없음")'

    if r.tool == "quant":
        return f'c = dartlab.Company("{sc}")\nresult = c.quant()\nprint(result)'

    if r.tool == "search":
        return 'results = dartlab.search("키워드")\nprint(f"검색 결과: {len(results)}건")\nprint(results.head(10))'

    if r.tool == "news":
        return 'results = newsSearch("키워드", days=7)\nprint(formatResults(results))'

    if r.tool == "show":
        return f'c = dartlab.Company("{sc}")\nprint(c.show("IS"))'

    return ""


def _rule_route(question: str) -> RouteResult | None:
    """규칙 기반 라우팅."""
    for pattern, tool, group, axis, needs_company, confidence in _RULES:
        if pattern.search(question):
            return RouteResult(
                tool=tool,
                group=group,
                axis=axis,
                needs_company=needs_company,
                confidence=confidence,
                source="rule",
            )
    return None


def route(
    question: str,
    *,
    stock_code: str | None = None,
    mode: str = "hybrid",
) -> RouteResult | None:
    """질문을 라우팅하여 최적의 도구와 코드를 반환.

    Args:
        question: 사용자 질문
        stock_code: 종목코드 (있으면)
        mode: "rule" | "local" | "hybrid"

    Returns:
        RouteResult 또는 None (라우팅 불가)
    """
    # 1. 규칙 기반 시도
    result = _rule_route(question)

    if result and result.confidence >= 0.85:
        result.code = _code_for_route(result, stock_code)
        return result

    # 2. 로컬 모델 (Phase 3 — ExLlamaV2)
    if mode in ("local", "hybrid"):
        local_result = _local_route(question, stock_code)
        if local_result:
            # hybrid: 규칙과 로컬 비교하여 더 높은 신뢰도 선택
            if result and result.confidence > local_result.confidence:
                result.code = _code_for_route(result, stock_code)
                return result
            return local_result

    # 3. 규칙 결과라도 반환 (낮은 신뢰도)
    if result:
        result.code = _code_for_route(result, stock_code)
        return result

    return None


def _local_route(question: str, stock_code: str | None = None) -> RouteResult | None:
    """로컬 소형 모델로 라우팅 (Phase 3에서 활성화).

    ExLlamaV2 + Qwen3 1.7B로 추론.
    모델이 없으면 None 반환 (rule fallback).
    """
    try:
        from dartlab.ai.selfai.router.model import infer_route

        return infer_route(question, stock_code)
    except ImportError:
        log.debug("로컬 라우터 모델 없음 — rule 모드 사용")
        return None
    except (OSError, RuntimeError) as e:
        log.warning("로컬 라우터 추론 실패: %s", e)
        return None
