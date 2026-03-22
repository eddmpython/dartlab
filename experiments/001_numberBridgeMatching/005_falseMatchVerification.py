"""
실험 ID: 001-005
실험명: 오매칭(False Match) 검증

목적:
- 숫자 브릿지 매칭에서 우연한 숫자 일치로 잘못 매칭된 쌍의 비율을 측정
- 1차 정확 매칭(숫자 동일)의 신뢰도를 정량화

가설:
1. 1차 정확 매칭 쌍의 95%+ 는 이름이 동일하거나 유사 (유사도 0.6+)
2. 전전기 교차 검증(N년 전전기 == N-2년 당기)으로 독립 확인 시 90%+ 일치
3. 오매칭의 대부분은 금액이 0이거나 동일한 소액 항목에서 발생

방법:
1. 1차 정확 매칭만 별도 추출 (numberBridgeMatch 내부를 분리)
2. 검증 A: 이름 일치율 — 매칭 쌍의 이름 유사도 분포
3. 검증 B: 전전기 교차 — N년 전전기(idx=2) vs N-2년 당기(idx=0) 일치율
4. 검증 C: 오매칭 유형 분류 — 이름 완전 불일치인 쌍의 원인 분석
5. 전체 5개 기업 × 전 연도에 적용

결과 (K-IFRS 2011~2025, 5개 기업):
- 총 1차 정확 매칭 쌍: 1,465개

[검증 A] 이름 일치율:
  이름 완전 일치 (1.0): 1,440개 (98.3%)
  높은 유사도 (0.8+): 1,443개 (98.5%)
  의심 오매칭 (<0.3): 4개 (0.3%)

[검증 B] 전전기 교차 검증:
  교차 검증 통과율: 99.8% (1,194/1,196)
  모순율: 0.2% (2/1,196)

[검증 C] 의심 오매칭 유형:
  총 4건 중:
  - 하위항목 명칭변경(ㆍ): 1건 (관계기업투자→지분법적용투자, SK하이닉스)
  - 계정체계 변경: 2건 (기타자본구성요소↔자기주식, [소유주지분]↔자본총계, 동화약품)
  - 진짜 오매칭: 1건 (지배기업의소유주지분↔총포괄손익, 동화약품 2019↔2018)

[심층 분석] 의심 4건 → 실제 오매칭 1건:
  - 기타자본구성요소↔자기주식: 명칭변경 (정당)
  - [소유주지분]↔자본총계: 비지배지분 없는 회사에서 동일 개념 (정당)
  - 관계기업투자↔지분법적용투자: 명칭변경 (정당)
  - 지배기업소유주지분↔총포괄손익: 우연한 금액 일치 (진짜 오매칭)

결론:
- 가설1 채택: 이름 일치율 98.5% (0.8+ 기준), 95% 초과
- 가설2 채택: 교차 검증 통과율 99.8%, 90% 초과
- 가설3 부분채택: 오매칭은 제로/소액이 아닌, 계정 체계 변경 경계에서 발생
- 1차 정확 매칭 진짜 오매칭률: 0.07% (1/1,465)
- 숫자 브릿지 매칭의 신뢰도 99.93% 확인

실험일: 2026-03-06
"""

import io
import re
import sys
from collections import defaultdict
from pathlib import Path

import polars as pl

# Windows 콘솔 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 004에서 공유 함수 import
from importlib.util import module_from_spec, spec_from_file_location

spec = spec_from_file_location("pipeline", Path(__file__).parent / "004_fullPipeline.py")
pipeline = module_from_spec(spec)
spec.loader.exec_module(pipeline)

selectReport = pipeline.selectReport
extractSummaryContent = pipeline.extractSummaryContent
extractAccounts = pipeline.extractAccounts
nameSimilarity = pipeline.nameSimilarity
loadCompanyData = pipeline.loadCompanyData

DATA_DIR = Path("data/docsData")

COMPANY_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "001200": "유진증권",
    "000020": "동화약품",
    "000040": "KR모터스",
}


# ─── 검증용 매칭 함수 (1차 정확 매칭만, 상세 정보 반환) ───

