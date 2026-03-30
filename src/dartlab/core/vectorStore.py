"""벡터 임베딩 + 시맨틱 검색 — LanceDB 기반.

공시 원문을 임베딩하여 자연어로 검색 가능하게 만든다.
GPU 자동 감지, Scalar Quantization 압축 지원.

``pip install dartlab[vector]`` 필요 (sentence-transformers + lancedb).

사용법::

    from dartlab.core.vectorStore import buildFromParquet, search

    buildFromParquet("data/dart/allFilings/20260327.parquet")
    results = search("유상증자 결정", top_k=10)
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config as _cfg

# ── 상수 ──

_DEFAULT_MODEL = "jhgan/ko-sroberta-multitask"
_MAX_CHUNK_CHARS = 10_000
_OVERLAP_CHARS = 500
_TABLE_NAME = "filings"

# ── lazy imports ──

_model = None
_db = None
_device = None


def _indexDir() -> Path:
    """벡터 인덱스 저장 디렉토리."""
    d = Path(_cfg.dataDir) / "dart" / "vectorIndex"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _detectDevice() -> str:
    """GPU 자동 감지. CUDA > MPS > CPU."""
    global _device
    if _device is not None:
        return _device

    try:
        import torch

        if torch.cuda.is_available():
            _device = "cuda"
            name = torch.cuda.get_device_name(0)
            print(f"[vectorStore] GPU 감지: {name}")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            _device = "mps"
            print("[vectorStore] Apple MPS 감지")
        else:
            _device = "cpu"
    except ImportError:
        _device = "cpu"

    return _device


def _loadModel():
    """임베딩 모델 lazy load (GPU 자동 사용)."""
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers가 필요합니다.\n"
            "  pip install dartlab[vector]"
        )

    device = _detectDevice()
    _model = SentenceTransformer(_DEFAULT_MODEL, device=device)
    return _model


def _openDb():
    """LanceDB 연결 lazy open."""
    global _db
    if _db is not None:
        return _db

    try:
        import lancedb
    except ImportError:
        raise ImportError(
            "lancedb가 필요합니다.\n"
            "  pip install dartlab[vector]"
        )

    _db = lancedb.connect(str(_indexDir()))
    return _db


def _chunk(text: str, title: str = "") -> list[str]:
    """긴 텍스트를 청크로 분할. 짧으면 그대로 반환."""
    if not text or len(text) <= _MAX_CHUNK_CHARS:
        prefix = f"{title}\n\n" if title else ""
        return [f"{prefix}{text}"] if text else []

    chunks = []
    prefix = f"{title}\n\n" if title else ""
    start = 0
    while start < len(text):
        end = start + _MAX_CHUNK_CHARS
        chunk = text[start:end]
        chunks.append(f"{prefix}{chunk}")
        start = end - _OVERLAP_CHARS

    return chunks


# ── 인덱스 빌드 ──


def buildFromParquet(
    parquetPath: str | Path,
    *,
    batchSize: int = 256,
    showProgress: bool = True,
) -> int:
    """parquet → 청킹 → 임베딩(GPU) → LanceDB 저장.

    Parameters
    ----------
    parquetPath : allFilings parquet 경로 (파일 또는 glob).
    batchSize : 임베딩 배치 크기 (GPU면 256, CPU면 64 자동 조정).
    showProgress : 진행 표시 여부.

    Returns
    -------
    int
        저장된 벡터 수.
    """
    import time

    model = _loadModel()
    db = _openDb()

    device = _detectDevice()
    if device == "cpu":
        batchSize = min(batchSize, 64)

    # glob 또는 단일 파일
    path = Path(parquetPath)
    if "*" in str(path):
        df = pl.scan_parquet(str(path)).collect()
    else:
        df = pl.read_parquet(path)

    # section_content가 있는 행만
    df = df.filter(pl.col("section_content").is_not_null())
    if df.height == 0:
        if showProgress:
            print("[vectorStore] 임베딩할 섹션 없음")
        return 0

    # 이미 인덱싱된 rcept_no 건너뜀 (증분)
    existingIds: set[str] = set()
    try:
        table = db.open_table(_TABLE_NAME)
        # 해당 날짜의 기존 벡터 확인
        dates = df["rcept_dt"].unique().to_list()
        for dt in dates:
            try:
                existing = table.search().where(f"rcept_dt = '{dt}'").limit(1).to_pandas()
                if not existing.empty:
                    allExisting = table.search().where(f"rcept_dt = '{dt}'").limit(100_000).to_pandas()
                    existingIds.update(allExisting["id"].tolist())
            except Exception:
                pass
    except (ValueError, FileNotFoundError):
        pass

    if showProgress:
        print(f"[vectorStore] {df.height}개 섹션, 디바이스: {device}, 배치: {batchSize}")

    # 청킹 + 메타데이터 준비
    records: list[dict] = []
    for row in df.iter_rows(named=True):
        chunks = _chunk(row["section_content"], row.get("section_title", ""))
        for chunkIdx, chunkText in enumerate(chunks):
            recId = f"{row['rcept_no']}_{row['section_order']}_{chunkIdx}"
            if recId in existingIds:
                continue
            records.append({
                "id": recId,
                "text": chunkText[:2000],
                "full_text": chunkText,
                "rcept_no": row["rcept_no"],
                "corp_code": row.get("corp_code", ""),
                "corp_name": row.get("corp_name", ""),
                "stock_code": row.get("stock_code", ""),
                "rcept_dt": row.get("rcept_dt", ""),
                "report_nm": row.get("report_nm", ""),
                "section_title": row.get("section_title", ""),
            })

    if not records:
        if showProgress:
            print("[vectorStore] 신규 청크 없음 (이미 인덱싱됨)")
        return 0

    # 배치 임베딩
    texts = [r["full_text"] for r in records]
    if showProgress:
        print(f"[vectorStore] {len(texts)}개 청크 임베딩 중...")

    t0 = time.time()
    allVectors = []
    for i in range(0, len(texts), batchSize):
        batch = texts[i : i + batchSize]
        vectors = model.encode(
            batch,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=batchSize,
        )
        allVectors.extend(vectors.tolist())
        if showProgress and (i + batchSize) % (batchSize * 5) == 0:
            elapsed = time.time() - t0
            speed = (i + batchSize) / elapsed if elapsed > 0 else 0
            print(f"  [{i + batchSize}/{len(texts)}] {speed:.0f} chunks/sec")

    elapsed = time.time() - t0

    for rec, vec in zip(records, allVectors):
        rec["vector"] = vec
        del rec["full_text"]

    # LanceDB 저장
    if showProgress:
        print(f"[vectorStore] {len(records)}개 벡터 저장 중...")

    try:
        table = db.open_table(_TABLE_NAME)
        table.add(records)
    except (ValueError, FileNotFoundError):
        db.create_table(_TABLE_NAME, records)

    if showProgress:
        speed = len(texts) / elapsed if elapsed > 0 else 0
        print(f"[vectorStore] 완료: {len(records)}개 벡터, "
              f"{elapsed:.1f}초 ({speed:.0f} chunks/sec, {device})")

    return len(records)


def compactIndex() -> dict:
    """벡터 인덱스 최적화 — Scalar Quantization 압축 + IVF-PQ 인덱스 생성.

    데이터가 충분히 쌓인 후 (1만+ 벡터) 호출하면 효과적.
    검색 속도 향상 + 디스크 용량 절감.

    Returns
    -------
    dict
        압축 전후 통계.
    """
    db = _openDb()

    try:
        table = db.open_table(_TABLE_NAME)
    except (ValueError, FileNotFoundError):
        return {"error": "테이블 없음"}

    beforeCount = table.count_rows()

    # IVF-PQ 인덱스 생성 (벡터 수에 따라 파티션 조정)
    nPartitions = max(2, min(256, beforeCount // 500))
    nSubVectors = 48  # 768d / 48 = 16d per subvector

    table.create_index(
        metric="cosine",
        num_partitions=nPartitions,
        num_sub_vectors=nSubVectors,
    )

    afterCount = table.count_rows()

    return {
        "vectors": afterCount,
        "partitions": nPartitions,
        "subVectors": nSubVectors,
        "compressed": True,
    }


# ── 검색 ──


def search(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    top_k: int = 10,
) -> pl.DataFrame:
    """자연어로 공시 시맨틱 검색.

    Parameters
    ----------
    query : 검색 쿼리 (한국어).
    corpCode : 특정 기업으로 필터 (8자리).
    stockCode : 종목코드로 필터 (6자리).
    top_k : 반환 건수.

    Returns
    -------
    pl.DataFrame
        검색 결과. columns: score, rcept_no, corp_name, rcept_dt,
        report_nm, section_title, text
    """
    model = _loadModel()
    db = _openDb()

    try:
        table = db.open_table(_TABLE_NAME)
    except (ValueError, FileNotFoundError):
        return pl.DataFrame()

    queryVec = model.encode(query, normalize_embeddings=True).tolist()

    # 필터가 있으면 where절로 사전 필터
    searchQuery = table.search(queryVec)

    whereClause = []
    if corpCode:
        whereClause.append(f"corp_code = '{corpCode}'")
    if stockCode:
        whereClause.append(f"stock_code = '{stockCode}'")
    if whereClause:
        searchQuery = searchQuery.where(" AND ".join(whereClause))

    searchQuery = searchQuery.limit(top_k)
    results = searchQuery.to_pandas()

    if results.empty:
        return pl.DataFrame()

    keepCols = [
        "_distance", "rcept_no", "corp_name", "stock_code",
        "rcept_dt", "report_nm", "section_title", "text",
    ]
    availCols = [c for c in keepCols if c in results.columns]
    result = pl.from_pandas(results[availCols])

    if "_distance" in result.columns:
        result = result.rename({"_distance": "distance"}).with_columns(
            (1 - pl.col("distance")).alias("score")
        ).drop("distance").sort("score", descending=True)

    return result


def indexStats() -> dict:
    """벡터 인덱스 통계."""
    import os

    indexPath = _indexDir()
    try:
        db = _openDb()
        table = db.open_table(_TABLE_NAME)
        count = table.count_rows()
        totalSize = sum(
            f.stat().st_size for f in indexPath.rglob("*") if f.is_file()
        )
        return {
            "table": _TABLE_NAME,
            "vectors": count,
            "sizeMb": round(totalSize / 1024 / 1024, 1),
            "path": str(indexPath),
            "device": _device or "unknown",
        }
    except (ValueError, FileNotFoundError, ImportError):
        return {"table": _TABLE_NAME, "vectors": 0, "sizeMb": 0, "path": str(indexPath)}
