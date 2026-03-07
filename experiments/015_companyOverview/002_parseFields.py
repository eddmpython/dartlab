"""회사의 개요 정량 필드 파싱 실험.

"1. 회사의 개요" 텍스트에서 추출 가능한 필드:
- 설립일자
- 본사 주소
- 홈페이지
- 종속기업 수
- 중소기업/벤처/중견기업 여부
- 신용등급 (Moody's, S&P, 한국 신용평가사)
- 상장일
"""

import sys
import re
sys.stdout.reconfigure(encoding="utf-8")

from dartlab.core import loadData
from dartlab.core.reportSelector import selectReport, extractReportYear
import polars as pl


def parseOverview(text: str) -> dict:
    result = {}

    m = re.search(r"설립일[자]?\s*\n?(.*?\d{4}년\s*\d{1,2}월\s*\d{1,2}일)", text, re.DOTALL)
    if m:
        dateStr = m.group(1)
        dm = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", dateStr)
        if dm:
            result["founded"] = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
    if "founded" not in result:
        m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일[에\s]*설립", text)
        if m:
            result["founded"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    addrPatterns = [
        r"\|\s*(?:주\s*소|본사\s*주소)\s*\|\s*:?\s*\|?\s*(?:\(본사\)\s*)?(.+?)\s*\|",
        r"본점소재지\s*[:：]\s*(.+)",
        r"(?:○\s*)?주\s+소\s*[:：]\s*(.+)",
        r"주소\s*[:：]\s*(.+)",
        r"\(주\s*소\)\s*(.+)",
        r"주소지는\s*'([^']+)'",
        r"본사의\s*주소[^\n]*\n[-\s]*([가-힣].{10,})",
    ]
    for pat in addrPatterns:
        m = re.search(pat, text)
        if m:
            addr = m.group(1).strip().rstrip("|").strip()
            if len(addr) > 5 and not addr.startswith("http"):
                result["address"] = addr
                break

    hpPatterns = [
        r"홈페이지\s*[:：]?\s*(https?://\S+)",
        r"\|\s*홈페이지\s*(?:주소)?\s*\|\s*:?\s*\|?\s*(https?://\S+?)[\s|]",
        r"홈페이지[^\n]*?(https?://\S+)",
        r"\(홈페이지\)\s*(https?://\S+)",
        r"홈페이지[^\n]*?'(www\.\S+?)'",
        r"홈페이지[^\n]*?(www\.\S+?)[\s'\")]",
    ]
    for pat in hpPatterns:
        m = re.search(pat, text)
        if m:
            hp = m.group(1).strip().rstrip("|").strip()
            if not hp.startswith("http"):
                hp = "http://" + hp
            result["homepage"] = hp
            break

    m = re.search(r"(\d+)개의?\s*종속(?:기업|회사)", text)
    if m:
        result["subsidiaryCount"] = int(m.group(1))

    m = re.search(r"종속기업은.*?(\d+)개사", text)
    if not m:
        m = re.search(r"(\d+)개사", text)
    if m and "subsidiaryCount" not in result:
        result["subsidiaryCount"] = int(m.group(1))

    smeMatch = re.search(r"중소기업\s*해당\s*여부\s*\|?\s*(미해당|해당)", text)
    if not smeMatch:
        smeMatch = re.search(r"중소기업에\s*(해당되지\s*않|해당)", text)
    if smeMatch:
        result["isSME"] = "해당되지" not in smeMatch.group(1) and "미해당" not in smeMatch.group(1)

    ventureMatch = re.search(r"벤처기업\s*해당\s*여부\s*\|?\s*(미해당|해당)", text)
    if ventureMatch:
        result["isVenture"] = "미해당" not in ventureMatch.group(1)

    midMatch = re.search(r"중견기업\s*해당\s*여부\s*\|?\s*(미해당|해당)", text)
    if midMatch:
        result["isMidCap"] = "미해당" not in midMatch.group(1)

    seen = set()
    ratings = []
    creditSection = text.split("신용평가에 관한 사항")[-1] if "신용평가에 관한 사항" in text else ""
    if creditSection:
        lastDateMatch = None
        for dm in re.finditer(r"(\d{4}\.\d{2})", creditSection):
            lastDateMatch = dm
        if lastDateMatch:
            lastPos = lastDateMatch.start()
            recentSection = creditSection[max(0, lastPos - 200):lastPos + 200]
        else:
            recentSection = creditSection[:500]

        for m in re.finditer(
            r"(Moody'?s|S&P|한국신용평가|한국기업평가|NICE신용평가|나이스신용평가)"
            r"\D{0,20}?"
            r"(Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|Caa|Ca|C"
            r"|AAA|AA[+\-]|AA|A[+\-]|A"
            r"|BBB[+\-]|BBB|BB[+\-]|BB|B[+\-]|B"
            r"|CCC[+\-]|CCC|CC|D)",
            recentSection
        ):
            key = (m.group(1), m.group(2))
            if key not in seen:
                seen.add(key)
                ratings.append({"agency": m.group(1), "grade": m.group(2)})
    if ratings:
        result["creditRatings"] = ratings

    listedPatterns = [
        r"(?:상장|기업공개).*?(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        r"(?:유가증권|코스닥|코넥스|코스피).*?상장\s*\|\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
    ]
    for pat in listedPatterns:
        m = re.search(pat, text)
        if m:
            result["listedDate"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            break

    return result


testCodes = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대자동차"),
    ("035720", "카카오"),
    ("001200", "유진증권"),
    ("003490", "대교"),
    ("000020", "동화약품"),
    ("293940", "신한알파리츠"),
    ("055550", "신한지주"),
    ("105560", "KB금융"),
]

for code, name in testCodes:
    print(f"\n{'=' * 60}")
    print(f"{code} {name}")
    print("=" * 60)

    df = loadData(code)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        overviewRow = report.filter(
            pl.col("section_title") == "1. 회사의 개요"
        )
        if overviewRow.height == 0:
            overviewRow = report.filter(
                pl.col("section_title").str.contains("회사의 개요")
                & pl.col("section_title").str.starts_with("1.")
            )
        if overviewRow.height == 0:
            overviewRow = report.filter(
                pl.col("section_title").str.contains("회사의 개요")
                & ~pl.col("section_title").str.starts_with("I.")
            )
        if overviewRow.height == 0:
            print(f"  {year}: 1.회사의 개요 없음")
            continue

        text = overviewRow.row(0, named=True)["section_content"]
        parsed = parseOverview(text)

        reportYear = extractReportYear(overviewRow["report_type"][0])
        print(f"  {reportYear}: {parsed}")
        break
