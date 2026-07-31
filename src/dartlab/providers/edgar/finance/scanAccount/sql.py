"""EDGAR 계정 스캔 DuckDB 실행 튜닝값과 연도 집계 SQL.

SQL 문자열과 스레드·메모리 상한만 소유한다. 실행과 조립은 ``pipeline`` 이,
공개 호출은 ``api`` 가 맡는다."""

from __future__ import annotations

_DUCKDB_THREADS = 4
_DUCKDB_MEMORY_LIMIT_MB = 192
_DUCKDB_BATCH_THREADS = 2
_DUCKDB_BATCH_MEMORY_LIMIT_MB = 256
_DUCKDB_BATCH_ACCOUNT_LIMIT = 3
_DUCKDB_YEAR_SQL = """
    WITH matched AS (
        SELECT
            regexp_extract(filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
            namespace,
            lower(tag) AS tag,
            val,
            fy,
            fp,
            start,
            "end",
            filed,
            file_row_number,
            CASE namespace
                WHEN 'us-gaap' THEN list_position(?, lower(tag))
                ELSE list_position(?, lower(tag))
            END AS tagPriority,
            CASE namespace
                WHEN 'us-gaap' THEN
                    CASE WHEN lower(tag) IN (SELECT unnest(?)) THEN 0 ELSE 1 END
                ELSE
                    CASE WHEN lower(tag) IN (SELECT unnest(?)) THEN 0 ELSE 1 END
            END AS fallbackRank,
            min(CASE namespace WHEN 'us-gaap' THEN 0 ELSE 1 END)
                OVER (PARTITION BY filename) AS selectedNamespace
        FROM read_parquet(?, filename = true, file_row_number = true)
        WHERE (
                (namespace = 'us-gaap' AND lower(tag) IN (SELECT unnest(?)))
                OR
                (namespace = 'ifrs-full' AND lower(tag) IN (SELECT unnest(?)))
              )
          AND starts_with(unit, 'USD')
          AND fy BETWEEN 2000 AND 2030
          AND fp IN ('FY', 'Q1', 'Q2', 'Q3')
    ),
    deduped AS (
        SELECT *
        FROM matched
        QUALIFY row_number() OVER (
            PARTITION BY fileCik, fy, fp, namespace, tag, start, "end"
            ORDER BY (val IS NULL), filed DESC, file_row_number
        ) = 1
    )
    SELECT
        fileCik,
        fy,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'FY') AS fyFirst,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        )
            FILTER (WHERE fp = 'FY') AS fyVal,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q1') AS q1,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q2') AS q2,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q3') AS q3
    FROM deduped
    WHERE (namespace = 'us-gaap' AND selectedNamespace = 0)
       OR (namespace = 'ifrs-full' AND selectedNamespace = 1)
    GROUP BY fileCik, fy
"""
_DUCKDB_BATCH_YEAR_SQL = """
    WITH matched AS (
        SELECT
            batchTags.snakeId,
            regexp_extract(facts.filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
            facts.namespace,
            lower(facts.tag) AS tag,
            facts.val,
            facts.fy,
            facts.fp,
            facts.start,
            facts."end",
            facts.filed,
            facts.file_row_number,
            batchTags.priority AS tagPriority,
            batchTags.fallbackRank AS fallbackRank,
            min(CASE facts.namespace WHEN 'us-gaap' THEN 0 ELSE 1 END)
                OVER (PARTITION BY facts.filename, batchTags.snakeId) AS selectedNamespace
        FROM read_parquet(?, filename = true, file_row_number = true) AS facts
        INNER JOIN batchTags
            ON facts.namespace = batchTags.namespace
           AND lower(facts.tag) = batchTags.tag
        WHERE starts_with(facts.unit, 'USD')
          AND facts.fy BETWEEN 2000 AND 2030
          AND facts.fp IN ('FY', 'Q1', 'Q2', 'Q3')
    ),
    deduped AS (
        SELECT *
        FROM matched
        QUALIFY row_number() OVER (
            PARTITION BY snakeId, fileCik, fy, fp, namespace, tag, start, "end"
            ORDER BY (val IS NULL), filed DESC, file_row_number
        ) = 1
    )
    SELECT
        snakeId,
        fileCik,
        fy,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'FY') AS fyFirst,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        )
            FILTER (WHERE fp = 'FY') AS fyVal,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q1') AS q1,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q2') AS q2,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q3') AS q3
    FROM deduped
    WHERE (namespace = 'us-gaap' AND selectedNamespace = 0)
       OR (namespace = 'ifrs-full' AND selectedNamespace = 1)
    GROUP BY snakeId, fileCik, fy
"""
