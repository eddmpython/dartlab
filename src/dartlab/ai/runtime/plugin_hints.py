"""플러그인 추천 시스템 — 사용자 질문에서 유용한 플러그인을 감지.

사용자의 분석 패턴을 보고 아직 설치되지 않은 유용한 플러그인을 추천한다.
LLM context에 힌트를 주입하여 자연스러운 안내가 가능하다.
"""

from __future__ import annotations

# 질문 키워드 → 추천 플러그인 매핑
# 커뮤니티 성장에 따라 동적 목록으로 확장 가능
_PLUGIN_HINTS: dict[str, dict[str, str]] = {
    "ESG": {
        "name": "dartlab-plugin-esg",
        "topic": "esgScore",
        "description": "ESG 등급 및 환경/사회/지배구조 점수 분석",
        "install": "uv pip install dartlab-plugin-esg",
    },
    "백테스트": {
        "name": "dartlab-plugin-backtest",
        "topic": "backtest",
        "description": "투자 전략 백테스트 및 성과 분석",
        "install": "uv pip install dartlab-plugin-backtest",
    },
    "기술적분석": {
        "name": "dartlab-plugin-technical",
        "topic": "technicalIndicators",
        "description": "이동평균, RSI, MACD 등 기술적 지표",
        "install": "uv pip install dartlab-plugin-technical",
    },
    "뉴스": {
        "name": "dartlab-plugin-news",
        "topic": "newsSentiment",
        "description": "실시간 뉴스 수집 및 감성 분석",
        "install": "uv pip install dartlab-plugin-news",
    },
    "주가": {
        "name": "dartlab-plugin-price",
        "topic": "priceHistory",
        "description": "주가 시계열, 수익률, 변동성 분석",
        "install": "uv pip install dartlab-plugin-price",
    },
    "밸류에이션": {
        "name": "dartlab-plugin-valuation",
        "topic": "dcfValuation",
        "description": "DCF, 상대가치 등 본격 밸류에이션 모델",
        "install": "uv pip install dartlab-plugin-valuation",
    },
    "공급망": {
        "name": "dartlab-plugin-supplychain",
        "topic": "supplyChain",
        "description": "공급망 분석 및 거래 관계 맵",
        "install": "uv pip install dartlab-plugin-supplychain",
    },
    "peer": {
        "name": "dartlab-plugin-peer",
        "topic": "peerComparison",
        "description": "동종업계 비교 분석 (peer group)",
        "install": "uv pip install dartlab-plugin-peer",
    },
    "AI분석": {
        "name": "dartlab-plugin-ai-analyst",
        "topic": "aiReport",
        "description": "AI 기반 종합 리서치 리포트 자동 생성",
        "install": "uv pip install dartlab-plugin-ai-analyst",
    },
}

# 키워드 별칭 (다양한 표현 매칭)
_KEYWORD_ALIASES: dict[str, str] = {
    "이에스지": "ESG",
    "탄소": "ESG",
    "환경": "ESG",
    "사회적": "ESG",
    "지속가능": "ESG",
    "backtest": "백테스트",
    "전략검증": "백테스트",
    "시뮬레이션": "백테스트",
    "기술적": "기술적분석",
    "차트": "기술적분석",
    "RSI": "기술적분석",
    "MACD": "기술적분석",
    "이동평균": "기술적분석",
    "볼린저": "기술적분석",
    "news": "뉴스",
    "감성분석": "뉴스",
    "여론": "뉴스",
    "주가": "주가",
    "수익률": "주가",
    "변동성": "주가",
    "price": "주가",
    "DCF": "밸류에이션",
    "적정주가": "밸류에이션",
    "목표주가": "밸류에이션",
    "내재가치": "밸류에이션",
    "supply": "공급망",
    "공급": "공급망",
    "동종": "peer",
    "비교분석": "peer",
    "업종비교": "peer",
    "peer": "peer",
    "리포트": "AI분석",
    "리서치": "AI분석",
}


def detect_plugin_hints(
    question: str,
    loaded_plugin_names: list[str] | None = None,
) -> list[dict[str, str]]:
    """질문에서 유용한 미설치 플러그인을 감지.

    Args:
        question: 사용자 질문 텍스트.
        loaded_plugin_names: 이미 설치된 플러그인 이름 목록.

    Returns:
        추천 플러그인 정보 리스트 (최대 2개).
    """
    if not question:
        return []

    loaded = set(loaded_plugin_names or [])
    q_lower = question.lower()
    matched: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    # 직접 매칭
    for key, hint in _PLUGIN_HINTS.items():
        if key.lower() in q_lower and hint["name"] not in loaded and key not in seen_keys:
            matched.append(hint)
            seen_keys.add(key)

    # 별칭 매칭
    for alias, key in _KEYWORD_ALIASES.items():
        if alias.lower() in q_lower and key not in seen_keys:
            hint = _PLUGIN_HINTS.get(key)
            if hint and hint["name"] not in loaded:
                matched.append(hint)
                seen_keys.add(key)

    # 최대 2개만 반환 (스팸 방지)
    return matched[:2]


def format_plugin_hints(hints: list[dict[str, str]]) -> str | None:
    """추천 힌트를 LLM context용 텍스트로 포맷."""
    if not hints:
        return None

    lines = ["💡 **유용한 플러그인 추천:**"]
    for h in hints:
        lines.append(f"- **{h['name']}**: {h['description']}")
        lines.append(f"  설치: `{h['install']}`")

    lines.append("")
    lines.append('플러그인 만들기: `dartlab.ask("... 플러그인 만들어줘")`로 AI가 자동 생성합니다.')
    return "\n".join(lines)
