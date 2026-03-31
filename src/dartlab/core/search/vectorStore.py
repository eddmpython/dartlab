"""벡터 임베딩 + 시맨틱 검색 — LanceDB 기반.

공시 원문을 임베딩하여 자연어로 검색 가능하게 만든다.
GPU 자동 감지, Scalar Quantization 압축 지원.

``pip install dartlab[vector]`` 필요 (sentence-transformers + lancedb).

사용법::

    from dartlab.core.vectorStore import buildFromParquet, search

    buildFromParquet("data/dart/allFilings/20260327.parquet")
    results = search("유상증자 결정", topK=10)
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
        raise ImportError("sentence-transformers가 필요합니다.\n  pip install dartlab[vector]")

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
        raise ImportError("lancedb가 필요합니다.\n  pip install dartlab[vector]")

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
            records.append(
                {
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
                }
            )

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
        print(f"[vectorStore] 완료: {len(records)}개 벡터, {elapsed:.1f}초 ({speed:.0f} chunks/sec, {device})")

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


def _ensureFtsIndex(table) -> None:
    """FTS 인덱스가 없으면 생성."""
    try:
        table.search("__fts_check__", query_type="fts").limit(1).to_pandas()
    except Exception:
        try:
            table.create_fts_index("text", replace=True)
        except Exception:
            pass


def _startModelLoading() -> None:
    """백그라운드에서 모델 로딩 시작."""
    import threading

    global _model

    if _model is not None:
        return

    def _load():
        try:
            _loadModel()
        except Exception:
            pass

    threading.Thread(target=_load, daemon=True).start()


def search(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    topK: int = 10,
) -> pl.DataFrame:
    """공시 시맨틱 검색 — FTS 즉시 반환 + 벡터 보강.

    2계층 구조:
    - L1: LanceDB FTS (BM25) — 모델 불필요, 즉시 반환
    - L2: 벡터 ANN — 모델 로딩 완료 시 의미 검색으로 보강

    Parameters
    ----------
    query : 검색 쿼리 (한국어).
    corpCode : 특정 기업으로 필터 (8자리).
    stockCode : 종목코드로 필터 (6자리).
    topK : 반환 건수.

    Returns
    -------
    pl.DataFrame
        검색 결과. columns: score, rcept_no, corp_name, rcept_dt,
        report_nm, section_title, text, dartUrl
    """
    db = _openDb()

    try:
        table = db.open_table(_TABLE_NAME)
    except (ValueError, FileNotFoundError):
        return pl.DataFrame()

    _ensureFtsIndex(table)

    # 백그라운드 모델 로딩 시작 (아직 안 됐으면)
    _startModelLoading()

    # L1: FTS (즉시)
    ftsResult = _searchFts(table, query, topK=topK * 2)

    # L2: 벡터 (모델 로딩 완료 시만)
    vecResult = None
    if _model is not None:
        vecResult = _searchVector(table, query, corpCode=corpCode, stockCode=stockCode, topK=topK * 2)

    # 합산
    result = _mergeResults(ftsResult, vecResult, topK=topK)

    # 필터 적용
    if corpCode and "corp_code" in result.columns:
        result = result.filter(pl.col("corp_code") == corpCode)
    if stockCode and "stock_code" in result.columns:
        result = result.filter(pl.col("stock_code") == stockCode)

    # DART 공시 뷰어 링크
    if "rcept_no" in result.columns:
        from dartlab.core.dataLoader import DART_VIEWER

        result = result.with_columns((pl.lit(DART_VIEWER) + pl.col("rcept_no")).alias("dartUrl"))

    return result.head(topK)


def _searchFts(table, query: str, topK: int = 20) -> pl.DataFrame | None:
    """FTS (BM25) 검색."""
    try:
        results = table.search(query, query_type="fts").limit(topK).to_pandas()
        if results.empty:
            return None
        keepCols = [
            "rcept_no",
            "corp_name",
            "stock_code",
            "corp_code",
            "rcept_dt",
            "report_nm",
            "section_title",
            "text",
            "_score",
        ]
        availCols = [c for c in keepCols if c in results.columns]
        df = pl.from_pandas(results[availCols])
        if "_score" in df.columns:
            df = df.rename({"_score": "ftsScore"})
        return df
    except Exception:
        return None


def _searchVector(table, query: str, *, corpCode=None, stockCode=None, topK: int = 20) -> pl.DataFrame | None:
    """벡터 ANN 검색."""
    try:
        queryVec = _model.encode(query, normalize_embeddings=True).tolist()
        searchQuery = table.search(queryVec)

        whereClause = []
        if corpCode:
            whereClause.append(f"corp_code = '{corpCode}'")
        if stockCode:
            whereClause.append(f"stock_code = '{stockCode}'")
        if whereClause:
            searchQuery = searchQuery.where(" AND ".join(whereClause))

        results = searchQuery.limit(topK).to_pandas()
        if results.empty:
            return None

        keepCols = [
            "_distance",
            "rcept_no",
            "corp_name",
            "stock_code",
            "corp_code",
            "rcept_dt",
            "report_nm",
            "section_title",
            "text",
        ]
        availCols = [c for c in keepCols if c in results.columns]
        df = pl.from_pandas(results[availCols])
        if "_distance" in df.columns:
            df = (
                df.rename({"_distance": "distance"})
                .with_columns((1 - pl.col("distance")).alias("vecScore"))
                .drop("distance")
            )
        return df
    except Exception:
        return None


def _mergeResults(ftsResult, vecResult, topK: int = 10) -> pl.DataFrame:
    """FTS + 벡터 결과를 RRF(Reciprocal Rank Fusion)로 합산."""
    if ftsResult is None and vecResult is None:
        return pl.DataFrame()
    if ftsResult is None:
        return vecResult.with_columns(pl.col("vecScore").alias("score")).head(topK)
    if vecResult is None:
        if "ftsScore" in ftsResult.columns:
            return ftsResult.with_columns(pl.col("ftsScore").alias("score")).head(topK)
        return ftsResult.with_columns(pl.lit(1.0).alias("score")).head(topK)

    # RRF: score = 1/(k+rank_fts) + 1/(k+rank_vec)
    k = 60  # RRF 상수

    ftsRanked = ftsResult.with_row_index("ftsRank")
    vecRanked = vecResult.with_row_index("vecRank")

    # rcept_no 기준 합산
    ftsMap = {row["rcept_no"]: row["ftsRank"] for row in ftsRanked.iter_rows(named=True)}
    vecMap = {row["rcept_no"]: row["vecRank"] for row in vecRanked.iter_rows(named=True)}

    allRcepts = set(ftsMap.keys()) | set(vecMap.keys())
    rrfScores = {}
    for rcept in allRcepts:
        score = 0
        if rcept in ftsMap:
            score += 1 / (k + ftsMap[rcept])
        if rcept in vecMap:
            score += 1 / (k + vecMap[rcept])
        rrfScores[rcept] = score

    # 상위 topK
    topRcepts = sorted(rrfScores.items(), key=lambda x: x[1], reverse=True)[:topK]

    # 메타데이터 복원
    # FTS 결과 우선, 없으면 벡터 결과에서
    rows = []
    for rcept, rrfScore in topRcepts:
        ftsRows = ftsResult.filter(pl.col("rcept_no") == rcept)
        vecRows = vecResult.filter(pl.col("rcept_no") == rcept)
        source = ftsRows if ftsRows.height > 0 else vecRows
        if source.height > 0:
            row = source.row(0, named=True)
            row = {k: v for k, v in row.items() if k not in ("ftsScore", "vecScore", "ftsRank", "vecRank")}
            row["score"] = round(rrfScore, 6)
            rows.append(row)

    if not rows:
        return pl.DataFrame()

    return pl.DataFrame(rows).sort("score", descending=True)


def indexStats() -> dict:
    """벡터 인덱스 통계."""

    indexPath = _indexDir()
    try:
        db = _openDb()
        table = db.open_table(_TABLE_NAME)
        count = table.count_rows()
        totalSize = sum(f.stat().st_size for f in indexPath.rglob("*") if f.is_file())
        return {
            "table": _TABLE_NAME,
            "vectors": count,
            "sizeMb": round(totalSize / 1024 / 1024, 1),
            "path": str(indexPath),
            "device": _device or "unknown",
        }
    except (ValueError, FileNotFoundError, ImportError):
        return {"table": _TABLE_NAME, "vectors": 0, "sizeMb": 0, "path": str(indexPath)}


# ── HuggingFace 업로드/다운로드 ──


def _compressedDir() -> Path:
    """TurboQuant 압축 벡터 저장 디렉토리."""
    d = _indexDir() / "compressed"
    d.mkdir(parents=True, exist_ok=True)
    return d


def pushToHub(*, token: str | None = None, bits: int = 4) -> str:
    """LanceDB 벡터를 TurboQuant 압축 → HuggingFace 업로드.

    LanceDB(96MB) 대신 압축 벡터(8MB)만 올린다.
    사용자는 pullFromHub()로 다운로드 → 로컬 LanceDB 자동 빌드.

    Parameters
    ----------
    token : HuggingFace write token.
    bits : TurboQuant 비트 수 (기본 4).
    """
    import numpy as np
    from huggingface_hub import HfApi
    from turboquant_vectors import compress

    from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

    db = _openDb()
    table = db.open_table(_TABLE_NAME)

    # LanceDB에서 전체 데이터 추출
    allData = table.to_pandas()
    vectors = np.array(allData["vector"].tolist(), dtype=np.float32)

    print(f"[pushToHub] {len(vectors)}개 벡터 TurboQuant {bits}bit 압축 중...")
    comp = compress(vectors, bits=bits)

    # 압축 벡터 저장
    outDir = _compressedDir()
    np.savez_compressed(
        outDir / "vectors.npz",
        indices=comp.indices,
        norms=comp.norms,
        codebook=comp.codebook,
        rotation=comp.rotation,
    )

    # 메타데이터 parquet (벡터 제외)
    metaCols = [c for c in allData.columns if c != "vector"]
    metaDf = pl.from_pandas(allData[metaCols])
    metaDf.write_parquet(outDir / "meta.parquet")

    # 설정 저장
    import json

    config = {"bits": bits, "dim": vectors.shape[1], "n_vectors": len(vectors)}
    (outDir / "config.json").write_text(json.dumps(config))

    origMb = vectors.nbytes / 1024 / 1024
    compMb = sum(f.stat().st_size for f in outDir.iterdir()) / 1024 / 1024
    print(f"[pushToHub] {origMb:.1f}MB → {compMb:.1f}MB ({origMb / compMb:.0f}x 압축)")

    # HF 업로드
    hfDir = DATA_RELEASES["vectorIndex"]["dir"]
    api = HfApi(token=token)
    api.upload_folder(
        repo_id=HF_REPO,
        folder_path=str(outDir),
        path_in_repo=hfDir,
        repo_type="dataset",
    )

    url = f"https://huggingface.co/datasets/{HF_REPO}/tree/main/{hfDir}"
    print(f"[pushToHub] 업로드 완료: {url}")
    return url


def pullFromHub(*, token: str | None = None, force: bool = False) -> Path:
    """HuggingFace에서 TurboQuant 압축 벡터 다운로드 → LanceDB 자동 빌드.

    다운로드 ~8MB → decompress 0.3초 → LanceDB 빌드 0.6초 → 검색 가능.

    Parameters
    ----------
    token : HuggingFace read token (공개 데이터셋이면 불필요).
    force : True면 기존 인덱스 덮어쓰기.
    """
    import json

    import numpy as np
    from huggingface_hub import snapshot_download
    from turboquant_vectors import decompress
    from turboquant_vectors.core import CompressedVectors

    from dartlab.core.dataConfig import DATA_RELEASES, HF_REPO

    # 이미 LanceDB 인덱스 있으면 건너뜀
    if not force:
        try:
            db = _openDb()
            table = db.open_table(_TABLE_NAME)
            if table.count_rows() > 0:
                print(f"[pullFromHub] 인덱스 이미 존재 ({table.count_rows()}개 벡터)")
                return _indexDir()
        except (ValueError, FileNotFoundError):
            pass

    # HF에서 압축 벡터 다운로드
    hfDir = DATA_RELEASES["vectorIndex"]["dir"]
    print("[pullFromHub] HuggingFace에서 압축 벡터 다운로드 중...")
    snapshot_download(
        repo_id=HF_REPO,
        repo_type="dataset",
        allow_patterns=f"{hfDir}/**",
        local_dir=str(_indexDir().parent.parent.parent),  # data/ 루트
        token=token,
    )

    outDir = _compressedDir()
    vecPath = outDir / "vectors.npz"
    metaPath = outDir / "meta.parquet"
    configPath = outDir / "config.json"

    if not vecPath.exists() or not metaPath.exists():
        raise FileNotFoundError(f"압축 벡터 파일을 찾을 수 없습니다: {outDir}")

    # config 로드
    config = json.loads(configPath.read_text()) if configPath.exists() else {}
    bits = config.get("bits", 4)
    dim = config.get("dim", 768)
    nVectors = config.get("n_vectors", 0)

    # TurboQuant 복원
    print(f"[pullFromHub] {nVectors}개 벡터 복원 중 ({bits}bit)...")
    loaded = np.load(vecPath)
    comp = CompressedVectors(
        indices=loaded["indices"],
        norms=loaded["norms"],
        codebook=loaded["codebook"],
        rotation=loaded["rotation"],
        dim=dim,
        bits=bits,
        n_vectors=nVectors,
    )
    vectors = decompress(comp)

    # 메타데이터 로드
    metaDf = pl.read_parquet(metaPath)

    # LanceDB 빌드
    print("[pullFromHub] LanceDB 인덱스 빌드 중...")
    records = []
    for i, row in enumerate(metaDf.iter_rows(named=True)):
        rec = dict(row)
        rec["vector"] = vectors[i].tolist()
        records.append(rec)

    global _db
    _db = None
    db = _openDb()
    db.create_table(_TABLE_NAME, records, mode="overwrite")

    stats = indexStats()
    print(f"[pullFromHub] 완료: {stats['vectors']}개 벡터, 검색 가능")
    return _indexDir()
