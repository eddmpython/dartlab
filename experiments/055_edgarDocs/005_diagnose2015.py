"""
실험 ID: 055-005
실험명: 2015 10-K HTML Item 헤더 구조 진단

목적:
- 2015 10-K만 2개 Item 분리 (나머지 20+개)인 원인 파악
- bold Item 태그가 2016과 다른 패턴인지 확인

실험일: 2026-03-11
"""

import re
import time
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}


def getFilingUrl(cik: str, targetYear: int) -> str:
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    subs = resp.json()
    recent = subs["filings"]["recent"]
    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        year = int(recent["filingDate"][i][:4])
        if year == targetYear:
            accession = recent["accessionNumber"][i]
            primaryDoc = recent["primaryDocument"][i]
            return f"https://www.sec.gov/Archives/edgar/data/{subs['cik']}/{accession.replace('-', '')}/{primaryDoc}"
    return ""


if __name__ == "__main__":
    url = getFilingUrl("320193", 2015)
    print(f"URL: {url}\n")
    time.sleep(0.2)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    html = resp.text

    print(f"HTML 크기: {len(html):,} bytes\n")

    print("=== 1) HTML에서 'Item' 포함 bold 태그 검색 ===\n")
    soup = BeautifulSoup(html, "lxml")
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()

    itemRe = re.compile(r"Item\s+\d+[A-C]?[\.\s]", re.IGNORECASE)
    count = 0
    for tag in soup.find_all(["font", "span", "b", "strong", "td", "div", "p"]):
        text = tag.get_text(strip=True)
        if not itemRe.match(text):
            continue
        style = tag.get("style", "")
        isBold = (
            tag.name in ("b", "strong")
            or ("font-weight" in style and ("bold" in style or "700" in style))
        )
        hasLink = tag.find_parent("a") is not None or tag.find("a") is not None
        inTable = tag.find_parent("table") is not None

        print(f"<{tag.name}> bold={isBold} link={hasLink} table={inTable}")
        print(f"  text: {text[:100]}")
        print(f"  style: {style[:100]}")
        if tag.parent:
            print(f"  parent: <{tag.parent.name}> style={tag.parent.get('style', '')[:80]}")
        print()
        count += 1
        if count >= 40:
            break

    print(f"\n총 {count}개 'Item N' 태그 발견")

    print("\n\n=== 2) raw HTML에서 'Item 1.' 주변 100자 검색 ===\n")
    for m in re.finditer(r"Item\s+1\.", html):
        start = max(0, m.start() - 150)
        end = min(len(html), m.end() + 150)
        snippet = html[start:end].replace("\n", " ").replace("\r", "")
        print(f"[pos {m.start()}] ...{snippet}...\n")
