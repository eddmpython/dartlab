"""
실험 ID: 055-004
실험명: 2016 10-K HTML에서 bold Item 태그 구조 확인

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
    url = getFilingUrl("320193", 2016)
    time.sleep(0.2)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    html = resp.text

    itemRe = re.compile(r"font-weight\s*:\s*bold[^>]*>Item\s+\d+", re.IGNORECASE)

    print("=== 2016 10-K: bold Item 태그 주변 HTML ===\n")
    for i, m in enumerate(itemRe.finditer(html)):
        start = max(0, m.start() - 100)
        end = min(len(html), m.end() + 200)
        snippet = html[start:end].replace("\n", " ")
        print(f"[{i}] ...{snippet}...\n")
        if i >= 5:
            break

    print("\n=== BeautifulSoup으로 bold Item 찾기 ===\n")
    soup = BeautifulSoup(html, "lxml")
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()

    itemTextRe = re.compile(r"Item\s+\d+[A-C]?[\.\s]", re.IGNORECASE)
    count = 0
    for tag in soup.find_all(["span", "font", "div", "td", "b", "strong"]):
        text = tag.get_text(strip=True)
        if not itemTextRe.match(text):
            continue
        style = tag.get("style", "")
        isBold = "font-weight" in style and ("bold" in style or "700" in style)
        isParentBold = tag.find_parent(["b", "strong"]) is not None
        hasLink = tag.find("a") is not None or tag.find_parent("a") is not None

        print(f"Tag: <{tag.name}> text='{text[:60]}' bold={isBold} parentBold={isParentBold} hasLink={hasLink}")
        print(f"  style: {style[:100]}")
        print(f"  parent: <{tag.parent.name}> children: {[c.name for c in tag.children if c.name]}")
        print()
        count += 1
        if count >= 25:
            break
