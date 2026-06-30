"""IPO 증권신고서(지분증권) 본문 → 6 카테고리 구조화 — dart4.xsd 네이티브 파서.

신규상장 IPO 의 증권신고서(지분증권)는 OpenDART 구조화 엔드포인트가 *없다* — dart4.xsd
원문(`<DOCUMENT>`/`<TITLE>`/`<TABLE>`) 만 존재한다. 따라서 ``gather/dart/dart.py`` 구조화
JSON API 에 흡수 불가. ``eventDisclosure`` 의 형제 위치(수시공시 파서)이되, 증권신고서는 *자유
서식 장문*(60 만~470 만 자, <TABLE> 1000+)이라 라벨 고정 1 엔트리로 끝나지 않는다. 대신 dart4.xsd
``<TITLE>`` *구조 앵커*로 6 섹션을 자른 뒤, 섹션별 표를 **내적 항등식**으로 자기검증한다.

설계 (개념확립 `tests/_attempts/ipo/`, 발행사 7 곳 교차 실측):
  ① classifyIpo — ``지분증권 subtype(첫 괄호) + corp_cls=="E" + stock_code==""`` 3 조건
     기계 ground-truth (사람 라벨 0). 2 조건만은 펀드·채권·유동화 대량 오분류.
  ② 섹션 앵커 — ``<TITLE>`` 텍스트로 6 섹션 경계 (텍스트변형 정규식 누적 X, 구조 위치). 발행사
     7 곳 100% 검출. ``[발행조건확정]`` 은 CORRECTION doc(단일 TITLE)이라 FULL 신고서만 대상.
  ③ 셀 추출 — 공통 ``dartXmlNormalize.normalizeDartXml`` (대문자→소문자 HTML·``<TE>/<TU>``
     dialect) → ``htmlTableParser.cellGrid`` (병합 보존). 공통 가드 ``"<table"`` 가 case-sensitive
     라 raw 대문자 ``<TABLE>`` 을 거르는 회귀를 normalizeDartXml 경유로 흡수.
  ④ 항등식 게이트 — 공모가×주식수≈모집총액 / ①순이익×②PER÷③주식수≈주당평가액 /
     주당평가액×(1−할인율)≈공모가밴드 / 자산=부채+자본 / Σ배정=모집주식수. 발행사 6/6 EXACT
     (오차<0.02%). 원문 콤마오타("1,7000,000"→17M)도 항등식이 잡아내고 복구한다.

전 상장사 횡단 소비는 :func:`dartlab.scan.ipo.scanIpo`. 본문 content_raw 는 PRIVATE.
"""

from __future__ import annotations

import re

from dartlab.providers.dart.parse.dartXmlNormalize import coerceCell, normalizeDartXml
from dartlab.providers.dart.parse.htmlTableParser import cellGrid

# 6 카테고리 → 섹션 시작 ``<TITLE>`` 정규식 (구조 앵커). 유통물량은 독립 TITLE 없음(공모방법 하위표),
# 비교기업 PER·평가가액·할인율은 '3.공모가격결정'(수요예측 절차뿐) 아니라 'IV.인수인의 의견'에 있다(실측).
IPO_SECTION_ANCHORS: dict[str, str] = {
    "offering": r"^1\.\s*공모개요",
    "method": r"^2\.\s*공모방법",
    "underwriterOpinion": r"인수인의\s*의견|분석기관의\s*평가의견",
    "financials": r"^1\.\s*요약재무정보",
    "riskSummary": r"^1\.\s*핵심투자위험",
    "riskDetail": r"III\.\s*투자위험요소",
}

_SUBTYPES = ("지분증권", "집합투자증권", "채무증권", "유동화증권", "투자계약증권", "파생결합증권")
_SCALE = {"조": 1e12, "억": 1e8, "백만": 1e6, "천만": 1e7, "만": 1e4}
_FIN_ROWS = {
    "자산총계": r"자산총계",
    "부채총계": r"부채총계",
    "자본총계": r"자본총계",
    "매출액": r"^매출액|^영업수익",
    "영업이익": r"^영업이익",
    "당기순이익": r"당기순이익|당기.?순.?이익",
}


# ═══════════════════════════════════════════
# 공개 — 판별
# ═══════════════════════════════════════════


