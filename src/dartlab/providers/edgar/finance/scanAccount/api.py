"""전종목 EDGAR 단일 계정/비율 시계열 공개 호출.

EDGAR finance parquet({cik}.parquet)를 병렬 스캔하여 특정 snakeId 하나의
전종목 x 기간 시계열 DataFrame 을 반환한다.

연간: FY 직접값 (IS/CF=연간합계, BS=시점잔액)
분기: FY + Q1-Q3 standalone (기존 pivot 로직 재활용)
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from dartlab.providers.edgar.finance.mapper import EdgarMapper
from dartlab.providers.edgar.finance.scanAccount.pipeline import (
    _listedParquetFiles,
    _scanAccountDuckDb,
    _scanAccountFileLoop,
    _scanAccountsDuckDb,
)
from dartlab.providers.edgar.finance.scanAccount.sql import _DUCKDB_BATCH_ACCOUNT_LIMIT
from dartlab.providers.edgar.finance.scanAccount.taxonomy import (
    _buildEdgarTagKeys,
    _joinCorpName,
    _loadTickerUniverse,
)
from dartlab.providers.edgar.finance.scanAccount.types import (
    EdgarScanError,
    EdgarScanExecutionError,
    EdgarScanMappingError,
    _TaxonomyTagKeys,
)

_log = logging.getLogger(__name__)


def scanAccounts(
    dartSnakeIds: list[str],
    *,
    freq: str = "Q",
) -> dict[str, pl.DataFrame]:
    """전종목 EDGAR 여러 계정을 bounded source batch로 반환한다.

    Args:
        dartSnakeIds: 서로 함께 비교할 DART canonical snakeId 목록.
        freq: ``"Q"`` 분기 또는 ``"Y"`` 연간.

    Returns:
        입력 snakeId를 key로 하고 각 계정 wide DataFrame을 값으로 갖는 dict.
        메모리 피크를 제한하기 위해 최대 3계정씩 같은 source scan을 공유한다.

    Raises:
        ValueError: 계정 목록이나 freq가 잘못된 경우.
        EdgarScanError: ticker, parquet 또는 batch 실행 실패.

    Example:
        >>> frames = scanAccounts(["sales", "operating_profit"], freq="Y")
        >>> sorted(frames)
        ['operating_profit', 'sales']
    """

    if not isinstance(dartSnakeIds, list) or not dartSnakeIds:
        raise ValueError("dartSnakeIds는 비어 있지 않은 문자열 list여야 합니다")
    if any(not isinstance(snakeId, str) or not snakeId.strip() for snakeId in dartSnakeIds):
        raise ValueError("dartSnakeIds는 비어 있지 않은 문자열만 포함해야 합니다")
    snakeIds = list(dict.fromkeys(snakeId.strip() for snakeId in dartSnakeIds))
    freq = str(freq).upper()
    if freq not in {"Q", "Y"}:
        raise ValueError(f"freq는 'Q' 또는 'Y'여야 합니다: {freq!r}")

    from dartlab.core.dataLoader import _dataDir

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))
    empty = {snakeId: pl.DataFrame({"stockCode": []}) for snakeId in snakeIds}
    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return empty

    tagKeysBySnakeId: dict[str, _TaxonomyTagKeys] = {}
    for snakeId in snakeIds:
        tagKeys = _buildEdgarTagKeys(snakeId)
        if tagKeys.empty:
            _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", snakeId)
            continue
        tagKeysBySnakeId[snakeId] = tagKeys
    if not tagKeysBySnakeId:
        return empty

    tickerUniverse = _loadTickerUniverse()
    listedFiles = _listedParquetFiles(edgarDir, tickerUniverse.cikToTicker)
    if not listedFiles:
        raise EdgarScanMappingError(
            "listed_shard_join",
            f"local parquet {len(parquetFiles)}개 중 ticker universe와 연결된 shard가 없습니다",
            source=str(edgarDir),
        )
    instantBySnakeId = {snakeId: EdgarMapper.getAccountStmt(snakeId) == "BS" for snakeId in tagKeysBySnakeId}

    batch: dict[str, pl.DataFrame] = {}
    tagItems = list(tagKeysBySnakeId.items())
    for offset in range(0, len(tagItems), _DUCKDB_BATCH_ACCOUNT_LIMIT):
        chunk = dict(tagItems[offset : offset + _DUCKDB_BATCH_ACCOUNT_LIMIT])
        try:
            batch.update(
                _scanAccountsDuckDb(
                    listedFiles,
                    chunk,
                    tickerUniverse,
                    freq=freq,
                    instantBySnakeId=instantBySnakeId,
                )
            )
        except EdgarScanExecutionError as batchError:
            _log.warning(
                "scanAccounts(edgar) %d계정 batch 실패, 단일 계정 fallback: %s",
                len(chunk),
                batchError,
            )
            try:
                for snakeId in chunk:
                    batch[snakeId] = scanAccount(snakeId, freq=freq)
            except (EdgarScanError, OSError, RuntimeError, pl.exceptions.PolarsError) as fallbackError:
                raise EdgarScanExecutionError(
                    "batch_fallback",
                    f"single-account fallback failed: {type(fallbackError).__name__}: {fallbackError}",
                    source=str(edgarDir),
                    primaryError=batchError,
                ) from fallbackError

    return {snakeId: batch.get(snakeId, empty[snakeId]) for snakeId in snakeIds}


def scanAccount(
    dartSnakeId: str,
    *,
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 EDGAR 단일 계정 시계열. US 패리티 atomic primitive.

    DART ``scanAccount`` 와 동치다. 동일 snakeId 호출 시 동일 schema 의 wide DataFrame
    반환. 내부적으로 ``_buildEdgarTagKeys`` 가 DART snakeId를 US GAAP과 IFRS concept set으로
    분리 매핑한다.

    parquet source-native 처리:
      - ticker map에 존재하는 filename CIK 파일만 source manifest에 포함.
      - DuckDB threads와 memory limit를 명시해 filter와 company-year aggregation.
      - DuckDB 비가용 또는 실패 시 검증된 ThreadPool file-loop로 fallback.
      - fallback도 실패하면 DuckDB 원인과 shard 원인을 ``EdgarScanExecutionError``에 보존.
      - period pivot wide → ``stockCode + 기간 컬럼들`` (최신 period 좌측).
      - ``_joinCorpName`` 으로 corpName 추가.

    Args:
        dartSnakeId: DART canonical snakeId (예: ``"sales"`` / ``"operating_profit"`` /
            ``"total_assets"``). DART scanAccount 와 호환되는 키 사용. provider 간 동일
            호출 가능. 미매핑 snakeId 호출 시 빈 DataFrame + warning.
        freq: ``"Q"`` 분기 wide (default) / ``"Y"`` 연간 wide. Company 엔진 freq 와 일치.

    Returns:
        pl.DataFrame. ``stockCode`` (=ticker) / ``corpName`` (str) + 기간 컬럼들
        (``"2025Q4"`` / ... / ``"2019Q1"``, 최신 좌측). row ~10K (SEC 등록 ticker 전체).

    Raises:
        ValueError: freq 또는 snakeId 입력이 잘못된 경우.
        EdgarScanMappingError: ticker universe schema 또는 CIK 연결 실패.
        EdgarScanStorageError: listed companyfacts shard 손상.
        EdgarScanExecutionError: DuckDB와 file-loop fallback이 모두 실패.

    Example:
        >>> df = scanAccount("sales", freq="Y")
        >>> df.sort("2025", descending=True).head(10)
              / 가변 기간 컬럼 (float). freq="Q": ``"YYYYQn"`` / freq="Y": ``"YYYY"``.
            - row ≤ SEC 등록 ticker 수 (~10K).
            - 빈 DataFrame: parquet 부재 또는 tagKeys 매칭 0.
        Prerequisites:
            - ``edgar/*.parquet`` (companyfacts XBRL 정규화본).
            - ``_buildEdgarTagKeys`` 의 US GAAP 및 IFRS concept 매핑 사전.
            - SEC tickers.parquet 또는 SEC API origin (CIK ↔ ticker).
        Freshness:
            - SEC EDGAR XBRL 분기 마감 후 ~45 일 (10-Q) / ~60 일 (10-K).
            - parquet 은 SEC ``data.sec.gov/api/xbrl/companyfacts`` nightly pull.
        Dataflow:
            - dartSnakeId → ``_buildEdgarTagKeys`` (US GAAP 및 IFRS concept set)
            - → ticker map filename CIK pruning
            - → DuckDB source-native filter + company-year aggregation
            - → 실패 시 ``_EdgarFileProcessor`` ThreadPool fallback
            - → period pivot wide (latest 좌측) → ``_joinCorpName`` → pl.DataFrame.
        TargetMarkets:
            - US (SEC EDGAR). NYSE/NASDAQ/AMEX/OTC SEC 등록 + 10-K/10-Q 정기공시.
    """
    from dartlab.core.dataLoader import _dataDir

    if not isinstance(dartSnakeId, str) or not dartSnakeId.strip():
        raise ValueError("dartSnakeId는 비어 있지 않은 문자열이어야 합니다")
    freq = str(freq).upper()
    if freq not in {"Q", "Y"}:
        raise ValueError(f"freq는 'Q' 또는 'Y'여야 합니다: {freq!r}")

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))

    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return pl.DataFrame({"stockCode": []})

    tagKeys = _buildEdgarTagKeys(dartSnakeId)
    if tagKeys.empty:
        _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", dartSnakeId)
        return pl.DataFrame({"stockCode": []})

    tickerUniverse = _loadTickerUniverse()
    listedFiles = _listedParquetFiles(edgarDir, tickerUniverse.cikToTicker)
    if not listedFiles:
        raise EdgarScanMappingError(
            "listed_shard_join",
            f"local parquet {len(parquetFiles)}개 중 ticker universe와 연결된 shard가 없습니다",
            source=str(edgarDir),
        )
    stmt = EdgarMapper.getAccountStmt(dartSnakeId)
    isInstant = stmt == "BS"
    _log.info(
        "scanAccount(edgar, '%s', freq=%s, stmt=%s): listed %d/%d 파일 source-native scan",
        dartSnakeId,
        freq,
        stmt or "unknown",
        len(listedFiles),
        len(parquetFiles),
    )

    try:
        result = _scanAccountDuckDb(
            listedFiles,
            tagKeys,
            tickerUniverse,
            freq=freq,
            isInstant=isInstant,
        )
    except EdgarScanExecutionError as duckError:
        _log.warning(
            "scanAccount(edgar) DuckDB 실패, file-loop fallback: %s: %s",
            type(duckError.__cause__).__name__ if duckError.__cause__ else type(duckError).__name__,
            duckError,
        )
        try:
            result = _scanAccountFileLoop(
                listedFiles,
                tagKeys,
                tickerUniverse,
                freq=freq,
                isInstant=isInstant,
            )
        except (EdgarScanError, OSError, RuntimeError, pl.exceptions.PolarsError) as fallbackError:
            raise EdgarScanExecutionError(
                "fallback",
                f"file-loop failed after DuckDB failure: {type(fallbackError).__name__}: {fallbackError}",
                source=str(edgarDir),
                primaryError=duckError,
            ) from fallbackError

    periodCount = len([name for name in result.columns if name not in ("stockCode", "corpName")])
    _log.info("scanAccount(edgar): %d종목 × %d기간", result.height, periodCount)
    return result


