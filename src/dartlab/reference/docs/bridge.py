"""sections 텍스트-재무 숫자 교차 참조.

sections 텍스트에 언급된 금액(매출액 xxx억, 영업이익 xxx억 등)을 추출하고
finance DataFrame 실제 숫자와 자동 매칭한다.
075-003 실험으로 검증 (10사 매칭률 54.2%, 평균 오차 1.89%).

사용법::

    from dartlab.reference.docs.bridge import (
        extract_amounts_from_text, get_finance_amounts, match_amounts,
    )

    amounts = extract_amounts_from_text("매출액 86조 1,229억원")
    fin = get_finance_amounts(company, "2024")
    matched = match_amounts(amounts, fin)
"""

from __future__ import annotations

import re

# 금액 추출 패턴 — 조+억, 단독 조, 단독 억, 백만원, 천원
AMOUNT_PATTERNS = [
    re.compile(r"([\d,]+)\s*조\s*([\d,]*)\s*억"),
    re.compile(r"([\d,]+)\s*조(?:\s*원)?(?![억])"),
    re.compile(r"([\d,]+)\s*억(?:\s*원)?"),
    re.compile(r"([\d,]+)\s*백만\s*원"),
    re.compile(r"([\d,]+)\s*천\s*원"),
]


def _parseNumber(s: str) -> float:
    """쉼표 제거 후 float 변환."""
    if not s:
        return 0
    cleaned = s.replace(",", "").strip()
    if not cleaned:
        return 0
    try:
        return float(cleaned)
    except ValueError:
        return 0


def extractAmountsFromText(text: str) -> list[dict]:
    """텍스트에서 금액 추출 → [{value_억: float, raw: str, unit: str}].

    지원 단위: 조+억, 단독 조, 단독 억, 백만원, 천원.
    위치 기반 중복 제거로 같은 숫자가 여러 패턴에 잡히는 것을 방지한다.
    """
    if not text or not isinstance(text, str):
        return []

    results: list[dict] = []
    # 범위 기반 중복 제거: 이미 매칭된 문자 위치는 재사용하지 않음
    used: set[int] = set()

    def _overlaps(m) -> bool:
        return any(i in used for i in range(m.start(), m.end()))

    def _mark(m) -> None:
        used.update(range(m.start(), m.end()))

    # 조+억 (가장 구체적인 패턴 먼저)
    for m in AMOUNT_PATTERNS[0].finditer(text):
        if _overlaps(m):
            continue
        _mark(m)
        jo = _parseNumber(m.group(1))
        eok = _parseNumber(m.group(2)) if m.group(2) else 0
        results.append({"value_억": jo * 10000 + eok, "raw": m.group(0), "unit": "조억"})

    # 단독 조
    for m in AMOUNT_PATTERNS[1].finditer(text):
        if _overlaps(m):
            continue
        _mark(m)
        results.append({"value_억": _parseNumber(m.group(1)) * 10000, "raw": m.group(0), "unit": "조"})

    # 단독 억
    for m in AMOUNT_PATTERNS[2].finditer(text):
        if _overlaps(m):
            continue
        _mark(m)
        results.append({"value_억": _parseNumber(m.group(1)), "raw": m.group(0), "unit": "억"})

    # 백만원 → 억 (÷100)
    for m in AMOUNT_PATTERNS[3].finditer(text):
        if _overlaps(m):
            continue
        _mark(m)
        results.append({"value_억": _parseNumber(m.group(1)) / 100, "raw": m.group(0), "unit": "백만원"})

    # 천원 → 억 (÷100000)
    for m in AMOUNT_PATTERNS[4].finditer(text):
        if _overlaps(m):
            continue
        _mark(m)
        results.append({"value_억": _parseNumber(m.group(1)) / 100_000, "raw": m.group(0), "unit": "천원"})

    return results


