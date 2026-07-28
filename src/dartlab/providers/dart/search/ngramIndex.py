"""Ngram+Synonym 검색 엔진 — stem ID 역인덱스, CSR 구조, bincount 검색.

report_nm + panel section_title 대상 bigram/trigram 역인덱스.
scope="title" 검색에서 사용.

allFilings(수시공시) + panel(정기보고서) 통합 인덱스 지원.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import numpy as np
import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.providers.dart.search.coerce import _periodToReportName
from dartlab.providers.dart.search.ngramIndexSync import _stemIndexDir

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
    "자사주": "자기주식 자기주식취득",
    "자사주매입": "자기주식취득 자기주식취득결정",
    "자사주 매입": "자기주식취득 자기주식취득결정",
    "자사주 취득": "자기주식취득 자기주식취득결정",
    "자사주 소각": "자기주식소각",
    "주식매입": "자기주식취득 자기주식취득결정",
    "스톡옵션": "주식매수선택권",
    "사옵": "주식매수선택권",
    "정관변경": "정관 변경",
    "물적분할": "분할 분할결정",
    "인적분할": "분할 분할결정",
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


def _normalizeReportName(col: pl.Expr) -> pl.Expr:
    """report_nm 정규화 — [기재정정]/[첨부정정] 접두사 및 날짜 접미사 제거.

    Parameters
    ----------
    col : pl.Expr
        report_nm 컬럼 expression (예: ``pl.col("report_nm")``).

    Returns
    -------
    pl.Expr
        정규화된 report_nm expression.
    """
    return (
        col.str.replace(r"^\[기재정정\]", "", literal=False)
        .str.replace(r"^\[첨부정정\]", "", literal=False)
        .str.replace(r"^\[첨부추가\]", "", literal=False)
        .str.replace(r"^\[발행조건확정\]", "", literal=False)
        .str.replace(r"\s*\(\d{4}\.\d{2}\)\s*$", "", literal=False)
        .str.replace(r"\s*\(.*?\)\s*$", "", literal=False)
        .str.strip_chars()
    )


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


def _panelCodes() -> list[str]:
    """panel artifact 에서 사용 가능한 종목코드 목록."""
    panelDir = Path(_cfg.dataDir) / DATA_RELEASES["panel"]["dir"]
    if not panelDir.exists():
        return []
    flat = {p.stem for p in panelDir.glob("*.parquet") if not p.name.startswith("_")}
    nested = {p.name for p in panelDir.iterdir() if p.is_dir()}
    return sorted(flat | nested)


# 캐시
_cachedIndex: dict | None = None
_cachedMeta: pl.DataFrame | None = None


# ── 빌드 ──


def buildNgramIndex(
    parquetPaths: list[str | Path] | None = None,
    *,
    includePanel: bool = False,
    panelBatchSize: int = 100,
    showProgress: bool = True,
) -> int:
    """통합 stem ID 역인덱스 구축.

    allFilings parquet + (선택) panel parquet → stemIndex.npz + stemDict.json + meta.parquet

    Parameters
    ----------
    parquetPaths : allFilings parquet 경로. None이면 자동 탐색.
    includePanel : True면 panel(정기보고서)도 포함.
    panelBatchSize : panel 종목 배치 크기 (OOM 방지).
    showProgress : 진행 표시.

    Returns
    -------
    int
        인덱싱된 문서 수.

    Raises:
        없음.

    Example:
        >>> buildNgramIndex(...)

    Args:
        parquetPaths: 인덱스 source parquet 경로 리스트. None 이면 기본.
        includePanel: True 면 panel sectionLeaf 포함.
        panelBatchSize: panel 처리 batch 크기.
        showProgress: True 면 progress 로그.

    Returns:
        int — 인덱스 건수.
    """
    import time

    global _cachedIndex, _cachedMeta
    t0 = time.time()

    # ── Phase 1: allFilings 로드 ──
    if parquetPaths is None:
        from dartlab.core.dartClient import allFilingsDir as _allFilingsDir
        from dartlab.core.dartClient import allFilingsMetaSuffix

        _META_SUFFIX = allFilingsMetaSuffix()
        outDir = _allFilingsDir()
        parquetPaths = sorted(str(f) for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)

    stemToId: dict[str, int] = {}
    nextId = 0
    invertedIndex: dict[int, list[int]] = defaultdict(list)
    allMeta: list[dict] = []
    globalDocId = 0
    # allFilings 신규 schema 는 한 공시 = 1 row 이라 rcept_no 자체로 unique.
    # panel (사업보고서 등) 는 block 분할이라 (rcept_no, block_order) 필요.
    existingKeys: set[tuple[str, int]] = set()

    # allFilings — raw 본문 단일 컬럼 (content_raw, DART XML/HTML 생긴 그대로). 표시용
    # text 는 BeautifulSoup ``lxml`` parser (XML/HTML 양쪽 안전) get_text 로 변환.
    # 토큰화는 report_nm 만 사용 (section_title / contentHead 없음).
    if parquetPaths:
        from bs4 import BeautifulSoup

        for p in parquetPaths:
            try:
                df = pl.read_parquet(
                    p,
                    columns=[
                        "rcept_no",
                        "corp_code",
                        "corp_name",
                        "stock_code",
                        "rcept_dt",
                        "report_nm",
                        "content_raw",
                        "fetch_status",
                    ],
                ).filter(pl.col("fetch_status") == "ok")
            except (pl.exceptions.PolarsError, OSError):
                continue

            for row in df.iter_rows(named=True):
                key = (row["rcept_no"], 0)
                existingKeys.add(key)

                text = row["report_nm"]
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

                raw = row.get("content_raw") or ""
                displayText = BeautifulSoup(raw, "lxml").get_text(" ", strip=True)[:2000] if raw else ""
                allMeta.append(
                    {
                        "rcept_no": row["rcept_no"],
                        "corp_code": row.get("corp_code", ""),
                        "corp_name": row.get("corp_name", ""),
                        "stock_code": row.get("stock_code", ""),
                        "rcept_dt": row.get("rcept_dt", ""),
                        "report_nm": row.get("report_nm", ""),
                        "section_title": "",
                        "source": "allFilings",
                        "text": displayText,
                    }
                )
                globalDocId += 1

        if showProgress:
            _log.info(f"[stemIndex] allFilings: {globalDocId:,}문서, {nextId:,} stems")

    # ── Phase 2: panel 로드 (배치) ──
    if includePanel:
        from dartlab.providers.dart.panel.text import panelTextRows

        panelCodes = _panelCodes()
        try:
            from dartlab.core.listingResolver import getListingResolver

            resolver = getListingResolver()
        except Exception:  # noqa: BLE001 — resolver 부재는 메타 회사명 공백으로 graceful degrade
            resolver = None

        if showProgress:
            _log.info(f"[stemIndex] panel: {len(panelCodes)}종목 처리 시작")

        for batchStart in range(0, len(panelCodes), panelBatchSize):
            batchCodes = panelCodes[batchStart : batchStart + panelBatchSize]
            for code in batchCodes:
                try:
                    df = panelTextRows(code)
                except (pl.exceptions.PolarsError, OSError):
                    continue
                if df is None or df.is_empty():
                    continue
                try:
                    corpName = resolver.codeToName(code) if resolver else ""
                except Exception:  # noqa: BLE001 — resolver 구현 오류가 색인을 막지 않게 함
                    corpName = ""

                for row in df.iter_rows(named=True):
                    rceptNo = row.get("rceptNo") or ""
                    if not rceptNo:
                        continue
                    blockOrder = int(row.get("blockOrder") or 0)
                    key = (rceptNo, blockOrder)
                    if key in existingKeys:
                        continue
                    existingKeys.add(key)

                    reportNm = _periodToReportName(str(row.get("period") or ""))
                    sectionTitle = row.get("sectionLeaf") or ""
                    contentHead = (row.get("contentRaw", "") or "")[:_CONTENT_INDEX_CHARS]
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
                            "rcept_no": rceptNo,
                            "corp_code": "",
                            "corp_name": corpName or "",
                            "stock_code": code,
                            "rcept_dt": rceptNo[:8] if len(rceptNo) >= 8 else "",
                            "report_nm": reportNm,
                            "section_title": sectionTitle,
                            "source": "panel",
                            "text": "",
                        }
                    )
                    globalDocId += 1

            if showProgress and (batchStart + panelBatchSize) % (panelBatchSize * 5) == 0:
                elapsed = time.time() - t0
                _log.info(
                    "  [%d/%d] %s문서, %s stems, %.0f초",
                    batchStart + len(batchCodes),
                    len(panelCodes),
                    f"{globalDocId:,}",
                    f"{nextId:,}",
                    elapsed,
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
    from dartlab.providers.dart.search.derived import buildCompanyProfile, buildDna, buildEventTimeline

    buildCompanyProfile(metaDf, outDir)
    buildEventTimeline(metaDf, outDir)
    buildDna(metaDf, outDir)
    if showProgress:
        _log.info("[stemIndex] 파생 집계 빌드 완료 (companyProfile, eventTimeline, dna)")

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
        _log.info(f"[stemIndex] 완료: {globalDocId:,}문서, {nextId:,} stems, {npzMb:.1f}MB, {elapsed:.0f}초")

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
        .with_columns(_normalizeReportName(pl.col("report_nm")).alias("_norm"))
        .filter(pl.col("_norm") != "")
        .group_by("_norm")
        .agg(pl.col("_docId"))
        .collect(engine="streaming")
    )

    typeToDocIds: dict[str, list[int]] = {row[0]: row[1] for row in norm.iter_rows()}

    (outDir / "typeIndex.json").write_text(json.dumps(typeToDocIds, ensure_ascii=False), encoding="utf-8")

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
            .with_columns(_normalizeReportName(pl.col("report_nm")).alias("_norm"))
            .filter(pl.col("_norm") != "")
            .group_by("_norm")
            .agg(pl.col("_docId"))
            .collect(engine="streaming")
        )
        typeToDocIds = {row[0]: row[1] for row in norm.iter_rows()}

    typeIndex = {nt: set(_tokenize(nt)) for nt in typeToDocIds}

    _typeIndex = typeIndex
    _typeToDocIds = typeToDocIds
    return typeIndex, typeToDocIds


def _matchTypes(query: str, typeIndex: dict, limit: int = 3) -> list[tuple[str, float]]:
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
    return scores[:limit]


def searchNgram(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    limit: int = 10,
) -> pl.DataFrame:
    """계층적 검색 — L0 유형 라우팅 + L1 BM25F bincount 융합.

    DART 공시 제목/섹션 검색의 **메인 엔트리**. 2-tier 검색 전략으로 동의어/오타 견고:

    **L0 (유형 라우팅)**: 114 개 정규화 보고서 유형 (사업보고서/분기보고서/감사보고서/...)
    에서 쿼리 매칭. 비공식 표기 (``"분기"`` → ``"분기보고서"``) 변환 포함. 임계값 0.2
    이상만 채택. exact substring match 시 3 배 boost (``in reportNm``) 또는 2 배
    (``in sectionTitle``).

    **L1 (BM25F bincount)**: 전체 인덱스에서 bigram/trigram 토큰 매칭. CSR (Compressed
    Sparse Row) 구조로 ``offsets`` / ``docIds`` 배열 직접 슬라이싱 + ``numpy.bincount``
    로 전종목 동시 ranking. Python loop 0.

    **L0 ∪ L1 병합**: L0 결과 우선 삽입, L1 은 L0 미포함 문서만 추가 (중복 ``rcept_no`` 제외).

    Args:
        query: 검색 쿼리 자연어 (예: ``"삼성전자 분기보고서 2024"`` / ``"감사의견 한정"``).
            ``_tokenize`` 가 공백 분리 후 bigram/trigram 생성.
        corpCode: 8 자리 corp_code 로 결과 필터 (선택).
        stockCode: 6 자리 종목코드로 결과 필터 (선택). corpCode 와 동시 지정 가능.
        limit: 반환 문서 수 (default 10). L0 후보는 ``limit * 3`` 까지 스캔.

    Returns:
        pl.DataFrame — 검색 결과 (점수 내림차순). 컬럼:

        - ``score`` (float): 정규화 점수 (L0 boost 적용).
        - ``rcept_no`` (str): 접수번호 (유일 키).
        - ``corp_name`` / ``stock_code`` / ``corp_code`` (str).
        - ``rcept_dt`` (str ``YYYYMMDD``): 접수일자.
        - ``report_nm`` / ``section_title`` / ``text`` (str): 매칭 본문.
        - ``dartUrl`` (str): DART 공시뷰어 URL (``DART_VIEWER + rcept_no``).

    Raises:
        없음. 인덱스 부재 / meta empty 시 빈 DataFrame 반환.

    Example:
        >>> df = searchNgram("분기보고서 2024", stockCode="005930", limit=20)
        >>> df.select(["score", "rcept_dt", "report_nm"]).head(5)
              / ``stock_code`` (str) / ``rcept_dt`` (str YYYYMMDD) / ``report_nm`` (str)
              / ``section_title`` (str) / ``text`` (str) / ``dartUrl`` (str).
            - row 수 ≤ limit (L0 ∪ L1 병합 후).
            - 빈 DataFrame — 인덱스 부재 / 매칭 0.
        Prerequisites:
            - stem index (``stemToId`` / ``offsets`` / ``docIds`` / ``meta``) 로드 완료.
            - HuggingFace origin 또는 local cache (``pushStemIndex`` / ``pullStemIndex``).
        Freshness:
            - 인덱스는 일 단위 rebuild (DART 일일 공시 cadence).
            - L0 type index 는 ``_buildTypeIndex`` 가 호출 시 derive (캐시 X).
        Dataflow:
            - query → ``_tokenize`` (bigram/trigram 토큰)
            - → (L0) ``_buildTypeIndex`` + ``_matchTypes`` (114 유형 매칭, 임계값 0.2)
            - → exact substring boost (reportNm 3x / sectionTitle 2x)
            - → (L1) stemToId lookup → offsets/docIds CSR slice → ``np.bincount``
            - → L0 ∪ L1 병합 (중복 rcept_no 제거) → corpCode / stockCode 필터
            - → score 내림차순 정렬 → top-limit pl.DataFrame.
        TargetMarkets:
            - KR (DART) — 공시 보고서 제목 + 섹션 제목 전수 인덱스.
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
    matchedTypes = [(t, s) for t, s in _matchTypes(query, typeIndex, limit=3) if s >= _L0_MIN_SCORE]
    l0DocIds = set()
    for typeName, _ in matchedTypes:
        l0DocIds.update(typeToDocIds[typeName])

    # L0 먼저: 유형 매칭 문서를 먼저 삽입 (높은 점수)
    rows = []
    seen: set[str] = set()
    queryWords = [w for w in query.split() if len(w) >= 2]

    if matchedTypes:
        for typeName, typeScore in matchedTypes:
            for docId in typeToDocIds[typeName][: limit * 3]:
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
                rows.append(
                    {
                        "score": round(10.0 * typeScore * exactBoost, 4),
                        "rcept_no": rcept,
                        "corp_name": row.get("corp_name", ""),
                        "stock_code": row.get("stock_code", ""),
                        "rcept_dt": row.get("rcept_dt", ""),
                        "report_nm": reportNm,
                        "section_title": sectionTitle,
                        "text": row.get("text", ""),
                        "dartUrl": f"{DART_VIEWER}{rcept}",
                    }
                )

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

            nTop = min(limit * 5, nDocs)
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

                rows.append(
                    {
                        "score": round(baseScore * boost, 4),
                        "rcept_no": rcept,
                        "corp_name": row.get("corp_name", ""),
                        "stock_code": row.get("stock_code", ""),
                        "rcept_dt": row.get("rcept_dt", ""),
                        "report_nm": reportNm,
                        "section_title": sectionTitle,
                        "text": row.get("text", ""),
                        "dartUrl": f"{DART_VIEWER}{rcept}",
                    }
                )

                if len(rows) >= limit * 3:
                    break

    # (L0 문서는 이미 위에서 삽입됨)

    if not rows:
        return pl.DataFrame()

    rows.sort(key=lambda x: x["score"], reverse=True)
    return pl.DataFrame(rows[:limit])


# ── 통계 ──


def ngramStats() -> dict:
    """ngram 인덱스 파일 메타 통계 — stemIndex.npz 파일 크기 / stem 수 / document 수.

    Returns:
        ``{"sizeMb": float, "stems": int, "documents": int}``.

    Raises:
        없음.

    Example:
        >>> ngramStats()
        {'sizeMb': 12.3, 'stems': 45678, 'documents': 12345}
    """
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
        documents = pl.scan_parquet(metaPath).select(pl.len()).collect(engine="streaming").item()

    return {
        "stems": stems,
        "documents": documents,
        "sizeMb": round(sizeMb, 1),
        "path": str(outDir),
    }


# ── HF push/pull ──


# ── push/pull/iter helper 는 ngramIndexSync.py 로 분리 (규칙 3 LoC).
from dartlab.providers.dart.search.ngramIndexSync import (  # noqa: E402, F401
    iterNgram,
    pullStemIndex,
    pushStemIndex,
)
