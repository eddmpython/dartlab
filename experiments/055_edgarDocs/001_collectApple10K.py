"""
실험 ID: 055-001
실험명: Apple 10-K 원문 수집 → DART docs parquet 형태 저장

목적:
- SEC EDGAR에서 10-K 원문 HTML을 다운로드
- DART docs parquet과 동일한 스키마로 변환 가능한지 검증
- Item별 분리가 regex로 가능한지 확인
- parquet 파일 크기 측정 → shard 정책 결정 근거

가설:
1. SEC Submissions API + HTML 직접 다운로드로 외부 의존성 없이 수집 가능
2. 10-K의 Item 분리는 regex로 90% 이상 정확하게 가능
3. 1개 종목 10년치 parquet 크기가 10MB 이하

방법:
1. Submissions API로 Apple(CIK 0000320193)의 10-K 목록 조회
2. 2015년 이후 10-K HTML 다운로드
3. HTML → 마크다운 변환 (eddmpython _htmlToText 패턴)
4. Item별 분리 (regex)
5. DART docs 스키마로 parquet 저장
6. 파일 크기, 섹션 수, 변환 품질 확인

결과 (실험 후 작성):
- 11개 10-K (2015~2025) 수집 성공
- 237행, 0.52 MB parquet (11개 종목년도)
- Item 분리: 2015-2016 20개, 2017-2020 21개, 2021-2022 22개, 2023-2025 23개
- 주요 Item 크기: Financial Statements 104K, Risk Factors 61K, MD&A 35K, Business 19K
- HTML 형식 3종 발견:
  - 2015: <b><a name="toc..."></a>Item N.</b> (앵커 기반, <td> 안)
  - 2016-2019: <font style="font-weight:bold">Item N.</font> (<td> 안, bold로 구분)
  - 2020+: <span style="...">Item N.</span> (인라인 XBRL, <div>/<p> 안)
- _extractItemHeaders: 테이블 변환 전 bold Item 헤더를 <p>로 추출하여 해결
- <a href="...">(목차)와 <a name="...">(본문 앵커) 구별이 핵심

결론:
- 가설1 채택: SEC API + HTML 직접 다운로드로 외부 의존성 없이 수집 가능
- 가설2 채택: regex Item 분리 100% 성공 (3종 HTML 형식 모두 대응)
- 가설3 채택: 1종목 11년치 = 0.52 MB (10MB 이하)
- shard 정책: 1000종목 기준 약 500MB → 단일 릴리즈 태그로 충분

실험일: 2026-03-11
"""

import re
import time
from pathlib import Path

import polars as pl
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}
BASE_URL = "https://www.sec.gov"
DATA_URL = "https://data.sec.gov"
OUTPUT_DIR = Path(__file__).parent


def getSubmissions(cik: str) -> dict:
    """SEC Submissions API로 파일링 목록 조회"""
    url = f"{DATA_URL}/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find10Ks(submissions: dict, sinceYear: int = 2015) -> list[dict]:
    """10-K 파일링만 필터링 (sinceYear 이후)"""
    recent = submissions["filings"]["recent"]
    results = []
    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        filingDate = recent["filingDate"][i]
        year = int(filingDate[:4])
        if year < sinceYear:
            continue
        accession = recent["accessionNumber"][i]
        primaryDoc = recent["primaryDocument"][i]
        results.append({
            "accessionNumber": accession,
            "filingDate": filingDate,
            "year": year,
            "primaryDocument": primaryDoc,
            "filingUrl": f"{BASE_URL}/Archives/edgar/data/{submissions['cik']}/{accession.replace('-', '')}/{primaryDoc}",
        })
    return sorted(results, key=lambda x: x["filingDate"])


def downloadHtml(url: str) -> str:
    """HTML 다운로드 (rate limit 준수)"""
    time.sleep(0.15)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def tableToMarkdown(table) -> str:
    """HTML 테이블 → 마크다운 (eddmpython 패턴)"""
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            colspan = int(cell.get("colspan", 1))
            text = cell.get_text(strip=True)
            text = re.sub(r"\s+", " ", text)
            text = text.replace("|", "｜")
            cells.append(text)
            for _ in range(colspan - 1):
                cells.append("")
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    maxCols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < maxCols:
            r.append("")

    lines = []
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * maxCols) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extractItemHeaders(soup) -> None:
    """테이블 안 Item 헤더를 독립 <p> 태그로 추출.

    HTML 형식별 패턴:
    - AAPL 2015: <b><a name="toc..."></a>Item N.</b> in <td>
    - AAPL 2016-2019: <font style="font-weight:bold">Item N.</font> in <td>
    - INTC 2021+: <span style="font-size:9pt">Item N.</span> in <td> (bold 없음)
    - TSLA 2015-2018: <p style="margin-left:12pt">Item N.</p> in <td> (bold 없음)

    공통점: 테이블 안에 있고, <a href="..."> 링크가 없음.
    목차(TOC)는 항상 <a href="#...">로 감싸져 있으므로 href 체크로 구분 가능.
    """
    itemRe = re.compile(r"Item\s+\d+[A-C]?\.", re.IGNORECASE)
    for tag in soup.find_all(["font", "span", "b", "strong", "p", "div"]):
        text = tag.get_text(strip=True)
        if not itemRe.match(text):
            continue
        if tag.find_parent("a", href=True) or tag.find("a", href=True):
            continue
        parentTable = tag.find_parent("table")
        if not parentTable:
            continue
        headerP = soup.new_tag("p")
        headerP.string = text
        parentTable.insert_before(headerP)


