"""재예보 시험장 : 과거 시점에 보행자를 세워 걸음수별 skill 곡선 실측 (L2.5 simulate).

"과거로 돌아가 미래를 연장하고 이미 아는 답과 대조"(기상 reforecast 동형)의 본진. 두 팔 (15 §6):
- fan: origin PIT 격자의 스텝별 분위를 기대 원장에 봉인(issuedLive=False)·채점 + 곡선 직접 산출
  → coverage(h)·CRPS(h)/carry. 격자 분포가 몇 걸음까지 현실을 커버하나 (h*_env).
- actualPath: 실측 매크로 경로 주입 = 회사층 법칙 격리 채점. origin vintage 베타(nested PIT) x
  실현 누적충격의 예측 반응 vs 실현 버킷중립 초과의 걸음수별 IC + t (h*_firm). **arm 라벨 영구:
  조건부(매크로 실경로 가정) 채점이지 트랙레코드가 아니다.**

h* 판정 규칙 (사전 등록 H_STAR_RULES, 변경 = 새 시리즈): h*_env = coverage90([p5,p95] 명목 90%)
이탈 |cov-0.90|>0.10 첫 걸음. h*_firm = IC 평균의 t < 2.0 첫 걸음. 개별 셀 주장 금지 = 곡선
전체(전 팩터 x 전 지평) 통봉인·통보고. 어떤 채널도 벤치마크를 못 이기면 "다걸음 전개 기각"이
정직한 산출이다 (VAR 기각 동형).

Layer: L2.5 simulate. lattice·scenarioSim·table·estimate(봉인·채점)·readingScorecard(라벨) 배선.
"""

from __future__ import annotations

from datetime import datetime as _dt
from datetime import timedelta as _td
from pathlib import Path

import numpy as np
import polars as pl

from dartlab.simulate import estimate as _estimate
from dartlab.simulate import lattice as _lattice
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import scenarioSim as _ss
from dartlab.simulate import table as _table
from dartlab.simulate.factors import macroFactors
from dartlab.synth.expectationSpec import pinballLoss

H_STAR_RULES = "hstar-v1: env=|cov90-0.90|>0.10 첫 h, firm=t(IC)<2.0 첫 h. 곡선 통보고, 셀 선별 금지."


def origins(weekEnd: pl.DataFrame, *, start: str = "20190101", gapWeeks: int = 8, steps: int = 8) -> list[str]:
    """재예보 출발점 목록 (사전 등록): start 이후 주말일을 gap 간격 비중첩 추출, 지평 도래분만.

    Args:
        weekEnd: (week, date). start: 첫 origin 하한. gapWeeks: 간격 (>= steps = 표본 비중첩,
            인접 여정 겹침 t 부풀림 차단). steps: 지평 주 수 (마지막 origin + steps 가 데이터 안).
    """
    dates = weekEnd.sort("week")["date"].to_list()
    picked = [d for i, d in enumerate(dates) if d >= start and i % max(gapWeeks, steps) == 0]
    return [d for d in picked if dates.index(d) + steps < len(dates)]


def _factorLevelAt(macro: pl.DataFrame, factor: str, date: str) -> float | None:
    s = macro.filter(pl.col("date") <= date)[factor].drop_nulls()
    return float(s[-1]) if s.len() else None


