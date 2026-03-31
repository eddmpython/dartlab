"""계정명 snakeId → 사람이 읽기 쉬운 라벨 변환.

DART accountMappings.json의 standardAccounts에서 korName을 추출하여
AI 컨텍스트와 도구 반환에서 한글/영문 라벨을 제공한다.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_standard_accounts() -> dict[str, dict]:
    """DART mapperData/standardAccounts → {snakeId: {korName, code, level, sj}}."""
    mapper_path = Path(__file__).resolve().parents[2] / "providers" / "dart" / "finance" / "mapperData" / "accountMappings.json"
    if not mapper_path.exists():
        return {}
    data = json.loads(mapper_path.read_text(encoding="utf-8"))
    return data.get("standardAccounts", {})


# standardAccounts에 없지만 AI 컨텍스트에서 자주 쓰는 snakeId 보충 매핑
_KR_SUPPLEMENTS: dict[str, str] = {
    "pretax_income": "법인세비용차감전순이익",
    "income_tax_expense": "법인세비용",
    "net_income": "당기순이익",
    "net_income_controlling": "지배기업귀속순이익",
    "net_income_cf": "당기순이익",
    "operating_cash_flow": "영업활동현금흐름",
    "investing_cash_flow": "투자활동현금흐름",
    "financing_cash_flow": "재무활동현금흐름",
    "basic_eps": "기본주당이익",
    "diluted_eps": "희석주당이익",
    "dividends_per_share": "주당배당금",
    "interest_expense": "이자비용",
    "free_cash_flow": "잉여현금흐름",
    "short_term_borrowings": "단기차입금",
    "debentures": "사채",
    "net_debt": "순차입금",
    "ebitda": "EBITDA",
    "total_equity": "자본총계",
    "owners_of_parent_equity": "지배기업소유주지분",
    "noncontrolling_interests_equity": "비지배지분",
    "common_stock": "보통주자본금",
    "additional_paid_in_capital": "주식발행초과금",
    "accumulated_other_comprehensive_income": "기타포괄손익누계액",
    "treasury_stock": "자기주식",
}


@lru_cache(maxsize=1)
def get_korean_labels() -> dict[str, str]:
    """snakeId → 한글 라벨. 3,143개 표준계정 + 보충 매핑."""
    sa = _load_standard_accounts()
    labels = {sid: meta["korName"] for sid, meta in sa.items() if meta.get("korName")}
    # 보충 매핑 (standardAccounts에 없는 키만 추가)
    for sid, name in _KR_SUPPLEMENTS.items():
        if sid not in labels:
            labels[sid] = name
    return labels


def _snake_to_title(snake_id: str) -> str:
    """snake_case → Title Case. 영문 fallback."""
    words = snake_id.replace("_", " ").strip()
    return words.title()


# ── EDGAR 영문 readable 라벨 (주요 계정 하드코딩 + fallback) ──

_EDGAR_LABELS: dict[str, str] = {
    "current_assets": "Current Assets",
    "cash_and_cash_equivalents": "Cash & Equivalents",
    "short_term_investments": "Short-term Investments",
    "trade_and_other_receivables": "Receivables",
    "inventories": "Inventories",
    "noncurrent_assets": "Non-current Assets",
    "tangible_assets": "PP&E",
    "intangible_assets": "Intangible Assets",
    "goodwill": "Goodwill",
    "total_assets": "Total Assets",
    "current_liabilities": "Current Liabilities",
    "trade_and_other_payables": "Payables",
    "short_term_borrowings": "Short-term Debt",
    "noncurrent_liabilities": "Non-current Liabilities",
    "longterm_borrowings": "Long-term Debt",
    "debentures": "Bonds Payable",
    "total_liabilities": "Total Liabilities",
    "total_stockholders_equity": "Total Equity",
    "retained_earnings": "Retained Earnings",
    "accumulated_other_comprehensive_income": "Accumulated OCI",
    "treasury_stock": "Treasury Stock",
    "paidin_capital": "Paid-in Capital",
    "capital_surplus": "Capital Surplus",
    "sales": "Revenue",
    "cost_of_sales": "Cost of Revenue",
    "gross_profit": "Gross Profit",
    "selling_and_administrative_expenses": "SG&A",
    "operating_profit": "Operating Income",
    "operating_income": "Operating Income",
    "pretax_income": "Pre-tax Income",
    "income_tax_expense": "Income Tax",
    "net_income": "Net Income",
    "net_income_controlling": "Net Income (Parent)",
    "net_income_cf": "Net Income",
    "basic_eps": "Basic EPS",
    "diluted_eps": "Diluted EPS",
    "dividends_per_share": "DPS",
    "operating_cash_flow": "Operating CF",
    "investing_cash_flow": "Investing CF",
    "financing_cash_flow": "Financing CF",
    "depreciation": "Depreciation",
    "capex": "CAPEX",
    "free_cash_flow": "Free Cash Flow",
    "interest_expense": "Interest Expense",
    "research_and_development": "R&D",
    "common_stock": "Common Stock",
    "additional_paid_in_capital": "Additional Paid-in Capital",
    "owners_of_parent_equity": "Parent Equity",
    "noncontrolling_interests_equity": "NCI",
    "total_equity": "Total Equity",
    "restricted_cash_current": "Restricted Cash",
    "deferred_revenue_current": "Deferred Revenue",
}


@lru_cache(maxsize=1)
def get_english_labels() -> dict[str, str]:
    """snakeId → 영문 readable 라벨. 하드코딩 + snake_to_title fallback."""
    return dict(_EDGAR_LABELS)


def get_account_labels(locale: str = "kr") -> dict[str, str]:
    """snakeId → 사람이 읽기 쉬운 라벨.

    Args:
        locale: "kr"이면 한글, "en"이면 영문.

    Returns:
        {snakeId: label} dict.
    """
    if locale == "kr":
        return get_korean_labels()
    return get_english_labels()


@lru_cache(maxsize=1)
def get_reverse_korean_labels() -> dict[str, str]:
    """한글 라벨 → snakeId 역조회. get_korean_labels()의 역방향.

    동일 한글 라벨이 여러 snakeId에 매핑될 경우 첫 번째를 유지한다.
    정규화된(소문자+공백제거) 키도 함께 등록하여 cascade 매칭에서 활용한다.
    """
    import re
    import unicodedata

    forward = get_korean_labels()
    reverse: dict[str, str] = {}
    for sid, kr in forward.items():
        if kr not in reverse:
            reverse[kr] = sid
        # 정규화 키 (show.py normalizeItemKey와 동일 로직)
        nk = unicodedata.normalize("NFKC", kr)
        nk = re.sub(r"\s+", "", nk).lower()
        if nk not in reverse:
            reverse[nk] = sid
    return reverse


def resolve_label(snake_id: str, market: str = "KR") -> str:
    """단일 snakeId를 라벨로 변환. 매칭 실패 시 snake_to_title fallback."""
    labels = get_account_labels("kr" if market == "KR" else "en")
    label = labels.get(snake_id)
    if label:
        return label
    if market != "KR":
        return _snake_to_title(snake_id)
    return snake_id
