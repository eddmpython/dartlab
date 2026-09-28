"""SEC disclosure parser — Form 4 / DEF 14A / 8-K skeleton (P-PR7+8 신규).

dart 의 ops/insiderTrades + docs/finance/executivePay + buildLiveFilings 패리티.

향후 본문 구현은 P-PR-edgar-depth 트랙. 본 모듈은 측정 게이트 통과 + 시그니처 정착.

3 함수:
    parseForm4Xml — SEC Form 4 임원 거래 XML.
    parseDef14aHtml — SEC DEF 14A 임원 보수 HTML.
    parseEightKHtml — SEC 8-K Item 별 본문.
"""

from __future__ import annotations

import re

import polars as pl

# 8-K Item 헤더 regex — "Item X.XX" 또는 "ITEM X.XX" (대소문자 무관).
# 본문이 plaintext / HTML 모두 매칭 — HTML 태그는 strip 후 적용.
_RE_8K_ITEM_HEADER = re.compile(
    r"(?:^|\n|\.|>)\s*(?:Item|ITEM)\s+([1-9]\.\d{2})\b[\s\.\-:]*",
    re.IGNORECASE,
)


def _parseForm4Xml(xml: str) -> pl.DataFrame:
    """SEC Form 4 ownership XML → transaction row.

    Form 4 XML schema:
    - ``<reportingOwner>/<reportingOwnerId>/<rptOwnerName>`` — insider name
    - ``<reportingOwner>/<reportingOwnerRelationship>`` — role (officer/director 등)
    - ``<nonDerivativeTransaction>`` 또는 ``<derivativeTransaction>``:
      - ``<transactionDate>/<value>`` — YYYY-MM-DD
      - ``<transactionAmounts>/<transactionShares>/<value>`` — share count
      - ``<transactionAmounts>/<transactionPricePerShare>/<value>`` — price
      - ``<postTransactionAmounts>/<sharesOwnedFollowingTransaction>/<value>``
      - ``<transactionCoding>/<transactionCode>`` — A/D/P/S/M/F 등

    Args:
        xml: Form 4 XML 본문.

    Returns:
        7 컬럼 DataFrame. 파싱 실패 / 매칭 0 → 빈 schema.

    Raises:
        없음.
    """
    if not xml or "<" not in xml:
        return pl.DataFrame(
            schema={
                "insider": pl.Utf8,
                "role": pl.Utf8,
                "transactionDate": pl.Utf8,
                "shares": pl.Float64,
                "price": pl.Float64,
                "postShares": pl.Float64,
                "transactionCode": pl.Utf8,
            }
        )

    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return pl.DataFrame(
            schema={
                "insider": pl.Utf8,
                "role": pl.Utf8,
                "transactionDate": pl.Utf8,
                "shares": pl.Float64,
                "price": pl.Float64,
                "postShares": pl.Float64,
                "transactionCode": pl.Utf8,
            }
        )

    # reportingOwner 이름 + role 추출 (첫 1 명만).
    insider = ""
    role = ""
    ownerNode = root.find(".//reportingOwner")
    if ownerNode is not None:
        nameNode = ownerNode.find(".//rptOwnerName")
        if nameNode is not None and nameNode.text:
            insider = nameNode.text.strip()
        relation = ownerNode.find(".//reportingOwnerRelationship")
        if relation is not None:
            roles: list[str] = []
            for childTag in ("isDirector", "isOfficer", "isTenPercentOwner", "isOther"):
                child = relation.find(childTag)
                if child is not None and child.text and child.text.strip() in ("1", "true"):
                    roles.append(childTag.removeprefix("is").lower())
            officerTitle = relation.find("officerTitle")
            if officerTitle is not None and officerTitle.text:
                roles.append(officerTitle.text.strip())
            role = "/".join(roles)

    rows: list[dict[str, object]] = []
    for txnTag in ("nonDerivativeTransaction", "derivativeTransaction"):
        for txn in root.findall(f".//{txnTag}"):
            txnDate = _xmlValue(txn, "transactionDate/value")
            shares = _xmlFloat(txn, "transactionAmounts/transactionShares/value")
            price = _xmlFloat(txn, "transactionAmounts/transactionPricePerShare/value")
            postShares = _xmlFloat(txn, "postTransactionAmounts/sharesOwnedFollowingTransaction/value")
            code = _xmlValue(txn, "transactionCoding/transactionCode")
            if txnDate is None and shares is None and code is None:
                continue
            rows.append(
                {
                    "insider": insider,
                    "role": role,
                    "transactionDate": txnDate or "",
                    "shares": shares,
                    "price": price,
                    "postShares": postShares,
                    "transactionCode": code or "",
                }
            )

    if not rows:
        return pl.DataFrame(
            schema={
                "insider": pl.Utf8,
                "role": pl.Utf8,
                "transactionDate": pl.Utf8,
                "shares": pl.Float64,
                "price": pl.Float64,
                "postShares": pl.Float64,
                "transactionCode": pl.Utf8,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "insider": pl.Utf8,
            "role": pl.Utf8,
            "transactionDate": pl.Utf8,
            "shares": pl.Float64,
            "price": pl.Float64,
            "postShares": pl.Float64,
            "transactionCode": pl.Utf8,
        },
    )


