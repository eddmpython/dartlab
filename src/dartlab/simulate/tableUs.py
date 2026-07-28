"""판독 입력 상(床) US : EDGAR 벌크 직독 → 주간 (ticker, week) 행렬 (L2.5 simulate).

table.py(KR)의 US 대칭이다 (10 §1b 시장 파라미터화). 같은 출력 스키마(code=ticker, week, 신호)를
EDGAR 원천에서 낸다: 가격 OHLCV(edgar/prices), 재무 XBRL(edgar/finance, frame 기반 분기), 공시
(edgar/allFilings, form 타입). code=ticker 로 통일해 opine·scorecard·certify 는 시장 무관하게
소비한다. 채점·중립화·비용 바닥은 시장 내 완결 (US 세율=SEC fee, costs 스프레드 추정은 동일).

Layer: L2.5 simulate. 원천 = data/edgar (prices·finance·allFilings). Company 객체 0, 벌크 직독.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.simulate.dataStore import dataDir

# XBRL 태그 → 계정 (첫 매칭 우선). 흐름(netIncome·revenue)·잔고(asset·equity·debt·shares).
_US_ACCOUNT_TAGS: dict[str, tuple[str, ...]] = {
    "netIncome": ("NetIncomeLoss", "ProfitLoss"),
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"),
    "asset": ("Assets",),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "debt": ("Liabilities",),
    "shares": (
        "CommonStockSharesOutstanding",
        "EntityCommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ),
}
# US 공시 form → 레버/이벤트 타입 (10 §1b). Form 4=내부자, NT=감사지연, 13D/G=대주주.
_US_FORM_EVENT: dict[str, str] = {
    "4": "insiderTransaction",
    "144": "insiderSale",
    "8-K": "materialEvent",
    "NT 10-K": "auditDelay",
    "NT 10-Q": "auditDelay",
    "SC 13D": "largeHolding",
    "SC 13D/A": "largeHolding",
    "SC 13G": "largeHolding",
    "SC 13G/A": "largeHolding",
    "424B2": "securitiesOffering",
    "424B5": "securitiesOffering",
}


_EMPTY_PX = {
    "code": pl.Utf8,
    "date": pl.Utf8,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "vol": pl.Float64,
}


def _pricesRaw(baseDir: Path | None) -> pl.DataFrame:
    """edgar/prices → (code=ticker, date, high, low, close, vol). recent.parquet(ticker 열) +
    company/<TICKER>.parquet(ticker=파일명). 둘 다 concat, 중복 제거."""
    base = dataDir(baseDir) / "edgar/prices"
    frames = []
    cols = ["date", "high", "low", "close", "volume"]
    order = ["code", "date", "high", "low", "close", "vol"]
    if (base / "recent.parquet").exists():
        r = pl.read_parquet(base / "recent.parquet", columns=["ticker", *cols])
        frames.append(r.rename({"ticker": "code", "volume": "vol"}).select(order))
    comp = base / "company"
    if comp.exists() and any(comp.glob("*.parquet")):
        c = (
            pl.scan_parquet(str(comp / "*.parquet"), include_file_paths="fp", extra_columns="ignore")
            .select(*cols, "fp")
            .collect(engine="streaming")
            .with_columns(code=pl.col("fp").str.extract(r"([^/\\]+)\.parquet$"))
            .rename({"volume": "vol"})
            .select(order)
        )
        frames.append(c)
    if not frames:
        return pl.DataFrame(schema=_EMPTY_PX)
    df = pl.concat(frames, how="vertical")
    return (
        df.with_columns(
            pl.col("date").cast(pl.Utf8),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            pl.col("vol").cast(pl.Float64),
        )
        .filter((pl.col("close") > 0) & (pl.col("high") > 0) & (pl.col("low") > 0))
        .unique(["code", "date"])
    )


def weekCalendar(baseDir: Path | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    """US 거래일에서 주 달력 → (weekMap[date,week], weekEnd[week,date])."""
    cal = (
        _pricesRaw(baseDir)
        .select("date")
        .unique()
        .sort("date")
        .with_columns(d=pl.col("date").str.to_date("%Y%m%d"))
        .with_columns(week=(pl.col("d").dt.iso_year() * 100 + pl.col("d").dt.week()).cast(pl.Int64))
    )
    return cal.select("date", "week"), cal.group_by("week").agg(pl.col("date").max().alias("date"))


def dailyPrices(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 가격 (채점 라벨용) → (date, code, close, shares, mktcap). mktcap=달러거래대금(사이즈 프록시).

    US 일별 상장주식수 원천 부재라 shares=1.0 중립(corpAction 주식수 점프 검사 무력화, 40% 일수익
    검사만 유효). 사이즈 버킷 중립화는 달러거래대금(close x vol)을 프록시로 쓴다 (시장 내 완결).
    """
    px = _pricesRaw(baseDir).select("date", "code", "close", "vol")
    return px.with_columns(shares=pl.lit(1.0, dtype=pl.Float64), mktcap=pl.col("close") * pl.col("vol"))


