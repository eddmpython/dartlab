"""
실험 ID: 055-003
실험명: 텍스트 변환 결과 직접 확인 (2016 vs 2021)

목적:
- htmlToText 결과에서 "Item" 문자열이 실제로 어떻게 보이는지 확인
- 002에서 텍스트 변환 후 "Item" 0개였던 원인 정확히 파악

결과 (실험 후 작성):
-

실험일: 2026-03-11
"""

import re
import time
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}


def htmlToText(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()
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
    for targetYear in [2016, 2021]:
        print(f"\n{'='*60}")
        print(f"  {targetYear}년 텍스트 변환 결과 확인")
        print(f"{'='*60}")

        url = getFilingUrl("320193", targetYear)
        time.sleep(0.2)
        resp = requests.get(url, headers=HEADERS, timeout=60)
        text = htmlToText(resp.text)

        print(f"텍스트 길이: {len(text):,} chars")

        itemLines = []
        for i, line in enumerate(text.split("\n")):
            if re.search(r"Item\s+\d+[A-C]?", line, re.IGNORECASE):
                itemLines.append((i, line[:150]))

        print(f"\n'Item N' 포함 줄 ({len(itemLines)}개):")
        for lineNum, content in itemLines[:40]:
            print(f"  L{lineNum:5d}: {content}")

        print(f"\n처음 200줄:")
        for i, line in enumerate(text.split("\n")[:200]):
            if line.strip():
                print(f"  L{i:5d}: {line[:120]}")
