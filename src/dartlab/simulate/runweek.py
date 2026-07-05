"""주간 오케스트레이션 : 전 모듈 배선 → 공개 봉인 블록 (L2.5 simulate).

전 모듈을 주간 사이클로 묶는다 (06 §7b 공개 봉인 원장). 대상 주 판독을 발행·봉인하고
(readingCycle) 지평 경과분을 채점한 뒤, 표면 손실을 AdaHedge 로 결합해 가중을 산출하고
(combine), 성적표·인증(certify)·비용 바닥(costs) net 게이트·레짐 태그(regime)를 얹어 board·top10
을 낸 다음, 주 1블록 해시체인으로 봉인한다. 블록 = {판독 요약, 비용 바닥, 레짐 태그, ACI 커버리지,
결합 가중, 인증 요약, 코드 버전 해시, prevHash}. 채점은 다음 블록에서 "직전 블록 + 공개 데이터"의
순수함수라 외부인이 replay 로 재검산 가능하다. OpenTimestamps 앵커는 운영 런북(블록 해시에 적용).

Layer: L2.5 simulate. readingCycle·readingScorecard·board·combine·certify·costs·regime 배선.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

from dartlab.simulate import board as _board
from dartlab.simulate import certify as _certify
from dartlab.simulate import combine as _combine
from dartlab.simulate import costs as _costs
from dartlab.simulate import readingCycle as _cycle
from dartlab.simulate import readingLedger as _ledger
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import regime as _regime

BLOCK_SUBDIR = "readingBlocks"
CODE_VERSION = "reading-v2"
_LOSS_SCALE = 0.02  # 표면 손실 사전 봉인 함수의 스케일: loss = 1/(1+exp(spread/s0)) (spread>0 → loss<0.5)
_CERTIFY_MIN_WEEKS = 20  # 인증 최소 채점 주 (미달이면 인증 스킵)


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def codeVersionHash() -> str:
    """코드 버전 봉인 해시: 판독 코드 + 레짐 분류기 + 손실 스케일 (변경 = 새 시리즈)."""
    s = f"{CODE_VERSION}|regime:{_regime.regimeVersionHash()}|lossScale:{_LOSS_SCALE}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def hashBlock(block: dict) -> str:
    """블록의 결정론 SHA256 (정렬 JSON, prevHash 포함이라 체인 변조 증거)."""
    canonical = json.dumps(block, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def adaHedgeWeights(spreads: pl.DataFrame) -> dict[str, float]:
    """표면 주간 스프레드 시계열 → AdaHedge 결합 가중 (사전 봉인 손실 함수). 부족하면 {} (균등).

    Args:
        spreads: surfaceWeeklySpreads 산출 (surface, week, spread).

    Returns:
        {surface: weight}. 손실 = 1/(1+exp(spread/s0)) 를 [0,1] 봉인 손실로 AdaHedge 결합해 사후
        최강 표면 추종. 주 2 미만·표면 0 이면 {} (board 균등 fallback).
    """
    if spreads.height == 0:
        return {}
    wide = spreads.pivot(values="spread", index="week", on="surface", aggregate_function="first").sort("week")
    surfaces = [c for c in wide.columns if c != "week"]
    if len(wide) < 2 or not surfaces:
        return {}
    W = wide.select(surfaces).to_numpy().astype(float)
    loss = 1.0 / (1.0 + np.exp(W / _LOSS_SCALE))  # spread>0 = 좋음 = 낮은 손실
    res = _combine.adaHedge(loss)
    fw = res["finalWeights"]
    return {s: float(fw[i]) for i, s in enumerate(surfaces)}


def _certifiedNetSpread(certifyRes: dict | None) -> dict[str, float]:
    """certify 산출 → {surface: shrunkMean} (인증·발굴 표면만, net 게이트 엣지용)."""
    if certifyRes is None or certifyRes["surfaces"].height == 0:
        return {}
    df = certifyRes["surfaces"].filter(pl.col("verdict").is_in(["인증", "발굴"]))
    return {r["surface"]: float(r["shrunkMean"]) for r in df.iter_rows(named=True)}


def _edgeByCode(weekReadings: pl.DataFrame, certifiedNet: dict[str, float]) -> pl.DataFrame:
    """그 주 판독 → 종목별 기대 엣지 = 발화 인증표면 shrunk 스프레드 x 방향 x 강도 합. net 게이트용."""
    if not certifiedNet or weekReadings.height == 0:
        return pl.DataFrame(schema={"code": pl.Utf8, "edge": pl.Float64})
    r = weekReadings.filter(pl.col("surface").is_in(list(certifiedNet)) & pl.col("score").is_not_null())
    r = r.with_columns(
        nm=pl.col("surface").replace_strict(certifiedNet, default=0.0),
        strength=(pl.col("score") - 0.5).abs() * 2,
    ).with_columns(contrib=pl.col("nm") * pl.col("direction") * pl.col("strength"))
    return r.group_by("code").agg(edge=pl.col("contrib").sum())


def buildBlock(
    week: int,
    market: str,
    readings: pl.DataFrame,
    scorecard: pl.DataFrame,
    boardTop: pl.DataFrame,
    top10: pl.DataFrame,
    *,
    prevHash: str = "",
    issuedAt: str | None = None,
    costFloorMedian: float | None = None,
    regimeTag: str | None = None,
    combinedWeights: dict[str, float] | None = None,
    certifySummary: dict | None = None,
    aciCoverage: float | None = None,
) -> dict:
    """주간 블록 조립 + 해시 (06 §7b 공개 봉인). 판독은 요약(표면별 수·방향)만 담아 가볍게."""
    surfSummary = (
        {}
        if readings.height == 0
        else {
            r["surface"]: {"n": r["n"], "up": r["up"], "down": r["down"], "abstain": r["abstain"]}
            for r in readings.group_by("surface")
            .agg(
                n=pl.len(),
                up=(pl.col("direction") == 1).sum(),
                down=(pl.col("direction") == -1).sum(),
                abstain=pl.col("score").is_null().sum() if "score" in readings.columns else pl.lit(0),
            )
            .iter_rows(named=True)
        }
    )
    body = {
        "week": week,
        "market": market,
        "codeVersion": CODE_VERSION,
        "codeVersionHash": codeVersionHash(),
        "issuedAt": issuedAt or _nowUtc(),
        "readingCount": readings.height,
        "surfaceSummary": surfSummary,
        "scorecard": scorecard.to_dicts() if scorecard.height else [],
        "boardTop": boardTop.select("code", "consensus").to_dicts() if boardTop.height else [],
        "top10": top10.select("code", "consensus").to_dicts() if top10.height else [],
        "costFloorMedian": costFloorMedian,
        "regimeTag": regimeTag,
        "combinedWeights": combinedWeights or {},
        "certifySummary": certifySummary,
        "aciCoverage": aciCoverage,
        "prevHash": prevHash,
        "disclaimer": _board.DISCLAIMER,
    }
    body["hash"] = hashBlock(body)
    return body


def _blockDir(baseDir: Path | None) -> Path:
    root = _ledger.ledgerDir(baseDir).parent
    return root / BLOCK_SUBDIR


def _lastHash(blockDir: Path) -> str:
    files = sorted(blockDir.glob("block_*.json"))
    if not files:
        return ""
    return json.loads(files[-1].read_text(encoding="utf-8")).get("hash", "")


def _asCode(df: pl.DataFrame) -> pl.DataFrame:
    """원장 stockCode → code (board·성적표 공통 스키마)."""
    if "code" not in df.columns and "stockCode" in df.columns:
        return df.rename({"stockCode": "code"})
    return df


def runWeek(
    *,
    market: str = "KR",
    week: int | None = None,
    live: bool = True,
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    matrices: tuple | None = None,
    labels: pl.DataFrame | None = None,
    surfaceWeights: dict[str, float] | None = None,
    nBoot: int = 500,
) -> dict:
    """대상 주 발행·봉인 → 채점 → AdaHedge 결합 → 인증·net 게이트 → 해시체인 블록. 반환 = 블록 dict.

    Args:
        market/week/live: 발행 메타 (week None = 최신).
        baseDir: 원장/블록 루트. dataDir: 데이터 SSOT 루트.
        matrices: 주입 (weekMap, weekEnd, priceM, fundM, eventM) (테스트). 주입 시 레짐·비용 스캔 생략.
        labels: 채점 라벨 (테스트 주입). None = table 계산.
        surfaceWeights: 강제 가중 (None = AdaHedge 산출). nBoot: 인증 부트스트랩 반복.

    Returns:
        봉인 블록 dict (06 §7b 필드 + hash·prevHash). 전 모듈 배선: issue→score→AdaHedge→certify→
        net 게이트→regime→해시체인. 미발행이면 readingCount=0 블록.
    """
    injected = matrices is not None
    tbl = _cycle.marketTable(market)
    weekMap, weekEnd, priceM, fundM, eventM = matrices or _cycle._buildMatrices(dataDir, market)
    lab = labels if labels is not None else _sc.weeklyLabels(weekEnd, tbl.dailyPrices(dataDir))
    directionByType = _sc.deriveEventDirections(eventM, lab)
    _cycle.issueReadings(
        market=market,
        week=week,
        live=live,
        baseDir=baseDir,
        matrices=(weekMap, weekEnd, priceM, fundM, eventM),
        directionByType=directionByType,
    )
    _cycle.scoreReadingsDue(market=market, baseDir=baseDir, dataDir=dataDir, labels=labels)
    if week is None:
        led = _ledger.readReadings(baseDir=baseDir)
        week = int(led["week"].max()) if led is not None and led.height else 0
    _wk = _ledger.readReadings(week=week, live=True, baseDir=baseDir)
    _all = _ledger.readReadings(live=True, baseDir=baseDir)
    weekReadings = _asCode(_wk if _wk is not None else _emptyReadings())
    allReadings = _asCode(_all if _all is not None else _emptyReadings())

    # 표면 스프레드 시계열 → AdaHedge 결합 가중 + 인증.
    spreads = (
        _sc.surfaceWeeklySpreads(allReadings.select("code", "week", "surface", "direction", "score"), lab)
        if allReadings.height
        else pl.DataFrame(schema={"surface": pl.Utf8, "week": pl.Int64, "spread": pl.Float64})
    )
    weights = surfaceWeights if surfaceWeights is not None else adaHedgeWeights(spreads)
    certifyRes = None
    if spreads.height and spreads["week"].n_unique() >= _CERTIFY_MIN_WEEKS:
        certifyRes = _certify.certify(spreads, nBoot=nBoot)
    certifiedNet = _certifiedNetSpread(certifyRes)

    weekSel = (
        weekReadings.select("code", "surface", "direction", "score").with_columns(week=pl.lit(week))
        if weekReadings.height
        else pl.DataFrame(
            schema={"code": pl.Utf8, "surface": pl.Utf8, "direction": pl.Int64, "score": pl.Float64, "week": pl.Int64}
        )
    )
    card = _sc.scorecard(weekSel, lab) if weekReadings.height else pl.DataFrame()
    boardTop = (
        _board.board100(weekSel, surfaceWeights=weights or None, n=100)
        if weekReadings.height
        else pl.DataFrame(schema={"code": pl.Utf8, "consensus": pl.Float64})
    )

    # 회피(red-flag) = 이벤트 표면 하방(희석·거버넌스), net-of-cost 게이트.
    redFlag = set(
        weekReadings.filter((pl.col("surface").str.starts_with("event.")) & (pl.col("direction") == -1))[
            "code"
        ].to_list()
    )
    costFloorMedian = None
    netPos = None
    if not injected:  # 라이브 런만 비용 바닥 스캔 (주입 테스트는 net 게이트 생략, OOM 회피)
        cfWk = _costs.costFloorWeekly(weekEnd, tbl.dailyHighLow(dataDir), market=market).filter(pl.col("week") == week)
        if cfWk.height:
            costFloorMedian = float(cfWk["costFloor"].median())
            edge = _edgeByCode(weekReadings, certifiedNet)
            netPos = _costs.netPositive(edge, cfWk, avoidCodes=redFlag) if edge.height else set()
    top10 = (
        _board.applyGates(boardTop, redFlagCodes=redFlag, netPositiveCodes=netPos, n=10)
        if boardTop.height
        else pl.DataFrame(schema={"code": pl.Utf8, "consensus": pl.Float64})
    )

    regimeTag = None
    if not injected:  # 라이브 런만 레짐 분류 (시장 스캔)
        mw = _regime.marketWeekly(tbl.dailyPrices(dataDir))
        reg = _regime.classifyRegimes(mw).filter(pl.col("week") == week)
        regimeTag = reg["regime"][0] if reg.height else None

    certifySummary = (
        None
        if certifyRes is None
        else {
            "spaP": certifyRes["spaP"],
            "nEff": certifyRes["nEff"],
            "nCertified": int((certifyRes["surfaces"]["verdict"] == "인증").sum()),
        }
    )
    blockDir = _blockDir(baseDir)
    blockDir.mkdir(parents=True, exist_ok=True)
    block = buildBlock(
        week,
        market,
        weekReadings,
        card,
        boardTop,
        top10,
        prevHash=_lastHash(blockDir),
        costFloorMedian=costFloorMedian,
        regimeTag=regimeTag,
        combinedWeights=weights,
        certifySummary=certifySummary,
    )
    (blockDir / f"block_{week}.json").write_text(json.dumps(block, ensure_ascii=False, indent=2), encoding="utf-8")
    return block


def _emptyReadings() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "week": pl.Int64,
            "stockCode": pl.Utf8,
            "market": pl.Utf8,
            "surface": pl.Utf8,
            "asOf": pl.Utf8,
            "horizon": pl.Int64,
            "direction": pl.Int64,
            "score": pl.Float64,
            "abstainReason": pl.Utf8,
            "refs": pl.Utf8,
            "condition": pl.Utf8,
            "issuedAt": pl.Utf8,
            "issuedLive": pl.Boolean,
        }
    )
