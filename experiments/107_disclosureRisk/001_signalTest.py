"""
실험 ID: 107-001
실험명: changes.parquet 기반 공시 리스크 시그널 유효성 검증

목적:
- changes.parquet에서 5개 시그널을 추출하고
- 기존 scan 축(debt, audit, profitability, growth)과 교차하여
- 기존 축이 "안전"으로 판정한 기업 중 시그널이 위험을 포착하는 건수를 측정
- 20건 이상이면 선행 지표로 유효

가설:
1. 우발부채 증가 기업 중 debt 등급 "안전"이 30% 이상 → 선행 지표
2. 공시 변화 강도 상위 100 중 profitability 악화(적자/저수익) 비율이 전체 평균보다 높음
3. 감사 구조 변경 기업 중 audit riskLevel "안전"이 50% 이상 → 아직 감지 못한 리스크
4. 사업 전환(bizPivot) 기업이 growth 패턴에서 특정 분포를 보임

방법:
1. changes.parquet 로드 → 최신 기간(2024→2025) 필터
2. 5개 시그널 계산 (종목별 집계)
3. 기존 scan 축 로드 (debt, audit, profitability, growth)
4. 시그널 상위 종목과 기존 등급 교차표 작성
5. 유효성 판정: "기존 축 안전인데 시그널 위험" 건수 기준

결과 (실험 후 작성):
- 기간: 2024→2025, 2,489종목
- 시그널 활성: changeIntensity 2489, contingentDebt 1068, bizPivot 424, auditStruct 2061, affiliate 185

교차 검증:
| 시그널 | 교차 축 | 핵심 수치 | 판정 |
|---|---|---|---|
| contingentDebt | debt | 1,068종목 중 384개(36.0%)가 부채등급 안전/관찰 | 유효 |
| changeIntensity | profitability | 상위100 적자비율 48.0% vs 시장 61.4% — enrichment 0.78 | 미달 |
| auditStruct | audit | 2,061종목 중 1,256개(60.9%)가 감사 안전 | 유효 |
| affiliateChange | (독립) | 185종목 — 기존 축에 없는 M&A 신호 | 유효 |
| bizPivot | growth | 424종목 분포: 고성장98/정체71/급감58/역성장47/성장30 | 참고 (독립 분포) |

결론:
- **유효 3/4**: contingentDebt, auditStruct, affiliateChange
- **미달 1/4**: changeIntensity — 공시 많이 바뀐 기업이 오히려 수익성이 좋음 (대기업 효과)
- **참고**: bizPivot은 성장등급과 독립적 분포 — 별도 가치 있으나 교차 enrichment 측정 불가
- contingentDebt가 핵심: 부채등급 "안전"인데 우발부채 증가한 384종목 = debt 축이 못 보는 선행 위험
- auditStruct는 대상이 2,061종목(전체의 83%)으로 너무 넓음 — 임계값 강화 필요(3건 이상 등)
- 흡수 권장 시그널: contingentDebt(핵심), affiliateChange(독립 가치), auditStruct(임계값 조정 후)
- changeIntensity는 scan 축에서는 빼되, 개별 기업 company-bound 분석에서는 여전히 유용

실험일: 2026-04-01
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

CHANGES_PATH = Path("data/dart/scan/changes.parquet")
OUT_DIR = Path("data/dart/auditScan")


def _loadChanges() -> pl.DataFrame:
    """최신 기간 changes 로드."""
    df = pl.read_parquet(str(CHANGES_PATH))
    # 최신 기간 자동 탐지
    latest_to = df["toPeriod"].max()
    latest_from = str(int(latest_to) - 1)
    return df.filter(
        (pl.col("fromPeriod") == latest_from) & (pl.col("toPeriod") == latest_to)
    ), f"{latest_from}→{latest_to}"


def _calcSignals(changes: pl.DataFrame) -> pl.DataFrame:
    """종목별 5개 시그널 계산."""
    # 1. changeIntensity: 전체 |sizeDelta| 합
    intensity = (
        changes.group_by("stockCode")
        .agg(
            pl.col("sizeDelta").abs().sum().alias("changeIntensity"),
            pl.len().alias("changeCount"),
        )
    )

    # 2. contingentDebtGrowth: 우발부채 섹션 sizeDelta > 0 합
    contingent = (
        changes.filter(
            pl.col("sectionTitle").str.contains("우발부채")
            & (pl.col("sizeDelta") > 0)
        )
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").sum().alias("contingentDebtGrowth"))
    )

    # 3. bizPivot: 사업의 내용 |sizeDelta| > 5000
    biz = (
        changes.filter(
            pl.col("sectionTitle").str.contains("사업의")
            & (pl.col("sizeDelta").abs() > 5000)
        )
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").abs().max().alias("bizPivotDelta"))
    )

    # 4. auditStructChange: 감사/내부통제 structural 건수
    audit_struct = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("감사") | pl.col("sectionTitle").str.contains("내부통제"))
            & (pl.col("changeType") == "structural")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("auditStructCount"))
    )

    # 5. affiliateChange: 계열/타법인 numeric 건수
    affiliate = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("계열") | pl.col("sectionTitle").str.contains("타법인출자"))
            & (pl.col("changeType") == "numeric")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("affiliateChangeCount"))
    )

    # 병합
    result = intensity
    for right in [contingent, biz, audit_struct, affiliate]:
        result = result.join(right, on="stockCode", how="left")

    return result.fill_null(0)


def _loadExistingAxes() -> dict[str, pl.DataFrame]:
    """기존 scan 축 로드."""
    from dartlab.scan import Scan
    s = Scan()

    axes = {}
    for name in ["debt", "audit", "profitability", "growth"]:
        df = s(name)
        # 종목코드 정규화
        if "종목코드" in df.columns and "stockCode" not in df.columns:
            df = df.rename({"종목코드": "stockCode"})
        if "위험등급" in df.columns:
            df = df.rename({"위험등급": "debtGrade"})
        axes[name] = df
        gc.collect()

    return axes


def _crossValidate(signals: pl.DataFrame, axes: dict[str, pl.DataFrame]) -> dict:
    """시그널 vs 기존 축 교차 검증."""
    results = {}

    # === 1. 우발부채 증가 vs debt ===
    contingent_top = signals.filter(pl.col("contingentDebtGrowth") > 0)
    if "debt" in axes and contingent_top.height > 0:
        debt = axes["debt"]
        merged = contingent_top.join(debt.select(["stockCode", "debtGrade"]), on="stockCode", how="left")
        total = merged.height
        safe_count = merged.filter(pl.col("debtGrade").is_in(["안전", "관찰"])).height
        safe_pct = round(safe_count / total * 100, 1) if total > 0 else 0
        results["contingentDebt_vs_debt"] = {
            "total": total,
            "debtSafe": safe_count,
            "debtSafePct": safe_pct,
            "verdict": "유효" if safe_count >= 20 else "미달",
            "interpretation": f"우발부채 증가 {total}종목 중 {safe_count}개({safe_pct}%)가 부채등급 안전/관찰 — 선행 지표",
        }

    # === 2. 공시 강도 상위 vs profitability ===
    top100 = signals.sort("changeIntensity", descending=True).head(100)
    if "profitability" in axes:
        prof = axes["profitability"]
        merged = top100.join(prof.select(["stockCode", "grade"]), on="stockCode", how="left")
        loss_count = merged.filter(pl.col("grade").is_in(["적자", "저수익"])).height
        # 전체 시장 적자+저수익 비율
        total_loss = prof.filter(pl.col("grade").is_in(["적자", "저수익"])).height
        market_loss_pct = round(total_loss / prof.height * 100, 1) if prof.height > 0 else 0
        sample_loss_pct = round(loss_count / merged.height * 100, 1) if merged.height > 0 else 0
        results["intensity_vs_profitability"] = {
            "top100_lossPct": sample_loss_pct,
            "market_lossPct": market_loss_pct,
            "enrichment": round(sample_loss_pct / market_loss_pct, 2) if market_loss_pct > 0 else 0,
            "verdict": "유효" if sample_loss_pct > market_loss_pct * 1.2 else "미달",
            "interpretation": f"공시 강도 상위 100의 적자/저수익 비율 {sample_loss_pct}% vs 시장 {market_loss_pct}%",
        }

    # === 3. 감사 구조 변경 vs audit ===
    audit_change_top = signals.filter(pl.col("auditStructCount") > 0)
    if "audit" in axes and audit_change_top.height > 0:
        audit = axes["audit"]
        merged = audit_change_top.join(audit.select(["stockCode", "riskLevel"]), on="stockCode", how="left")
        total = merged.height
        safe_count = merged.filter(pl.col("riskLevel") == "안전").height
        safe_pct = round(safe_count / total * 100, 1) if total > 0 else 0
        results["auditStruct_vs_audit"] = {
            "total": total,
            "auditSafe": safe_count,
            "auditSafePct": safe_pct,
            "verdict": "유효" if safe_count >= 20 else "미달",
            "interpretation": f"감사 구조 변경 {total}종목 중 {safe_count}개({safe_pct}%)가 감사 안전 — 아직 미감지",
        }

    # === 4. 사업 전환 vs growth ===
    biz_pivot = signals.filter(pl.col("bizPivotDelta") > 0)
    if "growth" in axes and biz_pivot.height > 0:
        growth = axes["growth"]
        merged = biz_pivot.join(growth.select(["stockCode", "grade"]), on="stockCode", how="left")
        grade_dist = {}
        for r in merged["grade"].drop_nulls().value_counts().to_dicts():
            grade_dist[r["grade"]] = r["count"]
        results["bizPivot_vs_growth"] = {
            "total": biz_pivot.height,
            "gradeDistribution": grade_dist,
            "interpretation": f"사업 전환 {biz_pivot.height}종목의 성장등급 분포",
        }

    # === 5. 계열 변화 vs 기존 어떤 축에도 없는 정보 ===
    affiliate_top = signals.filter(pl.col("affiliateChangeCount") > 0)
    results["affiliateChange"] = {
        "total": affiliate_top.height,
        "verdict": "유효" if affiliate_top.height >= 50 else "미달",
        "interpretation": f"계열/타법인 변화 {affiliate_top.height}종목 — 기존 축에 없는 M&A 신호",
    }

    return results


def main():
    print("=== 107-001: disclosureRisk 시그널 유효성 검증 ===\n")

    # 1. changes 로드
    print("[1/4] changes.parquet 로드...")
    changes, period = _loadChanges()
    print(f"  기간: {period}, {changes.height:,}행, {changes['stockCode'].n_unique()}종목\n")

    # 2. 시그널 계산
    print("[2/4] 시그널 계산...")
    signals = _calcSignals(changes)
    print(f"  {signals.height}종목")
    for col in ["changeIntensity", "contingentDebtGrowth", "bizPivotDelta", "auditStructCount", "affiliateChangeCount"]:
        nonzero = signals.filter(pl.col(col) > 0).height
        print(f"  {col}: {nonzero}종목 활성")
    print()

    del changes
    gc.collect()

    # 3. 기존 축 로드
    print("[3/4] 기존 scan 축 로드...")
    axes = _loadExistingAxes()
    for name, df in axes.items():
        print(f"  {name}: {df.height}종목")
    print()

    # 4. 교차 검증
    print("[4/4] 교차 검증...")
    results = _crossValidate(signals, axes)
    print()

    for name, r in results.items():
        print(f"--- {name} ---")
        for k, v in r.items():
            print(f"  {k}: {v}")
        print()

    # 저장
    out = {"period": period, "signalCount": signals.height, "crossValidation": results}
    outPath = Path("experiments/107_disclosureRisk/001_result.json")
    outPath.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[SAVED] {outPath}")

    # 요약
    valid_count = sum(1 for r in results.values() if r.get("verdict") == "유효")
    total_count = sum(1 for r in results.values() if "verdict" in r)
    print(f"\n=== 유효 시그널: {valid_count}/{total_count} ===")


if __name__ == "__main__":
    main()