_DEF14A_COMP_COLUMNS = (
    "name",
    "position",
    "year",
    "salary",
    "bonus",
    "stockAwards",
    "total",
)

# Summary Compensation Table 헤더 후보 — SEC convention.
# 본 함수는 BS 없이 regex 만으로 row 추출 (간단 휴리스틱). 정확도는 별 cycle 의
# BS 기반 parser 가 후속.
_RE_DEF14A_YEAR = re.compile(r"\b(20\d{2})\b")
_RE_DEF14A_DOLLAR = re.compile(r"\$?\s*([\d,]+(?:\.\d+)?)")


def _parseDef14aCompensation(html: str) -> pl.DataFrame:
    """DEF 14A HTML 의 Summary Compensation Table row 추출.

    SEC Summary Compensation Table 표준 구조:
    - Name and Principal Position / Year / Salary / Bonus / Stock Awards /
      Option Awards / Non-Equity Incentive / Pension / All Other / Total.

    본 함수는 BS 없이 regex 기반 휴리스틱 — table cell 단위 추출:
    1. ``<table>`` block 식별 + ``compensation``/``summary`` 키워드 매칭
    2. 각 row 의 cells 추출 → year 컬럼 + dollar 컬럼 위치 매핑
    3. name + position (첫 2 셀) + 금액 (year / salary / bonus / stockAwards / total)

    Args:
        html: DEF 14A HTML 본문.

    Returns:
        7 컬럼 DataFrame. 파싱 실패 → 빈 schema.

    Raises:
        없음.
    """
    if not html or "<table" not in html.lower():
        return pl.DataFrame(
            schema={
                "name": pl.Utf8,
                "position": pl.Utf8,
                "year": pl.Int64,
                "salary": pl.Float64,
                "bonus": pl.Float64,
                "stockAwards": pl.Float64,
                "total": pl.Float64,
            }
        )

    # compensation 키워드 보유 table block 만 추출.
    tableBlocks = re.findall(
        r"<table[^>]*>(.*?)</table>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    rows: list[dict[str, object]] = []
    for block in tableBlocks:
        if "compensation" not in block.lower() and "salary" not in block.lower():
            continue
        for trMatch in re.finditer(r"<tr[^>]*>(.*?)</tr>", block, flags=re.IGNORECASE | re.DOTALL):
            tr = trMatch.group(1)
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.IGNORECASE | re.DOTALL)
            if len(cells) < 4:
                continue
            cleanCells = [_stripHtmlTags(c) for c in cells]
            row = _matchCompensationRow(cleanCells)
            if row:
                rows.append(row)

    if not rows:
        return pl.DataFrame(
            schema={
                "name": pl.Utf8,
                "position": pl.Utf8,
                "year": pl.Int64,
                "salary": pl.Float64,
                "bonus": pl.Float64,
                "stockAwards": pl.Float64,
                "total": pl.Float64,
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "name": pl.Utf8,
            "position": pl.Utf8,
            "year": pl.Int64,
            "salary": pl.Float64,
            "bonus": pl.Float64,
            "stockAwards": pl.Float64,
            "total": pl.Float64,
        },
    )


