"""DEF 14A proxy HTML 거버넌스 3표 파서. 감사보수·임원보수(SCT)·실질지분(Beneficial Ownership).

US 는 per-person 임원보수·per-holder 지분·감사보수를 XBRL 집계 API 로 주지 않고 proxy(DEF 14A) HTML
표로만 공시한다(SEC Reg S-K 로 구조 수렴). 본 모듈은 proxy HTML 문자열을 받아 3표를 추출하는 순수
파서다(네트워크 0). 개념·적중률은 ``tests/_attempts/proxyGovernance`` 실측: 20사 스윕 auditFees 85%,
SCT 75%, ownership 80%. 미스는 표 자체가 없는 문서(폐쇄형펀드·특별총회 proxy)에 집중, 패널 자연 미표시.

파싱 전략: 전 <table> 을 grid(colspan 전개)로 편 뒤 합성헤더(다행 분할 병합) 시그니처로 분류.
  - auditFees: 행 라벨 'Audit/Audit-Related/Tax/All Other Fees' + 헤더 연도 컬럼. 'in thousands' 단위 감지.
  - SCT: 헤더 salary+total. 연도는 행 전체에서 '20NN' 단독 셀(위치 가변), total 은 행 마지막 금액.
  - ownership: 헤더 beneficial + percent 명명 컬럼 지정 추출(나이·주식수 오인 차단).

scan 빌더(``scan/builders/edgar/report/proxyBuild``)가 lazy import 로 소비한다(L1 provider, 상향 import 0).
"""

from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# SCT 이름 셀에서 직함 분리("Tim Cook Chief Executive Officer"). 첫 직함 키워드 앞=이름.
_TITLE_RE = re.compile(
    r"\b(Chairman|Chief|President|Senior|Executive|General|Former|Principal|Vice|Interim|Global|Group)\b"
)


def tableGrid(table) -> list[list[str]]:
    """bs4 <table> 을 2차원 텍스트 grid 로 편다(colspan 전개·공백 정규화).

    Args:
        table: BeautifulSoup ``<table>`` 태그.

    Returns:
        list[list[str]]: 행×셀 텍스트. 빈 행 제외.

    Raises:
        없음.

    Example:
        >>> soup = BeautifulSoup("<table><tr><td colspan=2>a</td></tr></table>", "lxml")
        >>> tableGrid(soup.table)
        [['a', 'a']]
    """
    grid: list[list[str]] = []
    for tr in table.find_all("tr"):
        row: list[str] = []
        for cell in tr.find_all(["td", "th"]):
            txt = re.sub(r"\s+", " ", cell.get_text(" ", strip=True))
            try:
                span = max(1, int(cell.get("colspan", 1)))
            except (ValueError, TypeError):
                span = 1
            row.extend([txt] * span)
        if row:
            grid.append(row)
    return grid


def moneyToFloat(s: str) -> float | None:
    """'$1,234,567' 류 금액 문자열을 float 로. 금액 아님/0 이하는 None.

    Args:
        s: 셀 텍스트.

    Returns:
        float | None: 파싱 값(>0) 또는 None.

    Raises:
        없음.

    Example:
        >>> moneyToFloat("$24,703")
        24703.0
    """
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)", s or "")
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
        return v if v > 0 else None
    except ValueError:
        return None


def gridsFromHtml(html: str) -> list[list[list[str]]]:
    """HTML 전체를 1회 파싱해 전 <table> grid 목록으로. 3표 파서가 공유(3배 재파싱 방지).

    Args:
        html: proxy 전체 HTML.

    Returns:
        list: tableGrid 결과 목록(빈 grid 제외).

    Raises:
        없음.

    Example:
        >>> grids = gridsFromHtml("<table><tr><td>x</td></tr></table>")
        >>> len(grids)
        1
    """
    soup = BeautifulSoup(html, "lxml")
    return [g for g in (tableGrid(t) for t in soup.find_all("table")) if g]


