"""EDGAR scan 공용 헬퍼 — scanAccount 기반 전종목 재무 지표 계산.

DART scan은 프리빌드 parquet에서 읽지만, EDGAR scan은
providers/edgar/finance/scanAccount.py를 활용하여 전종목 XBRL 데이터를 읽는다.
"""

from __future__ import annotations

import polars as pl


def edgarCikToTicker(univ: pl.DataFrame | None = None) -> dict[str, str]:
    """CIK(10자리 zero-pad) → 대표(보통주) 티커 매핑 — 다중 티커 CIK 는 첫 티커 채택.

    SEC ``company_tickers`` 는 CIK 당 보통주를 *맨 앞*에 둔다(예 JPMORGAN: JPM → JPM-PC → ... → VYLD).
    단순 dict 컴프리헨션은 *마지막* 티커(우선주·구조화상품)를 남겨 ~18% 다중티커 CIK 를 엉뚱한 코드로
    키잉했다(JPM→VYLD). 본 헬퍼는 ``setdefault`` 로 *첫* 티커를 채택해 보통주를 보장한다. finance·
    valuation·report 빌더가 공유해 stockCode 키 일관성(드리프트 0)을 강제한다.

    Parameters
    ----------
    univ : pl.DataFrame | None
        ``loadEdgarListedUniverse()`` 결과(cik·ticker 컬럼). None 이면 직접 로드.

    Returns
    -------
    dict[str, str]
        {cik(10자리): 대표 티커}. ticker 가 빈 행은 제외.

    Raises
    ------
    OSError
        ``univ=None`` 인데 universe 로드 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.helpers import edgarCikToTicker
    >>> m = edgarCikToTicker()  # doctest: +SKIP
    >>> m["0000019617"]  # doctest: +SKIP
    'JPM'
    """
    if univ is None:
        from dartlab.core.dataLoader import loadEdgarListedUniverse

        univ = loadEdgarListedUniverse()
    out: dict[str, str] = {}
    for c, t in zip(univ["cik"].to_list(), univ["ticker"].to_list()):
        if not t:
            continue
        out.setdefault(str(c).zfill(10), str(t))  # 첫(=대표 보통주) 티커 우선
    return out


def scanEdgarAccounts(snakeIds: list[str], *, annual: bool = True) -> pl.DataFrame:
    """여러 EDGAR 계정을 한번에 스캔하여 wide DataFrame으로 반환.

    Parameters
    ----------
    snake_ids : list[str]
        스캔할 계정 snakeId 목록 (예: ["sales", "operating_profit"]).
    annual : bool
        연간(10-K) 데이터 사용 여부.

    Returns
    -------
    pl.DataFrame
        stockCode : str — CIK 또는 종목코드
        corpName : str — 회사명
        {snakeId} : float — 해당 계정의 최신 기간 값
        {snakeId}_prev : float — 해당 계정의 전기 값 (YoY 계산용)

    Raises
    ------
    polars.PolarsError
        EDGAR scanAccount 가 반환한 DataFrame join 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.helpers import scanEdgarAccounts
    >>> df = scanEdgarAccounts(["sales", "operating_profit"])
    >>> df.filter(pl.col("operating_profit") > 1e9).head()

    Capabilities:
        - 여러 snakeId 계정을 차례로 `scanAccount` 호출 → 종목별 단면 dataFrame 들을 outer join
          으로 wide 합산. 각 계정마다 "데이터가 가장 많은 기간" 컬럼 자동 선택 + prev (전기) 추가.
        - corpName 충돌 시 coalesce 로 단일화.

    AIContext:
        EDGAR 11 scan axis (`_scanProfitability`/`_scanGrowth`/...) 모두가 본 함수로 종목별 wide
        DataFrame 을 받아 비율 계산. AI 가 `dartlab.scan("xxx", market="us")` 호출 시 본 함수가
        실질적 데이터 fetch entry.

    Guide:
        - 계정 누락 (XBRL tag 부재) 종목은 해당 컬럼 null → 후속 비율도 null. 호출자가 nulls_last
          처리 권장.
        - annual=True 가 기본 — 10-K 기반. quarterly 필요 시 False 호출자 책임.

    When:
        EDGAR scan axis 함수가 종목별 계정 단면을 wide 로 모을 때. 직접 호출은 prototype.

    How:
        ``snakeIds`` iterate → ``scanAccount`` 호출 → most-non-null period column 선택 → narrow
        select (stockCode/corpName + {sid} + {sid}_prev) → 첫 base 또는 outer join 누적.

    Requires:
        - 로컬 ``data/edgar/finance/{ticker}.parquet`` (EDGAR Data Sync)
        - ``dartlab.providers.edgar.finance.scanAccount.scanAccount``

    SeeAlso:
        - :func:`dartlab.providers.edgar.finance.scanAccount.scanAccount` — 단일 계정 source
        - :func:`scanEdgarRawTags` — XBRL 태그 직접 (snakeId 매핑 없이)
        - :func:`safeDiv` · :func:`pct` · :func:`gradeByValue` — 비율/등급 계산 헬퍼
    """
    from dartlab.providers.edgar.finance.scanAccount import scanAccount

    base: pl.DataFrame | None = None
    for sid in snakeIds:
        # scanAccount 계약은 freq("Q"/"Y") keyword — annual bool 이 아니다. annual→freq 변환.
        df = scanAccount(sid, freq="Y" if annual else "Q")
        if df.is_empty():
            continue
        # 가장 데이터가 많은 기간을 선택 (non-null 최다)
        period_cols = [c for c in df.columns if c not in ("stockCode", "corpName")]
        if len(period_cols) < 1:
            continue
        best_col = max(period_cols, key=lambda c: df[c].drop_nulls().len())
        prev_idx = period_cols.index(best_col) + 1
        prev_col = period_cols[prev_idx] if prev_idx < len(period_cols) else None
        select_cols = ["stockCode", "corpName", pl.col(best_col).alias(f"{sid}")]
        if prev_col:
            select_cols.append(pl.col(prev_col).alias(f"{sid}_prev"))
        narrow = df.select(select_cols)
        if base is None:
            base = narrow
        else:
            # full + coalesce=True: join 키(stockCode) 를 한 컬럼으로 병합 — 누락 시 stockCode_{sid}
            # 누출 + 키 불일치 행 stockCode null 방지. corpName 은 키가 아니라 별도 coalesce.
            base = base.join(narrow, on="stockCode", how="full", coalesce=True, suffix=f"_{sid}")
            if f"corpName_{sid}" in base.columns:
                base = base.with_columns(
                    pl.coalesce(pl.col("corpName"), pl.col(f"corpName_{sid}")).alias("corpName")
                ).drop(f"corpName_{sid}")
    return base if base is not None else pl.DataFrame({"stockCode": []})


