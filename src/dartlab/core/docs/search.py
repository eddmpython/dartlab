"""docs semantic search."""

import numpy as np
import polars as pl


def _loadEmbedding(stockCode: str) -> pl.DataFrame | None:
    """embedding parquet 로드 (on-demand 다운로드)."""
    from dartlab.core.dataLoader import loadData

    try:
        return loadData(stockCode, "docsEmbedding")
    except (FileNotFoundError, KeyError, ValueError, OSError):
        return None


def _encodeQuery(query: str) -> np.ndarray | None:
    """쿼리 임베딩. sentence-transformers 없으면 None."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None

    model = SentenceTransformer("intfloat/multilingual-e5-base")
    vec = model.encode(f"query: {query}", normalize_embeddings=True)
    return vec.astype(np.float32)


def _recoverChunkText(
    stockCode: str,
    hits: pl.DataFrame,
) -> pl.DataFrame:
    """검색 히트에 원문 텍스트를 붙인다.

    docs parquet에서 해당 section을 찾고,
    build.py와 동일한 청킹을 재수행해서 정확한 청크 본문을 추출.
    """
    from dartlab.core.dataLoader import loadData

    try:
        docsDf = loadData(stockCode, "docs")
    except (FileNotFoundError, KeyError, ValueError, OSError):
        return hits.with_columns(pl.lit("").alias("text"))

    # 청킹 함수 import (scripts/embedding/chunk.py와 동일 로직 인라인)
    texts = []
    for row in hits.iter_rows(named=True):
        rceptNo = row["rceptNo"]
        secOrder = row["sectionOrder"]
        chunkTitle = row.get("chunkTitle", "")

        docRow = docsDf.filter((pl.col("rcept_no") == rceptNo) & (pl.col("section_order") == secOrder))
        if docRow.is_empty():
            texts.append("")
            continue

        content = docRow["section_content"][0] or ""
        # 해당 청크 본문 찾기: chunkTitle로 매칭
        found = _findChunkText(content, chunkTitle)
        texts.append(found)

    return hits.with_columns(pl.Series("text", texts))


def _findChunkText(content: str, chunkTitle: str, maxChars: int = 5000) -> str:
    """section_content에서 chunkTitle에 해당하는 청크 본문 추출."""
    import re

    if not content:
        return ""

    # chunkTitle이 비어있으면 전체 반환 (단일 청크 section)
    if not chunkTitle:
        return content[:maxChars]

    # "(part N)" suffix 제거
    cleanTitle = re.sub(r"\s*\(part \d+\)$", "", chunkTitle)

    if not cleanTitle:
        return content[:maxChars]

    # 제목 위치 찾기
    pos = content.find(cleanTitle)
    if pos == -1:
        return content[:maxChars]

    # 제목부터 maxChars까지 추출
    return content[pos : pos + maxChars]


def _keywordSearch(
    df: pl.DataFrame,
    query: str,
    topK: int,
) -> pl.DataFrame:
    """키워드 fallback 검색."""
    terms = query.split()
    if not terms:
        return pl.DataFrame()

    # AND 먼저
    expr = pl.lit(True)
    for term in terms:
        expr = expr & (
            pl.col("sectionTitle").str.contains(term, literal=True)
            | pl.col("chunkTitle").str.contains(term, literal=True)
        )
    matched = df.filter(expr).head(topK)

    # AND 결과 없으면 OR
    if matched.is_empty():
        expr = pl.lit(False)
        for term in terms:
            expr = expr | (
                pl.col("sectionTitle").str.contains(term, literal=True)
                | pl.col("chunkTitle").str.contains(term, literal=True)
            )
        matched = df.filter(expr).head(topK)

    return matched.select(["chunkId", "rceptNo", "year", "sectionOrder", "sectionTitle", "chunkTitle"]).with_columns(
        pl.lit(0.0).alias("score"),
        pl.lit("keyword").alias("method"),
    )


def searchDocs(
    stockCode: str,
    query: str,
    *,
    topK: int = 5,
    year: int | None = None,
    withText: bool = True,
) -> pl.DataFrame | None:
    """docs semantic search.

    embedding parquet + numpy cosine.
    sentence-transformers 없으면 keyword fallback.
    withText=True면 docs parquet에서 원문 스니펫까지 반환.
    """
    embDf = _loadEmbedding(stockCode)
    if embDf is None:
        return None

    if year is not None:
        embDf = embDf.filter(pl.col("year") == year)

    if embDf.is_empty():
        return None

    queryVec = _encodeQuery(query)

    if queryVec is None:
        hits = _keywordSearch(embDf, query, topK)
    else:
        # int8 복원 → cosine similarity
        vectors = np.array(embDf["vector"].to_list(), dtype=np.float32)
        vecMin = embDf["vecMin"][0]
        vecScale = embDf["vecScale"][0]
        restored = vectors * vecScale + vecMin

        norms = np.linalg.norm(restored, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        restored = restored / norms

        queryNorm = queryVec / (np.linalg.norm(queryVec) or 1.0)
        scores = restored @ queryNorm

        topIdx = np.argsort(scores)[::-1][:topK]

        hits = (
            embDf[topIdx.tolist()]
            .select(["chunkId", "rceptNo", "year", "sectionOrder", "sectionTitle", "chunkTitle"])
            .with_columns(
                pl.Series("score", [float(scores[i]) for i in topIdx]),
                pl.lit("vector").alias("method"),
            )
        )

    if hits.is_empty():
        return hits

    if withText:
        hits = _recoverChunkText(stockCode, hits)

    return hits