def _mergedHead(g: list[list[str]], depth: int = 4) -> tuple[list[str], int]:
    """상위 depth 행을 컬럼별 이어붙인 합성 헤더(소문자) + 본문 시작 인덱스. 다행 분할 헤더 대응."""
    n = max((len(r) for r in g[:depth]), default=0)
    merged = ["" for _ in range(n)]
    bodyStart = 0
    for i, r in enumerate(g[:depth]):
        joined = " ".join(r).lower()
        if i > 0 and re.search(r"\$|\d{3,}", joined) and not re.search(r"salary|total|percent|shares|name", joined):
            break
        for j, c in enumerate(r):
            if c:
                merged[j] = (merged[j] + " " + c).strip()
        bodyStart = i + 1
    return [m.lower() for m in merged], bodyStart


def parseAuditFees(html: str | BeautifulSoup) -> list[dict]:
    """proxy HTML 에서 감사보수 표를 찾아 연도별 fee 행을 뽑는다.

    행 라벨 'Audit Fees/Audit-Related Fees/Tax Fees/All Other Fees' 시그니처. 헤더의 연도(20NN)
    컬럼 순서대로 금액을 매핑. 표/직전 문맥에 'in thousands' 마커가 있으면 1000 배 보정.

    Args:
        html: DEF 14A 전체 HTML 또는 사전 파싱 BeautifulSoup(1회 파싱 공유).

    Returns:
        list[dict]: ``{year(str), auditFee, auditRelatedFee, taxFee, otherFee}`` (USD). 표 부재 시 [].

    Raises:
        없음.

    Example:
        >>> rows = parseAuditFees(proxyHtml)  # doctest: +SKIP
        >>> rows[0]["auditFee"]  # AAPL 2025
        24703000.0
    """
    soup = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        g = tableGrid(table)
        if not g:
            continue
        labels = [r[0] for r in g if r]
        if not any(re.match(r"(?i)^audit fees?\b", x or "") for x in labels):
            continue
        head, _ = _mergedHead(g)
        years = []
        for c in head:
            m = re.search(r"\b(20\d\d)\b", c)
            if m and m.group(1) not in years:
                years.append(m.group(1))
        if not years:  # 헤더 연도 부재 시 표 텍스트에서 좌→우 순 추출
            m = re.findall(r"\b(20\d\d)\b", " ".join(head) + " " + " ".join(g[0]))
            years = list(dict.fromkeys(m))
        # 단위: 표 자신 + 직전 형제 텍스트에서 thousands 마커
        ctx = table.get_text(" ", strip=True)[:400]
        prev = table.find_previous(string=re.compile(r"(?i)in thousands|\(\s*\$?\s*000"))
        mult = 1000.0 if (re.search(r"(?i)in thousands|\(\s*\$?\s*000", ctx) or prev) else 1.0
        # 구체 라벨 우선(Audit-Related 가 'audit' startswith 에 먼저 걸려 auditFee 를 덮는 버그 방지)
        fieldOf = [
            ("audit-related", "auditRelatedFee"),
            ("audit related", "auditRelatedFee"),
            ("all other", "otherFee"),
            ("tax", "taxFee"),
            ("audit", "auditFee"),
        ]
        byYear: dict[str, dict] = {}
        for r in g:
            if not r:
                continue
            lab = (r[0] or "").lower()
            key = next((v for k, v in fieldOf if lab.startswith(k)), None)
            if not key:
                continue
            amts = [a for a in (moneyToFloat(c) for c in r[1:]) if a is not None]
            # 같은 값 colspan 중복 제거(인접 동일값 collapse)
            dedup: list[float] = []
            for a in amts:
                if not dedup or dedup[-1] != a:
                    dedup.append(a)
            for i, a in enumerate(dedup[: len(years) or 3]):
                # 연도 미검출 표는 emit 하지 않는다(옛 str(i) fallback 이 year='1' 쓰레기 행 생성).
                yr = years[i] if i < len(years) else (str(int(years[0]) - i) if years else None)
                if yr is None or not (1990 <= int(yr) <= 2035):
                    continue
                byYear.setdefault(yr, {"year": yr})[key] = a * mult
        out = [
            {**{"auditFee": None, "auditRelatedFee": None, "taxFee": None, "otherFee": None}, **v}
            for v in byYear.values()
            if v.get("auditFee")
        ]
        if out:
            return sorted(out, key=lambda x: x["year"])
    return []


