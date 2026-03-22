"""전 종목 회사의 개요 파싱 커버리지 테스트."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import polars as pl

from dartlab.core import buildIndex, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport

sys.path.insert(0, "experiments/015_companyOverview")
import importlib

ext = importlib.import_module("002_parseFields")


idx = buildIndex()
codes = idx["stockCode"].to_list()

fieldCounts = {}
results = []
errors = []

for code in codes:
    try:
        df = loadData(code)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        parsed = None
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
                continue

            text = overviewRow.row(0, named=True)["section_content"]
            parsed = ext.parseOverview(text)
            reportYear = extractReportYear(overviewRow["report_type"][0])
            break

        if parsed is None:
            errors.append((code, "no overview section"))
            continue

        results.append({"code": code, "year": reportYear, "fields": parsed})
        for key in parsed:
            fieldCounts[key] = fieldCounts.get(key, 0) + 1

    except Exception as e:
        errors.append((code, str(e)))


print("=" * 60)
print("전 종목 회사의 개요 파싱 결과")
print("=" * 60)
print(f"총 종목: {len(codes)}")
print(f"파싱 성공: {len(results)}")
print(f"실패/없음: {len(errors)}")

print(f"\n필드별 추출 성공 수:")
for key, count in sorted(fieldCounts.items(), key=lambda x: -x[1]):
    pct = round(count / len(results) * 100, 1) if results else 0
    print(f"  {key}: {count}종목 ({pct}%)")

noFounded = [r for r in results if "founded" not in r["fields"]]
if noFounded:
    print(f"\nfounded 없는 종목: {len(noFounded)}")
    for r in noFounded[:10]:
        print(f"  {r['code']}")

noAddress = [r for r in results if "address" not in r["fields"]]
if noAddress:
    print(f"\naddress 없는 종목: {len(noAddress)}")
    for r in noAddress[:10]:
        print(f"  {r['code']}")

if errors:
    print(f"\n실패 종목:")
    for code, msg in errors[:20]:
        print(f"  {code}: {msg}")
