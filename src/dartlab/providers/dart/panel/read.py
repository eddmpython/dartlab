"""panel read 엔진 (L1 read) — parquet long → 항목 × period wide 수평화 (lxml 0).

``Panel`` 이 wrap 하는 read backend 단일 모듈 (reader+anchor+pivot 통합). ``read_parquet`` +
columnar projection 만 — BUILD(build/) 와 물리 분리, lxml/zipfile import 0 (R2, 콜드 <1s).
period 파일 prune(``periods`` 인자)으로 대형 종목 메모리 핸들.

수평화 단계:
    1. ``readLong`` — flat 파일 read + disclosureKey 보장(build native 채움, 옛 artifact 만 fallback).
    2. ``alignNotes`` — 옛 split 주석행(null key, BUILD 가 제목만 분할)을 회사 최근 XBRL 뼈대(scope,제목)→NT_
       에 read-time 정렬. 정렬·뼈대 개선이 **재빌드 무관**(빌드는 분할만 동결).
    3. ``anchorLatest`` — (disclosureKey, scope) 앵커로 era drift(BS→BS_C) 흡수 → 한 행 정렬.
    4. ``dedupKeyed`` — 본문+첨부 중복 keyed 행을 (key,scope,leafType,period) 당 1개 (collapse 증식 차단).
    5. ``canonicalChapterExpr`` — 회사 드리프트 챕터((첨부)재무제표 등)를 정부표준 14 노드로 흡수((첨부)→III).
    6. ``readWide`` — (canonicalChapter, sectionLeaf, blockLeaf, leafType, key, scope) collapse → period 축
       pivot → canonical rank 정렬. leafType 으로 표↔표·텍스트↔텍스트 분리. ``tag=False`` 면 정렬된 wide 셀에
       태그 1회 strip(plain) — 큰 셀 1회가 fragment 수천개 strip 보다 2.8x 빠름(byte-identical 실측).

LLM Specifications:
    AntiPatterns:
        - lxml/zipfile/network import 금지 — read 표면(R2, 콜드 <1s).
        - 매 read resolveBatch 금지 — build 가 채운 disclosureKey 우선, 전부 null 일 때만 fallback.
        - build 단계 plain 사전계산 금지 — read 파생(R4). collapse(long) 단계 strip 금지 — wide 셀 1회(2.8x).
        - pivot index 에 xbrlClass 유지 금지 — era drift, scope(파생)로 대체.
    OutputSchema:
        - ``readLong(code, *, marketNs, periods) -> pl.DataFrame | None`` (14-col + disclosureKey).
        - ``readWide(code, *, marketNs, periods, tag) -> pl.DataFrame | None`` (index + period 열).
        - ``scopeExpr(col) -> pl.Expr`` / ``anchorLatest(df) -> pl.DataFrame``.
    Prerequisites:
        - polars. data/{dart|edgar}/panel/{code}.parquet (build 결과).
    Freshness:
        - 매 호출 read (artifact 변경 즉시 반영, 캐시 0 — 누적 0).
    Dataflow:
        - parquet → readLong → anchorLatest → collapse(+tag strip) → pivot.
    TargetMarkets:
        - KR (DART) + US (EDGAR) 공통.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import polars as pl

import dartlab.config as _cfg

from .period import sortPeriods

_log = logging.getLogger(__name__)

# pyodide(브라우저 WASM)는 huggingface_hub 이 없다(emscripten 제외 dep). panel 보드 lazy 조달은
# 로더 공용 pyodide fetch(pyodideFetchToFS, pyfetch/XHR)로 우회한다. 데스크톱은 huggingface_hub.
_IS_PYODIDE = sys.platform == "emscripten"

# pivot row identity (회사내 다기간 정렬 키). scope = read 파생(scopeExpr). chapter 는 readWide 가
# canonicalChapterExpr 로 접은 canonical 라벨((첨부)→III). leafType = text/table 분리(표↔표 정렬).
_INDEX_COLS = ["chapter", "sectionLeaf", "blockLeaf", "leafType", "disclosureKey", "scope"]

# 태그 strip — 순수 polars regex (lxml 0, R2).
_TAG_RE = r"<[^>]+>"
_WS_RE = r"\s+"


class PanelArtifactFetchError(RuntimeError):
    """원격 panel artifact 조달 실패."""

    def __init__(self, code: str, marketNs: str, category: str, cause: BaseException):
        self.code = code
        self.marketNs = marketNs
        self.category = category
        super().__init__(
            f"panel artifact fetch 실패: code={code}, market={marketNs}, "
            f"category={category}, error={type(cause).__name__}: {cause}"
        )


class PanelArtifactReadError(RuntimeError):
    """로컬 panel artifact 읽기 또는 정리 실패."""

    def __init__(self, code: str, marketNs: str, operation: str, cause: BaseException):
        self.code = code
        self.marketNs = marketNs
        self.operation = operation
        super().__init__(
            f"panel artifact {operation} 실패: code={code}, market={marketNs}, error={type(cause).__name__}: {cause}"
        )


class PanelSchemaError(ValueError):
    """panel artifact schema 또는 수평화 계약 위반."""


def _stripExpr(col: str) -> pl.Expr:
    """contentRaw(태그 포함) → plain 텍스트 strip Expr (태그 제거 + 공백 정리).

    ``<...>`` 태그를 공백으로 치환 → 연속 공백 1칸 → 양끝 trim. ``readWide``/``Panel`` 이
    pivot 된 wide 셀에 일괄 적용 (collapse 단계 fragment strip 보다 2.8x 빠름 — 큰 셀 1회
    정규식이 작은 조각 수천개 정규식보다 효율적, byte-identical 실측). 순수 polars(lxml 0, R2).

    Args:
        col: strip 할 컬럼명 (period 컬럼).

    Returns:
        ``col`` 별칭 유지 plain Expr.

    Raises:
        없음.

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"2025Q4": ["<TD>재고</TD> <TD>290</TD>"]})
        >>> df.select(_stripExpr("2025Q4"))["2025Q4"][0]
        '재고 290'

    SeeAlso:
        - ``readWide`` — pivot 후 본 Expr 로 wide 셀 strip.

    Requires:
        - polars.

    Capabilities:
        - 태그 무손실 raw 셀을 plain 으로 — wide 격자에 일괄/부분 적용 (filter 후 그 행만도 가능).

    Guide:
        - readWide(tag=False) 가 정렬된 wide 의 period 컬럼에 일괄 적용. 직접 부분 적용 가능.

    AIContext:
        - 순수 regex — strip 시점은 build 가 아니라 read(파생물 미저장, R4).

    LLM Specifications:
        AntiPatterns:
            - build 단계 plain 사전계산 금지 — read 파생(R4, feedback_no_content_plain_precompute).
            - collapse(long) 단계 strip 금지 — pivot 후 wide 셀 1회(2.8x).
        OutputSchema:
            - ``pl.Expr`` (col 별칭 유지, Utf8).
        Prerequisites:
            - polars. 태그 포함 raw 셀.
        Freshness:
            - read 파생.
        Dataflow:
            - col → TAG→" " → WS→" " → strip.
        TargetMarkets:
            - KR + US 공통.
    """
    return pl.col(col).str.replace_all(_TAG_RE, " ").str.replace_all(_WS_RE, " ").str.strip_chars()


def _panelDir(code: str, marketNs: str = "kr") -> Path:
    """panel artifact read 디렉터리 (시장별 단일 경로).

    Args:
        code: 종목코드(KR 6자리) 또는 CIK/ticker(US).
        marketNs: 시장 namespace ("kr" / "us").

    Returns:
        KR: ``data/dart/panel/{code}/`` · US: ``data/edgar/panel/{code}/`` Path.

    Raises:
        없음.

    Example:
        >>> _panelDir("005930").as_posix().endswith("dart/panel/005930")  # doctest: +SKIP
        True

    SeeAlso:
        - ``readLong`` / ``readWide`` — 본 디렉터리 read.

    Requires:
        - dartlab.config.

    Capabilities:
        - 시장별 panel artifact 단일 경로 — read 엔진이 본 함수만 경유(경로 분산 0).

    Guide:
        - 내부 helper — readLong/readWide 경유.

    AIContext:
        - 경로 계산만 — 부작용 0.

    LLM Specifications:
        AntiPatterns:
            - 경로 분산 하드코딩 금지 — 본 함수 단일.
        OutputSchema:
            - ``pathlib.Path``.
        Prerequisites:
            - config.dataDir.
        Freshness:
            - 정적.
        Dataflow:
            - (code, marketNs) → data/{dart|edgar}/panel/{code}.
        TargetMarkets:
            - KR + US.
    """
    base = "dart" if marketNs == "kr" else "edgar"
    return Path(_cfg.dataDir) / base / "panel" / code


_HF_PANEL_ATTEMPTED: set[str] = set()


def ensurePanelFromHf(code: str, marketNs: str = "kr") -> bool:
    """panel.parquet 부재 시 HF lazy 다운로드 — 한 종목만, 1회 시도 (단일 artifact 자동로드).

    sections ``_ensureFromHf`` 미러. 로컬 우선 — 파일 있으면 즉시 반환. offline/
    ``DARTLAB_NO_HF_DOWNLOAD=1`` skip. KR(panel) + US(edgarPanel) 둘 다.
    native is/bs/cf/ratios(셀)도 이 한 artifact 에서 파생되므로 panel.parquet 만 받으면 충분.

    Args:
        code: 종목코드 (KR 6자리) 또는 ticker (US — 대소문자 무관, 내부 upper 정규화).
        marketNs: 시장 namespace. ``"kr"`` → panel repo, ``"us"`` → edgarPanel repo. 그 외 즉시 반환.

    Returns:
        로컬 또는 다운로드 artifact가 준비됐으면 ``True``. 다운로드 비활성 또는 원격에
        실제 artifact가 없으면 ``False``.

    Example:
        >>> ensurePanelFromHf("005930")              # doctest: +SKIP — KR (dart/panel)
        >>> ensurePanelFromHf("AAPL", marketNs="us") # doctest: +SKIP — US (edgar/panel)

    Raises:
        ValueError: 지원하지 않는 ``marketNs``.
        PanelArtifactFetchError: 원격 요청·인증·저장·검증 실패.
    """
    import os as _os

    if marketNs not in ("kr", "us"):
        raise ValueError(f"marketNs는 'kr' 또는 'us'여야 합니다: {marketNs!r}")
    code = code.upper() if marketNs == "us" else code  # EDGAR ticker 대소문자 무관 (build 가 upper 저장)
    flat = _panelDir(code, marketNs).parent / f"{code}.parquet"
    if flat.exists():  # flat 파일만 — 옛 nested 폴더는 flat 다운로드를 막지 않음(stale 서빙 방지)
        return True
    if _os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        return False
    attemptKey = f"{marketNs}:{code}"
    if attemptKey in _HF_PANEL_ATTEMPTED:
        return False

    category = "panel" if marketNs == "kr" else "edgarPanel"

    if _IS_PYODIDE:
        # 브라우저: huggingface_hub 부재. 로더 공용 pyodide fetch(pyfetch/XHR)로 flat parquet 조달.
        # Pyodide fetch 실패는 typed error로 전파하고 영구 마킹하지 않아 재시도 가능하게 둔다.
        from dartlab.core.dataConfig import DATA_RELEASES
        from dartlab.core.dataLoaderPyodide import pyodideFetchToFS

        try:
            pyodideFetchToFS(code, category, DATA_RELEASES[category]["dir"], flat)
        except MemoryError:
            raise
        except (OSError, RuntimeError, ValueError) as exc:
            raise PanelArtifactFetchError(code, marketNs, category, exc) from exc
        return flat.exists()

    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import HfHubHTTPError
    except ImportError as exc:
        raise PanelArtifactFetchError(code, marketNs, category, exc) from exc

    try:
        from dartlab.core.dataConfig import DATA_RELEASES, repoFor
        from dartlab.core.hfRetry import retryHfCall

        repoId = repoFor(category)
        patterns = [f"{DATA_RELEASES[category]['dir']}/{code}.parquet"]  # flat 회사당 1파일 (us 는 보드+셀)
        retryHfCall(  # HF read SSOT(core.hfRetry). 429/503/504 단일 백오프
            snapshot_download,
            repo_id=repoId,
            repo_type="dataset",
            allow_patterns=patterns,  # flat 회사당 1파일 (us 는 보드+셀)
            local_dir=str(Path(_cfg.dataDir)),
        )
    except (HfHubHTTPError, OSError, RuntimeError, ValueError) as exc:
        raise PanelArtifactFetchError(code, marketNs, category, exc) from exc
    # snapshot_download 는 allow_patterns 가 HF 에 없어도 *예외 없이* 0 파일로 '성공'한다 — 이게
    # 옛 silent-empty(reader flat ↔ HF nested 불일치)의 근본. 다운로드 후 파일 존재를 확인해
    # 부재면 1회 가시 경고 + 영구 마킹(genuinely absent ≠ 일시 실패).
    if flat.exists():
        return True
    _HF_PANEL_ATTEMPTED.add(attemptKey)
    _log.warning(
        "panel %s: HF artifact 부재 — 빈 결과(repo=%s, pattern=%s). 데이터 미발행/오경로 가능.",
        code,
        repoId,
        patterns,
    )
    return False


def scopeExpr(col: str = "xbrlClass") -> pl.Expr:
    """xbrlClass → scope ('consolidated' / 'standalone') 파생 Expr (연결/별도 분리 보존).

    DART ACLASS 규약: 별도(개별)는 ``_S`` 표식(BS_S/IS_S2/NT_S_D######), 연결은 ``_C`` 또는
    옛 무접미사(BS/IS2/CF). ``_S`` 없으면 연결. 같은 disclosureKey 라도 scope 로 분리해 BS_C↔BS_S
    병합 차단.

    Args:
        col: xbrlClass 컬럼명 (기본 "xbrlClass").

    Returns:
        ``scope`` 별칭 Utf8 Expr ("consolidated"/"standalone").

    Raises:
        없음.

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"xbrlClass": ["BS_C", "BS_S", "BS", "NT_S_D826385", None]})
        >>> df.select(scopeExpr())["scope"].to_list()
        ['consolidated', 'standalone', 'consolidated', 'standalone', 'consolidated']

    SeeAlso:
        - ``anchorLatest`` — scope 로 연결/별도 병합 방지.
        - ``readWide`` — scope 가 pivot index 의 일부.

    Requires:
        - polars.

    Capabilities:
        - 연결/별도 분리 보존 — 회사내 수평화에서 BS_C↔BS_S 병합 착시 차단.

    Guide:
        - anchorLatest / readWide 내부에서 사용 — 직접 호출 가능(순수 Expr).

    AIContext:
        - 순수 Expr — literal 매칭(특수문자 0).

    LLM Specifications:
        AntiPatterns:
            - ``_S`` regex 부분매칭 금지 — literal 매칭.
            - narrative(null) 에 None scope 금지 — consolidated 기본(pivot index 안정).
        OutputSchema:
            - ``pl.Expr`` (alias "scope", Utf8).
        Prerequisites:
            - polars. xbrlClass 컬럼.
        Freshness:
            - read 파생.
        Dataflow:
            - xbrlClass → null/_S/else → scope.
        TargetMarkets:
            - KR (DART _C/_S 규약). EDGAR 는 별도 scope 규칙.
    """
    c = pl.col(col)
    return (
        pl.when(c.is_null())
        .then(pl.lit("consolidated"))
        .when(c.str.contains("_S", literal=True))
        .then(pl.lit("standalone"))
        .otherwise(pl.lit("consolidated"))
        .alias("scope")
    )


def anchorLatest(df: pl.DataFrame) -> pl.DataFrame:
    """과거 기간을 최신기준으로 수평화 — (disclosureKey, scope) 앵커 정렬 (era drift 흡수).

    같은 disclosure 가 era 마다 xbrlClass(BS→BS_C)·제목이 흔들려 pivot 이 era 별로 행을 쪼갬 →
    ``coalesce(disclosureKey, xbrlClass)`` 앵커(disclosureKey 가 canonical 키면 그 자체가 era-안정,
    build 가 scope-strip 채움)의 ``(_, scope)`` 그룹 **최신 period 라벨**(chapter/sectionLeaf/
    blockLeaf)을 전 기간에 덮어써 한 행으로 정렬. 앵커 null(narrative) 행은 손대지 않음(텍스트 정렬 유지).

    Args:
        df: panel long DataFrame (disclosureKey/xbrlClass/period/chapter/sectionLeaf/blockLeaf 포함).

    Returns:
        ``scope`` 컬럼 추가 + keyed 행의 chapter/sectionLeaf/blockLeaf 최신기준 통일 DataFrame.
        빈/필수컬럼 부재 시 원본 그대로.

    Raises:
        없음.

    Example:
        >>> out = anchorLatest(longDf)  # doctest: +SKIP
        >>> "scope" in out.columns  # doctest: +SKIP
        True

    SeeAlso:
        - ``scopeExpr`` — scope 파생.
        - ``readWide`` — anchorLatest 후 period 축 pivot.

    Requires:
        - polars.

    Capabilities:
        - 회사내 수평화의 era drift 흡수 — 과거 기간이 최신기준 한 행에 정렬(행 쪼개짐 0).

    Guide:
        - readWide 가 wide 변환 전 호출 — 직접 호출 가능.

    AIContext:
        - keyed 행만 라벨 통일, narrative 는 보존 — 무손실.

    When:
        - pivot 이 회사내 wide 변환 전 era drift 를 흡수할 때.

    How:
        - scope 부착 → (anchorKey, scope) 최신 period 라벨 → join 덮어쓰기.

    LLM Specifications:
        AntiPatterns:
            - 앵커 단독 group 금지 — (anchorKey, scope) 페어(연결/별도 병합 방지).
            - raw xbrlClass 를 pivot index 유지 금지 — era drift 로 행 쪼개짐(canonicalKey/scope 대체).
            - 최신 = period 최대 문자열(YYYYQn 정렬, 12월결산화라 안전).
        OutputSchema:
            - 입력 + ``scope``, keyed 행 라벨 최신 통일.
        Prerequisites:
            - disclosureKey/period/xbrlClass 컬럼.
        Freshness:
            - read 파생.
        Dataflow:
            - scope 부착 → keyed (anchorKey,scope) 최신 period 라벨 → join 덮어쓰기.
        TargetMarkets:
            - KR + US 공통.
    """
    if df.is_empty() or "disclosureKey" not in df.columns or "period" not in df.columns:
        return df
    df = df.with_columns(scopeExpr())
    anchorExpr = (
        pl.coalesce([pl.col("disclosureKey"), pl.col("xbrlClass")])
        if "xbrlClass" in df.columns
        else pl.col("disclosureKey")
    )
    df = df.with_columns(anchorExpr.alias("_anchorKey"))
    # scope era-안정화 — 옛 보고서는 xbrlClass=None 이라 scopeExpr 이 별도 주석을 consolidated(기본)로
    # 흔들어 같은 canonicalKey 가 era 별로 쪼개진다. xbrlClass(_S definitive)를 가진 최신 era 의 scope 를
    # 같은 _anchorKey 전 era 에 전파(라벨 anchorLatest 와 동일 원리). xbrlClass 부재 키는 raw 유지.
    if "xbrlClass" in df.columns:
        anchorScope = (
            df.filter(pl.col("_anchorKey").is_not_null() & pl.col("xbrlClass").is_not_null())
            .sort("period")
            .group_by("_anchorKey", maintain_order=True)
            .agg(pl.col("scope").last().alias("_anchorScope"))
        )
        df = (
            df.join(anchorScope, on="_anchorKey", how="left")
            .with_columns(pl.coalesce([pl.col("_anchorScope"), pl.col("scope")]).alias("scope"))
            .drop("_anchorScope")
        )
    keyed = df.filter(pl.col("_anchorKey").is_not_null())
    if keyed.is_empty():
        return df.drop("_anchorKey")
    # 라벨 source 선택 — 최신 period 우선, 단 같은 period 에 canonical(III)·물리첨부((첨부)*)가 공존하면
    # canonical 을 집어야 한다. (첨부)연결재무제표/(첨부)재무제표는 최신 XBRL 뼈대가 아닌 물리 복제 —
    # period asc + 첨부 먼저(canonical 마지막) 정렬 → .last() 가 항상 canonical 라벨(III)을 채택.
    # (이게 없으면 연간보고서의 III↔첨부 중복에서 .last() 가 첨부를 집어 (첨부) chapter 가 혼재 잔존.)
    _attach = pl.col("chapter").cast(pl.Utf8).str.contains("(첨부)", literal=True).fill_null(False)
    latest = (
        keyed.with_columns(_attach.alias("_attach"))
        .sort(["period", "_attach"], descending=[False, True])
        .group_by(["_anchorKey", "scope"], maintain_order=True)
        .agg(
            pl.col("chapter").last().alias("_chapterL"),
            pl.col("sectionLeaf").last().alias("_sectionLeafL"),
            pl.col("blockLeaf").last().alias("_blockLeafL"),
        )
    )
    df = df.join(latest, on=["_anchorKey", "scope"], how="left")
    return df.with_columns(
        pl.when(pl.col("_chapterL").is_not_null())
        .then(pl.col("_chapterL"))
        .otherwise(pl.col("chapter"))
        .alias("chapter"),
        pl.when(pl.col("_sectionLeafL").is_not_null())
        .then(pl.col("_sectionLeafL"))
        .otherwise(pl.col("sectionLeaf"))
        .alias("sectionLeaf"),
        pl.when(pl.col("_blockLeafL").is_not_null())
        .then(pl.col("_blockLeafL"))
        .otherwise(pl.col("blockLeaf"))
        .alias("blockLeaf"),
    ).drop(["_chapterL", "_sectionLeafL", "_blockLeafL", "_anchorKey"])


def alignNotes(df: pl.DataFrame) -> pl.DataFrame:
    """옛 split 주석행(blockLeaf=제목, disclosureKey=null)을 회사 최근 XBRL 뼈대(scope,제목)→NT_ 에 정렬.

    BUILD(``dechunkNotes``)는 옛 통짜 주석을 ``N.제목`` 헤더로 쪼개 제목만 박고 disclosureKey 는 null 로 둔다
    (NT_ 미부여). 본 함수가 read-time 에 null-key 주석행((scope, 정규화제목))에 NT_ 를 **2단 뼈대**로 부여한다 —
    **(1) 회사 자기 native NT_ 주석행**(회사 표준·NT_C_U 회사코드 포함, 우선), **(2) 전역 taxonomy**
    (``noteTaxonomyData`` — cross-company 학습 표준 NT_D, 자기 XBRL 노트 0 회사가 남의 표준코드를 받음, fallback).
    둘 다 같은 표준 코드라 native 와 dedupKeyed 로 병합(뼈대 중복 0). 주석영역(sectionLeaf "주석") 행만 채우고
    어느 뼈대에도 없는 제목·비-주석 narrative 는 null 유지. 정렬 규칙·뼈대 개선이 **재빌드 무관**(read-time) —
    빌드는 분할만 동결. scope 는 native·split 공통으로 chapter/sectionLeaf 의 "연결" 마커(옛 노트는 xbrlClass null
    이라 scopeExpr 가 흔들림) + native 제목 접미사(" - 연결/별도")에서 도출.

    Args:
        df: ``readLong`` long DataFrame (disclosureKey/blockLeaf/chapter/sectionLeaf 컬럼). 전 period 권장
            (뼈대는 최근 native 주석 — period subset 이면 뼈대 부재 가능).

    Returns:
        null-key 주석행이 뼈대 매칭 시 native NT_ 로 채워진 동일 schema DataFrame. 뼈대 부재/매칭 0 이면 원본.

    Raises:
        없음.

    Example:
        >>> aligned = alignNotes(longDf)  # doctest: +SKIP

    SeeAlso:
        - ``build.dechunkNotes`` — 옛 주석을 제목 행으로 분할(null key) — 본 함수가 정렬.
        - ``anchorLatest`` — 정렬 후 era drift 흡수.
        - ``mapper.dedupKeyed`` — 정렬로 native 와 같은 키가 된 행의 중복 축약.

    Requires:
        - polars. (데이터 파일 의존 0 — 같은 df 안의 native 행이 뼈대)

    Capabilities:
        - 옛 주석을 회사 최근 XBRL 뼈대에 read-time 정렬 — 정렬 개선이 재빌드 무관(빌드 동결).

    Guide:
        - ``readWide`` 가 anchorLatest 직전 호출. 직접 호출 가능.

    AIContext:
        - 회사 자기 native 주석이 뼈대(cross-company 아님) — "최근껄로" 정렬, 뼈대 없는 제목은 narrative.

    When:
        - 옛 split 주석행에 최근 XBRL identity 를 부여해 수평화 정렬할 때.

    How:
        - native NT_ 행 (scope, 정규화제목)→NT_ 뼈대 build → null-key 주석행 left join → 매칭 시 disclosureKey 채움.

    LLM Specifications:
        AntiPatterns:
            - 전역 taxonomy 를 회사 자기 native 보다 우선 금지 — own-skeleton 우선, 전역은 주석영역 fallback.
            - 비-주석 narrative 행에 키 부여 금지 — 주석영역(_isNote)만 채움(오정렬 차단).
        OutputSchema:
            - ``alignNotes(df) -> pl.DataFrame`` (null-key 주석행 → 뼈대 매칭 시 NT_).
        Prerequisites:
            - disclosureKey/blockLeaf/chapter/sectionLeaf 컬럼.
        Freshness:
            - read 파생 — 매 호출(재빌드 무관).
        Dataflow:
            - native NT_ → (scope,제목) 뼈대 → null-key 주석행 join → disclosureKey 채움.
        TargetMarkets:
            - KR (DART).
    """
    if df.is_empty() or "disclosureKey" not in df.columns or "blockLeaf" not in df.columns:
        return df
    # native 주석 blockLeaf 는 scope 접미사(" - 연결"/" - 별도")를 단다(예 "재고자산 - 별도"). 옛 split 은 bare 제목.
    # 뼈대·옛행을 같은 키로 맞추려면 (1) 접미사 분리해 bare 제목 정규화, (2) scope = 접미사(native) 또는
    # chapter/sectionLeaf "연결" 마커(옛행, 접미사 없음). 같은 (scope, bare제목) 이 옛↔native 정합.
    bl = pl.col("blockLeaf").fill_null("")
    sufScope = bl.str.extract(r"[-–―]\s*(연결|별도)\s*$", 1)  # native 접미사 scope ("연결"/"별도"/null)
    bareTitle = bl.str.replace(r"\s*[-–―]\s*(연결|별도)\s*$", "")  # 접미사 제거 bare 제목
    secMark = pl.col("chapter").fill_null("") + pl.col("sectionLeaf").fill_null("")
    scope = (
        pl.when(sufScope == "연결")
        .then(pl.lit("consolidated"))
        .when(sufScope == "별도")
        .then(pl.lit("standalone"))
        .when(secMark.str.contains("연결", literal=True))
        .then(pl.lit("consolidated"))
        .otherwise(pl.lit("standalone"))
    )
    from .mapper import NOTE_TITLE_NORM_PATTERN

    normTitle = bareTitle.str.replace_all(NOTE_TITLE_NORM_PATTERN, "")
    isNote = pl.col("sectionLeaf").cast(pl.Utf8).str.contains("주석").fill_null(False)
    tmp = df.with_columns(scope.alias("_alignScope"), normTitle.alias("_alignTitle"), isNote.alias("_isNote"))

    notesOwn = tmp.filter(
        pl.col("disclosureKey").cast(pl.Utf8).str.starts_with("NT_") & (pl.col("_alignTitle").str.len_chars() > 1)
    )
    # 표준 뼈대 = 회사 자기 NT_D(표준 인라인 XBRL, 최신 뼈대) — NT_C_U/NT_S_U(회사고유 첨부코드) 제외.
    # (scope, 정규화제목) → 표준키. 같은 주석이 III(NT_D)·(첨부)(NT_C_U)·옛 split(null)로 갈려도 이 표준키로 통일.
    ownStd = (
        notesOwn.filter(~pl.col("disclosureKey").cast(pl.Utf8).str.contains("_U", literal=True))
        .select(["_alignScope", "_alignTitle", "disclosureKey"])
        .unique(subset=["_alignScope", "_alignTitle"], keep="first")
        .rename({"disclosureKey": "_stdKey"})
    )
    # 자기 native 전체(U 포함) — 표준짝 없는 null-key 주석행의 fallback.
    own = (
        notesOwn.select(["_alignScope", "_alignTitle", "disclosureKey"])
        .unique(subset=["_alignScope", "_alignTitle"], keep="first")
        .rename({"disclosureKey": "_ownKey"})
    )
    # 전역 taxonomy (cross-company 학습 표준 NT_D) — 자기 XBRL 노트 0 회사가 남의 표준코드를 받는다.
    from .build.noteTaxonomyData import NOTE_TAXONOMY

    glob = pl.DataFrame(
        {
            "_alignScope": [k.split("|", 1)[0] for k in NOTE_TAXONOMY],
            "_alignTitle": [k.split("|", 1)[1] for k in NOTE_TAXONOMY],
            "_globKey": list(NOTE_TAXONOMY.values()),
        }
    )
    # 주석영역(_isNote)은 (scope,정규화제목) 표준 뼈대로 **통일** — III(NT_D)·(첨부)(NT_C_U)·옛 split(null)
    # 변종을 하나의 표준 NT_D 로 흡수(anchorLatest 가 그 표준키로 III chapter 에 접음). 표준짝 없는 기존 키
    # (비-주석, 또는 표준화 불가 U-only 주석)는 보존. null-key 표준무 주석은 native(U 포함)→전역 순 fallback.
    return (
        tmp.join(ownStd, on=["_alignScope", "_alignTitle"], how="left")
        .join(own, on=["_alignScope", "_alignTitle"], how="left")
        .join(glob, on=["_alignScope", "_alignTitle"], how="left")
        .with_columns(
            pl.when(pl.col("_isNote") & pl.col("_stdKey").is_not_null())
            .then(pl.col("_stdKey"))
            .when(pl.col("disclosureKey").is_not_null())
            .then(pl.col("disclosureKey"))
            .when(pl.col("_isNote") & pl.col("_ownKey").is_not_null())
            .then(pl.col("_ownKey"))
            .when(pl.col("_isNote") & pl.col("_globKey").is_not_null())
            .then(pl.col("_globKey"))
            .otherwise(pl.col("disclosureKey"))
            .alias("disclosureKey")
        )
        .drop(["_alignScope", "_alignTitle", "_isNote", "_stdKey", "_ownKey", "_globKey"])
    )


# (첨부) 물리 재무첨부 흡수 — sectionPath 에서 감지(공백 변형 무시), 정규 재무섹션 sectionLeaf 로 relabel.
_ATTACH_TAG = "(첨부)"


def absorbAttached(df: pl.DataFrame) -> pl.DataFrame:
    """옛 연차보고서의 ``(첨부)연결재무제표``/``(첨부)재무제표`` 물리첨부를 정규 재무섹션으로 흡수(relabel).

    최신 보고서는 연결/별도 본표가 인라인 XBRL(BS_C/IS_C/CF_C·BS_S 등) 로 ``2. 연결재무제표``/``4. 재무제표``
    에 들어오지만, 옛 연차본은 같은 본표를 **XBRL 태깅 없는 물리 첨부**(``(첨부)연 결 재 무 제 표``)로 실어
    ``xbrlClass``/``disclosureKey`` 가 null 이라 ``anchorLatest`` 가 못 잡는다 → ``(첨부)`` 가 ghost 섹션으로 잔존,
    게다가 ``spine.SPINE`` 에 직접 등재돼(spineOrder) III 머리에 부유한다. 본 함수가 read-time 에 ``sectionPath``
    (전 깊이 truth, 공백 변형 무시)에서 ``(첨부)`` + 재무제표류를 감지해 ``chapter``→III, ``sectionLeaf``→
    연결 ``2. 연결재무제표``/별도 ``4. 재무제표`` (주석 하위는 ``3.``/``5. … 주석``) 로 relabel 한다. 정규 식별자가 되어
    collapse/pivot 이 정규 섹션으로 모으고 ghost 부유가 자연 해소. ``alignNotes`` 와 동형(read-time, 재빌드 무관).

    Args:
        df: ``canonicalChapterExpr`` 적용 후 long DataFrame (chapter/sectionLeaf/sectionPath 컬럼).

    Returns:
        ``(첨부)`` 재무첨부 행의 chapter/sectionLeaf 가 정규 재무섹션으로 relabel 된 동일 schema DataFrame.
        빈/필수컬럼 부재 시 원본.

    Raises:
        없음.

    Example:
        >>> out = absorbAttached(longDf)  # doctest: +SKIP

    SeeAlso:
        - ``anchorLatest`` — keyed era drift 흡수(본 함수는 narrative 물리첨부 흡수 보완).
        - ``readWide`` — canonicalChapter 직후 본 함수 호출.

    Requires:
        - polars. sectionPath 컬럼(없으면 원본 반환).

    Capabilities:
        - 옛 물리 재무첨부를 XBRL 정규 재무섹션으로 read-time 흡수 — ghost 섹션·spine 부유 제거(재빌드 무관).

    Guide:
        - readWide 가 canonicalChapter 직후 호출. 직접 호출 가능(순수).

    AIContext:
        - relabel 만(드롭 0) — (첨부) 본문은 정규 섹션의 과거 period 행으로 합류.

    When:
        - 옛 연차본의 물리 재무첨부를 정규 재무섹션으로 수평화 흡수할 때.

    How:
        - sectionPath(공백제거)에서 (첨부)+재무제표 감지 → 연결/별도·주석 분기 → chapter/sectionLeaf relabel.

    LLM Specifications:
        AntiPatterns:
            - (첨부) 행 드롭 금지 — relabel(데이터 손실 0).
            - 정규 "2.연결재무제표"(sectionPath 에 (첨부) 없음) 오감지 금지 — sectionPath 의 (첨부) 토큰 필수.
        OutputSchema:
            - ``absorbAttached(df) -> pl.DataFrame`` (chapter/sectionLeaf relabel).
        Prerequisites:
            - chapter/sectionLeaf/sectionPath 컬럼.
        Freshness:
            - read 파생 — 매 호출(재빌드 무관).
        Dataflow:
            - sectionPath(no-ws) → (첨부)+재무제표 감지 → 연결/별도·주석 → chapter/sectionLeaf relabel.
        TargetMarkets:
            - KR (DART).
    """
    if df.is_empty() or "sectionLeaf" not in df.columns or "sectionPath" not in df.columns:
        return df
    pathNoWs = pl.col("sectionPath").fill_null("").str.replace_all(_WS_RE, "")
    isAttach = pathNoWs.str.contains(_ATTACH_TAG, literal=True) & pathNoWs.str.contains("재무제표", literal=True)
    isConsol = pathNoWs.str.contains("연결", literal=True)
    isNote = pl.col("sectionLeaf").fill_null("").str.contains("주석", literal=True)
    newSection = (
        pl.when(isAttach & isNote & isConsol)
        .then(pl.lit("3. 연결재무제표 주석"))
        .when(isAttach & isNote)
        .then(pl.lit("5. 재무제표 주석"))
        .when(isAttach & isConsol)
        .then(pl.lit("2. 연결재무제표"))
        .when(isAttach)
        .then(pl.lit("4. 재무제표"))
        .otherwise(pl.col("sectionLeaf"))
    )
    newChapter = pl.when(isAttach).then(pl.lit("III. 재무에 관한 사항")).otherwise(pl.col("chapter"))
    cols = [newChapter.alias("chapter"), newSection.alias("sectionLeaf")]
    # 섹션 위치는 정규(XBRL) 행이 잡아야 한다 — 흡수된 옛 물리첨부 행은 blockOrder 를 크게 밀어 _skel 정렬에서
    # 섹션 뒤로(섹션이 앞으로 끌려가는 회귀 차단). 같은 offset 이라 흡수행 상호 순서·본문 join 은 불변.
    if "blockOrder" in df.columns:
        cols.append(
            pl.when(isAttach).then(pl.col("blockOrder") + 1_000_000).otherwise(pl.col("blockOrder")).alias("blockOrder")
        )
    return df.with_columns(cols)


# narrative 섹션 라벨을 SPINE(최신 필링 골격) 등재 라벨로 정규화 — era 라벨 변종 통일.
_NARR_SEP = "␟"  # rowIdentity NARR::{chapter}␟{sectionLeaf} 와 동일 구분자
_NARR_NUM_RE = r"^\s*\d+(-\d+)?\.?\s*"  # 선행 절 번호("6. "/"7-1. ")
_NARR_ETC_RE = r"\s*등\s*$"  # 후행 "등"(era 표기 변종)
_SELF_HDR_RE = r"^\s*(?:[IVXLCDM]+\s*\.|【)"  # 챕터-자기행 헤더형(로마numeral·【) — 번호절 비대상
_SPINE_NARR_MAP: dict[str, str] | None = None
_ERA_ALIAS_MAP: dict[str, str] | None = None


def _narrativeCore(leaf: str) -> str:
    """섹션 라벨 → 제목 코어 (선행 번호·후행 '등' 제거 + NOTE_TITLE_NORM 정규화) — Python str 판.

    ``_narrativeCoreExpr`` 의 scalar 짝(SPINE 룩업 dict 구축용). 둘이 byte-identical 코어를 내야 매칭 성립.
    예) "6. 배당에 관한 사항 등" → "배당에관한사항", "8. 기타 재무에 관한 사항" → "기타재무에관한사항".
    """
    import re

    from .mapper import NOTE_TITLE_NORM_PATTERN

    s = re.sub(_NARR_NUM_RE, "", leaf or "")
    s = s.strip()
    s = re.sub(_NARR_ETC_RE, "", s)
    return re.sub(NOTE_TITLE_NORM_PATTERN, "", s)


def _narrativeCoreExpr(col: str | pl.Expr = "sectionLeaf") -> pl.Expr:
    """섹션 라벨(컬럼명 또는 Expr) → 제목 코어 Expr (``_narrativeCore`` 의 polars 짝). 번호·'등' strip + 정규화."""
    from .mapper import NOTE_TITLE_NORM_PATTERN

    e = pl.col(col) if isinstance(col, str) else col
    return (
        e.fill_null("")
        .str.replace(_NARR_NUM_RE, "")
        .str.strip_chars()
        .str.replace(_NARR_ETC_RE, "")
        .str.replace_all(NOTE_TITLE_NORM_PATTERN, "")
    )


def sectionLeafConvergeExpr() -> pl.Expr:
    """TOC 표준 수렴 3룰의 **단일 Expr** — read(``anchorNarrativeToSpine``)·검열(``audit``) 공용 SSOT.

    chapter 가 canonical 로 확정된 frame 위에서 ``sectionLeaf`` 를 표준 라벨로 접는다:
    ① 챕터-자기행(로마/【 헤더 + canonical 라벨=자기 chapter) → chapter 라벨
    ② SPINE 코어 일치 = 표면 표기 정규화 ③ era-alias(서식개정, 운영자 수동). 미매칭 원본(honest).
    Expr 라 lazy frame 전종목 스캔에도 그대로 적용 가능(검열기 전제).

    Returns:
        ``sectionLeaf`` 별칭 Utf8 Expr.

    Raises:
        없음 — 순수 Expr 빌더. 미매칭 라벨은 예외 없이 원본 유지(honest)이며,
        ``chapter``/``sectionLeaf`` 컬럼 부재는 적용 시점에 polars ColumnNotFoundError.

    Example:
        >>> from dartlab.providers.dart.panel.read import sectionLeafConvergeExpr
        >>> frame.with_columns(sectionLeafConvergeExpr())  # doctest: +SKIP
    """
    from .canonical import _canonLabelExpr

    leaf = pl.col("sectionLeaf")
    isHdr = leaf.fill_null("").str.contains(_SELF_HDR_RE)
    selfFixed = pl.when(isHdr & (_canonLabelExpr(leaf) == pl.col("chapter"))).then(pl.col("chapter")).otherwise(leaf)
    key = pl.col("chapter").fill_null("") + pl.lit(_NARR_SEP) + _narrativeCoreExpr(selfFixed)
    canon = key.replace_strict(_spineNarrativeMap(), default=None, return_dtype=pl.Utf8)
    alias = key.replace_strict(_eraAliasMap(), default=None, return_dtype=pl.Utf8)
    return pl.coalesce([canon, alias, selfFixed]).alias("sectionLeaf")


def _spineNarrativeMap() -> dict[str, str]:
    """SPINE 의 narrative 라벨 → ``{f'{chapter}␟{코어}': 정식 sectionLeaf}`` 룩업 (module-level 1회 캐시).

    SPINE 은 최신 Q4 사업보고서에서 구운 골격이라 등재 narrative 라벨 = "가장 최근 필링 구조(핵)".
    같은 chapter·코어의 옛 era 변종을 이 정식 라벨로 통일하는 화이트리스트. 첫 등장 우선(SPINE=정부순서).
    ``NARRATIVE_ERA_ALIASES``(서식개정 옛코어→현행코어, 운영자 수동)를 같은 정식 라벨로 추가 등재해
    실질 명칭변경(2018 외감법 V 재편 등)도 수렴 — 현행코어가 SPINE 에 없으면 미등재(데이터가 가부 결정).
    """
    global _SPINE_NARR_MAP
    if _SPINE_NARR_MAP is not None:
        return _SPINE_NARR_MAP
    from .spine import SPINE

    m: dict[str, str] = {}
    for ident in SPINE:
        if not ident.startswith("NARR::"):
            continue
        chap, sep, leaf = ident[len("NARR::") :].partition(_NARR_SEP)
        if not sep:
            continue
        m.setdefault(f"{chap}{_NARR_SEP}{_narrativeCore(leaf)}", leaf)
    _SPINE_NARR_MAP = m
    return m


def _eraAliasMap() -> dict[str, str]:
    """서식개정 era-alias 만 — ``{f'{chapter}␟{옛코어}': 현행 SPINE 라벨}`` (keyed 행에도 적용되는 부분집합).

    일반 SPINE 코어매칭(표면 변형)은 narrative 한정이지만, 운영자 큐레이션 era-alias 는 **단종 키 가족**
    (옛 INS_* 감사표 등 — 신서식은 같은 내용을 narrative 로 실음)의 좀비 섹션도 현행 TOC 노드로 수렴해야
    하므로 keyed 행의 *그룹핑 라벨*(sectionLeaf)에도 적용한다. keyed 식별(disclosureKey)은 불변.
    """
    global _ERA_ALIAS_MAP
    if _ERA_ALIAS_MAP is not None:
        return _ERA_ALIAS_MAP
    from .canonical import NARRATIVE_ERA_ALIASES

    spine = _spineNarrativeMap()
    m: dict[str, str] = {}
    for chap, aliases in NARRATIVE_ERA_ALIASES.items():
        for oldCore, newCore in aliases.items():
            label = spine.get(f"{chap}{_NARR_SEP}{newCore}")
            if label is not None:
                m[f"{chap}{_NARR_SEP}{oldCore}"] = label
    _ERA_ALIAS_MAP = m
    return m


def anchorNarrativeToSpine(df: pl.DataFrame) -> pl.DataFrame:
    """narrative 섹션 라벨을 SPINE(최신 필링 골격) 등재 라벨로 정규화 — era 변종을 "최신이 핵"으로 통일.

    ``anchorLatest`` 가 keyed 행(disclosureKey 보유 재무제표)을 회사-자기 최신 period 라벨로 통일하지만,
    narrative 섹션(배당·증권발행·기타재무 등, disclosureKey null)은 손대지 않아 era 별 라벨 변종이 별도 행으로
    잔존한다 ("6. 배당에 관한 사항"(현행) vs "6. 배당에 관한 사항 등"(옛), "6. 기타 재무에 관한 사항"(옛 번호) vs
    "8. 기타 재무에 관한 사항"(현행 번호)). 정부 서식 개정으로 라벨·번호가 드리프트한 것. 본 함수가 read-time 에
    narrative ``sectionLeaf`` 를 **같은 chapter 의 SPINE 등재 라벨**(제목 코어 일치)로 덮어써 통일한다 — SPINE 이
    최신 필링 골격이라 곧 운영자가 말한 "가장 최근 XBRL 이 핵". ``canonicalChapterExpr`` 이 chapter 를 14노드로
    bounded 흡수하는 것과 동형(SPINE 화이트리스트 매칭만, 자유 fuzzy 0). 번호 드리프트(6→8)는 SPINE 라벨 전체를
    채택하므로 자동 해소(_secNum 도 새 번호).

    3중 수렴 (전부 bounded·항목 동일성 구조 보장 — 자유 fuzzy 0, "확신오정렬 > 정렬실패". keyed/narrative 균일
    적용 — keyed 의 sectionLeaf 는 순수 그룹핑 라벨(wide 식별 = disclosureKey)이라 셀 식별·anchorLatest 무충돌):
        ① **챕터-자기행**: 헤더형(로마numeral·【 prefix) sectionLeaf 의 canonical 라벨이 자기 chapter 와 일치하면
           chapter 라벨로 ("IV. 감사인의 감사의견 등"→"V. 회계감사인의 감사의견 등", "X. 이해관계자와의 거래내용"→
           "X. 대주주 등과의 거래내용"). CANONICAL_L1 키워드 재사용 — 별도 리스트 0.
        ② **SPINE 코어 일치** = 표면 표기 정규화(같은 chapter·같은 코어 = 같은 항목 *정의*) — 번호·후행'등'·
           문장부호 변형 통일. keyed 도 era 별 키 단절("6.배당 등"[옛 keyed]↔"6.배당") 시 필요.
        ③ **era-alias**(``NARRATIVE_ERA_ALIASES`` 서식개정 실질 명칭변경, 운영자 수동) — 단종 키 가족(옛 INS_*
           감사표, 신서식은 같은 내용 narrative)의 좀비 섹션 포함 수렴. 같은 번호의 *다른 항목*(옛 I.5
           의결권현황 vs 현행 I.5 정관)은 등재 금지 — 분리 유지(honest).

    Args:
        df: ``canonicalChapterExpr``·``absorbAttached`` 적용 후 long DataFrame (chapter/sectionLeaf/disclosureKey).

    Returns:
        narrative 행의 sectionLeaf 가 SPINE 등재 라벨로 통일된 동일 schema DataFrame. SPINE 비매칭·keyed 행은 원본.

    Raises:
        없음.

    Example:
        >>> out = anchorNarrativeToSpine(longDf)  # doctest: +SKIP

    SeeAlso:
        - ``anchorLatest`` — keyed era drift 흡수(본 함수는 narrative 보완).
        - ``spine.SPINE`` — 최신 필링 골격(핵) 출처.
        - ``readWide`` — absorbAttached 직후·leafSeq 직전 호출.

    Requires:
        - polars. spine.SPINE. mapper.NOTE_TITLE_NORM_PATTERN.

    Capabilities:
        - 옛 era narrative 섹션 라벨을 최신 SPINE 골격으로 read-time 통일 — cross-era 한 행 수평화(재빌드 무관).

    AIContext:
        - SPINE 화이트리스트 bounded 매핑 — 코어 미등재는 분리 유지("확신오정렬 > 정렬실패"). keyed 행 불변.

    LLM Specifications:
        AntiPatterns:
            - 자유 fuzzy(Levenshtein/Jaccard) 금지 — SPINE 등재 코어 일치 + 운영자 era-alias 만(오병합 차단).
            - chapter cross 매칭 금지 — 룩업 키에 chapter 포함(다른 챕터 같은 번호 분리).
            - 같은 번호 다른 항목(의결권현황 vs 정관) alias 등재 금지 — 분리가 정답(병합 = 진짜 정보손실).
            - disclosureKey(셀 식별) 변경 금지 — 본 함수는 그룹핑 라벨(sectionLeaf)만 통일.
        OutputSchema:
            - ``anchorNarrativeToSpine(df) -> pl.DataFrame`` (narrative sectionLeaf SPINE 통일).
        Prerequisites:
            - chapter/sectionLeaf/disclosureKey 컬럼. SPINE.
        Freshness:
            - read 파생 — 매 호출(재빌드 무관). SPINE 재생성 시 핵 갱신.
        Dataflow:
            - (chapter, 제목코어) → SPINE 라벨 룩업 → narrative 행 sectionLeaf 덮어쓰기.
        TargetMarkets:
            - KR (DART 정부 서식).
    """
    if df.is_empty() or "sectionLeaf" not in df.columns or "chapter" not in df.columns:
        return df
    spineMap = _spineNarrativeMap()
    if not spineMap:
        return df
    # 세 룰 모두 *항목 동일성이 구조적으로 보장*되는 bounded 수렴이라 keyed/narrative 구분 없이 전 행 균일 적용
    # — keyed 의 sectionLeaf 는 순수 그룹핑 라벨(wide 식별 = disclosureKey)이라 셀 식별·anchorLatest 와 무충돌.
    # 룰 본체 = ``sectionLeafConvergeExpr``(단일 Expr SSOT — 검열기 ``audit`` 와 공용).
    return df.with_columns(sectionLeafConvergeExpr())


def readLong(code: str, *, marketNs: str = "kr", periods: list[str] | None = None) -> pl.DataFrame | None:
    """panel long format read + disclosureKey 보장 (period 파일 prune).

    Args:
        code: 종목코드.
        marketNs: 시장 namespace ("kr" / "us").
        periods: 특정 period 만(파일 단위 prune — 대형 종목 메모리 핸들). None = 전체.

    Returns:
        long DataFrame (14-col + disclosureKey) 또는 None (artifact 없음/빈/read 실패).

    Raises:
        PanelArtifactFetchError: 부재 artifact의 원격 조달 실패.
        PanelArtifactReadError: 손상 parquet 읽기 또는 정리 실패.
        PanelSchemaError: artifact 컬럼 계약 위반.

    Example:
        >>> df = readLong("005930", periods=["2025Q4"])  # doctest: +SKIP

    SeeAlso:
        - ``readWide`` — 본 long 을 wide 수평화.
        - ``mapper.resolveBatch`` — disclosureKey fallback.

    Requires:
        - polars. panel artifact. (fallback 시) native canonicalKey 규칙(mapper, 데이터 0).

    Capabilities:
        - 한 회사 전(또는 일부) 기간 long 본문 read — disclosureKey 보장, period 파일 prune.

    Guide:
        - readWide / Panel.long() 이 호출. 직접 호출 가능.

    AIContext:
        - build 가 채운 disclosureKey 사용, 옛 artifact(전부 null)만 fallback resolve.

    When:
        - 한 회사 long 본문 + disclosureKey 가 필요할 때.

    How:
        - dir glob → (periods filter) → read_parquet → disclosureKey null 검사 → (fallback) resolveBatch.

    LLM Specifications:
        AntiPatterns:
            - 매 read resolveBatch 금지 — build 가 채운 값 우선, 전부 null 일 때만.
        OutputSchema:
            - ``pl.DataFrame | None`` (14-col + disclosureKey).
        Prerequisites:
            - panel artifact.
        Freshness:
            - 매 호출 read.
        Dataflow:
            - dir glob → (periods filter) → read_parquet → disclosureKey 보장.
        TargetMarkets:
            - KR + US.
    """
    # 다회사 루프 OOM 가드 — panel 은 회사당 통째 read(Polars Rust 힙 누수). 로드 전 RSS 확인 + 임계 시 GC.
    from dartlab.core.memory import checkMemoryAndGc

    checkMemoryAndGc(f"panel:{code}")
    code = code.upper() if marketNs == "us" else code  # EDGAR ticker 대소문자 무관 (build 가 upper 저장)
    ensurePanelFromHf(code, marketNs)  # artifact 부재 시 HF lazy 다운로드 (로컬 우선, 단일 자동로드)
    d = _panelDir(code, marketNs)
    flat = d.parent / f"{code}.parquet"  # flat: data/{dart|edgar}/panel/{code}.parquet (회사당 1파일)
    # WASM 세이프 read: pyodide 는 pl.read_parquet 비활성이라 pyarrow 경유(readParquetSafe).
    # 함수 스코프 lazy import (R2 콜드<1s 유지 + core.dataLoader cycle 회피).
    from dartlab.core.dataLoader import readParquetSafe

    try:
        if flat.exists():
            df = readParquetSafe(str(flat))
            if periods:
                df = df.filter(pl.col("period").is_in(list(periods)))  # 1파일 → 행 필터(파일 prune 대체)
        elif d.exists():  # 하위호환(옛 period-shard 폴더)
            files = sorted(d.glob("*.parquet"))
            if periods:
                files = [f for f in files if f.stem in set(periods)]
            if not files:
                return None
            df = readParquetSafe([str(f) for f in files])
        else:
            return None
    except (pl.exceptions.PolarsError, OSError) as exc:
        # 손상(부분 다운로드 등) 의심 — 손상 flat 삭제 + 시도마킹 해제해 다음 호출이 재다운로드.
        # (옛 코드는 손상 파일 + _HF_PANEL_ATTEMPTED 로 세션 내내 고정됐다.)
        _log.warning("panel read 실패 %s: %s — 손상 의심, 정리 후 재시도 가능", code, exc)
        try:
            if flat.exists():
                flat.unlink()
            _HF_PANEL_ATTEMPTED.discard(f"{marketNs}:{code}")
        except OSError as cleanupExc:
            error = PanelArtifactReadError(code, marketNs, "손상 cache 정리", cleanupExc)
            error.add_note(f"선행 읽기 실패: {type(exc).__name__}: {exc}")
            raise error from cleanupExc
        raise PanelArtifactReadError(code, marketNs, "읽기", exc) from exc
    if df.is_empty():
        return None
    if "disclosureKey" not in df.columns or df["disclosureKey"].null_count() == df.height:
        from .mapper import resolveBatch

        if "disclosureKey" in df.columns:
            df = df.drop("disclosureKey")
        # native canonicalKey (옛 artifact·미빌드 fallback — build 가 채우면 미도달).
        df = resolveBatch(df, marketNs=marketNs)
    return df


def readWide(
    code: str,
    *,
    marketNs: str = "kr",
    periods: list[str] | None = None,
    tag: bool = True,
) -> pl.DataFrame | None:
    """panel wide pivot — index=(canonical key), columns=period (회사내 수평화 + tag strip).

    Args:
        code: 종목코드.
        marketNs: 시장 namespace.
        periods: 특정 period 만(파일 prune). None = 전체.
        tag: True(기본) 면 contentRaw 원본 XML 무손실(R4), False 면 정렬된 wide 셀에 태그 strip(plain).

    Returns:
        wide DataFrame. row identity = (chapter, sectionLeaf, blockLeaf, disclosureKey, scope),
        열 = period (cell = 본문). 또는 None (artifact 없음/빈/pivot 실패).

    Raises:
        PanelArtifactFetchError: 부재 artifact의 원격 조달 실패.
        PanelArtifactReadError: parquet 읽기 실패.
        PanelSchemaError: 필수 컬럼 누락 또는 pivot 실패.

    Example:
        >>> readWide("005930", tag=False, periods=["2025Q4", "2024Q4"])  # doctest: +SKIP

    SeeAlso:
        - ``readLong`` — long 입력.
        - ``anchorLatest`` — 최신기준 정렬.
        - ``Panel`` — 본 함수를 wide 본체로 wrap.

    Requires:
        - polars. panel artifact.

    Capabilities:
        - 한 회사 다기간을 항목 행 × period 열로 정렬 — era drift 흡수.
        - tag=False 면 pivot·정렬 후 wide 셀 1회 strip → plain(raw 의 ~22%, 표시·메모리 경량, 2.8x).

    Guide:
        - Panel.__init__ 이 본 함수로 wide 생성. 직접 호출 가능.

    AIContext:
        - contentRaw 는 blockOrder 순 join(무손실), anchorLatest 후 pivot, spine 정렬.
        - tag=False strip 은 정렬된 wide 셀에 1회 — collapse fragment strip 보다 2.8x.

    When:
        - 한 회사 다기간을 항목 × period 로 수평화할 때.

    How:
        - readLong → alignNotes → anchorLatest → dedupKeyed → canonicalChapter → collapse → pivot → canonical rank.

    LLM Specifications:
        AntiPatterns:
            - contentRaw 다중블록 first 금지 — blockOrder 순 join(무손실).
            - xbrlClass pivot index 금지 — scope 대체.
            - 챕터 임의 재구성 금지 — canonical 14 노드 bounded 매핑((첨부)→III).
            - collapse(long fragment) 단계 strip 금지 — pivot·정렬 후 wide 셀 1회(2.8x).
        OutputSchema:
            - ``pl.DataFrame | None`` (index cols + period 열).
        Prerequisites:
            - panel artifact + period 컬럼.
        Freshness:
            - 매 호출.
        Dataflow:
            - readLong → alignNotes → anchorLatest → dedupKeyed → canonicalChapter → collapse → pivot → canonical rank.
        TargetMarkets:
            - KR + US.
    """
    from .mapper import dedupKeyed

    long = readLong(code, marketNs=marketNs, periods=periods)
    if long is None or long.is_empty():
        return None
    if "contentRaw" not in long.columns:
        raise PanelSchemaError(f"panel {code}: 필수 컬럼 누락: contentRaw")
    long = alignNotes(long)  # 옛 split 주석행(null key) → 회사 최근 XBRL 뼈대 NT_ 정렬 (read-time, 재빌드 무관)
    long = anchorLatest(long)
    long = dedupKeyed(long)  # 본문+첨부 중복 keyed 행 → (key,scope,leafType,period) 당 1개 (collapse 증식 차단)
    # canonical L1 챕터 복원·접기 — sectionPath 깊은 canonical 원소로 **붕괴된 chapter 복원**(DART era 가 III~XII
    # 를 II 아래 mis-nesting → walker chapter 붕괴) + (첨부)→III 흡수 + 구조신호 0 인 NT_ 주석 orphan III 복원
    # ((첨부) flat <P ID> 주석은 SECTION 부재로 chapter·sectionPath 공백 — NT_ 표준코드가 정의상 재무주석).
    # 회사간 비교축. READ 파생(재빌드 무관).
    from .canonical import canonicalChapterExpr

    if "chapter" in long.columns:
        pathCol = "sectionPath" if "sectionPath" in long.columns else "chapter"
        noteKeyCol = "disclosureKey" if "disclosureKey" in long.columns else None
        long = long.with_columns(canonicalChapterExpr("chapter", pathCol, noteKeyCol=noteKeyCol).alias("chapter"))
    # (첨부) 물리 재무첨부((첨부)연결재무제표·(첨부)재무제표) → 정규 재무섹션(2.연결재무제표/4.재무제표 …)으로 흡수.
    # 옛 연차본 물리첨부(XBRL 태깅 0 → anchor 못 잡음)가 ghost 섹션·spine 부유로 남는 것을 read-time 정규화.
    long = absorbAttached(long)
    # narrative 섹션 라벨을 SPINE(최신 필링 골격=핵) 등재 라벨로 정규화 — era 변종("6.배당" vs "6.배당 등",
    # 옛 "6.기타재무" vs 현행 "8.기타재무") 통일. leafSeq·collapse·pivot 전이라 통일 라벨이 row identity 에
    # 반영돼 한 행으로 모이고 orderBySpine 의 _spOrder 를 정상 획득(챕터 말미 부유 해소).
    long = anchorNarrativeToSpine(long)
    # narrative 수평화 — 과거 뭉태기 leaf 를 **섹션 내 문서위치**로 정렬(leafSeq). 각 leaf(표·텍스트)가 별도
    # 행이라 표↔표 안 뭉침(재뭉침 0). 같은 섹션의 같은 위치 표가 기간 간 한 행(매출실적 등 안정위치 표는 정렬).
    # 위치정렬은 안정위치 표엔 효과적이나 삽입 누적 시 drift — 표구조-aware fuzzy 정렬은 후속 정공(operation.architecture).
    # keyed(재무제표)는 disclosureKey 가 식별 → seq=0(불변).
    if "blockOrder" in long.columns:
        seq = (
            pl.when(pl.col("disclosureKey").is_null())
            .then(pl.col("blockOrder").rank("ordinal").over(["chapter", "sectionLeaf", "leafType", "period"]))
            .otherwise(0)
            .cast(pl.Int64)
        )
        long = long.with_columns(seq.alias("leafSeq"))
    indexCols = [c for c in _INDEX_COLS if c in long.columns]
    missingIdx = [c for c in _INDEX_COLS if c not in long.columns]
    if missingIdx:
        # 옛 schema artifact — 인덱스 컬럼 누락 시 조용히 행이 collapse(다른 행이 한 행으로 병합,
        # silent 오답)된다. 명시 경고로 관측화(forceUpdate 재다운로드 유도).
        _log.warning("panel %s: 인덱스 컬럼 누락 %s — 옛 schema 의심, 행 collapse 가능", code, missingIdx)
    if "leafSeq" in long.columns:
        indexCols = [*indexCols, "leafSeq"]
    if not indexCols or "period" not in long.columns:
        missing = [*missingIdx, *(["period"] if "period" not in long.columns else [])]
        raise PanelSchemaError(f"panel {code}: 수평화 필수 컬럼 누락: {sorted(set(missing))}")
    # collapse 는 항상 raw join (태그 무손실). strip(tag=False)은 pivot·정렬 후 wide 셀에 1회
    # — 작은 fragment 수천개 정규식보다 큰 셀 1회가 2.8x 빠름(byte-identical 실측), raw wide
    # 2중 materialize 도 회피(strip 은 같은 wide 를 in-place with_columns).
    joined = pl.col("contentRaw").str.join("")
    try:
        collapsed = (
            long.sort("blockOrder")
            .group_by([*indexCols, "period"], maintain_order=True)
            .agg(joined.alias("contentRaw"), pl.col("blockOrder").min().alias("_bo"))
        )
        # skeleton 표시순서 = **최신 *연간*(Q4) 보고서의 blockOrder**(뼈대 기준). 분기보고서(Q1~Q3)는 구조가
        # 빈약(사업의 내용 등 생략)이라 절대 최신 분기를 기준 삼으면 narrative leaf 가 거기 없어 muddle — 전체구조를
        # 가진 최신 사업보고서(Q4)가 뼈대. Q4 부재 시 절대 최신. 최신 뼈대에 없는 과거전용 leaf 는 _skel null →
        # 뒤로(_skelOld 차순서). "최신 뼈대 기준, 과거 흡수" 구현.
        allP = collapsed.select(pl.col("period").unique()).to_series().to_list()
        q4 = [p for p in allP if p.endswith("Q4")]
        latestP = max(q4) if q4 else max(allP)
        skelOrder = collapsed.filter(pl.col("period") == latestP).select([*indexCols, pl.col("_bo").alias("_skel")])
        skelOld = (
            collapsed.sort("period")
            .group_by(indexCols, maintain_order=True)
            .agg(pl.col("_bo").last().alias("_skelOld"))
        )
        wide = collapsed.drop("_bo").pivot(
            values="contentRaw", index=indexCols, on="period", aggregate_function="first"
        )
        wide = wide.join(skelOrder, on=indexCols, how="left").join(skelOld, on=indexCols, how="left")
    except (pl.exceptions.ComputeError, pl.exceptions.ShapeError) as exc:
        raise PanelSchemaError(f"panel {code}: pivot 실패: {type(exc).__name__}: {exc}") from exc
    wide = orderBySpine(wide, indexCols)
    if not tag:
        periodCols = [c for c in wide.columns if c not in indexCols]
        wide = wide.with_columns([_stripExpr(c) for c in periodCols])
    return wide


def orderBySpine(wide: pl.DataFrame, indexCols: list[str]) -> pl.DataFrame:
    """wide 행을 정부 뼈대(SPINE) 순서로 정렬 + period 열 최신순 배치.

    각 행의 ``rowIdentity`` 로 ``SPINE`` 을 조회해 **(chapterRank 우선, spineOrder 차선)** 정렬 —
    챕터(I~XII) 단위로 모은 뒤 챕터 내 정부 문서순서. chapterRank 우선이라 정부가 본문 중간에
    물리 삽입한 '(첨부)재무제표' 같은 블록은 흩어지지 않고 자기 챕터로 모인다(한눈에 정돈된 격자).
    spine 미등재 행은 chapter 말미(nulls_last). period 열은 최신순(2026Q1 좌측), index 컬럼이 먼저.

    Args:
        wide: pivot 직후 wide DataFrame (index 컬럼 + period 열).
        indexCols: 행 식별 컬럼 (PIVOT_INDEX 교집합).

    Returns:
        SPINE 순서 정렬 + period 최신순 wide. spine 빈/identity 컬럼 부재 시 원본 컬럼순.

    Raises:
        없음.

    Example:
        >>> orderBySpine(wide, ["disclosureKey", "chapter", "sectionLeaf"])  # doctest: +SKIP

    SeeAlso:
        - ``mapper.rowIdentityExpr`` — 행 identity 산출.
        - ``spine.SPINE`` — 정부 서식 순서.

    Requires:
        - polars. spine.SPINE (없으면 정렬 skip).

    Capabilities:
        - 정부 문서순서로 wide 행 정렬 — blockOrder 재발견(기간 리셋) 없이 정부 서식 truth.

    Guide:
        - readWide 가 pivot 후 호출. 직접 호출 가능.

    AIContext:
        - SPINE module-level dict O(1) lookup — 누적 0.

    When:
        - wide 행을 정부 뼈대 순서로 세우고 period 열을 최신순으로 배치할 때.

    How:
        - rowIdentityExpr → SPINE map(chapterRank, spineOrder) → sort → period 최신순 select.

    LLM Specifications:
        AntiPatterns:
            - blockOrder 로 행 정렬 금지 — 기간 리셋(정렬 truth=SPINE).
            - spine 미등재에 임의 순서 금지 — nulls_last(chapter 말미).
        OutputSchema:
            - ``pl.DataFrame`` (정부순서 행 + 최신순 period 열).
        Prerequisites:
            - polars. SPINE dict.
        Freshness:
            - SPINE 재생성 시 반영.
        Dataflow:
            - rowIdentity → SPINE → (chapterRank, spineOrder) sort → period 최신순.
        TargetMarkets:
            - KR + US 공통.
    """
    from .canonical import canonicalRankExpr
    from .mapper import rowIdentityExpr
    from .spine import SPINE

    helperCols = {"_skel", "_skelOld", "leafSeq", "_canonRank", "_spOrder", "_rowIdentity", "_secNum", "_secSub"}
    periodCols = sortPeriods([c for c in wide.columns if c not in indexCols and c not in helperCols])
    orderedCols = [*indexCols, *reversed(periodCols)]  # period 최신순(좌측), 헬퍼(_skel 등)는 제외
    if "chapter" not in wide.columns or "sectionLeaf" not in wide.columns:
        return wide.select([c for c in orderedCols if c in wide.columns])
    # 정렬키 = (1) canonical 14 노드 chapter rank ((첨부)→III 가 III 로 모임), (2) **섹션 번호**("2. …"→2,
    # "7-1. …"→7,1) — 정부 서식의 절 번호가 챕터 내 1차 순서(흡수된 (첨부)·표지(COVER2 등)가 옛 spine 으로
    # 섹션을 끌어오는 회귀 차단), (3) spine 정부 문서순서(같은 절 번호 내 leaf/era drift tiebreak), (4) 최신
    # 뼈대 위치 _skel, (5) leafSeq. 번호 없는 헤더·표지는 nulls_last(절 뒤).
    spineOrder = {k: v[0] for k, v in SPINE.items()} if SPINE else {}
    ranked = wide.with_columns(canonicalRankExpr("chapter"), rowIdentityExpr())
    ranked = ranked.with_columns(
        pl.col("_rowIdentity").replace_strict(spineOrder, default=None, return_dtype=pl.Int64).alias("_spOrder"),
        pl.col("sectionLeaf").str.extract(r"^\s*(\d+)", 1).cast(pl.Int64).alias("_secNum"),
        pl.col("sectionLeaf").str.extract(r"^\s*\d+\s*-\s*(\d+)", 1).cast(pl.Int64).fill_null(0).alias("_secSub"),
    )
    sortKeys = ["_canonRank", "_secNum", "_secSub", "_spOrder"]
    for c in ("_skel", "_skelOld", "leafSeq"):
        if c in wide.columns:
            sortKeys.append(c)
    return ranked.sort(sortKeys, nulls_last=True).select(orderedCols)
