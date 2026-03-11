"""
실험 ID: 055-010
실험명: INTC/TSLA low-split 연도별 진단

목적:
- INTC 6개, TSLA 4개 low-split filing의 연도와 HTML 구조 확인
- Item 헤더가 어떤 패턴으로 존재하는지 파악
- _extractItemHeaders가 커버하지 못하는 새 패턴 식별

실험일: 2026-03-11
"""

import re
import time
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}
DATA_URL = "https://data.sec.gov"
BASE_URL = "https://www.sec.gov"

ITEM_PATTERN = re.compile(
    r"(?:^|\n)\s*"
    r"(?:ITEM|Item)\s+"
    r"(\d+[A-K]?)"
    r"[\.\:\s\—\-]+"
    r"([^\n]{3,80})",
    re.MULTILINE,
)


def getSubmissions(cik: str) -> dict:
    url = f"{DATA_URL}/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _mergeFilingArrays(submissions: dict, sinceYear: int) -> dict:
    recent = submissions["filings"]["recent"]
    merged = {k: list(v) for k, v in recent.items()}
    for fileInfo in submissions["filings"].get("files", []):
        filingTo = fileInfo.get("filingTo", "")
        if filingTo and int(filingTo[:4]) < sinceYear:
            continue
        fname = fileInfo["name"]
        url = f"{DATA_URL}/submissions/{fname}"
        time.sleep(0.12)
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        extra = resp.json()
        for k in merged:
            if k in extra:
                merged[k].extend(extra[k])
    return merged


def findFilings(submissions: dict, sinceYear: int) -> list[dict]:
    allFilings = _mergeFilingArrays(submissions, sinceYear)
    results = []
    for i, form in enumerate(allFilings["form"]):
        if form != "10-K":
            continue
        filingDate = allFilings["filingDate"][i]
        year = int(filingDate[:4])
        if year < sinceYear:
            continue
        accession = allFilings["accessionNumber"][i]
        primaryDoc = allFilings["primaryDocument"][i]
        results.append({
            "accessionNumber": accession,
            "filingDate": filingDate,
            "year": year,
            "primaryDocument": primaryDoc,
            "filingUrl": f"{BASE_URL}/Archives/edgar/data/{submissions['cik']}/{accession.replace('-', '')}/{primaryDoc}",
        })
    return sorted(results, key=lambda x: x["filingDate"])


def _extractItemHeaders(soup) -> None:
    itemRe = re.compile(r"Item\s+\d+[A-K]?\.", re.IGNORECASE)
    for tag in soup.find_all(["font", "span", "b", "strong"]):
        text = tag.get_text(strip=True)
        if not itemRe.match(text):
            continue
        if tag.find_parent("a", href=True) or tag.find("a", href=True):
            continue
        style = tag.get("style", "")
        isBold = (
            tag.name in ("b", "strong")
            or ("font-weight" in style and ("bold" in style or "700" in style))
        )
        if not isBold:
            continue
        parentTable = tag.find_parent("table")
        if not parentTable:
            continue
        headerP = soup.new_tag("p")
        headerP.string = text
        parentTable.insert_before(headerP)


def htmlToText(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()
    _extractItemHeaders(soup)
    for table in soup.find_all("table"):
        table.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4"]):
        p.insert_after("\n")
    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def diagnose(cik: str, ticker: str):
    print(f"\n{'='*60}")
    print(f"  {ticker} (CIK {cik}) 진단")
    print(f"{'='*60}\n")

    subs = getSubmissions(cik)
    filings = findFilings(subs, 2009)

    for fi in filings:
        time.sleep(0.12)
        resp = requests.get(fi["filingUrl"], headers=HEADERS, timeout=60)
        html = resp.text
        text = htmlToText(html)
        matches = list(ITEM_PATTERN.finditer(text))
        nItems = len(set(m.group(1).upper() for m in matches))

        marker = " <<<< LOW" if nItems <= 3 else ""
        print(f"{fi['filingDate']} ({fi['year']}): {nItems} items, {len(html):,} HTML bytes{marker}")

        if nItems <= 3:
            print(f"  URL: {fi['filingUrl']}")
            itemLines = []
            for i, line in enumerate(text.split("\n")):
                if re.search(r"Item\s+\d+[A-K]?", line, re.IGNORECASE):
                    itemLines.append((i, line[:120]))
            print(f"  텍스트 내 'Item N' 줄 ({len(itemLines)}개):")
            for ln, content in itemLines[:10]:
                print(f"    L{ln}: {content}")

            soup = BeautifulSoup(html, "lxml")
            for ix_tag in soup.find_all(re.compile(r"^ix:")):
                ix_tag.unwrap()
            itemRe = re.compile(r"Item\s+\d+[A-K]?[\.\s]", re.IGNORECASE)
            htmlItems = []
            for tag in soup.find_all(["font", "span", "b", "strong", "p", "div", "h1", "h2", "h3", "h4"]):
                t = tag.get_text(strip=True)
                if itemRe.match(t):
                    style = tag.get("style", "")
                    inTable = tag.find_parent("table") is not None
                    hasLink = tag.find_parent("a") is not None or tag.find("a") is not None
                    htmlItems.append(f"<{tag.name}> table={inTable} link={hasLink} '{t[:60]}' style={style[:60]}")
            print(f"  HTML 내 Item 태그 ({len(htmlItems)}개):")
            for item in htmlItems[:15]:
                print(f"    {item}")
            print()


if __name__ == "__main__":
    diagnose("50863", "INTC")
    diagnose("1318605", "TSLA")