def classifyIpo(reportNm: str, corpCls: str, stockCode: str, corpName: str) -> dict:
    """증권신고서 메타 → 신규상장 IPO 판별 (3 조건 기계 ground-truth, 사람 라벨 0).

    실측 정정(`tests/_attempts/ipo/`, 2026-06-29): ``corp_cls=="E" + stock_code==""`` 2 조건만은
    과대 — 6 개월 corp_cls=E 증권신고서 826 건 중 783 건이 펀드·채권·유동화. ``report_nm`` 첫
    괄호 subtype 이 ``"지분증권"`` 인 조건까지 세 조건 동시라야 진짜 주식 IPO 다. 지분증권 43 건
    전수에서 오분류 0.

    Args:
        reportNm: DART ``report_nm`` (예 ``"[기재정정]증권신고서(지분증권)"``).
        corpCls: 법인구분 (``"E"`` 기타 / ``"Y"`` 유가 / ``"K"`` 코스닥 / ``"N"`` 코넥스).
        stockCode: 종목코드 (상장 전 IPO 는 빈 문자열).
        corpName: 회사명 (스팩 식별용 — ``report_nm`` 아니라 회사명에 "기업인수목적/스팩").

    Returns:
        dict
            isIpo : bool — 신규상장 IPO(지분증권+E+빈 stock_code) 여부.
            subtype : str — 증권신고서 첫 괄호 종류 (지분증권/집합투자증권/채무증권/...).
            isSpac : bool — 기업인수목적(스팩) 여부 (corpName 매칭).
            kind : str — ``"prospectus"``(파싱 대상 본문) / ``"notice"``(효력발생안내·정정요구).
            verdict : str — 사람 가독 라벨.

    Raises:
        없음.

    Example:
        >>> classifyIpo("증권신고서(지분증권)", "E", "", "주식회사 기도산업")["isIpo"]
        True
        >>> classifyIpo("증권신고서(집합투자증권-신탁형)(...)", "E", "", "한국투자신탁운용")["isIpo"]
        False

    Capabilities:
        - 펀드·채권·유동화·조각투자(투자계약증권) 대량 오분류 차단 (첫 괄호 subtype 판정).
        - 상장사 유상증자/DR(corp_cls Y/K, stock_code 보유) 자동 비-IPO.
        - 스팩 별도 태그 + prospectus/notice 분리.

    Guide:
        - 전 상장사 횡단 발굴은 본 함수 직접 호출 말고 :func:`dartlab.scan.ipo.scanIpo` 사용.

    SeeAlso:
        - :func:`parseIpoProspectus` — IPO 통과분 본문 6 카테고리 파싱.
        - :func:`dartlab.scan.ipo.scanIpo` — 전수 횡단 발굴.

    Requires:
        - DART ``listFilings`` 또는 ``allFilings`` 의 메타 컬럼 (report_nm/corp_cls/stock_code/corp_name).

    AIContext:
        Agent 가 "이번달 신규 IPO" / "청약 임박 종목" 류 질문 시 후보 게이트로 사용. 사후공시
        (수요예측 결과·확정공모가)는 별 트랙 — 본 판별은 사전 신고서 한정.

    LLM Specifications:
        AntiPatterns:
            - ``corp_cls=="E" + stock_code==""`` 2 조건만으로 IPO 판정 (펀드/채권 대량 누수).
            - subtype 을 단순 substring 으로 판정 (펀드명 속 "(지분증권)" 오매칭).
            - 스팩을 report_nm 으로 식별 (report_nm 은 "증권신고서(지분증권)" 뿐 — corpName 봐야).
        OutputSchema:
            - dict: isIpo(bool) / subtype(str) / isSpac(bool) / kind(str) / verdict(str).
        Prerequisites:
            - 증권신고서 메타 4 필드.
        Freshness:
            - 공시 접수 시점 (사전 신고서).
        Dataflow:
            - listFilings → classifyIpo → IPO 통과분 rcept → parseIpoProspectus.
        TargetMarkets:
            - KR (DART 발행공시).
    """
    subtype = _subtype(reportNm)
    sc = (stockCode or "").strip()
    isSpac = ("스팩" in corpName) or ("기업인수목적" in corpName)
    kind = "notice" if (reportNm.startswith("효력발생안내") or "정정신고서제출요구" in reportNm) else "prospectus"
    isIpo = subtype == "지분증권" and corpCls == "E" and sc == ""
    if isIpo:
        verdict = f"IPO({'스팩' if isSpac else '일반'})/{kind}"
    elif subtype == "지분증권" and corpCls in ("Y", "K"):
        verdict = "비-IPO(상장사 유상증자)"
    else:
        verdict = f"비-IPO({subtype})"
    return {"isIpo": isIpo, "subtype": subtype, "isSpac": isSpac, "kind": kind, "verdict": verdict}