def fanCurves(
    *,
    dataDir: Path | None = None,
    baseDir: Path | None = None,
    start: str = "20190101",
    steps: int = 8,
    gapWeeks: int = 8,
    seal: bool = True,
) -> pl.DataFrame:
    """fan 팔: origin 별 격자 스텝 분위 vs 실현 → (factor, h, cov90, cov50, crps, crpsCarry, n).

    carry 벤치마크 = 무변화 점예보 (CRPS = |실현-현재|, 점예보의 CRPS = MAE). 봉인은 기존
    sealMacroOutlook 계약 재사용 (issuedLive=False, 같은 vintage 재실행 멱등 스킵).

    Returns:
        걸음수별 곡선 + skill = crpsCarry/crps (>1 = 격자가 carry 보다 낫다). h* 판정은 호출측이
        H_STAR_RULES 로 (곡선 전체 반환 = 셀 선별 금지).
    """
    macro = _table.macroDaily(dataDir)
    _, weekEnd = _table.weekCalendar(dataDir)
    kinds = {mf.factor: mf.kind for mf in macroFactors()}
    ogs = origins(weekEnd, start=start, gapWeeks=gapWeeks, steps=steps)
    rows: list[dict] = []
    for og in ogs:
        pit = macro.filter(pl.col("date") <= og)
        if pit.height < 100:
            continue
        cov = _ss.factorCovariance(pit)
        k = len(cov["factors"])
        lat = _lattice.growLattice(
            cov, steps=steps, stepDays=5, beamWidth=min(1500 * 10 ** max(0, k - 3), 50000), perStep=True
        )
        for h, marg in enumerate(lat["stepMarginals"], 1):
            target = (_dt.strptime(og, "%Y%m%d") + _td(days=7 * h)).strftime("%Y%m%d")
            if seal:
                _estimate.sealMacroOutlook(pit, marg, asOf=og, horizonWeeks=h, live=False, baseDir=baseDir)
            for factor, q in marg.items():
                cur = _factorLevelAt(pit, factor, og)
                act = _factorLevelAt(macro, factor, target)
                if cur is None or act is None:
                    continue
                if kinds.get(factor) == "price":
                    if cur <= 0:
                        continue
                    quants = {p: cur * (1.0 + q[p]) for p in (5, 25, 50, 75, 95)}
                else:
                    quants = {p: cur + q[p] for p in (5, 25, 50, 75, 95)}
                rows.append(
                    {
                        "origin": og,
                        "factor": factor,
                        "h": h,
                        "hit90": quants[5] <= act <= quants[95],
                        "hit50": quants[25] <= act <= quants[75],
                        "crps": pinballLoss(quants, act),
                        "crpsCarry": abs(act - cur),
                    }
                )
    if seal:
        _estimate.scoreMacroDue(market="KR", baseDir=baseDir, macro=macro)
    if not rows:
        return pl.DataFrame(
            schema={
                "factor": pl.Utf8,
                "h": pl.Int64,
                "cov90": pl.Float64,
                "cov50": pl.Float64,
                "crps": pl.Float64,
                "crpsCarry": pl.Float64,
                "skill": pl.Float64,
                "n": pl.UInt32,
            }
        )
    return (
        pl.DataFrame(rows)
        .group_by(["factor", "h"])
        .agg(
            cov90=pl.col("hit90").mean(),
            cov50=pl.col("hit50").mean(),
            crps=pl.col("crps").mean(),
            crpsCarry=pl.col("crpsCarry").mean(),
            n=pl.len(),
        )
        .with_columns(skill=pl.col("crpsCarry") / pl.col("crps"))
        .select("factor", "h", "cov90", "cov50", "crps", "crpsCarry", "skill", "n")
        .sort(["factor", "h"])
    )


def actualPathCurves(
    *,
    dataDir: Path | None = None,
    start: str = "20190101",
    steps: int = 8,
    gapWeeks: int = 8,
    minCross: int = 300,
) -> pl.DataFrame:
    """actualPath 팔: 실측 매크로 경로 주입 회사층 IC 곡선 → (h, icMean, t, nOrigins, avgCross).

    예측 = origin vintage 베타(nested PIT: macroBetaByCodeWide(asOf=origin)) x 실현 누적 팩터
    변화. 실현 = 지평 h 버킷중립 초과(weeklyLabels horizonDays=5h, 절단 포함). IC = origin 별
    횡단면 Spearman. **조건부 채점(매크로 실경로 가정) 라벨 영구 = 트랙레코드 아님.**

    Returns:
        걸음수별 IC 곡선 (origin 비중첩 = 플레인 t 유효, 참고로 표본 std 병기). h*_firm 판정은
        호출측 H_STAR_RULES.
    """
    macro = _table.macroDaily(dataDir)
    weekMap, weekEnd = _table.weekCalendar(dataDir)
    px = _table.dailyPrices(dataDir)
    kinds = {mf.factor: mf.kind for mf in macroFactors()}
    we = weekEnd.sort("week")
    dates = we["date"].to_list()
    ogs = origins(we, start=start, gapWeeks=gapWeeks, steps=steps)
    labsByH = {h: _sc.weeklyLabels(we, px, horizonDays=5 * h) for h in range(1, steps + 1)}
    weekByDate = dict(zip(we["date"].to_list(), we["week"].to_list()))
    rows: list[dict] = []
    for og in ogs:
        idx = dates.index(og)
        betas = _lattice.winsorizeBetas(_table.macroBetaByCodeWide(og, baseDir=dataDir))
        if betas.height == 0:
            continue
        pit = macro.filter(pl.col("date") <= og)
        for h in range(1, steps + 1):
            target = dates[idx + h]
            pred = pl.lit(0.0)
            for factor, kind in kinds.items():
                col = f"{factor}Beta"
                if col not in betas.columns or factor not in macro.columns:
                    continue
                cur = _factorLevelAt(pit, factor, og)
                lvl = _factorLevelAt(macro, factor, target)
                if cur is None or lvl is None or (kind == "price" and cur <= 0):
                    continue
                dv = (lvl / cur - 1.0) if kind == "price" else (lvl - cur)
                pred = pred + pl.col(col).fill_null(0.0) * dv
            sig = betas.select("code", pred=pred)
            lab = labsByH[h].filter(pl.col("week") == weekByDate[og]).select("code", "exNeutral")
            j = sig.join(lab, on="code", how="inner").drop_nulls()
            if j.height < minCross:
                continue
            rr = j.with_columns(pr=pl.col("pred").rank(), lr=pl.col("exNeutral").rank())
            ic = float(np.corrcoef(rr["pr"].to_numpy(), rr["lr"].to_numpy())[0, 1])
            rows.append({"origin": og, "h": h, "ic": ic, "nCross": j.height})
    if not rows:
        return pl.DataFrame(
            schema={"h": pl.Int64, "icMean": pl.Float64, "t": pl.Float64, "nOrigins": pl.UInt32, "avgCross": pl.Float64}
        )
    df = pl.DataFrame(rows)
    return (
        df.group_by("h")
        .agg(
            icMean=pl.col("ic").mean(),
            t=pl.col("ic").mean() / (pl.col("ic").std() / pl.len().sqrt()),
            nOrigins=pl.len(),
            avgCross=pl.col("nCross").mean(),
        )
        .sort("h")
    )


def hStar(fan: pl.DataFrame, firm: pl.DataFrame) -> dict:
    """사전 등록 규칙(H_STAR_RULES)으로 전개 한계 판정 → {"env": {factor: h*}, "firm": h*}.

    h* = 규칙 위반 첫 걸음 (전 걸음 통과면 지평+1 = 관측 한계까지 유효). 곡선 전체와 함께
    보고해야 하며 h* 단독 인용 금지.
    """
    env: dict[str, int] = {}
    for factor in fan["factor"].unique().sort().to_list() if fan.height else []:
        sub = fan.filter(pl.col("factor") == factor).sort("h")
        star = int(sub["h"].max()) + 1
        for r in sub.iter_rows(named=True):
            if abs(r["cov90"] - 0.90) > 0.10:
                star = r["h"]
                break
        env[factor] = star
    firmStar = (int(firm["h"].max()) + 1) if firm.height else 0
    for r in firm.sort("h").iter_rows(named=True) if firm.height else []:
        if r["t"] < 2.0:
            firmStar = r["h"]
            break
    return {"env": env, "firm": firmStar, "rules": H_STAR_RULES}
