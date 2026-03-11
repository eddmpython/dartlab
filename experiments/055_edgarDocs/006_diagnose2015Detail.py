"""
실험 ID: 055-006
실험명: 2015 10-K <a> 태그 구분 (href vs name)

목적:
- 2015 10-K의 Item 헤더 <a> 태그가 href(목차)인지 name(본문 앵커)인지 확인
- 본문 Item 식별 기준 도출

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
    time.sleep(0.2)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    html = resp.text

    soup = BeautifulSoup(html, "lxml")
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()

    itemRe = re.compile(r"Item\s+\d+[A-C]?\.", re.IGNORECASE)

    print("=== 2015 10-K: <a> 태그 속성 분석 ===\n")
    for tag in soup.find_all("a"):
        text = tag.get_text(strip=True)
        if not itemRe.match(text):
            continue
        href = tag.get("href", "")
        name = tag.get("name", "")
        parentTag = tag.parent.name if tag.parent else ""
        inTable = tag.find_parent("table") is not None
        parentStyle = tag.parent.get("style", "") if tag.parent else ""

        marker = "TOC" if href else "BODY" if name else "???"
        print(f"[{marker}] <a href='{href}' name='{name}'> text='{text[:60]}'")
        print(f"  parent: <{parentTag}> table={inTable}")
        print(f"  parentStyle: {parentStyle[:100]}")
        print()
