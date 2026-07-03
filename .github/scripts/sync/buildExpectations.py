"""Thin shim : 기대치 격자 월/분기 사이클 진입점 (발행 → 채점 → 성적표 → HF push).

사이클 오케스트레이션은 in-library SSOT ``dartlab.simulate.expectationCycle`` 이 소유한다
(별도빌드 0 · 유일 기록자 = simulate). 본 스크립트는 CLI 계약(--cycle/--market/--push)만
보존하는 진입점이다. 원장 = append-only (mainPlan/expectation-grid/01 §4).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle", choices=["monthly", "quarterly"], default="monthly")
    parser.add_argument("--market", default="KR")
    parser.add_argument("--push", action="store_true", help="HF expectations/ surface 업로드")
    args = parser.parse_args()

    from dartlab.simulate.expectationCycle import buildScorecard, issueMacro, scoreDue
    from dartlab.simulate.expectationLedger import ledgerDir

    issued = []
    if args.cycle == "monthly":
        issued = issueMacro(market=args.market, live=True)
    # quarterly(매출·손익·credit) 발행은 P3~P5 에서 본 진입점에 합류한다.

    scores = scoreDue()
    card = buildScorecard()
    outDir = ledgerDir()
    outDir.mkdir(parents=True, exist_ok=True)
    (outDir / "scorecard.json").write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"[expectation-cycle] cycle={args.cycle} issued={len(issued)} scored={len(scores)} "
        f"errorRows={card['totals']['errorRows']} unscored={card['totals']['unscored']} dir={outDir}"
    )

    if args.push:
        from dartlab.pipeline.hfUpload import uploadCategoryToHf

        n = uploadCategoryToHf("expectations", fullUpload=True)
        print(f"[expectation-cycle] HF push 완료 files={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
