"""
실험 ID: 012
실험명: equity 분리 매핑 + NCA 신뢰도 검증

목적:
- 011 진단에서 발견된 3가지 문제 해결:
  1. StockholdersEquity(parent) vs StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest(NCI포함)
     동일 snakeId 충돌 → equity_including_nci에 잘못된 값 (D1 오차)
  2. NoncurrentAssets가 전체 비유동이 아닌 부분 소계인 기업 (D4 오차)
  3. TemporaryEquity/RedeemableNCI가 BS 등식에서 누락 (D1 미세 오차)

가설:
1. SE_NCI를 equity_including_nci에, SE를 total_equity에 분리하면 D1 오차 해소
2. D4는 reported NCA vs derived NCA 중 큰 값(=derived)을 쓰면 해소
3. NCA 보고값 < derived의 80%이면 derived가 더 정확

방법:
1. standardAccounts.json에 equity_including_nci(BS) 항목 추가
2. total_equity에서 SE_NCI 제거, SE만 남김
3. EDGAR_TO_DART_ALIASES에서 total_equity→equity_including_nci 제거
4. _computeEquity 로직 조정 (이미 분리된 값 활용)
5. _computeDerived D4에서 reported < derived*0.8이면 derived 우선
6. 007 검증 실행

결과 (실험 후 작성):
- standardAccounts.json: total_equity에서 SE_NCI 제거, equity_including_nci(BS) 신규 추가
- mapper.py: EDGAR_TO_DART_ALIASES에서 total_equity→equity_including_nci 제거
- pivot.py _computeEquity: 양방향 파생 (eq_nci없으면 teq에서, teq없으면 eq_nci에서)
- 007 검증 결과:
  | Formula | 010 이후 | 012 이후 | 변화 |
  | D1 | 88.6% | 96.9% | +8.3pp |
  | D2 | 98.8% | 99.0% | +0.2pp |
  | D3 | 83.7% | 91.8% | +8.1pp |
  | D4 | 62.3% | 96.4% | +34.1pp |
  | D5 | 98.8% | 99.0% | +0.2pp |
- 개별 기업: NEE 9.8%→0.3%, KHC 0.5%→0.0%, TSLA 3.3%→0.1%, BKNG 0%→0%(유지)
- 테스트: 18/18 통과

결론:
- 가설 1 채택: SE_NCI 분리로 D1 96.9% 달성
- 가설 2 부분 채택: D4 96.4% 달성, 잔여 오차는 NoncurrentAssets 의미 불일치 (GOOG/TSLA/META)
- 잔여 D1 오차: TemporaryEquity(mezzanine equity) 미처리 — NEE 0.3%, TSLA 0.1% (수용 가능)
- 잔여 D4 오차: NoncurrentAssets ≠ Assets - CurrentAssets인 기업 — 향후 개선 대상

실험일: 2026-03-10
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"
MAPPER_DIR = PROJECT_ROOT / "src" / "dartlab" / "engines" / "edgar" / "finance" / "mapperData"


def phase1_verifyProblem():
    """현재 상태에서 SE vs SE_NCI 충돌 확인."""
    from dartlab.engines.company.edgar.finance.mapper import EdgarMapper

    se = EdgarMapper.mapToDart("StockholdersEquity", "BS")
    seNci = EdgarMapper.mapToDart(
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "BS"
    )
    print(f"StockholdersEquity -> {se}")
    print(f"StockholdersEquityIncl... -> {seNci}")
    print(f"충돌 여부: {se == seNci}")
    return se == seNci


def phase2_applySplit():
    """standardAccounts.json 수정: equity_including_nci 분리."""
    stdPath = MAPPER_DIR / "standardAccounts.json"
    with open(stdPath, encoding="utf-8") as f:
        data = json.load(f)

    modified = False

    for acct in data["accounts"]:
        if acct["snakeId"] == "total_equity" and acct["stmt"] == "BS":
            tags = acct.get("commonTags", [])
            seNciTag = "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"
            if seNciTag in tags:
                tags.remove(seNciTag)
                acct["commonTags"] = tags
                modified = True
                print(f"total_equity: SE_NCI 제거 -> {tags}")

    hasEqNci = any(
        a["snakeId"] == "equity_including_nci" and a["stmt"] == "BS"
        for a in data["accounts"]
    )

    if not hasEqNci:
        newAcct = {
            "snakeId": "equity_including_nci",
            "stmt": "BS",
            "commonTags": [
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            ],
        }
        eqIdx = next(
            i for i, a in enumerate(data["accounts"])
            if a["snakeId"] == "total_equity" and a["stmt"] == "BS"
        )
        data["accounts"].insert(eqIdx + 1, newAcct)
        modified = True
        print(f"equity_including_nci(BS) 항목 추가")

    if modified:
        with open(stdPath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("standardAccounts.json 저장 완료")
    else:
        print("이미 분리됨, 수정 불필요")


def phase3_verifyMapping():
    """수정 후 매핑 결과 확인 (mapper 재로드)."""
    from importlib import reload
    import dartlab.engines.company.edgar.finance.mapper as mapperMod
    reload(mapperMod)
    from dartlab.engines.company.edgar.finance.mapper import EdgarMapper

    EdgarMapper._tagMap = None
    EdgarMapper._stmtTagMap = None
    EdgarMapper._commonTags = None
    EdgarMapper._accounts = None

    se = EdgarMapper.mapToDart("StockholdersEquity", "BS")
    seNci = EdgarMapper.mapToDart(
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "BS"
    )
    print(f"StockholdersEquity -> {se}")
    print(f"StockholdersEquityIncl... -> {seNci}")
    print(f"분리 성공: {se != seNci}")
    return se != seNci


def phase4_testBuildTimeseries():
    """NEE, KHC, TSLA, META에서 D1/D4 검증."""
    from importlib import reload
    import dartlab.engines.company.edgar.finance.mapper as mapperMod
    import dartlab.engines.company.edgar.finance.pivot as pivotMod
    reload(mapperMod)
    reload(pivotMod)

    from dartlab.engines.company.edgar.finance.mapper import EdgarMapper
    EdgarMapper._tagMap = None
    EdgarMapper._stmtTagMap = None
    EdgarMapper._commonTags = None
    EdgarMapper._accounts = None

    from dartlab.engines.company.edgar.finance.pivot import buildTimeseries

    testCases = {
        "NEE": "0000753308",
        "KHC": "0001637459",
        "TSLA": "0001318605",
        "META": "0001326801",
    }

    for ticker, cik in sorted(testCases.items()):
        ts = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        if ts is None:
            print(f"{ticker}: buildTimeseries 실패")
            continue
        series, periods = ts
        bs = series["BS"]
        ta = bs.get("total_assets")
        eqNci = bs.get("equity_including_nci")
        tl = bs.get("total_liabilities")
        ca = bs.get("current_assets")
        nca = bs.get("non_current_assets")
        teq = bs.get("total_equity")

        print(f"\n=== {ticker} ({cik}) ===")
        print(
            f"  {'period':<10s} {'total_assets':>16s} {'eq_incl_nci':>16s} "
            f"{'total_eq':>16s} {'total_liab':>16s} {'D1_err':>8s} "
            f"{'cur_a':>16s} {'noncur_a':>16s} {'D4_derived':>16s} {'D4_err':>8s}"
        )
        for i, p in enumerate(periods[-8:]):
            j = len(periods) - 8 + i
            if j < 0:
                continue

            taV = ta[j] if ta else None
            eqV = eqNci[j] if eqNci else None
            tlV = tl[j] if tl else None
            caV = ca[j] if ca else None
            ncaV = nca[j] if nca else None
            teqV = teq[j] if teq else None

            if taV is None:
                continue

            d1 = (taV - eqV) if eqV is not None else None
            d4 = (taV - caV) if caV is not None else None

            d1err = ""
            if tlV is not None and d1 is not None and abs(tlV) > 0:
                d1err = f"{abs(d1-tlV)/abs(tlV)*100:.1f}%"

            d4err = ""
            if ncaV is not None and d4 is not None and abs(ncaV) > 0:
                d4err = f"{abs(d4-ncaV)/abs(ncaV)*100:.1f}%"

            def fmt(v):
                return f"{v:>16,.0f}" if v is not None else f"{'None':>16s}"

            print(
                f"  {p:<10s} {fmt(taV)} {fmt(eqV)} {fmt(teqV)} "
                f"{fmt(tlV)} {d1err:>8s} {fmt(caV)} {fmt(ncaV)} {fmt(d4)} {d4err:>8s}"
            )


if __name__ == "__main__":
    print("=" * 70)
    print("Phase 1: 현재 충돌 확인")
    print("=" * 70)
    hasConflict = phase1_verifyProblem()

    if hasConflict:
        print("\n" + "=" * 70)
        print("Phase 2: standardAccounts.json equity 분리")
        print("=" * 70)
        phase2_applySplit()

    print("\n" + "=" * 70)
    print("Phase 3: 수정 후 매핑 검증")
    print("=" * 70)
    phase3_verifyMapping()

    print("\n" + "=" * 70)
    print("Phase 4: buildTimeseries D1/D4 검증")
    print("=" * 70)
    phase4_testBuildTimeseries()

    print("\n" + "=" * 70)
    print("완료.")
    print("=" * 70)
