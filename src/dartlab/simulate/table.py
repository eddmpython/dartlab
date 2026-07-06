"""판독 입력 상(床) : 3축(가격·재무·이벤트) 벌크 직독 → 주간 (code, week) 행렬 (L2.5 simulate).

시뮬레이터가 매주 소비하는 입력 행렬을 무bake·벌크 parquet 직독으로 차린다 (Company 객체 루프
0, 06 §7). 세 축 전부 SSOT 직독이라 별도 산출물 굽기 없이 런타임에 세운다 (실측: 재무 그리드
3.7초·이벤트 정규화 2.4초·가격 신호 초 단위). 재무는 raw panel(섹션 원문)이 아니라 수치
SSOT(dart/finance)를 읽는다.

Layer: L2.5 simulate. 원천은 벌크 데이터 SSOT (gov/prices·dart/finance·dart/allFilings).
정정공시 vintage·잠정실적 이중 이벤트는 fundDaily 본구현 확장 대상 (v0 는 최신 접수 우선).
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from dartlab.simulate.surfaces import normalizeEventType

# account_id(IFRS 표준) 우선, account_nm 부분일치 폴백. (표준 id 목록, nm 키워드 목록)
_ACCOUNT_MAP: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "revenue": (("ifrs-full_Revenue", "ifrs_Revenue"), ("매출액", "영업수익")),
    "opProfit": (("dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"), ("영업이익",)),
    "netIncome": (("ifrs-full_ProfitLoss", "ifrs_ProfitLoss"), ("당기순이익", "분기순이익")),
    "asset": (("ifrs-full_Assets", "ifrs_Assets"), ("자산총계",)),
    "equity": (("ifrs-full_Equity", "ifrs_Equity"), ("자본총계",)),
    "debt": (("ifrs-full_Liabilities", "ifrs_Liabilities"), ("부채총계",)),
}
_REPRT_Q = {"11013": "Q1", "11012": "Q2", "11014": "Q3", "11011": "Q4"}
_PRICE_YEARS = range(2015, 2027)
_EVENT_YEARS_PREFIX = "2"


def dataDir(baseDir: Path | None = None) -> Path:
    """데이터 루트: 명시 baseDir > DARTLAB_DATA_DIR env > ./data."""
    if baseDir is not None:
        return baseDir
    root = os.environ.get("DARTLAB_DATA_DIR")
    return Path(root) if root else Path("data")


def weekCalendar(baseDir: Path | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    """gov/prices 거래일에서 주 달력. → (weekMap[date,week], weekEnd[week,date=그 주 마지막 거래일])."""
    base = dataDir(baseDir) / "gov/prices/date"
    frames = [
        pl.scan_parquet(base / f"{y}.parquet").select(pl.col("BAS_DD").alias("date"))
        for y in _PRICE_YEARS
        if (base / f"{y}.parquet").exists()
    ]
    cal = (
        pl.concat(frames)
        .collect()
        .unique()
        .sort("date")
        .with_columns(d=pl.col("date").str.to_date("%Y%m%d"))
        .with_columns(week=(pl.col("d").dt.iso_year() * 100 + pl.col("d").dt.week()).cast(pl.Int64))
    )
    weekMap = cal.select("date", "week")
    weekEnd = cal.group_by("week").agg(pl.col("date").max().alias("date"))
    return weekMap, weekEnd


def scanFinanceGrid(baseDir: Path | None = None) -> pl.DataFrame:
    """dart/finance 전종목 수치 재무 → (code, period, rceptDate, account, amount) long.

    단일 lazy glob 스캔(streaming) + 조기 계정 필터 (파일 루프 대비 ~460배, 실측 3.7초). 같은
    (code,period,account) 다중 공시는 최신 접수 우선. rceptDate = rcept_no 앞 8자 (PIT 접수일).
    """
    finDir = dataDir(baseDir) / "dart/finance"
    idMap = {aid: k for k, (ids, _) in _ACCOUNT_MAP.items() for aid in ids}
    nmPat = "|".join(nm for _, nms in _ACCOUNT_MAP.values() for nm in nms)
    cols = ["rcept_no", "reprt_code", "bsns_year", "sj_div", "account_id", "account_nm", "thstrm_amount", "fp"]
    df = (
        pl.scan_parquet(
            str(finDir / "*.parquet"), include_file_paths="fp", extra_columns="ignore", missing_columns="insert"
        )
        .select(cols)
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS", "BS"])
            & (pl.col("account_id").is_in(list(idMap)) | pl.col("account_nm").str.contains(nmPat))
        )
        .collect(engine="streaming")
    )
    acct = pl.col("account_id").replace_strict(idMap, default=None)
    for k, (_, nms) in _ACCOUNT_MAP.items():
        for nm in nms:
            acct = (
                pl.when(acct.is_null() & pl.col("account_nm").str.contains(nm, literal=True))
                .then(pl.lit(k))
                .otherwise(acct)
            )
    out = (
        df.with_columns(
            code=pl.col("fp").str.extract(r"(\d{6})\.parquet"),
            rceptDate=pl.col("rcept_no").str.slice(0, 8),
            quarter=pl.col("reprt_code").replace_strict(_REPRT_Q, default=None),
            amount=pl.col("thstrm_amount").str.replace_all(",", "").cast(pl.Float64, strict=False),
            account=acct,
        )
        .filter(pl.col("account").is_not_null() & pl.col("quarter").is_not_null())
        .with_columns(period=pl.col("bsns_year") + pl.col("quarter"))
        .select("code", "period", "rceptDate", "account", "amount")
    )
    return out.sort("rceptDate", descending=True).unique(subset=["code", "period", "account"], keep="first")


def fundWeekly(weekEnd: pl.DataFrame, mktcap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """재무 비율 표면 입력: 주말 시총에 PIT as-of 재무 → (code, week, ep, bm).

    계단 분자(공시 발효 재무) / 일별 분모(시총). look-ahead 차단 = as-of backward (rceptDate<=주말).
    """
    grid = scanFinanceGrid(baseDir)
    wide = grid.pivot(values="amount", index=["code", "rceptDate"], on="account", aggregate_function="first")
    fund = wide.select("code", "rceptDate", "netIncome", "equity").drop_nulls("rceptDate").sort(["code", "rceptDate"])
    snap = (
        weekEnd.join(mktcap, on="date", how="inner")
        .sort(["code", "date"])
        .join_asof(fund, left_on="date", right_on="rceptDate", by="code", strategy="backward")
        .drop_nulls("rceptDate")
    )
    return snap.with_columns(
        ep=pl.col("netIncome") / pl.col("mktcap"),
        bm=pl.col("equity") / pl.col("mktcap"),
    ).select("code", "week", "ep", "bm")


def eventWeekly(weekMap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """이벤트 표면 입력: allFilings 접수 → (code, week, reportType) v2 정규화."""
    base = dataDir(baseDir)
    paths = sorted(
        set(str(p) for p in (base / "dart/allFilings").glob(f"{_EVENT_YEARS_PREFIX}*.parquet"))
        | set(str(p) for p in (base / "dart/_afresume/dart/allFilings").glob(f"{_EVENT_YEARS_PREFIX}*.parquet"))
    )
    if not paths:
        return pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    ev = pl.concat([pl.read_parquet(p, columns=["stock_code", "rcept_dt", "report_nm"]) for p in paths])
    ev = ev.filter(pl.col("stock_code").str.len_chars() == 6).with_columns(reportType=normalizeEventType())
    return (
        ev.select(pl.col("rcept_dt").alias("date"), pl.col("stock_code").alias("code"), "reportType")
        .join(weekMap, on="date", how="left")
        .drop_nulls("week")
        .select("code", "week", "reportType")
    )


def priceWeekly(weekMap: pl.DataFrame, baseDir: Path | None = None) -> pl.DataFrame:
    """가격 표면 입력: 종목별 trailing 신호를 주말 스냅샷 → (code, week, ret5, mom20x5, volShock, high52).

    수정주가 근사(분할/병합 연속화) 후 신호 계산, 전부 종목 내 거래일 shift (look-ahead 0).
    """
    import math

    base = dataDir(baseDir) / "gov/prices/date"
    frames = [
        pl.scan_parquet(base / f"{y}.parquet").select(
            pl.col("BAS_DD").alias("date"),
            pl.col("ISU_CD").alias("code"),
            pl.col("TDD_CLSPRC").cast(pl.Float64).alias("close"),
            pl.col("LIST_SHRS").cast(pl.Float64).alias("shares"),
            pl.col("ACC_TRDVOL").cast(pl.Float64).alias("vol"),
            pl.col("TDD_HGPRC").cast(pl.Float64).alias("high"),
        )
        for y in _PRICE_YEARS
        if (base / f"{y}.parquet").exists()
    ]
    df = pl.concat(frames).collect().filter(pl.col("close") > 0).sort(["code", "date"])
    # 수정주가 근사: 상장주식수 점프 + 역방향 가격 점프 동시 = 분할/병합
    ratio = (pl.col("shares") / pl.col("shares").shift(1).over("code")).fill_null(1.0)
    closeRatio = (pl.col("close") / pl.col("close").shift(1).over("code")).fill_null(1.0)
    mech = ((ratio >= 1.2) | (ratio <= 1 / 1.2)) & ((closeRatio * ratio).log().abs() < math.log(1.7))
    f = pl.when(mech).then(ratio).otherwise(1.0).fill_null(1.0)
    df = df.with_columns(adj=f.cum_prod().over("code")).with_columns(close=pl.col("close") * pl.col("adj"))
    c = pl.col("close")
    df = df.with_columns(
        ret5=(c / c.shift(5).over("code") - 1),
        mom20x5=(c.shift(5).over("code") / c.shift(25).over("code") - 1),
        volShock=(pl.col("vol") / pl.col("vol").rolling_mean(20).over("code") - 1),
        high52=(c / c.rolling_max(250).over("code")),
        maxRet20=(c / c.shift(1).over("code") - 1).rolling_max(20).over("code"),  # MAX 복권성(회피)
    )
    return df.join(weekMap.rename({"date": "d0"}), left_on="date", right_on="d0", how="inner").select(
        "code", "week", "ret5", "mom20x5", "volShock", "high52", "maxRet20"
    )


def marketCap(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 시총 (재무 비율 분모·사이즈 버킷용) → (date, code, mktcap)."""
    base = dataDir(baseDir) / "gov/prices/date"
    frames = [
        pl.scan_parquet(base / f"{y}.parquet").select(
            pl.col("BAS_DD").alias("date"),
            pl.col("ISU_CD").alias("code"),
            pl.col("MKTCAP").cast(pl.Float64).alias("mktcap"),
        )
        for y in _PRICE_YEARS
        if (base / f"{y}.parquet").exists()
    ]
    return pl.concat(frames).collect().filter(pl.col("mktcap") > 0)


