"""
실험 ID: 055-002
실험명: 2015~2019 Apple 10-K Item 분리 실패 진단

목적:
- 001에서 2015~2019 10-K가 Item 1~2개로만 분리됨
- 해당 연도 HTML/텍스트에서 "Item" 패턴이 어떤 형태인지 확인
- regex 보강 방안 도출

가설:
1. 2015~2019 10-K는 Item 헤더 포맷이 다를 수 있음 (대문자, 볼드, 공백 등)
2. iXBRL 태그가 Item 텍스트를 분리시킬 수 있음

방법:
1. 2016년 10-K HTML 다운로드
2. "Item" 문자열 주변 컨텍스트 100자씩 출력
3. 텍스트 변환 후에도 동일 확인
4. regex 패턴 개선안 테스트

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-11
"""

import re
import time

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}


def getFilingUrl(cik: str, sinceYear: int, targetYear: int) -> str:
    """특정 연도 10-K URL 반환"""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    subs = resp.json()
    recent = subs["filings"]["recent"]
    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        filingDate = recent["filingDate"][i]
        year = int(filingDate[:4])
        if year == targetYear:
            accession = recent["accessionNumber"][i]
            primaryDoc = recent["primaryDocument"][i]
            cikNum = subs["cik"]
            return f"https://www.sec.gov/Archives/edgar/data/{cikNum}/{accession.replace('-', '')}/{primaryDoc}"
    return ""


def diagnose(html: str, year: int):
    """HTML과 텍스트에서 Item 패턴 진단"""
    print(f"\n{'='*60}")
    print(f"  {year}년 10-K 진단")
    print(f"{'='*60}")

    print(f"\n[HTML 크기] {len(html):,} bytes")

    print(f"\n[1] HTML 원문에서 'Item' 검색 (대소문자 무시, 처음 30개):")
    itemRe = re.compile(r".{0,50}(?:Item|ITEM)\s+\d+[A-C]?.{0,50}", re.IGNORECASE)
    htmlMatches = itemRe.findall(html)
    for i, m in enumerate(htmlMatches[:30]):
        clean = re.sub(r"\s+", " ", m).strip()
        print(f"  [{i:2d}] {clean[:120]}")

    print(f"\n  총 {len(htmlMatches)}개 매치")

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    print(f"\n[2] 텍스트 변환 후 'Item' 검색:")
    textItemRe = re.compile(
        r"^(.{0,10}(?:Item|ITEM)\s+\d+[A-C]?.{0,80})",
        re.MULTILINE | re.IGNORECASE,
    )
    textMatches = textItemRe.findall(text)
    for i, m in enumerate(textMatches[:30]):
        clean = m.strip()
        print(f"  [{i:2d}] {clean[:120]}")

    print(f"\n  총 {len(textMatches)}개 매치")

    print(f"\n[3] 정확한 Item 헤더 패턴 (줄 시작):")
    headerRe = re.compile(
        r"^((?:Item|ITEM)\s+\d+[A-C]?[\.\:\s\—\-]+[^\n]{3,80})",
        re.MULTILINE,
    )
    headerMatches = headerRe.findall(text)
    for i, m in enumerate(headerMatches[:30]):
        print(f"  [{i:2d}] {m.strip()[:120]}")
    print(f"\n  총 {len(headerMatches)}개 매치")

    print(f"\n[4] 'PART' 패턴:")
    partRe = re.compile(r"^(.{0,5}(?:PART|Part)\s+[IViv]+.{0,50})", re.MULTILINE)
    partMatches = partRe.findall(text)
    for m in partMatches[:10]:
        print(f"  {m.strip()[:100]}")


if __name__ == "__main__":
    for targetYear in [2016, 2019, 2021]:
        print(f"\n\n>>> {targetYear}년 10-K 다운로드 중...")
        url = getFilingUrl("320193", sinceYear=2015, targetYear=targetYear)
        if not url:
            print(f"  {targetYear}년 10-K 없음")
            continue
        time.sleep(0.2)
        resp = requests.get(url, headers=HEADERS, timeout=60)
        diagnose(resp.text, targetYear)