def _matchCompensationRow(cells: list[str]) -> dict[str, object] | None:
    """compensation table row 의 cells 에서 7 필드 매칭.

    Args:
        cells: row 의 plaintext 셀 list (>= 4 개).

    Returns:
        7 컬럼 dict 또는 매칭 실패 시 None (header / sub-header / 빈 row).

    Raises:
        없음.
    """
    if not cells:
        return None
    # name = 첫 셀 (한 줄 ≤ 80 자 이상이면 row 아님).
    name = cells[0].strip()
    if not name or len(name) > 80:
        return None
    # year 컬럼 — 셀 중 4 자리 연도 단독.
    year: int | None = None
    yearIdx: int | None = None
    for i, c in enumerate(cells[1:], start=1):
        cleaned = c.strip()
        m = _RE_DEF14A_YEAR.fullmatch(cleaned)
        if m:
            year = int(m.group(1))
            yearIdx = i
            break
    if year is None or yearIdx is None:
        return None

    # position = name 셀 안 줄바꿈 두 번째 줄 또는 두 번째 셀.
    position = ""
    if "\n" in cells[0]:
        parts = cells[0].split("\n", 1)
        name = parts[0].strip()
        position = parts[1].strip()
    elif yearIdx > 1:
        position = cells[1].strip()

    # year 이후 셀 = 금액 — dollar regex 매칭 순서대로 salary / bonus / stockAwards / total.
    amounts: list[float] = []
    for c in cells[yearIdx + 1 :]:
        m = _RE_DEF14A_DOLLAR.search(c)
        if m:
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except ValueError:
                pass
    if not amounts:
        return None

    salary = amounts[0] if len(amounts) >= 1 else None
    bonus = amounts[1] if len(amounts) >= 2 else None
    stockAwards = amounts[2] if len(amounts) >= 3 else None
    total = amounts[-1] if len(amounts) >= 4 else None

    return {
        "name": name,
        "position": position,
        "year": year,
        "salary": salary,
        "bonus": bonus,
        "stockAwards": stockAwards,
        "total": total,
    }


def _xmlValue(node, path: str) -> str | None:
    """XML node 의 path 텍스트 추출. 부재 시 None."""
    child = node.find(path)
    if child is None or child.text is None:
        return None
    text = child.text.strip()
    return text or None


def _xmlFloat(node, path: str) -> float | None:
    """XML node 의 path 를 float 으로 변환. 부재/실패 → None."""
    text = _xmlValue(node, path)
    if not text:
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


# script / style block (여는 태그부터 끝 태그까지). HTML 토크나이저처럼 태그 이름 뒤에는 공백, "/", ">" 만 온다고
# 본다. 그래서 "</script >", '</script foo="bar">', "</SCRIPT\t\n bar>" 같은 끝 태그도 블록 끝으로 잡고,
# "<scripts>"/"<stylesheet>" 처럼 이름이 다른 태그는 블록 시작으로 보지 않는다.
_RE_SCRIPT_STYLE_BLOCK = re.compile(
    r"<(?:script|style)(?:[\s/][^>]*)?>.*?</(?:script|style)(?:[\s/][^>]*)?>",
    re.IGNORECASE | re.DOTALL,
)


