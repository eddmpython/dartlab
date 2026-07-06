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
    (code,period,account) 다중 행은 연결(CFS) 우선, 그 안에서 최신 접수 우선 (연결/별도 혼입 =
    삼성 매출 333조 CFS vs 238조 OFS 가 접수순으로 뒤섞이던 2026-07-06 실측 결함). rceptDate =
    rcept_no 앞 8자 (PIT 접수일).
    """
    finDir = dataDir(baseDir) / "dart/finance"
    idMap = {aid: k for k, (ids, _) in _ACCOUNT_MAP.items() for aid in ids}
    nmPat = "|".join(nm for _, nms in _ACCOUNT_MAP.values() for nm in nms)
    cols = [
        "rcept_no",
        "reprt_code",
        "bsns_year",
        "sj_div",
        "fs_div",
        "account_id",
        "account_nm",
        "thstrm_amount",
        "fp",
    ]
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
        .with_columns(
            period=pl.col("bsns_year") + pl.col("quarter"),
            fsRank=pl.when(pl.col("fs_div") == "CFS").then(0).otherwise(1),  # 연결 우선 (별도는 연결 부재 시만)
        )
        .select("code", "period", "rceptDate", "account", "amount", "fsRank")
    )
    return (
        out.sort(["fsRank", "rceptDate"], descending=[False, True])
        .unique(subset=["code", "period", "account"], keep="first")
        .drop("fsRank")
    )


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
    주말 스냅샷 = (code, week) 마지막 거래일 1행 (2026-07-06 실측 결함: 일별 raw 에서 거래일마다
    행이 나가 주간 판독이 5배 중복 봉인. 옛 로컬 파일이 우연히 주간형이라 잠복했었음).
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
    return (
        df.join(weekMap.rename({"date": "d0"}), left_on="date", right_on="d0", how="inner")
        .sort(["code", "date"])
        .group_by(["code", "week"], maintain_order=True)
        .last()
        .select("code", "week", "ret5", "mom20x5", "volShock", "high52", "maxRet20")
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


# 지분/대주주 관계 공시 (제출인 flr_nm = 상대방 실명). 축2 counterparty 엣지 원천.
_RELATIONSHIP_REPORT_PAT = "대량보유|임원ㆍ주요주주|최대주주변경"


def macroDaily(baseDir: Path | None = None) -> pl.DataFrame:
    """거시 팩터 일별 → (date 'YYYYMMDD', <factor>...). 노출 벡터(profile 축5) macroBeta 입력.

    **팩터 축 = factors.macroFactors() 레지스트리 전수** (하드코딩 0): 팩터 등록 1행이면 이 패널·
    베타·격자·시나리오가 자동흡수. ecos/fred observations SSOT parquet 직독 (床-layer, 엔진 로직
    재구현 0). Date -> 'YYYYMMDD' 정규화. 소스/시리즈 부재 팩터는 열 자체 생략 (0 대체 금지).
    """
    from dartlab.simulate import factors as _factors

    base = dataDir(baseDir) / "macro"
    out: pl.DataFrame | None = None
    for mf in _factors.macroFactors():
        p = base / mf.source / "observations.parquet"
        if not p.exists():
            continue
        o = (
            pl.scan_parquet(p)
            .filter(pl.col("seriesId") == mf.seriesId)
            .select(
                pl.col("date").dt.strftime("%Y%m%d").alias("date"), pl.col("value").cast(pl.Float64).alias(mf.factor)
            )
            .collect()
        )
        if o.height == 0:
            continue
        out = o if out is None else out.join(o, on="date", how="full", coalesce=True)
    if out is None:
        return pl.DataFrame(schema={"date": pl.Utf8})
    return out.sort("date")


def _macroChange(factor: str) -> pl.Expr:
    """팩터 일별 변화 (factors.macroChange 위임, 기존 소비처 호환 얇은 별칭)."""
    from dartlab.simulate import factors as _factors

    return _factors.macroChange(factor)


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


def macroBetaByCodeWide(asOf: str, *, window: int = 250, baseDir: Path | None = None) -> pl.DataFrame:
    """전종목 전팩터 베타 → (code, <factor>Beta...). 가격 스캔 1회, 팩터 축 = 레지스트리 전수.

    시나리오 시뮬레이터 노출 입력 (회사 반응 = Σ 베타 x 충격). **팩터 목록은 factors.macroFactors()
    순회** = 팩터 등록 1행이면 베타 열이 자동 추가 (하류 격자·시나리오·프로파일 무수정 흡수).
    asOf 이전 window 거래일, 벌크 groupby (Company 루프 0). 팩터별 단변량 OLS. 무변동(var 0)·
    표본<20·데이터 부재 팩터는 None (0 대체 금지).
    """
    from dartlab.simulate import factors as _factors

    allFactors = _factors.factorNames()
    macro = macroDaily(baseDir)
    schema = {"code": pl.Utf8, **{_factors.betaCol(f): pl.Float64 for f in allFactors}}
    if macro.height == 0:
        return pl.DataFrame(schema=schema)
    factors = [f for f in allFactors if f in macro.columns]
    px = (
        dailyPrices(baseDir)
        .filter((pl.col("close") > 0) & (pl.col("date") <= asOf))
        .sort(["code", "date"])
        .with_columns(ret=pl.col("close") / pl.col("close").shift(1).over("code") - 1)
    )
    dates = px.select("date").unique().sort("date")
    fac = (
        dates.join(macro, on="date", how="left").sort("date").with_columns([pl.col(f).forward_fill() for f in factors])
    )
    fac = fac.with_columns([_macroChange(f).alias(f"d_{f}") for f in factors]).select(
        "date", *[f"d_{f}" for f in factors]
    )
    j = px.select("code", "date", "ret").join(fac, on="date", how="inner").sort(["code", "date"])
    tail = j.group_by("code", maintain_order=True).tail(window)
    aggs = [pl.len().alias("n")]
    for f in factors:
        aggs.append(
            ((pl.col("ret") * pl.col(f"d_{f}")).mean() - pl.col("ret").mean() * pl.col(f"d_{f}").mean()).alias(
                f"cov_{f}"
            )
        )
        aggs.append(((pl.col(f"d_{f}") ** 2).mean() - pl.col(f"d_{f}").mean() ** 2).alias(f"var_{f}"))
    g = tail.group_by("code").agg(aggs).filter(pl.col("n") >= 20)
    betaCols = [
        pl.when(pl.col(f"var_{f}") > 0).then(pl.col(f"cov_{f}") / pl.col(f"var_{f}")).otherwise(None).alias(f"{f}Beta")
        for f in factors
    ]
    out = g.with_columns(betaCols).select("code", *[f"{f}Beta" for f in factors])
    for f in allFactors:  # 데이터 부재 팩터 열 보강 (스키마 안정, null = 정직 결측)
        if _factors.betaCol(f) not in out.columns:
            out = out.with_columns(pl.lit(None, dtype=pl.Float64).alias(_factors.betaCol(f)))
    return out.select("code", *[_factors.betaCol(f) for f in allFactors])


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


def counterpartyCountsBulk(asOf: str, baseDir: Path | None = None) -> pl.DataFrame:
    """전종목 상대방(flr_nm) distinct 수 → (code, counterpartyCount). counterpartyFilings 벌크 대칭.

    profileAll(전종목 프로파일 한 방)의 축2 입력. allFilings 1 스캔 (per-company 루프 0). asOf 이전만.
    """
    base = dataDir(baseDir)
    paths = sorted(str(p) for p in (base / "dart/allFilings").glob("2*.parquet"))
    if not paths:
        return pl.DataFrame(schema={"code": pl.Utf8, "counterpartyCount": pl.UInt32})
    return (
        pl.scan_parquet(paths, extra_columns="ignore", missing_columns="insert")
        .filter(
            (pl.col("rcept_dt").cast(pl.Utf8) <= asOf)
            & (pl.col("stock_code").str.len_chars() == 6)
            & pl.col("report_nm").str.contains(_RELATIONSHIP_REPORT_PAT)
            & pl.col("flr_nm").is_not_null()
        )
        .group_by("stock_code")
        .agg(counterpartyCount=pl.col("flr_nm").n_unique())
        .rename({"stock_code": "code"})
        .collect(engine="streaming")
    )


def industryMap(baseDir: Path | None = None) -> pl.DataFrame:
    """종목 → 업종 맵 → (code, industry). kindList corpList(KRX 업종 분류 159종) 직독. 산업층(cascade) 원천.

    시나리오 시뮬레이터 산업 노드의 그룹 정의. 종목코드(6자리)로 가격 유니버스와 조인. 결측/중복 드롭.
    """
    p = dataDir(baseDir) / "kindList/corpList.parquet"
    if not p.exists():
        return pl.DataFrame(schema={"code": pl.Utf8, "industry": pl.Utf8})
    df = pl.read_parquet(p, columns=["종목코드", "업종"])
    return df.rename({"종목코드": "code", "업종": "industry"}).drop_nulls().unique("code", keep="first")


def liquidUniverse(asOf: str, *, mktcapQuantile: float = 0.3, baseDir: Path | None = None) -> set[str]:
    """유동 유니버스: asOf 최근일 시총 분위 컷 통과 종목 집합 (정밀도 부채: 극단베타 잡주 쏠림 완화).

    Args:
        asOf: 기준일 'YYYYMMDD'. mktcapQuantile: 하위 컷 분위 (기본 0.3 = 하위 30% 제외).
        baseDir: 데이터 SSOT 루트 override.

    Returns:
        시총 >= 분위 컷 종목코드 집합. 시나리오 결정(latticeDecision·monteCarloDecision) 입력
        baseScores 를 이 집합으로 필터하면 top 픽의 잡주 쏠림이 완화된다 (실측: top15 시총중앙
        691억 -> 2,233억). 데이터 부재 시 빈 집합 (필터 미적용은 소비처 판단).
    """
    caps = marketCap(baseDir).filter(pl.col("date") <= asOf)
    if caps.height == 0:
        return set()
    day = caps.filter(pl.col("date") == caps["date"].max())
    cut = day["mktcap"].quantile(mktcapQuantile)
    return set(day.filter(pl.col("mktcap") >= cut)["code"].to_list())


def industryMomentum(asOf: str, *, baseDir: Path | None = None, window: int = 20) -> pl.DataFrame:
    """업종별 피어 모멘텀 → (industry, momentum, breadth, nCodes). 산업 시나리오 판독 baseline (벌크).

    각 업종 소속 종목의 asOf 이전 window 거래일 등가중 수익 + 상승 비율(breadth). Company 루프 0
    (industryMap 조인 후 groupby). 산업층 cascade 노드의 현재 상태 = 그 업종이 최근 뜨거운가/식었나.
    """
    imap = industryMap(baseDir)
    empty = {"industry": pl.Utf8, "momentum": pl.Float64, "breadth": pl.Float64, "nCodes": pl.UInt32}
    if imap.height == 0:
        return pl.DataFrame(schema=empty)
    px = dailyPrices(baseDir).filter((pl.col("close") > 0) & (pl.col("date") <= asOf)).sort(["code", "date"])
    tail = px.group_by("code", maintain_order=True).tail(window)
    perCode = (
        tail.group_by("code")
        # 정정주가 미반영 급변(분할/병합)을 ±50%로 캡 (raw 종가라 corp-action 오염 방어).
        .agg(ret=(pl.col("close").last() / pl.col("close").first() - 1).clip(-0.5, 0.5), n=pl.len())
        .filter(pl.col("n") >= window // 2)
    )
    j = perCode.join(imap, on="code", how="inner")
    return (
        # 중앙값 = 소수 종목 업종의 극단 방어. breadth(상승 비율)·nCodes 동반(소비처가 얇은 업종 필터).
        j.group_by("industry")
        .agg(momentum=pl.col("ret").median(), breadth=(pl.col("ret") > 0).mean(), nCodes=pl.len())
        .sort("momentum", descending=True)
    )
