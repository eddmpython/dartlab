"""정성 서술 추출 단일 메커니즘 (SPINE 앵커 구동, L1.5 frame).

사업보고서의 정성 텍스트(사업개요·매출및수주·생산능력및가동률·원재료·위험·경영진단·연구개발 등)를
개념마다 파서를 늘리지 않고 **하나의 메커니즘**으로 뽑는다. 카탈로그(`core.extractionCatalog`)의
narrativeAnchor(chapterRoman, sectionLeaf 한글 키워드)를 들고 panel narrative leaf(disclosureKey null)
를 앵커로 선택한다. 파서는 하나, 카탈로그가 자란다.

DART `sectionTopic.py` 의 ~200 손regex 덕지덕지를 대체하는 정공 경로. 앵커는 최신 골격 기준 sectionLeaf
키워드라 era/회사 변형에 견고하다(정부 표준 서식). 본 모듈은 sectionTopic 을 건드리지 않는 additive 신설
(무회귀). sectionTopic 의 SPINE 앵커 수렴은 후속 이관.

**계층 (L1.5 frame)**: core(카탈로그)·providers(panel) 만 import. raw 생산 0, 앵커 선택 가공만.
소비자: story(보고서 서술 블록)·ai(정성 Q&A)·workbench(정성 조립). US(EDGAR)는 SEC Item 택소노미
구조라 별도 경로(concept.edgar Item), 본 모듈은 DART(kr) 서술 전담.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.extractionCatalog import getConcept, getExtractionConcepts


def extractNarrative(
    code: str,
    conceptId: str,
    *,
    marketNs: str = "kr",
    leafType: str | None = None,
) -> pl.DataFrame | None:
    """정성 개념의 서술 leaf 를 앵커로 추출한다 (단일 메커니즘).

    Args:
        code: 종목코드 (KR 6자리).
        conceptId: narrative 카테고리 conceptId (예 "narrative.salesOrder"). 그 개념의
            narrativeAnchor(chapterRoman, sectionLeaf 키워드)로 panel 서술 leaf 선택.
        marketNs: 시장 ("kr" 만 지원. US 는 SEC Item 구조라 별도 경로).
        leafType: None(기본, text+table 전부) / "text" / "table" 로 leaf 종류 필터.

    Returns:
        pl.DataFrame 또는 None. panel narrative 행(disclosureKey null) 중 sectionLeaf 가 앵커
        키워드를 포함하는 leaf (chapter · sectionLeaf · blockLeaf · leafType · period 컬럼 + 본문).
        미매칭·비narrative·비kr 은 None.

    Raises:
        없음. panel 부재·빈 결과는 None.

    Example:
        >>> import dartlab
        >>> df = dartlab.frame.narrative.extractNarrative("005930", "narrative.salesOrder")  # doctest: +SKIP

    Capabilities:
        - 개념마다 파서 신설 0. 카탈로그 앵커 하나로 사업보고서 정성 섹션 전수 추출.

    Guide:
        - "삼성전자 수주상황" -> extractNarrative("005930", "narrative.salesOrder").
        - "생산능력/가동률" -> extractNarrative(code, "narrative.productionCapacity").
        - 표만 -> leafType="table". 서술만 -> leafType="text".

    AIContext:
        정성 Q&A 의 raw 근거 layer. 본문은 외부 untrusted 라 ai 층이 [EXTERNAL CONTENT] 마커로 감쌈.

    Requires:
        - core.extractionCatalog(앵커), providers.dart.panel(서술 leaf). marketNs="kr".
    """
    if marketNs != "kr":
        return None
    concept = getConcept(conceptId)
    if concept is None or concept.category != "narrative" or concept.narrativeAnchor is None:
        return None
    _chapter, keyword = concept.narrativeAnchor

    from dartlab.providers.dart.panel import Panel

    p = Panel(code, marketNs=marketNs)
    if p is None or getattr(p, "height", 0) == 0:
        return None
    if "sectionLeaf" not in p.columns or "disclosureKey" not in p.columns:
        return None

    mask = pl.col("disclosureKey").is_null() & pl.col("sectionLeaf").fill_null("").str.contains(keyword, literal=True)
    if leafType is not None and "leafType" in p.columns:
        mask = mask & (pl.col("leafType") == leafType)
    out = p.filter(mask)
    return out if not out.is_empty() else None


def listNarrativeConcepts() -> list[dict]:
    """추출 가능한 정성 개념 목록(conceptId · label · anchor · edgarItem)을 반환한다.

    Returns:
        [{conceptId, label, chapter, keyword, edgar}] 리스트.

    Raises:
        없음.

    Example:
        >>> from dartlab.frame.narrative import listNarrativeConcepts
        >>> any(c["conceptId"] == "narrative.salesOrder" for c in listNarrativeConcepts())
        True
    """
    out: list[dict] = []
    for c in getExtractionConcepts(category="narrative"):
        anchor = c.narrativeAnchor or ("", "")
        edgar = None
        keys = getattr(c.edgar, "keys", None)
        if keys:
            edgar = keys[0]
        out.append(
            {
                "conceptId": c.conceptId,
                "label": c.label,
                "chapter": anchor[0],
                "keyword": anchor[1],
                "edgar": edgar,
            }
        )
    return out
