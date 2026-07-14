"""panel canonical L1 TOC — 회사 챕터 드리프트를 정부표준 14 노드로 흡수 (READ-time 파생).

``read.readWide`` 가 pivot 전 ``canonicalChapterExpr`` 로 회사별 드리프트 챕터((첨부)재무제표·감사보고서
변형 등)를 14 canonical 노드 라벨로 접는다 → (첨부)가 III 로 흡수돼 phantom 챕터 0. ``CANONICAL_RANK``
(라벨→정부 문서순서)는 ``orderBySpine`` 의 챕터 대순서. 매핑 SSOT = ``canonicalData.CANONICAL_L1`` (운영자 수동).

LLM Specifications:
    AntiPatterns:
        - 챕터 임의 재구성/forward-fill 금지 — bounded 14 노드 매핑(첫 키워드 매치).
        - 매핑을 schema 컬럼으로 bake 금지 — READ 파생(재빌드 무관, schema 17-col 불변).
        - canonical 자동 빌드 도구 금지 — CANONICAL_L1 운영자 수동(docstring 룰).
    OutputSchema:
        - ``canonicalChapterExpr(col) -> pl.Expr`` (chapter → canonical 라벨, 미매칭은 원본).
        - ``CANONICAL_RANK: dict[str, int]`` (canonical 라벨 → 정부 문서순서 0..13).
        - ``canonicalRankExpr(col) -> pl.Expr`` (canonical 라벨 → rank Int).
    Prerequisites:
        - polars. canonicalData.CANONICAL_L1.
    Freshness:
        - CANONICAL_L1 갱신 시 즉시 반영 (READ 파생).
    Dataflow:
        - chapter → 정규화(로마·공백 strip) → 키워드 첫 매치 → canonical 라벨/rank.
    TargetMarkets:
        - KR (DART 정부 서식).
"""

from __future__ import annotations

import re as _re
import sys as _sys
from functools import lru_cache as _lru_cache

import polars as pl

from .canonicalData import CANONICAL_L1, CERT_NODE_IDS, NARRATIVE_ERA_ALIASES, REPORT_CHAPTER_LABELS

# pyodide(polars WASM)는 .list.eval() 중첩표현식이 lazy 엔진에서 capacity overflow 패닉을 낸다.
# 그 경로만 map_elements(Python 포트)로 우회한다(아래 canonicalChapterExpr 분기).
_IS_PYODIDE = _sys.platform == "emscripten"

# canonical 라벨 → 정부 문서순서(rank). list 순서 = rank.
CANONICAL_RANK: dict[str, int] = {label: i for i, (_nid, label, _kw) in enumerate(CANONICAL_L1)}

# 정규화 — 로마숫자 머리("III. ")·공백 제거 (chapter·키워드 공통 축).
_ROMAN_RE = r"^\s*[IVXLCDM]+\s*\.\s*"
_WS_RE = r"\s+"


def _normExpr(col: str) -> pl.Expr:
    """chapter 컬럼 → 정규화 Expr (로마숫자 머리 + 전 공백 제거). 키워드 매칭 축."""
    return pl.col(col).fill_null("").str.replace_all(_ROMAN_RE, "").str.replace_all(_WS_RE, "")


def _normKeyword(kw: str) -> str:
    """키워드 → 정규화 (공백 제거, 키워드엔 로마숫자 없음). chapter 정규화와 같은 축."""
    return "".join(kw.split())


# CANONICAL_L1 키워드는 상수라 정규화형(_normKeyword)을 모듈 로드 시 1회만 계산한다. _pyCanonLabel 이
# 원소마다 라벨과 키워드를 재스캔하며 _normKeyword(kw) 를 매번 재계산하던 것(pyodide panel 한 번에 수십만 회,
# str.split/join 대부분)을 제거한다. (label, 정규화키워드 tuple) 순서는 CANONICAL_L1 그대로 유지.
_CANONICAL_L1_NORM: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
    (label, tuple(_normKeyword(kw) for kw in kws)) for _nid, label, kws in CANONICAL_L1
)