def htmlToText(html: str) -> str:
    """HTML → 텍스트+마크다운 변환 (eddmpython 패턴)"""
    import warnings

    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()

    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()

    _extractItemHeaders(soup)

    for table in soup.find_all("table"):
        md = tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
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


ITEM_PATTERN = re.compile(
    r"(?:^|\n)\s*"
    r"(?:ITEM|Item)\s+"
    r"(\d+[A-C]?)"
    r"[\.\:\s\—\-]+"
    r"([^\n]{3,80})",
    re.MULTILINE,
)

ITEM_NAMES = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Common Equity",
    "6": "Reserved",
    "7": "MD&A",
    "7A": "Market Risk Disclosures",
    "8": "Financial Statements",
    "9": "Changes in Accountants",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Foreign Jurisdiction Disclosures",
    "10": "Directors & Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership",
    "13": "Related Transactions",
    "14": "Principal Accountant Fees",
    "15": "Exhibits & Schedules",
    "16": "Form 10-K Summary",
}


def splitItems(text: str) -> list[dict]:
    """텍스트를 Item별로 분리"""
    matches = list(ITEM_PATTERN.finditer(text))
    if not matches:
        return [{"itemNumber": "0", "title": "Full Document", "content": text}]

    seen = set()
    items = []
    for i, m in enumerate(matches):
        itemNum = m.group(1).upper()
        if itemNum in seen:
            continue
        seen.add(itemNum)

        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        title = m.group(2).strip().rstrip(".")
        canonTitle = ITEM_NAMES.get(itemNum, title)

        items.append({
            "itemNumber": itemNum,
            "title": f"Item {itemNum}. {canonTitle}",
            "content": content,
        })

    return items


def collect(cik: str, ticker: str, companyName: str, sinceYear: int = 2015):
    """메인 수집 파이프라인"""
    print(f"=== {companyName} ({ticker}) 10-K 수집 시작 (since {sinceYear}) ===\n")

    print("[1/4] Submissions API 조회...")
    subs = getSubmissions(cik)

    print("[2/4] 10-K 필터링...")
    filings = find10Ks(subs, sinceYear=sinceYear)
    print(f"  → {len(filings)}개 10-K 발견\n")

    allSections = []
    for fi in filings:
        print(f"[3/4] {fi['filingDate']} 10-K 다운로드...")
        html = downloadHtml(fi["filingUrl"])
        print(f"  → HTML {len(html):,} bytes")

        text = htmlToText(html)
        print(f"  → 텍스트 {len(text):,} chars")

        items = splitItems(text)
        print(f"  → {len(items)}개 Item 분리")

        for order, item in enumerate(items):
            allSections.append({
                "cik": str(subs["cik"]),
                "company_name": companyName,
                "ticker": ticker,
                "year": str(fi["year"]),
                "filing_date": fi["filingDate"],
                "accession_no": fi["accessionNumber"],
                "form_type": "10-K",
                "section_order": order,
                "section_title": item["title"],
                "filing_url": fi["filingUrl"],
                "section_content": item["content"],
            })
        print()

    if not allSections:
        print("수집된 데이터 없음")
        return

    print(f"[4/4] Parquet 저장...")
    df = pl.DataFrame(allSections)
    outPath = OUTPUT_DIR / f"{ticker}.parquet"
    df.write_parquet(outPath)

    fileSizeMb = outPath.stat().st_size / (1024 * 1024)
    print(f"\n=== 결과 ===")
    print(f"  파일: {outPath}")
    print(f"  크기: {fileSizeMb:.2f} MB")
    print(f"  행 수: {df.height}")
    print(f"  연도: {df['year'].unique().sort().to_list()}")
    print(f"  섹션 수/연도: {df.height / len(filings):.1f}")
    print(f"\n  스키마:")
    print(f"  {df.schema}")
    print(f"\n  섹션 제목 샘플:")
    for title in df["section_title"].unique().sort().to_list()[:20]:
        print(f"    - {title}")

    print(f"\n  섹션별 평균 크기:")
    stats = (
        df.group_by("section_title")
        .agg(
            pl.col("section_content").str.len_chars().mean().alias("avg_chars"),
            pl.len().alias("count"),
        )
        .sort("avg_chars", descending=True)
    )
    for row in stats.iter_rows(named=True):
        print(f"    {row['section_title']}: {row['avg_chars']:,.0f} chars ({row['count']}건)")


if __name__ == "__main__":
    collect(
        cik="320193",
        ticker="AAPL",
        companyName="Apple Inc.",
        sinceYear=2015,
    )