# ── scanRatio (EDGAR) ─────────────────────────────────────────

# DART 비율 정의 재활용
from dartlab.providers.dart.finance.scanAccount import _RATIO_DEFS


def scanRatio(
    ratioName: str,
    *,
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 EDGAR 재무비율 시계열.

    Args:
        ratioName: 비율 식별자. scanRatioList() 참조.
        freq: "Q" 분기 (기본) · "Y" 연간. Company 엔진과 일치.

    Returns:
        stockCode | corpName | 기간컬럼들... DataFrame.

    Raises:
        ValueError: 지원하지 않는 ratioName.
        EdgarScanError: 구성 계정의 ticker universe, 저장소 또는 scan 실행 실패.

    Example:
        >>> scanRatio("debt_ratio", freq="Y")
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        msg = f"지원하지 않는 비율: '{ratioName}'. 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, freq=freq)
    return _calcSimpleRatio(defn, freq=freq)


def _calcSimpleRatio(defn: dict, *, freq: str = "Q") -> pl.DataFrame:
    """분자/분모 비율 계산."""
    accountFrames = scanAccounts([defn["numer"], defn["denom"]], freq=freq)
    numer = accountFrames[defn["numer"]]
    denom = accountFrames[defn["denom"]]

    numerCols = [c for c in numer.columns if c not in ("stockCode", "corpName")]
    denomCols = [c for c in denom.columns if c not in ("stockCode", "corpName")]
    commonCols = sorted(set(numerCols) & set(denomCols), reverse=True)

    if not commonCols:
        return pl.DataFrame({"stockCode": []})

    joined = numer.select(["stockCode"] + commonCols).join(
        denom.select(["stockCode"] + commonCols),
        on="stockCode",
        suffix="_d",
    )

    isPct = defn.get("pct", False)
    multiplier = 100.0 if isPct else 1.0

    resultExprs = [pl.col("stockCode")]
    for y in commonCols:
        expr = (
            pl.when((pl.col(f"{y}_d") != 0) & pl.col(f"{y}_d").is_not_null() & pl.col(y).is_not_null())
            .then((pl.col(y) / pl.col(f"{y}_d") * multiplier).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(y)
        )
        resultExprs.append(expr)

    result = joined.select(resultExprs)
    return _joinCorpName(result)


def _calcYoyRatio(defn: dict, *, freq: str = "Q") -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], freq=freq)
    periodCols = sorted(c for c in base.columns if c not in ("stockCode", "corpName"))

    if len(periodCols) < 2:
        return pl.DataFrame({"stockCode": []})

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(periodCols)):
        cur = periodCols[i]
        prev = periodCols[i - 1]
        expr = (
            pl.when((pl.col(prev) != 0) & pl.col(prev).is_not_null() & pl.col(cur).is_not_null())
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    yoyCols = [periodCols[i] for i in range(1, len(periodCols))]
    result = base.select(resultExprs).select(["stockCode"] + list(reversed(yoyCols)))
    return _joinCorpName(result)
