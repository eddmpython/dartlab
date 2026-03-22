"""통합 추출 테스트 — 연결 우선, 별도 fallback.

현재 statements() pipeline:
  extractConsolidatedContent → "연결재무제표" 전용 → 161/267

개선 로직:
  1) "연결재무제표" 섹션 → 연결 추출 (scope="consolidated")
  2) 연결 없으면 "재무제표" 섹션 (비연결, 비주석) → 별도 추출 (scope="separate")
  3) 둘 다 없으면 None

전체 커버리지 측정.
"""

import os
import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractAccounts
from dartlab.finance.statements.extractor import splitStatements

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def extractContent(
    report: pl.DataFrame,
) -> tuple[str | None, str]:
    """연결 우선, 별도 fallback.

    Returns:
        (content, scope) — scope은 "consolidated" | "separate" | "none"
    """
    # 1) 연결재무제표
    cons = report.filter(
        pl.col("section_title").str.contains("연결재무제표")
        & ~pl.col("section_title").str.contains("주석")
    )
    if cons.height > 0:
        return cons["section_content"][0], "consolidated"

    # 2) 별도/개별 재무제표 (연결 아닌 재무제표)
    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"

    return None, "none"


def statementsUnified(
    stockCode: str,
    ifrsOnly: bool = True,
    period: str = "y",
) -> dict | None:
    """통합 추출 — 연결 우선, 별도 fallback."""
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

            content, scope = extractContent(report)
            if content is None:
                continue

            scopes.add(scope)
            parts = splitStatements(content)

            if period == "y":
                key = year
            else:
                continue  # 단순화

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

    consOk = 0       # 연결만으로 성공
    sepOk = 0        # 별도만으로 성공
    bothOk = 0       # 연결+별도 혼합 (연도에 따라)
    fail = 0
    err = 0

    failCodes = []

    for code in codes:
        try:
            r = statementsUnified(code)
            if r is None:
                fail += 1
                df = loadData(code)
                corpName = extractCorpName(df)
                failCodes.append((code, corpName))
            elif r["scopes"] == {"consolidated"}:
                consOk += 1
            elif r["scopes"] == {"separate"}:
                sepOk += 1
            else:
                bothOk += 1
        except Exception as e:
            err += 1
            print(f"[{code}] ERROR: {e}")

    total = len(codes)
    ok = consOk + sepOk + bothOk
    print(f"\n=== 통합 추출 결과 ===")
    print(f"총: {total}")
    print(f"성공: {ok} ({ok/total*100:.1f}%)")
    print(f"  연결만: {consOk}")
    print(f"  별도만: {sepOk}")
    print(f"  연결+별도 혼합: {bothOk}")
    print(f"실패: {fail}")
    print(f"에러: {err}")

    if failCodes:
        print(f"\n실패 기업 ({len(failCodes)}개):")
        for code, name in failCodes:
            print(f"  [{code}] {name}")
