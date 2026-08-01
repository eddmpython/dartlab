"""재무 데이터 join — finance.parquet → nodes에 매출/이익/자산 붙이기.

account_id_std(정규화 snakeId)를 사용하여 전종목 재무 데이터를 추출한다.
CFS(연결) 우선, OFS(개별) fallback.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from dartlab.industry.types import IndustryNode

logger = logging.getLogger(__name__)

# 추출할 계정
_ACCOUNTS = {
    "sales": "revenue",
    "operating_profit": "opIncome",
    "net_profit": "netIncome",
    "total_assets": "totalAssets",
}

# 단위 오류 sanity guard — 한 종목 매출이 500조 KRW (5e14) 초과하면 단위 mix 의심
# (삼성전자 연결 매출 ~300조 미만이라 정상값은 절대 hit 안 함). DART 원본 또는 빌드
# 단계에서 단위 혼동 (원/백만원 mix) 으로 7.34e16 같은 값이 들어오면 산업 집계 왜곡.
_REVENUE_SANITY_LIMIT = 5.0e14
_OPINCOME_SANITY_LIMIT = 1.0e14
_ASSET_SANITY_LIMIT = 5.0e15


def _finPath() -> Path:
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / DATA_RELEASES["scan"]["dir"] / "finance.parquet"


def _extractYearly(year: str) -> pl.DataFrame:
    """특정 연도의 전종목 재무 데이터를 추출.

    Returns
    -------
    pl.DataFrame
        columns: stockCode, revenue, opIncome, netIncome, totalAssets
    """
    path = _finPath()
    if not path.exists():
        return pl.DataFrame()

    snakeIds = list(_ACCOUNTS.keys())

    df = (
        pl.scan_parquet(str(path))
        .filter(pl.col("account_id_std").is_in(snakeIds))
        .filter(pl.col("bsns_year") == year)
        .filter(pl.col("reprt_nm") == "4분기")  # 연간 누적만
        .filter(pl.col("sj_div").is_in(["IS", "CIS", "BS"]))
        .select(["stockCode", "fs_div", "account_id_std", "thstrm_amount"])
        .collect(engine="streaming")
    )

    if df.height == 0:
        return pl.DataFrame()

    # 금액 변환
    df = df.with_columns(
        pl.col("thstrm_amount").str.replace_all(",", "").cast(pl.Float64, strict=False).alias("amount")
    )

    # 계정별로 CFS 우선, OFS fallback
    allCodes = df["stockCode"].unique().sort()
    result = pl.DataFrame({"stockCode": allCodes})

    for snakeId, alias in _ACCOUNTS.items():
        subset = df.filter(pl.col("account_id_std") == snakeId)
        cfs = subset.filter(pl.col("fs_div") == "CFS").group_by("stockCode").agg(pl.col("amount").first().alias(alias))
        ofsCodes = cfs.select("stockCode")
        ofs = (
            subset.filter(pl.col("fs_div") == "OFS")
            .join(ofsCodes, on="stockCode", how="anti")
            .group_by("stockCode")
            .agg(pl.col("amount").first().alias(alias))
        )
        acct = pl.concat([cfs, ofs])
        result = result.join(acct, on="stockCode", how="left")

    return _applySanityGuard(result, year=year)


def _availableAnnualYears(*, limit: int | None = None) -> list[str]:
    """finance.parquet에서 실제 관측된 연간 사업연도를 최신순으로 반환한다."""
    path = _finPath()
    if not path.exists():
        return []
    query = (
        pl.scan_parquet(str(path))
        .filter(pl.col("reprt_nm") == "4분기")
        .filter(pl.col("account_id_std").is_in(list(_ACCOUNTS)))
        .select(pl.col("bsns_year").cast(pl.Utf8).alias("year"))
        .drop_nulls()
        .unique()
        .sort("year", descending=True)
    )
    if limit is not None:
        query = query.limit(limit)
    observed = query.collect(engine="streaming")
    return observed.get_column("year").to_list() if observed.height else []


def _latestAvailableAnnualYear() -> str | None:
    """finance.parquet에서 실제 관측된 가장 최근 연간 사업연도를 반환한다."""
    years = _availableAnnualYears(limit=1)
    return years[0] if years else None


def _applySanityGuard(result: pl.DataFrame, *, year: str) -> pl.DataFrame:
    """단위 오류 outlier 제거 + 경고 로깅.

    한 종목 매출 > 500조 / 영업이익 > 100조 / 총자산 > 5,000조 면 단위 mix 의심
    (예: 032680 소프트센 2022 sales = 7.34e16 = 73,373조 — 한국 GDP 30 배).
    해당 종목의 해당 계정 값을 None 으로 대체해 산업 집계 왜곡 차단.
    """
    if result.height == 0:
        return result

    checks = (
        ("revenue", _REVENUE_SANITY_LIMIT),
        ("opIncome", _OPINCOME_SANITY_LIMIT),
        ("totalAssets", _ASSET_SANITY_LIMIT),
    )
    for col, limit in checks:
        if col not in result.columns:
            continue
        # null dtype (모든 값 None) 컬럼은 skip — abs 연산 불가
        if not result.schema[col].is_numeric():
            continue
        outliers = result.filter(pl.col(col).abs() > limit)
        if outliers.height == 0:
            continue
        for row in outliers.iter_rows(named=True):
            logger.warning(
                "%s %s outlier (단위 오류 의심): %s = %.2e (> %.2e), 산업 집계에서 제외",
                year,
                col,
                row["stockCode"],
                row[col],
                limit,
            )
        result = result.with_columns(pl.when(pl.col(col).abs() > limit).then(None).otherwise(pl.col(col)).alias(col))

    return result


def attachFinancials(
    nodes: list[IndustryNode],
    *,
    years: list[str] | None = None,
) -> list[IndustryNode]:
    """nodes에 재무 데이터를 붙인다.

    Capabilities:
        IndustryNode 리스트에 ``revenue`` 필드를 in-place 로 채워 반환. 최신 연도부터 fallback —
        연결재무제표 매출액이 있는 가장 최근 연도가 채워짐. 누락 데이터는 None 유지.

    최신 연도부터 시도하여 데이터가 있는 연도를 사용한다.

    Parameters
    ----------
    nodes : list[IndustryNode]
        기존 노드 리스트.
    years : list[str] | None
        시도할 연도 목록 (내림차순). None이면 실제 관측 최신 3개 연도.

    Returns
    -------
    list[IndustryNode]
        revenue 필드가 채워진 노드 리스트.

    Raises:
        없음 — finance.parquet 없거나 빈 결과면 nodes 그대로 반환.

    Example:
        >>> from dartlab.industry.build.financials import attachFinancials
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> nodes = attachFinancials(loadNodes())
        >>> nodes[0].revenue
        300870000000000

    Guide:
        ``Industry().build()`` 의 stage 후처리 단계에서 호출. ``buildIndustrySummary`` 가
        revenue 값을 산업/공정 집계에 사용.

    When:
        manifest 빌드 (`buildIndustryMap`) 의 재무 attach 단계. 일반 분석 흐름에서는 직접 호출
        않음.

    How:
        ``_extractYearly`` 로 최신 연도부터 finance.parquet 추출 → 종목 → revenue dict → nodes
        in-place 갱신.

    Requires:
        - L1.5 scan: finance.parquet
        - L1 raw: DART 연간 보고서 1 개 이상

    See Also:
        - ``dartlab.industry.build.financials.buildIndustrySummary`` : revenue 소비처
        - ``dartlab.industry.build.financials.buildTimelineSummary`` : 연도별 집계

    AIContext:
        AI 가 직접 호출하지 않는다 (배치). ``Industry().build()`` 후 결과 nodes 의 revenue 필드만
        cite.
    """
    if years is None:
        years = _availableAnnualYears(limit=3)

    # 최신 연도부터 merge

    allFin: dict[str, dict] = {}
    for year in years:
        fin = _extractYearly(year)
        if fin.height == 0:
            continue
        for row in fin.iter_rows(named=True):
            code = row["stockCode"]
            if code not in allFin:  # 최신 연도 우선
                allFin[code] = {**row, "revenuePeriod": year}

    if not allFin:
        return nodes

    finMap = allFin

    for node in nodes:
        data = finMap.get(node.stockCode)
        if data:
            node.revenue = data.get("revenue")
            node.revenuePeriod = data.get("revenuePeriod")

    joinedPeriods = sorted({str(row.get("revenuePeriod")) for row in finMap.values()}, reverse=True)
    logger.info("재무 데이터 %d사 join (periods=%s)", len(finMap), ",".join(joinedPeriods))
    return nodes


def buildIndustrySummary(
    nodes: list[IndustryNode],
    industryId: str,
    *,
    year: str | None = None,
) -> pl.DataFrame:
    """산업별/공정별 재무 집계.

    Capabilities:
        nodes 리스트에서 ``industryId`` 매칭 회사들의 단일 연도 재무를 추출해 stage (공정) 별로
        매출(조)/영업이익(조)/기업수 집계 DataFrame 반환. 산업 카드 헤더 요약의 데이터 소스.

    Parameters
    ----------
    nodes : list[IndustryNode]
        IndustryNode 리스트 (stage 필드 채워진 상태).
    industryId : str
        대상 산업 ID.
    year : str | None
        집계 연도 (예: "2024"). None이면 finance.parquet의 최근 연간 사업연도.

    Returns
    -------
    pl.DataFrame
        columns: stage, 공정명, 매출(조), 영업이익(조), 기업수, 영업이익률(%), coverageRatio

        - ``영업이익률(%)``: stage 단위 **revenue-weighted** 마진 = Σ영업이익 / Σ매출 × 100
          (revenue·opIncome 둘 다 present 인 회사만 집계, 단순평균 아님 — 소형사 극단 마진
          왜곡 차단). 매출 합 0 이면 null.
        - ``coverageRatio``: opIncome 산출가능 회사 / stage 내 finance-join 회사수 (0~1).
          profit-pool 격자의 결손 노출용 — 0 채움 금지. ★dual-source SSOT: 본 엔진 파생이
          **캐논**, 브라우저 ``industries/{id}.json`` per-node 롤업은 표시용 (커버리지·분모
          상이, ``mainPlan/industry-analysis-lab/07-implementation-plan.md`` §구멍1).

    Raises:
        없음 — finance 데이터 없거나 매칭 0 면 빈 DataFrame.

    Example:
        >>> from dartlab.industry.build.financials import buildIndustrySummary
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> df = buildIndustrySummary(loadNodes(), "semiconductor", year="2024")
        >>> df.select(["공정명", "매출(조)"]).head(3)

    Guide:
        매출/영업이익 단위는 조원. ``buildTimelineSummary`` 가 본 함수를 연도별 호출해 시계열로
        결합.

    When:
        산업 카드의 stage 단위 매출/영업이익 비교가 필요할 때. UI 카드 헤더 / Story 6 막
        narrative 데이터.

    How:
        ``_extractYearly(year)`` → finance × nodes inner join → industryId 필터 → stage 그룹
        집계 → taxonomy stage 한글명 매핑.

    Requires:
        - L1.5 scan: finance.parquet
        - reference: ``industry/taxonomy.getIndustry`` 정적 정의

    See Also:
        - ``dartlab.industry.build.financials.buildTimelineSummary`` : 연도별 시계열
        - ``dartlab.industry.build.financials.attachFinancials`` : nodes revenue 채우기

    AIContext:
        "이 산업의 공정별 시장 규모" 류 답변 데이터. 매출(조) 단독보다 영업이익률 (영업이익/매출)
        파생 인용 권장.
    """
    resolvedYear = year or _latestAvailableAnnualYear()
    if resolvedYear is None:
        return pl.DataFrame()
    fin = _extractYearly(resolvedYear)
    if fin.height == 0:
        return pl.DataFrame()

    # nodes → DataFrame
    nodesDf = pl.DataFrame(
        {
            "stockCode": [n.stockCode for n in nodes],
            "industry": [n.industry for n in nodes],
            "stage": [n.stage for n in nodes],
        }
    )

    joined = fin.join(nodesDf, on="stockCode", how="inner")
    filtered = joined.filter((pl.col("industry") == industryId) & (pl.col("stage") != ""))

    if filtered.height == 0:
        return pl.DataFrame()

    # stage label 매핑
    from dartlab.industry.taxonomy import getIndustry

    ind = getIndustry(industryId)
    stageLabels = {s.key: s.name for s in ind.stages} if ind else {}

    # revenue·opIncome 둘 다 present 인 행만 revenue-weighted 마진 모집단 (단순평균 왜곡 차단)
    _bothPresent = pl.col("revenue").is_not_null() & pl.col("opIncome").is_not_null()

    result = (
        filtered.group_by("stage")
        .agg(
            [
                pl.col("revenue").sum().alias("_revSum"),
                pl.col("opIncome").sum().alias("_opSum"),
                pl.len().alias("기업수"),
                pl.col("revenue").filter(_bothPresent).sum().alias("_revBoth"),
                pl.col("opIncome").filter(_bothPresent).sum().alias("_opBoth"),
                _bothPresent.sum().alias("_nBoth"),
            ]
        )
        .with_columns(
            [
                (pl.col("_revSum") / 1e12).round(1).alias("매출(조)"),
                (pl.col("_opSum") / 1e12).round(1).alias("영업이익(조)"),
                # revenue-weighted: Σ영업이익 / Σ매출 × 100 (둘 다 present 인 회사만), Σ매출 0 이면 null
                pl.when(pl.col("_revBoth") != 0)
                .then((pl.col("_opBoth") / pl.col("_revBoth") * 100).round(1))
                .otherwise(None)
                .alias("영업이익률(%)"),
                # opIncome 산출가능 회사 / stage finance-join 회사수 (결손 노출, 0 채움 금지)
                (pl.col("_nBoth") / pl.col("기업수")).round(3).alias("coverageRatio"),
            ]
        )
        .sort("매출(조)", descending=True)
    )

    # 공정명 추가
    result = result.with_columns(
        pl.col("stage").replace_strict(stageLabels, default=None, return_dtype=pl.Utf8).alias("공정명")
    )

    return result.select(["stage", "공정명", "매출(조)", "영업이익(조)", "기업수", "영업이익률(%)", "coverageRatio"])


def buildTimelineSummary(
    nodes: list[IndustryNode],
    industryId: str,
    *,
    years: list[str] | None = None,
) -> pl.DataFrame:
    """연도별 공정 매출 추이.

    Capabilities:
        ``buildIndustrySummary`` 를 ``years`` 각 연도에 호출해 결과를 연도 컬럼 첨부 + concat
        해 시계열 long-format DataFrame 반환. 산업의 공정 단위 시계열 비교용.

    Parameters
    ----------
    nodes : list[IndustryNode]
        nodes 리스트.
    industryId : str
        대상 산업 ID.
    years : list[str] | None
        대상 연도 리스트. None 이면 실제 관측 최신 5개 연도.

    Returns
    -------
    pl.DataFrame
        columns: 연도, 공정, 공정명, 매출(조), 영업이익(조), 기업수

    Raises:
        없음 — 모든 연도 빈 결과면 빈 DataFrame.

    Example:
        >>> from dartlab.industry.build.financials import buildTimelineSummary
        >>> from dartlab.industry.build.pipeline import loadNodes
        >>> df = buildTimelineSummary(loadNodes(), "semiconductor")
        >>> df.filter(pl.col("stage") == "memory").select(["연도", "매출(조)"])

    Guide:
        반환 frame 은 long-format (stage × year). UI 시계열 차트 / Story 6 막 "변화" 부분 데이터.

    When:
        산업 stage 단위 시계열 비교가 필요할 때 (단일 연도는 ``buildIndustrySummary``).

    How:
        years 루프 → ``buildIndustrySummary`` 호출 → 연도 컬럼 첨부 → concat → 정렬.

    Requires:
        - L1.5 scan: finance.parquet (years 각각)

    See Also:
        - ``dartlab.industry.build.financials.buildIndustrySummary`` : 단일 연도 집계
        - ``dartlab.industry.build.financials.attachFinancials`` : revenue 첨부

    AIContext:
        "메모리 공정 시장 규모 추이" 류 답변 데이터. 연도 간 차이 (delta) 단독보다 절대값 매출(조)
        과 동반 인용 권장.
    """
    if years is None:
        years = list(reversed(_availableAnnualYears(limit=5)))

    frames: list[pl.DataFrame] = []
    for year in years:
        df = buildIndustrySummary(nodes, industryId, year=year)
        if df.height > 0:
            df = df.with_columns(pl.lit(year).alias("연도"))
            frames.append(df)

    if not frames:
        return pl.DataFrame()

    return (
        pl.concat(frames)
        .select(["연도", "stage", "공정명", "매출(조)", "영업이익(조)", "기업수"])
        .sort(["stage", "연도"])
    )
