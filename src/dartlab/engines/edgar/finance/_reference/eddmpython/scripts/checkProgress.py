"""
EDGAR 학습 진행 상황 확인

실행: python -X utf8 -m core.edgar.scripts.checkProgress
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json
from pathlib import Path

from core.edgar.getEdgar.v1.ticker import TickerManager
from core.edgar.searchEdgar.finance.v1.synonymLearner import SynonymLearner


def checkProgress():
    print("=" * 70)
    print("EDGAR 학습 진행 상황")
    print("=" * 70)

    learner = SynonymLearner()
    coverage = learner.getCoverage()

    print("\n[매핑 통계]")
    print(f"  Tag Mappings: {coverage['learnedTagMappings']:,}개")
    print(f"  Plabel Mappings: {coverage.get('learnedPlabelMappings', 0):,}개")
    print(f"  표준계정: {coverage['standardAccounts']}개")

    tickerMgr = TickerManager()
    allTickers = tickerMgr.getTickers()["ticker"].tolist()
    totalTickers = len(allTickers)

    cacheFile = Path(__file__).parent.parent / "learnedTickers.json"
    if cacheFile.exists():
        with open(cacheFile, "r", encoding="utf-8") as f:
            learnedList = json.load(f)
        learnedCount = len(learnedList)
    else:
        learnedList = []
        learnedCount = 0

    print("\n[종목 커버리지]")
    print(f"  학습 완료: {learnedCount:,}개")
    print(f"  전체 종목: {totalTickers:,}개")
    print(f"  진행률: {learnedCount / totalTickers * 100:.2f}%")
    print(f"  남은 작업: {totalTickers - learnedCount:,}개")

    if learnedCount > 0:
        print("\n[최근 학습 종목 (최근 10개)]")
        for ticker in learnedList[-10:]:
            print(f"  - {ticker}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    checkProgress()
