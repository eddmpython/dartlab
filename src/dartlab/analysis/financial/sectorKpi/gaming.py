"""게임·엔터 KPI — IP 포트폴리오/콘텐츠 집중도/매출 구성.

DART panel(productService) + IS 활용.
"""

from __future__ import annotations

import logging
import re

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import parseNumStr

log = logging.getLogger(__name__)

# 공시 표는 셀 안에 공백을 섞어 쓴다 ("합 계", "품 목"). 비교 전에 지운다.
_WS_RE = re.compile(r"\s+")

# 표 첫 행은 기수 열의 부제목이다 (매출액 / 영업수익 / 비율). 이름 열은 제 이름을 되풀이한다.
_AMOUNT_LABELS = ("매출", "금액", "수익")
_RATIO_LABELS = ("비율", "비중")
# 이름 열 후보에서 뺄 것. 이 표에서 알고 싶은 것은 품목이지 그것을 파는 법인이 아니다.
_ENTITY_LABELS = ("회사", "법인", "대상", "거래처")
# 합계 행 표시. "영업수익 총계" 처럼 앞말이 붙기도 해서 부분일치로 본다. 홑글자 "계" 는
# "계열" 같은 품목명을 잡아먹으므로 전체가 그 글자일 때만 합계로 친다.
_TOTAL_MARKS = ("합계", "소계", "총계")


def _splitHeader(header: dict[str, str]) -> tuple[str | None, str | None]:
    """부제목 행에서 (금액 열, 이름 열) 을 고른다. 못 고르면 (None, None).

    가르는 기준은 머리글이 제 열 이름을 되풀이하는지다. 이름 열은 위아래 두 줄이 같은 말을
    쓴다 ("품목" 아래 "품목"). 값 열은 열 이름이 기수고 그 아래에 무엇을 담았는지가 온다
    ("제30기 1분기" 아래 "매출액"). 이 구분이 없으면 "매출유형" 처럼 이름 안에 "매출" 이
    든 이름 열을 금액 열로 잘못 집는다.

    DART 표는 기수를 최신부터 왼쪽에 두므로 첫 금액 열이 최신 기수다. 이름 열은 여러 개
    (사업부문·구분·품목) 인데 가장 오른쪽이 가장 잘게 쪼갠 이름이라 그것을 쓴다. 다만
    "대상회사" 처럼 법인을 적는 열은 품목이 아니므로 후보에서 뺀다.
    """
    amountCol = None
    nameCol = None
    for key, label in header.items():
        text = _WS_RE.sub("", str(label or ""))
        if not text:
            continue
        if text == _WS_RE.sub("", str(key or "")):
            if not any(word in text for word in _ENTITY_LABELS):
                nameCol = key
            continue
        if any(word in text for word in _RATIO_LABELS):
            continue
        if amountCol is None and any(word in text for word in _AMOUNT_LABELS):
            amountCol = key
    return amountCol, nameCol


def _pickProductTable(code: str | None) -> tuple[list[dict[str, str]], str, str, str] | None:
    """제품별 매출 표를 하나 고른다. (행, 금액 열, 이름 열, 기간) 또는 None.

    한 섹션에 표가 여러 개 붙어 있다 (사업부문 설명표, 매출 구성표, 주석표). 표를 이어
    붙여 놓고 첫 행을 머리로 삼으면 엉뚱한 표의 머리를 읽는다. 표 단위로 훑어 금액 열과
    이름 열이 모두 잡히는 첫 표를 쓴다. 기간을 최신 하나로 묶는 것은 여러 해 표가 섞여
    합계가 뒤엉키는 것을 막기 위해서다.
    """
    if not code:
        return None
    from dartlab.providers.dart.panel.text import gridToRowDicts, panelLatestPeriod, panelXmlTables

    for pattern in ("제품", "부문"):
        period = panelLatestPeriod(code, sectionPattern=pattern)
        if period is None:
            continue
        for grid in panelXmlTables(code, sectionPattern=pattern, period=period):
            rows = gridToRowDicts(grid)
            if len(rows) < 2:
                continue
            amountCol, nameCol = _splitHeader(rows[0])
            if amountCol and nameCol:
                return rows, amountCol, nameCol, period
    return None


@memoizedCalc
def calcGamingKpis(company, *, basePeriod: str | None = None) -> dict | None:
    """게임·엔터 핵심 KPI.

    Capabilities:
        - productService 매출 분해 → IP 포트폴리오 HHI + 1위 IP 의존도.

    Guide:
        rows → 매출액 추출 → share 계산 → HHI · top1 share.

    When:
        넥슨/엔씨/카카오게임즈 등 IP 비즈니스 평가 시.

    How:
        제품별 매출 share → 제곱합×10000 = HHI. >4000 고집중, >2500 중집중, 이하 분산.

    Requires:
        company.panel("productService") 또는 panel("segments") rows 존재.

    Raises:
        없음. AttributeError·ValueError·TypeError·KeyError try 흡수.

    Returns:
        dict | None
            ipPortfolio : dict — IP별 매출 추정 + HHI
            contentConcentration : dict | None — 주력 IP 의존도

    Example:
        >>> calcGamingKpis(엔씨소프트)
        {"ipPortfolio": {...}, "contentConcentration": {...}}

    See Also:
        - dispatcher.sectorKpi : 섹터 자동 라우팅.

    AIContext:
        IP 집중 위험 (단일 IP 매출 의존) 평가 인용.
    """
    result: dict = {}

    try:
        picked = _pickProductTable(getattr(company, "stockCode", None))
        if picked is None:
            return None
        rows, amountCol, nameCol, period = picked

        # 같은 품목이 사업부문만 달리해 두 줄로 나뉘어 있기도 하다. 이름으로 합치지 않으면
        # 한 품목이 쪼개져 집중도가 실제보다 낮게 나온다.
        byName: dict[str, float] = {}
        for r in rows[1:]:
            name = str(r.get(nameCol, "") or "").strip()
            flat = _WS_RE.sub("", name)
            if not flat or flat == "계" or any(mark in flat for mark in _TOTAL_MARKS):
                continue
            amt = parseNumStr(r.get(amountCol))
            if amt:
                byName[name] = byName.get(name, 0.0) + abs(amt)

        products = [{"name": n, "revenue": v} for n, v in byName.items()]
        total_rev = sum(byName.values())

        if products and total_rev > 0:
            for p in products:
                p["share"] = round(p["revenue"] / total_rev * 100, 1)

            shares = [p["share"] / 100 for p in products]
            hhi = round(sum(s**2 for s in shares) * 10000)

            products.sort(key=lambda x: x["revenue"], reverse=True)

            result["ipPortfolio"] = {
                "products": products[:10],
                "hhi": hhi,
                "totalRevenue": total_rev,
                "period": period,
            }
            result["contentConcentration"] = {
                "topIp": products[0]["name"],
                "topShare": products[0]["share"],
                "hhi": hhi,
                "verdict": "고집중" if hhi > 4000 else "중집중" if hhi > 2500 else "분산",
            }
    except (AttributeError, ValueError, TypeError, KeyError) as exc:
        log.debug("게임 KPI 산출 실패: %s", exc)

    return result if result else None
