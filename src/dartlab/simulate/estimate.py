"""E 연장 층 : 작업대 재무 분기 시계열의 예측 연장(E) 생성·봉인·채점 (L2.5 simulate).

작업대 1 포맷(code, period, account, amount)의 분기 시계열을 미래 분기로 연장한다(운영자 개념
2번: "시계열에 E 를 달아 연장선"). 방법은 실측 백테스트로 선택 (2026-07-06 KR 그리드 6.4만
표본/계정): 흐름 계정(revenue·opProfit·netIncome)=전년동기 seasonal(상대오차 중앙 0.214 vs
carry 0.741, DART 분기 누적 관행에 면역), 저량 계정(equity·asset·debt)=직전분기 carry(0.044 vs
0.114). 성장 외삽(seasonal x YoY)은 전 계정 패배로 기각 (VAR 기각과 동일 교훈: 외삽=노이즈).

점 예측 금지 계약(synth.expectationSpec)에 따라 E 는 항상 분위 5점 밴드다. 밴드 스케일은 베이크
없이 런타임 계산: 같은 그리드의 PIT 과거(asOf 이전) 부호 편차 d=(actual-pred)/scale 분위를
회사 자신 이력(최소 _MIN_OWN_HIST 관측)에서, 미달이면 계정별 풀링에서 얻는다. 분모 scale 은
|앵커| 아니라 최근 4분기 평균 |값| (0 근처를 오가는 순이익에서 |앵커| 분모가 밴드를 폭발시키던
2026-07-06 실측 결함: 삼성 순이익 p95 3,791조). 모든 E 는
expectationLedger 에 ExpectationSpec 으로 봉인되고, 실제치가 그리드에 도착하면 pinball/CRPS
채점된다. E = 등재된 기대이며 채점 없는 E 는 존재하지 않는다. E 는 표시·시뮬 전용이고 판독
피처(PIT 계단)로 역류하지 않는다 (06 §5c 보간 금지 계약).

Layer: L2.5 simulate. table·tableUs(그리드)·synth.expectationSpec·expectationLedger 의존 (하향).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from dartlab.simulate import expectationLedger as _eled
from dartlab.simulate import table as _table
from dartlab.simulate import tableUs as _tableUs
from dartlab.synth.expectationSpec import ExpectationSpec, buildExpectationId, scoreExpectation

FLOW_ACCOUNTS: tuple[str, ...] = ("revenue", "opProfit", "netIncome")
STOCK_ACCOUNTS: tuple[str, ...] = ("equity", "asset", "debt")
_QUANTS: tuple[int, ...] = (5, 25, 50, 75, 95)
_MIN_OWN_HIST = 8  # 회사 자신 오차분위 최소 관측 (미달 = 계정 풀링 밴드)
_DOMAIN_BY_ACCOUNT = {
    "revenue": "revenue",
    "opProfit": "earnings",
    "netIncome": "earnings",
    "equity": "credit",
    "asset": "credit",
    "debt": "credit",
}
ENGINE = "dartlab.simulate.estimate"
ENGINE_VERSION = "e-v2"  # e-v1 = |앵커| 분모 밴드 (기각·원장 박제), e-v2 = 4분기 평균 규모 분모


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def quarterGrid(market: str = "KR", baseDir: Path | None = None) -> pl.DataFrame:
    """시장별 재무 분기 그리드 → (code, period, rceptDate, account, amount). KR=dart, US=edgar."""
    tbl = _tableUs if market == "US" else _table
    return tbl.scanFinanceGrid(baseDir)


def _withQi(grid: pl.DataFrame) -> pl.DataFrame:
    """period "2026Q1" → 정수 분기 인덱스 qi (연속성 판단·lag 정합용)."""
    return grid.filter(pl.col("period").str.contains(r"^\d{4}Q\d$")).with_columns(
        qi=pl.col("period").str.slice(0, 4).cast(pl.Int64) * 4 + pl.col("period").str.slice(5, 1).cast(pl.Int64) - 1
    )


def _periodFromQi(qi: pl.Expr) -> pl.Expr:
    return (qi // 4).cast(pl.Utf8) + pl.lit("Q") + (qi % 4 + 1).cast(pl.Utf8)


def _histDeviations(pit: pl.DataFrame) -> pl.DataFrame:
    """PIT 과거의 방법별 부호 편차 → (code, account, d). 흐름=전년동기, 저량=직전분기 앵커.

    d = (actual - pred) / scale, scale = 직전 4분기 평균 |값| (0 근처 시계열에서 |앵커| 분모 폭발
    차단). 앵커 분기(qi-4 또는 qi-1)가 정확히 연속 관측된 행만 (결손 시계열의 엇갈린 lag 오염
    차단). 분위가 밴드 스케일이 된다 (회사 자신 또는 계정 풀링).
    """
    lag = pit.sort(["code", "account", "qi"]).with_columns(
        v1=pl.col("amount").shift(1).over(["code", "account"]),
        v2=pl.col("amount").shift(2).over(["code", "account"]),
        v3=pl.col("amount").shift(3).over(["code", "account"]),
        qi1=pl.col("qi").shift(1).over(["code", "account"]),
        v4=pl.col("amount").shift(4).over(["code", "account"]),
        qi4=pl.col("qi").shift(4).over(["code", "account"]),
    )
    isFlow = pl.col("account").is_in(list(FLOW_ACCOUNTS))
    pred = pl.when(isFlow).then(pl.col("v4")).otherwise(pl.col("v1"))
    okLag = pl.when(isFlow).then(pl.col("qi4") == pl.col("qi") - 4).otherwise(pl.col("qi1") == pl.col("qi") - 1)
    scale = (pl.col("v1").abs() + pl.col("v2").abs() + pl.col("v3").abs() + pl.col("v4").abs()) / 4
    return (
        lag.filter(okLag & pred.is_not_null() & pl.col("amount").is_not_null() & (scale > 0))
        .with_columns(d=(pl.col("amount") - pred) / scale)
        .select("code", "account", "d")
    )


def _bandQuantiles(dev: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """편차 → (회사별 밴드, 계정 풀링 밴드). 회사별은 최소 관측 미달 행 제거."""
    aggs = [pl.col("d").quantile(p / 100).alias(f"d{p}") for p in _QUANTS] + [pl.len().alias("nHist")]
    own = dev.group_by(["code", "account"]).agg(aggs).filter(pl.col("nHist") >= _MIN_OWN_HIST)
    pooled = dev.group_by("account").agg(aggs)
    return own, pooled


def estimateQuarters(
    grid: pl.DataFrame,
    *,
    asOf: str,
    horizonQ: int = 4,
    accounts: tuple[str, ...] | None = None,
) -> pl.DataFrame:
    """asOf 시점 PIT 그리드에서 미래 분기 E 밴드 생성 → 1 포맷 유지 long.

    Args:
        grid: quarterGrid 산출 (code, period, rceptDate, account, amount).
        asOf: 발행 데이터 vintage (yyyymmdd). rceptDate > asOf 행은 보지 않는다 (look-ahead 0).
        horizonQ: 몇 분기 앞까지 (1~4. 흐름 계정 앵커=전년동기가 관측 구간에 있도록 4 상한).
        accounts: 대상 계정 (None = 흐름+저량 전부).

    Returns:
        (code, account, period, qi, horizon, basis="E", anchor, method, bandSource, nHist,
        p5, p25, p50, p75, p95). 앵커 결손·0 인 시계열은 기권 = 무행 (0 대체·조작 금지).

    Guide:
        - 다음 분기 매출 E: estimateQuarters(quarterGrid(), asOf="20260619").filter(
          (pl.col("account")=="revenue") & (pl.col("horizon")==1)).
    """
    horizonQ = min(max(int(horizonQ), 1), 4)
    accounts = accounts or (FLOW_ACCOUNTS + STOCK_ACCOUNTS)
    pit = _withQi(grid).filter((pl.col("rceptDate") <= asOf) & pl.col("account").is_in(list(accounts)))
    if pit.height == 0:
        return _emptyE()
    own, pooled = _bandQuantiles(_histDeviations(pit))
    last = pit.group_by(["code", "account"]).agg(
        lastQi=pl.col("qi").max(),
        lastVal=pl.col("amount").sort_by("qi").last(),
        scale=pl.col("amount").abs().sort_by(pl.col("qi")).tail(4).mean(),
        nObs=pl.len(),
    )
    targets = last.join(pl.DataFrame({"horizon": list(range(1, horizonQ + 1))}), how="cross").with_columns(
        qi=pl.col("lastQi") + pl.col("horizon")
    )
    isFlow = pl.col("account").is_in(list(FLOW_ACCOUNTS))
    # 앵커: 흐름 = 대상 분기의 전년동기 관측값 (exact join), 저량 = 최종 관측값 carry.
    seasonalAnchor = pit.select("code", "account", anchorQi=pl.col("qi"), seasonalVal=pl.col("amount"))
    targets = (
        targets.with_columns(anchorQi=pl.col("qi") - 4)
        .join(seasonalAnchor, on=["code", "account", "anchorQi"], how="left")
        .with_columns(
            anchor=pl.when(isFlow).then(pl.col("seasonalVal")).otherwise(pl.col("lastVal")),
            method=pl.when(isFlow).then(pl.lit("seasonal")).otherwise(pl.lit("carry")),
        )
        .filter(pl.col("anchor").is_not_null() & (pl.col("scale") > 0) & (pl.col("nObs") >= 2))
    )
    ownCols = {f"d{p}": f"own{p}" for p in _QUANTS}
    j = (
        targets.join(own.rename(ownCols | {"nHist": "ownN"}), on=["code", "account"], how="left")
        .join(pooled.rename({f"d{p}": f"pool{p}" for p in _QUANTS} | {"nHist": "poolN"}), on="account", how="left")
        .with_columns(
            bandSource=pl.when(pl.col("ownN").is_not_null()).then(pl.lit("own")).otherwise(pl.lit("pooled")),
            nHist=pl.coalesce(pl.col("ownN"), pl.lit(0)).cast(pl.Int64),
        )
    )
    for p in _QUANTS:
        dq = pl.coalesce(pl.col(f"own{p}"), pl.col(f"pool{p}"))
        j = j.with_columns((pl.col("anchor") + dq * pl.col("scale")).alias(f"p{p}"))
    return (
        j.filter(pl.col("p5").is_not_null())
        .with_columns(period=_periodFromQi(pl.col("qi")), basis=pl.lit("E"))
        .select(
            "code",
            "account",
            "period",
            "qi",
            "horizon",
            "basis",
            "anchor",
            "method",
            "bandSource",
            "nHist",
            "p5",
            "p25",
            "p50",
            "p75",
            "p95",
        )
        .sort(["code", "account", "horizon"])
    )


def _emptyE() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "account": pl.Utf8,
            "period": pl.Utf8,
            "qi": pl.Int64,
            "horizon": pl.Int64,
            "basis": pl.Utf8,
            "anchor": pl.Float64,
            "method": pl.Utf8,
            "bandSource": pl.Utf8,
            "nHist": pl.Int64,
            "p5": pl.Float64,
            "p25": pl.Float64,
            "p50": pl.Float64,
            "p75": pl.Float64,
            "p95": pl.Float64,
        }
    )


def seriesWithE(grid: pl.DataFrame, eFrame: pl.DataFrame, *, code: str | None = None) -> pl.DataFrame:
    """실적(A)+연장(E) 통합 시계열 → (code, account, period, basis, value, p5, p95). 1 포맷 유지.

    Args:
        grid: quarterGrid 산출 (실적). eFrame: estimateQuarters 산출 (E). code: 단일 종목 필터.

    Returns:
        실적 행 basis="A"(value=amount, 밴드 null) + E 행 basis="E"(value=p50, p5/p95 밴드).
        운영자 개념 2번의 "연장선" 그 자체: 이 프레임 하나로 과거~미래가 이어진다.

    Guide:
        - 프로파일/보고서 입력: seriesWithE(quarterGrid(), estimateQuarters(...), code="005930").
    """
    a = _withQi(grid).select(
        "code",
        "account",
        "period",
        basis=pl.lit("A"),
        value=pl.col("amount"),
        p5=pl.lit(None, dtype=pl.Float64),
        p95=pl.lit(None, dtype=pl.Float64),
    )
    e = eFrame.select("code", "account", "period", "basis", value=pl.col("p50"), p5=pl.col("p5"), p95=pl.col("p95"))
    out = pl.concat([a, e], how="vertical").sort(["code", "account", "period"])
    return out.filter(pl.col("code") == code) if code else out


def sealEstimates(
    eFrame: pl.DataFrame,
    *,
    asOf: str,
    market: str = "KR",
    live: bool = True,
    baseDir: Path | None = None,
    issuedAt: str | None = None,
) -> int:
    """E 프레임을 expectationLedger 에 ExpectationSpec 으로 봉인. 반환 = 신규 봉인 행 수.

    Args:
        eFrame: estimateQuarters 산출. asOf: 데이터 vintage. market: 변수 접두 ("KR"|"US").
        live: False = backfill (공개 성적표 혼합 금지 라벨).
        baseDir: 원장 루트 override. issuedAt: 발행 시각 override (기본 now UTC).

    Returns:
        신규 봉인 수. 같은 (variable, targetPeriod, horizon, asOf, engineVersion) 기존 봉인은 스킵
        (같은 vintage 재발행 무의미. 새 vintage 또는 방법 개정 재발행은 정당한 revision 이력 = 새 행).
    """
    if eFrame.height == 0:
        return 0
    stamp = issuedAt or _nowUtc()
    unit = "USD" if market == "US" else "KRW"
    existing = _eled.readExpectations(baseDir=baseDir)
    seen: set[tuple] = set()
    if existing is not None and existing.height:
        prior = existing.filter((pl.col("engine") == ENGINE) & (pl.col("engineVersion") == ENGINE_VERSION))
        seen = {
            (r["variable"], r["targetPeriod"], r["horizon"], r["asOf"])
            for r in prior.select("variable", "targetPeriod", "horizon", "asOf").iter_rows(named=True)
        }
    rows: list[ExpectationSpec] = []
    for r in eFrame.iter_rows(named=True):
        variable = f"{market}.{r['code']}.{r['account']}"
        key = (variable, r["period"], r["horizon"], asOf)
        if key in seen:
            continue
        warnings = ("pooledBand",) if r["bandSource"] == "pooled" else ()
        rows.append(
            ExpectationSpec(
                expectationId=buildExpectationId(
                    _DOMAIN_BY_ACCOUNT[r["account"]], variable, "Q", r["horizon"], r["period"], stamp
                ),
                domain=_DOMAIN_BY_ACCOUNT[r["account"]],
                variable=variable,
                unit=unit,
                freq="Q",
                horizon=r["horizon"],
                targetPeriod=r["period"],
                issuedAt=stamp,
                issuedLive=live,
                asOf=asOf,
                engine=ENGINE,
                engineVersion=ENGINE_VERSION,
                kind="quantiles",
                quantiles={p: float(r[f"p{p}"]) for p in _QUANTS},
                baselines={"anchor": float(r["anchor"])},
                sourceRefs=(f"simulate.quarterGrid.{market}", f"method.{r['method']}"),
                warnings=warnings,
            )
        )
    _eled.appendExpectations(rows, baseDir=baseDir)
    return len(rows)


def scoreEstimatesDue(
    *,
    market: str = "KR",
    baseDir: Path | None = None,
    dataDir: Path | None = None,
    grid: pl.DataFrame | None = None,
) -> int:
    """실제치가 그리드에 도착한 미채점 E 를 pinball/CRPS 채점. 반환 = 채점 행 수.

    Args:
        market: 시장 (그리드·변수 접두 일치 필수). baseDir: 원장 루트. dataDir: 그리드 데이터 루트.
        grid: 주입 그리드 (None = quarterGrid 스캔. 테스트·백테스트용).

    Returns:
        채점 수. 실제치 미도착(분기보고 미공시)은 pending 유지 (error 봉인은 조회 실패에만).
    """
    due = _eled.readExpectations(baseDir=baseDir, unscoredOnly=True)
    if due is None or due.height == 0:
        return 0
    due = due.filter((pl.col("engine") == ENGINE) & pl.col("variable").str.starts_with(f"{market}."))
    if due.height == 0:
        return 0
    if grid is None:
        grid = quarterGrid(market, dataDir)
    actual = grid.select(
        variable=pl.lit(f"{market}.") + pl.col("code") + pl.lit(".") + pl.col("account"),
        targetPeriod=pl.col("period"),
        actualVal=pl.col("amount"),
        actualAsOf=pl.col("rceptDate"),
    )
    j = due.join(actual, on=["variable", "targetPeriod"], how="inner")
    if j.height == 0:
        return 0
    stamp = _nowUtc()
    scores = [
        scoreExpectation(_eled.specFromRow(r), r["actualVal"], scoredAt=stamp, actualAsOf=r["actualAsOf"])
        for r in j.iter_rows(named=True)
    ]
    _eled.appendScores(scores, baseDir=baseDir)
    return len(scores)
