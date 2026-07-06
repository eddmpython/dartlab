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
from dartlab.simulate import enginefeeds as _enginefeeds
from dartlab.simulate import estimate as _estimate
from dartlab.simulate import readingCycle as _cycle
from dartlab.simulate import readingLedger as _ledger
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import regime as _regime

BLOCK_SUBDIR = "readingBlocks"
CODE_VERSION = "reading-v3"  # v3: 재무 그리드 연결(CFS) 우선 정정 (fund 표면 입력 semantics 변경)
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


def otsAnchor(block: dict) -> dict:
    """블록 해시의 OpenTimestamps 앵커 페이로드 (06 §7b, 운영 런북에서 비트코인 블록에 무료 앵커).

    엔진은 앵커 요청(해시·알고리즘)을 낸다. 실제 stamp 제출·.ots 증명 공개는 운영자 독립 런북
    (외부 서비스 의존이라 엔진 결정론 밖). 앵커되면 봉인 시각이 비트코인 블록타임으로 증명된다.
    """
    return {
        "hash": block.get("hash"),
        "algorithm": "sha256",
        "week": block.get("week"),
        "runbook": "ots stamp <hash> → .ots 증명 저장·공개. 외부인이 비트코인 블록타임으로 봉인 시각 검증.",
    }


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


def _netGate(
    weekReadings: pl.DataFrame, certifiedNet: dict[str, float], cfWk: pl.DataFrame, redFlag: set[str]
) -> set[str] | None:
    """net-of-cost 게이트 종목집합. 인증 표면 0(콜드스타트) = 엣지 계산 불가 → None (게이트 미적용).

    빈 집합을 돌려주면 applyGates 가 전 종목을 걸러 top10 이 공백이 된다 (2026-07-06 라이브 첫 주
    실측 결함). 인증 표면이 있는데 그 주 발화 엣지가 없으면 빈 집합 (통과 0 이 정직)."""
    if not certifiedNet:
        return None
    edge = _edgeByCode(weekReadings, certifiedNet)
    return _costs.netPositive(edge, cfWk, avoidCodes=redFlag) if edge.height else set()


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
    latticeDropped: list[str] | None = None,
    estimateSummary: dict | None = None,
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
        "latticeDropped": latticeDropped,  # 격자 오버레이 제거 종목 (None = 미적용 명시)
        "estimateSummary": estimateSummary,  # E 봉인·채점 요약 (None = 주입 경로 미실행 명시)
        "prevHash": prevHash,
        "disclaimer": _board.DISCLAIMER,
    }
    body["hash"] = hashBlock(body)
    return body


def _blockDir(baseDir: Path | None) -> Path:
    root = _ledger.ledgerDir(baseDir).parent
    return root / BLOCK_SUBDIR


def _lastHash(blockDir: Path, week: int | None = None) -> str:
    files = sorted(blockDir.glob("block_*.json"))
    if week is not None:
        files = [f for f in files if f.stem < f"block_{week}"]  # 같은 주 재발간 시 자기/미래 블록 참조 방지
    if not files:
        return ""
    return json.loads(files[-1].read_text(encoding="utf-8")).get("hash", "")


def _asCode(df: pl.DataFrame) -> pl.DataFrame:
    """원장 stockCode → code (board·성적표 공통 스키마)."""
    if "code" not in df.columns and "stockCode" in df.columns:
        return df.rename({"stockCode": "code"})
    return df