# ═══════════════════════════════════════════
# 공개 — 본문 파싱
# ═══════════════════════════════════════════


def parseIpoProspectus(content: str) -> dict:
    """IPO 증권신고서(지분증권) 본문 → 6 카테고리 구조화 + 내적 항등식 검증.

    dart4.xsd ``<TITLE>`` 으로 6 섹션을 자르고(발행사 7 곳 100% 검출), 섹션별 표를
    ``normalizeDartXml→cellGrid`` 로 추출한 뒤 카테고리별 항등식으로 자기검증한다. 항등식이
    원문 콤마오타("1,7000,000"→17M)를 검출하고 복구(주식수=총액/가액)까지 한다.

    Args:
        content: 증권신고서 본문 dart4.xsd 원문 (``allFilings`` content_raw 또는
            ``Company.readFiling(rcept)["text"]``). ``[발행조건확정]`` CORRECTION doc 은
            6 섹션이 없으므로 FULL 신고서(초판·[기재정정])를 넣어야 한다.

    Returns:
        dict — 6 카테고리 + 항등식 + 섹션 커버리지. 미검출 카테고리는 빈 dict.
            offering : dict — priceBand(low,high)·offerTotal·shares(복구)·subscription·payDate.
            valuation : dict — model·netIncome·peerMultiple·perShareValue·discount·band·peers.
            financials : dict — periods·rows(자산총계/매출액/당기순이익 등 × 기간).
            allocation : dict — byTarget(우리사주/일반공모 주식수)·total.
            float : dict — freeFloatShares·freeFloatPct(상장후 유통가능)·lockedShares(매각제한)·
                postOfferingShares·lockups[{holder,shares,period}](주주별 보호예수 일정).
            multiples : dict — marketCap(low,high)·per·psr·pbr(공모가밴드 기준 IPO 자체 멀티플,
                비교기업 멀티플 대비 좌표)·annualPeriod·isLoss(적자 리스크 태그).
            risk : dict — sections(사업/회사/기타위험)·count.
            identities : dict — 각 카테고리 항등식 통과 여부 (truth proxy).
            sections : list[str] — 검출된 섹션 앵커 키 (커버리지).

    Raises:
        없음 — 미검출·파싱 실패는 빈 dict 로 흡수 (never-raise).

    Example:
        >>> # html = Company("...").readFiling(rcept)["text"]  # doctest: +SKIP
        >>> # r = parseIpoProspectus(html)  # doctest: +SKIP
        >>> # r["valuation"]["peerMultiple"], r["identities"]["valuationChain"]  # doctest: +SKIP

    Capabilities:
        - 공모개요(공모가밴드·청약일)·밸류(적용 PER·평가가액·할인율)·재무3개년·배정·리스크 추출.
        - 상장후 유통가능물량·보호예수(매각제한) 워터폴 + 주주별 보호예수 일정.
        - 공모가밴드 기준 IPO 자체 implied PER/PBR/PSR (비교기업 멀티플 대비 고저평가 좌표·적자 태그).
        - 카테고리별 내적 항등식으로 오추출·원문오타 검출 및 복구 (truth proxy).

    Guide:
        - ``[발행조건확정]`` 은 CORRECTION doc(6 섹션 없음) → FULL 신고서를 넣을 것
          (:func:`classifyIpo` 의 ``kind`` 와 report_nm prefix 로 구분).
        - 전 상장사 횡단은 :func:`dartlab.scan.ipo.scanIpo`.

    SeeAlso:
        - :func:`classifyIpo` — IPO 판별 (파싱 전 게이트).
        - :func:`dartlab.providers.dart.eventDisclosure.parseEventDisclosure` — 수시공시 형제 파서.
        - :func:`dartlab.providers.dart.parse.dartXmlNormalize.normalizeDartXml` — 셀 정규화 SSOT.

    Requires:
        - ``normalizeDartXml`` · ``cellGrid`` · ``coerceCell`` (dart4.xsd 셀 추출).
        - 본문 content_raw (allFilings 또는 readFiling).

    AIContext:
        Agent 가 특정 IPO 의 공모 조건·밸류에이션을 물을 때 사용. 발행사가 적용한 PER 배수·
        할인율을 좌표화해 "고저평가 단정" 대신 비교군 위치를 제시한다(투자판단 단정 회피).

    LLM Specifications:
        AntiPatterns:
            - ``[발행조건확정]`` CORRECTION doc 을 넣고 6 섹션 기대 (단일 TITLE — 빈 결과).
            - 평문 get_text 정규식으로 숫자 추출 (전부 실패 — ``<TABLE>`` 구조 파싱 강제).
            - ``identities`` False 인 값을 신뢰 (항등식 위반 = 오추출 의심).
        OutputSchema:
            - dict: offering / valuation / financials / allocation / float / risk / identities / sections.
        Prerequisites:
            - FULL 증권신고서(지분증권) dart4.xsd 본문.
        Freshness:
            - 공시 접수 시점.
        Dataflow:
            - content_raw → 섹션 슬라이스 → 카테고리 파서 → 항등식 검증 → dict.
        TargetMarkets:
            - KR (DART 증권신고서 지분증권).
    """
    sections = _sliceSections(content)
    offering = _parseOffering(sections)
    valuation = _parseValuation(sections)
    financials = _parseFinancials(sections)
    allocation = _parseAllocation(sections)
    floatData = _parseFloat(content)
    multiples = _impliedMultiples(offering, financials, floatData)
    risk = _parseRisk(content)
    identities = _verifyIdentities(offering, valuation, financials, allocation, floatData)
    return {
        "offering": offering,
        "valuation": valuation,
        "financials": financials,
        "allocation": allocation,
        "float": floatData,
        "multiples": multiples,
        "risk": risk,
        "identities": identities,
        "sections": sorted(sections.keys()),
    }


