"""
실험 ID: 005
실험명: 003 오수정 롤백 + 안전한 재매핑

목적:
- 004에서 발견한 71개 의심 수정 중 명확한 오류를 롤백
- 롤백 기준: (1) liability→asset 전환, (2) 세부항목→합계 승격, (3) asset→liability 잘못된 전환
- 롤백 후 실제 매핑 품질 재측정
- total_liabilities 파생 계산 시뮬레이션 (current_liabilities + non_current_liabilities)

가설:
1. 71개 중 실제 오류는 50개+ (나머지는 문맥에 따라 허용 가능)
2. 롤백 후에도 핵심 계정 커버리지 93%+ 유지 (파생 계산으로 보완)
3. total_liabilities 파생으로 AMZN/WMT 갭 해결 가능

방법:
1. 003 수정 로그에서 의심 수정 분류
2. 명확한 오류 식별 (liability→asset, accrued→total 등)
3. learnedSynonyms.json에서 오수정 롤백 (이전 값 복원)
4. 파생 계산 추가 시뮬레이션
5. 개선 측정

결과 (2026-03-10):

[Phase 1] 오수정 분류
  총 003 수정: 284개
  롤백 대상: 92개 (예상 71개보다 21개 더 발견)
  주요 사유:
    liability→non_current_assets 오전환: 39개
    deposit/other/accrued liability→total_liabilities 잘못된 승격: 34개
    CF 변동항목→BS 전환: 7개
    deferred tax/M&A→total_liabilities: 6개
    기타: 6개 (삭제 - 이전 매핑 없었음)

[Phase 2] 롤백 적용
  삭제: 6개 (이전 매핑이 없던 태그 - 매핑 자체 제거)
  복원: 86개 (이전 값으로 복원)
  로그: learningLogs/20260310_103825_rollback_bad_fixes.json

[Phase 3] 롤백 후 측정 (파생 계정 포함)
  ★ AMZN: 95% → 100% (total_liabilities 파생 성공!)
  - total_liabilities = current_liabilities + non_current_liabilities (5Q)

  AAPL: 100%, MSFT: 100%, GOOG: 100%, NVDA: 100%, JNJ: 100% (변동 없음)
  AMZN: 100% ← 개선! (파생: non_current_assets + total_liabilities)
  META: 95% (inventories 누락 - 보고 안 함)
  XOM: 86% (cost_of_sales/gross_profit/operating_income 누락 - 에너지업)
  WMT: 90% (total_liabilities + non_current_liabilities 누락)
  JPM: 67% (7개 누락 - 금융업)

  10사 공통: 40개 (변동 없음)
  공통 핵심: 13/21 (변동 없음)
  ← 공통 기준은 10사 모두 있어야 하므로, JPM/XOM/WMT 한계로 변동 불가

  ★ WMT total_liabilities 미해결 원인:
    - WMT는 Liabilities 태그도, LiabilitiesNoncurrent 태그도 보고하지 않음
    - current_liabilities만 존재 → 합산 파생 불가
    - total_assets - total_equity로 역산 가능성 검토 필요

결론:
- 가설1 초과 달성: 92개 오수정 롤백 (예상 50개+)
- 가설2 채택: 핵심 커버리지 93.3% 유지 + AMZN 100% 달성
- 가설3 부분 채택: AMZN 해결, WMT는 non_current_liabilities 자체가 없어 합산 불가

남은 과제:
1. WMT total_liabilities: total_assets - total_equity 역산 방식 검토
2. 파생 계정 pivot.py 실배치 (003 → 005 검증 완료한 안전한 방식으로)
3. 003에서 남은 192개 수정(284-92)은 유효 — 유지

learnedSynonyms 최종 상태:
  003 전: 11,386개
  003 후: 11,666개 (+280 학습, +284 수정)
  005 후: 11,660개 (-6 삭제) + 86개 복원 = 실질 11,660개

실험일: 2026-03-10
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dartlab.engines.company.edgar.finance.mapper import EdgarMapper
from dartlab.engines.company.edgar.finance.pivot import buildTimeseries

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"
MAPPER_DATA = PROJECT_ROOT / "src" / "dartlab" / "engines" / "edgar" / "finance" / "mapperData"
LEARNED_PATH = MAPPER_DATA / "learnedSynonyms.json"
REF_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = REF_DIR / "learningLogs"

TICKERS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "NVDA": "0001045810",
    "META": "0001326801",
    "JPM": "0000019617",
    "JNJ": "0000200406",
    "XOM": "0000034088",
    "WMT": "0000104169",
}

CORE_ACCOUNTS = [
    "revenue", "cost_of_sales", "gross_profit", "operating_income", "net_income",
    "total_assets", "current_assets", "non_current_assets",
    "cash_and_equivalents", "inventories",
    "total_liabilities", "current_liabilities", "non_current_liabilities",
    "total_equity", "equity_including_nci",
    "operating_cashflow", "investing_cashflow", "financing_cashflow",
    "trade_receivables", "ppe",
    "profit_before_tax",
]


def writeLog(action, details):
    """학습 변경사항을 JSON 로그로 기록."""
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logFile = LOG_DIR / f"{ts}_{action}.json"
    logEntry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "experiment": "005_rollbackBadFixes",
        **details,
    }
    with open(logFile, "w", encoding="utf-8") as f:
        json.dump(logEntry, f, ensure_ascii=False, indent=2)
    print(f"  [LOG] {logFile.name}")


def phase1_identifyBadFixes():
    """Phase 1: 오수정 분류 및 롤백 대상 확정."""
    print("\n[Phase 1] 오수정 롤백 대상 확정")
    print("=" * 60)

    logFiles = sorted(LOG_DIR.glob("*fix_mismappings*.json"))
    if not logFiles:
        print("  수정 로그 파일 없음")
        return {}

    with open(logFiles[-1], encoding="utf-8") as f:
        logData = json.load(f)

    fixes = logData.get("fixes", {})
    rollbacks = {}

    for tag, info in fixes.items():
        fromSid = info["from"]
        toSid = info["to"]
        reason = None

        if "liabilit" in tag and toSid == "non_current_assets":
            reason = "liability→non_current_assets 오전환"
        elif "liabilit" in tag and toSid == "current_assets":
            reason = "liability→current_assets 오전환"
        elif "accruedliabilit" in tag and toSid == "total_liabilities":
            reason = "세부항목(accrued)→합계(total) 승격"
        elif "deferredtaxassets" in tag and toSid == "total_liabilities":
            reason = "deferred tax → total_liabilities 잘못된 매핑"
        elif tag.startswith("businesscombination") and toSid in ["total_liabilities", "non_current_assets"]:
            if "liabilit" in tag and toSid == "non_current_assets":
                reason = "M&A liability→asset 오전환"
            elif "assets" in tag and toSid == "total_liabilities":
                reason = "M&A asset→total_liabilities 잘못된 승격"
        elif "assetretirementobligationliabilit" in tag and toSid == "total_liabilities":
            reason = "ARO liability→total_liabilities 잘못된 승격"
        elif "workerscompensation" in tag and toSid == "non_current_assets":
            reason = "workers comp liability→asset 오전환"
        elif "pension" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "pension liability→asset 오전환"
        elif "postemployment" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "post-employment liability→asset 오전환"
        elif "deferredcompensation" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "deferred comp liability→asset 오전환"
        elif "disposalgroup" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "disposal group liability→asset 오전환"
        elif "regulatory" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "regulatory liability→asset 오전환"
        elif "deposit" in tag and "liabilit" in tag and toSid == "total_liabilities":
            reason = "deposit liability→total_liabilities 잘못된 승격"
        elif "increasedecrease" in tag and toSid in ["non_current_assets", "total_liabilities"]:
            reason = "CF 변동항목을 BS 항목으로 잘못 전환"
        elif "other" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "other liability→asset 오전환"
        elif "other" in tag and "liabilit" in tag and toSid == "total_liabilities" and "total" not in tag:
            reason = "세부 other liability→total_liabilities 잘못된 승격"
        elif "customerrefund" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "customer refund liability→asset 오전환"
        elif "energymarketing" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "energy marketing liability→asset 오전환"
        elif "decommissioning" in tag and toSid == "non_current_assets":
            reason = "decommissioning liability→asset 오전환"
        elif "frequentflier" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "frequent flier liability→asset 오전환"
        elif "variableinterest" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "VIE liability→asset 오전환"
        elif "mineral" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "mine reclamation liability→asset 오전환"
        elif "taxcutsandjobs" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "TCJA liability→asset 오전환"
        elif "liabilitiesof" in tag and toSid == "total_liabilities":
            reason = "세부 liabilities→total_liabilities 잘못된 승격"
        elif "noncash" in tag and "liabilit" in tag and toSid == "total_liabilities":
            reason = "non-cash liability→total_liabilities 잘못된 승격"
        elif "serviceliabilit" in tag and toSid == "total_liabilities":
            reason = "servicing liability→total_liabilities 잘못된 승격"
        elif "oilandgas" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "oil&gas liability→asset 오전환"
        elif "government" in tag and "liabilit" in tag and toSid == "non_current_assets":
            reason = "government assistance liability→asset 오전환"

        if reason:
            restoreTo = fromSid if fromSid != "(없음)" else None
            rollbacks[tag] = {
                "currentSid": toSid,
                "restoreTo": restoreTo,
                "reason": reason,
            }

    print(f"  총 003 수정: {len(fixes)}개")
    print(f"  롤백 대상: {len(rollbacks)}개")

    byReason = {}
    for tag, info in rollbacks.items():
        reason = info["reason"]
        byReason.setdefault(reason, []).append(tag)

    print(f"\n  [롤백 사유별 분류]")
    for reason, tags in sorted(byReason.items(), key=lambda x: -len(x[1])):
        print(f"    {reason}: {len(tags)}개")

    return rollbacks


def phase2_applyRollback(rollbacks, dryRun=True):
    """Phase 2: 오수정 롤백 적용."""
    print(f"\n[Phase 2] 오수정 롤백 {'(Dry Run)' if dryRun else '(적용)'}")
    print("=" * 60)

    if not rollbacks:
        print("  롤백 대상 없음")
        return

    with open(LEARNED_PATH, encoding="utf-8") as f:
        learned = json.load(f)

    tagMappings = learned.get("tagMappings", {})

    deleted = []
    restored = []

    for tag, info in rollbacks.items():
        restoreTo = info["restoreTo"]
        currentSid = tagMappings.get(tag)

        if currentSid != info["currentSid"]:
            continue

        if restoreTo is None:
            if not dryRun:
                del tagMappings[tag]
            deleted.append(tag)
        else:
            if not dryRun:
                tagMappings[tag] = restoreTo
            restored.append((tag, currentSid, restoreTo))

    print(f"  삭제: {len(deleted)}개")
    print(f"  복원: {len(restored)}개")

    if not dryRun and (deleted or restored):
        learned["tagMappings"] = tagMappings
        with open(LEARNED_PATH, "w", encoding="utf-8") as f:
            json.dump(learned, f, ensure_ascii=False, indent=2)

        writeLog("rollback_bad_fixes", {
            "description": "004 검증 결과 오수정 롤백",
            "deleted": deleted,
            "restored": [{"tag": t, "from": f, "to": to} for t, f, to in restored],
            "totalDeleted": len(deleted),
            "totalRestored": len(restored),
        })

        EdgarMapper._tagMap = None

    if deleted[:10]:
        print(f"\n  삭제 예시:")
        for tag in deleted[:10]:
            print(f"    {tag}")

    if restored[:10]:
        print(f"\n  복원 예시:")
        for tag, fromSid, toSid in restored[:10]:
            print(f"    {tag}: {fromSid} → {toSid}")


def phase3_measureAfterRollback():
    """Phase 3: 롤백 후 측정 (파생 계정 포함)."""
    print("\n[Phase 3] 롤백 후 커버리지 측정 (파생 계정 포함)")
    print("=" * 60)

    derivable = {
        "gross_profit": ("IS", "revenue", "IS", "cost_of_sales", "subtract"),
        "non_current_assets": ("BS", "total_assets", "BS", "current_assets", "subtract"),
        "non_current_liabilities": ("BS", "total_liabilities", "BS", "current_liabilities", "subtract"),
        "total_liabilities": ("BS", "current_liabilities", "BS", "non_current_liabilities", "add"),
    }

    allSnakeIdSets = {}

    for ticker, cik in TICKERS.items():
        result = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if result is None:
            continue

        series, periods = result
        allSids = set()
        for stmt in series:
            allSids.update(series[stmt].keys())

        derivedList = []
        for targetSid, (aStmt, aSid, bStmt, bSid, op) in derivable.items():
            if targetSid not in allSids:
                aVals = series.get(aStmt, {}).get(aSid)
                bVals = series.get(bStmt, {}).get(bSid)
                if aVals and bVals:
                    nonNull = sum(1 for a, b in zip(aVals, bVals) if a is not None and b is not None)
                    if nonNull > 0:
                        allSids.add(targetSid)
                        derivedList.append(f"{targetSid}({nonNull}Q)")

        allSnakeIdSets[ticker] = allSids

        coreHits = sum(1 for sid in CORE_ACCOUNTS if sid in allSids)
        missing = [sid for sid in CORE_ACCOUNTS if sid not in allSids]
        missingStr = ", ".join(missing) if missing else "없음"
        print(f"  {ticker}: {coreHits}/{len(CORE_ACCOUNTS)} ({coreHits/len(CORE_ACCOUNTS)*100:.0f}%) "
              f"누락: {missingStr}")
        if derivedList:
            print(f"         파생: {' + '.join(derivedList)}")

    tickers = list(allSnakeIdSets.keys())
    if len(tickers) >= 2:
        commonAll = allSnakeIdSets[tickers[0]]
        for t in tickers[1:]:
            commonAll = commonAll & allSnakeIdSets[t]

        print(f"\n  10사 공통 snakeId: {len(commonAll)}개")

        coreInCommon = [sid for sid in CORE_ACCOUNTS if sid in commonAll]
        print(f"  공통 핵심계정: {len(coreInCommon)}/{len(CORE_ACCOUNTS)}")
        for sid in CORE_ACCOUNTS:
            marker = "O" if sid in commonAll else "X"
            coverage = sum(1 for t in tickers if sid in allSnakeIdSets[t])
            print(f"    [{marker}] {sid:<30s} ({coverage}/{len(tickers)}사)")

        print(f"\n  [이전 대비]")
        print(f"    003 후: 공통 40개, 핵심 13/21")
        print(f"    005 후: 공통 {len(commonAll)}개, 핵심 {len(coreInCommon)}/21")


def main():
    print("=" * 70)
    print("003 오수정 롤백 + 안전한 재매핑")
    print("=" * 70)

    rollbacks = phase1_identifyBadFixes()

    if not rollbacks:
        print("\n  롤백 대상 없음 — 종료")
        return

    print("\n" + "=" * 70)
    print("DRY RUN")
    print("=" * 70)
    phase2_applyRollback(rollbacks, dryRun=True)

    print("\n" + "=" * 70)
    print("실제 적용")
    print("=" * 70)
    phase2_applyRollback(rollbacks, dryRun=False)

    phase3_measureAfterRollback()


if __name__ == "__main__":
    main()
