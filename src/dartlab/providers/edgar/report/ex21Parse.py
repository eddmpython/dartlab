"""10-K EX-21(자회사 목록) exhibit 파서. 자회사명 + 설립관할 추출.

US 는 타법인출자를 DART(피출자사 장부가·지분율 표)처럼 주지 않고 10-K EX-21 exhibit 에 자회사명·설립
관할(jurisdiction) 목록만 공시한다(장부가·지분율 무공시 = 정직 null). 표 기반(name|jurisdiction 2컬럼)
과 리스트 기반 양식을 처리한다. 실측: AAPL EX-21 자회사 19개(Apple Asia Limited/Hong Kong 등).

scan 빌더(``ex21Build``)가 lazy import 로 소비(L1 provider, 상향 import 0).
"""

from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# 헤더/잡행 배제 시그니처 (자회사명 아님)
_NOT_NAME = re.compile(r"(?i)^(name|subsidiar|jurisdiction|state|country|entity|exhibit|list of)")


def parseSubsidiaries(html: str) -> list[dict]:
    """EX-21 exhibit HTML 에서 자회사 행을 뽑는다.

    표 양식: 행 = [자회사명, (중간컬럼), 관할]. 마지막 비어있지 않은 셀을 관할로 본다.
    헤더행(Name/Jurisdiction 류)과 3자 미만 텍스트는 제외.

    Args:
        html: EX-21 exhibit 전체 HTML.

    Returns:
        list[dict]: ``{name, jurisdiction}``. 표 부재/비정형이면 [].

    Raises:
        없음.

    Example:
        >>> rows = parseSubsidiaries(ex21Html)  # doctest: +SKIP
        >>> rows[0]  # {'name': 'Apple Asia Limited', 'jurisdiction': 'Hong Kong'}
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for tab in soup.find_all("table"):
        for tr in tab.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            cells = [re.sub(r"\s+", " ", c) for c in cells if c and c.strip()]
            if len(cells) < 2:
                continue
            name = cells[0]
            juris = cells[-1]
            if not re.search(r"[A-Za-z]{3,}", name) or _NOT_NAME.search(name):
                continue
            if len(juris) > 60 or not re.search(r"[A-Za-z]{2,}", juris):
                juris = ""
            out.append({"name": name[:80], "jurisdiction": juris[:60]})
    # 중복 제거(멀티 표 재수록)
    seen: set[str] = set()
    uniq: list[dict] = []
    for r in out:
        if r["name"] not in seen:
            seen.add(r["name"])
            uniq.append(r)
    return uniq


__all__ = ["parseSubsidiaries"]