# ═══════════════════════════════════════════
# 내부 — 섹션 앵커 / 셀 추출
# ═══════════════════════════════════════════


def _subtype(reportNm: str) -> str:
    """증권신고서 직후 *첫 괄호* = 정본 subtype (펀드명 속 '(지분증권)' 오매칭 차단)."""
    m = re.search(r"증권신고서\(([^)]+)\)", reportNm)
    if not m:
        return "기타"
    inner = m.group(1)
    for s in _SUBTYPES:
        if s[:4] in inner:
            return s
    return inner


def _titlePositions(content: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"<TITLE[^>]*>(.*?)</TITLE>", content, re.S):
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1)).strip())
        if txt:
            out.append((m.start(), txt))
    return out


def _sliceSections(content: str) -> dict[str, str]:
    """6 카테고리 섹션 텍스트 슬라이스 — ``<TITLE>`` 시작점 ~ 다음 TITLE."""
    titles = _titlePositions(content)
    out: dict[str, str] = {}
    for cat, pat in IPO_SECTION_ANCHORS.items():
        for i, (pos, t) in enumerate(titles):
            if re.search(pat, t):
                end = titles[i + 1][0] if i + 1 < len(titles) else len(content)
                out[cat] = content[pos:end]
                break
    return out


def _tableGrids(sectionXml: str) -> list[list[list[str]]]:
    """섹션 내 모든 ``<TABLE>`` → normalizeDartXml(SSOT) → 병합보존 grid(텍스트)."""
    grids: list[list[list[str]]] = []
    for block in re.findall(r"<TABLE.*?</TABLE>", sectionXml, re.S):
        grid = cellGrid(normalizeDartXml(block))
        if grid:
            grids.append([[c.text if c else "" for c in row] for row in grid])
    return grids


def _ws(s: str) -> str:
    return re.sub(r"\s", "", s or "")


def _num(s: str) -> float | None:
    v = coerceCell(s)
    return float(v) if isinstance(v, (int, float)) else None


