"""Scan 교차 분석 — 학술 프레임워크 기반 인사이트 발굴.

Piotroski F-Score, Altman Z-Score, DuPont 분해, Composite Quality를
기반으로 전 상장사를 교차 분석한다.

Usage:
    uv run python -X utf8 scripts/scanCrossInsights.py
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

OUT_DIR = Path("data/dart/auditScan")
DATE = "2026-04-01"


# ── 컬럼 정규화 ──────────────────────────────────────────


def _loadAxis(axisName: str) -> pl.DataFrame:
    """축 데이터를 로드하고, stockCode 외 모든 컬럼에 축 prefix를 붙인다."""
    import dartlab

    df = dartlab.scan(axisName)

    # 종목코드 → stockCode
    if "종목코드" in df.columns and "stockCode" not in df.columns:
        df = df.rename({"종목코드": "stockCode"})

    # 등급 컬럼 통일 → grade
    for old in ("위험등급", "등급", "riskLevel"):
        if old in df.columns and "grade" not in df.columns:
            df = df.rename({old: "grade"})

    # stockCode 외 모든 컬럼에 축 이름 prefix
    renames = {col: f"{axisName}_{col}" for col in df.columns if col != "stockCode"}
    return df.rename(renames)


def _mergeAll() -> pl.DataFrame:
    """12개 축을 순차 left join으로 병합."""
    axes = [
        "profitability", "quality", "cashflow", "debt",
        "liquidity", "efficiency", "growth", "valuation",
        "governance", "insider", "dividendTrend", "capital",
        "audit",
    ]
    merged = None
    for axis in axes:
        print(f"  loading {axis}...")
        df = _loadAxis(axis)
        if merged is None:
            merged = df
        else:
            merged = merged.join(df, on="stockCode", how="left")
        gc.collect()
    return merged


# ── 등급 → 점수 변환 ──────────────────────────────────────


_GRADE_SCORES: dict[str, int] = {
    "우수": 2, "양호": 1, "보통": 0, "저수익": -1, "적자": -2,
    "A": 2, "B": 1, "C": 0, "D": -1, "E": -2,
    "안전": 2, "관찰": 0, "주의": -1, "고위험": -2,
    "고성장": 2, "성장": 1, "정체": 0, "역성장": -1, "급감": -2,
    "저평가": 2, "적정": 1, "고평가": -1, "과열": -2, "해당없음": 0,
    "비효율": -2, "무배당": -1, "위험": -2,
}


def _gradeToScore(col: str) -> pl.Expr:
    """등급 컬럼 → 정수 점수."""
    return pl.col(col).replace_strict(_GRADE_SCORES, default=0).cast(pl.Int8)


# ── 학술 프레임워크 ────────────────────────────────────────


def _addPiotroskiFScore(m: pl.DataFrame) -> pl.DataFrame:
    """Piotroski F-Score (0~9) proxy 계산."""
    def _safe(col: str) -> pl.Expr:
        return pl.col(col) if col in m.columns else pl.lit(None)

    f1 = (_safe("profitability_roa") > 0).fill_null(False).cast(pl.Int8)
    f2 = (_safe("cashflow_ocf") > 0).fill_null(False).cast(pl.Int8)
    f3 = (_safe("quality_accrualRatio") < 0).fill_null(False).cast(pl.Int8)
    f4 = (_safe("quality_cfToNi").is_not_null() & (_safe("quality_cfToNi") > 1)).fill_null(False).cast(pl.Int8)
    f5 = (_safe("debt_grade").is_in(["안전", "관찰"])).fill_null(False).cast(pl.Int8)
    f6 = (_safe("liquidity_grade").is_in(["우수", "양호", "보통"])).fill_null(False).cast(pl.Int8)
    f7 = (~_safe("capital_분류").is_in(["희석형"])).fill_null(True).cast(pl.Int8)
    f8 = (_safe("profitability_opMargin") > 5).fill_null(False).cast(pl.Int8)
    f9 = (_safe("efficiency_grade").is_in(["우수", "양호"])).fill_null(False).cast(pl.Int8)

    return m.with_columns(
        (f1 + f2 + f3 + f4 + f5 + f6 + f7 + f8 + f9).alias("fScore"),
        pl.when(f1 + f2 + f3 + f4 + f5 + f6 + f7 + f8 + f9 >= 7).then(pl.lit("Strong"))
        .when(f1 + f2 + f3 + f4 + f5 + f6 + f7 + f8 + f9 >= 4).then(pl.lit("Neutral"))
        .otherwise(pl.lit("Weak")).alias("fZone"),
    )


def _addAltmanZScore(m: pl.DataFrame) -> pl.DataFrame:
    """Altman Z-Score 계산 (proxy). 필수 컬럼 없으면 null."""
    has_all = all(
        c in m.columns
        for c in ["liquidity_currentAssets", "liquidity_currentLiabilities",
                   "quality_totalAssets", "profitability_roa",
                   "valuation_marketCap", "debt_총부채", "efficiency_assetTurnover"]
    )
    if not has_all:
        return m.with_columns(pl.lit(None).cast(pl.Float64).alias("zScore"), pl.lit(None).cast(pl.Utf8).alias("zZone"))

    x1 = (pl.col("liquidity_currentAssets") - pl.col("liquidity_currentLiabilities")) / pl.col("quality_totalAssets")
    x2 = pl.col("profitability_roa") / 100
    x3 = pl.col("profitability_roa") / 100 * 1.5  # EBIT/TA proxy
    x4 = pl.col("valuation_marketCap") / pl.col("debt_총부채")
    x5 = pl.col("efficiency_assetTurnover")

    z = (1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + x5)

    return m.with_columns(
        z.alias("zScore"),
        pl.when(z > 2.99).then(pl.lit("Safe"))
        .when(z > 1.81).then(pl.lit("Grey"))
        .otherwise(pl.lit("Distress")).alias("zZone"),
    )


def _addDuPont(m: pl.DataFrame) -> pl.DataFrame:
    """DuPont 3-factor 분해."""
    has_all = all(
        c in m.columns
        for c in ["profitability_netMargin", "efficiency_assetTurnover", "debt_부채비율"]
    )
    if not has_all:
        return m.with_columns(
            pl.lit(None).cast(pl.Float64).alias("dupont_margin"),
            pl.lit(None).cast(pl.Float64).alias("dupont_turnover"),
            pl.lit(None).cast(pl.Float64).alias("dupont_leverage"),
            pl.lit(None).cast(pl.Utf8).alias("dupont_driver"),
        )

    margin = pl.col("profitability_netMargin").abs() / 100
    turnover = pl.col("efficiency_assetTurnover")
    leverage = (1 + pl.col("debt_부채비율") / 100)

    total = margin + turnover + leverage
    m_pct = margin / total * 100
    t_pct = turnover / total * 100
    l_pct = leverage / total * 100

    driver = (
        pl.when(l_pct > 50).then(pl.lit("레버리지형"))
        .when(m_pct > 40).then(pl.lit("마진형"))
        .when(t_pct > 40).then(pl.lit("회전형"))
        .otherwise(pl.lit("균형형"))
    )

    return m.with_columns(
        (pl.col("profitability_netMargin") / 100).alias("dupont_margin"),
        pl.col("efficiency_assetTurnover").alias("dupont_turnover"),
        leverage.alias("dupont_leverage"),
        driver.alias("dupont_driver"),
    )


def _addCompositeQuality(m: pl.DataFrame) -> pl.DataFrame:
    """5축 Composite Quality Score (-10 ~ +10)."""
    score_cols = []
    for axis in ["profitability", "quality", "growth", "debt", "efficiency"]:
        col = f"{axis}_grade"
        if col in m.columns:
            score_cols.append(_gradeToScore(col).alias(f"_qs_{axis}"))

    if not score_cols:
        return m.with_columns(pl.lit(None).cast(pl.Int8).alias("qualityScore"))

    m = m.with_columns(score_cols)
    qs_names = [f"_qs_{a}" for a in ["profitability", "quality", "growth", "debt", "efficiency"] if f"_qs_{a}" in m.columns]
    m = m.with_columns(
        pl.sum_horizontal(*[pl.col(c) for c in qs_names]).alias("qualityScore")
    ).drop(qs_names)
    return m


# ── 인사이트 발굴 ──────────────────────────────────────────


def _extractInsights(m: pl.DataFrame) -> dict:
    """14개 교차 인사이트 추출."""
    R: dict[str, int] = {}

    def _count(label: str, expr: pl.Expr) -> int:
        n = m.filter(expr).height
        R[label] = n
        return n

    # ── 기존 8개 (버그 수정) ──

    # 1. 허상이익
    _count("허상이익(수익양호+질위험)",
           pl.col("profitability_grade").is_in(["양호", "우수"])
           & pl.col("quality_grade").is_in(["주의", "위험"]))

    # 2. 적자but현금유입
    _count("적자but현금유입(턴어라운드후보)",
           (pl.col("profitability_grade") == "적자")
           & pl.col("quality_grade").is_in(["양호", "우수"]))

    # 3. 레버리지성장 — growth_grade 사용 (기존 pattern 버그 수정)
    _count("레버리지성장(고성장+부채고위험)",
           (pl.col("growth_grade") == "고성장")
           & (pl.col("debt_grade") == "고위험"))

    # 4. 건전성장
    _count("건전성장(성장+부채안전)",
           pl.col("growth_grade").is_in(["고성장", "성장"])
           & (pl.col("debt_grade") == "안전"))

    # 5. 가치주
    _count("가치주(저평가+수익양호)",
           (pl.col("valuation_grade") == "저평가")
           & pl.col("profitability_grade").is_in(["양호", "우수"]))

    # 6. 거품
    _count("거품(고평가+적자)",
           pl.col("valuation_grade").is_in(["고평가", "과열"])
           & (pl.col("profitability_grade") == "적자"))

    # 7. 배당지속가능성
    if "dividendTrend_pattern" in m.columns and "cashflow_pattern" in m.columns:
        _count("배당연속증가+현금건전",
               (pl.col("dividendTrend_pattern") == "연속증가")
               & pl.col("cashflow_pattern").is_in(["현금축적형", "성장투자형"]))
        _count("배당연속증가but현금위기",
               (pl.col("dividendTrend_pattern") == "연속증가")
               & pl.col("cashflow_pattern").is_in(["현금위기형", "외부의존형"]))

    # 8. 효율적but유동성위험
    _count("효율적but유동성위험",
           pl.col("efficiency_grade").is_in(["우수", "양호"])
           & pl.col("liquidity_grade").is_in(["위험", "주의"]))

    # ── 신규 6개 (학술 프레임워크) ──

    # 9. F-Score 가치주
    if "fScore" in m.columns:
        _count("F-Score가치주(F>=8+저평가)",
               (pl.col("fScore") >= 8) & (pl.col("valuation_grade") == "저평가"))

    # 10. F-Score 위험 거품
    if "fScore" in m.columns:
        _count("F-Score위험거품(F<=2+고평가)",
               (pl.col("fScore") <= 2)
               & pl.col("valuation_grade").is_in(["고평가", "과열"]))

    # 11. Z-Score 잠재위험
    if "zZone" in m.columns and "audit_opinion" in m.columns:
        _count("Z-Score잠재위험(Distress+감사적정)",
               (pl.col("zZone") == "Distress")
               & (pl.col("audit_opinion") == "적정의견"))

    # 12. Z-Score 안전 저평가
    if "zZone" in m.columns:
        _count("Z-Score안전저평가(Safe+저평가)",
               (pl.col("zZone") == "Safe") & (pl.col("valuation_grade") == "저평가"))

    # 13. DuPont 레버리지 의존
    if "dupont_driver" in m.columns:
        _count("DuPont레버리지의존",
               (pl.col("dupont_driver") == "레버리지형")
               & (pl.col("profitability_roe").is_not_null())
               & (pl.col("profitability_roe") > 5))

    # 14. Quality 올스타
    if "qualityScore" in m.columns:
        _count("Quality올스타(QS>=7+저평가)",
               (pl.col("qualityScore") >= 7) & (pl.col("valuation_grade") == "저평가"))

    return R


def _extractSamples(m: pl.DataFrame) -> dict:
    """주요 인사이트의 샘플 종목."""
    samples: dict[str, list] = {}

    # F-Score 가치주 top10
    if "fScore" in m.columns and "valuation_per" in m.columns:
        fv = m.filter((pl.col("fScore") >= 8) & (pl.col("valuation_grade") == "저평가"))
        if fv.height > 0:
            samples["F-Score가치주_top10"] = [
                {k: r.get(k) for k in
                 ["stockCode", "fScore", "valuation_per", "valuation_pbr",
                  "profitability_opMargin", "quality_accrualRatio", "debt_grade"]}
                for r in fv.sort("fScore", descending=True).head(10).to_dicts()
            ]

    # Z-Score Distress top10
    if "zScore" in m.columns:
        distress = m.filter(pl.col("zZone") == "Distress").filter(pl.col("zScore").is_not_null())
        if distress.height > 0:
            samples["Z-Score_Distress_top10"] = [
                {k: r.get(k) for k in
                 ["stockCode", "zScore", "valuation_grade", "profitability_grade",
                  "debt_grade", "liquidity_grade"]}
                for r in distress.sort("zScore").head(10).to_dicts()
            ]

    # Quality 올스타 top10
    if "qualityScore" in m.columns:
        qs = m.filter((pl.col("qualityScore") >= 7) & (pl.col("valuation_grade") == "저평가"))
        if qs.height > 0:
            samples["Quality올스타_top10"] = [
                {k: r.get(k) for k in
                 ["stockCode", "qualityScore", "fScore", "valuation_per", "valuation_pbr",
                  "profitability_opMargin", "quality_accrualRatio"]}
                for r in qs.sort("qualityScore", descending=True).head(10).to_dicts()
            ]

    # DuPont 레버리지형 top10
    if "dupont_driver" in m.columns:
        lev = m.filter(
            (pl.col("dupont_driver") == "레버리지형")
            & pl.col("profitability_roe").is_not_null()
            & (pl.col("profitability_roe") > 5)
        )
        if lev.height > 0:
            samples["DuPont레버리지형_top10"] = [
                {k: r.get(k) for k in
                 ["stockCode", "profitability_roe", "dupont_margin",
                  "dupont_turnover", "dupont_leverage", "debt_부채비율"]}
                for r in lev.sort("dupont_leverage", descending=True).head(10).to_dicts()
            ]

    return samples


def _marketStructure(m: pl.DataFrame) -> dict:
    """시장 구조 통계."""
    stats: dict[str, dict] = {}

    # 수익성 분포
    if "profitability_grade" in m.columns:
        d = {}
        for r in m["profitability_grade"].drop_nulls().value_counts().to_dicts():
            d[r["profitability_grade"]] = r["count"]
        stats["profitability"] = d

    # 성장 등급 분포 (grade 사용!)
    if "growth_grade" in m.columns:
        d = {}
        for r in m["growth_grade"].drop_nulls().value_counts().to_dicts():
            d[r["growth_grade"]] = r["count"]
        stats["growth_grade"] = d

    # F-Score 분포
    if "fScore" in m.columns:
        d = {}
        for r in m["fScore"].drop_nulls().value_counts().sort("fScore").to_dicts():
            d[str(r["fScore"])] = r["count"]
        stats["fScore"] = d

    # Z-Score zone 분포
    if "zZone" in m.columns:
        d = {}
        for r in m["zZone"].drop_nulls().value_counts().to_dicts():
            d[r["zZone"]] = r["count"]
        stats["zScore_zone"] = d

    # DuPont driver 분포
    if "dupont_driver" in m.columns:
        d = {}
        for r in m["dupont_driver"].drop_nulls().value_counts().to_dicts():
            d[r["dupont_driver"]] = r["count"]
        stats["dupont_driver"] = d

    # Composite Quality 분포
    if "qualityScore" in m.columns:
        d = {}
        for r in m["qualityScore"].drop_nulls().value_counts().sort("qualityScore").to_dicts():
            d[str(r["qualityScore"])] = r["count"]
        stats["qualityScore"] = d

    return stats


# ── 마크다운 보고서 ────────────────────────────────────────


def _generateMarkdown(out: dict) -> str:
    """JSON 결과 → 마크다운 보고서."""
    lines = [f"# Scan 교차 분석 — {out['date']}", ""]

    # 방법론
    lines.append("## 방법론")
    lines.append("")
    for k, v in out.get("methodology", {}).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    # 프레임워크 분포
    ms = out.get("market_structure", {})

    if "fScore" in ms:
        lines.append("## Piotroski F-Score 분포")
        lines.append("")
        lines.append("| 점수 | 종목수 |")
        lines.append("|---|---|")
        for k in sorted(ms["fScore"], key=int):
            lines.append(f"| {k} | {ms['fScore'][k]} |")
        lines.append("")

    if "zScore_zone" in ms:
        lines.append("## Altman Z-Score 분포")
        lines.append("")
        lines.append("| Zone | 종목수 |")
        lines.append("|---|---|")
        for k, v in ms["zScore_zone"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    if "dupont_driver" in ms:
        lines.append("## DuPont 드라이버 분포")
        lines.append("")
        lines.append("| 유형 | 종목수 |")
        lines.append("|---|---|")
        for k, v in ms["dupont_driver"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    if "qualityScore" in ms:
        lines.append("## Composite Quality Score 분포")
        lines.append("")
        lines.append("| 점수 | 종목수 |")
        lines.append("|---|---|")
        for k in sorted(ms["qualityScore"], key=int):
            lines.append(f"| {k} | {ms['qualityScore'][k]} |")
        lines.append("")

    # 인사이트
    lines.append("## 교차 인사이트")
    lines.append("")
    lines.append("| 인사이트 | 종목수 |")
    lines.append("|---|---|")
    for k, v in out.get("insights", {}).items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # 샘플
    for title, rows in out.get("samples", {}).items():
        lines.append(f"### {title}")
        lines.append("")
        if rows:
            cols = list(rows[0].keys())
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for r in rows:
                vals = [str(r.get(c, "")) for c in cols]
                lines.append("| " + " | ".join(vals) + " |")
        lines.append("")

    # 시장 구조
    if "profitability" in ms:
        lines.append("## 시장 구조: 수익성")
        lines.append("")
        lines.append("| 등급 | 종목수 |")
        lines.append("|---|---|")
        for k, v in ms["profitability"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    if "growth_grade" in ms:
        lines.append("## 시장 구조: 성장 등급")
        lines.append("")
        lines.append("| 등급 | 종목수 |")
        lines.append("|---|---|")
        for k, v in ms["growth_grade"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    return "\n".join(lines)


# ── 메인 ──────────────────────────────────────────────────


def main():
    print(f"=== Scan 교차 분석 시작 ({DATE}) ===\n")

    # 1. 전 축 로드 + 병합
    print("[1/5] 축 데이터 로드 + 병합...")
    m = _mergeAll()
    print(f"  병합 완료: {m.height}종목, {m.width}컬럼\n")

    # 2. 학술 프레임워크 계산
    print("[2/5] 학술 프레임워크 계산...")
    m = _addPiotroskiFScore(m)
    print(f"  F-Score: {m.filter(pl.col('fScore').is_not_null()).height}종목")
    m = _addAltmanZScore(m)
    print(f"  Z-Score: {m.filter(pl.col('zScore').is_not_null()).height}종목")
    m = _addDuPont(m)
    print(f"  DuPont: {m.filter(pl.col('dupont_driver').is_not_null()).height}종목")
    m = _addCompositeQuality(m)
    print(f"  Quality: {m.filter(pl.col('qualityScore').is_not_null()).height}종목\n")

    # 3. 인사이트 추출
    print("[3/5] 인사이트 추출...")
    insights = _extractInsights(m)
    for k, v in insights.items():
        print(f"  {k}: {v}")

    # 4. 샘플 추출
    print("\n[4/5] 샘플 추출...")
    samples = _extractSamples(m)
    for k, v in samples.items():
        print(f"  {k}: {len(v)}종목")

    # 5. 시장 구조
    print("\n[5/5] 시장 구조 통계...")
    market = _marketStructure(m)

    # 출력 구성
    out = {
        "date": DATE,
        "methodology": {
            "piotroskiFScore": "9개 바이너리 시그널 proxy. 원본은 YoY 변화 기반이나, scan은 단년도 snapshot이므로 수준값 기반으로 대체.",
            "altmanZScore": "5변수 (X2/X3는 ROA proxy). Zone: >2.99 Safe, 1.81~2.99 Grey, <1.81 Distress.",
            "dupontAnalysis": "3-factor (netMargin × assetTurnover × equityMultiplier). 기여도 기반 driver 분류.",
            "compositeQuality": "5축(profitability, quality, growth, debt, efficiency) 등급 점수 합산 (-10 ~ +10).",
        },
        "total_stocks": m.height,
        "insights": insights,
        "samples": samples,
        "market_structure": market,
    }

    # JSON 저장
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonPath = OUT_DIR / f"scan_cross_insights_{DATE}.json"
    jsonPath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {jsonPath}")

    # 마크다운 저장
    mdPath = OUT_DIR / f"scan_cross_insights_{DATE}.md"
    mdPath.write_text(_generateMarkdown(out), encoding="utf-8")
    print(f"[SAVED] {mdPath}")

    # 요약 출력
    print(f"\n=== 완료: {m.height}종목, {len(insights)}개 인사이트 ===")


if __name__ == "__main__":
    main()
