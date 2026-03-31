"""Ngram+Synonym 검색 엔진 — 모델 불필요, cold start 0ms.

DART 공시의 report_nm + section_title에서 bigram/trigram 역인덱스를 구축하고,
자연어 쿼리를 동의어 확장으로 공시 키워드로 변환하여 검색한다.

실험 105-008에서 precision@5 = 95%, 속도 1ms, 의존성 0 달성.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import polars as pl

from dartlab import config as _cfg

# ── 동의어 테이블 ──

SYNONYMS = {
    "돈을 빌렸다": ["사채", "차입", "대출", "자금조달", "전환사채", "회사채"],
    "빌렸다": ["사채", "차입", "대출"],
    "경영진이 바뀌었다": ["대표이사", "임원", "선임", "해임", "변경"],
    "바뀌었다": ["변경", "교체", "선임", "해임"],
    "주식을 발행했다": ["유상증자", "증자", "신주", "발행"],
    "합쳤다": ["합병", "인수", "교환"],
    "돈을 줬다": ["배당", "배당금", "현금배당"],
    "소송": ["소송", "분쟁", "가처분", "경영권"],
    "투자": ["투자", "시설", "출자", "취득"],
    "문제": ["한정", "부적정", "거절", "감사"],
    "나빠졌다": ["부채", "미지급", "손실", "감자", "관리종목"],
    "높이겠다": ["제고", "기업가치", "개선"],
    "맺었다": ["계약", "체결", "공급"],
    "매수했다": ["대량보유", "취득", "매수"],
    "배당": ["배당", "현금배당", "배당금"],
    "합병": ["합병", "인수", "분할", "교환"],
    "재무": ["재무", "재무제표", "재무상태"],
}

# ── Ngram 유틸 ──


def _ngrams(text: str) -> set[str]:
    """bigram + trigram 동시 추출."""
    text = text.strip()
    result = set()
    if len(text) >= 2:
        result.update(text[i : i + 2] for i in range(len(text) - 1))
    if len(text) >= 3:
        result.update(text[i : i + 3] for i in range(len(text) - 2))
    return result


def _expandQuery(query: str) -> str:
    """자연어 쿼리를 동의어로 확장."""
    expanded = query
    for phrase, synonyms in SYNONYMS.items():
        if phrase in query:
            expanded += " " + " ".join(synonyms)
    return expanded


# ── Ngram 인덱스 ──


def _indexPath() -> Path:
    """ngram 인덱스 저장 경로."""
    return Path(_cfg.dataDir) / "dart" / "vectorIndex" / "ngram_index.json"


def _metaPath() -> Path:
    """메타데이터 parquet 경로."""
    return Path(_cfg.dataDir) / "dart" / "vectorIndex" / "ngram_meta.parquet"


# 인메모리 캐시
_cachedIndex: dict | None = None
_cachedMeta: pl.DataFrame | None = None


def buildNgramIndex(parquetPaths: list[str | Path] | None = None) -> int:
    """allFilings parquet에서 ngram 인덱스 구축 → JSON + meta parquet 저장.

    Parameters
    ----------
    parquetPaths : allFilings parquet 경로 목록. None이면 전체 수집 데이터.

    Returns
    -------
    int
        인덱싱된 문서 수.
    """
    global _cachedIndex, _cachedMeta

    if parquetPaths is None:
        from dartlab.providers.dart.openapi.allFilingsCollector import _META_SUFFIX, _allFilingsDir

        outDir = _allFilingsDir()
        parquetPaths = sorted(str(f) for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)

    if not parquetPaths:
        return 0

    # 데이터 로드
    dfs = [pl.read_parquet(p) for p in parquetPaths]
    df = pl.concat(dfs).filter(pl.col("section_content").is_not_null())

    # 역인덱스 구축
    index: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(df.iter_rows(named=True)):
        text = f"{row['report_nm']} {row.get('section_title', '') or ''}"
        for ng in _ngrams(text):
            index[ng].append(i)

    # 리스트를 세트로 중복 제거 후 다시 리스트 (JSON 직렬화)
    cleanIndex = {ng: sorted(set(ids)) for ng, ids in index.items()}

    # 저장
    idxPath = _indexPath()
    idxPath.parent.mkdir(parents=True, exist_ok=True)
    idxPath.write_text(json.dumps(cleanIndex, ensure_ascii=False), encoding="utf-8")

    # 메타데이터 (검색 결과 표시용)
    meta = df.select(
        [
            "rcept_no",
            "corp_code",
            "corp_name",
            "stock_code",
            "rcept_dt",
            "report_nm",
            "section_title",
            "section_order",
        ]
    ).with_columns(
        pl.Series("text", df["section_content"].str.slice(0, 2000).to_list()),
    )
    meta.write_parquet(_metaPath())

    # 캐시 갱신
    _cachedIndex = cleanIndex
    _cachedMeta = meta

    return df.height


def _loadIndex() -> tuple[dict, pl.DataFrame]:
    """인덱스 + 메타 로드 (캐시 우선)."""
    global _cachedIndex, _cachedMeta

    if _cachedIndex is not None and _cachedMeta is not None:
        return _cachedIndex, _cachedMeta

    idxPath = _indexPath()
    metPath = _metaPath()

    if not idxPath.exists() or not metPath.exists():
        return {}, pl.DataFrame()

    _cachedIndex = json.loads(idxPath.read_text(encoding="utf-8"))
    _cachedMeta = pl.read_parquet(metPath)

    return _cachedIndex, _cachedMeta


def searchNgram(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    topK: int = 10,
) -> pl.DataFrame:
    """Ngram+Synonym 검색. 모델 불필요, cold start 0ms.

    Parameters
    ----------
    query : 검색어 (한국어).
    corpCode : 기업 필터 (8자리).
    stockCode : 종목코드 필터 (6자리).
    topK : 반환 건수.

    Returns
    -------
    pl.DataFrame
        검색 결과. columns: score, rcept_no, corp_name, rcept_dt,
        report_nm, section_title, text, dartUrl
    """
    index, meta = _loadIndex()
    if not index or meta.height == 0:
        return pl.DataFrame()

    # 쿼리 동의어 확장 + ngram 분해
    expanded = _expandQuery(query)
    qNgrams = _ngrams(expanded)
    if not qNgrams:
        return pl.DataFrame()

    # 매칭 점수 계산
    scores: dict[int, int] = defaultdict(int)
    for ng in qNgrams:
        for docId in index.get(ng, []):
            scores[docId] += 1

    if not scores:
        return pl.DataFrame()

    # 상위 결과
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 메타데이터 복원 + 필터
    from dartlab.core.dataLoader import DART_VIEWER

    rows = []
    seen: set[str] = set()
    for docId, matchCount in ranked:
        if docId >= meta.height:
            continue
        row = meta.row(docId, named=True)
        rcept = row["rcept_no"]
        if rcept in seen:
            continue

        # 필터
        if corpCode and row.get("corp_code", "") != corpCode:
            continue
        if stockCode and row.get("stock_code", "") != stockCode:
            continue

        seen.add(rcept)
        rows.append(
            {
                "score": round(matchCount / len(qNgrams), 4),
                "rcept_no": rcept,
                "corp_name": row.get("corp_name", ""),
                "stock_code": row.get("stock_code", ""),
                "rcept_dt": row.get("rcept_dt", ""),
                "report_nm": row.get("report_nm", ""),
                "section_title": row.get("section_title", ""),
                "text": row.get("text", ""),
                "dartUrl": f"{DART_VIEWER}{rcept}",
            }
        )

        if len(rows) >= topK:
            break

    if not rows:
        return pl.DataFrame()

    return pl.DataFrame(rows)


def ngramStats() -> dict:
    """Ngram 인덱스 통계."""
    index, meta = _loadIndex()
    idxPath = _indexPath()
    metPath = _metaPath()

    sizeMb = 0
    if idxPath.exists():
        sizeMb += idxPath.stat().st_size / 1024 / 1024
    if metPath.exists():
        sizeMb += metPath.stat().st_size / 1024 / 1024

    return {
        "ngrams": len(index),
        "documents": meta.height,
        "sizeMb": round(sizeMb, 1),
        "path": str(idxPath.parent),
    }
