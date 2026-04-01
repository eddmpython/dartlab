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

# report_nm + section_title만 인덱싱 — content 인덱싱은 노이즈 유발 (실험 014).
_CONTENT_INDEX_CHARS = 0

# L0 유형 라우팅 — 114개 정규화 유형에서만 적용하므로 노이즈 없음 (실험 015).
_L0_INFORMAL = {
    "사장": "대표이사 대표이사변경",
    "경영진": "대표이사 대표이사변경",
    "대표": "대표이사",
    "빚": "사채",
    "돈을 빌렸다": "사채 차입 자금",
    "빌렸다": "사채 차입",
    "망하다": "상장폐지 관리종목",
    "망할": "상장폐지",
    "파산": "회생 관리",
    "팔았다": "처분 양도 매도",
    "만들었다": "설립 출자",
    "바뀌었다": "변경 선임 해임 대표이사변경",
    "M&A": "합병 인수",
    "IPO": "상장 공모",
    "ESG": "지배구조",
    "CB": "전환사채",
    "CEO": "대표이사 대표이사변경",
    "배당금": "배당 현금 현물배당결정",
    "주가": "주가연계",
    "공장": "사업장 시설",
    "횡령": "제재 부정 소송",
    "상장폐지": "상장폐지 관리종목 기타시장안내",
    "워크아웃": "채권은행 관리절차",
    # 줄임말
    "유증": "유상증자 유상증자결정",
    "사보": "사업보고서",
    "대변": "대표이사변경",
    "주담대": "담보 차입",
    # 영어 약어
    "BW": "신주인수권 신주인수권부사채",
    "IR": "기업설명회",
    "SPAC": "기업인수목적 합병",
    # 비공식 표현
    "부도": "관리종목 미지급 채권은행",
    "사기": "횡령 제재 소송 부정",
}

# 유형 인덱스 캐시
_typeIndex: dict | None = None
_typeToDocIds: dict | None = None


