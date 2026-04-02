"""실험 109-01: 경제 사이클 판별 정확도.

가설: 하이일드 스프레드, 장단기 스프레드, VIX, 금, CLI 신호를
조합하면 경제 사이클 4국면(침체/회복/확장/둔화)을 판별할 수 있다.

방법:
1. FRED/ECOS에서 과거 10년 핵심 신호 지표 수집
2. 각 신호의 수준/변화율 기반 국면 판정 로직 프로토타입
3. NBER 경기순환 기준일과 사후 비교

성공 기준: 전환점 +-2개월 이내 감지, 4국면 중 3개 이상 정확 매칭
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import polars as pl

# dartlab import
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.gather import getDefaultGather  # noqa: E402


# ── NBER 기준일 (미국) ──
# https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
# Peak = 확장 끝 → 침체 시작, Trough = 침체 끝 → 회복 시작
NBER_CYCLES = [
    # (peak, trough, label)
    ("2007-12-01", "2009-06-01", "Great Recession"),
    ("2020-02-01", "2020-04-01", "COVID-19"),
]

# 한국은행 경기기준순환일 (간략)
BOK_CYCLES = [
    # (정점, 저점, label)
    ("2008-01-01", "2009-02-01", "글로벌 금융위기"),
    ("2011-08-01", "2013-03-01", "유럽 재정위기"),
    ("2017-09-01", "2020-05-01", "경기 둔화+COVID"),
]


@dataclass
class CycleSignals:
    """한 시점의 사이클 판별 신호."""

    date: str
    hy_spread: float | None  # 하이일드 스프레드 (bp)
    term_spread: float | None  # 장단기 스프레드 (10Y-2Y, %)
    vix: float | None  # VIX
    gold_yoy: float | None  # 금 가격 YoY 변화율 (%)
    cli: float | None  # 경기선행지수
    cli_mom: float | None  # CLI 전월비 변화


def classify_cycle(s: CycleSignals) -> tuple[str, str, list[str]]:
    """신호 조합으로 4국면 판정.

    Returns:
        (phase, confidence, signals)
        phase: contraction | recovery | expansion | slowdown
    """
    signals: list[str] = []
    scores = {"contraction": 0, "recovery": 0, "expansion": 0, "slowdown": 0}

    # 1. 하이일드 스프레드 — 신용 스트레스 핵심 지표
    if s.hy_spread is not None:
        if s.hy_spread > 500:
            scores["contraction"] += 3
            signals.append(f"HY spread 급등 ({s.hy_spread:.0f}bp) -> 신용 스트레스")
        elif s.hy_spread > 400:
            scores["contraction"] += 2
            scores["slowdown"] += 1
            signals.append(f"HY spread 경고 ({s.hy_spread:.0f}bp)")
        elif s.hy_spread < 350:
            scores["expansion"] += 1
            scores["recovery"] += 1
            signals.append(f"HY spread 안정 ({s.hy_spread:.0f}bp)")

    # 2. 장단기 스프레드 — 경기 방향 선행
    if s.term_spread is not None:
        if s.term_spread < 0:
            scores["contraction"] += 2
            scores["slowdown"] += 1
            signals.append(f"수익률곡선 역전 ({s.term_spread:+.2f}%)")
        elif s.term_spread < 0.5:
            scores["slowdown"] += 2
            signals.append(f"수익률곡선 평탄화 ({s.term_spread:+.2f}%)")
        elif s.term_spread > 1.5:
            scores["recovery"] += 2
            signals.append(f"수익률곡선 정상화 ({s.term_spread:+.2f}%)")
        else:
            scores["expansion"] += 1
            signals.append(f"수익률곡선 정상 ({s.term_spread:+.2f}%)")

    # 3. VIX — 공포 수준
    if s.vix is not None:
        if s.vix > 30:
            scores["contraction"] += 2
            signals.append(f"VIX 급등 ({s.vix:.1f}) -> 공포")
        elif s.vix > 20:
            scores["slowdown"] += 1
            signals.append(f"VIX 상승 ({s.vix:.1f})")
        elif s.vix < 15:
            scores["expansion"] += 2
            signals.append(f"VIX 안정 ({s.vix:.1f}) -> 낙관")
        else:
            scores["recovery"] += 1
            signals.append(f"VIX 보통 ({s.vix:.1f})")

    # 4. 금 YoY — 안전자산 선호
    if s.gold_yoy is not None:
        if s.gold_yoy > 15:
            scores["contraction"] += 1
            scores["slowdown"] += 1
            signals.append(f"금 급등 (YoY {s.gold_yoy:+.1f}%) -> 안전자산 선호")
        elif s.gold_yoy < -5:
            scores["recovery"] += 1
            scores["expansion"] += 1
            signals.append(f"금 하락 (YoY {s.gold_yoy:+.1f}%) -> 위험자산 선호")

    # 5. CLI — 경기선행지수 모멘텀
    if s.cli_mom is not None:
        if s.cli_mom < -0.5:
            scores["contraction"] += 2
            scores["slowdown"] += 1
            signals.append(f"CLI 급락 (MoM {s.cli_mom:+.2f})")
        elif s.cli_mom < 0:
            scores["slowdown"] += 2
            signals.append(f"CLI 하락 (MoM {s.cli_mom:+.2f})")
        elif s.cli_mom > 0.5:
            scores["recovery"] += 2
            signals.append(f"CLI 급등 (MoM {s.cli_mom:+.2f})")
        elif s.cli_mom > 0:
            scores["expansion"] += 1
            signals.append(f"CLI 상승 (MoM {s.cli_mom:+.2f})")

    # 최고 점수 국면 선택
    phase = max(scores, key=scores.get)  # type: ignore[arg-type]
    max_score = scores[phase]
    total = sum(scores.values())

    if total == 0:
        return "unknown", "low", ["신호 데이터 부족"]

    # 신뢰도: 최고 점수의 비율
    ratio = max_score / total if total > 0 else 0
    if ratio > 0.5:
        confidence = "high"
    elif ratio > 0.35:
        confidence = "medium"
    else:
        confidence = "low"

    return phase, confidence, signals


PHASE_LABELS = {
    "contraction": "침체",
    "recovery": "회복",
    "expansion": "확장",
    "slowdown": "둔화",
    "unknown": "미정",
}


def main():
    """FRED 데이터로 과거 10년 월별 사이클 판별."""
    g = getDefaultGather()

    print("=== 109-01: 경제 사이클 판별 실험 ===\n")
    print("FRED에서 핵심 신호 지표 수집 중...\n")

    # 개별 지표 수집 (2014~현재, 월별 리샘플 비교 위해)
    indicators = {}
    series_list = [
        ("BAMLH0A0HYM2", "하이일드 스프레드"),
        ("T10Y2Y", "장단기 스프레드"),
        ("VIXCLS", "VIX"),
        ("GOLDAMGBD228NLBM", "금 가격"),
        ("DGS10", "국채 10년"),
        ("DGS2", "국채 2년"),
        ("FEDFUNDS", "연방기금금리"),
    ]

    for code, label in series_list:
        df = g.macro(code, start="2014-01-01")
        if df is not None and len(df) > 0:
            indicators[code] = df
            print(f"  {label} ({code}): {len(df)}건")
        else:
            print(f"  {label} ({code}): 수집 실패")

    # ECOS CLI (한국)
    cli_df = g.macro("KR", "CLI", start="2014-01-01")
    if cli_df is not None:
        indicators["CLI"] = cli_df
        print(f"  경기선행지수 (CLI): {len(cli_df)}건")

    print()

    if not indicators:
        print("데이터 수집 실패. API 키를 확인하세요.")
        return

    # 월별 시계열 구성 — 각 지표의 월말 값
    # 금 가격 YoY 계산
    gold_df = indicators.get("GOLDAMGBD228NLBM")
    gold_monthly = None
    if gold_df is not None:
        gold_monthly = (
            gold_df.sort("date")
            .group_by_dynamic("date", every="1mo")
            .agg(pl.col("value").last())
            .with_columns(
                (pl.col("value") / pl.col("value").shift(12) - 1).alias("gold_yoy") * 100
            )
        )

    # HY spread 월말
    hy_df = indicators.get("BAMLH0A0HYM2")
    hy_monthly = None
    if hy_df is not None:
        hy_monthly = (
            hy_df.sort("date")
            .group_by_dynamic("date", every="1mo")
            .agg(pl.col("value").last())
            .rename({"value": "hy_spread"})
        )
        # bp 단위 변환 (원래 % 단위, 100 곱하면 bp)
        hy_monthly = hy_monthly.with_columns(
            (pl.col("hy_spread") * 100).alias("hy_spread")
        )

    # Term spread 월말
    ts_df = indicators.get("T10Y2Y")
    ts_monthly = None
    if ts_df is not None:
        ts_monthly = (
            ts_df.sort("date")
            .group_by_dynamic("date", every="1mo")
            .agg(pl.col("value").last())
            .rename({"value": "term_spread"})
        )

    # VIX 월말
    vix_df = indicators.get("VIXCLS")
    vix_monthly = None
    if vix_df is not None:
        vix_monthly = (
            vix_df.sort("date")
            .group_by_dynamic("date", every="1mo")
            .agg(pl.col("value").last())
            .rename({"value": "vix"})
        )

    # CLI 월말 + MoM
    cli_data = indicators.get("CLI")
    cli_monthly = None
    if cli_data is not None:
        cli_monthly = (
            cli_data.sort("date")
            .with_columns(
                (pl.col("value") - pl.col("value").shift(1)).alias("cli_mom")
            )
            .rename({"value": "cli"})
        )

    # 월별 시계열 merge
    # 기준 날짜 생성 (2015-01 ~ 현재, YoY 계산에 12개월 필요)
    dates = pl.date_range(
        pl.date(2015, 1, 1), pl.date(2026, 3, 1), interval="1mo", eager=True
    )
    base = pl.DataFrame({"date": dates})

    def _asof_join(base_df, right_df, col_name):
        if right_df is None:
            return base_df.with_columns(pl.lit(None).cast(pl.Float64).alias(col_name))
        right = right_df.select("date", col_name).sort("date")
        return base_df.sort("date").join_asof(right, on="date", strategy="backward")

    merged = base
    merged = _asof_join(merged, hy_monthly, "hy_spread")
    merged = _asof_join(merged, ts_monthly, "term_spread")
    merged = _asof_join(merged, vix_monthly, "vix")
    if gold_monthly is not None:
        gold_sub = gold_monthly.select("date", "gold_yoy")
        merged = _asof_join(merged, gold_sub, "gold_yoy")
    else:
        merged = merged.with_columns(pl.lit(None).cast(pl.Float64).alias("gold_yoy"))
    merged = _asof_join(merged, cli_monthly, "cli")
    merged = _asof_join(merged, cli_monthly, "cli_mom")

    # 사이클 판별 실행
    results = []
    for row in merged.iter_rows(named=True):
        sig = CycleSignals(
            date=str(row["date"]),
            hy_spread=row.get("hy_spread"),
            term_spread=row.get("term_spread"),
            vix=row.get("vix"),
            gold_yoy=row.get("gold_yoy"),
            cli=row.get("cli"),
            cli_mom=row.get("cli_mom"),
        )
        phase, confidence, signals = classify_cycle(sig)
        results.append({
            "date": row["date"],
            "phase": phase,
            "label": PHASE_LABELS.get(phase, phase),
            "confidence": confidence,
            "signals": " | ".join(signals[:3]),
        })

    result_df = pl.DataFrame(results)

    # 결과 출력
    print("=== 월별 사이클 판별 결과 (주요 시점) ===\n")

    # NBER 전환점 전후 출력
    for peak, trough, label in NBER_CYCLES:
        print(f"--- {label} (Peak: {peak}, Trough: {trough}) ---")
        from datetime import datetime, timedelta

        peak_dt = datetime.strptime(peak, "%Y-%m-%d")
        trough_dt = datetime.strptime(trough, "%Y-%m-%d")

        # peak 전후 3개월
        for offset_months in [-3, -2, -1, 0, 1, 2, 3]:
            target = peak_dt + timedelta(days=offset_months * 30)
            target_date = pl.date(target.year, target.month, 1)
            row = result_df.filter(pl.col("date") == target_date)
            if len(row) > 0:
                r = row.row(0, named=True)
                marker = " <-- PEAK" if offset_months == 0 else ""
                print(
                    f"  {r['date']}  {r['label']:4s} ({r['confidence']:6s}) {r['signals']}{marker}"
                )

        print()
        # trough 전후 3개월
        for offset_months in [-3, -2, -1, 0, 1, 2, 3]:
            target = trough_dt + timedelta(days=offset_months * 30)
            target_date = pl.date(target.year, target.month, 1)
            row = result_df.filter(pl.col("date") == target_date)
            if len(row) > 0:
                r = row.row(0, named=True)
                marker = " <-- TROUGH" if offset_months == 0 else ""
                print(
                    f"  {r['date']}  {r['label']:4s} ({r['confidence']:6s}) {r['signals']}{marker}"
                )
        print()

    # 최근 12개월
    print("=== 최근 12개월 ===\n")
    recent = result_df.tail(12)
    for row in recent.iter_rows(named=True):
        print(f"  {row['date']}  {row['label']:4s} ({row['confidence']:6s}) {row['signals']}")

    # 국면 분포
    print("\n=== 전체 국면 분포 ===\n")
    dist = result_df.group_by("label").len().sort("len", descending=True)
    for row in dist.iter_rows(named=True):
        print(f"  {row['label']}: {row['len']}개월")

    print("\n실험 완료.")


if __name__ == "__main__":
    main()