def dailyPrices(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 가격 (채점 라벨용) → (date, code, close, shares, mktcap)."""
    base = dataDir(baseDir) / "gov/prices/date"
    frames = [
        pl.scan_parquet(base / f"{y}.parquet").select(
            pl.col("BAS_DD").alias("date"),
            pl.col("ISU_CD").alias("code"),
            pl.col("TDD_CLSPRC").cast(pl.Float64).alias("close"),
            pl.col("LIST_SHRS").cast(pl.Float64).alias("shares"),
            pl.col("MKTCAP").cast(pl.Float64).alias("mktcap"),
        )
        for y in _PRICE_YEARS
        if (base / f"{y}.parquet").exists()
    ]
    return pl.concat(frames).collect().filter(pl.col("close") > 0)


def dailyHighLow(baseDir: Path | None = None) -> pl.DataFrame:
    """일별 고저종가 (비용 바닥 스프레드 추정용) → (date, code, high, low, close, mktcap).

    Corwin-Schultz·Abdi-Ranaldo 는 일 고저가에서 유효 스프레드를 추정한다 (06 §4). gov/prices
    date 샤드 직독 (별도 산출물 굽기 0). high/low <= 0 (거래정지·이상치) 행은 드롭.
    """
    base = dataDir(baseDir) / "gov/prices/date"
    frames = [
        pl.scan_parquet(base / f"{y}.parquet").select(
            pl.col("BAS_DD").alias("date"),
            pl.col("ISU_CD").alias("code"),
            pl.col("TDD_HGPRC").cast(pl.Float64).alias("high"),
            pl.col("TDD_LWPRC").cast(pl.Float64).alias("low"),
            pl.col("TDD_CLSPRC").cast(pl.Float64).alias("close"),
            pl.col("MKTCAP").cast(pl.Float64).alias("mktcap"),
        )
        for y in _PRICE_YEARS
        if (base / f"{y}.parquet").exists()
    ]
    return (
        pl.concat(frames)
        .collect()
        .filter((pl.col("high") > 0) & (pl.col("low") > 0) & (pl.col("close") > 0) & (pl.col("high") >= pl.col("low")))
    )


# 거시 팩터 (노출 벡터 축5 macroBeta 입력): 금리·환율·유가. ecos/fred SSOT parquet 직독.
_MACRO_FACTORS: tuple[tuple[str, str, str], ...] = (
    ("rate", "ecos", "BASE_RATE"),  # 한국 기준금리 (일별, %)
    ("fx", "ecos", "USDKRW"),  # 원/달러 (일별)
    ("oil", "fred", "DCOILWTICO"),  # WTI 유가 (일별, 글로벌)
)
# 지분/대주주 관계 공시 (제출인 flr_nm = 상대방 실명). 축2 counterparty 엣지 원천.
_RELATIONSHIP_REPORT_PAT = "대량보유|임원ㆍ주요주주|최대주주변경"


def macroDaily(baseDir: Path | None = None) -> pl.DataFrame:
    """거시 팩터 일별 → (date 'YYYYMMDD', rate, fx, oil). 노출 벡터(profile 축5) macroBeta 입력.

    ecos/fred observations SSOT parquet 직독 (床-layer, gather 수집물 소비 = 엔진 로직 재구현 0).
    Date -> 'YYYYMMDD' 정규화해 거래일(gov/prices)과 정렬 가능. 팩터별 결측은 소비처 forward-fill.
    """
    base = dataDir(baseDir) / "macro"
    out: pl.DataFrame | None = None
    for factor, src, sid in _MACRO_FACTORS:
        p = base / src / "observations.parquet"
        if not p.exists():
            continue
        o = (
            pl.scan_parquet(p)
            .filter(pl.col("seriesId") == sid)
            .select(pl.col("date").dt.strftime("%Y%m%d").alias("date"), pl.col("value").cast(pl.Float64).alias(factor))
            .collect()
        )
        out = o if out is None else out.join(o, on="date", how="full", coalesce=True)
    if out is None:
        return pl.DataFrame(schema={"date": pl.Utf8, "rate": pl.Float64, "fx": pl.Float64, "oil": pl.Float64})
    return out.sort("date")


def _macroChange(factor: str) -> pl.Expr:
    """팩터 일별 변화: 금리는 수준 차분(%p), 환율·유가는 수익률. 단변량 베타 회귀항."""
    if factor == "rate":
        return pl.col(factor) - pl.col(factor).shift(1)
    return pl.col(factor) / pl.col(factor).shift(1) - 1


def macroBetaByCode(asOf: str, *, factor: str = "oil", window: int = 250, baseDir: Path | None = None) -> pl.DataFrame:
    """전종목 거시 팩터 베타 → (code, beta). asOf 이전 window 거래일, 벌크 groupby (Company 루프 0).

    노출 형질(profile 축5)의 유니버스 버킷용 = 형질 조건부 성적표(11 §5) 입력. beta = cov(일수익,
    팩터변화)/var(팩터변화) (단변량 OLS). PIT: asOf 이전 거래일만. 표본<20·분산 0 종목은 드롭.
    """
    macro = macroDaily(baseDir)
    if macro.height == 0 or factor not in macro.columns:
        return pl.DataFrame(schema={"code": pl.Utf8, "beta": pl.Float64})
    px = (
        dailyPrices(baseDir)
        .filter((pl.col("close") > 0) & (pl.col("date") <= asOf))
        .sort(["code", "date"])
        .with_columns(ret=pl.col("close") / pl.col("close").shift(1).over("code") - 1)
    )
    dates = px.select("date").unique().sort("date")
    fac = (
        dates.join(macro.select("date", factor), on="date", how="left")
        .sort("date")
        .with_columns(pl.col(factor).forward_fill())
        .with_columns(dfac=_macroChange(factor))
        .select("date", "dfac")
    )
    j = (
        px.select("code", "date", "ret")
        .join(fac, on="date", how="inner")
        .drop_nulls(["ret", "dfac"])
        .sort(["code", "date"])
    )
    tail = j.group_by("code", maintain_order=True).tail(window)
    return (
        tail.group_by("code")
        .agg(
            n=pl.len(),
            cov=(pl.col("ret") * pl.col("dfac")).mean() - pl.col("ret").mean() * pl.col("dfac").mean(),
            var=(pl.col("dfac") ** 2).mean() - pl.col("dfac").mean() ** 2,
        )
        .filter((pl.col("n") >= 20) & (pl.col("var") > 0))
        .with_columns(beta=pl.col("cov") / pl.col("var"))
        .select("code", "beta")
    )


def counterpartyFilings(code: str, asOf: str, baseDir: Path | None = None) -> pl.DataFrame:
    """한 종목의 지분/대주주 관계 공시에서 제출인(flr_nm) = 상대방 실명 집계 (profile 축2).

    대량보유·임원소유·최대주주변경 공시의 flr_nm 이 보유자/거래자 상대방이다. asOf 이전만.
    → (counterparty, count) 내림차순. allFilings lazy 스캔 (stock_code 조기 필터, streaming).
    """
    base = dataDir(baseDir)
    paths = sorted(str(p) for p in (base / "dart/allFilings").glob("2*.parquet"))
    if not paths:
        return pl.DataFrame(schema={"counterparty": pl.Utf8, "count": pl.UInt32})
    df = (
        pl.scan_parquet(paths, extra_columns="ignore", missing_columns="insert")
        .filter(
            (pl.col("stock_code") == code)
            & (pl.col("rcept_dt").cast(pl.Utf8) <= asOf)
            & pl.col("report_nm").str.contains(_RELATIONSHIP_REPORT_PAT)
            & pl.col("flr_nm").is_not_null()
            & (pl.col("flr_nm").str.len_chars() > 0)
        )
        .select(pl.col("flr_nm").alias("counterparty"))
        .collect(engine="streaming")
    )
    if df.height == 0:
        return pl.DataFrame(schema={"counterparty": pl.Utf8, "count": pl.UInt32})
    # 동점 정렬은 counterparty 명 2차키로 안정화 (replay 항등성: 같은 asOf 재계산 = byte 일치).
    return df.group_by("counterparty").len(name="count").sort(["count", "counterparty"], descending=[True, False])
