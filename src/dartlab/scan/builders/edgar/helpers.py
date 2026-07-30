"""EDGAR scan 공용 헬퍼 — scanAccount 기반 전종목 재무 지표 계산.

DART scan은 프리빌드 parquet에서 읽지만, EDGAR scan은
providers/edgar/finance/scanAccount.py를 활용하여 전종목 XBRL 데이터를 읽는다.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

EDGAR_PREBUILD_READ_WORKERS = 12


def edgarListedFinanceSources(
    financeDir: Path,
    cikToTicker: Mapping[str, str],
) -> list[tuple[Path, str, str]]:
    """finance directory에서 listed CIK source만 결정적 순서로 고른다."""

    return [
        (path, path.stem.zfill(10), cikToTicker[path.stem.zfill(10)])
        for path in sorted(financeDir.glob("*.parquet"))
        if path.stem.zfill(10) in cikToTicker
    ]


def _writeParquetAtomic(frame: pl.DataFrame, outputPath: Path) -> None:
    """EDGAR prebuild frame을 footer 검증 후 같은 volume에서 원자 교체한다."""

    outputPath.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporaryName = tempfile.mkstemp(
        prefix=f".{outputPath.stem}-",
        suffix=".tmp.parquet",
        dir=outputPath.parent,
    )
    os.close(descriptor)
    temporary = Path(temporaryName)
    try:
        frame.write_parquet(temporary, compression="zstd")
        parquet = pq.ParquetFile(temporary, memory_map=False, pre_buffer=False)
        try:
            actualRows = parquet.metadata.num_rows
            actualSchema = parquet.schema_arrow
        finally:
            parquet.close()
        expectedSchema = frame.to_arrow().schema
        if actualRows != frame.height or not actualSchema.equals(expectedSchema):
            raise RuntimeError(
                "EDGAR prebuild 임시 artifact 검증 실패: "
                f"path={outputPath}, rows={actualRows}/{frame.height}, "
                f"schemaEqual={actualSchema.equals(expectedSchema)}"
            )
        with temporary.open("r+b") as written:
            os.fsync(written.fileno())
        os.replace(temporary, outputPath)
        if os.name != "nt":
            directoryDescriptor = os.open(outputPath.parent, os.O_RDONLY)
            try:
                os.fsync(directoryDescriptor)
            finally:
                os.close(directoryDescriptor)
    except BaseException as primaryError:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException as cleanupError:
            raise BaseExceptionGroup(
                "EDGAR prebuild write와 temporary cleanup이 함께 실패했습니다",
                [primaryError, cleanupError],
            ) from primaryError
        raise


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

        univ = loadEdgarListedUniverse(localOnly=True)
    required = {"cik", "ticker"}
    missing = sorted(required - set(univ.columns))
    if missing:
        raise ValueError(f"EDGAR listed universe identity columns 누락: {missing}")
    if "is_exchange_listed" in univ.columns:
        univ = univ.filter(pl.col("is_exchange_listed") == True)  # noqa: E712
    if "is_otc" in univ.columns:
        univ = univ.filter(pl.col("is_otc") != True)  # noqa: E712
    if univ.is_empty():
        raise ValueError("EDGAR listed universe identity가 비어 있습니다")

    out: dict[str, str] = {}
    cikByTicker: dict[str, str] = {}
    for c, t in zip(univ["cik"].to_list(), univ["ticker"].to_list()):
        cik = str(c or "").strip().zfill(10)
        ticker = str(t or "").strip().upper()
        if len(cik) != 10 or not cik.isascii() or not cik.isdigit():
            raise ValueError(f"EDGAR listed universe CIK가 유효하지 않습니다: {c!r}")
        if not ticker or ticker.isdigit():
            raise ValueError(f"EDGAR listed universe ticker가 유효하지 않습니다: {t!r}")
        owner = cikByTicker.setdefault(ticker, cik)
        if owner != cik:
            raise ValueError(f"EDGAR listed universe ticker가 여러 CIK에 연결됩니다: {ticker}={owner},{cik}")
        out.setdefault(cik, ticker)  # 첫(=대표 보통주) 티커 우선
    if not out:
        raise ValueError("EDGAR listed universe canonical identity가 비어 있습니다")
    return out


def scanEdgarAccounts(snakeIds: list[str], *, annual: bool = True) -> pl.DataFrame:
    """여러 EDGAR 계정을 한번에 스캔하여 wide DataFrame으로 반환.

    Parameters
    ----------
    snakeIds : list[str]
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
        EDGAR scanAccounts batch 또는 기간 정렬 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.helpers import scanEdgarAccounts
    >>> df = scanEdgarAccounts(["sales", "operating_profit"])
    >>> df.filter(pl.col("operating_profit") > 1e9).head()

    Capabilities:
        - 여러 snakeId 계정을 `scanAccounts` 1회 호출로 source scan하고 종목별 단면을
          wide 합산한다.
        - 회사마다 모든 계정에 동일한 최신·전기 기간을 적용한다. 최신 기간에 없는
          계정은 과거값으로 대체하지 않고 null로 남긴다.

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
        ``scanAccounts`` batch → 계정별 wide를 long 변환 → 회사별 기간 rank →
        최신·전기 두 기간만 account wide로 pivot.

    Requires:
        - 로컬 ``data/edgar/finance/{ticker}.parquet`` (EDGAR Data Sync)
        - ``dartlab.providers.edgar.finance.scanAccount.scanAccount``

    SeeAlso:
        - :func:`dartlab.providers.edgar.finance.scanAccount.scanAccount` — 단일 계정 source
        - :func:`scanEdgarRawTags` — XBRL 태그 직접 (snakeId 매핑 없이)
        - :func:`safeDiv` · :func:`pct` · :func:`gradeByValue` — 비율/등급 계산 헬퍼
    """
    from dartlab.providers.edgar.finance.scanAccount import scanAccounts

    frames = scanAccounts(snakeIds, freq="Y" if annual else "Q")
    return _alignAccountPeriods(snakeIds, frames)


def _alignAccountPeriods(
    snakeIds: list[str],
    frames: dict[str, pl.DataFrame],
) -> pl.DataFrame:
    """회사별 최신·전기 한 쌍에 여러 계정 값을 정확히 맞춘다."""

    longFrames: list[pl.DataFrame] = []
    nameFrames: list[pl.DataFrame] = []
    for snakeId in snakeIds:
        frame = frames.get(snakeId)
        if frame is None or frame.is_empty() or "stockCode" not in frame.columns:
            continue
        if "corpName" in frame.columns:
            nameFrames.append(frame.select("stockCode", "corpName"))
        periodCols = [column for column in frame.columns if column not in ("stockCode", "corpName")]
        if not periodCols:
            continue
        longFrames.append(
            frame.unpivot(
                index="stockCode",
                on=periodCols,
                variable_name="_period",
                value_name="_value",
            )
            .filter(pl.col("_value").is_not_null())
            .with_columns(pl.lit(snakeId).alias("_snakeId"))
        )

    if not longFrames:
        return pl.DataFrame({"stockCode": []})

    long = pl.concat(longFrames, how="vertical_relaxed")
    periods = (
        long.select("stockCode", "_period")
        .unique()
        .with_columns(pl.col("_period").rank("dense", descending=True).over("stockCode").alias("_periodRank"))
        .filter(pl.col("_periodRank") <= 2)
    )
    selected = (
        long.join(periods, on=["stockCode", "_period"], how="inner")
        .with_columns(
            pl.when(pl.col("_periodRank") == 1)
            .then(pl.col("_snakeId"))
            .otherwise(pl.col("_snakeId") + pl.lit("_prev"))
            .alias("_column")
        )
        .select("stockCode", "_column", "_value")
        .pivot(
            on="_column",
            index="stockCode",
            values="_value",
            aggregate_function="first",
        )
    )

    if nameFrames:
        names = (
            pl.concat(nameFrames, how="vertical_relaxed")
            .filter(pl.col("corpName").is_not_null())
            .group_by("stockCode")
            .agg(pl.col("corpName").first())
        )
        selected = selected.join(names, on="stockCode", how="left")
    else:
        selected = selected.with_columns(pl.lit(None, dtype=pl.Utf8).alias("corpName"))

    expected = [name for snakeId in snakeIds for name in (snakeId, f"{snakeId}_prev")]
    missing = [name for name in expected if name not in selected.columns]
    if missing:
        selected = selected.with_columns(pl.lit(None, dtype=pl.Float64).alias(name) for name in missing)
    return selected.select("stockCode", "corpName", *expected).sort("stockCode")


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
    result = pl.lit(default)
    for threshold, label in reversed(thresholds):
        result = pl.when(val >= threshold).then(pl.lit(label)).otherwise(result)
    return result