# SECTION-N 경로 구분자 (walker._SECTION_SEP 와 동일). sectionPath = "II␟IV␟2..." depth join.
_SECTION_SEP = "␟"

# III(재무) 라벨 — NT_ 주석키 복원 타깃 (CANONICAL_L1 SSOT 파생, 하드코딩 0).
_FINANCE_LABEL: str = next(label for nid, label, _kw in CANONICAL_L1 if nid == "L3_finance")
# XII(상세표) 라벨 — 부록 컨테이너. 그 안 상세표 제목이 챕터 키워드를 포함해도("2. 계열회사 현황(상세)")
# 소속은 XII — deepest-match 가 IX/X 로 오배정하던 것을 XII-우선으로 차단.
_DETAIL_LABEL: str = next(label for nid, label, _kw in CANONICAL_L1 if nid == "L12_detail")


def _canonLabelExpr(e: pl.Expr) -> pl.Expr:
    """단일 원소(chapter/sectionPath 원소) Expr → canonical L1 라벨 또는 **null**(미매칭).

    정규화(로마·공백 strip) 후 CANONICAL_L1 순서 키워드 첫 매치 라벨. 미매칭은 null(원본 보존은 호출측 coalesce).
    """
    norm = e.fill_null("").str.replace_all(_ROMAN_RE, "").str.replace_all(_WS_RE, "")
    expr: pl.Expr | None = None
    for _nid, label, kws in CANONICAL_L1:
        cond: pl.Expr | None = None
        for kw in kws:
            c = norm.str.contains(_normKeyword(kw), literal=True)
            cond = c if cond is None else (cond | c)
        if cond is None:
            continue
        branch = pl.when(cond).then(pl.lit(label))
        expr = branch if expr is None else expr.when(cond).then(pl.lit(label))
    return expr.otherwise(None) if expr is not None else pl.lit(None, dtype=pl.Utf8)


# ── pyodide 전용 Python 포트 (위 벡터 Expr 과 동일 로직, .list.eval 회피) ──
_ROMAN_PY = _re.compile(_ROMAN_RE)


def _pyNorm(s: str | None) -> str:
    """chapter/원소 문자열 정규화 (로마숫자 머리 + 전 공백 제거). ``_normExpr`` 파이썬 포트."""
    return "".join(_ROMAN_PY.sub("", s or "").split())


@_lru_cache(maxsize=4096)
def _pyCanonLabel(s: str | None) -> str | None:
    """단일 원소 → canonical L1 라벨/None. ``_canonLabelExpr`` 파이썬 포트(순서 키워드 첫 매치).

    순수함수라 메모이즈한다(같은 챕터/원소명이 행마다 반복되고 캐논 라벨은 회사 무관 보편). 정규화 키워드는
    ``_CANONICAL_L1_NORM`` 로 사전계산돼 매 호출 재정규화가 없다. 로직/결과는 옛 구현과 동일.
    """
    norm = _pyNorm(s)
    if not norm:
        return None
    for label, normKws in _CANONICAL_L1_NORM:
        for nkw in normKws:
            if nkw in norm:
                return label
    return None


@_lru_cache(maxsize=4096)
def _pyCanonChapter(pathVal: str | None, chapterVal: str | None, noteKeyVal: str | None) -> str | None:
    """canonicalChapterExpr 파이썬 포트. sectionPath 깊은 canonical → chapter 라벨 → NT_ III → 원본.

    순수함수 + map_elements 로 행마다 호출되나 (path, chapter, noteKey) 조합은 소수라 메모이즈한다.
    """
    labels = (
        [lbl for el in str(pathVal).split(_SECTION_SEP) if (lbl := _pyCanonLabel(el)) is not None] if pathVal else []
    )
    if labels:
        return _DETAIL_LABEL if _DETAIL_LABEL in labels else labels[-1]
    ch = _pyCanonLabel(chapterVal)
    if ch is not None:
        return ch
    if noteKeyVal is not None and str(noteKeyVal).startswith("NT_"):
        return _FINANCE_LABEL
    return chapterVal


