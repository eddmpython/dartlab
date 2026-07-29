"""DuckDB 기반 long → wide 피벗 — Phase B 처방의 핵심.

기존 ``_pivotToSeries`` 가 ``df.iter_rows(named=True)`` 로 long DataFrame
전수를 Python row dict 로 변환하며 Python heap 누적이 발생했다 (현대차 기준
peak 13GB 의 산술적 trigger). 본 모듈은 동일 결과를 다음 단계로 도출한다:

1. Python 에서 ``snake_id`` / ``priority`` / ``_ingestion_order`` 3 컬럼만
   long DataFrame 에 신설 (mapper LRU 보존).
2. DuckDB 가 ``ROW_NUMBER() OVER (PARTITION BY sj_div, snake_id, period_key
   ORDER BY priority ASC, _ingestion_order ASC)`` 로 tie-break 후 ``rn = 1``
   선별 — 구 코드의 ``priorityTrack`` Python dict 가 SQL window 로 흡수된다.
3. 결과 long Arrow Table 을 결과 dict 로 변환 — wide cell 수 만큼만 iter
   (구 코드의 *long row 수* iter 보다 ~3 배 적음).

Python intermediate dict (priorityTrack · unmappedAccounts · per-row dict)
가 사라지므로 peak 가 *결과 크기* 만 점유.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import polars as pl

from dartlab.core.accounts import mappingLedger
from dartlab.core.utils.period import formatPeriod
from dartlab.providers.dart.finance.mapper import AccountMapper

if TYPE_CHECKING:
    pass

_log = logging.getLogger(__name__)

QUARTER_ORDER = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def _attachMappingColumns(
    df: pl.DataFrame,
    *,
    accountIdPriority,
    fallbackSnakeId,
    ifrsTopLevelIds: frozenset[str],
) -> tuple[pl.DataFrame, dict[str, int], int, list[tuple[str, str, str, int]]]:
    """long DataFrame 에 ``snake_id`` / ``priority`` / ``_ingestion_order`` 컬럼 신설.

    mapper.map LRU 캐시를 보존하기 위해 매핑은 Python loop. priority/ingestion 은
    polars expression 으로 벡터화. nonstd_ fallback + unmapped 카운트 동시 회수.

    Returns:
        (augmented_df, unmappedAccounts, unmappedRows, ledgerEntries)
    """
    mapper = AccountMapper.get()

    accountIds = df.get_column("account_id").to_list() if "account_id" in df.columns else [""] * df.height
    accountNms = df.get_column("account_nm").to_list() if "account_nm" in df.columns else [""] * df.height

    snakeIds: list[str | None] = []
    priorities: list[int] = []
    unmappedAccounts: dict[str, int] = {}
    unmappedRows = 0
    ledgerEntries: list[tuple[str, str, str, int]] = []
    ledgerKeys: dict[tuple[str, str, str], int] = {}

    sjDivs = df.get_column("sj_div").to_list() if "sj_div" in df.columns else [""] * df.height

    for i in range(df.height):
        aId = accountIds[i] or ""
        aNm = accountNms[i] or ""
        sj = sjDivs[i] or ""
        sjNorm = "IS" if sj == "CIS" else sj

        snake = mapper.map(aId, aNm)
        if snake is None:
            snake = fallbackSnakeId(aNm)
            if sjNorm in ("BS", "IS", "CF"):
                ledgerKeys[(aId, aNm, sjNorm)] = ledgerKeys.get((aId, aNm, sjNorm), 0) + 1
            if snake is None:
                unmappedRows += 1
                k = f"{aId}|{aNm}"
                unmappedAccounts[k] = unmappedAccounts.get(k, 0) + 1
            else:
                k = f"{aId}|{aNm}"
                unmappedAccounts[k] = unmappedAccounts.get(k, 0) + 1

        snakeIds.append(snake)

        # priority 계산 — _accountIdPriority 의 등가 (구 코드 inline).
        if not aId:
            priorities.append(3)
        else:
            lower = aId.lower()
            if lower in ifrsTopLevelIds:
                priorities.append(0)
            elif lower.startswith("ifrs-full_") or lower.startswith("ifrs_"):
                priorities.append(1)
            elif lower.startswith("dart_"):
                priorities.append(2)
            else:
                priorities.append(3)

    augmented = df.with_columns(
        pl.Series("snake_id", snakeIds, dtype=pl.Utf8),
        pl.Series("priority", priorities, dtype=pl.Int32),
        pl.int_range(0, df.height, dtype=pl.Int64).alias("_ingestion_order"),
    )

    for (aId, aNm, sj), cnt in ledgerKeys.items():
        ledgerEntries.append((aId, aNm, sj, cnt))

    return augmented, unmappedAccounts, unmappedRows, ledgerEntries


def _buildPeriodKeyColumn(df: pl.DataFrame) -> pl.DataFrame:
    """``bsns_year`` + ``reprt_nm`` → ``period_key`` 컬럼."""
    yearCol = df.get_column("bsns_year").to_list()
    reprtCol = df.get_column("reprt_nm").to_list()
    keys: list[str] = []
    for y, r in zip(yearCol, reprtCol, strict=False):
        qNum = QUARTER_ORDER.get(r, 0)
        keys.append(formatPeriod(y, qNum))
    return df.with_columns(pl.Series("period_key", keys, dtype=pl.Utf8))


_RESULT_SCHEMA = {
    "sj_div_norm": pl.Utf8,
    "snake_id": pl.Utf8,
    "period_key": pl.Utf8,
    "amount": pl.Float64,
}


def _runDuckdbPivot(augmented: pl.DataFrame) -> "pl.DataFrame":
    """DuckDB ROW_NUMBER tie-break + 선별. 결과 long DataFrame (sj_div_norm, snake_id,
    period_key, amount). 입력 empty 시 동일 schema 의 빈 DataFrame 반환.
    """
    if augmented.height == 0:
        return pl.DataFrame(schema=_RESULT_SCHEMA)

    import duckdb

    con = duckdb.connect(":memory:")
    try:
        con.register("longDf", augmented.to_arrow())
        rel = con.execute("""
            WITH tagged AS (
                SELECT
                    CASE WHEN sj_div = 'CIS' THEN 'IS' ELSE sj_div END AS sj_div_norm,
                    snake_id,
                    period_key,
                    _normalized_amount AS amount,
                    priority,
                    _ingestion_order
                FROM longDf
                WHERE sj_div IN ('BS', 'IS', 'CIS', 'CF')
                  AND snake_id IS NOT NULL
            ),
            ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY sj_div_norm, snake_id, period_key
                        ORDER BY
                            CASE WHEN amount IS NULL THEN 1 ELSE 0 END ASC,
                            priority ASC,
                            _ingestion_order ASC
                    ) AS rn
                FROM tagged
            )
            SELECT sj_div_norm, snake_id, period_key, amount
            FROM ranked
            WHERE rn = 1
        """)
        result = rel.to_arrow_table()
        if result.num_rows == 0:
            return pl.DataFrame(schema=_RESULT_SCHEMA)
        return pl.from_arrow(result)
    finally:
        con.close()


def pivotToSeriesArrow(
    df: pl.DataFrame,
    periods: list[str],
    *,
    accountIdPriority,
    fallbackSnakeId,
    ifrsTopLevelIds: frozenset[str],
    stockCode: str | None = None,
) -> dict[str, dict[str, list[float | None]]]:
    """``_pivotToSeries`` 의 DuckDB 버전 — 동일 결과, Python intermediate dict 0.

    Args:
        df: ``_normalized_amount`` 포함 long DataFrame.
        periods: 결과 list 길이 + 인덱스. (pl.DataFrame 의 period 와 정확히 매치.)
        accountIdPriority: priority 함수 (caller 가 _accountIdPriority 전달).
        fallbackSnakeId: nonstd_ fallback 함수.
        ifrsTopLevelIds: priority 0 화이트리스트.
        stockCode: mapping ledger 옵트인 시 기록.

    Returns:
        ``{sjDiv: {snakeId: [v1, v2, ...]}}`` — caller 호환 dict.
        ``_fillSnakeIdGaps`` / ``sortSeries`` post-process 는 caller 가 수행.

    Raises:
        OSError: mapping ledger를 명시적으로 켠 상태에서 관측 저장이 실패한 경우.

    Example:
        >>> pivotToSeriesArrow(df, ["2024", "2023"], ...)  # doctest: +SKIP
    """
    augmented, unmappedAccounts, unmappedRows, ledgerEntries = _attachMappingColumns(
        df,
        accountIdPriority=accountIdPriority,
        fallbackSnakeId=fallbackSnakeId,
        ifrsTopLevelIds=ifrsTopLevelIds,
    )

    augmented = _buildPeriodKeyColumn(augmented)

    selected = _runDuckdbPivot(augmented)

    periodIdx = {p: i for i, p in enumerate(periods)}
    nPeriods = len(periods)
    result: dict[str, dict[str, list[float | None]]] = {"BS": {}, "IS": {}, "CF": {}}

    # 결과 long → wide dict. iter 회수 = wide cell 수 (구 코드의 long row 수보다 작음).
    if selected.height > 0:
        sjCol = selected.get_column("sj_div_norm").to_list()
        snakeCol = selected.get_column("snake_id").to_list()
        periodCol = selected.get_column("period_key").to_list()
        amountCol = selected.get_column("amount").to_list()
        for i in range(selected.height):
            sj = sjCol[i]
            if sj not in result:
                continue
            snake = snakeCol[i]
            pKey = periodCol[i]
            idx = periodIdx.get(pKey)
            if idx is None:
                continue
            target = result[sj]
            row = target.get(snake)
            if row is None:
                row = [None] * nPeriods
                target[snake] = row
            row[idx] = amountCol[i]

    # mapping 로그 — 구 코드와 같은 형식 (parity).
    totalRows = df.height
    if unmappedAccounts:
        nonstdRows = sum(unmappedAccounts.values()) - unmappedRows
        _log.info(
            "finance 매핑: %d/%d 행 표준 매핑, %d 행 nonstd_ fallback, %d 행 손실 (%d 고유 비표준 계정)",
            totalRows - unmappedRows - nonstdRows,
            totalRows,
            nonstdRows,
            unmappedRows,
            len(unmappedAccounts),
        )
        for acct, cnt in sorted(unmappedAccounts.items(), key=lambda x: -x[1])[:5]:
            _log.info("  표준화 후보: %s (%d회)", acct, cnt)

    # ENV gated ledger
    if ledgerEntries and mappingLedger.isEnabled():
        records = [
            {"accountId": aId, "accountNm": aNm, "sjDiv": sj, "occurrenceCount": cnt}
            for (aId, aNm, sj, cnt) in ledgerEntries
        ]
        mappingLedger.append(records, stockCode=stockCode)

    return result
