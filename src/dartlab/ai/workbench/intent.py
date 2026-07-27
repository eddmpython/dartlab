"""정규식·키워드 SSOT — 종목코드 / 티커 / show 주제 인식 helper.

P-revised: `isAnalysisIntent` 함수 폐기. 작업대 elevate 는 사용자 명시 mode 또는
모델 자율 `RunWorkbench` 도구 호출 두 경로만. 본 모듈은 회사 분리 / 종목코드
정규식 + show 토픽 alias 제공만 — targets.py / heuristic.py 가 import.
"""

from __future__ import annotations

import re

from dartlab.core.market import KR_STOCK_CODE_TEXT_RE

# 정규식. 질문에서 종목코드 / 티커 / 회사 분리 / show 주제 인식.
_COMPANY_SPLIT_RE = re.compile(r"\s*(?:,|/|vs\.?|VS\.?|랑|하고|와|과)\s*")
# KRX 단축코드 정본 패턴 (영숫자 코드 0008Z0 포함, 기간 "2026Q1" 오탐 배제).
_STOCK_CODE_RE = KR_STOCK_CODE_TEXT_RE
_TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")

_SHOW_TOPIC_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("BS", ("BS", "balance sheet", "재무상태표", "재무제표", "자산", "부채", "자본")),
    ("IS", ("IS", "income statement", "손익계산서", "손익", "이익", "매출")),
    ("CF", ("CF", "cash flow", "현금흐름표", "현금흐름", "FCF", "free cash flow")),
)

_ACTION_WORDS = (
    "확인",
    "비교",
    "분석",
    "설명",
    "계산",
    "알려줘",
    "해줘",
    "봐줘",
    "찾아줘",
    "재무제표",
    "재무상태표",
    "손익계산서",
    "현금흐름표",
    "자산",
    "부채",
    "자본",
)
