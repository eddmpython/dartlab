"""질문 자동 생성기 — CAPABILITIES에서 API를 추출하여 자연어 질문을 생성.

각 도구 × 축 × 종목 조합으로 다양한 질문을 자동 생성.
외부 LLM 없이 템플릿 기반으로 생성하므로 비용 0.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

# 종목 풀 — 다양한 업종 대표 30개
STOCK_POOL = [
    ("005930", "삼성전자", "반도체"),
    ("000660", "SK하이닉스", "반도체"),
    ("005380", "현대차", "자동차"),
    ("035420", "NAVER", "IT"),
    ("005490", "POSCO홀딩스", "철강"),
    ("051910", "LG화학", "화학"),
    ("006400", "삼성SDI", "배터리"),
    ("003550", "LG", "지주"),
    ("105560", "KB금융", "금융"),
    ("055550", "신한지주", "금융"),
    ("028260", "삼성물산", "건설"),
    ("000270", "기아", "자동차"),
    ("068270", "셀트리온", "바이오"),
    ("207940", "삼성바이오로직스", "바이오"),
    ("034730", "SK", "지주"),
    ("096770", "SK이노베이션", "에너지"),
    ("003670", "포스코퓨처엠", "소재"),
    ("012330", "현대모비스", "자동차부품"),
    ("066570", "LG전자", "전자"),
    ("032830", "삼성생명", "보험"),
    ("003490", "대한항공", "항공"),
    ("009150", "삼성전기", "전자부품"),
    ("018260", "삼성에스디에스", "IT서비스"),
    ("033780", "KT&G", "식품"),
    ("030200", "KT", "통신"),
    ("017670", "SK텔레콤", "통신"),
    ("086790", "하나금융지주", "금융"),
    ("316140", "우리금융지주", "금융"),
    ("010130", "고려아연", "비철금속"),
    ("011170", "롯데케미칼", "화학"),
]

# 질문 템플릿 — 도구별로 다양한 표현
_TEMPLATES: dict[str, list[str]] = {
    "analysis_financial": [
        "{corp} {axis} 분석해줘",
        "{corp}의 {axis}이 어때?",
        "{corp} {axis} 추이 보여줘",
        "{corp}의 {axis} 변화 원인이 뭐야?",
        "{corp} {axis}이 개선되고 있어?",
    ],
    "analysis_valuation": [
        "{corp} 적정 주가 알려줘",
        "{corp} 가치평가 해줘",
        "{corp} DCF 분석해줘",
    ],
    "analysis_forecast": [
        "{corp} 매출 전망이 어때?",
        "{corp} 실적이 앞으로 좋아질까?",
        "{corp} 매출 방향 예측해줘",
    ],
    "credit": [
        "{corp} 신용등급 알려줘",
        "{corp} 재무 건전도가 어때?",
        "{corp} 신용 분석해줘",
    ],
    "scan": [
        "{axis}이 좋은 회사 TOP 10 보여줘",
        "시장에서 {axis} 순위 알려줘",
        "{axis} 기준 상위 종목 찾아줘",
    ],
    "macro": [
        "경제 {axis} 어때?",
        "현재 {axis} 상황 분석해줘",
        "{axis} 방향이 어떻게 되나?",
    ],
    "gather": [
        "{corp} 최근 주가 추이 보여줘",
        "{corp} 수급 상황이 어때?",
        "{corp} 관련 뉴스 알려줘",
    ],
    "quant": [
        "{corp} 기술적 분석해줘",
        "{corp} 매매 신호 알려줘",
        "{corp} 기술적 관점에서 어때?",
    ],
    "search": [
        "유상증자 공시 찾아줘",
        "전환사채 발행 공시 검색해줘",
        "대표이사 변경 공시 알려줘",
        "{corp} 최근 공시 중 중요한 거 있어?",
    ],
    "comparison": [
        "{corp1}이랑 {corp2} 수익성 비교해줘",
        "{corp1} vs {corp2} 재무 비교",
        "{corp1}하고 {corp2} 중에 어디가 나아?",
    ],
    "comprehensive": [
        "{corp} 종합 분석해줘",
        "{corp} 어때?",
        "{corp} 투자해도 될까?",
        "{corp} 전반적인 재무 상태 분석해줘",
    ],
}

# analysis financial 축 목록
_FINANCIAL_AXES = [
    "수익구조", "자금조달", "자산구조", "현금흐름", "수익성", "성장성",
    "안정성", "효율성", "종합평가", "이익품질", "비용구조", "자본배분",
    "투자효율", "재무정합성",
]

# scan 축 목록
_SCAN_AXES = [
    "profitability", "growth", "debt", "capital", "governance",
    "cashflow", "quality", "liquidity",
]

# macro 축 목록
_MACRO_AXES = ["사이클", "금리", "자산", "심리", "유동성", "종합"]


def generateQuestions(*, count: int = 2000, seed: int = 42) -> list[dict]:
    """학습용 질문을 자동 생성.

    Args:
        count: 생성할 질문 수
        seed: 랜덤 시드

    Returns:
        [{"question": str, "tool": str, "group": str|None, "axis": str|None,
          "stock_code": str|None, "corp_name": str|None}]
    """
    rng = random.Random(seed)
    questions: list[dict] = []

    def _add(q: str, tool: str, group: str | None = None, axis: str | None = None,
             stock_code: str | None = None, corp_name: str | None = None):
        questions.append({
            "question": q,
            "tool": tool,
            "group": group,
            "axis": axis,
            "stock_code": stock_code,
            "corp_name": corp_name,
        })

    # 1. analysis/financial — 축 × 종목 × 템플릿
    for axis in _FINANCIAL_AXES:
        for code, corp, sector in rng.sample(STOCK_POOL, min(8, len(STOCK_POOL))):
            tmpl = rng.choice(_TEMPLATES["analysis_financial"])
            _add(tmpl.format(corp=corp, axis=axis), "analysis", "financial", axis, code, corp)

    # 2. analysis/valuation, forecast
    for code, corp, sector in rng.sample(STOCK_POOL, 10):
        tmpl = rng.choice(_TEMPLATES["analysis_valuation"])
        _add(tmpl.format(corp=corp), "analysis", "valuation", "가치평가", code, corp)
        tmpl = rng.choice(_TEMPLATES["analysis_forecast"])
        _add(tmpl.format(corp=corp), "analysis", "forecast", "매출전망", code, corp)

    # 3. credit
    for code, corp, sector in rng.sample(STOCK_POOL, 10):
        tmpl = rng.choice(_TEMPLATES["credit"])
        _add(tmpl.format(corp=corp), "credit", None, None, code, corp)

    # 4. scan — 축 × 템플릿
    for axis in _SCAN_AXES:
        for tmpl in _TEMPLATES["scan"]:
            _add(tmpl.format(axis=axis), "scan", None, axis)

    # 5. macro
    for axis in _MACRO_AXES:
        for tmpl in _TEMPLATES["macro"]:
            _add(tmpl.format(axis=axis), "macro", None, axis)

    # 6. gather
    for code, corp, sector in rng.sample(STOCK_POOL, 10):
        for tmpl in _TEMPLATES["gather"]:
            _add(tmpl.format(corp=corp), "gather", None, "price", code, corp)

    # 7. quant
    for code, corp, sector in rng.sample(STOCK_POOL, 8):
        tmpl = rng.choice(_TEMPLATES["quant"])
        _add(tmpl.format(corp=corp), "quant", None, None, code, corp)

    # 8. search
    for tmpl in _TEMPLATES["search"]:
        for code, corp, sector in rng.sample(STOCK_POOL, 3):
            _add(tmpl.format(corp=corp), "search", None, None, code, corp)

    # 9. comparison — 종목 쌍
    pairs = [(STOCK_POOL[i], STOCK_POOL[j])
             for i in range(len(STOCK_POOL))
             for j in range(i+1, len(STOCK_POOL))
             if STOCK_POOL[i][2] == STOCK_POOL[j][2]]  # 같은 업종
    for (c1, n1, _), (c2, n2, _) in rng.sample(pairs, min(15, len(pairs))):
        tmpl = rng.choice(_TEMPLATES["comparison"])
        _add(tmpl.format(corp1=n1, corp2=n2), "analysis", "financial", "비교", c1, n1)

    # 10. comprehensive
    for code, corp, sector in rng.sample(STOCK_POOL, 15):
        tmpl = rng.choice(_TEMPLATES["comprehensive"])
        _add(tmpl.format(corp=corp), "analysis", "financial", "종합", code, corp)

    # 셔플 + 상한
    rng.shuffle(questions)
    return questions[:count]


def saveQuestions(questions: list[dict], path: Path | str) -> int:
    """질문을 JSONL로 저장."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    return len(questions)
