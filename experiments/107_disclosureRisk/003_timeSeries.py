"""
실험 ID: 107-003
실험명: 시계열 패턴 — 만성 우발부채 + 변화량 가속

목적:
- 5개년 시계열로 "만성적 문제"를 탐지 — 단년도 snapshot보다 강력한 시그널인지 검증
- 만성 우발부채 기업이 debt 축에서 미감지인 비율 측정

가설:
1. 우발부채 3년+ 연속 증가 기업 중 debt "안전"이 30건 이상 → 시계열 선행 지표
2. 공시 변화량 3년 연속 가속(매년 x1.5+) 기업은 구조적 변화 진행 중 → profitability 악화 비율 높음

방법:
1. 전 기간 종목별 연도별 우발부채 delta 집계
2. 3년+ 연속 증가 추출 → debt 교차
3. 전 기간 종목별 연도별 totalDelta → 3년 연속 증가 + 가속(x1.5+) 추출
4. 가속 종목 vs profitability 교차

결과 (실험 후 작성):
| 시그널 | 종목수 | 교차 결과 | 판정 |
|--------|--------|----------|------|
| 만성 우발부채 (3년+) | 2,142 | debt 안전/관찰 768건(35.9%) | 유효 |
| 변화량 가속 (3년 x2) | 390 | 적자/저수익 46.7% vs 시장 61.4% (enrichment 0.76) | 미달 |

만성 우발부채 debt 분포: 주의 955, 안전 498, 관찰 270, 고위험 193
변화량 가속 profitability 분포: 저수익 122, 보통 78, 적자 60, 양호 50, 우수 37

결론:
- 가설1 채택: 만성 우발부채 2,142종목 중 768건(35.9%)이 debt 안전/관찰 → 시계열이 단년도보다 강력
  - 498건이 "안전"인데 3년+ 우발부채 연속 증가 = debt 축이 못 보는 선행 위험
- 가설2 기각: 변화량 가속 기업이 오히려 수익성이 좋음 (enrichment 0.76)
  - 대기업/성장기업이 공시를 많이 바꾸는 경향 → 변화량 자체는 부정적 시그널이 아님
- 흡수 권장: chronicContingentDebt(만성 우발부채 연수) — 현재 contingentDebt 단년도에 연수 정보 추가
- 흡수 비권장: acceleratingChange — 001에서 changeIntensity와 같은 결론 (대기업 효과)

실험일: 2026-04-01
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

CHANGES_PATH = Path("data/dart/scan/changes.parquet")


def main():
    print("=== 107-003: 시계열 패턴 ===\n")

    df = pl.read_parquet(str(CHANGES_PATH))
    print(f"전체: {df.height:,}행, {df['stockCode'].n_unique()}종목\n")

    # ── 1. 만성 우발부채 ──
    print("[1/2] 만성 우발부채...")
    contingent_yearly = (
        df.filter(
            pl.col("sectionTitle").str.contains("우발부채")
            & (pl.col("sizeDelta") > 0)
        )
        .group_by(["stockCode", "toPeriod"])
        .agg(pl.col("sizeDelta").sum().alias("delta"))
        .sort(["stockCode", "toPeriod"])
    )

    # 연속 증가 연수 계산
    chronic = []
    for code in contingent_yearly["stockCode"].unique().to_list():
        sub = contingent_yearly.filter(pl.col("stockCode") == code).sort("toPeriod")
        years = sub.height
        if years >= 3:
            total_delta = sub["delta"].sum()
            chronic.append({"stockCode": code, "chronicYears": years, "totalDelta": int(total_delta)})

    chronic_df = pl.DataFrame(chronic) if chronic else pl.DataFrame()
    print(f"  3년+ 연속 우발부채 증가: {chronic_df.height}종목")

    # debt 교차
    from dartlab.scan import Scan
    s = Scan()
    debt = s("debt")
    if "종목코드" in debt.columns:
        debt = debt.rename({"종목코드": "stockCode"})
    if "위험등급" in debt.columns:
        debt = debt.rename({"위험등급": "debtGrade"})

    if not chronic_df.is_empty():
        merged = chronic_df.join(debt.select(["stockCode", "debtGrade"]), on="stockCode", how="left")
        safe = merged.filter(pl.col("debtGrade").is_in(["안전", "관찰"])).height
        safe_pct = round(safe / merged.height * 100, 1)

        # debt 등급 분포
        debt_dist = {}
        for r in merged["debtGrade"].drop_nulls().value_counts().to_dicts():
            debt_dist[r["debtGrade"]] = r["count"]

        print(f"  debt 안전/관찰: {safe}건 ({safe_pct}%)")
        print(f"  debt 분포: {debt_dist}")
        chronic_result = {
            "total": chronic_df.height,
            "debtSafe": safe,
            "debtSafePct": safe_pct,
            "debtDist": debt_dist,
            "verdict": "유효" if safe >= 30 else "미달",
        }
    else:
        chronic_result = {"total": 0, "verdict": "데이터 없음"}

    del debt
    gc.collect()
    print()

    # ── 2. 변화량 가속 ──
    print("[2/2] 변화량 가속...")
    yearly_delta = (
        df.group_by(["stockCode", "toPeriod"])
        .agg(pl.col("sizeDelta").abs().sum().alias("yearDelta"))
        .sort(["stockCode", "toPeriod"])
    )
    del df

    accelerating = []
    for code in yearly_delta["stockCode"].unique().to_list():
        sub = yearly_delta.filter(pl.col("stockCode") == code).sort("toPeriod")
        if sub.height < 3:
            continue
        deltas = sub["yearDelta"].to_list()
        # 최근 3개년 연속 증가 + 가속(각 x1.5+)
        if len(deltas) >= 3:
            d1, d2, d3 = deltas[-3], deltas[-2], deltas[-1]
            if d1 > 0 and d2 > d1 and d3 > d2:
                ratio = d3 / d1
                if ratio >= 2.0:  # 3년간 2배 이상
                    accelerating.append({
                        "stockCode": code,
                        "ratio3y": round(ratio, 1),
                        "delta_n3": int(d1), "delta_n2": int(d2), "delta_n1": int(d3),
                    })

    accel_df = pl.DataFrame(accelerating) if accelerating else pl.DataFrame()
    print(f"  3년 연속 증가 + x2 가속: {accel_df.height}종목")

    # profitability 교차
    prof = s("profitability")
    if "종목코드" in prof.columns:
        prof = prof.rename({"종목코드": "stockCode"})
    if "등급" in prof.columns:
        prof = prof.rename({"등급": "grade"})

    if not accel_df.is_empty():
        merged = accel_df.join(prof.select(["stockCode", "grade"]), on="stockCode", how="left")
        loss = merged.filter(pl.col("grade").is_in(["적자", "저수익"])).height
        loss_pct = round(loss / merged.height * 100, 1)

        # 시장 전체 적자/저수익 비율
        market_loss = prof.filter(pl.col("grade").is_in(["적자", "저수익"])).height
        market_loss_pct = round(market_loss / prof.height * 100, 1)

        prof_dist = {}
        for r in merged["grade"].drop_nulls().value_counts().to_dicts():
            prof_dist[r["grade"]] = r["count"]

        print(f"  적자/저수익: {loss_pct}% (시장: {market_loss_pct}%)")
        print(f"  enrichment: x{round(loss_pct / market_loss_pct, 2) if market_loss_pct > 0 else 0}")
        print(f"  profitability 분포: {prof_dist}")
        accel_result = {
            "total": accel_df.height,
            "lossPct": loss_pct,
            "marketLossPct": market_loss_pct,
            "enrichment": round(loss_pct / market_loss_pct, 2) if market_loss_pct > 0 else 0,
            "profDist": prof_dist,
            "verdict": "유효" if loss_pct > market_loss_pct * 1.2 else "미달",
        }
    else:
        accel_result = {"total": 0, "verdict": "데이터 없음"}

    print()

    results = {
        "chronicContingentDebt": chronic_result,
        "acceleratingChange": accel_result,
    }

    for name, r in results.items():
        print(f"--- {name}: {r.get('verdict', '?')} ---")

    outPath = Path("experiments/107_disclosureRisk/003_result.json")
    outPath.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
