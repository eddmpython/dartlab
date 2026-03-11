"""
실험 ID: 055-007
실험명: 2015 10-K 본문 앵커 위치와 Item 텍스트 관계

목적:
- <a name="toc17062_*"> 앵커 주변에 Item 텍스트가 어떻게 배치되는지 확인
- 본문 Item 헤더 추출 방법 도출

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

    print("=== <a name='toc17062_*'> 앵커 주변 구조 ===\n")
    anchorRe = re.compile(r"toc17062_\d+")
    for tag in soup.find_all("a", attrs={"name": anchorRe}):
        name = tag.get("name", "")
        parent = tag.parent
        grandparent = parent.parent if parent else None

        print(f"<a name='{name}'> text='{tag.get_text(strip=True)[:60]}'")
        print(f"  parent: <{parent.name}> text='{parent.get_text(strip=True)[:80]}'")
        if grandparent:
            print(f"  grandparent: <{grandparent.name}>")

        nextSibs = []
        for sib in tag.next_siblings:
            if hasattr(sib, "name") and sib.name:
                sibText = sib.get_text(strip=True)[:80]
                nextSibs.append(f"<{sib.name}> '{sibText}'")
            elif str(sib).strip():
                nextSibs.append(f"text: '{str(sib).strip()[:80]}'")
            if len(nextSibs) >= 3:
                break
        print(f"  next siblings: {nextSibs}")

        parentNextSibs = []
        if parent:
            for sib in parent.next_siblings:
                if hasattr(sib, "name") and sib.name:
                    sibText = sib.get_text(strip=True)[:80]
                    parentNextSibs.append(f"<{sib.name}> '{sibText}'")
                if len(parentNextSibs) >= 3:
                    break
        print(f"  parent next siblings: {parentNextSibs}")
        print()

    print("\n\n=== raw HTML에서 'toc17062_2' 주변 500자 ===\n")
    m = re.search(r'name="toc17062_2"', html)
    if m:
        start = max(0, m.start() - 100)
        end = min(len(html), m.end() + 500)
        print(html[start:end])
