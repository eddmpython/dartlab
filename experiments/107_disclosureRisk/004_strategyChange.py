"""
실험 ID: 107-004
실험명: 전략 변화 시그널 — 정관변경 + 경영진단 + 임원구조

목적:
- 정관 대규모 변경이 성장 정체/역성장 기업에서 높은 비율로 나타나면 → 턴어라운드 시도 탐지
- 경영진단 대규모 변화가 수익성 등급 변화와 연관되는지 검증

가설:
1. 정관변경(266종목) 중 growth 정체/역성장 비율이 시장 평균보다 높음 → 구조전환 신호
2. 경영진단 변화(296종목) 중 profitability 적자/저수익 비율이 시장 평균보다 높음
3. 임원/직원 구조변화(211종목)는 독립 참고 가치

방법:
1. 정관 structural sizeDelta > 2000 종목 vs growth grade 교차
2. 경영진단 abs(sizeDelta) > 10000 종목 vs profitability grade 교차
3. 임원/직원 structural abs(sizeDelta) > 5000 종목 vs workforce 교차

결과 (실험 후 작성):
| 시그널 | 종목수 | 핵심 수치 | 판정 |
|--------|--------|----------|------|
| 정관변경 vs growth | 266 | 정체/역성장/급감 40.2% vs 시장 62.1% | 유효 (역방향) |
| 경영진단 vs prof | 296 | 적자/저수익 51.7% vs 시장 61.4% | 미달 |
| 임원/직원 구조변화 | 211 | 증가 70, 감소 150 | 참고 |

정관변경 grade 분포: 고성장 52, 정체 41, 급감 35, 역성장 31, 성장 17
경영진단 grade 분포: 저수익 104, 보통 60, 적자 49, 양호 37, 우수 21

결론:
- 가설1 **역방향 채택**: 정관변경 기업은 정체/역성장 비율이 시장보다 **낮음**(40% vs 62%)
  - 고성장 52종목이 최다 → 정관변경은 성장기업이 신사업 확장할 때 더 많이 함
  - "성장 정체→정관변경→턴어라운드" 시나리오보다 "성장중→정관변경→추가확장"이 현실
  - 단, 정체+역성장+급감 107종목(40%)도 상당 → 전환 시도 기업도 존재
- 가설2 기각: 경영진단 변화는 수익성과 무관 (enrichment 0.84)
- 임원/직원: 감소 150 > 증가 70 → 구조조정이 채용보다 2배 많음, 독립 참고 가치
- **흡수 권장**: 정관변경(charterChange)은 "성장 신호"로 재해석 — 리스크보다 기회 시그널
  - disclosureRisk 축보다 growth 보조 지표로 적합
- **흡수 비권장**: 경영진단, 임원구조 — 변별력 부족

실험일: 2026-04-01
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

CHANGES_PATH = Path("data/dart/scan/changes.parquet")


def main():
    print("=== 107-004: 전략 변화 시그널 ===\n")

    df = pl.read_parquet(str(CHANGES_PATH))
    latest = df.filter((pl.col("fromPeriod") == "2024") & (pl.col("toPeriod") == "2025"))
    del df
    print(f"최신 기간: {latest.height:,}행, {latest['stockCode'].n_unique()}종목\n")

    from dartlab.scan import Scan
    s = Scan()

    results = {}

    # ── 1. 정관변경 vs growth ──
    print("[1/3] 정관 대규모 변경 vs growth...")
    charter = latest.filter(
        pl.col("sectionTitle").str.contains("정관")
        & (pl.col("changeType") == "structural")
        & (pl.col("sizeDelta") > 2000)
    )
    charter_codes = set(charter["stockCode"].unique().to_list())
    print(f"  정관변경: {len(charter_codes)}종목")

    growth = s("growth")
    charter_df = pl.DataFrame({"stockCode": list(charter_codes)})
    merged = charter_df.join(growth.select(["stockCode", "grade"]), on="stockCode", how="left")

    grade_dist = {}
    for r in merged["grade"].drop_nulls().value_counts().to_dicts():
        grade_dist[r["grade"]] = r["count"]

    # 시장 전체 정체+역성장+급감 비율
    stagnant = merged.filter(pl.col("grade").is_in(["정체", "역성장", "급감"])).height
    stagnant_pct = round(stagnant / merged.height * 100, 1) if merged.height > 0 else 0

    market_stagnant = growth.filter(pl.col("grade").is_in(["정체", "역성장", "급감"])).height
    market_stagnant_pct = round(market_stagnant / growth.height * 100, 1)

    print(f"  정체/역성장/급감: {stagnant_pct}% (시장: {market_stagnant_pct}%)")
    print(f"  grade 분포: {grade_dist}")
    results["charterChange_vs_growth"] = {
        "total": len(charter_codes),
        "stagnantPct": stagnant_pct,
        "marketStagnantPct": market_stagnant_pct,
        "enrichment": round(stagnant_pct / market_stagnant_pct, 2) if market_stagnant_pct > 0 else 0,
        "gradeDist": grade_dist,
        "verdict": "유효" if stagnant >= 50 else "미달",
    }
    del growth
    gc.collect()
    print()

    # ── 2. 경영진단 vs profitability ──
    print("[2/3] 경영진단 대규모 변화 vs profitability...")
    mgmt = latest.filter(
        pl.col("sectionTitle").str.contains("이사의 경영진단")
        & (pl.col("sizeDelta").abs() > 10000)
    )
    mgmt_codes = set(mgmt["stockCode"].unique().to_list())
    print(f"  경영진단변화: {len(mgmt_codes)}종목")

    prof = s("profitability")
    if "종목코드" in prof.columns:
        prof = prof.rename({"종목코드": "stockCode"})
    if "등급" in prof.columns:
        prof = prof.rename({"등급": "grade"})

    mgmt_df = pl.DataFrame({"stockCode": list(mgmt_codes)})
    merged = mgmt_df.join(prof.select(["stockCode", "grade"]), on="stockCode", how="left")

    grade_dist = {}
    for r in merged["grade"].drop_nulls().value_counts().to_dicts():
        grade_dist[r["grade"]] = r["count"]

    loss = merged.filter(pl.col("grade").is_in(["적자", "저수익"])).height
    loss_pct = round(loss / merged.height * 100, 1) if merged.height > 0 else 0
    market_loss = prof.filter(pl.col("grade").is_in(["적자", "저수익"])).height
    market_loss_pct = round(market_loss / prof.height * 100, 1)

    print(f"  적자/저수익: {loss_pct}% (시장: {market_loss_pct}%)")
    print(f"  grade 분포: {grade_dist}")
    results["mgmtChange_vs_profitability"] = {
        "total": len(mgmt_codes),
        "lossPct": loss_pct,
        "marketLossPct": market_loss_pct,
        "enrichment": round(loss_pct / market_loss_pct, 2) if market_loss_pct > 0 else 0,
        "gradeDist": grade_dist,
        "verdict": "유효" if loss_pct > market_loss_pct * 1.2 else "미달",
    }
    del prof
    gc.collect()
    print()

    # ── 3. 임원/직원 구조변화 ──
    print("[3/3] 임원/직원 대규모 구조변화...")
    hr = latest.filter(
        (pl.col("sectionTitle").str.contains("임원") | pl.col("sectionTitle").str.contains("직원"))
        & (pl.col("changeType") == "structural")
        & (pl.col("sizeDelta").abs() > 5000)
    )
    hr_codes = set(hr["stockCode"].unique().to_list())
    print(f"  임원/직원 구조변화: {len(hr_codes)}종목")

    # 증가 vs 감소 분리
    hr_increase = hr.filter(pl.col("sizeDelta") > 0)["stockCode"].unique().to_list()
    hr_decrease = hr.filter(pl.col("sizeDelta") < 0)["stockCode"].unique().to_list()
    print(f"  내용 증가(채용?): {len(hr_increase)}, 내용 감소(구조조정?): {len(hr_decrease)}")

    results["hrChange"] = {
        "total": len(hr_codes),
        "increase": len(hr_increase),
        "decrease": len(hr_decrease),
        "verdict": "참고" if len(hr_codes) >= 50 else "미달",
    }
    print()

    # ── 요약 ──
    for name, r in results.items():
        print(f"--- {name}: {r.get('verdict', '?')} ---")

    outPath = Path("experiments/107_disclosureRisk/004_result.json")
    outPath.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