def exactMatchWithDetail(accCur, accPrev):
    """1차 정확 매칭만 수행. 각 쌍의 이름, 금액, 유사도를 상세 반환.

    Returns:
        pairs: [(nameCur, namePrev, amtCur_prev, amtPrev_cur, nameSim)]
        unmatched: [nameCur] - 1차에서 매칭 안 된 항목
    """
    pairs = []
    unmatched = []
    usedPrev = set()

    for nameCur, amtsCur in accCur.items():
        if len(amtsCur) < 2 or amtsCur[1] is None:
            continue

        prevAmt = amtsCur[1]  # N년의 전기

        candidates = []
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            if abs(prevAmt - amtsPrev[0]) < 0.5:
                sim = nameSimilarity(nameCur, namePrev)
                candidates.append((namePrev, amtsPrev[0], sim))

        if candidates:
            candidates.sort(key=lambda x: -x[2])
            bestPrev, bestAmt, bestSim = candidates[0]
            pairs.append((nameCur, bestPrev, prevAmt, bestAmt, bestSim))
            usedPrev.add(bestPrev)
        else:
            unmatched.append(nameCur)

    return pairs, unmatched


# ─── 검증 A: 이름 일치율 분석 ───

def verifyNameConsistency(allPairs):
    """매칭 쌍의 이름 유사도 분포 분석."""
    if not allPairs:
        return {}

    sims = [p[4] for p in allPairs]
    exact = sum(1 for s in sims if s == 1.0)
    high = sum(1 for s in sims if 0.8 <= s < 1.0)
    medium = sum(1 for s in sims if 0.6 <= s < 0.8)
    low = sum(1 for s in sims if 0.3 <= s < 0.6)
    zero = sum(1 for s in sims if s < 0.3)
    total = len(sims)

    return {
        "total": total,
        "exact_name": exact,
        "high_sim": high,
        "medium_sim": medium,
        "low_sim": low,
        "zero_sim": zero,
        "name_match_rate": (exact + high) / total if total > 0 else 0,
        "suspicious_rate": zero / total if total > 0 else 0,
    }


# ─── 검증 B: 전전기 교차 검증 ───

def crossValidateWithPrevPrev(yearData, sortedYears):
    """전전기 교차 검증: N년 전전기(idx=2) == N-2년 당기(idx=0).

    1차 매칭과 독립적으로, 전전기 경로가 같은 결론을 내는지 확인.
    """
    results = []

    for i in range(len(sortedYears) - 2):
        curYear = sortedYears[i]
        prevYear = sortedYears[i + 1]
        ppYear = sortedYears[i + 2]

        accCur = yearData[curYear][0]
        accPrev = yearData[prevYear][0]
        accPP = yearData[ppYear][0]

        # 1차 매칭으로 N년↔N-1년 쌍 생성
        pairs, _ = exactMatchWithDetail(accCur, accPrev)

        # 교차 검증: 이 쌍에서 N년의 전전기(idx=2)가 N-2년 당기(idx=0)와 일치하는지
        verified = 0
        notVerifiable = 0  # 전전기 데이터가 없어서 검증 불가
        contradicted = 0   # 전전기 경로로 다른 계정에 매칭됨
        consistent = 0     # 전전기 경로로 같은 계열 계정에 매칭됨

        for nameCur, namePrev, _, _, _ in pairs:
            amtsCur = accCur[nameCur]
            if len(amtsCur) < 3 or amtsCur[2] is None:
                notVerifiable += 1
                continue

            ppAmt = amtsCur[2]  # N년의 전전기

            # N-2년 당기에서 이 금액 찾기
            ppMatches = []
            for namePP, amtsPP in accPP.items():
                if len(amtsPP) < 1 or amtsPP[0] is None:
                    continue
                if abs(ppAmt - amtsPP[0]) < 0.5:
                    ppMatches.append(namePP)

            if not ppMatches:
                notVerifiable += 1
                continue

            # N-1년에서도 전전기(idx=2) 경로로 N-2년 매칭 확인
            amtsPrev = accPrev.get(namePrev, [])
            if len(amtsPrev) < 2 or amtsPrev[1] is None:
                # N-1년의 전기가 없으면, N-2년 이름 직접 비교
                # N년→N-1년 쌍의 namePrev와, N년→N-2년 쌍의 ppMatch가 유사한지
                simMax = max(nameSimilarity(namePrev, ppN) for ppN in ppMatches)
                if simMax >= 0.6:
                    consistent += 1
                else:
                    contradicted += 1
                continue

            prevPrevAmt = amtsPrev[1]  # N-1년의 전기
            # N-1년 전기 == N-2년 당기?
            prevPPMatches = []
            for namePP, amtsPP in accPP.items():
                if len(amtsPP) < 1 or amtsPP[0] is None:
                    continue
                if abs(prevPrevAmt - amtsPP[0]) < 0.5:
                    prevPPMatches.append(namePP)

            if not prevPPMatches:
                notVerifiable += 1
                continue

            # 두 경로가 같은 N-2 계정을 가리키는지
            overlap = set(ppMatches) & set(prevPPMatches)
            if overlap:
                verified += 1
            else:
                # 다른 계정을 가리키지만, 유사도 확인
                simMax = 0
                for pp1 in ppMatches:
                    for pp2 in prevPPMatches:
                        simMax = max(simMax, nameSimilarity(pp1, pp2))
                if simMax >= 0.6:
                    consistent += 1
                else:
                    contradicted += 1

        total = verified + consistent + contradicted
        results.append({
            "curYear": curYear,
            "prevYear": prevYear,
            "ppYear": ppYear,
            "nPairs": len(pairs),
            "verified": verified,
            "consistent": consistent,
            "contradicted": contradicted,
            "notVerifiable": notVerifiable,
            "crossRate": (verified + consistent) / total if total > 0 else None,
        })

    return results


