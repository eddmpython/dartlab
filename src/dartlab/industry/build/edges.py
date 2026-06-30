"""엣지 빌더 — panel + scan/network에서 공급-수요·계열 관계 추출.

데이터 소스:
1. scan/network — 투자관계(investedCompany), 계열사(affiliateGroup)
2. panel — 거래처(rawMaterial 텍스트), 특수관계자거래
3. 추후: AI/사람 검수

Company 객체를 로드하지 않고 parquet/report를 직접 스캔한다.
"""

from __future__ import annotations

import logging
import re

from dartlab.industry.types import IndustryEdge, IndustryNode

logger = logging.getLogger(__name__)


def _listingLookup() -> tuple[dict[str, str], dict[str, str]]:
    """KindList에서 종목코드↔회사명 양방향 매핑 테이블을 생성한다.

    Returns
    -------
    tuple[dict[str, str], dict[str, str]]
        (code_to_name, name_to_code) 두 딕셔너리.
        KindList 로드 실패 시 빈 딕셔너리 쌍 반환.
    """
    # F4.1: gather 직접 호출 → IndustryDataAccessor 위임 (정공법 B+C)
    from dartlab.core.di import getIndustryAccessor

    try:
        df = getIndustryAccessor().fetchListing()
        if df is None:
            return {}, {}
        cols = df.columns
        # listing 스키마는 gov 마이그레이션으로 short_code/codeName 으로 변경됨
        # (옛 종목코드/회사명). 신·구 양쪽 지원 (재빌드 견고성).
        codeCol = next((c for c in ("short_code", "종목코드") if c in cols), None)
        nameCol = next((c for c in ("codeName", "회사명") if c in cols), None)
        if not codeCol or not nameCol:
            return {}, {}
        codes = df[codeCol].to_list()
        names = df[nameCol].to_list()
        c2n = dict(zip(codes, names))
        n2c = dict(zip(names, codes))
        return c2n, n2c
    except (ValueError, KeyError, TypeError):
        return {}, {}


def _buildNodeIndex(nodes: list[IndustryNode]) -> dict[str, IndustryNode]:
    """노드 리스트에서 primary 노드만 추출하여 종목코드 인덱스를 만든다.

    Parameters
    ----------
    nodes : list[IndustryNode]
        전체 노드 리스트.

    Returns
    -------
    dict[str, IndustryNode]
        종목코드 → primary IndustryNode 매핑. 중복 시 첫 번째만 보존.
    """
    idx: dict[str, IndustryNode] = {}
    for n in nodes:
        if n.primary and n.stockCode not in idx:
            idx[n.stockCode] = n
    return idx


# ── 1. scan/network에서 계열사/투자 관계 ──


