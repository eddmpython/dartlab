"""
실험 ID: 055-009
실험명: Submissions API 구조 확인 — recent vs files

목적:
- recent에 왜 일부 종목만 적은 filing이 있는지 확인
- files 배열에 추가 JSON이 있는지 확인
- 전체 filing 목록을 가져오는 방법 확인

실험일: 2026-03-11
"""

import requests

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}


def checkSubmissions(cik: str, ticker: str):
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    data = resp.json()

    recent = data["filings"]["recent"]
    files = data["filings"]["files"]

    recentForms = recent["form"]
    tenKs = [f for f in recentForms if f in ("10-K", "20-F")]

    print(f"{ticker} (CIK {cik}):")
    print(f"  recent: {len(recentForms)} filings total, {len(tenKs)} 10-K/20-F")
    print(f"  files: {len(files)} additional JSON files")
    if files:
        for f in files:
            print(f"    - {f['name']} ({f['filingCount']} filings, {f['filingFrom']}~{f['filingTo']})")

    tenKYears = []
    for i, form in enumerate(recent["form"]):
        if form in ("10-K", "20-F"):
            tenKYears.append(recent["filingDate"][i][:4])
    if tenKYears:
        print(f"  10-K/20-F years in recent: {tenKYears}")
    print()


if __name__ == "__main__":
    targets = [
        ("320193", "AAPL"), ("789019", "MSFT"), ("1652044", "GOOGL"),
        ("1018724", "AMZN"), ("1326801", "META"), ("19617", "JPM"),
        ("886982", "GS"), ("50863", "INTC"),
        ("1090872", "TSM"), ("1577552", "BABA"),
        ("1364742", "SAP"), ("1108524", "TM"), ("885590", "NVO"),
    ]
    for cik, ticker in targets:
        checkSubmissions(cik, ticker)
