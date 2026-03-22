"""개선된 로직으로 전체 커버리지 최종 측정.

개선 사항:
1. splitStatements: 공백 제거 후 패턴 매칭
2. extractContent: "연결대상이 없어" → 별도 fallback
3. 연결 우선, 별도 fallback
"""

import os
import re
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, extractCorpName, loadData
from dartlab.core.reportSelector import parsePeriodKey, selectReport
from dartlab.core.tableParser import extractAccounts

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

# --- 개선된 함수들 ---

_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "PNL": r"손익계산서",
    "CI": r"포괄손익",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}


def splitStatementsV2(content: str) -> dict[str, str]:
    """개선된 splitStatements — 공백 포함 패턴 지원."""
    lines = content.split("\n")

    headers: list[tuple[int, str]] = []
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

    seen: dict[str, int] = {}
    uniqueHeaders: list[tuple[int, str]] = []
    for idx, key in headers:
        if key in seen:
            uniqueHeaders[seen[key]] = (idx, key)
        else:
            seen[key] = len(uniqueHeaders)
            uniqueHeaders.append((idx, key))

    result: dict[str, str] = {}
    for j, (startIdx, key) in enumerate(uniqueHeaders):
        if j + 1 < len(uniqueHeaders):
            endIdx = uniqueHeaders[j + 1][0]
        else:
            endIdx = len(lines)
        result[key] = "\n".join(lines[startIdx:endIdx])

    return result


def extractContentV2(report: pl.DataFrame) -> tuple[str | None, str]:
    """연결 우선, 별도 fallback (연결대상없음 처리 포함)."""
    cons = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & ~pl.col("section_title").str.contains("주석")
    )
    if cons.height > 0:
        content = cons["section_content"][0]
        if "연결대상" in content and ("없어" in content or "없으므로" in content):
            pass  # fallback to separate
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


def statementsV2(
    stockCode: str,
    ifrsOnly: bool = True,
    period: str = "y",
) -> dict | None:
    """개선된 statements."""
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    years = sorted(df["year"].unique().to_list(), reverse=True)

    bsData = {}
    isData = {}
    cfData = {}
    scopes = set()

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            content, scope = extractContentV2(report)
            if content is None:
                continue

            scopes.add(scope)
            parts = splitStatementsV2(content)

            if period == "y":
                key = year
            else:
                reportType = report["report_type"][0]
                key = parsePeriodKey(reportType)
                if key is None:
                    continue

            if ifrsOnly and int(key[:4]) < 2011:
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
        return None

    return {
        "corpName": corpName,
        "nYears": len(set(bsData) | set(isData) | set(cfData)),
        "scopes": scopes,
        "bsKeys": len(bsData),
        "isKeys": len(isData),
        "cfKeys": len(cfData),
    }


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    consOk = 0
    sepOk = 0
    bothOk = 0
    fail = 0
    err = 0

    failCodes = []
    results = []

    for code in codes:
        try:
            r = statementsV2(code)
            if r is None:
                fail += 1
                df = loadData(code)
                corpName = extractCorpName(df)
                failCodes.append((code, corpName))
            else:
                if r["scopes"] == {"consolidated"}:
                    consOk += 1
                elif r["scopes"] == {"separate"}:
                    sepOk += 1
                else:
                    bothOk += 1
                results.append(r)
        except Exception as e:
            err += 1
            print(f"[{code}] ERROR: {e}")

    total = len(codes)
    ok = consOk + sepOk + bothOk
    print(f"\n=== 최종 커버리지 (개선 후) ===")
    print(f"총: {total}")
    print(f"성공: {ok} ({ok/total*100:.1f}%)")
    print(f"  연결만: {consOk}")
    print(f"  별도만: {sepOk}")
    print(f"  연결+별도 혼합: {bothOk}")
    print(f"실패: {fail}")
    print(f"에러: {err}")

    # 연도 수 분포
    if results:
        nYears = [r["nYears"] for r in results]
        print(f"\n연도 수 분포:")
        print(f"  평균: {sum(nYears)/len(nYears):.1f}")
        print(f"  최소: {min(nYears)}, 최대: {max(nYears)}")

    if failCodes:
        print(f"\n실패 기업 ({len(failCodes)}개):")
        for code, name in failCodes[:30]:
            print(f"  [{code}] {name}")

    # 기존 대비 개선
    print(f"\n=== 기존 대비 개선 ===")
    print(f"기존 statements(): 161/267 (60.3%)")
    print(f"개선 후: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"순증: +{ok - 161}개")
