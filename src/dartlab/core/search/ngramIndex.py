"""Ngram+Synonym 검색 엔진 — stem ID 역인덱스, CSR 구조, bincount 검색.

agiPath의 posting 방식 적용:
- 텍스트 → stem(ngram) ID 정수 → CSR 역인덱스
- 검색: numpy bincount (vectorized, 400만 문서에서 140ms)
- 저장: numpy int32 CSR (stemIndex.npz) — JSON 대비 8.5x 축소

allFilings(수시공시) + docs(사업보고서) 통합 인덱스 지원.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl

from dartlab import config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES

# ── 동의어 테이블 ──

# content[:50] 인덱싱으로 동의어 하드코딩 불필요.
# report_nm + section_title + content 앞 50자가 DART 공식 + 비공식 어휘를 모두 포함.
_CONTENT_INDEX_CHARS = 50


def _tokenize(text: str) -> list[str]:
    """bigram + trigram 추출 (중복 제거)."""
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i: i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i: i + 3] for i in range(len(text) - 2))
    return list(tokens)


# ── 경로 ──


def _stemIndexDir() -> Path:
    d = Path(_cfg.dataDir) / DATA_RELEASES["stemIndex"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


# 캐시
_cachedIndex: dict | None = None
_cachedMeta: pl.DataFrame | None = None


# ── 빌드 ──


def buildNgramIndex(
    parquetPaths: list[str | Path] | None = None,
    *,
    includeDocs: bool = False,
    docsBatchSize: int = 100,
    showProgress: bool = True,
) -> int:
    """통합 stem ID 역인덱스 구축.

    allFilings parquet + (선택) docs parquet → stemIndex.npz + stemDict.json + meta.parquet

    Parameters
    ----------
    parquetPaths : allFilings parquet 경로. None이면 자동 탐색.
    includeDocs : True면 docs(사업보고서)도 포함.
    docsBatchSize : docs 배치 크기 (OOM 방지).
    showProgress : 진행 표시.

    Returns
    -------
    int
        인덱싱된 문서 수.
    """
    import time

    global _cachedIndex, _cachedMeta
    t0 = time.time()

    # ── Phase 1: allFilings 로드 ──
    if parquetPaths is None:
        from dartlab.providers.dart.openapi.allFilingsCollector import _META_SUFFIX, _allFilingsDir
        outDir = _allFilingsDir()
        parquetPaths = sorted(str(f) for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)

    stemToId: dict[str, int] = {}
    nextId = 0
    invertedIndex: dict[int, list[int]] = defaultdict(list)
    allMeta: list[dict] = []
    globalDocId = 0
    existingKeys: set[tuple[str, int]] = set()  # (rcept_no, section_order) 중복 방지

    # allFilings
    if parquetPaths:
        for p in parquetPaths:
            try:
                df = pl.read_parquet(p).filter(pl.col("section_content").is_not_null())
            except Exception:
                continue

            for row in df.iter_rows(named=True):
                key = (row["rcept_no"], row.get("section_order", 0))
                existingKeys.add(key)

                contentHead = (row.get("section_content", "") or "")[:_CONTENT_INDEX_CHARS]
                text = f"{row['report_nm']} {row.get('section_title', '') or ''} {contentHead}"
                tokens = _tokenize(text)
                seenStems: set[int] = set()
                for token in tokens:
                    if token not in stemToId:
                        stemToId[token] = nextId
                        nextId += 1
                    stemId = stemToId[token]
                    if stemId not in seenStems:
                        seenStems.add(stemId)
                        invertedIndex[stemId].append(globalDocId)

                allMeta.append({
                    "rcept_no": row["rcept_no"],
                    "corp_code": row.get("corp_code", ""),
                    "corp_name": row.get("corp_name", ""),
                    "stock_code": row.get("stock_code", ""),
                    "rcept_dt": row.get("rcept_dt", ""),
                    "report_nm": row.get("report_nm", ""),
                    "section_title": row.get("section_title", "") or "",
                    "source": "allFilings",
                    "text": (row.get("section_content", "") or "")[:2000],
                })
                globalDocId += 1

        if showProgress:
            print(f"[stemIndex] allFilings: {globalDocId:,}문서, {nextId:,} stems")

    # ── Phase 2: docs 로드 (배치) ──
    if includeDocs:
        docsDir = Path(_cfg.dataDir) / DATA_RELEASES["docs"]["dir"]
        docsFiles = sorted(docsDir.glob("*.parquet"))

        if showProgress:
            print(f"[stemIndex] docs: {len(docsFiles)}종목 처리 시작")

        for batchStart in range(0, len(docsFiles), docsBatchSize):
            batchFiles = docsFiles[batchStart: batchStart + docsBatchSize]
            for f in batchFiles:
                try:
                    df = pl.read_parquet(f, columns=[
                        "rcept_no", "corp_code", "corp_name", "stock_code",
                        "report_type", "section_title", "section_order",
                        "section_content",
                    ])
                except Exception:
                    continue

                for row in df.iter_rows(named=True):
                    key = (row["rcept_no"], row.get("section_order", 0))
                    if key in existingKeys:
                        continue
                    existingKeys.add(key)

                    reportNm = row.get("report_type", "")
                    sectionTitle = row.get("section_title", "") or ""
                    contentHead = (row.get("section_content", "") or "")[:_CONTENT_INDEX_CHARS]
                    text = f"{reportNm} {sectionTitle} {contentHead}"

                    tokens = _tokenize(text)
                    seenStems: set[int] = set()
                    for token in tokens:
                        if token not in stemToId:
                            stemToId[token] = nextId
                            nextId += 1
                        stemId = stemToId[token]
                        if stemId not in seenStems:
                            seenStems.add(stemId)
                            invertedIndex[stemId].append(globalDocId)

                    allMeta.append({
                        "rcept_no": row["rcept_no"],
                        "corp_code": row.get("corp_code", ""),
                        "corp_name": row.get("corp_name", ""),
                        "stock_code": row.get("stock_code", ""),
                        "rcept_dt": "",
                        "report_nm": reportNm,
                        "section_title": sectionTitle,
                        "source": "docs",
                        "text": "",
                    })
                    globalDocId += 1

            if showProgress and (batchStart + docsBatchSize) % (docsBatchSize * 5) == 0:
                elapsed = time.time() - t0
                print(f"  [{batchStart + len(batchFiles)}/{len(docsFiles)}] "
                      f"{globalDocId:,}문서, {nextId:,} stems, {elapsed:.0f}초")

    if globalDocId == 0:
        return 0

    # ── CSR 저장 ──
    outDir = _stemIndexDir()

    offsets = [0]
    flatDocIds = []
    for stemId in range(nextId):
        docList = invertedIndex.get(stemId, [])
        flatDocIds.extend(docList)
        offsets.append(len(flatDocIds))

    np.savez_compressed(
        outDir / "stemIndex.npz",
        offsets=np.array(offsets, dtype=np.int32),
        docIds=np.array(flatDocIds, dtype=np.int32),
    )

    (outDir / "stemDict.json").write_text(
        json.dumps(stemToId, ensure_ascii=False), encoding="utf-8"
    )

    metaDf = pl.DataFrame(allMeta)
    metaDf.write_parquet(outDir / "meta.parquet")

    # 캐시 갱신
    _cachedIndex = {
        "stemToId": stemToId,
        "offsets": np.array(offsets, dtype=np.int32),
        "docIds": np.array(flatDocIds, dtype=np.int32),
    }
    _cachedMeta = metaDf

    elapsed = time.time() - t0
    npzMb = (outDir / "stemIndex.npz").stat().st_size / 1024 / 1024
    if showProgress:
        print(f"[stemIndex] 완료: {globalDocId:,}문서, {nextId:,} stems, "
              f"{npzMb:.1f}MB, {elapsed:.0f}초")

    return globalDocId


# ── 검색 ──


def _loadIndex() -> tuple[dict, pl.DataFrame]:
    global _cachedIndex, _cachedMeta

    if _cachedIndex is not None and _cachedMeta is not None:
        return _cachedIndex, _cachedMeta

    outDir = _stemIndexDir()
    npzPath = outDir / "stemIndex.npz"
    dictPath = outDir / "stemDict.json"
    metaPath = outDir / "meta.parquet"

    if not npzPath.exists() or not metaPath.exists():
        return {}, pl.DataFrame()

    loaded = np.load(npzPath)
    stemToId = json.loads(dictPath.read_text(encoding="utf-8"))

    _cachedIndex = {
        "stemToId": stemToId,
        "offsets": loaded["offsets"],
        "docIds": loaded["docIds"],
    }
    _cachedMeta = pl.read_parquet(metaPath)

    return _cachedIndex, _cachedMeta


def searchNgram(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    topK: int = 10,
) -> pl.DataFrame:
    """stem ID 역인덱스 검색 — numpy bincount vectorized.

    400만 문서에서 140ms. 모델 불필요, cold start 0ms.
    """
    index, meta = _loadIndex()
    if not index or meta.height == 0:
        return pl.DataFrame()

    stemToId = index["stemToId"]
    offsets = index["offsets"]
    docIds = index["docIds"]
    nDocs = meta.height

    tokens = _tokenize(query)
    if not tokens:
        return pl.DataFrame()

    queryStems = [stemToId[t] for t in tokens if t in stemToId]
    if not queryStems:
        return pl.DataFrame()

    # numpy bincount — vectorized 집계
    allMatched = []
    for stemId in queryStems:
        start = offsets[stemId]
        end = offsets[stemId + 1]
        if end > start:
            allMatched.append(docIds[start:end])

    if not allMatched:
        return pl.DataFrame()

    flat = np.concatenate(allMatched)
    counts = np.bincount(flat, minlength=nDocs)

    nTop = min(topK * 3, nDocs)
    topIndices = np.argpartition(counts, -nTop)[-nTop:]
    topIndices = topIndices[np.argsort(counts[topIndices])[::-1]]

    from dartlab.core.dataLoader import DART_VIEWER

    rows = []
    seen: set[str] = set()
    for docId in topIndices:
        matchCount = int(counts[docId])
        if matchCount == 0:
            break
        if docId >= nDocs:
            continue
        row = meta.row(int(docId), named=True)
        rcept = row["rcept_no"]
        if rcept in seen:
            continue
        if corpCode and row.get("corp_code", "") != corpCode:
            continue
        if stockCode and row.get("stock_code", "") != stockCode:
            continue

        seen.add(rcept)
        rows.append({
            "score": round(matchCount / len(queryStems), 4),
            "rcept_no": rcept,
            "corp_name": row.get("corp_name", ""),
            "stock_code": row.get("stock_code", ""),
            "rcept_dt": row.get("rcept_dt", ""),
            "report_nm": row.get("report_nm", ""),
            "section_title": row.get("section_title", ""),
            "text": row.get("text", ""),
            "dartUrl": f"{DART_VIEWER}{rcept}",
        })

        if len(rows) >= topK:
            break

    if not rows:
        return pl.DataFrame()

    return pl.DataFrame(rows)


# ── 통계 ──


def ngramStats() -> dict:
    outDir = _stemIndexDir()
    npzPath = outDir / "stemIndex.npz"
    dictPath = outDir / "stemDict.json"
    metaPath = outDir / "meta.parquet"

    sizeMb = 0
    stems = 0
    documents = 0

    if npzPath.exists():
        sizeMb += npzPath.stat().st_size / 1024 / 1024
        loaded = np.load(npzPath)
        stems = len(loaded["offsets"]) - 1
    if dictPath.exists():
        sizeMb += dictPath.stat().st_size / 1024 / 1024
    if metaPath.exists():
        sizeMb += metaPath.stat().st_size / 1024 / 1024
        documents = pl.scan_parquet(metaPath).select(pl.len()).collect().item()

    return {
        "stems": stems,
        "documents": documents,
        "sizeMb": round(sizeMb, 1),
        "path": str(outDir),
    }


# ── HF push/pull ──


def pushStemIndex(*, token: str | None = None) -> str:
    """stemIndex를 HuggingFace에 업로드."""
    from huggingface_hub import HfApi
    from dartlab.core.dataConfig import HF_REPO

    outDir = _stemIndexDir()
    hfDir = DATA_RELEASES["stemIndex"]["dir"]

    api = HfApi(token=token)
    api.upload_folder(
        repo_id=HF_REPO,
        folder_path=str(outDir),
        path_in_repo=hfDir,
        repo_type="dataset",
    )

    url = f"https://huggingface.co/datasets/{HF_REPO}/tree/main/{hfDir}"
    print(f"[stemIndex] HF 업로드 완료: {url}")
    return url


def pullStemIndex(*, token: str | None = None, force: bool = False) -> Path:
    """HuggingFace에서 stemIndex 다운로드 → 즉시 검색 가능."""
    from huggingface_hub import snapshot_download
    from dartlab.core.dataConfig import HF_REPO

    outDir = _stemIndexDir()
    hfDir = DATA_RELEASES["stemIndex"]["dir"]

    if not force:
        npzPath = outDir / "stemIndex.npz"
        if npzPath.exists():
            stats = ngramStats()
            if stats["documents"] > 0:
                print(f"[stemIndex] 인덱스 이미 존재 ({stats['documents']:,}문서)")
                return outDir

    print("[stemIndex] HuggingFace에서 다운로드 중...")
    snapshot_download(
        repo_id=HF_REPO,
        repo_type="dataset",
        allow_patterns=f"{hfDir}/**",
        local_dir=str(outDir.parent.parent.parent),
        token=token,
    )

    global _cachedIndex, _cachedMeta
    _cachedIndex = None
    _cachedMeta = None

    stats = ngramStats()
    print(f"[stemIndex] 완료: {stats['documents']:,}문서, {stats['sizeMb']}MB")
    return outDir
