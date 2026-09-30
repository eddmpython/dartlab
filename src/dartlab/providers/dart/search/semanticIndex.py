"""검색 catalog와 로컬 원문을 문단 단위로 연결하는 증분 의미 인덱스.

Parquet는 위치·본문의 정본이고 float32 sidecar는 재생성 가능한 검색 투영이다.
빠른 다국어 후보 회수 뒤 E5로 재정렬한다. 유사도는 사실·인과관계의 증명이 아니다.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import numpy as np
import polars as pl

from dartlab.core.hfRetry import retryHfCall
from dartlab.core.logger import getLogger
from dartlab.core.utils.fileDigest import fileHash
from dartlab.providers.dart.search.fieldIndex import _activeIndexDir, _contentIndexDir

_MODEL = "minishlab/potion-multilingual-128M"
_REVISION = "73908c3438cf03b6a01bcb9611d62b23d0726f08"
_RERANK_MODEL = "intfloat/multilingual-e5-small"
_RERANK_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
_VERSION = 1
_DIM = 256
_CHARS = 900
_OVERLAP = 120
_SOURCE_NAMES = {"dartPanel": "panel", "edgarPanel": "edgar-panel", "newsPublic": "news"}
_log = getLogger(__name__)


def _indexDir() -> Path:
    return _contentIndexDir() / "semantic"


def _modelDir(name: str) -> Path:
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "models" / name.rsplit("/", 1)[-1]


def _requireModels() -> None:
    try:
        import fastembed  # noqa: F401
        import model2vec  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "의미 검색 준비: pip install 'dartlab[semantic]' 후 dartlab search --build-semantic"
        ) from exc


def prepareSemanticModels() -> None:
    """명시적인 빌드에서 고정 revision의 모델을 준비한다.

    Args:
        없음. 데이터 루트 아래 models 캐시를 사용한다.
    Returns:
        None.
    Raises:
        RuntimeError: semantic 선택 의존성이 없을 때.
        OSError: 모델 다운로드나 저장 실패.
    Example:
        >>> # prepareSemanticModels()
    """
    _requireModels()
    from huggingface_hub import snapshot_download

    models = (
        (_MODEL, _REVISION, ["config.json", "tokenizer.json", "model.safetensors"]),
        (
            _RERANK_MODEL,
            _RERANK_REVISION,
            [
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "onnx/model_qint8_avx512_vnni.onnx",
            ],
        ),
    )
    for name, revision, files in models:
        retryHfCall(snapshot_download, name, revision=revision, allow_patterns=files, local_dir=str(_modelDir(name)))


@lru_cache(maxsize=1)
def _encoder():
    _requireModels()
    from model2vec import StaticModel

    path = _modelDir(_MODEL)
    if not (path / "model.safetensors").is_file():
        raise RuntimeError("의미 검색 모델이 없습니다. dartlab search --build-semantic 으로 준비하세요.")
    return StaticModel.from_pretrained(path)


@lru_cache(maxsize=1)
def _reranker():
    _requireModels()
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType

    path = _modelDir(_RERANK_MODEL)
    if not (path / "onnx/model_qint8_avx512_vnni.onnx").is_file():
        raise RuntimeError("의미 검색 재정렬 모델이 없습니다. dartlab search --build-semantic 으로 준비하세요.")
    if _RERANK_MODEL not in {row["model"] for row in TextEmbedding.list_supported_models()}:
        TextEmbedding.add_custom_model(
            _RERANK_MODEL,
            PoolingType.MEAN,
            True,
            ModelSource(hf=_RERANK_MODEL),
            384,
            model_file="onnx/model_qint8_avx512_vnni.onnx",
        )
    return TextEmbedding(_RERANK_MODEL, specific_model_path=str(path), threads=4)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest(indexDir: Path) -> dict:
    path = indexDir / "manifest.json"
    if not path.exists():
        return {}
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("version") != _VERSION or result.get("modelRevision") != _REVISION:
        raise RuntimeError("의미 인덱스 버전이 다릅니다. dartlab search --build-semantic 으로 갱신하세요.")
    return result


def semanticIndexInfo(*, indexDir: Path | None = None) -> dict:
    """모델 추론 없이 인덱스 범위를 반환한다.

    Args:
        indexDir: 인덱스 경로. None이면 기본 데이터 루트.
    Returns:
        가용 여부, 문단 수, 모델 revision, 빌드 시점과 coverage.
    Raises:
        RuntimeError: 저장된 인덱스 버전이 호환되지 않을 때.
    Example:
        >>> # semanticIndexInfo()["available"]
    """
    result = _manifest(indexDir or _indexDir())
    return {"available": bool(result), **{key: value for key, value in result.items() if key != "shards"}}


def _sources() -> list[tuple[Path, str]]:
    from dartlab.core.dataLoader import _getDataRoot

    root = _getDataRoot()
    catalog = _activeIndexDir() / "catalog_snapshot.parquet"
    sources = [(catalog, "catalog")] if catalog.exists() else []
    for provider in ("dart", "edgar"):
        sources.extend((path, provider + "Panel") for path in sorted((root / provider / "panel").glob("*.parquet")))
    return sources


def _sourceRows(path: Path, source: str) -> Iterator[dict]:
    """기존 catalog identity를 보존하고 로컬 panel의 뒤쪽 block까지 투영한다."""
    import pyarrow.parquet as pq

    from dartlab.providers.dart.search.sourceCatalog import _sourceDataAsOfFromPanelRow, _stripPanelText

    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=1024):
        for row in batch.to_pylist():
            if source == "catalog":
                if not row.get("deleted") and row.get("searchText"):
                    yield {**row, "coverage": "catalogExcerpt", "blockOrder": -1}
                continue
            rcept = str(row.get("rceptNo") or "")
            if not rcept:
                continue
            text = _stripPanelText(str(row.get("contentRaw") or ""), limit=None)
            if not text:
                continue
            code = path.stem
            block = int(row.get("blockOrder") or 0)
            date = _sourceDataAsOfFromPanelRow(row, source=source, rceptNo=rcept)
            prefix = "edgar" if source == "edgarPanel" else "dart"
            yield {
                "source": source,
                "sourceRef": f"{prefix}:panel:{rcept}#section={block}",
                "rceptNo": rcept,
                "sectionOrder": block,
                "blockOrder": block,
                "stockCode": code if prefix == "dart" else "",
                "ticker": code if prefix == "edgar" else "",
                "corpCode": "",
                "companyName": str(row.get("corp") or code),
                "title": str(row.get("sectionPath") or row.get("sectionLeaf") or ""),
                "reportName": str(row.get("period") or ""),
                "date": date,
                "sourceDataAsOf": date,
                "searchText": text,
                "coverage": "localFullText",
                "url": "",
            }


def _passages(path: Path, source: str) -> Iterator[dict]:
    for row in _sourceRows(path, source):
        text = str(row["searchText"])
        title = str(row.get("title") or "")
        for start in range(0, len(text), _CHARS - _OVERLAP):
            passage = text[start : start + _CHARS]
            if not passage.strip():
                continue
            textHash = _digest(title + "\n" + passage)
            ref = str(row["sourceRef"])
            yield {
                "passageId": ref + "@" + _digest(f"{textHash}:{start}:{row.get('coverage')}")[:20],
                "sourceRef": ref,
                "source": _SOURCE_NAMES.get(str(row["source"]), str(row["source"])),
                "rcept_no": str(row.get("rceptNo") or ""),
                "section_order": int(row.get("sectionOrder") or 0),
                "corp_code": str(row.get("corpCode") or ""),
                "stock_code": str(row.get("stockCode") or row.get("ticker") or ""),
                "corp_name": str(row.get("companyName") or ""),
                "rcept_dt": str(row.get("date") or ""),
                "report_nm": str(row.get("reportName") or ""),
                "section_title": title,
                "text": passage,
                "evidenceText": passage,
                "sourceDataAsOf": str(row.get("sourceDataAsOf") or ""),
                "url": str(row.get("url") or ""),
                "textHash": textHash,
                "charStart": start,
                "charEnd": start + len(passage),
                "coverage": row["coverage"],
                "blockOrder": int(row["blockOrder"]),
            }
            if start + _CHARS >= len(text):
                break


def buildSemanticIndex(*, indexDir: Path | None = None, sources: list[tuple[Path, str]] | None = None) -> dict:
    """수집된 catalog 및 로컬 원문 전체를 증분 색인한다. 원격 원문 수집은 하지 않는다.

    변경 없는 파일은 재사용하고 수정 파일에서도 같은 본문 벡터는 재사용한다.
    모든 shard가 성공한 뒤 manifest를 교체하므로 실패한 빌드는 기존 검색을 보존한다.

    Args:
        indexDir: 인덱스 저장 경로. None이면 기본 데이터 루트.
        sources: (Parquet 경로, source 종류) 쌍. None이면 기존 catalog와 로컬 원문.
    Returns:
        인덱스 메타데이터와 새로 인코딩·재사용한 문단 수.
    Raises:
        RuntimeError: 입력 또는 모델이 준비되지 않았을 때.
        filelock.Timeout: 다른 빌드가 실행 중일 때.
        OSError: 파일 저장 실패. 이전 manifest는 유지한다.
    Example:
        >>> # buildSemanticIndex()
    """
    from filelock import FileLock

    target = indexDir or _indexDir()
    target.mkdir(parents=True, exist_ok=True)
    with FileLock(str(target / "build.lock"), timeout=0):
        inputs = _sources() if sources is None else sources
        if not inputs:
            raise RuntimeError("검색 catalog와 로컬 원문이 없습니다. 검색 인덱스 또는 회사 데이터를 먼저 준비하세요.")
        previous = _manifest(target)
        oldShards = {row["input"]: row for row in previous.get("shards", [])}
        shards, created = [], []
        encoded = reused = 0
        try:
            for path, source in inputs:
                identity = f"{source}:{path.resolve()}"
                fingerprint = fileHash(path)
                old = oldShards.get(identity)
                if old and old["fingerprint"] == fingerprint:
                    shards.append(old)
                    reused += old["rows"]
                    continue
                _log.info("의미 인덱스: %s (%s)", path.name, source)
                shard, files, fresh, kept = _buildShard(target, path, source, old)
                created.extend(files)
                shard.update(input=identity, fingerprint=fingerprint)
                shards.append(shard)
                encoded += fresh
                reused += kept
            manifest = {
                "version": _VERSION,
                "model": _MODEL,
                "modelRevision": _REVISION,
                "rerankModel": _RERANK_MODEL,
                "rerankRevision": _RERANK_REVISION,
                "builtAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "dimensions": _DIM,
                "passages": sum(row["rows"] for row in shards),
                "sourceFiles": len(shards),
                "coverage": "published catalog excerpts plus complete locally available panel blocks",
                "shards": shards,
            }
            temp = target / "manifest.json.tmp"
            temp.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            temp.replace(target / "manifest.json")
        except BaseException:
            for path in created:
                path.unlink(missing_ok=True)
            raise
        _retireShards(target, shards)
        return {**semanticIndexInfo(indexDir=target), "encoded": encoded, "reused": reused}


def _retireShards(target: Path, shards: list[dict]) -> None:
    from filelock import FileLock, Timeout

    try:
        with FileLock(str(target / "read.lock"), timeout=0):
            active = {row[key] for row in shards for key in ("meta", "vectors")}
            for path in target.iterdir():
                if path.suffix not in {".parquet", ".f32"} or len(path.stem) != 32:
                    continue
                if any(char not in "0123456789abcdef" for char in path.stem) or path.name in active:
                    continue
                try:
                    path.unlink(missing_ok=True)
                except PermissionError:
                    pass  # 열린 Windows reader의 파일은 다음 빌드에서 정리한다.
    except Timeout:
        pass  # 읽는 동안 publication은 허용하고 오래된 shard 회수만 다음 빌드로 미룬다.


def _buildShard(target: Path, path: Path, source: str, old: dict | None) -> tuple[dict, list[Path], int, int]:
    import pyarrow.parquet as pq

    name = uuid.uuid4().hex
    metaPath, vectorPath = target / f"{name}.parquet", target / f"{name}.f32"
    oldHashes, oldVectors = {}, None
    if old and old["rows"]:
        hashes = pl.read_parquet(target / old["meta"], columns=["textHash"])["textHash"]
        oldHashes = {value: i for i, value in enumerate(hashes)}
        oldVectors = np.memmap(target / old["vectors"], dtype=np.float32, mode="r", shape=(old["rows"], _DIM))
    writer = None
    count = encoded = reused = 0
    batch = []
    try:
        with vectorPath.open("wb") as output:

            def _flush():
                nonlocal writer, count, encoded, reused
                values = np.empty((len(batch), _DIM), dtype=np.float32)
                missing = []
                for i, row in enumerate(batch):
                    previous = oldHashes.get(row["textHash"])
                    if previous is None:
                        missing.append(i)
                    else:
                        values[i] = oldVectors[previous]
                        reused += 1
                if missing:
                    texts = [batch[i]["section_title"] + "\n" + batch[i]["text"] for i in missing]
                    values[missing] = _encoder().encode(texts, use_multiprocessing=False)
                    encoded += len(missing)
                if not np.isfinite(values).all():
                    raise ValueError("의미 벡터에 유효하지 않은 값이 있습니다")
                frame = pl.DataFrame(batch).with_row_index("vectorRow", offset=count)
                table = frame.to_arrow()
                if writer is None:
                    writer = pq.ParquetWriter(metaPath, table.schema, compression="zstd")
                writer.write_table(table)
                output.write(values.tobytes())
                count += len(batch)
                batch.clear()

            for row in _passages(path, source):
                batch.append(row)
                if len(batch) == 1024:
                    _flush()
            if batch:
                _flush()
        if writer:
            writer.close()
            writer = None
    except BaseException:
        if writer:
            writer.close()
        metaPath.unlink(missing_ok=True)
        vectorPath.unlink(missing_ok=True)
        raise
    finally:
        if oldVectors is not None:
            oldVectors._mmap.close()
    return {"meta": metaPath.name, "vectors": vectorPath.name, "rows": count}, [metaPath, vectorPath], encoded, reused


@lru_cache(maxsize=4096)
def _rerankVector(text: str) -> np.ndarray:
    return np.asarray(next(_reranker().embed(["passage: " + text])), dtype=np.float32)


def searchSemantic(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    sourceKind: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 10,
    relatedTo: str | None = None,
    excludeStockCode: str | None = None,
    indexDir: Path | None = None,
) -> pl.DataFrame:
    """회사·출처·기간을 먼저 제한한 뒤 문단을 회수한다.

    Args:
        query: 의미 검색어. relatedTo가 있으면 빈 문자열 허용.
        corpCode: DART 회사 고유번호 필터.
        stockCode: 종목코드·ticker 필터. corpCode보다 우선한다.
        sourceKind: filing 또는 news. None이면 전체.
        start: 접수일 시작 YYYYMMDD.
        end: 접수일 종료 YYYYMMDD.
        limit: 결과 수, 1~100.
        relatedTo: 이전 검색의 passageId. 같은 sourceRef는 제외한다.
        excludeStockCode: 다른 회사 탐색에서 제외할 종목코드 또는 ticker.
        indexDir: 기본 인덱스 위치를 대신할 경로.
    Returns:
        원문 문단, 출처, 위치, 유사도를 포함하는 DataFrame.
    Raises:
        ValueError: 잘못된 날짜·범위·검색어·문단 ID.
        RuntimeError: 모델·인덱스 미준비 또는 버전 불일치.
    Example:
        >>> # searchSemantic("전력 설비 확대", limit=5)
    """
    from filelock import FileLock

    target = indexDir or _indexDir()
    if not target.exists():
        raise RuntimeError("의미 인덱스가 없습니다. dartlab search --build-semantic 으로 준비하세요.")
    with FileLock(str(target / "read.lock"), timeout=60):
        return _searchSemantic(
            query,
            corpCode=corpCode,
            stockCode=stockCode,
            sourceKind=sourceKind,
            start=start,
            end=end,
            limit=limit,
            relatedTo=relatedTo,
            excludeStockCode=excludeStockCode,
            indexDir=target,
        )


def _searchSemantic(
    query, *, corpCode, stockCode, sourceKind, start, end, limit, relatedTo, excludeStockCode, indexDir
):
    from dartlab.providers.dart.search.fieldIndex import _resolveResultUrl
    from dartlab.providers.dart.search.sourceIntent import NEWS_SOURCES

    target = indexDir or _indexDir()
    if not 1 <= limit <= 100:
        raise ValueError("의미 검색 limit은 1~100 범위입니다")
    from datetime import datetime

    for date in (start, end):
        if date is not None:
            if len(date) != 8 or not date.isdigit():
                raise ValueError("의미 검색 날짜는 YYYYMMDD 형식입니다")
            datetime.strptime(date, "%Y%m%d")
    if start and end and start > end:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다")
    manifest = _manifest(target)
    if not manifest:
        raise RuntimeError("의미 인덱스가 없습니다. dartlab search --build-semantic 으로 준비하세요.")
    if corpCode and not stockCode:
        stockCode = _catalogStockCode(target, manifest["shards"], corpCode)
    if not query.strip() and not relatedTo:
        raise ValueError("검색어 또는 relatedTo passageId가 필요합니다")
    seed = None
    if relatedTo:
        seed = _relatedSeed(target, manifest["shards"], relatedTo)
        if not sourceKind:
            sourceKind = "news" if seed["source"] in NEWS_SOURCES else "filing"
        query = query.strip() or seed["text"]
    vector = np.asarray(_encoder().encode([query])[0], dtype=np.float32)
    poolSize = max(60, min(200, limit * 6))
    predicate = _candidateFilter(corpCode, stockCode, sourceKind, start, end, excludeStockCode, seed)
    candidates = _vectorCandidates(target, manifest["shards"], vector, predicate, poolSize)
    if not candidates:
        return pl.DataFrame()
    queryVector = np.asarray(next(_reranker().embed(["query: " + query])), dtype=np.float32)
    for row in candidates:
        row["score"] = float(_rerankVector(row["section_title"] + "\n" + row["text"]) @ queryVector)
        row["retrievalMethod"] = "semantic"
        row["relationType"] = "semanticSimilarity"
        row["relatedTo"] = relatedTo or ""
        row["indexedAt"] = manifest["builtAt"]
    candidates.sort(key=lambda row: row["score"], reverse=True)
    from dartlab.core.listingResolver import getListingResolver

    resolver = getListingResolver()
    for row in candidates[:limit]:
        if resolver and row["stock_code"] and row["corp_name"] == row["stock_code"]:
            row["corp_name"] = resolver.codeToName(row["stock_code"]) or row["corp_name"]
    return _resolveResultUrl(pl.DataFrame(candidates[:limit]).drop("vectorRow", "textHash"))


def _relatedSeed(target: Path, shards: list[dict], relatedTo: str) -> dict:
    """후속 검색의 기준 문단을 현재 manifest에서 정확한 ID로 읽는다."""
    for shard in shards:
        if not shard["rows"]:
            continue
        rows = pl.scan_parquet(target / shard["meta"]).filter(pl.col("passageId") == relatedTo).collect()
        if rows.height:
            return rows.row(0, named=True)
    raise ValueError("relatedTo 문단이 현재 인덱스에 없습니다. 검색 결과의 passageId를 사용하세요.")


def _catalogStockCode(target: Path, shards: list[dict], corpCode: str) -> str | None:
    """catalog의 회사 고유번호를 로컬 원문의 종목코드와 연결한다."""
    for shard in shards:
        if not shard["input"].startswith("catalog:") or not shard["rows"]:
            continue
        codes = (
            pl.scan_parquet(target / shard["meta"])
            .filter((pl.col("corp_code") == corpCode) & (pl.col("stock_code") != ""))
            .select("stock_code")
            .unique()
            .head(2)
            .collect()
        )
        if codes.height == 1:
            return codes["stock_code"][0]
    return None


def _candidateFilter(corpCode, stockCode, sourceKind, start, end, excludeStockCode, seed) -> pl.Expr:
    from dartlab.providers.dart.search.sourceIntent import FILING_SOURCES, NEWS_SOURCES

    predicate = pl.lit(True)
    for column, value in (("stock_code", stockCode),) if stockCode else (("corp_code", corpCode),):
        if value:
            predicate &= pl.col(column) == value
    if sourceKind:
        sources = NEWS_SOURCES if sourceKind == "news" else FILING_SOURCES
        predicate &= pl.col("source").is_in(sources)
    if excludeStockCode:
        predicate &= pl.col("stock_code") != excludeStockCode
    if start:
        predicate &= pl.col("rcept_dt") >= start
    if end:
        predicate &= pl.col("rcept_dt") <= end
    if seed:
        predicate &= pl.col("sourceRef") != seed["sourceRef"]
    return predicate


def _vectorCandidates(target: Path, shards: list[dict], vector: np.ndarray, predicate: pl.Expr, poolSize: int):
    """조건을 만족하는 행만 bounded batch로 점수화하고 중복 본문을 합친다."""
    candidates = []
    for shard in shards:
        if not shard["rows"]:
            continue
        lazy = pl.scan_parquet(target / shard["meta"])
        ids = lazy.filter(predicate).select("vectorRow").collect()["vectorRow"].to_numpy()
        if not len(ids):
            continue
        matrix = np.memmap(target / shard["vectors"], mode="r", dtype=np.float32, shape=(shard["rows"], _DIM))
        best = []
        try:
            for offset in range(0, len(ids), 8192):
                subset = ids[offset : offset + 8192]
                scores = matrix[subset] @ vector
                order = np.argsort(scores)[-poolSize:]
                best.extend((float(scores[i]), int(subset[i])) for i in order)
                best = sorted(best, reverse=True)[:poolSize]
        finally:
            matrix._mmap.close()
        scoresByRow = {i: score for score, i in best}
        selected = lazy.filter(pl.col("vectorRow").is_in(list(scoresByRow))).collect()
        candidates.extend(
            {**row, "semanticScore": scoresByRow[row["vectorRow"]]} for row in selected.iter_rows(named=True)
        )
        unique = {}
        for row in sorted(candidates, key=lambda row: (row["semanticScore"], row["rcept_dt"]), reverse=True):
            unique.setdefault(row["textHash"], row)
        candidates = list(unique.values())[:poolSize]
    return candidates


def iterSemantic(query: str, **kwargs) -> Iterator[dict]:
    """전역 재정렬이 끝난 의미 검색 결과를 행 단위로 제공한다.

    Args:
        query: 검색어.
        kwargs: searchSemantic의 회사·기간·문단·limit 필터.
    Returns:
        검색 결과 행 iterator. 추론 자체를 streaming하지는 않는다.
    Raises:
        ValueError: searchSemantic의 입력 검증 실패.
        RuntimeError: 모델 또는 인덱스 미준비.
    Example:
        >>> # list(iterSemantic("전력 설비", limit=3))
    """
    yield from searchSemantic(query, **kwargs).iter_rows(named=True)
