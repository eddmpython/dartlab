"""전 종목 사업의 내용 추출 커버리지 테스트.

전 267종목에 extractSections 적용:
- 성공/실패 통계
- 각 섹션별 추출 성공률
- 엣지케이스 목록
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import polars as pl

from dartlab.core import buildIndex, loadData

sys.path.insert(0, "experiments/014_business")
import importlib

ext = importlib.import_module("002_sectionExtract")


idx = buildIndex()
codes = idx["stockCode"].to_list()

results = []
errors = []
sectionCounts = {}

for code in codes:
    try:
        result = ext.extractSections(code)
        if not result:
            errors.append((code, "empty result"))
            continue

        sections = result.get("sections", {})
        results.append({
            "code": code,
            "year": result["year"],
            "nSections": len(sections),
            "keys": sorted(sections.keys()),
        })

        for key in sections:
            sectionCounts[key] = sectionCounts.get(key, 0) + 1

    except Exception as e:
        errors.append((code, str(e)))


print("=" * 60)
print(f"전 종목 사업의 내용 추출 결과")
print("=" * 60)
print(f"총 종목: {len(codes)}")
print(f"성공: {len(results)}")
print(f"실패: {len(errors)}")

print(f"\n섹션별 추출 성공 수:")
for key, count in sorted(sectionCounts.items(), key=lambda x: -x[1]):
    pct = round(count / len(results) * 100, 1) if results else 0
    print(f"  {key}: {count}종목 ({pct}%)")

if errors:
    print(f"\n실패 종목:")
    for code, msg in errors:
        print(f"  {code}: {msg}")

noBiz = [r for r in results if r["nSections"] == 0]
if noBiz:
    print(f"\n섹션 0개 종목:")
    for r in noBiz:
        print(f"  {r['code']} ({r['year']})")

fewSections = [r for r in results if 0 < r["nSections"] <= 2]
if fewSections:
    print(f"\n섹션 1~2개 종목 (부분 추출):")
    for r in fewSections:
        print(f"  {r['code']} ({r['year']}): {r['keys']}")