def getFinanceAmounts(company, period: str) -> dict[str, float]:
    """finance에서 주요 계정 → {account: value_억}.

    sections 기간이 '2024'(연간)이면 finance에서 '2024Q4'를 찾고,
    '2024Q3'(분기)이면 그대로 찾는다.

    Raises:
        RuntimeError: 재무제표를 한 장도 읽지 못했거나 대조할 기간이 없을 때.
            빈 dict 를 돌려주면 소비자가 만드는 matchRate 가 0.0 이 되어 "대조 불가"가
            "하나도 안 맞음"이라는 다른 사실 주장으로 바뀌므로 구분해서 올린다.
    """
    result: dict[str, float] = {}

    candidates = [period]
    if re.match(r"^\d{4}$", period):
        candidates.append(f"{period}Q4")

    # 예전에는 `company.finance` 에서 세 장을 꺼냈다. `finance` 는 표면에서 빠진 이름이라
    # 매 회전이 except 로 continue 했고, 이 함수가 어느 회사에서도 빈 dict 만 냈다. 그래서
    # 공시 본문 금액과 재무제표를 대조하는 검증이 통째로 무력했다. 공개 계약으로 부른다.
    loaded = 0
    periodMatched = 0
    failures: list[str] = []
    for stmt_name in ("IS", "BS", "CF"):
        try:
            stmt = company.panel(stmt_name)
        except (AttributeError, FileNotFoundError, KeyError, RuntimeError, TypeError, ValueError) as exc:
            failures.append(f"{stmt_name}: {type(exc).__name__}")
            continue
        if stmt is None or getattr(stmt, "height", 0) == 0:
            failures.append(f"{stmt_name}: 빈 재무제표")
            continue
        loaded += 1

        target_period = None
        for cand in candidates:
            if cand in stmt.columns:
                target_period = cand
                break
        if target_period is None:
            continue
        periodMatched += 1

        for row in stmt.iter_rows(named=True):
            account = row.get("항목") or row.get("account")
            val = row.get(target_period)
            if account and val is not None:
                try:
                    result[account] = float(val) / 100_000_000  # 원 → 억
                except (ValueError, TypeError):
                    pass

    # 재무를 한 장도 못 읽었거나 대조할 기간이 없으면 빈 dict 를 돌려주지 않는다.
    # 소비자(server analysis API)는 이 결과로 matchRate 를 만들기 때문에, 빈 dict 는
    # "공시 금액이 재무제표와 하나도 안 맞는다" 는 경보성 사실 주장(matchRate 0.0)이 된다.
    # 대조 자체가 불가능한 것과 대조해서 안 맞는 것은 다른 답이다.
    if loaded == 0:
        raise RuntimeError(f"재무제표를 읽지 못해 본문 금액을 대조할 수 없습니다 ({'; '.join(failures)})")
    if periodMatched == 0:
        raise RuntimeError(f"재무제표에 기간 {period} 이(가) 없어 본문 금액을 대조할 수 없습니다")

    return result


def matchAmounts(
    textAmounts: list[dict],
    financeAmounts: dict[str, float],
    *,
    tolerance: float = 0.05,
) -> list[dict]:
    """텍스트 금액 ↔ finance 금액 매칭.

    Args:
        text_amounts: extract_amounts_from_text() 결과.
        finance_amounts: get_finance_amounts() 결과.
        tolerance: 허용 오차율 (기본 5%).

    Returns:
        [{text_raw, text_value_억, finance_account, finance_value_억, error_pct}]
    """
    matches: list[dict] = []
    for ta in textAmounts:
        tv = ta.get("value_억", 0)
        if tv == 0:
            continue
        best_match = None
        best_error = float("inf")
        for account, fv in financeAmounts.items():
            if fv == 0:
                continue
            error = abs(tv - fv) / abs(fv)
            if error <= tolerance and error < best_error:
                best_error = error
                best_match = {
                    "text_raw": ta["raw"],
                    "text_value_억": tv,
                    "finance_account": account,
                    "finance_value_억": round(fv, 1),
                    "error_pct": round(error * 100, 2),
                }
        if best_match:
            matches.append(best_match)
    return matches