def parseSummaryComp(html: str | BeautifulSoup) -> list[dict]:
    """proxy HTML 의 Summary Compensation Table 에서 인물×연도 총보수를 뽑는다.

    헤더 salary+total 시그니처. 연도는 행 전체에서 '20NN' 단독 셀(위치 가변, MSFT 류 대응),
    총보수는 행 마지막 금액(SCT 는 Total($) 최우측 관례, 하한 1만 달러로 각주 오인 차단).
    이름 셀의 직함은 첫 직함 키워드 기준 분리(best-effort).

    Args:
        html: DEF 14A 전체 HTML 또는 사전 파싱 BeautifulSoup(1회 파싱 공유).

    Returns:
        list[dict]: ``{name, title, year(str), totalPay}`` (USD). SCT 부재 시 [].

    Raises:
        없음.

    Example:
        >>> rows = parseSummaryComp(proxyHtml)  # doctest: +SKIP
        >>> rows[0]  # {'name': 'Tim Cook', 'title': 'Chief Executive Officer', ...}
    """
    soup = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        g = tableGrid(table)
        if not g:
            continue
        head, bodyStart = _mergedHead(g)
        joined = " ".join(head)
        if "salary" not in joined or "total" not in joined:
            continue
        rows: list[dict] = []
        curName = ""
        for r in g[bodyStart:]:
            if not r:
                continue
            first = r[0] or ""
            ym = next((c.strip() for c in r if re.fullmatch(r"20\d\d", (c or "").strip())), None)
            if re.search(r"[A-Za-z]{3,}", first) and not re.match(r"(?i)total|all (other|current)", first):
                curName = first
            tot = next((moneyToFloat(c) for c in reversed(r) if moneyToFloat(c) and moneyToFloat(c) > 10_000), None)
            if curName and ym and tot:
                m = _TITLE_RE.search(curName)
                name = curName[: m.start()].strip(" ,;") if m else curName
                title = curName[m.start() :].strip() if m else ""
                rows.append({"name": name[:60], "title": title[:80], "year": ym, "totalPay": tot})
        if rows:
            return rows
    return []


def parseBeneficialOwnership(html: str | BeautifulSoup) -> list[dict]:
    """proxy HTML 의 Beneficial Ownership 표에서 주주별 지분율을 뽑는다.

    헤더에 'beneficial' + percent 명명 컬럼('percent'/'% of class') 시그니처. percent 컬럼에서만
    수치를 취해 나이·주식수 오인을 차단한다(0 < pct <= 100 게이트).

    Args:
        html: DEF 14A 전체 HTML 또는 사전 파싱 BeautifulSoup(1회 파싱 공유).

    Returns:
        list[dict]: ``{holder, pct}``. 표 부재 시 [].

    Raises:
        없음.

    Example:
        >>> rows = parseBeneficialOwnership(proxyHtml)  # doctest: +SKIP
        >>> rows[0]  # {'holder': 'The Vanguard Group', 'pct': 9.63}
    """
    soup = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        g = tableGrid(table)
        if not g:
            continue
        head, bodyStart = _mergedHead(g)
        joined = " ".join(head)
        if "beneficial" not in joined:
            continue
        pctCols = [j for j, c in enumerate(head) if re.search(r"percent|% of class|%\s*$", c)]
        if not pctCols:
            continue
        rows: list[dict] = []
        for r in g[bodyStart:]:
            if len(r) < 2:
                continue
            nm = r[0] or ""
            if not re.search(r"[A-Za-z]{3,}", nm):
                continue
            pm = None
            for j in pctCols:
                if j < len(r):
                    m = re.search(r"([\d.]+)\s*%?", (r[j] or "").strip())
                    if m and m.group(1) not in ("", "."):
                        v = float(m.group(1))
                        if 0 < v <= 100:
                            pm = v
                            break
            if pm is not None:
                rows.append({"holder": re.sub(r"\s*\(\d+\)\s*$", "", nm)[:60], "pct": pm})
        if rows:
            return rows
    return []


__all__ = ["moneyToFloat", "parseAuditFees", "parseBeneficialOwnership", "parseSummaryComp", "tableGrid"]