def _stripHtmlTags(html: str) -> str:
    """HTML 태그 제거 — BeautifulSoup 없이 regex 만으로 plaintext 변환.

    Args:
        html: HTML 본문.

    Returns:
        태그 제거된 plaintext (entity decoded).

    Raises:
        없음.
    """
    if not html or "<" not in html:
        return html
    # script / style block 본문 제거 (그 안 텍스트가 8-K item 처럼 보이는 사고 차단).
    text = _RE_SCRIPT_STYLE_BLOCK.sub(" ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    # HTML entity 간단 decode (& &amp; 등).
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parseEightKItems(html: str) -> pl.DataFrame:
    """8-K HTML → Item rows. Item X.XX 헤더 매칭 + 다음 헤더까지 본문 slice.

    Args:
        html: 8-K HTML 본문.

    Returns:
        ``item`` / ``label`` / ``text`` 3 컬럼 DataFrame. 매칭 0 → 빈 schema.

    Raises:
        없음.
    """
    if not html:
        return pl.DataFrame(schema={"item": pl.Utf8, "label": pl.Utf8, "text": pl.Utf8})
    text = _stripHtmlTags(html)
    if not text:
        return pl.DataFrame(schema={"item": pl.Utf8, "label": pl.Utf8, "text": pl.Utf8})

    # Item 헤더 매칭 위치 모두 수집.
    matches = list(_RE_8K_ITEM_HEADER.finditer(text))
    if not matches:
        return pl.DataFrame(schema={"item": pl.Utf8, "label": pl.Utf8, "text": pl.Utf8})

    rows: list[dict[str, str]] = []
    for i, match in enumerate(matches):
        itemNum = match.group(1)
        # 본문 = 현 헤더 끝부터 다음 헤더 시작까지.
        bodyStart = match.end()
        bodyEnd = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[bodyStart:bodyEnd].strip()
        # 본문 길이 제한 (4 KB) — 8-K item 본문이 비정상적으로 큰 경우 잘림.
        if len(body) > 4096:
            body = body[:4096] + "..."
        rows.append(
            {
                "item": itemNum,
                "label": STANDARD_8K_ITEMS.get(itemNum, f"Item {itemNum}"),
                "text": body,
            }
        )
    return pl.DataFrame(rows, schema={"item": pl.Utf8, "label": pl.Utf8, "text": pl.Utf8})


# 8-K 표준 Items (사용자 노출용 라벨)
STANDARD_8K_ITEMS: dict[str, str] = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrants Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure / Election of Directors or Principal Officers",
    "5.03": "Amendments to Articles of Incorporation",
    "5.04": "Temporary Suspension of Trading Under Registrants Employee Benefit Plans",
    "5.05": "Amendments to the Registrants Code of Ethics",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Director Nominations",
    "6.01": "ABS Informational and Computational Material",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


def parseForm4Xml(xml: str) -> pl.DataFrame:
    """Form 4 XML 본문에서 임원 거래 row 추출 (skeleton).

    Capabilities:
        - SEC Form 4 XML schema 따라 transaction row 추출 (향후 구현).
        - 본 skeleton 은 빈 DataFrame 반환.

    Args:
        xml: Form 4 XML 본문 문자열.

    Returns:
        pl.DataFrame — 임원 거래. 본 skeleton 은 빈 schema.

    Raises:
        없음.

    Example:
        >>> parseForm4Xml("").is_empty()
        True

    Guide:
        - "SEC 임원 거래" → 본 함수 (향후 구현 후).

    SeeAlso:
        - ``dart.providers.dart.ops.insiderTrades`` — 동등 KR 임원 거래.

    Requires:
        - polars.

    AIContext:
        Workbench "임원 거래 (insider trading)" 질문 entry (향후).

    LLM Specifications:
        AntiPatterns:
            - xml 이 Form 4 schema 아님 → 빈 DataFrame.
        OutputSchema:
            - pl.DataFrame — 7 컬럼.
        Prerequisites:
            - SEC EDGAR Form 4 XML 다운로드.
        Freshness:
            - 호출 시점.
        Dataflow:
            - SEC API → 본 함수 → AI.
        TargetMarkets:
            - US (EDGAR) 한정.
    """
    return _parseForm4Xml(xml)


def parseDef14aHtml(html: str) -> pl.DataFrame:
    """DEF 14A HTML 본문에서 임원 보수 row 추출 (skeleton).

    Capabilities:
        - SEC DEF 14A Summary Compensation Table 의 임원 보수 row 추출 (향후).
        - 본 skeleton 은 빈 DataFrame.

    Args:
        html: DEF 14A HTML 본문.

    Returns:
        pl.DataFrame — 임원 보수. 본 skeleton 은 빈 schema.

    Raises:
        없음.

    Example:
        >>> parseDef14aHtml("").is_empty()
        True

    Guide:
        - "이 회사 CEO 연봉" → 본 함수 (향후).

    SeeAlso:
        - ``dart.providers.dart.docs.finance.executivePay`` — 동등 KR.

    Requires:
        - polars.

    AIContext:
        Workbench "임원 보수" 질문 entry (향후).

    LLM Specifications:
        AntiPatterns:
            - html 이 DEF 14A 아님 → 빈.
        OutputSchema:
            - pl.DataFrame — 7 컬럼.
        Prerequisites:
            - SEC EDGAR DEF 14A HTML 다운로드.
        Freshness:
            - 호출 시점.
        Dataflow:
            - SEC API → 본 함수 → AI.
        TargetMarkets:
            - US (EDGAR) 한정.
    """
    return _parseDef14aCompensation(html)


def parseEightKHtml(html: str) -> pl.DataFrame:
    """8-K HTML 본문에서 Item 별 row 추출 (skeleton).

    Capabilities:
        - SEC 8-K "Item X.XX" 패턴 매칭 + 본문 slice (향후).
        - 본 skeleton 은 빈 DataFrame.

    Args:
        html: 8-K HTML 본문.

    Returns:
        pl.DataFrame — Item row. 본 skeleton 은 빈 schema.

    Raises:
        없음.

    Example:
        >>> parseEightKHtml("").is_empty()
        True

    Guide:
        - "이 회사 최근 8-K 무슨 일" → 본 함수 (향후).

    SeeAlso:
        - ``STANDARD_8K_ITEMS`` — 24 Item 카탈로그.
        - ``dart.providers.dart.builder.filingsCatalog.buildLiveFilings`` — 동등 KR.

    Requires:
        - polars.

    AIContext:
        Workbench "최근 8-K" 질문 entry (향후).

    LLM Specifications:
        AntiPatterns:
            - html 이 8-K 아님 → 빈.
        OutputSchema:
            - pl.DataFrame — 3 컬럼.
        Prerequisites:
            - SEC EDGAR 8-K HTML 다운로드.
        Freshness:
            - 호출 시점.
        Dataflow:
            - SEC API → 본 함수 → AI.
        TargetMarkets:
            - US (EDGAR) 한정.
    """
    return _parseEightKItems(html)


def itemLabel(itemNum: str) -> str:
    """8-K Item 번호 → 표준 라벨 lookup.

    Capabilities:
        - ``STANDARD_8K_ITEMS`` dict lookup.

    Args:
        itemNum: 예 "2.02", "5.02".

    Returns:
        str — 라벨. 미정의 → "Item {N}" fallback.

    Raises:
        없음.

    Example:
        >>> itemLabel("2.02")
        'Results of Operations and Financial Condition'

    Guide:
        - "Item 5.02 정식 이름" → ``itemLabel("5.02")``.

    SeeAlso:
        - ``STANDARD_8K_ITEMS`` — SSOT.

    Requires:
        - 외부 의존 없음.

    AIContext:
        AI 가 Item 번호 + 라벨 동시 노출.

    LLM Specifications:
        AntiPatterns:
            - itemNum 형식 변형 → fallback.
        OutputSchema:
            - str.
        Prerequisites:
            - 없음.
        Freshness:
            - SEC 양식 변경 시 갱신.
        Dataflow:
            - STANDARD_8K_ITEMS → 본 함수.
        TargetMarkets:
            - US (EDGAR) 한정.
    """
    return STANDARD_8K_ITEMS.get(itemNum, f"Item {itemNum}")


# 8-K Item → business category 매핑. SEC item 번호 (1.0x = agreements, 2.0x =
# financial, 3.0x = securities, 4.0x = auditor, 5.0x = governance, 6.0x = ABS,
# 7.0x = Reg FD, 8.0x = other, 9.0x = exhibits) 첫 자리 + 의미 매핑.
_ITEM_CATEGORY: dict[str, str] = {
    "1.01": "MATERIAL_AGREEMENT",
    "1.02": "MATERIAL_AGREEMENT",
    "1.03": "FINANCIAL_DISTRESS",
    "2.01": "MA_ACTIVITY",
    "2.02": "EARNINGS",
    "2.03": "FINANCIAL_OBLIGATION",
    "2.04": "FINANCIAL_OBLIGATION",
    "2.05": "RESTRUCTURING",
    "2.06": "IMPAIRMENT",
    "3.01": "LISTING_STATUS",
    "3.02": "EQUITY_ISSUANCE",
    "3.03": "SHAREHOLDER_RIGHTS",
    "4.01": "AUDITOR_CHANGE",
    "4.02": "ACCOUNTING_RESTATEMENT",
    "5.01": "CONTROL_CHANGE",
    "5.02": "EXECUTIVE_CHANGE",
    "5.03": "GOVERNANCE",
    "5.04": "EMPLOYEE_PLAN",
    "5.05": "ETHICS",
    "5.07": "SHAREHOLDER_VOTE",
    "5.08": "SHAREHOLDER_VOTE",
    "6.01": "ABS",
    "7.01": "REG_FD",
    "8.01": "OTHER",
    "9.01": "EXHIBITS",
}


def itemCategory(itemNum: str) -> str:
    """8-K Item 번호 → 비즈니스 카테고리 매핑.

    25 표준 item 을 15 카테고리 (MATERIAL_AGREEMENT / EARNINGS /
    EXECUTIVE_CHANGE / GOVERNANCE / 등) 로 분류. catalyst 시계열 분석 시
    item 번호 raw 보다 카테고리 단위 집계가 의미.

    Args:
        itemNum: 예 ``"2.02"`` / ``"5.02"``.

    Returns:
        대문자 카테고리 ID. 미정의 item → ``"UNKNOWN"``.

    Raises:
        없음.

    Example:
        >>> itemCategory("2.02")
        'EARNINGS'
        >>> itemCategory("99.99")
        'UNKNOWN'
    """
    return _ITEM_CATEGORY.get(itemNum, "UNKNOWN")


def fetchItemsByCategory(items: pl.DataFrame, category: str, *, limit: int = 100) -> pl.DataFrame:
    """parsed 8-K items DataFrame 에서 특정 카테고리만 필터.

    Args:
        items: ``parseEightKHtml`` 결과 또는 ``item`` 컬럼 보유 DataFrame.
        category: ``itemCategory`` 반환값 (예 ``"EARNINGS"``).
        limit: 최대 결과 row 수.

    Returns:
        해당 카테고리 items. 빈 입력 → 빈 DataFrame.

    Raises:
        없음.

    Example:
        >>> earnings = fetchItemsByCategory(items, "EARNINGS")  # doctest: +SKIP
    """
    if items.is_empty() or "item" not in items.columns:
        return items.head(0)
    filtered = (
        items.with_columns(pl.col("item").map_elements(itemCategory, return_dtype=pl.Utf8).alias("_category"))
        .filter(pl.col("_category") == category)
        .drop("_category")
    )
    if limit > 0:
        filtered = filtered.head(limit)
    return filtered


def iterItemsByCategory(items: pl.DataFrame, category: str, *, batchSize: int = 50):
    """``fetchItemsByCategory`` 의 streaming pair (룰 10).

    Args:
        items: ``item`` 컬럼 보유 DataFrame.
        category: ``itemCategory`` 반환값.
        batchSize: batch 당 row 수.

    Yields:
        pl.DataFrame — batch 단위.

    Raises:
        없음.

    Example:
        >>> for batch in iterItemsByCategory(items, "EARNINGS"):
        ...     pass  # doctest: +SKIP
    """
    if items.is_empty() or "item" not in items.columns:
        return
    filtered = (
        items.with_columns(pl.col("item").map_elements(itemCategory, return_dtype=pl.Utf8).alias("_category"))
        .filter(pl.col("_category") == category)
        .drop("_category")
    )
    n = filtered.height
    for start in range(0, n, batchSize):
        yield filtered.slice(start, batchSize)
