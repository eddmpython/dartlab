"""기업 유형 판별 — 스토리 템플릿 자동 감지 (L0).

story/analysis 양쪽에서 사용하는 기업 분류 로직.
Phase 9 A1: story/templates.py 에서 L0 으로 이동.
"""

from __future__ import annotations


def _extractCommon(company):
    """공통 데이터 추출 (체크 함수 공용)."""
    try:
        ratios = company._finance.ratios
    except (AttributeError, ValueError):
        return None

    def _g(name, default=None):
        return getattr(ratios, name, default)

    try:
        rs = company._finance.ratioSeries
        if rs:
            data, _ = rs
            opMargins = data.get("RATIO", {}).get("operatingMargin", [])
        else:
            opMargins = []
    except (AttributeError, ValueError):
        opMargins = []

    return {
        "ratios": ratios,
        "opMargin": _g("operatingMargin"),
        "netDebt": _g("netDebt"),
        "cash": _g("cash"),
        "totalAssets": _g("totalAssets"),
        "ppe": _g("ppe") or _g("tangibleAssets"),
        "opMargins": opMargins,
    }


def _cv(values: list, minCount: int = 4) -> float | None:
    valid = [m for m in values if m is not None]
    if len(valid) < minCount:
        return None
    avg = sum(valid) / len(valid)
    if avg == 0:
        return None
    std = (sum((m - avg) ** 2 for m in valid) / len(valid)) ** 0.5
    return std / abs(avg)


def _checkTurnaround(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    opMargins = ctx["opMargins"]
    if len(opMargins) < 3:
        return False
    recent3 = opMargins[-3:]
    hasNeg = any(m is not None and m < 0 for m in recent3[:-1])
    lastPos = recent3[-1] is not None and recent3[-1] > 0
    return hasNeg and lastPos


_HOLDING_NAME_WORDS = ("홀딩스", "지주", "Holdings")


def _listedAsHolding(company) -> bool:
    """국내 상장 목록에서 지주회사로 올라 있는지 본다.

    지주회사는 KIND 상장법인 목록의 주요제품 줄에 지주를 적는다
    (LG "지주회사", SK "지주회사, 시스템통합(SI)…", GS "지주회사/부동산 임대",
    노루홀딩스 "지주사업", 신한지주 "금융지주회사", 2026-11 목록 59개사).
    회사명에 홀딩스·지주가 든 회사도 지주회사로 본다(core.sector 의 지주사 낱말과 같다).
    재무 기준만으로는 연결재무제표에 자회사 손익이 영업이익으로 합쳐진 지주회사를 놓친다
    (LG 2025: 지분법이익 1,339억이 영업이익 9,122억의 15%). 해외 회사는 이 목록에 없다.
    """
    code = getattr(company, "stockCode", None)
    if not (isinstance(code, str) and len(code) == 6):
        return False
    name = getattr(company, "corpName", None) or ""
    if any(w in name for w in _HOLDING_NAME_WORDS):
        return True
    import polars as pl

    from dartlab.gather.krx.listing.registry import getKindList

    try:
        kind = getKindList()
    except OSError:
        return False
    if kind.is_empty() or "주요제품" not in kind.columns or "종목코드" not in kind.columns:
        return False
    row = kind.filter(pl.col("종목코드") == code)
    products = row["주요제품"][0] if row.height else None
    return isinstance(products, str) and "지주" in products


def _checkHolding(company) -> bool:
    if _listedAsHolding(company):
        return True
    from dartlab.analysis.financial.earningsQuality import calcNonOperatingBreakdown

    nob = calcNonOperatingBreakdown(company)
    if not nob:
        return False
    latest = nob["history"][0] if nob.get("history") else None
    if not latest:
        return False
    opInc = abs(latest.get("opIncome") or 1)
    assocInc = abs(latest.get("associateIncome") or 0)
    if opInc > 0 and assocInc / opInc > 0.30:
        return True
    finCost = abs(latest.get("finCost") or 0)
    finIncome = abs(latest.get("finIncome") or 0)
    nonOpTotal = abs(latest.get("nonOpTotal") or 0)
    nonOpExFinance = nonOpTotal - finCost - finIncome
    return opInc > 0 and nonOpExFinance > 0 and nonOpExFinance / opInc > 0.80


def _checkGrowth(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    from dartlab.analysis.financial.growthAnalysis import calcCagrComparison

    cc = calcCagrComparison(company)
    if not cc:
        return False
    for comp in cc.get("comparisons", []):
        if comp.get("label") == "마진 방향" and comp.get("cagr1") is not None:
            if comp["cagr1"] > 15:
                cv = _cv(ctx["opMargins"])
                if cv is not None and cv > 0.5:
                    return False
                return True
    return False


def _checkCashRich(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    nd, ta, cash = ctx["netDebt"], ctx["totalAssets"], ctx["cash"]
    return nd is not None and ta and cash and nd < 0 and cash / ta > 0.20


def _checkCyclical(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    cv = _cv(ctx["opMargins"])
    return cv is not None and cv > 0.4


def _checkCapitalIntensive(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    ppe, ta = ctx["ppe"], ctx["totalAssets"]
    return ppe is not None and ta and ppe / ta > 0.40


def _checkFranchise(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    opMargin = ctx["opMargin"]
    if opMargin is None or opMargin <= 10:
        return False
    cv = _cv(ctx["opMargins"])
    return cv is not None and cv < 0.15


_TEMPLATE_CHECKS: list[tuple[str, object]] = [
    ("턴어라운드", _checkTurnaround),
    ("지주", _checkHolding),
    ("성장", _checkGrowth),
    ("현금부자", _checkCashRich),
    ("사이클", _checkCyclical),
    ("자본집약", _checkCapitalIntensive),
    ("프랜차이즈", _checkFranchise),
]


def detectTemplates(company) -> list[str]:
    """기업 재무 데이터에서 해당하는 스토리 템플릿 전부 반환.

    Capabilities:
        - 9 종 템플릿 (턴어라운드/지주/성장/현금부자 등) 다중 매칭.

    Guide:
        한 회사가 여러 라벨 동시 충족 가능 — 전부 반환.

    When:
        스토리 작성 라우팅 — "어느 템플릿 코퍼스 쓸까?" 결정 시.

    How:
        _TEMPLATE_CHECKS 9 개 순회 → 매칭 이름 누적.

    Requires:
        company 객체와 각 check 가 요구하는 재무 슬롯.

    Raises:
        없음 (각 check 예외는 흡수).

    Example:
        >>> detectTemplates(c)
        ["성장", "프랜차이즈"]

    See Also:
        - detectTemplate : 첫 매칭만 반환

    AIContext:
        AI 가 회사 설명 톤/구조 라우팅 (성장 vs 가치) 결정에 사용.
    """
    results: list[str] = []
    for name, check in _TEMPLATE_CHECKS:
        try:
            if check(company):
                results.append(name)
        except (AttributeError, ValueError, TypeError, KeyError, IndexError):
            continue
    return results


def detectTemplate(company) -> str | None:
    """기업 재무 데이터에서 스토리 템플릿 자동 판별. 첫 매칭 반환.

    Requires:
        company 객체.

    Raises:
        없음.

    Example:
        >>> detectTemplate(c)
        "성장"
    """
    results = detectTemplates(company)
    return results[0] if results else None
