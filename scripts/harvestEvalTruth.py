"""personaCases.json의 groundTruthFacts를 finance 엔진에서 자동 채우기.

Usage::

    uv run python -X utf8 scripts/harvestEvalTruth.py
    uv run python -X utf8 scripts/harvestEvalTruth.py --dry-run
    uv run python -X utf8 scripts/harvestEvalTruth.py --severity critical,high
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / "src" / "dartlab" / "ai" / "eval" / "personaCases.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="groundTruthFacts harvester")
    parser.add_argument("--dry-run", action="store_true", help="추출 결과만 출력, 파일 미수정")
    parser.add_argument("--severity", default=None, help="필터 (comma-separated: critical,high)")
    parser.add_argument("--force", action="store_true", help="기존 facts가 있어도 덮어쓰기")
    args = parser.parse_args()

    severityFilter = set(args.severity.split(",")) if args.severity else None

    with open(CASES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", [])
    targetCases = []
    for case in cases:
        if not case.get("stockCode"):
            continue
        if severityFilter and case.get("severity", "medium") not in severityFilter:
            continue
        if not args.force and case.get("groundTruthFacts"):
            continue
        targetCases.append(case)

    if not targetCases:
        print("harvest 대상 케이스 없음.")
        return

    print(f"harvest 대상: {len(targetCases)}건")
    for c in targetCases:
        print(f"  [{c.get('severity', '?')}] {c['id']} — {c['question'][:40]}")

    # lazy import — Company 로드는 여기서부터
    from dartlab.ai.eval.truthHarvester import harvestBatch

    results = harvestBatch(targetCases)

    total = 0
    for caseId, facts in results.items():
        n = len(facts)
        total += n
        if n > 0:
            print(f"\n  {caseId}: {n}건")
            for f in facts[:5]:
                val = f["value"]
                if isinstance(val, (int, float)) and abs(val) >= 1e8:
                    display = f"{val / 1e8:,.0f}억"
                else:
                    display = f"{val:,.2f}" if isinstance(val, float) else str(val)
                print(f"    {f['label']} ({f['period']}): {display}")
            if n > 5:
                print(f"    ... +{n - 5}건")
        else:
            print(f"\n  {caseId}: 추출 없음")

    print(f"\n총 {total}건 추출")

    if args.dry_run:
        print("\n[dry-run] 파일 미수정")
        return

    # personaCases.json 업데이트
    caseMap = {c["id"]: c for c in cases}
    updated = 0
    for caseId, facts in results.items():
        if facts and caseId in caseMap:
            caseMap[caseId]["groundTruthFacts"] = facts
            updated += 1

    if updated > 0:
        data["truthAsOf"] = str(date.today())
        with open(CASES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\npersonaCases.json 업데이트: {updated}건 (truthAsOf: {date.today()})")
    else:
        print("\n업데이트할 케이스 없음")


if __name__ == "__main__":
    main()
