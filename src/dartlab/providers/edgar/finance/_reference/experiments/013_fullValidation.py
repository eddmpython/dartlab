"""
실험 ID: 013
실험명: 전체 CIK 파생 계정 정확도 검증

목적:
- 012까지의 개선이 S&P 100이 아닌 전체 16,601 CIK에서도 유효한지 검증
- 기업별 D1~D5 오차를 전수 스캔하여 잔존 문제 파악
- ≤1% 정확도, >5% 오류 기업 목록, 오차 분포 파악

가설:
1. S&P 100에서 96%+ 달성한 D1/D4가 전체에서도 90%+ 유지
2. 소규모/특수 기업에서 추가 오매핑 패턴이 발견될 수 있음

방법:
1. 16,601 CIK 전수 buildTimeseries → D1~D5 정확도 계산
2. 오차 ≤1%, ≤5%, >5% 분포 + >10% 기업 목록
3. 공식별 오차 패턴 분류

결과 (실험 후 작성):

Phase 1: 012 결과 그대로 2000 샘플 검증 (mezzanine fix 전)
| D1 93.3% | D2 98.9% | D3 90.6% | D4 95.5% | D5 98.7% |

- D1 >10% 분석: 192/1000사 중 176사(92%)가 gap>0 (equity undercount)
- 145사(76%)가 NCI 없음 → TemporaryEquity/mezzanine equity가 주범
- TemporaryEquityCarryingAmountAttributableToParent가 2,561 CIK에서 사용되나 미매핑

Phase 2: mezzanine equity 반영
- _computeEquity()에 redeemable_noncontrolling_interest를 equity_including_nci에 합산
- Assets = Liabilities + Equity + MezzanineEquity 항등식 반영
- sanity check: merged > total_assets이면 합산 안 함 (SPAC trust 이상치 방지)
- standardAccounts.json commonTags에 2개 태그 추가:
  - TemporaryEquityCarryingAmountAttributableToParent (2,561 CIK)
  - TemporaryEquityValueExcludingAdditionalPaidInCapital (243 CIK)

Phase 3: 최종 2000 샘플 검증 (mezzanine fix 후)
| D1 95.7% | D2 99.0% | D3 91.1% | D4 95.5% | D5 98.7% |

D1 개선: 93.3% → 95.7% (+2.4%p)
남은 >10% 오류 (2.6%): 합병 과도기(KHC 2015), SPAC trust 이상, 데이터 품질 문제

S&P 100 vs 전체 CIK 비교:
| D1 | S&P100: 96.9% | 전체: 95.7% | 차이 -1.2%p |
| D2 | S&P100: 99.0% | 전체: 99.0% | 차이 0.0%p  |
| D3 | S&P100: 91.8% | 전체: 91.1% | 차이 -0.7%p |
| D4 | S&P100: 96.4% | 전체: 95.5% | 차이 -0.9%p |
| D5 | S&P100: 99.0% | 전체: 98.7% | 차이 -0.3%p |

Phase 4: >10% 오류 기업 전수 개별 진단 (2000 샘플)

D1 >10%: 238개 기업 원인 분류
| 분류             | 수  | 비율 | 매핑 해결? |
| A.음수부채(원본오류) |   2 |  1% | 불가      |
| B.미매핑equity태그 |   0 |  0% | —        |
| C.multiEnd mixing |  71 | 30% | pivot 로직 |
| D.극소기업(<10M)  |  23 | 10% | 무시      |
| E.거대gap(>50%A)  | 142 | 60% | 불가      |

D2~D5 >10% 원인:
| 공식 | >10%수 | multiEnd | Q4역산 | 매핑문제 |
| D2   |   31  | 100%     |  0%   |   0    |
| D3   |  283  |  34%     | 66%   |   0    |
| D4   |   93  | 100%     |  0%   |   0    |
| D5   |   36  | 100%     |  0%   |   0    |

핵심: 미매핑 equity 태그 = 0, 매핑 데이터 수정 대상 = 0
D2/D4/D5는 100% majorityEnd cross-period mixing
D3은 66% Q4 역산(YTD 혼입), 34% multiEnd

결론:
- 가설 1 채택: D1 95.7%, D4 95.5%로 전체에서도 95%+ 달성 (목표 90% 초과)
- 가설 2 채택: SPAC/shell company에서 TemporaryEquity 미매핑 발견 → 2,561 CIK 태그 추가로 해결
- S&P 100과 전체 CIK 간 차이가 1~2%p 이내로 일관적
- **매핑 데이터(learnedSynonyms/standardAccounts)는 완벽** — 수정 대상 0건
- 남은 오류 원인: (1) _selectBS() majorityEnd한계, (2) _computeQ4() YTD혼입, (3) 원본 데이터 품질
- 추가 개선은 pivot.py 로직 개선(별도 실험) 또는 데이터 품질 필터링 필요

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"

FORMULAS = [
    ("D1", "BS", "total_liabilities", "total_assets", "equity_including_nci", "subtract"),
    ("D2", "BS", "total_liabilities", "current_liabilities", "non_current_liabilities", "add"),
    ("D3", "IS", "gross_profit", "revenue", "cost_of_sales", "subtract"),
    ("D4", "BS", "non_current_assets", "total_assets", "current_assets", "subtract"),
    ("D5", "BS", "non_current_liabilities", "total_liabilities", "current_liabilities", "subtract"),
]


def validateAll():
    from dartlab.providers.edgar.finance.pivot import buildTimeseries

    parquetFiles = sorted(EDGAR_DIR.glob("*.parquet"))
    total = len(parquetFiles)
    print(f"전체 CIK: {total}개")
    print()

    stats: dict[str, dict] = {}
    for fid, (label, *_) in enumerate(FORMULAS):
        stats[label] = {
            "total_points": 0,
            "le1": 0,
            "le5": 0,
            "gt5": 0,
            "gt10": 0,
            "gt10_companies": [],
            "companies_checked": 0,
            "errors": [],
        }

    loaded = 0
    failed = 0
    t0 = time.time()

    for idx, pf in enumerate(parquetFiles):
        cik = pf.stem
        if (idx + 1) % 2000 == 0:
            elapsed = time.time() - t0
            rate = (idx + 1) / elapsed
            eta = (total - idx - 1) / rate
            print(f"  진행: {idx+1}/{total} ({elapsed:.0f}s, {rate:.0f}/s, ETA {eta:.0f}s)")

        try:
            ts = buildTimeseries(cik, edgarDir=EDGAR_DIR)
        except Exception:
            failed += 1
            continue

        if ts is None:
            failed += 1
            continue

        loaded += 1
        series, periods = ts

        for label, stmt, target, srcA, srcB, op in FORMULAS:
            reported = series[stmt].get(target)
            aVals = series[stmt].get(srcA)
            bVals = series[stmt].get(srcB)

            if reported is None or aVals is None or bVals is None:
                continue

            st = stats[label]
            st["companies_checked"] += 1
            companyMaxErr = 0.0

            for i in range(len(periods)):
                r = reported[i]
                a = aVals[i]
                b = bVals[i]
                if r is None or a is None or b is None:
                    continue
                if abs(r) < 1000:
                    continue

                derived = (a + b) if op == "add" else (a - b)
                err = abs(derived - r) / abs(r)
                st["total_points"] += 1

                if err <= 0.01:
                    st["le1"] += 1
                elif err <= 0.05:
                    st["le5"] += 1
                elif err <= 0.10:
                    st["gt5"] += 1
                else:
                    st["gt10"] += 1

                if err > companyMaxErr:
                    companyMaxErr = err

            if companyMaxErr > 0.10:
                st["gt10_companies"].append((cik, companyMaxErr))

    elapsed = time.time() - t0
    print(f"\n로드 성공: {loaded}개, 실패: {failed}개 ({elapsed:.0f}s)")
    print()

    for label, stmt, target, srcA, srcB, op in FORMULAS:
        st = stats[label]
        tp = st["total_points"]
        if tp == 0:
            print(f"  {label}: 검증 포인트 없음")
            continue

        le1 = st["le1"]
        le5 = st["le1"] + st["le5"]
        gt5 = st["gt5"] + st["gt10"]
        gt10 = st["gt10"]

        print(f"  {label}: {target} = {srcA} {'+' if op == 'add' else '-'} {srcB}")
        print(f"    검증: {st['companies_checked']}사, {tp:,}포인트")
        print(f"    ≤1%: {le1:,}/{tp:,} ({le1/tp*100:.1f}%)")
        print(f"    ≤5%: {le5:,}/{tp:,} ({le5/tp*100:.1f}%)")
        print(f"    >5%: {gt5:,}/{tp:,} ({gt5/tp*100:.1f}%)")
        print(f"    >10%: {gt10:,}/{tp:,} ({gt10/tp*100:.1f}%)")

        if st["gt10_companies"]:
            worst = sorted(st["gt10_companies"], key=lambda x: -x[1])[:10]
            print(f"    최악 10사:")
            for cik, maxErr in worst:
                print(f"      {cik}: max {maxErr*100:.1f}%")
        print()


if __name__ == "__main__":
    print("=" * 70)
    print("013: 전체 CIK 파생 계정 정확도 검증")
    print("=" * 70)
    validateAll()