def extractNetworkEdges(nodes: list[IndustryNode]) -> list[IndustryEdge]:
    """scan/network의 investedCompany 데이터에서 계열·투자 엣지를 추출한다.

    Capabilities:
        DART 출자/투자내역 (`scan/network/scanner.scanInvested`) 에서 상장사 간 투자 관계만
        선별해 IndustryEdge 로 변환. 경영참여→affiliate (conf 0.9), 단순투자→investor (conf 0.6).

    Parameters
    ----------
    nodes : list[IndustryNode]
        전체 노드 리스트. primary 노드 기준으로 상장사 필터링.

    Returns
    -------
    list[IndustryEdge]
        추출된 계열·투자 엣지 리스트. 동일 from-to 쌍 중복 제거됨.

    Raises:
        없음 — scanInvested/buildInvestEdges 실패 시 warning + 빈 리스트 반환.

    Example:
        >>> from dartlab.industry.build.edges import extractNetworkEdges
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> edges = extractNetworkEdges(loadNodes())
        >>> edges[0].edgeType, edges[0].confidence
        ('affiliate', 0.9)

    Guide:
        ``buildAllEdges`` 의 1 단계 소스. 양쪽 모두 KindList 상장사여야 엣지 생성 — 비상장 모회사
        / 자회사는 자동 제외.

    When:
        산업지도 manifest 빌드 (`buildIndustryMap`) 의 1 단계 엣지 수집 시점.

    How:
        nodes 인덱스 + listing 룩업 → `scanInvested` 원천 → `buildInvestEdges` 변환 → 상장사 쌍
        필터링 → from-to 중복 제거 → IndustryEdge 리스트.

    Requires:
        - L1.5 scan: ``scan/network`` 산출 raw 데이터
        - reference: KindList (`_listingLookup`) — 상장사 code↔name 매핑

    See Also:
        - ``dartlab.industry.build.edges.extractDocsEdges`` : panel 패턴 추출
        - ``dartlab.industry.build.edges.extractRawMaterialEdges`` : 원재료 거래 추출
        - ``dartlab.industry.build.edges.buildAllEdges`` : 본 함수 호출 사용자

    AIContext:
        "이 회사의 계열사", "지분 관계" 류 답변 데이터. confidence 0.9 (경영참여) 만 강한 단정,
        0.6 (단순투자) 은 "투자 보유 관계" 정도로 약하게 인용.
    """
    edges: list[IndustryEdge] = []
    nodeIdx = _buildNodeIndex(nodes)
    c2n, n2c = _listingLookup()

    try:
        from dartlab.scan.network.scanner import loadListing, scanInvested

        raw = scanInvested()
        if raw is None or raw.height == 0:
            return edges

        name_to_code, code_to_name, listing_codes, _ = loadListing()

        from dartlab.scan.network.edges import buildInvestEdges

        investDf = buildInvestEdges(raw, name_to_code, code_to_name)
    except Exception as e:
        logger.warning("network 엣지 추출 실패: %s", e)
        return edges

    for row in investDf.iter_rows(named=True):
        fromCode = row.get("from_code", "")
        toCode = row.get("to_code")
        purpose = row.get("purpose", "")
        ownershipPct = row.get("ownership_pct")

        if not fromCode or not toCode:
            continue

        # 양쪽 다 상장사인 것만
        if fromCode not in nodeIdx or toCode not in nodeIdx:
            continue

        fromNode = nodeIdx[fromCode]
        toNode = nodeIdx[toCode]

        edgeType = "affiliate"
        if purpose == "경영참여":
            edgeType = "affiliate"
        elif purpose == "단순투자":
            edgeType = "investor"

        evidence = f"지분 {ownershipPct:.1f}%" if ownershipPct else ""
        if purpose:
            evidence = f"{purpose} {evidence}".strip()

        edges.append(
            IndustryEdge(
                fromCode=fromCode,
                fromName=c2n.get(fromCode, ""),
                toCode=toCode,
                toName=c2n.get(toCode, ""),
                edgeType=edgeType,
                industry=fromNode.industry,
                confidence=0.9 if purpose == "경영참여" else 0.6,
                source="network",
                evidence=evidence,
            )
        )

    # 중복 제거 (같은 from-to 쌍)
    seen: set[tuple[str, str]] = set()
    unique: list[IndustryEdge] = []
    for e in edges:
        key = (e.fromCode, e.toCode)
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique


# ── 2. panel에서 거래처 관계 (rawMaterial/relatedPartyTx) ──

# section_title → 공급/수요 분류 패턴
_SUPPLIER_TITLE = re.compile(r"원재료|원자재|부자재|매입처|공급처|거래처|생산설비")
_CUSTOMER_TITLE = re.compile(r"매출처|판매처|수주처|주요.*고객")
_RELATED_PARTY = re.compile(r"대주주.*거래|특수관계자|계열회사")

# 법인명 추출 패턴 — ㈜, (주), 주식회사 앞뒤로 회사명
_CORP_PATTERN = re.compile(
    r"㈜\s*([가-힣A-Za-z0-9]+)|([가-힣A-Za-z0-9]+)\s*㈜|\(주\)\s*([가-힣A-Za-z0-9]+)|주식회사\s+([가-힣A-Za-z0-9]+)"
)


