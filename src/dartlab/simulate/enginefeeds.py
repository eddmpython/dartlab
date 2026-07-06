"""엔진 피드 배선 : 작업대 기본 등록분 industry·credit (L2.5 simulate).

feeds 는 순수 레지스트리(메커니즘)고 본 모듈은 dartlab 엔진들의 기본 피드(배선)다. 산업층 =
업종 동행 모멘텀(kindList 159 업종 중앙, 자기 신호와 별개의 산업 동행 신호), 신용층 = 자금조달
공시 압력(52주 이동 건수, 만성 희석 형질의 주간 연속판). 라이브 경로(runWeek·issueReadings
matrices=None)가 installEngineFeeds 로 멱등 설치하고, 주입 테스트 경로는 미설치라 격리가 유지된다.
피드 부호는 선험 강제하지 않는다: 표면으로 등재되면 성적표·인증 깔때기가 부호와 생사를 정한다
(도태는 측정, 06 §3). 床 재사용: ctx 의 priceM·eventM 을 그대로 소비해 재스캔 0.

Layer: L2.5 simulate. feeds(레지스트리)·markets(床 라우팅)·table·surfaces 의존 (하향).
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate import estimate as _estimate
from dartlab.simulate import feeds as _feeds
from dartlab.simulate import markets as _markets
from dartlab.simulate import surfaces as _surfaces
from dartlab.simulate import table as _table

_MIN_INDUSTRY_SIZE = 5  # 업종 중앙값 최소 종목 수 (미달 업종은 결측 = 강제 0 금지)
_FIN_WINDOW_WEEKS = 52  # 자금조달 압력 이동 창


def _tbl(market: str):
    return _markets.tableModule(market) or _table


def industryFeedProvider(ctx: dict) -> pl.DataFrame:
    """업종 동행 모멘텀 → (code, week, indMom). 업종 = kindList 159 분류, 값 = 업종 중앙 mom20x5.

    Args:
        ctx: 床 컨텍스트. priceM 있으면 재스캔 0, 없으면 weekMap 으로 priceWeekly 스캔.

    Returns:
        (code, week, indMom). 업종 종목 수 _MIN_INDUSTRY_SIZE 미만 주는 무행 (기권 규율이 되살림).
    """
    priceM = ctx.get("priceM")
    if priceM is None:
        priceM = _tbl(ctx.get("market", "KR")).priceWeekly(ctx["weekMap"], ctx.get("dataDir"))
    imap = _table.industryMap(ctx.get("dataDir"))
    empty = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "indMom": pl.Float64})
    if priceM.height == 0 or imap.height == 0 or "mom20x5" not in priceM.columns:
        return empty
    j = priceM.select("code", "week", "mom20x5").drop_nulls().join(imap, on="code", how="inner")
    ind = (
        j.group_by(["industry", "week"])
        .agg(indMom=pl.col("mom20x5").median(), nInd=pl.len())
        .filter(pl.col("nInd") >= _MIN_INDUSTRY_SIZE)
    )
    return j.join(ind, on=["industry", "week"], how="inner").select("code", "week", "indMom")


def creditFeedProvider(ctx: dict) -> pl.DataFrame:
    """자금조달 압력 → (code, week, fin52w). 52주 이동 자금조달 공시 건수 (만성 희석 형질 주간판).

    Args:
        ctx: 床 컨텍스트. eventM(코드·주·타입) 있으면 재스캔 0. weekEnd 로 주 격자 정렬 (iso week
            정수는 연 경계 불연속이라 격자 인덱스로 rolling).

    Returns:
        (code, week, fin52w). 창 내 0건 종목은 무행 (발화형 연속 표면: 압력 있는 종목만 값, 부호는
        채점이 정한다). 타입 = surfaces.FINANCING_EVENTS[market] (KR 희석 3종·US securitiesOffering).
    """
    market = ctx.get("market", "KR")
    eventM = ctx.get("eventM")
    if eventM is None:
        eventM = _tbl(market).eventWeekly(ctx["weekMap"], ctx.get("dataDir"))
    empty = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "fin52w": pl.Float64})
    types = _surfaces.FINANCING_EVENTS.get(market, ())
    weekEnd = ctx.get("weekEnd")
    if eventM.height == 0 or not types or weekEnd is None or weekEnd.height == 0:
        return empty
    fin = eventM.filter(pl.col("reportType").is_in(list(types)))
    if fin.height == 0:
        return empty
    counts = fin.group_by(["code", "week"]).agg(n=pl.len().cast(pl.Float64))
    weeks = weekEnd.select("week").unique().sort("week")
    grid = fin.select("code").unique().join(weeks, how="cross")
    g = (
        grid.join(counts, on=["code", "week"], how="left")
        .with_columns(pl.col("n").fill_null(0.0))
        .sort(["code", "week"])
        .with_columns(fin52w=pl.col("n").rolling_sum(window_size=_FIN_WINDOW_WEEKS, min_samples=1).over("code"))
    )
    return g.filter(pl.col("fin52w") > 0).select("code", "week", "fin52w")


def estimateFeedProvider(ctx: dict) -> pl.DataFrame:
    """전방 E/P → (code, week, epFwd). E 층의 시뮬 소비 루프 (최신 주 한정 라이브 누적).

    epFwd = 다음 분기 순이익 E(p50) / asOf 시총. E 는 PIT 과거의 결정론 함수(전년동기 앵커 +
    과거 오차분위)라 look-ahead 0 이며, 실적 시계열로의 역류(보간)가 아니라 별도 표식 표면이다.
    trailing fund.ep 대비 전방 정보가 있는지는 성적표·인증 깔때기가 측정한다 (선험 주장 없음).
    과거 주 backfill 은 주별 vintage 재계산이 필요해 미포함 (라이브 누적, 정직 라벨).

    Args:
        ctx: 床 컨텍스트 (weekEnd·dataDir·market 소비).

    Returns:
        (code, week, epFwd). 최신 주 1개 행만. E 결손(이력<2분기 등)은 무행 (기권 규율이 되살림).
    """
    market = ctx.get("market", "KR")
    weekEnd = ctx.get("weekEnd")
    empty = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "epFwd": pl.Float64})
    if weekEnd is None or weekEnd.height == 0:
        return empty
    week = int(weekEnd["week"].max())
    asOf = weekEnd.filter(pl.col("week") == week)["date"][0]
    grid = _estimate.quarterGrid(market, ctx.get("dataDir"))
    e = _estimate.estimateQuarters(grid, asOf=asOf, horizonQ=1, accounts=("netIncome",))
    if e.height == 0:
        return empty
    caps = _tbl(market).marketCap(ctx.get("dataDir")).filter(pl.col("date") <= asOf)
    if caps.height == 0:
        return empty
    day = caps.filter(pl.col("date") == caps["date"].max())
    return (
        e.filter(pl.col("horizon") == 1)
        .join(day.select("code", "mktcap"), on="code", how="inner")
        .filter(pl.col("mktcap") > 0)
        .select("code", week=pl.lit(week, dtype=pl.Int64), epFwd=pl.col("p50") / pl.col("mktcap"))
    )


def installEngineFeeds() -> None:
    """기본 엔진 피드 멱등 설치 (라이브 경로 전용 호출. 주입 테스트 경로는 미설치 = 격리).

    등록 후에는 일반 피드와 동일 규율: opine 자동 표면(industry.indMom·credit.fin52w·
    estimate.epFwd) → 기권 완전성 → 성적표·인증·격자 무수정 흡수. 새 엔진 추가 = 여기 1줄
    (또는 외부 registerCompanyFeed).
    """
    _feeds.registerCompanyFeed(_feeds.CompanyFeed("industry", industryFeedProvider, markets=("KR",)))
    _feeds.registerCompanyFeed(_feeds.CompanyFeed("credit", creditFeedProvider, markets=("KR", "US")))
    _feeds.registerCompanyFeed(_feeds.CompanyFeed("estimate", estimateFeedProvider, markets=("KR", "US")))