def _tokenize(text: str) -> list[str]:
    """bigram + trigram 추출 (중복 제거)."""
    text = text.strip()
    tokens = set()
    if len(text) >= 2:
        tokens.update(text[i : i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        tokens.update(text[i : i + 3] for i in range(len(text) - 2))
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

                allMeta.append(
                    {
                        "rcept_no": row["rcept_no"],
                        "corp_code": row.get("corp_code", ""),
                        "corp_name": row.get("corp_name", ""),
                        "stock_code": row.get("stock_code", ""),
                        "rcept_dt": row.get("rcept_dt", ""),
                        "report_nm": row.get("report_nm", ""),
                        "section_title": row.get("section_title", "") or "",
                        "source": "allFilings",
                        "text": (row.get("section_content", "") or "")[:2000],
                    }
                )
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
            batchFiles = docsFiles[batchStart : batchStart + docsBatchSize]
            for f in batchFiles:
                try:
                    df = pl.read_parquet(
                        f,
                        columns=[
                            "rcept_no",
                            "corp_code",
                            "corp_name",
                            "stock_code",
                            "report_type",
                            "section_title",
                            "section_order",
                            "section_content",
                        ],
                    )
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

                    allMeta.append(
                        {
                            "rcept_no": row["rcept_no"],
                            "corp_code": row.get("corp_code", ""),
                            "corp_name": row.get("corp_name", ""),
                            "stock_code": row.get("stock_code", ""),
                            "rcept_dt": "",
                            "report_nm": reportNm,
                            "section_title": sectionTitle,
                            "source": "docs",
                            "text": "",
                        }
                    )
                    globalDocId += 1

            if showProgress and (batchStart + docsBatchSize) % (docsBatchSize * 5) == 0:
                elapsed = time.time() - t0
                print(
                    f"  [{batchStart + len(batchFiles)}/{len(docsFiles)}] "
                    f"{globalDocId:,}문서, {nextId:,} stems, {elapsed:.0f}초"
                )

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

    (outDir / "stemDict.json").write_text(json.dumps(stemToId, ensure_ascii=False), encoding="utf-8")

    metaDf = pl.DataFrame(allMeta)
    metaDf.write_parquet(outDir / "meta.parquet")

    # 유형 인덱스 사전 빌드 (검색 시 _buildTypeIndex 생략)
    _buildAndSaveTypeIndex(metaDf, outDir)

    # 파생 지식 레이어 빌드 (companyProfile, eventTimeline, DNA)
    from dartlab.core.search.derived import buildCompanyProfile, buildDna, buildEventTimeline

    buildCompanyProfile(metaDf, outDir)
    buildEventTimeline(metaDf, outDir)
    buildDna(metaDf, outDir)
    if showProgress:
        print("[stemIndex] 파생 집계 빌드 완료 (companyProfile, eventTimeline, dna)")

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
        print(f"[stemIndex] 완료: {globalDocId:,}문서, {nextId:,} stems, {npzMb:.1f}MB, {elapsed:.0f}초")

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


def _buildAndSaveTypeIndex(meta: pl.DataFrame, outDir: Path) -> None:
    """빌드 시점에 유형 인덱스를 생성하여 JSON으로 저장."""
    global _typeIndex, _typeToDocIds

    norm = (
        meta.lazy()
        .with_row_index("_docId")
        .with_columns(
            pl.col("report_nm")
            .str.replace(r"^\[기재정정\]", "", literal=False)
            .str.replace(r"^\[첨부정정\]", "", literal=False)
            .str.replace(r"^\[첨부추가\]", "", literal=False)
            .str.replace(r"^\[발행조건확정\]", "", literal=False)
            .str.replace(r"\s*\(\d{4}\.\d{2}\)\s*$", "", literal=False)
            .str.replace(r"\s*\(.*?\)\s*$", "", literal=False)
            .str.strip_chars()
            .alias("_norm")
        )
        .filter(pl.col("_norm") != "")
        .group_by("_norm")
        .agg(pl.col("_docId"))
        .collect()
    )

    typeToDocIds: dict[str, list[int]] = {
        row[0]: row[1] for row in norm.iter_rows()
    }

    (outDir / "typeIndex.json").write_text(
        json.dumps(typeToDocIds, ensure_ascii=False), encoding="utf-8"
    )

    typeIndex = {nt: set(_tokenize(nt)) for nt in typeToDocIds}
    _typeIndex = typeIndex
    _typeToDocIds = typeToDocIds


def _buildTypeIndex(meta: pl.DataFrame) -> tuple[dict, dict]:
    """114개 정규화 유형 인덱스 로드 (사전 빌드 파일 우선, 없으면 런타임 빌드)."""
    global _typeIndex, _typeToDocIds

    if _typeIndex is not None and _typeToDocIds is not None:
        return _typeIndex, _typeToDocIds

    outDir = _stemIndexDir()
    typeIndexPath = outDir / "typeIndex.json"

    if typeIndexPath.exists():
        typeToDocIds = json.loads(typeIndexPath.read_text(encoding="utf-8"))
    else:
        norm = (
            meta.lazy()
            .with_row_index("_docId")
            .with_columns(
                pl.col("report_nm")
                .str.replace(r"^\[기재정정\]", "", literal=False)
                .str.replace(r"^\[첨부정정\]", "", literal=False)
                .str.replace(r"^\[첨부추가\]", "", literal=False)
                .str.replace(r"^\[발행조건확정\]", "", literal=False)
                .str.replace(r"\s*\(\d{4}\.\d{2}\)\s*$", "", literal=False)
                .str.replace(r"\s*\(.*?\)\s*$", "", literal=False)
                .str.strip_chars()
                .alias("_norm")
            )
            .filter(pl.col("_norm") != "")
            .group_by("_norm")
            .agg(pl.col("_docId"))
            .collect()
        )
        typeToDocIds = {row[0]: row[1] for row in norm.iter_rows()}

    typeIndex = {nt: set(_tokenize(nt)) for nt in typeToDocIds}

    _typeIndex = typeIndex
    _typeToDocIds = typeToDocIds
    return typeIndex, typeToDocIds


def _matchTypes(query: str, typeIndex: dict, topK: int = 3) -> list[tuple[str, float]]:
    """L0: 쿼리 → 가장 유사한 정규화 유형 매칭."""
    expanded = query
    for informal, formal in _L0_INFORMAL.items():
        if informal in query:
            expanded += " " + formal

    qTokens = set(_tokenize(expanded))
    if not qTokens:
        return []

    scores = []
    for typeName, typeTokens in typeIndex.items():
        inter = len(qTokens & typeTokens)
        if inter == 0:
            continue
        union = len(qTokens | typeTokens)
        score = (inter / union) * 0.5 + (inter / len(qTokens)) * 0.5
        scores.append((typeName, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:topK]


def searchNgram(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    topK: int = 10,
) -> pl.DataFrame:
    """계층적 검색 — L0 유형 라우팅 + BM25F bincount.

    L0: 114개 정규화 유형에서 쿼리 매칭 (비공식 변환 포함)
    L1: BM25F bincount (전체 인덱스에서)
    합산: L0 후보 문서에 가산점, L1 결과와 병합
    """
    index, meta = _loadIndex()
    if not index or meta.height == 0:
        return pl.DataFrame()

    stemToId = index["stemToId"]
    offsets = index["offsets"]
    docIds = index["docIds"]
    nDocs = meta.height

    from dartlab.core.dataLoader import DART_VIEWER

    # L0: 유형 매칭 (임계값 0.2 — 약한 부분 매칭 차단)
    _L0_MIN_SCORE = 0.2
    typeIndex, typeToDocIds = _buildTypeIndex(meta)
    matchedTypes = [
        (t, s) for t, s in _matchTypes(query, typeIndex, topK=3) if s >= _L0_MIN_SCORE
    ]
    l0DocIds = set()
    for typeName, _ in matchedTypes:
        l0DocIds.update(typeToDocIds[typeName])

    # L0 먼저: 유형 매칭 문서를 먼저 삽입 (높은 점수)
    rows = []
    seen: set[str] = set()
    queryWords = [w for w in query.split() if len(w) >= 2]

    if matchedTypes:
        for typeName, typeScore in matchedTypes:
            for docId in typeToDocIds[typeName][:topK * 3]:
                if docId >= nDocs:
                    continue
                row = meta.row(docId, named=True)
                rcept = row["rcept_no"]
                if rcept in seen:
                    continue
                if corpCode and row.get("corp_code", "") != corpCode:
                    continue
                if stockCode and row.get("stock_code", "") != stockCode:
                    continue
                seen.add(rcept)
                reportNm = row.get("report_nm", "")
                sectionTitle = row.get("section_title", "")
                exactBoost = 1.0
                if query in reportNm:
                    exactBoost = 3.0
                elif query in sectionTitle:
                    exactBoost = 2.0
                rows.append({
                    "score": round(10.0 * typeScore * exactBoost, 4),
                    "rcept_no": rcept,
                    "corp_name": row.get("corp_name", ""),
                    "stock_code": row.get("stock_code", ""),
                    "rcept_dt": row.get("rcept_dt", ""),
                    "report_nm": reportNm,
                    "section_title": sectionTitle,
                    "text": row.get("text", ""),
                    "dartUrl": f"{DART_VIEWER}{rcept}",
                })

    # L1: BM25F bincount (전체 — L0에 없는 것만 추가)
    tokens = _tokenize(query)
    queryStems = [stemToId[t] for t in tokens if t in stemToId]

    if queryStems:
        allMatched = []
        for stemId in queryStems:
            start = offsets[stemId]
            end = offsets[stemId + 1]
            if end > start:
                allMatched.append(docIds[start:end])

        if allMatched:
            flat = np.concatenate(allMatched)
            counts = np.bincount(flat, minlength=nDocs)

            nTop = min(topK * 5, nDocs)
            topIndices = np.argpartition(counts, -nTop)[-nTop:]
            topIndices = topIndices[np.argsort(counts[topIndices])[::-1]]

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

                baseScore = matchCount / len(queryStems)
                boost = 1.0
                reportNm = row.get("report_nm", "")
                sectionTitle = row.get("section_title", "")

                # exact substring: 쿼리 원문이 그대로 포함되면 최강 부스트
                if query in reportNm:
                    boost += 20.0
                elif query in sectionTitle:
                    boost += 15.0
                else:
                    for w in queryWords:
                        if w in reportNm:
                            boost += 5.0
                        if w in sectionTitle:
                            boost += 2.0

                # L0 가산점: 유형 매칭된 문서면 강하게 부스트
                if int(docId) in l0DocIds:
                    boost += 10.0

                rows.append({
                    "score": round(baseScore * boost, 4),
                    "rcept_no": rcept,
                    "corp_name": row.get("corp_name", ""),
                    "stock_code": row.get("stock_code", ""),
                    "rcept_dt": row.get("rcept_dt", ""),
                    "report_nm": reportNm,
                    "section_title": sectionTitle,
                    "text": row.get("text", ""),
                    "dartUrl": f"{DART_VIEWER}{rcept}",
                })

                if len(rows) >= topK * 3:
                    break

    # (L0 문서는 이미 위에서 삽입됨)

    if not rows:
        return pl.DataFrame()

    rows.sort(key=lambda x: x["score"], reverse=True)
    return pl.DataFrame(rows[:topK])


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