def canonicalChapterExpr(
    chapterCol: str = "chapter", pathCol: str = "sectionPath", noteKeyCol: str | None = None
) -> pl.Expr:
    """드리프트·붕괴 chapter → canonical L1 라벨 Expr. **sectionPath 깊은 canonical 원소 우선**.

    DART XML 은 era 별로 챕터 III~XII 를 "II. 사업의 내용" 아래 SECTION-2 로 mis-nesting 해 walker 의
    chapter(SECTION-1)가 붕괴(전 narrative 가 II 로 몰림). 그러나 ``sectionPath``(전 깊이 truth)의 **가장 깊은
    canonical 매치 원소가 진짜 챕터**(예 ``II␟IV. 감사의견`` → IV). 따라서 sectionPath 를 ␟로 쪼개 원소별
    canonical 라벨 → drop_nulls → **last(deepest)**. sectionPath 에 canonical 원소 없으면 chapter 컬럼 직접.
    ``noteKeyCol`` 지정 시 그래도 미해소인 **NT_ 주석행은 III 복원** — (첨부)재무제표 flat ``<P ID>`` 주석은
    SECTION 이 없어 chapter·sectionPath 둘 다 공백으로 새는데(2025+ 35사 15,217행 실측), NT_ 표준코드가
    재무제표 주석임을 정의상 식별하므로 honest 복원(추측 0). 끝까지 미해소면 원본 chapter(honest).

    Args:
        chapterCol: 붕괴 가능 chapter 컬럼명 (fallback).
        pathCol: SECTION-N 전 깊이 sectionPath 컬럼명 (1순위 truth).
        noteKeyCol: 주석 표준코드 컬럼명(보통 "disclosureKey"). None(기본)이면 NT_ 복원 비활성.

    Returns:
        ``canonicalChapter`` 별칭 Utf8 Expr — sectionPath 복원 / chapter 키워드 / NT_→III / 원본.

    Raises:
        없음.

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"chapter": ["II. 사업의 내용"], "sectionPath": ["II. 사업의 내용␟III. 재무에 관한 사항"]})
        >>> df.select(canonicalChapterExpr())["canonicalChapter"].to_list()
        ['III. 재무에 관한 사항']

    SeeAlso:
        - ``read.readWide`` — pivot 전 본 Expr 로 챕터 복원·접기 (noteKeyCol="disclosureKey").
        - ``canonicalRankExpr`` — canonical 라벨 → rank.

    Requires:
        - polars. CANONICAL_L1. sectionPath(walker bake, SECTION-N 전 깊이).

    Capabilities:
        - 붕괴된 chapter 를 sectionPath 깊은 canonical 원소로 복원 — chapter collapse(전 narrative II 몰림) 해소.
        - 구조신호 0 인 NT_ 주석 orphan 을 III 로 honest 복원 — (첨부) flat 주석 챕터 탈락 회귀 흡수.

    Guide:
        - readWide 가 anchorLatest·dedupKeyed 후 호출. 직접 호출 가능(순수 Expr).

    AIContext:
        - list.eval 로 sectionPath 원소별 canonical 매치(vectorized, Python loop 0), READ 파생.

    LLM Specifications:
        AntiPatterns:
            - 붕괴된 chapter 컬럼 직접 신뢰 금지 — sectionPath 깊은 canonical 원소가 truth.
            - 미매칭에 None 강제 금지 — chapter→원본 coalesce(honest). NT_ 복원은 *정의상 III*(주석 표준코드)라 예외.
            - NT_ 외 키(front-matter ∅ 등) 추측 배정 금지 — honest-gap 유지.
        OutputSchema:
            - ``pl.Expr`` (alias "canonicalChapter", Utf8).
        Prerequisites:
            - polars. sectionPath/chapter 컬럼 (+선택 disclosureKey).
        Freshness:
            - READ 파생.
        Dataflow:
            - sectionPath split → 원소별 canonical → last → chapter 키워드 → NT_→III → 원본.
        TargetMarkets:
            - KR (DART).
    """
    if _IS_PYODIDE:
        # polars WASM 은 .list.eval() 이 lazy 엔진에서 capacity overflow 패닉 → 동일 로직을
        # map_elements(Python 포트)로. panel build 1회라 성능 허용, 벡터 경로와 결과 동일.
        cols = [pl.col(pathCol).alias("__p__"), pl.col(chapterCol).alias("__c__")]
        if noteKeyCol is not None:
            cols.append(pl.col(noteKeyCol).alias("__n__"))
        _hasNote = noteKeyCol is not None
        return (
            pl.struct(cols)
            .map_elements(
                lambda r: _pyCanonChapter(r["__p__"], r["__c__"], r["__n__"] if _hasNote else None),
                return_dtype=pl.Utf8,
            )
            .alias("canonicalChapter")
        )
    pathLabels = (
        pl.col(pathCol).fill_null("").str.split(_SECTION_SEP).list.eval(_canonLabelExpr(pl.element())).list.drop_nulls()
    )
    # XII(상세표) 우선 — 부록 컨테이너 안 상세표 제목의 챕터 키워드(계열회사·대주주 등)가 deepest 를 가로채
    # IX/X 로 오배정되는 것 차단. 그 외엔 가장 깊은 canonical 원소가 진짜 챕터.
    fromPath = (
        pl.when(pathLabels.list.contains(_DETAIL_LABEL)).then(pl.lit(_DETAIL_LABEL)).otherwise(pathLabels.list.last())
    )
    chain: list[pl.Expr] = [fromPath, _canonLabelExpr(pl.col(chapterCol))]
    if noteKeyCol is not None:
        # NT_ 표준코드 = 재무제표 주석(정의상 III). 구조신호(경로·키워드) 전무한 (첨부) flat 주석만 닿는다 —
        # 경로/키워드 해소가 chain 앞이라 front-matter(키 ∅)는 본 분기 미적용(honest-gap 보존).
        chain.append(pl.when(pl.col(noteKeyCol).str.starts_with("NT_")).then(pl.lit(_FINANCE_LABEL)).otherwise(None))
    return pl.coalesce([*chain, pl.col(chapterCol)]).alias("canonicalChapter")


def canonicalRankExpr(col: str = "chapter") -> pl.Expr:
    """canonical 라벨(이미 접힌 chapter) → 정부 문서순서 rank Int Expr (미등재는 null).

    ``orderBySpine`` 의 챕터 대순서 — canonicalChapterExpr 로 접힌 chapter 를 CANONICAL_RANK 로 매핑.
    14 밖(미매칭 원본 보존분)은 null → nulls_last(말미).

    Args:
        col: canonical 라벨 컬럼명 (보통 접힌 "chapter").

    Returns:
        ``_canonRank`` 별칭 Int64 Expr (rank 또는 null).

    Raises:
        없음.

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"chapter": ["III. 재무에 관한 사항", "별난챕터"]})
        >>> df.select(canonicalRankExpr())["_canonRank"].to_list()
        [3, None]
    """
    return pl.col(col).replace_strict(CANONICAL_RANK, default=None, return_dtype=pl.Int64).alias("_canonRank")


__all__ = [
    "CANONICAL_L1",
    "NARRATIVE_ERA_ALIASES",
    "CANONICAL_RANK",
    "CERT_NODE_IDS",
    "REPORT_CHAPTER_LABELS",
    "canonicalChapterExpr",
    "canonicalRankExpr",
]