# ─── 검증 C: 오매칭 유형 분류 ───

def classifyFalseMatches(allPairs):
    """이름 유사도 0.3 미만 (의심 오매칭) 쌍의 유형 분류."""
    suspicious = [(nc, np, amt, amtP, sim) for nc, np, amt, amtP, sim in allPairs if sim < 0.3]

    categories = defaultdict(list)
    for nameCur, namePrev, amt, _, sim in suspicious:
        if amt == 0 or (amt is not None and abs(amt) < 1):
            categories["zero_amount"].append((nameCur, namePrev, amt, sim))
        elif "주당" in nameCur or "주당" in namePrev:
            categories["eps_collision"].append((nameCur, namePrev, amt, sim))
        elif "회사" in nameCur or "회사" in namePrev:
            categories["company_count"].append((nameCur, namePrev, amt, sim))
        elif "ㆍ" in nameCur or "ㆍ" in namePrev:
            # 하위 항목 (ㆍ매출액 등)
            categories["sub_item"].append((nameCur, namePrev, amt, sim))
        else:
            categories["genuine_false"].append((nameCur, namePrev, amt, sim))

    return suspicious, categories


# ─── 금액 분포별 오매칭률 ───

def analyzeByAmountRange(allPairs):
    """금액 범위별 오매칭(이름 유사도 < 0.3) 비율."""
    ranges = [
        ("0 (제로)", lambda a: a == 0 or (a is not None and abs(a) < 1)),
        ("1~1,000", lambda a: a is not None and 1 <= abs(a) < 1000),
        ("1,000~100만", lambda a: a is not None and 1000 <= abs(a) < 1_000_000),
        ("100만~1억", lambda a: a is not None and 1_000_000 <= abs(a) < 100_000_000),
        ("1억+", lambda a: a is not None and abs(a) >= 100_000_000),
    ]

    results = []
    for label, cond in ranges:
        inRange = [(nc, np, amt, amtP, sim) for nc, np, amt, amtP, sim in allPairs if cond(amt)]
        if not inRange:
            results.append((label, 0, 0, 0, 0))
            continue
        total = len(inRange)
        suspicious = sum(1 for _, _, _, _, s in inRange if s < 0.3)
        nameMatch = sum(1 for _, _, _, _, s in inRange if s == 1.0)
        results.append((label, total, nameMatch, suspicious, suspicious / total if total > 0 else 0))

    return results


# ─── 메인 실행 ───