def _latticeOverlay(
    candidates: pl.DataFrame, weekEnd: pl.DataFrame, week: int, dataDir: Path | None, *, topK: int = 10
) -> tuple[pl.DataFrame, list[str]]:
    """격자 리스크 오버레이 (14 §9 역사검증 통과 규칙): 후보에서 매크로 꼬리 최악 제거 → (top-K, 제거목록).

    hardenedTopK = base 후보 중 respP5(격자 확률가중 하방 꼬리) 최악을 쳐낸다. 역사 실측: 평균
    +1.45% -> +1.82%, 주간 p5 -7.78% -> -4.68% (알파 틸트 아니라 "덜 죽는 결정"). 베타·격자 실패
    (macro 부재 등)는 오버레이 생략 = 후보 상위 topK 그대로 (fail-open 아님: 제거목록 None 반환으로
    미적용 명시).
    """
    from dartlab.simulate import lattice as _lt
    from dartlab.simulate import scenarioSim as _ss
    from dartlab.simulate import table as _table

    asOfS = weekEnd.filter(pl.col("week") == week)["date"]
    if asOfS.len() == 0:
        return candidates.head(topK), None
    macro = _table.macroDaily(dataDir)
    betas = _table.macroBetaByCodeWide(asOfS[0], baseDir=dataDir)
    if macro.height == 0 or betas.height == 0:
        return candidates.head(topK), None
    cov = _ss.factorCovariance(macro)
    # beam 은 팩터 수에 스케일 (실측 2026-07-06: k=3 beam 1500 = 손실질량 0.67%, k=4 는 1500 이
    # 49% 손실 → 15000 이 0.98%. 팩터 1 증가당 ~x10 필요, 상한 5만 = 런타임 가드).
    k = len(cov["factors"])
    beam = min(1500 * 10 ** max(0, k - 3), 50000)
    lat = _lt.growLattice(cov, steps=8, stepDays=5, beamWidth=beam)
    dec = _lt.latticeDecision(candidates, _lt.winsorizeBetas(betas), lat, topK=topK)
    picks = _lt.hardenedTopK(candidates, dec, topK=topK, candidateExtra=max(candidates.height - topK, 0))
    dropped = [c for c in candidates["code"].to_list() if c not in picks]
    return candidates.filter(pl.col("code").is_in(picks)), dropped


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
    if not injected:  # 라이브 런만 기본 엔진 피드 설치 (주입 테스트 격리)
        _enginefeeds.installEngineFeeds()
    tbl = _cycle.marketTable(market)
    weekMap, weekEnd, priceM, fundM, eventM = matrices or _cycle._buildMatrices(dataDir, market)
    if week is None:
        # 최신 완전주 = 가격 커버 최신 주 (미래 투영 레버가 max 를 미래로 끌어 near-empty 블록 되는 것 차단).
        week = int(priceM["week"].max()) if "week" in priceM.columns and priceM.height else 0
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
            netPos = _netGate(weekReadings, certifiedNet, cfWk, redFlag)
    # top10 = 게이트 통과 후보 20 에서 격자 리스크 오버레이(14 §9 검증: 평균↑·주간 p5 꼬리 40%↓)로
    # 매크로 꼬리 최악 10 제거. 라이브 KR 만 (US 는 macro 축 미배선, 주입 테스트는 스캔 생략).
    candidates = (
        _board.applyGates(boardTop, redFlagCodes=redFlag, netPositiveCodes=netPos, n=20)
        if boardTop.height
        else pl.DataFrame(schema={"code": pl.Utf8, "consensus": pl.Float64})
    )
    latticeDropped: list[str] | None = None
    top10 = candidates.head(10)
    if not injected and market == "KR" and candidates.height > 10:
        top10, latticeDropped = _latticeOverlay(candidates, weekEnd, week, dataDir, topK=10)

    regimeTag = None
    if not injected:  # 라이브 런만 레짐 분류 (시장 스캔)
        mw = _regime.marketWeekly(tbl.dailyPrices(dataDir))
        reg = _regime.classifyRegimes(mw).filter(pl.col("week") == week)
        regimeTag = reg["regime"][0] if reg.height else None

    # E 연장 봉인·채점 (라이브 런만): 주간 심장박동이 E 원장도 함께 굴린다 (E = 상시 봉인·채점,
    # 같은 vintage 재발행은 sealEstimates 가 스킵). 실패는 격리 + 블록에 정직 기록 (판독 봉인 우선).
    estimateSummary: dict | None = None
    if not injected:
        try:
            eGrid = _estimate.quarterGrid(market, dataDir)
            eAsOf = eGrid["rceptDate"].max() if eGrid.height else None
            sealedE = 0
            if eAsOf:
                eFrame = _estimate.estimateQuarters(eGrid, asOf=eAsOf)
                sealedE = _estimate.sealEstimates(eFrame, asOf=eAsOf, market=market, baseDir=baseDir)
            scoredE = _estimate.scoreEstimatesDue(market=market, baseDir=baseDir, grid=eGrid)
            estimateSummary = {"sealed": sealedE, "scored": scoredE, "asOf": eAsOf}
        except Exception as e:  # noqa: BLE001 - E 사이클 실패가 주간 판독 봉인을 못 죽임 (오류는 블록에 명시)
            estimateSummary = {"error": f"{type(e).__name__}: {e}"}

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
        prevHash=_lastHash(blockDir, week),
        costFloorMedian=costFloorMedian,
        regimeTag=regimeTag,
        combinedWeights=weights,
        certifySummary=certifySummary,
        latticeDropped=latticeDropped,
        estimateSummary=estimateSummary,
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