def _numIn(s: str) -> float | None:
    m = re.search(r"([\d,]+(?:\.\d+)?)", s or "")
    return float(m.group(1).replace(",", "")) if m else None


def _numU(s: str) -> float | None:
    s = (s or "").strip()
    if "~" in s:
        return None
    return _num(re.sub(r"[주원%\s]", "", s))


def _mult(s: str) -> float | None:
    m = re.search(r"([\d,]+\.?\d*)\s*배", s or "")
    return float(m.group(1).replace(",", "")) if m else None


def _pctRange(s: str) -> tuple[float, float] | None:
    nums = [float(x) for x in re.findall(r"([\d.]+)\s*%", s or "")]
    return (nums[0], nums[-1]) if nums else None


def _priceRange(s: str) -> tuple[float, float] | None:
    nums = [int(x.replace(",", "")) for x in re.findall(r"([\d,]{4,})\s*원", s or "")]
    return (float(min(nums)), float(max(nums))) if nums else None


def _cleanDate(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\n", "")).strip()


def _findRowValue(grids: list[list[list[str]]], headerPat: str) -> str | None:
    """header 셀 매칭 → 같은 컬럼 다음 행 값 (헤더행/값행 세로 표). 공백 정규화."""
    for grid in grids:
        for ri, row in enumerate(grid):
            for ci, cell in enumerate(row):
                if re.search(headerPat, _ws(cell)) and ri + 1 < len(grid) and ci < len(grid[ri + 1]):
                    return grid[ri + 1][ci]
    return None


# ═══════════════════════════════════════════
# 내부 — 카테고리 파서
# ═══════════════════════════════════════════


def _parseOffering(sections: dict[str, str]) -> dict:
    """카테고리1·2 — 공모가밴드·모집총액·청약/납입일."""
    sec = sections.get("offering", "")
    grids = _tableGrids(sec)
    out: dict[str, object] = {}
    price = _findRowValue(grids, r"모집.?매출.?가액")
    total = _findRowValue(grids, r"모집.?매출.?총액")
    qty = _findRowValue(grids, r"증권수량|모집.?매출.?수량")
    out["priceConfirmed"] = _num(price) if price else None
    out["offerTotal"] = _num(total) if total else None
    out["sharesRaw"] = _num(qty) if qty else None
    band = re.search(r"([\d,]{4,})\s*원\s*~\s*([\d,]{4,})\s*원", sec)
    if band:
        out["priceBand"] = (_num(band.group(1)), _num(band.group(2)))
    sub = _findRowValue(grids, r"청약기일")
    if sub:
        out["subscription"] = _cleanDate(sub)
    pay = _findRowValue(grids, r"납입기일")
    if pay:
        out["payDate"] = _cleanDate(pay)
    return out


def _valCell(row: list[str]) -> str:
    body = row[1:-1] if len(row) > 2 else row
    for c in reversed(body):
        if re.search(r"\d", c):
            return c
    return ""


def _scaleOf(row: list[str]) -> float:
    j = " ".join(row)
    for tok, mul in _SCALE.items():
        if tok + "원" in j:
            return mul
    return 1.0


def _parseValuation(sections: dict[str, str]) -> dict:
    """카테고리3 — 인수인 의견의 상대가치 평가 체인(모형·①순이익·②PER·③주식수·평가액·할인율·밴드)."""
    grids = _tableGrids(sections.get("underwriterOpinion", ""))
    summary = next(
        (
            g
            for g in grids
            if "평가방법" in "".join(_ws(c) for r in g[:3] for c in r)
            and "평가모형" in "".join(_ws(c) for r in g[:3] for c in r)
        ),
        None,
    )
    out: dict[str, object] = {}
    if summary is None:
        return out
    out["model"] = (summary[1][1] if len(summary) > 1 and len(summary[1]) > 1 else "").strip()
    for row in summary:
        if len(row) < 2:
            continue
        marker = _ws(row[1])
        wstxt = _ws(" ".join(row))
        val = _valCell(row)
        if marker == "①":
            n = _numIn(val)
            out["netIncome"] = n * _scaleOf(row) if n is not None else None
        elif marker == "②":
            out["peerMultiple"] = _mult(val) or _numIn(val)
        elif marker == "③":
            out["shares"] = _numIn(val)
        elif "주당평가" in wstxt and "할인" not in wstxt:
            n = _numIn(val)
            out["perShareValue"] = n * _scaleOf(row) if n is not None else None
        elif "할인율" in wstxt:
            out["discount"] = _pctRange(val)
        elif "공모가산정" in wstxt or "희망공모가" in wstxt or "공모가액밴드" in wstxt:
            out["band"] = _priceRange(val)
    out["peers"] = _parsePeers(grids)
    return out


def _parsePeers(grids: list[list[list[str]]]) -> list[str]:
    for g in grids:
        flat = " ".join(c for r in g for c in r)
        if "최종 비교기업" in flat or "최종비교기업" in _ws(flat):
            for r in g:
                for c in r:
                    if c.count(",") < 1 or len(c) > 80:
                        continue
                    parts = [p.strip() for p in re.split(r"[,、]", c) if p.strip()]
                    if len(parts) >= 2 and all(len(p) <= 12 and not p.endswith(("다", "함", "음")) for p in parts):
                        return parts[:8]
    return []


_FIN_UNITS = {"백만원": 1e6, "천원": 1e3, "억원": 1e8, "원": 1.0}


def _financialsUnit(sec: str) -> float:
    """요약재무정보 '단위: 백만원/천원/원' 캡션 → 원 환산 배수. 미검출 시 1.0(원)."""
    m = re.search(r"단위\s*[:：]?\s*([가-힣]*원)", sec)
    return _FIN_UNITS.get(m.group(1), 1.0) if m else 1.0


def _parseFinancials(sections: dict[str, str]) -> dict:
    """카테고리5 — 요약재무정보 3 개년(+분기) 격자에서 핵심 라인 + 단위 추출."""
    sec = sections.get("financials", "")
    grids = _tableGrids(sec)
    main = max(grids, key=lambda g: len(g) * (max((len(r) for r in g), default=0)), default=None)
    out: dict[str, object] = {"unit": _financialsUnit(sec)}
    if not main:
        return out
    out["periods"] = [h for h in (main[0][1:] if main else []) if h]
    rows: dict[str, list] = {}
    for label, pat in _FIN_ROWS.items():
        for row in main:
            if row and re.search(pat, _ws(row[0])):
                rows[label] = [_num(c) for c in row[1:]]
                break
    out["rows"] = rows
    return out


def _impliedMultiples(offering: dict, financials: dict, floatData: dict) -> dict:
    """공모가밴드 × 상장후주식수 = 시가총액 → IPO 자체 implied PER/PBR/PSR (비교기업 멀티플 대비 좌표).

    연간 컬럼(periods 중 '분기' 아닌 최근 연도)의 당기순이익·매출액 + 최근 자본총계(가장 최신 컬럼).
    적자(연간순이익≤0)면 per=None(PER 무의미·리스크). 재무 단위(원/백만원) 환산 후 계산.
    """
    band = offering.get("priceBand")
    shares = floatData.get("postOfferingShares")
    rows = financials.get("rows", {})
    periods = financials.get("periods", [])
    unit = financials.get("unit", 1.0)
    if not band or not shares or not periods or not rows:
        return {}
    lo, hi = float(min(band)), float(max(band))
    mcapLo, mcapHi = lo * shares, hi * shares
    out: dict[str, object] = {"marketCap": (mcapLo, mcapHi)}
    # 연간 컬럼만 — 'YYYY년' 이되 '월'(월말 interim)·'분기' 제외(레몬 '제10기(2026년3월말)' 류 오선택 차단).
    annualIdx = next(
        (i for i, p in enumerate(periods) if re.search(r"\d{4}\s*년", p) and "월" not in p and "분기" not in p),
        None,
    )
    if annualIdx is None:
        return out  # 깨끗한 연간 컬럼 없으면 멀티플 미산정 — 부정확값 방출 대신 marketCap 만 반환

    def _at(label: str, idx: int) -> float | None:
        vals = rows.get(label)
        v = vals[idx] if vals and idx < len(vals) else None
        return v * unit if v is not None else None

    netIncome = _at("당기순이익", annualIdx)
    revenue = _at("매출액", annualIdx)
    equity = _at("자본총계", 0)  # 자본총계는 시점값 — 가장 최신 컬럼
    out["annualPeriod"] = periods[annualIdx]
    if netIncome is not None:
        out["isLoss"] = netIncome <= 0  # 적자 리스크 태그 (None=미검출이라 미표기)
    if netIncome and netIncome > 0:
        out["per"] = (round(mcapLo / netIncome, 2), round(mcapHi / netIncome, 2))
    if revenue and revenue > 0:
        out["psr"] = (round(mcapLo / revenue, 2), round(mcapHi / revenue, 2))
    if equity and equity > 0:
        out["pbr"] = (round(mcapLo / equity, 2), round(mcapHi / equity, 2))
    return out


def _parseAllocation(sections: dict[str, str]) -> dict:
    """카테고리4 (1 차) — 공모 배정표 주식수. 상장후 유통/보호예수 워터폴은 별 하위표(미구현)."""
    grids = _tableGrids(sections.get("method", ""))
    out: dict[str, object] = {}
    for g in grids:
        if not g:
            continue
        head = "".join(_ws(c) for c in g[0])
        if "공모대상" in head and "주식수" in head and "배정비율" in head:
            alloc = {}
            for row in g[1:]:
                label = (row[0] or "").strip()
                if len(row) >= 2 and label and not label.startswith("주") and not re.match(r"합\s*계$", label):
                    alloc[label] = _numU(row[1])
            out["byTarget"] = alloc
            out["total"] = sum(v for v in alloc.values() if v)
            break
    return out


def _colLabels(rows: list[list[str]], headN: int = 3) -> dict[int, str]:
    """헤더 상위 headN 행을 컬럼별로 합쳐 라벨 — 병합셀 중복 제거(워터폴 다단 헤더 컬럼 식별)."""
    ncol = max((len(r) for r in rows), default=0)
    labels: dict[int, str] = {}
    for j in range(ncol):
        seen: set[str] = set()
        parts: list[str] = []
        for r in rows[:headN]:
            v = _ws(r[j]) if j < len(r) else ""
            if v and v not in seen:
                seen.add(v)
                parts.append(v)
        labels[j] = "".join(parts)
    return labels


def _findCol(labels: dict[int, str], must: list[str], without: tuple[str, ...] = ()) -> int | None:
    for j, lab in labels.items():
        if all(k in lab for k in must) and not any(b in lab for b in without):
            return j
    return None


def _parseFloat(content: str) -> dict:
    """카테고리4 (2 차) — 상장후 유통가능물량 + 보호예수(매각제한·의무보유) 워터폴.

    독립 TITLE 없이 'III.투자위험요소 → 기타위험'의 다단 헤더 표(유통가능물량+매각제한물량)로 산다.
    보호예수는 신규정 용어 '의무보유/매각제한'(구 '보호예수')으로 표기. 헤더 3 행을 컬럼별로 합쳐
    컬럼을 식별(발행사별 열수 변동 흡수)하고 합계행에서 추출, 주주별 보호예수 일정 동반.
    항등식: 매각제한물량 + 유통가능물량 = 공모후 총발행주식수 (발행사 6 곳 EXACT).
    """
    out: dict[str, object] = {}
    for tm in re.finditer(r"<TABLE.*?</TABLE>", content, re.S):
        tbl = tm.group(0)
        flat = _ws(re.sub(r"<[^>]+>", " ", tbl))
        if "유통가능물량" not in flat or "매각제한물량" not in flat:
            continue
        grid = cellGrid(normalizeDartXml(tbl))
        if not grid:
            continue
        rows = [[(c.text if c else "") for c in row] for row in grid]
        labels = _colLabels(rows)
        freeShareCol = _findCol(labels, ["유통가능물량", "주식수"])
        freePctCol = _findCol(labels, ["유통가능물량", "지분율"])
        lockShareCol = _findCol(labels, ["매각제한물량", "주식수"])
        postShareCol = _findCol(labels, ["공모후", "주식수"])
        periodCol = _findCol(labels, ["매각제한기간"])
        if freeShareCol is None or lockShareCol is None:
            continue
        total = next((r for r in rows if re.match(r"합\s*계", (r[0] or "").strip())), None)
        if total:
            out["lockedShares"] = _numIn(total[lockShareCol]) if lockShareCol < len(total) else None
            out["freeFloatShares"] = _numIn(total[freeShareCol]) if freeShareCol < len(total) else None
            if postShareCol is not None and postShareCol < len(total):
                out["postOfferingShares"] = _numIn(total[postShareCol])
            if freePctCol is not None and freePctCol < len(total):
                out["freeFloatPct"] = _numIn(total[freePctCol])
        lockups: list[dict] = []
        if periodCol is not None:
            for r in rows[3:]:
                if periodCol < len(r) and re.search(r"\d+\s*개월|\d+\s*년", r[periodCol] or ""):
                    lockups.append(
                        {
                            "holder": (r[1] or "").strip() if len(r) > 1 else "",
                            "shares": _numIn(r[lockShareCol]) if lockShareCol < len(r) else None,
                            "period": re.sub(r"\s+", " ", (r[periodCol] or "").strip()),
                        }
                    )
        out["lockups"] = lockups
        return out
    return out


def _parseRisk(content: str) -> dict:
    """카테고리6 — 투자위험요소 하위 위험 섹션(사업/회사/기타) 수."""
    risk = [t for _, t in _titlePositions(content) if re.search(r"위험", t)]
    return {"sections": risk, "count": len(risk)}


# ═══════════════════════════════════════════
# 내부 — 항등식 검증 (truth proxy)
# ═══════════════════════════════════════════


def _verifyIdentities(offering: dict, valuation: dict, financials: dict, allocation: dict, floatData: dict) -> dict:
    """카테고리별 내적 항등식 → 추출 신뢰도 (truth proxy). 위반 시 복구값 동반."""
    out: dict[str, object] = {}

    # 공모: 공모가(최저) × 주식수 ≈ 모집총액. 불일치 시 주식수 복구.
    band = offering.get("priceBand")
    price = offering.get("priceConfirmed") or (band[0] if band else None)
    total = offering.get("offerTotal")
    if price and total:
        recovered = round(total / price)
        out["sharesRecovered"] = recovered
        raw = offering.get("sharesRaw")
        if raw:
            out["offeringRawQtyOk"] = abs(raw * price - total) / total < 0.01
        if band and band[1]:
            out["offerTotalAtHigh"] = round(band[1] * recovered)

    # 밸류: ①×②÷③ ≈ 주당평가액 ; 평가액×(1−할인율) ≈ 공모가밴드.
    ni, per, sh, psv = (valuation.get(k) for k in ("netIncome", "peerMultiple", "shares", "perShareValue"))
    if ni and per and sh and psv:
        out["valuationChain"] = abs(ni * per / sh - psv) / psv < 0.02
    disc, vband = valuation.get("discount"), valuation.get("band")
    if psv and disc and vband:
        calcLo, calcHi = psv * (1 - max(disc) / 100), psv * (1 - min(disc) / 100)
        bLo, bHi = min(vband), max(vband)
        out["valuationBand"] = abs(calcLo - bLo) / bLo < 0.02 and abs(calcHi - bHi) / bHi < 0.02

    # 재무: 자산총계 = 부채총계 + 자본총계 (최근 기간).
    rows = financials.get("rows", {})
    asset = (rows.get("자산총계") or [None])[0]
    liab = (rows.get("부채총계") or [None])[0]
    equity = (rows.get("자본총계") or [None])[0]
    if asset and liab and equity:
        out["financialsBalance"] = abs(asset - (liab + equity)) / asset < 0.01

    # 배정: Σ배정 ≈ 모집주식수(복구).
    allocTotal = allocation.get("total")
    recovered = out.get("sharesRecovered")
    if allocTotal and recovered:
        out["allocationSum"] = abs(allocTotal - recovered) / recovered < 0.01

    # 유통: 매각제한물량 + 유통가능물량 ≈ 공모후 총발행주식수.
    locked, free, post = (
        floatData.get("lockedShares"),
        floatData.get("freeFloatShares"),
        floatData.get("postOfferingShares"),
    )
    if locked and free and post:
        out["floatBalance"] = abs((locked + free) - post) / post < 0.001

    return out


__all__ = ["IPO_SECTION_ANCHORS", "classifyIpo", "parseIpoProspectus"]