def main():
    print("=" * 60)
    print("005: 오매칭(False Match) 검증")
    print("=" * 60)

    parquetFiles = sorted(DATA_DIR.glob("*.parquet"))
    print(f"\n대상 파일: {len(parquetFiles)}개\n")

    globalPairs = []       # 모든 기업의 모든 1차 매칭 쌍
    globalCrossResults = []  # 모든 기업의 교차 검증 결과

    for filepath in parquetFiles:
        code = filepath.stem
        name = COMPANY_NAMES.get(code, code)
        print(f"\n{'─' * 50}")
        print(f"[{code}] {name}")
        print(f"{'─' * 50}")

        yearData = loadCompanyData(filepath)
        sortedYears = sorted([y for y in yearData.keys() if int(y) >= 2011], reverse=True)

        if len(sortedYears) < 2:
            print("  연도 부족, 스킵")
            continue

        # 연도 쌍별 1차 정확 매칭
        companyPairs = []
        for i in range(len(sortedYears) - 1):
            curYear = sortedYears[i]
            prevYear = sortedYears[i + 1]
            accCur = yearData[curYear][0]
            accPrev = yearData[prevYear][0]

            pairs, unmatched = exactMatchWithDetail(accCur, accPrev)
            companyPairs.extend(pairs)

        print(f"  1차 정확 매칭 쌍: {len(companyPairs)}개")

        # ─── 검증 A: 이름 일치율 ───
        nameStats = verifyNameConsistency(companyPairs)
        print(f"\n  [검증 A] 이름 일치율:")
        print(f"    이름 완전 일치 (1.0): {nameStats['exact_name']}개 ({nameStats['exact_name']/nameStats['total']*100:.1f}%)")
        print(f"    높은 유사도 (0.8~1.0): {nameStats['high_sim']}개 ({nameStats['high_sim']/nameStats['total']*100:.1f}%)")
        print(f"    중간 유사도 (0.6~0.8): {nameStats['medium_sim']}개 ({nameStats['medium_sim']/nameStats['total']*100:.1f}%)")
        print(f"    낮은 유사도 (0.3~0.6): {nameStats['low_sim']}개 ({nameStats['low_sim']/nameStats['total']*100:.1f}%)")
        print(f"    의심 오매칭 (<0.3): {nameStats['zero_sim']}개 ({nameStats['zero_sim']/nameStats['total']*100:.1f}%)")
        print(f"    → 이름 매칭률 (0.8+): {nameStats['name_match_rate']:.1%}")
        print(f"    → 의심 오매칭률 (<0.3): {nameStats['suspicious_rate']:.1%}")

        # 의심 오매칭 상세 출력
        suspicious, categories = classifyFalseMatches(companyPairs)
        if suspicious:
            print(f"\n  [검증 C] 의심 오매칭 ({len(suspicious)}건) 상세:")
            for nc, np, amt, amtP, sim in suspicious[:10]:
                print(f"    '{nc}' ↔ '{np}'  금액={amt:,.0f}  유사도={sim:.2f}")
            if len(suspicious) > 10:
                print(f"    ... 외 {len(suspicious)-10}건")

            print(f"\n    유형 분류:")
            for cat, items in categories.items():
                catLabels = {
                    "zero_amount": "제로/소액",
                    "eps_collision": "EPS 충돌",
                    "company_count": "회사수",
                    "sub_item": "하위항목(ㆍ)",
                    "genuine_false": "실제 오매칭",
                }
                print(f"      {catLabels.get(cat, cat)}: {len(items)}건")

        # ─── 검증 B: 전전기 교차 검증 ───
        if len(sortedYears) >= 3:
            crossResults = crossValidateWithPrevPrev(yearData, sortedYears)
            globalCrossResults.extend(crossResults)

            totalVerified = sum(r["verified"] for r in crossResults)
            totalConsistent = sum(r["consistent"] for r in crossResults)
            totalContradicted = sum(r["contradicted"] for r in crossResults)
            totalNotVerifiable = sum(r["notVerifiable"] for r in crossResults)
            totalCheck = totalVerified + totalConsistent + totalContradicted

            print(f"\n  [검증 B] 전전기 교차 검증:")
            print(f"    검증됨 (두 경로 일치): {totalVerified}건")
            print(f"    일관됨 (유사 계정): {totalConsistent}건")
            print(f"    모순됨 (다른 계정): {totalContradicted}건")
            print(f"    검증불가 (데이터 없음): {totalNotVerifiable}건")
            if totalCheck > 0:
                crossRate = (totalVerified + totalConsistent) / totalCheck
                print(f"    → 교차 검증 통과율: {crossRate:.1%} ({totalVerified+totalConsistent}/{totalCheck})")

        globalPairs.extend(companyPairs)

    # ─── 전체 종합 ───
    print(f"\n\n{'=' * 60}")
    print("전체 종합 결과")
    print(f"{'=' * 60}")

    totalPairs = len(globalPairs)
    print(f"\n총 1차 정확 매칭 쌍: {totalPairs}개")

    # 이름 일치율 종합
    globalNameStats = verifyNameConsistency(globalPairs)
    print(f"\n[종합 A] 이름 일치율 분포:")
    print(f"  이름 완전 일치 (1.0): {globalNameStats['exact_name']}개 ({globalNameStats['exact_name']/totalPairs*100:.1f}%)")
    print(f"  높은 유사도 (0.8+): {globalNameStats['exact_name'] + globalNameStats['high_sim']}개 ({(globalNameStats['exact_name']+globalNameStats['high_sim'])/totalPairs*100:.1f}%)")
    print(f"  중간 유사도 (0.6~0.8): {globalNameStats['medium_sim']}개 ({globalNameStats['medium_sim']/totalPairs*100:.1f}%)")
    print(f"  낮은 유사도 (0.3~0.6): {globalNameStats['low_sim']}개 ({globalNameStats['low_sim']/totalPairs*100:.1f}%)")
    print(f"  의심 오매칭 (<0.3): {globalNameStats['zero_sim']}개 ({globalNameStats['zero_sim']/totalPairs*100:.1f}%)")
    print(f"  → 전체 이름 매칭률 (0.8+): {globalNameStats['name_match_rate']:.1%}")
    print(f"  → 전체 의심 오매칭률 (<0.3): {globalNameStats['suspicious_rate']:.1%}")

    # 교차 검증 종합
    if globalCrossResults:
        totalV = sum(r["verified"] for r in globalCrossResults)
        totalC = sum(r["consistent"] for r in globalCrossResults)
        totalX = sum(r["contradicted"] for r in globalCrossResults)
        totalNV = sum(r["notVerifiable"] for r in globalCrossResults)
        totalCheck = totalV + totalC + totalX

        print(f"\n[종합 B] 전전기 교차 검증:")
        print(f"  검증됨: {totalV}건, 일관됨: {totalC}건, 모순됨: {totalX}건, 불가: {totalNV}건")
        if totalCheck > 0:
            print(f"  → 교차 검증 통과율: {(totalV+totalC)/totalCheck:.1%} ({totalV+totalC}/{totalCheck})")
            print(f"  → 모순율: {totalX/totalCheck:.1%} ({totalX}/{totalCheck})")

    # 오매칭 유형 종합
    allSuspicious, allCategories = classifyFalseMatches(globalPairs)
    print(f"\n[종합 C] 의심 오매칭 유형 분류 (이름 유사도 < 0.3):")
    print(f"  총 {len(allSuspicious)}건 / {totalPairs}건 = {len(allSuspicious)/totalPairs*100:.2f}%")
    catLabels = {
        "zero_amount": "제로/소액",
        "eps_collision": "EPS 충돌",
        "company_count": "회사수",
        "sub_item": "하위항목(ㆍ)",
        "genuine_false": "실제 오매칭",
    }
    for cat in ["zero_amount", "eps_collision", "company_count", "sub_item", "genuine_false"]:
        items = allCategories.get(cat, [])
        print(f"    {catLabels[cat]}: {len(items)}건")

    # 금액 범위별 오매칭률
    amountResults = analyzeByAmountRange(globalPairs)
    print(f"\n[종합 D] 금액 범위별 분석:")
    print(f"  {'범위':<15} {'총 쌍':>6} {'이름일치':>8} {'의심':>6} {'오매칭률':>8}")
    print(f"  {'-'*45}")
    for label, total, nameMatch, sus, rate in amountResults:
        if total > 0:
            print(f"  {label:<15} {total:>6} {nameMatch:>8} {sus:>6} {rate:>7.1%}")

    # 실제 오매칭 전체 목록
    genuineFalse = allCategories.get("genuine_false", [])
    if genuineFalse:
        print(f"\n[상세] 실제 오매칭 후보 (이름 무관, 비특수항목) {len(genuineFalse)}건:")
        for nc, np, amt, sim in genuineFalse:
            print(f"  '{nc}' ↔ '{np}'  금액={amt:,.0f}  유사도={sim:.2f}")

    # 최종 판정
    print(f"\n{'=' * 60}")
    print("최종 판정")
    print(f"{'=' * 60}")

    genuineCount = len(allCategories.get("genuine_false", []))
    print(f"\n  1차 정확 매칭 신뢰도: {(totalPairs - genuineCount) / totalPairs:.1%}")
    print(f"  실제 오매칭 비율: {genuineCount / totalPairs:.2%} ({genuineCount}/{totalPairs})")
    if globalCrossResults:
        totalCheck2 = totalV + totalC + totalX
        if totalCheck2 > 0:
            print(f"  교차 검증 통과율: {(totalV+totalC)/totalCheck2:.1%}")
            print(f"  교차 검증 모순율: {totalX/totalCheck2:.1%}")


if __name__ == "__main__":
    main()