def _extractCorpNames(content: str) -> list[str]:
    """본문에서 법인명 패턴(㈜, (주), 주식회사)을 추출한다.

    Parameters
    ----------
    content : str
        검색 대상 텍스트.

    Returns
    -------
    list[str]
        추출된 법인명 리스트 (2글자 이상만).
    """
    names: list[str] = []
    for m in _CORP_PATTERN.finditer(content):
        name = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if name and len(name) >= 2:
            names.append(name)
    return names


def extractDocsEdges(nodes: list[IndustryNode]) -> list[IndustryEdge]:
    """panel의 섹션 제목 패턴으로 supplier/customer/affiliate 엣지를 추출한다.

    Capabilities:
        DART 사업보고서 panel 의 ``section_title`` 패턴 (원재료/매출처/특수관계자) 으로
        본문에서 거래 상대방 상장사를 자동 식별. ㈜/주식회사 패턴 추출 + 상장사명 직접 매칭
        2 방식 병행.

    2가지 방법으로 상장사를 찾는다:
    1. 본문에서 ㈜/주식회사 패턴으로 법인명 추출 → KindList 매칭
    2. KindList 상장사명이 본문에 직접 나오는 경우 (3글자 이상)

    Parameters
    ----------
    nodes : list[IndustryNode]
        전체 노드 리스트. primary 노드의 종목코드별로 panel를 스캔.

    Returns
    -------
    list[IndustryEdge]
        추출된 엣지 리스트. from+to+type 기준 중복 제거됨.
        supplier confidence 0.7, customer 0.6, affiliate 0.5.

    Raises:
        없음 — 개별 panel 로드 실패 시 해당 종목만 skip.

    Example:
        >>> from dartlab.industry.build.edges import extractDocsEdges
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> edges = extractDocsEdges(loadNodes())
        >>> sum(1 for e in edges if e.edgeType == "supplier")
        2480

    Guide:
        ``buildAllEdges`` 의 2 단계. 패턴 추출이라 false positive 가능 — confidence 0.5~0.7
        구간이므로 단정 답변에는 부적합, "보고서에 언급" 정도로 인용.

    When:
        ``extractRawMaterialEdges`` 가 거래금액 정확도 우선이면, 본 함수는 거래 다양성/언급 추출
        우선. 두 함수 결과는 ``buildAllEdges`` 에서 병합.

    How:
        nodes 종목별 ``panel/{code}.parquet`` 스캔 → section_title 패턴 매칭 → 본문에서 ㈜/상장사명
        추출 → IndustryEdge 변환 → from+to+type 중복 제거.

    Requires:
        - providers.dart.panel.text: panel 섹션 본문 (`panelTextRows`)
        - reference: KindList (`_listingLookup`) — 상장사 code↔name 매핑

    See Also:
        - ``dartlab.industry.build.edges.extractRawMaterialEdges`` : 원재료 거래 (금액 우선)
        - ``dartlab.industry.build.edges.extractNetworkEdges`` : 계열·투자 관계
        - ``dartlab.industry.build.edges.buildAllEdges`` : 본 함수 호출 사용자

    AIContext:
        "이 회사의 주요 매출처", "거래처에 ○○ 언급" 류 답변 데이터. confidence 가 낮으므로 "보고서
        언급" 단서를 답변에 명시.
    """
    edges: list[IndustryEdge] = []
    nodeIdx = _buildNodeIndex(nodes)
    c2n, n2c = _listingLookup()

    # 매칭할 상장사명 집합 (3글자 이상 — 노이즈 방지)
    targetNames = {name: code for name, code in n2c.items() if len(name) >= 3}

    # providers.dart.panel.text SSOT(panel 섹션 본문) 소비.
    from dartlab.providers.dart.panel.text import panelTextRows

    processed = 0
    for code, node in nodeIdx.items():
        df = panelTextRows(code)
        if df is None or df.is_empty():
            continue

        for row in df.iter_rows(named=True):
            title = row.get("sectionLeaf") or ""
            content = row.get("contentRaw") or ""
            if not content or len(content) <= 20:
                continue

            isSupplier = bool(_SUPPLIER_TITLE.search(title))
            isCustomer = bool(_CUSTOMER_TITLE.search(title))
            isRelated = bool(_RELATED_PARTY.search(title))
            if not isSupplier and not isCustomer and not isRelated:
                continue

            # 방법 1: ㈜ 패턴으로 법인명 추출
            corpNames = _extractCorpNames(content)

            # 방법 2: 상장사명 직접 매칭
            foundCodes: set[str] = set()
            for corpName in corpNames:
                targetCode = n2c.get(corpName)
                if targetCode and targetCode != code:
                    foundCodes.add(targetCode)

            # content 2-gram 집합 — 이름 첫 2글자가 없으면 full substring 스캔 skip (조기 reject).
            # 결과 동일(이름이 content 에 있으면 첫 2글자는 반드시 2-gram), 2800 full-scan 대부분 컷.
            contentBigrams = {content[k : k + 2] for k in range(len(content) - 1)}
            for targetName, targetCode in targetNames.items():
                if targetCode == code or targetCode in foundCodes:
                    continue
                if targetName[:2] not in contentBigrams:
                    continue
                if targetName in content:
                    foundCodes.add(targetCode)

            # 엣지 생성
            for targetCode in foundCodes:
                targetName = c2n.get(targetCode, "")
                edgeType = "supplier" if isSupplier else "customer" if isCustomer else "affiliate"
                confidence = 0.7 if isSupplier else 0.6

                if isSupplier:
                    edges.append(
                        IndustryEdge(
                            fromCode=targetCode,
                            fromName=targetName,
                            toCode=code,
                            toName=c2n.get(code, ""),
                            edgeType="supplier",
                            industry=node.industry,
                            confidence=confidence,
                            source="panel_text",
                            evidence=f"{title}",
                        )
                    )
                elif isCustomer:
                    edges.append(
                        IndustryEdge(
                            fromCode=code,
                            fromName=c2n.get(code, ""),
                            toCode=targetCode,
                            toName=targetName,
                            edgeType="customer",
                            industry=node.industry,
                            confidence=confidence,
                            source="panel_text",
                            evidence=f"{title}",
                        )
                    )
                elif isRelated:
                    edges.append(
                        IndustryEdge(
                            fromCode=code,
                            fromName=c2n.get(code, ""),
                            toCode=targetCode,
                            toName=targetName,
                            edgeType="affiliate",
                            industry=node.industry,
                            confidence=0.5,
                            source="panel_text",
                            evidence=f"{title}",
                        )
                    )

        processed += 1

    logger.info("panel 텍스트 엣지: %d사 스캔, %d건 추출", processed, len(edges))

    # 중복 제거
    seen: set[tuple[str, str, str]] = set()
    unique: list[IndustryEdge] = []
    for e in edges:
        key = (e.fromCode, e.toCode, e.edgeType)
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique


# ── 3. panel 원재료 테이블 파싱 (강력한 한방) ──


def extractRawMaterialEdges(nodes: list[IndustryNode]) -> list[IndustryEdge]:
    """panel "원재료 및 생산설비" 마크다운 테이블에서 구조화된 supplier 엣지를 추출한다.

    Capabilities:
        DART 사업보고서 "원재료 및 생산설비" 섹션의 마크다운 테이블 (부문/품목/매입액/비중/매입처)
        을 파싱해 product/amount(억원)/ratio(%) 메타 포함 정밀 supplier 엣지를 산출. 표 헤더 매칭이
        성공한 회사만 — 비표 형식 본문은 ``extractDocsEdges`` 가 보완. 헤더는 퍼지 매칭(매입액/제NN기매입액
        ·비율/비중/병합셀)으로 드리프트 흡수 (레버 A).

        ★부수효과 (레버 A): 매입처가 **비상장**이면 그래프 엣지를 만들지 않되 (노드 미승격),
        매입액/비중을 가진 leaf supply fact 를 buyer 노드의 ``supplyFacts`` 에 **할당**한다 (in-place
        mutation, 멱등). ``calcSupplyInsights`` 가 이를 상장 엣지 amount 와 합산해 공급집중도 HHI 모수로
        쓴다 — 비상장 매입처가 대부분이라 amount 커버리지가 132 → ~600 수준으로 확장.

    구조화된 데이터: 부문 / 품목 / 매입액 / 비중 / 매입처
    → 공급사 실명 + 제품 + 거래 비중이 포함된 정밀 엣지.

    Parameters
    ----------
    nodes : list[IndustryNode]
        전체 노드 리스트. 비상장 매입처 leaf fact 가 primary 노드 ``supplyFacts`` 에 in-place 기록됨.

    Returns
    -------
    list[IndustryEdge]
        상장 매입처 supplier 엣지 리스트. confidence 0.9 (테이블 직접 매칭).
        각 엣지에 product (품목명), amount (매입액, 억원), ratio (비중, %) 포함.
        비상장 매입처는 엣지가 아니라 buyer 노드 ``supplyFacts`` 로 (Side Effects 참조).

    Raises:
        없음 — 개별 panel 로드 실패 시 해당 종목만 skip.

    Example:
        >>> from dartlab.industry.build.edges import extractRawMaterialEdges
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> edges = extractRawMaterialEdges(loadNodes())
        >>> precise = [e for e in edges if e.amount]
        >>> len(precise)
        642

    Guide:
        ``buildAllEdges`` 의 3 단계 — confidence 0.9, ``preciseEdgeCount`` 의 주요 소스.
        ``calcSupplyInsights`` 의 HHI 도 본 함수 산출 ``amount`` 가 있는 엣지만으로 계산.

    When:
        manifest 빌드 — 정밀 supplier 엣지 (amount/ratio 포함) 가 필요할 때만. 패턴/언급 추출은
        ``extractDocsEdges``.

    How:
        nodes 종목별 ``panel/{code}.parquet`` 의 "원재료" 섹션 → 최신 사업보고서 row → 마크다운
        테이블 추출 → "매입처" 헤더 매칭 → 행 단위 IndustryEdge 변환 (품목/매입액/비중/매입처
        정규화).

    Requires:
        - providers.dart.panel.text: panel 섹션 표 (`panelXmlTables`) + table_parser 헬퍼
        - reference: KindList (정규화된 회사명 매핑)

    See Also:
        - ``dartlab.industry.build.edges.extractDocsEdges`` : 비표 본문 패턴 보완
        - ``dartlab.industry.build.edges.buildAllEdges`` : 본 함수 호출 사용자
        - ``dartlab.industry.calcs.concentration.calcSupplyInsights`` : amount 우선 소비처

    AIContext:
        "주요 원재료 공급사", "매입처 비중" 류 답변 데이터. ``amount`` 와 ``ratio`` 보유한 엣지만
        강한 단정 가능 — ``preciseEdgeCount`` 적은 회사는 "일부 거래만 공시" 단서 명시.
    """
    # providers.dart.panel.text SSOT. panel contentRaw raw DART XML 표를
    # providers.dart.panel.text.panelXmlTables(lxml)가 markdown extractTables 와 동일 shape(표×행×셀)로 추출 —
    # 공급사명/매입액/비중 복원(드롭 0). period=None=전 기간(다운스트림 corp 명 dedup).
    from dartlab.providers.dart.panel.text import gridToRowDicts, panelXmlTables
    from dartlab.providers.dart.tableRows import (
        extractCorpNames,
        findTableByHeaders,
        normalizeCorpName,
        parseAmount,
        parsePercent,
    )

    edges: list[IndustryEdge] = []
    nodeIdx = _buildNodeIndex(nodes)
    c2n, n2c = _listingLookup()

    # 정규화된 회사명 → 종목코드 매핑 (㈜ 등 제거)
    n2cNorm = {normalizeCorpName(name): code for name, code in n2c.items() if len(name) >= 2}

    processed = 0
    matched = 0

    for code, node in nodeIdx.items():
        tables = panelXmlTables(code, sectionPattern="원재료")
        if not tables:
            continue

        processed += 1
        found = findTableByHeaders(tables, ["매입처"])
        if not found:
            continue

        table, hi = found
        # 격자전개(parsePanelXmlTables)가 rowspan 으로 부문 셀을 이미 forward-fill 하므로
        # 헤더행(hi)부터 슬라이스해 정렬된 row dict 로 변환 (옛 inheritColumns shift 휴리스틱 불요).
        rows = gridToRowDicts(table, headerRow=hi)

        buyerFacts: list[dict] = []  # 레버 A: 비상장 매입처 leaf fact (멱등 — 루프 후 할당)
        for r in rows:
            supplierCol = next((k for k in r.keys() if "매입처" in k), None)
            if not supplierCol:
                continue
            supplierText = r[supplierCol]
            if not supplierText:
                continue
            supNames = extractCorpNames(supplierText)
            if not supNames:
                continue

            # 부문 컬럼 헤더 변형 대응 (부문/사업부문/사업부분/구분) — 소계/총계 행 제외용
            bumunCol = next(
                (k for k in r.keys() if k.replace(" ", "") in ("부문", "사업부문", "사업부분", "구분")), None
            )
            bumun = (r.get(bumunCol, "") or "").strip() if bumunCol else ""
            if any(skip in bumun for skip in ["소 계", "소계", "총 계", "총계", "※"]):
                continue

            product = r.get("품 목", "").strip()
            # 퍼지 헤더 (레버 A) — 실제 헤더가 매입액/제NN기매입액·비율/비중/비울(오타)·병합셀로 천차만별.
            amountCol = next((k for k in r.keys() if "매입액" in k), None)
            ratioCol = next((k for k in r.keys() if ("비율" in k or "비중" in k) and "매입처" not in k), None)
            amount = parseAmount(r.get(amountCol, "") or "") if amountCol else None
            ratio = parsePercent(r.get(ratioCol, "") or "") if ratioCol else None
            # 합쳐진 셀 "138,272 (12.3%)" — 금액 컬럼에서 비율 보강
            if ratio is None and amountCol:
                ratio = parsePercent(r.get(amountCol, "") or "")

            for supName in supNames:
                # 정규화 매칭
                normName = normalizeCorpName(supName)
                supCode = n2c.get(supName) or n2cNorm.get(normName)
                if supCode and supCode != code:
                    # 상장 매입처 → 그래프 엣지 (현행)
                    matched += 1
                    edges.append(
                        IndustryEdge(
                            fromCode=supCode,
                            fromName=c2n.get(supCode, supName),
                            toCode=code,
                            toName=c2n.get(code, ""),
                            edgeType="supplier",
                            industry=node.industry,
                            confidence=0.9,  # 테이블 직접 매칭 — 높은 신뢰도
                            source="panel_table",
                            evidence=f"{bumun} {product}".strip(),
                            product=product,
                            amount=amount,
                            ratio=ratio,
                        )
                    )
                elif not supCode:
                    # 비상장 매입처 → 그래프 노드 미승격, buyer leaf fact로 보존 (레버 A).
                    # 정량값(amount/ratio) 있는 것만 — calcHHI 모수, name-only는 nodes.json 비대화만.
                    if (amount is not None and amount > 0) or ratio is not None:
                        buyerFacts.append({"supplier": supName, "amount": amount, "ratio": ratio})

        if buyerFacts:
            node.supplyFacts = buyerFacts  # 할당(멱등) — 재호출 시 누적 아닌 덮어쓰기

    logger.info("원재료 테이블 엣지: %d사 스캔, %d건 매칭", processed, matched)
    return edges


