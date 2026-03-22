"""XBRL Fact Explorer — SEC companyfacts 태그 단위 전 기간 값 탐색.

DART에 없는 EDGAR 고유 기능. SEC가 제공하는 모든 XBRL 태그의
전체 보고 이력을 조회할 수 있다.

사용법::

    c = Company("AAPL")
    c.finance.explore("Revenue")      # Revenue 관련 태그 전체 이력
    c.finance.explore("StockholdersEquity")  # 자본 관련 태그
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def explore(
    cik: str,
    query: str,
    *,
    edgarDir: Path | None = None,
) -> pl.DataFrame | None:
    """SEC companyfacts에서 query와 매칭되는 XBRL 태그의 전체 보고 이력 반환.

    Args:
        cik: SEC CIK 번호.
        query: 검색어 (태그명 부분 매칭, 대소문자 무시).
        edgarDir: EDGAR 데이터 디렉토리.

    Returns:
        DataFrame with columns: tag, snakeId, period, value, unit, form, filed
    """
    if edgarDir is None:
        from dartlab.core.dataLoader import _dataDir

        edgarDir = _dataDir("edgar")

    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return None

    df = pl.read_parquet(path)
    if df.is_empty():
        return None

    # us-gaap namespace만
    df = df.filter(pl.col("namespace") == "us-gaap")

    # query로 태그 필터 (대소문자 무시 부분 매칭)
    queryLower = query.lower()
    df = df.filter(pl.col("tag").str.to_lowercase().str.contains(queryLower))

    if df.is_empty():
        return None

    # snakeId 매핑
    from dartlab.engines.edgar.finance.mapper import EdgarMapper

    tags = df["tag"].unique().to_list()
    tagToSnake = {}
    for tag in tags:
        mapped = EdgarMapper.map(tag)
        tagToSnake[tag] = mapped if mapped else tag

    # 정리된 DataFrame 구성
    requiredCols = ["tag", "val", "end", "fp", "fy", "form", "filed"]
    available = [c for c in requiredCols if c in df.columns]
    result = df.select(available)

    # snakeId 컬럼 추가
    result = result.with_columns(pl.col("tag").replace_strict(tagToSnake, default=pl.col("tag")).alias("snakeId"))

    # period 컬럼 생성 (fy-fp 형태)
    if "fy" in result.columns and "fp" in result.columns:
        result = result.with_columns((pl.col("fy").cast(pl.Utf8) + pl.lit("-") + pl.col("fp")).alias("period"))

    # 정렬: tag → period 내림차순
    sortCols = []
    if "tag" in result.columns:
        sortCols.append("tag")
    if "end" in result.columns:
        sortCols.append("end")

    if sortCols:
        result = result.sort(sortCols, descending=[False] + [True] * (len(sortCols) - 1))

    return result


def listTags(
    cik: str,
    *,
    edgarDir: Path | None = None,
) -> pl.DataFrame | None:
    """SEC companyfacts의 모든 us-gaap 태그 목록과 빈도.

    Returns:
        DataFrame with columns: tag, snakeId, count, stmt
    """
    if edgarDir is None:
        from dartlab.core.dataLoader import _dataDir

        edgarDir = _dataDir("edgar")

    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        return None

    df = pl.read_parquet(path)
    if df.is_empty():
        return None

    df = df.filter(pl.col("namespace") == "us-gaap")

    tagCounts = df.group_by("tag").agg(pl.len().alias("count")).sort("count", descending=True)

    from dartlab.engines.edgar.finance.mapper import EdgarMapper

    tags = tagCounts["tag"].to_list()
    tagToSnake = {}
    stmtMap = EdgarMapper.classifyTagsByStmt()
    tagToStmt: dict[str, str] = {}
    for stmt, tagSet in stmtMap.items():
        for t in tagSet:
            tagToStmt[t] = stmt

    for tag in tags:
        mapped = EdgarMapper.map(tag)
        tagToSnake[tag] = mapped if mapped else ""

    tagCounts = tagCounts.with_columns(
        pl.col("tag").replace_strict(tagToSnake, default=pl.lit("")).alias("snakeId"),
        pl.col("tag").replace_strict(tagToStmt, default=pl.lit("")).alias("stmt"),
    )

    return tagCounts
