"""SPAC 제외 커버리지 재측정."""

import os
import re
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, extractCorpName, loadData
from dartlab.core.reportSelector import parsePeriodKey, selectReport
from dartlab.core.tableParser import extractAccounts

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "PNL": r"손익계산서",
    "CI": r"포괄손익",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}


def splitStatementsV2(content):
    lines = content.split("\n")
    headers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            if len(cells) != 1:
                continue
            s = cells[0]
        sNoSpace = re.sub(r"\s+", "", s)
        for key, pattern in _STATEMENT_PATTERNS.items():
            if re.search(pattern, sNoSpace):
                headers.append((i, key))
                break
    seen = {}
    uniqueHeaders = []
    for idx, key in headers:
        if key in seen:
            uniqueHeaders[seen[key]] = (idx, key)
        else:
            seen[key] = len(uniqueHeaders)
            uniqueHeaders.append((idx, key))
    result = {}
    for j, (startIdx, key) in enumerate(uniqueHeaders):
        endIdx = uniqueHeaders[j + 1][0] if j + 1 < len(uniqueHeaders) else len(lines)
        result[key] = "\n".join(lines[startIdx:endIdx])
    return result


def extractContentV2(report):
    cons = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & ~pl.col("section_title").str.contains("주석")
    )
    if cons.height > 0:
        content = cons["section_content"][0]
        if "연결대상" in content and ("없어" in content or "없으므로" in content):
            pass
        else:
            return content, "consolidated"
    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"
    return None, "none"


def isSpac(corpName):
    if corpName is None:
        return False
    return "스팩" in corpName or "스펙" in corpName or "SPAC" in corpName.upper()


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    spacCount = 0
    ok = 0
    fail = 0
    noReport = 0
    failCodes = []

    for code in codes:
        df = loadData(code)
        corpName = extractCorpName(df)

        if isSpac(corpName):
            spacCount += 1
            continue

        kinds = PERIOD_KINDS.get("y", PERIOD_KINDS["y"])
        years = sorted(df["year"].unique().to_list(), reverse=True)

        bsData = {}
        isData = {}
        cfData = {}

        for year in years:
            for kind in kinds:
                report = selectReport(df, year, reportKind=kind)
                if report is None:
                    continue
                content, scope = extractContentV2(report)
                if content is None:
                    continue
                parts = splitStatementsV2(content)
                key = year
                if int(key[:4]) < 2011:
                    continue
                for stKey, stContent, target in [
                    ("BS", parts.get("BS"), bsData),
                    ("IS", parts.get("PNL"), isData),
                    ("CF", parts.get("CF"), cfData),
                ]:
                    if stContent is None:
                        continue
                    accounts, order = extractAccounts(stContent)
                    if accounts:
                        target[key] = (accounts, order)

        if not bsData and not isData and not cfData:
            fail += 1
            # 보고서 자체 있는지 확인
            hasReport = any(
                selectReport(df, y, reportKind="annual") is not None
                for y in years[:1]
            )
            if not hasReport:
                noReport += 1
            failCodes.append((code, corpName, not hasReport))
        else:
            ok += 1

    total = len(codes) - spacCount
    print(f"=== SPAC 제외 커버리지 ===")
    print(f"전체: {len(codes)}, SPAC: {spacCount}, 대상: {total}")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}")
    print(f"  보고서없음: {noReport}")
    print(f"  기타: {fail - noReport}")

    print(f"\n실질 커버리지 (보고서있는 기업): {ok}/{total - noReport} ({ok/(total-noReport)*100:.1f}%)")

    if failCodes:
        print(f"\n실패 기업:")
        for code, name, noRep in failCodes:
            tag = "보고서없음" if noRep else "파싱실패"
            print(f"  [{code}] {name} ({tag})")