# ── 통합 ──


def buildAllEdges(nodes: list[IndustryNode], *, skipDocs: bool = False) -> list[IndustryEdge]:
    """network·panel 텍스트·원재료 테이블 3개 소스에서 엣지를 수집하여 통합한다.

    Capabilities:
        3 소스 (`extractNetworkEdges` / `extractDocsEdges` / `extractRawMaterialEdges`) 엣지를
        병합하고 (from, to, edgeType) 키로 중복 제거. 우선순위 panel_table > panel_text > network 적용.
        ``skipDocs`` 는 기존 호환 이름이며 panel 텍스트/테이블 패스를 생략한다.

    Parameters
    ----------
    nodes : list[IndustryNode]
        전체 노드 리스트.
    skipDocs : bool
        기존 호환 플래그. True이면 panel 기반 엣지(텍스트+테이블) 생략. 빠른 테스트용.

    Returns
    -------
    list[IndustryEdge]
        통합 엣지 리스트. from+to+type 기준 중복 제거.
        우선순위: panel_table > panel_text > network.

    Raises:
        없음 — 각 소스 추출 실패 시 warning + skip, 부분 결과 보존.

    Example:
        >>> from dartlab.industry.build.edges import buildAllEdges
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> edges = buildAllEdges(loadNodes())
        >>> len(edges)
        4820

    Guide:
        manifest 빌드 (`buildIndustryMap`) 의 단일 엣지 수집 진입점. 결과는 ``edges.json`` 으로
        직렬화. 동일 쌍의 panel_table 엣지가 panel_text/network 엣지를 덮어써 메타 풍부도 우선.

    When:
        ``buildIndustryMap`` 의 엣지 수집 단계. 일반 분석 흐름에서는 호출하지 않는다 — 전 종목
        panel 스캔 비용 때문.

    How:
        ``extractNetworkEdges`` (출자) → ``extractDocsEdges`` (panel 패턴) → ``extractRawMaterialEdges``
        (테이블) 순차 호출 → source 우선순위로 정렬 후 (from, to, edgeType) 중복 제거.

    Requires:
        - 3 소스 의존성 합집합: scan/network + panel + KindList reference
        - nodes 리스트 (primary 노드 기반)

    See Also:
        - ``dartlab.industry.build.edges.extractNetworkEdges`` : 1 단계 소스
        - ``dartlab.industry.build.edges.extractDocsEdges`` : 2 단계 소스
        - ``dartlab.industry.build.edges.extractRawMaterialEdges`` : 3 단계 소스
        - ``dartlab.industry.build.pipeline.buildIndustryMap`` : 본 함수 호출 사용자

    AIContext:
        산업지도 manifest 의 모든 회사 관계 (계열·매입·매출·원재료) 진입점. AI 답변에서 엣지
        ``source`` 가 panel_table 이면 강한 단정, network 면 "출자 관계", panel_text (텍스트 매칭) 면
        "보고서 언급" 단서 권장.
    """
    edges: list[IndustryEdge] = []

    # 1. scan/network
    try:
        networkEdges = extractNetworkEdges(nodes)
        edges.extend(networkEdges)
        logger.info("network 엣지: %d건", len(networkEdges))
    except Exception as e:
        logger.warning("network 엣지 실패: %s", e)

    # 2. panel text (텍스트 기반)
    if not skipDocs:
        try:
            docsEdges = extractDocsEdges(nodes)
            edges.extend(docsEdges)
            logger.info("panel 텍스트 엣지: %d건", len(docsEdges))
        except Exception as e:
            logger.warning("panel 텍스트 엣지 실패: %s", e)

        # 3. panel 원재료 테이블 (구조화 파싱)
        try:
            tableEdges = extractRawMaterialEdges(nodes)
            edges.extend(tableEdges)
            logger.info("원재료 테이블 엣지: %d건", len(tableEdges))
        except Exception as e:
            logger.warning("원재료 테이블 엣지 실패: %s", e)

    # 중복 제거 (from+to+type 기준, 테이블 우선)
    seen: set[tuple[str, str, str]] = set()
    unique: list[IndustryEdge] = []
    # source 우선순위: panel_table > panel_text > network
    priority = {"panel_table": 0, "panel_text": 1, "network": 2}
    edges.sort(key=lambda e: priority.get(e.source, 3))
    for e in edges:
        key = (e.fromCode, e.toCode, e.edgeType)
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique
