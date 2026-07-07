"""역사 백테스트 : 전 엔진을 실역사에 replay → 성적표·인증·sweep 증거 (L2.5 simulate).

라이브 채점은 매주 발행 후 지평 도래로 수개월 누적되지만, 역사 증거는 지금 낼 수 있다: 전
과거 주의 판독을 한 번에 opine 하고 (issuedLive=False bootstrap), 확보된 라벨로 성적표·인증
깔때기(certify)·가정 sweep(PBO/DSR/robust)를 계산한다. 가정 벌은 issuedLive=False 로 봉인(권위는
라이브만, 06 §5). 이것이 "시뮬레이터가 역사에서 실제로 무엇을 발견하는가"의 즉시 산출이다.

전수 replay 는 판독 행렬 재사용이라 분 단위 (06 §5 실측). 시장 파라미터(KR/US)로 시장 내 완결.

Layer: L2.5 simulate. readingCycle(라우팅)·opine·readingScorecard·certify·assume·sweep 배선.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from dartlab.simulate import assume as _assume
from dartlab.simulate import certify as _certify
from dartlab.simulate import opine as _opine
from dartlab.simulate import readingCycle as _cycle
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import sweep as _sweep


def _weightSchemes(certifyRes: dict, surfaces: list[str]) -> dict[str, dict]:
    """인증 결과 → sweep 가중 스킴 (equal·certifiedOnly·tWeighted). 가정 축 후보."""
    df = certifyRes["surfaces"]
    tByS = {r["surface"]: max(float(r["t"]), 0.0) for r in df.iter_rows(named=True)}
    certified = {r["surface"]: 1.0 for r in df.iter_rows(named=True) if r["verdict"] in ("인증", "발굴")}
    return {
        "equal": {s: 1.0 for s in surfaces},
        "certifiedOnly": certified or {s: 1.0 for s in surfaces},
        "tWeighted": tByS or {s: 1.0 for s in surfaces},
    }


def backtest(
    market: str = "KR",
    dataDir: Path | None = None,
    *,
    matrices: tuple | None = None,
    labels: pl.DataFrame | None = None,
    nBoot: int = 500,
    sealDir: Path | None = None,
    issuedAt: str = "backtest",
    trainFrac: float = 0.5,
) -> dict:
    """전 역사 replay → {"scorecard", "certify", "sweep", "weeks", "surfaces", "universe"}.

    Args:
        market: "KR"|"US". dataDir: 데이터 SSOT 루트.
        matrices/labels: 주입 (테스트). None = 시장 상(床)에서 계산.
        nBoot: 인증 부트스트랩. sealDir: 가정 봉인 루트 (None = 미봉인). issuedAt: 봉인 시각.
        trainFrac: 이벤트 방향사전(라벨 적합물)의 train 구간 비율. 방향사전은 train 주까지만
            도출하고 이벤트 표면 채점은 그 이후(OOS)만 한다 (2026-07-07 레드팀 실증: 전표본
            방향사전 = 이벤트·레버 t 부분 in-sample. 라이브 경로는 자연 PIT 라 무결, 15 §4-1).

    Returns:
        scorecard(표면 성적) + certify(2단 깔때기 verdict + spaP + nEff) + sweep(PBO·DSR·robust
        상위 종목 수) + 메타 + trainWeekMax. 가정 벌은 sealDir 시 issuedLive=False 봉인 (권위
        라이브만).
    """
    if matrices is not None:
        weekMap, weekEnd, priceM, fundM, eventM = matrices
    else:
        weekMap, weekEnd, priceM, fundM, eventM = _cycle._buildMatrices(dataDir, market)
    if labels is None:
        tbl = _cycle.marketTable(market)
        labels = _sc.weeklyLabels(weekEnd, tbl.dailyPrices(dataDir))
    # 분할 기준 = 적합물의 데이터 커버리지(이벤트 주). 라벨 전체 기준이면 이벤트 커버리지(KR
    # 2022-11~)가 전부 OOS 쪽에 몰려 train 이 공집합 = 방향사전 소멸 (2026-07-07 실측). 이벤트
    # 구간의 앞 절반으로 학습, 뒤 절반 OOS 채점이 공정한 재판정이다.
    evWeeks = sorted(eventM["week"].unique().to_list()) if eventM.height else []
    trainWeekMax = evWeeks[max(int(len(evWeeks) * trainFrac) - 1, 0)] if evWeeks else None
    directionByType = _sc.deriveEventDirections(eventM, labels, trainWeekMax=trainWeekMax)
    readings = _opine.opine(priceM, fundM, eventM, directionByType=directionByType)
    scored = readings.select("code", "week", "surface", "direction", "score")
    if trainWeekMax is not None:
        # 적합물(이벤트 방향사전) 표면은 OOS 주만 채점 = 자기채점 순환 차단. 연속 표면은 무적합이라 전 구간.
        scored = scored.filter(~(pl.col("surface").str.starts_with("event.") & (pl.col("week") <= trainWeekMax)))
    card = _sc.scorecard(scored, labels)
    spreads = _sc.surfaceWeeklySpreads(scored, labels)
    surfaces = spreads["surface"].unique().sort().to_list() if spreads.height else []
    certifyRes = (
        _certify.certify(spreads, nBoot=nBoot)
        if spreads.height and spreads["week"].n_unique() >= 2
        else {"surfaces": card.head(0), "spaP": 1.0, "nEff": 0.0, "T": 0}
    )
    # 가정 sweep: 가중 스킴 x topK x minSurfaces 격자 → 성과 행렬 → PBO/DSR/robust.
    schemes = _weightSchemes(certifyRes, surfaces) if surfaces else {}
    sweepOut = {"pbo": None, "dsr": None, "oosDegradeSlope": None, "robustCount": 0, "nConfigs": 0}
    grid = []
    if schemes:
        grid = _assume.assumptionGrid(schemes, topKs=(10, 20), minSurfaces=(1, 2))
        applied = _assume.applyGrid(scored, labels, grid)
        perf = applied["perf"]
        if perf.shape[0] >= 2 and perf.shape[1] >= 4 and np.isfinite(perf).any():
            sBlocks = min(16, (perf.shape[1] // 2) * 2)
            pbo = _sweep.cscvPbo(perf, sBlocks=max(sBlocks, 4))
            dsr = _sweep.deflatedSharpe(perf, nEff=max(int(certifyRes["nEff"]) or 1, 1))
            robust = _sweep.robustSelection(applied["configScores"], applied["codes"])
            sweepOut = {
                "pbo": pbo["pbo"],
                "oosDegradeSlope": pbo["oosDegradeSlope"],
                "dsr": dsr["dsr"],
                "robustCount": len(robust),
                "nConfigs": len(grid),
            }
    if sealDir is not None and grid:
        stats = {c.configId: {} for c in grid}
        _assume.sealAssumptions(
            grid,
            stats,
            week=int(spreads["week"].max()) if spreads.height else 0,
            issuedLive=False,
            issuedAt=issuedAt,
            baseDir=sealDir,
        )
    return {
        "scorecard": card,
        "certify": certifyRes,
        "sweep": sweepOut,
        "weeks": int(spreads["week"].n_unique()) if spreads.height else 0,
        "surfaces": surfaces,
        "universe": int(scored["code"].n_unique()) if scored.height else 0,
        "trainWeekMax": trainWeekMax,  # 이벤트 방향사전 train 컷 (이벤트 표면 = 그 이후 OOS 만 채점)
    }