def safeDiv(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    """안전한 나눗셈 — 분모 0이면 None.

    Parameters
    ----------
    num : pl.Expr
        분자 표현식.
    den : pl.Expr
        분모 표현식.

    Returns
    -------
    pl.Expr
        num / den. 분모가 0이면 None.

    Raises
    ------
    없음 — Polars when/then chain 으로 0 분모 처리.

    Examples
    --------
    >>> import polars as pl
    >>> from dartlab.scan.builders.edgar.helpers import safeDiv
    >>> df = pl.DataFrame({"a": [10, 5], "b": [2, 0]})
    >>> df.with_columns(ratio=safeDiv(pl.col("a"), pl.col("b")))

    Requires:
        - polars 만 (외부 의존 없음)
    """
    return pl.when(den != 0).then(num / den).otherwise(None)


def pct(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    """백분율 계산 — (num/den)*100, 소수점 2자리.

    Parameters
    ----------
    num : pl.Expr
        분자 표현식.
    den : pl.Expr
        분모 표현식.

    Returns
    -------
    pl.Expr
        비율 (%). 분모 0이면 None.

    Raises
    ------
    없음 — safeDiv 가 0 분모 None 처리.

    Examples
    --------
    >>> import polars as pl
    >>> from dartlab.scan.builders.edgar.helpers import pct
    >>> df = pl.DataFrame({"profit": [10, 5], "sales": [100, 50]})
    >>> df.with_columns(margin=pct(pl.col("profit"), pl.col("sales")))

    Requires:
        - polars · :func:`safeDiv`
    """
    return (safeDiv(num, den) * 100).round(2)


def scanEdgarRawTags(tags: list[str], *, annual: bool = True) -> pl.DataFrame:
    """XBRL 태그명으로 직접 전종목 스캔 (snakeId 매핑 없이).

    Parameters
    ----------
    tags : list[str]
        XBRL 태그명 목록 (예: ["AuditFees", "NonAuditServicesFees"]).
    annual : bool
        연간(10-K/20-F) 데이터만 필터.

    Returns
    -------
    pl.DataFrame
        stockCode : str — CIK
        corpName : str — 회사명
        {tag} : float — 각 태그의 최신 연도 값 (USD)

    Raises
    ------
    polars.exceptions.ComputeError · OSError
        개별 종목 parquet 손상 시 내부 흡수 (skip).

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.helpers import scanEdgarRawTags
    >>> df = scanEdgarRawTags(["AuditFees"])
    >>> df.filter(pl.col("AuditFees") > 1e6).head()

    Capabilities:
        - snakeId 정규화를 우회하고 XBRL 태그명 그대로 종목별 parquet 스캔. `scanAccount` 가
          매핑하지 않은 niche 태그 (AuditFees / NonAuditServicesFees 등) 추출용.

    AIContext:
        ``_scanAudit`` 같은 niche axis 가 호출. AI agent 가 "감사보수" / "특수 비용항목" 류
        질문 시 본 함수로 raw XBRL 태그를 직접 뽑아낸다.

    Guide:
        - 10-K / 20-F 만 — quarterly (10-Q) 데이터는 fy 단위 latest 불일치라 제외.
        - 종목별 ComputeError/OSError 는 silent skip (한 종목 깨져도 다른 종목 정상).

    When:
        snakeId 사전에 없는 XBRL 태그가 필요할 때. 정규 axis (profitability/growth/...) 는
        :func:`scanEdgarAccounts` 사용 권장.

    How:
        edgar finance 디렉토리 종목별 parquet glob → lazy filter (tag IN tags & form IN 10-K/20-F)
        → 최신 fy row 추출 → wide record 적재 → 종목 단위 dict list → DataFrame.

    Requires:
        - 로컬 ``data/edgar/finance/{ticker}.parquet`` (EDGAR Data Sync)
        - polars · ``_getDataRoot``

    SeeAlso:
        - :func:`scanEdgarAccounts` — snakeId 정규화 경로 (권장)
        - :func:`dartlab.scan.builders.edgar.scan._scanAudit` — 본 함수 호출자 예시
    """
    from dartlab.core.dataLoader import _getDataRoot

    edgarDir = _getDataRoot() / "edgar" / "finance"
    if not edgarDir.exists():
        return pl.DataFrame()

    records = []
    for fp in edgarDir.glob("*.parquet"):
        cik = fp.stem
        try:
            df = (
                pl.scan_parquet(fp)
                .filter(pl.col("tag").is_in(tags) & pl.col("form").is_in(["10-K", "20-F"]))
                .select("tag", "val", "fy", "entityName")
                .collect(engine="streaming")
            )

            if df.is_empty():
                continue

            # 최신 연도
            latestFy = df["fy"].max()
            latest = df.filter(pl.col("fy") == latestFy)

            record = {
                "stockCode": cik,
                "corpName": latest["entityName"][0] if latest.height > 0 else "",
            }
            for tag in tags:
                tagRows = latest.filter(pl.col("tag") == tag)
                record[tag] = tagRows["val"][0] if tagRows.height > 0 else None

            records.append(record)
        except (pl.exceptions.ComputeError, OSError):
            continue

    return pl.DataFrame(records) if records else pl.DataFrame()


def gradeByValue(val: pl.Expr, thresholds: list[tuple[float, str]], default: str = "해당없음") -> pl.Expr:
    """값 기반 등급 분류.

    Parameters
    ----------
    val : pl.Expr
        등급 판정 대상 Polars 표현식.
    thresholds : list[tuple[float, str]]
        (하한, 등급) 리스트 (내림차순). 예: [(20, "우수"), (10, "양호")].
    default : str
        어떤 threshold에도 해당 안 되면 반환할 등급.

    Returns
    -------
    pl.Expr
        등급 문자열 (예: "우수", "양호", ..., default).

    Raises
    ------
    없음 — Polars when/then chain, threshold list 비어도 default 만 반환.

    Examples
    --------
    >>> import polars as pl
    >>> from dartlab.scan.builders.edgar.helpers import gradeByValue
    >>> df = pl.DataFrame({"roe": [25.0, 15.0, 5.0]})
    >>> df.with_columns(grade=gradeByValue(pl.col("roe"), [(20, "우수"), (10, "양호")]))

    Capabilities:
        - 단일 metric 값 → 정렬된 threshold list 기반 등급 라벨 변환. when/then chain 자동
          조립으로 N 단계 임계 분기를 1 호출로 처리.
        - 임계 하나도 안 맞으면 ``default`` 라벨.

    AIContext:
        EDGAR scan 11 axis 가 등급 컬럼 생성 시 호출. ``[(20, "우수"), (10, "양호")]`` 같은 통일된
        등급 정책을 모듈 공유.

    Guide:
        - thresholds 는 반드시 내림차순 — 첫 매칭이 채택되므로 순서 잘못이면 등급 wrong.
        - threshold 같은 값이 여러 metric 에 공유될 때 본 함수로 통일 (정책 SSOT 효과).

    When:
        EDGAR _scan* 함수 grade 컬럼 계산 시. DART scan 도 같은 패턴이지만 별도 분기 모듈.

    How:
        thresholds iterate → 첫 entry 는 ``pl.when(val >= t).then(label)`` 시작 → 다음 entry 는
        ``.when().then()`` chain → ``.otherwise(default)`` 종료.

    Requires:
        - polars 만

    SeeAlso:
        - :func:`safeDiv` · :func:`pct` — 같은 모듈 helpers
        - EDGAR `_scan*` 함수들이 본 함수 사용 패턴 (스캔.py)
    """
    expr = val
    for i, (threshold, label) in enumerate(thresholds):
        if i == 0:
            expr = pl.when(val >= threshold).then(pl.lit(label))
        else:
            expr = expr.when(val >= threshold).then(pl.lit(label))
    return expr.otherwise(pl.lit(default))