def dailyHighLow(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 고저종가 (비용 바닥) → (date, code, high, low, close, mktcap). mktcap=달러거래대금 프록시."""
    px = _pricesRaw(baseDir)
    return px.select("date", "code", "high", "low", "close", mktcap=pl.col("close") * pl.col("vol")).filter(
        pl.col("high") >= pl.col("low")
    )


def scanFinanceGrid(baseDir: Path | None = None) -> pl.DataFrame:
    """edgar/finance XBRL → (code, period, rceptDate, account, amount) long. frame 기반 분기.

    cik→ticker 매핑(docs)으로 code=ticker 통일. 태그→계정, frame(CYyyyyQq)=period, filed=rceptDate.
    같은 (code,period,account) 다중 공시는 최신 접수 우선.
    """
    finDir = dataDir(baseDir) / "edgar/finance"
    tagMap = {tag: acct for acct, tags in _US_ACCOUNT_TAGS.items() for tag in tags}
    # cik→ticker (docs 단일 글롭 스캔)
    docs = dataDir(baseDir) / "edgar/docs"
    ck = (
        pl.scan_parquet(str(docs / "*.parquet"), extra_columns="ignore", missing_columns="insert")
        .select("cik", "ticker")
        .unique()
        .collect(engine="streaming")
        if docs.exists()
        else pl.DataFrame(schema={"cik": pl.Utf8, "ticker": pl.Utf8})
    )
    df = (
        pl.scan_parquet(str(finDir / "*.parquet"), extra_columns="ignore", missing_columns="insert")
        .select("cik", "tag", "frame", "filed", "val", "unit")
        .filter(pl.col("tag").is_in(list(tagMap)) & pl.col("frame").is_not_null())
        .collect(engine="streaming")
    )
    df = df.with_columns(pl.col("cik").cast(pl.Utf8)).join(
        ck.with_columns(pl.col("cik").cast(pl.Utf8)), on="cik", how="inner"
    )
    out = (
        df.with_columns(
            account=pl.col("tag").replace_strict(tagMap, default=None),
            period=pl.col("frame").cast(pl.Utf8).str.replace("^CY", "").str.replace("I$", ""),
            rceptDate=pl.col("filed").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8),
            amount=pl.col("val").cast(pl.Float64, strict=False),
        )
        .rename({"ticker": "code"})
        .filter(pl.col("account").is_not_null() & pl.col("period").str.contains(r"\d{4}Q\d"))
        .select("code", "period", "rceptDate", "account", "amount")
    )
    return out.sort("rceptDate", descending=True).unique(subset=["code", "period", "account"], keep="first")


def marketCap(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 시총 → (date, code, mktcap). shares(finance 최신) x close. shares 부재는 달러거래대금 프록시."""
    grid = scanFinanceGrid(baseDir)
    shares = (
        grid.filter(pl.col("account") == "shares")
        .sort("rceptDate", descending=True)
        .unique("code", keep="first")
        .select("code", sharesOut=pl.col("amount"))
    )
    px = _pricesRaw(baseDir).select("date", "code", "close", "vol")
    j = px.join(shares, on="code", how="left")
    return (
        j.with_columns(
            mktcap=pl.when(pl.col("sharesOut") > 0)
            .then(pl.col("close") * pl.col("sharesOut"))
            .otherwise(pl.col("close") * pl.col("vol"))
        )
        .select("date", "code", "mktcap")
        .filter(pl.col("mktcap") > 0)
    )


def fundWeekly(weekEnd: pl.DataFrame, mktcap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """재무 비율 표면 입력: 주말 시총에 PIT as-of 재무 → (code, week, ep, bm). 계단 분자/일별 분모."""
    grid = scanFinanceGrid(baseDir)
    wide = grid.pivot(values="amount", index=["code", "rceptDate"], on="account", aggregate_function="first")
    for col in ("netIncome", "equity"):
        if col not in wide.columns:
            wide = wide.with_columns(pl.lit(None, dtype=pl.Float64).alias(col))
    fund = wide.select("code", "rceptDate", "netIncome", "equity").drop_nulls("rceptDate").sort(["code", "rceptDate"])
    snap = (
        weekEnd.join(mktcap, on="date", how="inner")
        .sort(["code", "date"])
        .join_asof(fund, left_on="date", right_on="rceptDate", by="code", strategy="backward")
        .drop_nulls("rceptDate")
    )
    return snap.with_columns(ep=pl.col("netIncome") / pl.col("mktcap"), bm=pl.col("equity") / pl.col("mktcap")).select(
        "code", "week", "ep", "bm"
    )


def priceWeekly(weekMap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """가격 표면 입력 → (code, week, ret5, mom20x5, volShock, high52). 종목 내 거래일 shift (look-ahead 0).

    주말 스냅샷 = (code, week) 마지막 거래일 1행 (KR priceWeekly 와 동일 결함 동시 정정, 2026-07-06).
    """
    df = _pricesRaw(baseDir).select("date", "code", "close", "vol", "high").sort(["code", "date"])
    c = pl.col("close")
    df = df.with_columns(
        ret5=(c / c.shift(5).over("code") - 1),
        mom20x5=(c.shift(5).over("code") / c.shift(25).over("code") - 1),
        volShock=(pl.col("vol") / pl.col("vol").rolling_mean(20).over("code") - 1),
        high52=(c / c.rolling_max(250).over("code")),
        maxRet20=(c / c.shift(1).over("code") - 1).rolling_max(20).over("code"),  # MAX 복권성(회피)
    )
    return (
        df.join(weekMap.rename({"date": "d0"}), left_on="date", right_on="d0", how="inner")
        .sort(["code", "date"])
        .group_by(["code", "week"], maintain_order=True)
        .last()
        .select("code", "week", "ret5", "mom20x5", "volShock", "high52", "maxRet20")
    )


def eventWeekly(weekMap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """공시 표면 입력: allFilings form → (code, week, reportType). US form 타입 정규화."""
    base = dataDir(baseDir) / "edgar/allFilings"
    paths = [str(p) for p in base.glob("*.parquet")] if base.exists() else []
    if not paths:
        return pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    ev = pl.concat([pl.read_parquet(p, columns=["stockCode", "filingDate", "form"]) for p in paths])
    ev = ev.with_columns(
        reportType=pl.col("form").replace_strict(_US_FORM_EVENT, default=None),
        date=pl.col("filingDate").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8),
    ).drop_nulls("reportType")
    return (
        ev.select(pl.col("stockCode").alias("code"), "date", "reportType")
        .join(weekMap, on="date", how="left")
        .drop_nulls("week")
        .select("code", "week", "reportType")
    )
