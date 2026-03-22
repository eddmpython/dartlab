"""
EDGAR 배치 학습 스크립트

실행: python -X utf8 -m core.edgar.scripts.batchLearner
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json
from pathlib import Path

from core.edgar.getEdgar.v1.ticker import TickerManager
from core.edgar.searchEdgar.finance.v1.search import FinanceSearch
from core.edgar.searchEdgar.finance.v1.synonymLearner import SynonymLearner


def autoClassify(tag):
    tagL = tag.lower()

    if "othercomprehensiveincome" in tagL:
        return "total_other_comprehensive_income"

    if "derivative" in tagL:
        if "asset" in tagL:
            return "derivative_assets_detail"
        if "liabilit" in tagL:
            return "derivative_liabilities_detail"
        return "derivative_other_detail"

    if "fairvalue" in tagL:
        return "fair_value_measurement_detail"

    if "lease" in tagL:
        if "liabilit" in tagL:
            return "other_noncurrent_liabilities"
        return "lease_investment_detail"

    if "sharebased" in tagL or "stockoption" in tagL:
        return "stock_option_detail"

    if "businesscombination" in tagL or "acquisition" in tagL:
        return "acquisition_detail"

    if "restructuring" in tagL:
        return "restructuring_detail"

    if "incometax" in tagL or "deferredtax" in tagL:
        if "expense" in tagL:
            return "income_tax_expense"
        return "deferred_tax_detail"

    if "heldtomaturity" in tagL:
        return "held_to_maturity_detail"

    if "availableforsale" in tagL:
        return "afs_securities_detail"

    if "equitymethod" in tagL:
        return "equity_method_investment_detail"

    if "securities" in tagL:
        return "securities_collateral_detail"

    if "debtinstrument" in tagL or "longtermdebt" in tagL:
        return "debt_instrument_detail"

    if "treasurystock" in tagL:
        return "treasury_stock_purchased"

    if "commonstock" in tagL or "preferredstock" in tagL:
        return "other_equity_adjustments"

    if "dividend" in tagL:
        return "dividends_declared"

    if "noncontrolling" in tagL or "minority" in tagL:
        return "nci_business_combination"

    if "pension" in tagL or "postretirement" in tagL:
        return "other_note_detail"

    if "goodwill" in tagL or "intangible" in tagL:
        return "acquisition_detail"

    if "impairment" in tagL:
        return "other_income_expense"

    if "gainloss" in tagL:
        return "other_income_expense"

    if "depreciation" in tagL or "amortization" in tagL:
        if "cashflow" in tagL or "operating" in tagL:
            return "depreciation_cf"
        return "depreciation_amortization"

    if "increasedecrease" in tagL:
        if "operating" in tagL:
            return "working_capital_changes"
        return "operating_cash_flow"

    if "proceedsfrom" in tagL:
        if "investing" in tagL:
            return "other_investing_activities"
        return "other_financing_activities"

    if "paymentsto" in tagL or "repayments" in tagL:
        if "debt" in tagL:
            return "debt_repayment"
        return "other_financing_activities"

    if "insurance" in tagL or "policyholder" in tagL:
        if "premium" in tagL or "revenue" in tagL:
            return "revenue"
        if "claim" in tagL or "benefit" in tagL:
            return "other_income_expense"
        return "other_noncurrent_liabilities"

    if "loan" in tagL:
        if "provision" in tagL or "allowance" in tagL:
            return "bad_debt_provision"
        return "notes_loans_receivable_current"

    if "regulatory" in tagL:
        if "asset" in tagL:
            return "other_noncurrent_assets"
        return "other_note_detail"

    if "asset" in tagL:
        if "current" in tagL and "noncurrent" not in tagL:
            return "other_current_assets"
        return "other_noncurrent_assets"

    if "liabilit" in tagL:
        if "current" in tagL and "noncurrent" not in tagL:
            return "current_liabilities"
        return "other_noncurrent_liabilities"

    if "revenue" in tagL:
        return "revenue"

    if "expense" in tagL or "cost" in tagL:
        if "operating" in tagL:
            return "operating_expenses"
        return "other_income_expense"

    return "other_note_detail"


def runBatchLearning(batchSize=50, maxBatches=None):
    print("=" * 70)
    print("EDGAR 배치 학습 시작")
    print("=" * 70)

    tickerMgr = TickerManager()
    allTickers = tickerMgr.getTickers()["ticker"].tolist()
    print(f"\n전체 티커: {len(allTickers):,}개")

    cacheFile = Path(__file__).parent.parent / "learnedTickers.json"
    if cacheFile.exists():
        with open(cacheFile, "r", encoding="utf-8") as f:
            learnedSet = set(json.load(f))
        print(f"기존 학습: {len(learnedSet):,}개")
    else:
        learnedSet = set()
        print("새로운 학습 시작")

    remaining = [t for t in allTickers if t not in learnedSet]
    print(f"남은 작업: {len(remaining):,}개")

    if len(remaining) == 0:
        print("\n모든 티커 학습 완료!")
        return

    search = FinanceSearch()
    learner = SynonymLearner()

    totalBatches = (len(remaining) + batchSize - 1) // batchSize
    if maxBatches:
        totalBatches = min(totalBatches, maxBatches)

    print(f"\n배치 크기: {batchSize}개")
    print(f"예상 배치: {totalBatches}개")
    print("=" * 70)

    for batchIdx in range(totalBatches):
        start = batchIdx * batchSize
        end = start + batchSize
        batch = remaining[start:end]

        print(f"\n[배치 {batchIdx + 1}/{totalBatches}] {len(batch)}개 처리 중...")

        allNewTags = set()
        successCount = 0

        for ticker in batch:
            try:
                facts = search.getFacts(ticker)
                if facts is None or len(facts) < 50:
                    continue

                unmapped = facts.filter(facts["snakeId"].is_null())
                if len(unmapped) > 0:
                    tags = unmapped["tag"].unique().to_list()
                    allNewTags.update(tags)

                learnedSet.add(ticker)
                successCount += 1

            except Exception as e:
                print(f"  오류 ({ticker}): {e}")
                continue

        if allNewTags:
            print(f"  새 태그: {len(allNewTags)}개")
            for tag in allNewTags:
                learner.addTagMapping(tag, autoClassify(tag))
            learner.saveSynonyms()

            coverage = learner.getCoverage()
            print(f"  총 매핑: {coverage['learnedTagMappings']:,}개")

        print(f"  성공: {successCount}/{len(batch)}개")
        print(f"  누적: {len(learnedSet):,}개")

        if (batchIdx + 1) % 5 == 0 or (batchIdx + 1) == totalBatches:
            with open(cacheFile, "w", encoding="utf-8") as f:
                json.dump(sorted(list(learnedSet)), f, ensure_ascii=False, indent=2)
            print("  ✓ 캐시 저장 완료")

    with open(cacheFile, "w", encoding="utf-8") as f:
        json.dump(sorted(list(learnedSet)), f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("배치 학습 완료!")
    print(f"총 학습: {len(learnedSet):,}개")
    print(f"남은 작업: {len([t for t in allTickers if t not in learnedSet]):,}개")
    print("=" * 70)


if __name__ == "__main__":
    import sys

    batchSize = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    maxBatches = int(sys.argv[2]) if len(sys.argv) > 2 else None

    runBatchLearning(batchSize, maxBatches)
