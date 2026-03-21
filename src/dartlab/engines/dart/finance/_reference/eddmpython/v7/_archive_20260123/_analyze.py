"""Analyze remaining stocks for unmapped accounts"""

import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from core.dart.searchDart.finance.v7.synonymLearner import SynonymLearner

learner = SynonymLearner()
fs = learner._getFinanceSearch()

allCodes = fs.lf.select("stock_code").unique().collect()["stock_code"].to_list()

with open(str(Path(__file__).parent / "quickCheck.py"), "r", encoding="utf-8") as f:
    content = f.read()
codes = re.findall(r"'(\d{6})'", content.split("COMPLETED")[1].split("]")[0])
completed = set(codes)

remaining = [c for c in allCodes if c not in completed]
print(f"Remaining: {len(remaining)}")

already100 = []
unmapped1 = []
unmapped2 = []

for code in remaining:
    r = learner.analyzeCompany(code)
    if r and r.totalAccounts > 0:
        if len(r.unmatched) == 0:
            already100.append((code, r.corpName))
        elif len(r.unmatched) == 1 and r.matchRate >= 97.0:
            unmapped1.append((code, r.corpName, r.matchRate, r.unmatched[0]))
        elif len(r.unmatched) == 2 and r.matchRate >= 97.0:
            unmapped2.append((code, r.corpName, r.matchRate, r.unmatched))

print(f"\nAlready 100%: {len(already100)}")
print(f"1 unmapped (>=97%): {len(unmapped1)}")
print(f"2 unmapped (>=97%): {len(unmapped2)}")

print("\n--- 1 unmapped accounts ---")
for code, name, rate, acc in sorted(unmapped1, key=lambda x: -x[2]):
    print(f"{code} {name}: {rate:.1f}% [{acc}]")

print("\n--- 2 unmapped (top 20) ---")
for code, name, rate, accs in sorted(unmapped2, key=lambda x: -x[2])[:20]:
    print(f"{code} {name}: {rate:.1f}% {accs}")

# Save already100 codes
with open(str(Path(__file__).parent / "_already100.json"), "w", encoding="utf-8") as f:
    json.dump(already100, f, ensure_ascii=False)

# Save unmapped
with open(str(Path(__file__).parent / "_unmapped.json"), "w", encoding="utf-8") as f:
    json.dump(
        {
            "unmapped1": unmapped1,
            "unmapped2": unmapped2,
        },
        f,
        ensure_ascii=False,
    )

print(f"\nSaved _already100.json ({len(already100)}) and _unmapped.json")
