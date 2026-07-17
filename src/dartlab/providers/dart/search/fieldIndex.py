"""필드 분리 BM25 검색 — scope="content" 전용 엔진.

실험 116 검증 결과 적용. title/section은 기존 ngramIndex 그대로 유지하고,
본문(content) 검색을 별도 엔진으로 분리.

설계:
- word 토크나이저 (공백+구두점) + BM25 + 필드 분리
- main + delta 세그먼트 구조 (월 1회 main 리빌드, 일 단위 delta 증분)
- scope="content": content 인덱스만 사용, title 매칭은 무관

저장 구조::

    data/dart/contentIndex/        # 월간 main + 선택적 일간 delta, postings=STORED sidecar(npz 폐기)
    ├── main.postings.bin   # content CSR (term별 docId delta-gap + tf varint) = postings SSOT
    ├── main.terms.bin · main.docLengths.bin · main.meta.bin · main.metaOffsets.bin · main.search_meta.json
    ├── main_meta.parquet   # 엔진/searchUnified 전체 스캔용 meta SSOT
    ├── main_stems.json · main_info.json   # stem→id · nDocs/avgDocLength
    └── delta.* + delta_overrides.json     # main 기준 누적 changed-set과 tombstone

병합 검색::

    mainScore = BM25(mainIndex, query)
    deltaScore = BM25(deltaIndex, query)
    rerank(union) by score desc — rcept_no 중복 시 delta 우선
"""

from __future__ import annotations

import array
import json
import math
import re
import time
from pathlib import Path

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import numpy as np
import polars as pl

# ── 상수 ──

CONTENT_LIMIT = 1500  # section_content 인덱싱 최대 글자 수
EVIDENCE_TEXT_LIMIT = 4000  # LLM/evidence card 용 bounded 원문 후보 텍스트

# 인덱스 직렬화 포맷 버전 — 코드(라이브러리)와 HF 인덱스의 호환 계약.
# bump 규칙: npz 키 구성·토크나이저(stems 어휘)·meta 스키마가 비호환 변경될 때 +1.
# 사용자가 받은 인덱스 schemaVersion > 코드면 best-effort(경고), < 면 재pull 안내(indexInfo.compatible).
# v2: content 토크나이저 word → 음절 bigram (stems 어휘 전면 교체 — v1 인덱스와 매칭 불가).
# v3: report_nm/section_title title field 가중 주입 — 공시 유형 질의에서 본문 길이에 제목이 묻히는 문제 보정.
INDEX_SCHEMA_VERSION = 3
TITLE_WEIGHT_REPEAT = 4

_HANGUL_RE = re.compile(r"[가-힣]+")
_ASCII_RE = re.compile(r"[A-Za-z]{2,20}")
_RUNTIME_META_COLUMNS: tuple[str, ...] = (
    "docKey",
    "rcept_no",
    "section_order",
    "corp_code",
    "corp_name",
    "stock_code",
    "rcept_dt",
    "report_nm",
    "section_title",
    "text",
    "source",
    "sourceRef",
    "sourceDataAsOf",
    "contentLen",
    "url",
    "deleted",
)
_EVIDENCE_META_COLUMNS: tuple[str, ...] = ("evidenceText",)


def _contentIndexDir(tier: str | None = None) -> Path:
    """content 인덱스 디렉터리. tier 없으면 flat base(legacy/full 배포 위치), 있으면 base/{tier}.

    하위호환 — tier=None 은 기존 배포 위치 ``data/dart/contentIndex/`` 그대로(모든 기존 호출자
    무영향). lite tier 는 ``data/dart/contentIndex/lite/`` 서브디렉터리에 격리.
    """
    from dartlab.core.dataLoader import _getDataRoot

    base = _getDataRoot() / "dart" / "contentIndex"
    if tier:
        base = base / tier
    base.mkdir(parents=True, exist_ok=True)
    return base


def _hasMainPostings(d: Path) -> bool:
    """flat/tier 디렉터리에 로드 가능한 main postings(STORED sidecar = SSOT)가 있나.

    compact-only(P2): postings 표현은 ``main.postings.bin`` 단독(npz 폐기).
    """
    return (d / "main.postings.bin").exists()


def _activeIndexDir() -> Path:
    """런타임 검색이 읽을 *유효* 인덱스 디렉터리 — flat 우선, 없으면 tier(기본 lite).

    1) ``contentIndex/active.json`` 이 유효하면 해당 artifact dir.
    2) flat 에 main postings(sidecar 또는 npz) 존재 → flat(기존 배포·dev). 기존 동작 보존.
    3) 없으면 tier = env ``DARTLAB_SEARCH_TIER`` 또는 ``lite`` → ``contentIndex/{tier}/``.
    모두 없으면 flat(빈 디렉터리 → graceful 빈 결과).
    """
    import os

    base = _contentIndexDir()
    from dartlab.providers.dart.search.localUpdate import resolveActiveIndexDir

    active = resolveActiveIndexDir(base)
    if active is not None:
        return active
    if _hasMainPostings(base):
        return base
    tier = (os.environ.get("DARTLAB_SEARCH_TIER") or "lite").strip()
    tierDir = base / tier
    if _hasMainPostings(tierDir):
        return tierDir
    return base


# ── 토크나이저 ──


def tokenizeContent(text: str) -> list[str]:
    """content 토크나이저 — 한글 음절 bigram + 영문 단어(소문자).

    음절 bigram 이 조사 변형을 형태소 분석 0 으로 흡수한다("배당을"→[배당,당을] 가
    "배당" 질의와 매칭). 숫자는 vocab 오염 차단을 위해 제외. landing
    ``viewer/searchIndex.tokenizeBigram`` 과 byte-parity (브라우저·서버 동일 토큰).

    Args:
        text: 색인/질의 원문 (빈 값·None 허용).

    Raises:
        없음.

    Example:
        >>> tokenizeContent("배당금 지급")
        ['배당', '당금', '지급']

    Returns:
        list[str] — 한글 음절 bigram(1음절 run 은 그대로) + 영문 소문자 토큰.
    """
    if not text:
        return []
    out: list[str] = []
    for run in _HANGUL_RE.findall(text):
        if len(run) == 1:
            out.append(run)
        else:
            out.extend(run[i : i + 2] for i in range(len(run) - 1))
    out.extend(m.lower() for m in _ASCII_RE.findall(text))
    return out


# ── 빌더 ──


class _IncrementalBuilder:
    """문서 단위로 점진적 토큰 축적 후 CSR로 finalize.

    posting 누적을 ``array.array('i')`` 3열(stemId/docId/tf, 각 4 byte)로 — dict-of-list-of-tuple
    (posting 당 ~56 byte) 대비 ~7x 메모리 절감. 풀 색인(수억 posting) OOM 회피. finalize 에서
    stemId 기준 stable argsort → bincount cumsum 으로 CSR offsets 구성.
    """

    def __init__(self):
        self.stemToId: dict[str, int] = {}
        self._pSid = array.array("i")  # posting별 stem id
        self._pDid = array.array("i")  # posting별 doc id
        self._pTf = array.array("i")  # posting별 term freq
        self._docLengths = array.array("i")

    def addDoc(self, text: str) -> None:
        """document 1 개 추가 — 토크나이즈 + stem→id 매핑 + posting 3열 누적.

        Args:
            text: document 본문 (빈 문자열 = 길이 0 doc 으로 기록).

        Returns:
            None.

        Raises:
            없음.

        Example:
            >>> builder.addDoc("배당에 관한 사항")  # doctest: +SKIP
        """
        docId = len(self._docLengths)
        if not text:
            self._docLengths.append(0)
            return
        toks = tokenizeContent(text)
        self._docLengths.append(len(toks))
        tf: dict[int, int] = {}
        getSid = self.stemToId.get
        for t in toks:
            sid = getSid(t)
            if sid is None:
                sid = len(self.stemToId)
                self.stemToId[t] = sid
            tf[sid] = tf.get(sid, 0) + 1
        apS, apD, apT = self._pSid.append, self._pDid.append, self._pTf.append
        for sid, c in tf.items():
            apS(sid)
            apD(docId)
            apT(c)

    def finalize(self) -> dict:
        """누적된 posting 3열/docLengths → CSR 인덱스 dict — BM25 검색 준비 완료 상태.

        Returns:
            ``{"stemDict": dict, "offsets": np.ndarray, "docIds": np.ndarray,
            "termFreqs": np.ndarray, "docLengths": np.ndarray, "avgDocLength": float, "nDocs": int}``.

        Raises:
            없음.

        Example:
            >>> idx = builder.finalize()  # doctest: +SKIP
        """
        nDocs = len(self._docLengths)
        nStems = len(self.stemToId)
        sids = np.frombuffer(self._pSid, dtype=np.int32)
        dids = np.frombuffer(self._pDid, dtype=np.int32)
        tfs = np.frombuffer(self._pTf, dtype=np.int32)
        offsets = np.zeros(nStems + 1, dtype=np.int64)
        if sids.size:
            order = np.argsort(sids, kind="stable")  # stemId 기준 그룹화
            docIds = np.ascontiguousarray(dids[order])
            termFreqs = np.ascontiguousarray(tfs[order])
            counts = np.bincount(sids, minlength=nStems)
            np.cumsum(counts, out=offsets[1:])
            del order, counts
        else:
            docIds = np.zeros(0, dtype=np.int32)
            termFreqs = np.zeros(0, dtype=np.int32)
        docLengths = np.frombuffer(self._docLengths, dtype=np.int32).copy()
        # 메모리 해제 (array.array 버퍼 + frombuffer view 참조 해제)
        del sids, dids, tfs
        self._pSid = self._pDid = self._pTf = array.array("i")
        self._docLengths = array.array("i")
        return {
            "stemDict": self.stemToId,
            "offsets": offsets,
            "docIds": docIds,
            "termFreqs": termFreqs,
            "docLengths": docLengths,
            "avgDocLength": float(docLengths.mean()) if nDocs > 0 else 0.0,
            "nDocs": nDocs,
        }


def buildContentSegment(
    rows: list[dict],
    *,
    contentLimit: int = CONTENT_LIMIT,
    showProgress: bool = True,
) -> tuple[dict, pl.DataFrame]:
    """문서 리스트로부터 content 세그먼트 1개 빌드.

    Parameters
    ----------
    rows : list[dict]
        각 row는 rcept_no, section_order, corp_name, stock_code, rcept_dt,
        report_nm, section_title, section_content 포함.
    contentLimit : int
        section_content 인덱싱 최대 글자 수.

    Returns
    -------
    (index, meta)
        index : CSR dict. meta : polars DataFrame.

    Raises:
        없음.

    Example:
        >>> buildContentSegment(...)

    Args:
        rows: 문서 row dict 리스트.
        contentLimit: 본문 최대 문자 수.
        showProgress: True 면 progress 로그.

    Returns:
        tuple[dict, pl.DataFrame] — (인덱스, meta).
    """
    t0 = time.perf_counter()
    builder = _IncrementalBuilder()
    metaRecs = []

    for row in rows:
        content = (row.get("section_content") or "")[:contentLimit]
        builder.addDoc(_weightedIndexText(row, content))
        metaRecs.append(
            {
                "rcept_no": row.get("rcept_no") or "",
                "section_order": int(row.get("section_order") or 0),
                "corp_code": row.get("corp_code") or "",
                "corp_name": row.get("corp_name") or "",
                "stock_code": row.get("stock_code") or "",
                "rcept_dt": str(row.get("rcept_dt") or ""),
                "report_nm": row.get("report_nm") or "",
                "section_title": row.get("section_title") or "",
                "text": content[:500],  # 스니펫용
                "evidenceText": str(row.get("evidenceText") or row.get("evidence_text") or content)[
                    :EVIDENCE_TEXT_LIMIT
                ],
                "source": row.get("source") or "",
                "sourceRef": row.get("sourceRef") or row.get("source_ref") or "",
                "sourceDataAsOf": row.get("sourceDataAsOf")
                or row.get("source_data_as_of")
                or row.get("rcept_dt")
                or "",
                "contentLen": len(content),
                "url": row.get("url") or "",  # 뉴스 기사 url (비뉴스는 "")
            }
        )

    idx = builder.finalize()
    meta = pl.DataFrame(metaRecs)
    if showProgress:
        elapsed = time.perf_counter() - t0
        _log.info(
            "  [content] %s문서, %s stems, %s postings, %.1f초",
            f"{idx['nDocs']:,}",
            f"{len(idx['stemDict']):,}",
            f"{idx['offsets'][-1]:,}",
            elapsed,
        )
    return idx, meta


def _weightedIndexText(row: dict, content: str) -> str:
    """Build BM25 input text with bounded title/report weighting.

    공시 유형 검색은 대부분 report_nm/section_title 이 정답 신호다. 본문 앞에 제목이 한 번
    들어가 있어도 1,500자 본문과 BM25 길이 정규화에 묻히므로, build-time 에만 작은 반복
    prefix 를 넣어 title lane 을 content index 안에 통합한다. 메타의 snippet/evidenceText 는
    원문 그대로 유지한다.
    """
    titleParts = [
        str(row.get("report_nm") or "").strip(),
        str(row.get("section_title") or "").strip(),
    ]
    title = " ".join(part for part in titleParts if part)
    if not title:
        return content
    weightedTitle = " ".join(title for _ in range(TITLE_WEIGHT_REPEAT))
    return f"{weightedTitle} {content}".strip()


# ── 저장/로드 ──


def writeSegmentCompanions(idx: dict, meta: pl.DataFrame, name: str, outDir: Path | None = None) -> None:
    """세그먼트 동반물(stems/info/meta.parquet)을 디스크에 저장 — postings 표현(npz)은 쓰지 않는다.

    compact-only(P2): postings SSOT 는 STORED sidecar(``saveShardedSegment``) 단독. 본 함수는
    sidecar 가 읽어들이는 동반물(stem→id·nDocs/avg·doc meta)만 기록한다. ``saveSegmentWithSidecar`` 가
    본 함수 + sidecar 를 한 묶음으로 호출(유일 writer).

    Args:
        idx: 인덱스 dict (stemDict/nDocs/avgDocLength 사용).
        meta: doc 순 meta DataFrame.
        name: 세그먼트 이름("main").
        outDir: 출력 디렉터리. None 이면 ``_contentIndexDir()``.

    Raises:
        OSError: 파일 기록 실패.

    Example:
        >>> callable(writeSegmentCompanions)
        True
    """
    outDir = outDir or _contentIndexDir()
    outDir.mkdir(parents=True, exist_ok=True)
    (outDir / f"{name}_stems.json").write_text(
        json.dumps(idx["stemDict"], ensure_ascii=False),
        encoding="utf-8",
    )
    meta.write_parquet(outDir / f"{name}_meta.parquet")
    (outDir / f"{name}_info.json").write_text(
        json.dumps(
            {
                "nDocs": idx["nDocs"],
                "avgDocLength": idx["avgDocLength"],
                "builtAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "schemaVersion": INDEX_SCHEMA_VERSION,
            }
        ),
        encoding="utf-8",
    )


def _encodeVarintArray(vals: np.ndarray) -> tuple[bytes, np.ndarray]:
    """비음수 정수 배열을 LEB128 unsigned varint 로 벡터 인코딩.

    Sig:
        _encodeVarintArray(vals: np.ndarray) -> tuple[bytes, np.ndarray]

    Args:
        vals: 비음수 정수 배열 (docId delta-gap 또는 termFreq).

    Returns:
        tuple[bytes, np.ndarray] — (연접 varint 바이트, 값별 byte 수 배열).

    Example:
        >>> b, n = _encodeVarintArray(np.array([1, 300], dtype=np.int64))
        >>> int(n[0]), int(n[1])
        (1, 2)
    """
    v = np.asarray(vals, dtype=np.uint64)
    if v.size == 0:  # 빈 스트림(예: df 0 또는 term 단독 doc) — .max() 빈 reduction 회피
        return b"", np.zeros(0, dtype=np.int64)
    nbits = np.where(v > 0, np.floor(np.log2(v.astype(np.float64) + 0.5)).astype(np.int64) + 1, 1)
    nbytes = np.maximum(1, (nbits + 6) // 7).astype(np.int64)
    out = np.zeros(int(nbytes.sum()), dtype=np.uint8)
    starts = np.zeros(len(v), dtype=np.int64)
    if len(v) > 1:
        np.cumsum(nbytes[:-1], out=starts[1:])
    for k in range(int(nbytes.max())):
        mask = nbytes > k
        out[starts[mask] + k] = ((v[mask] >> np.uint64(7 * k)) & np.uint64(0x7F)).astype(np.uint8) | (
            (k < (nbytes[mask] - 1)).astype(np.uint8) * np.uint8(0x80)
        )
    return out.tobytes(), nbytes


def _decodeVarintStream(raw: bytes, count: int) -> np.ndarray:
    """``_encodeVarintArray`` 의 역연산 — 연접 LEB128 varint 바이트열을 ``count`` 개 int64 로 벡터 디코드.

    각 바이트는 자신이 속한 값 그룹(continuation 비트 0 = 그룹 끝)을 ``cumsum`` 으로 식별하고,
    그룹 내 위치 × 7 만큼 shift 한 7-bit 페이로드를 ``np.add.reduceat`` 로 그룹별 합산한다. Python
    바이트 루프 없이 전 스트림을 한 번에 디코드(콜드 로드 속도·RSS 가드).

    Sig:
        _decodeVarintStream(raw: bytes, count: int) -> np.ndarray

    Args:
        raw: 연접 varint 바이트열.
        count: 디코드할 값 개수 (continuation 0 바이트 수와 일치해야 함).

    Returns:
        np.ndarray(int64) — 길이 ``count`` 값 배열.

    Raises:
        ValueError: 스트림의 값 개수가 ``count`` 와 다를 때(인코딩 불일치).

    Example:
        >>> b, _ = _encodeVarintArray(np.array([1, 300, 5], dtype=np.int64))
        >>> _decodeVarintStream(b, 3).tolist()
        [1, 300, 5]
    """
    if count == 0:
        return np.zeros(0, dtype=np.int64)
    b = np.frombuffer(raw, dtype=np.uint8)
    isLast = (b & 0x80) == 0
    lastPos = np.nonzero(isLast)[0]  # 각 값의 마지막 바이트 위치
    if len(lastPos) != count:
        raise ValueError(f"varint stream 값 개수 {len(lastPos)} != 기대 {count}")
    groupStart = np.empty(count, dtype=np.int64)
    groupStart[0] = 0
    groupStart[1:] = lastPos[:-1] + 1
    valueIndex = np.cumsum(isLast.astype(np.int64)) - isLast.astype(np.int64)  # 바이트별 0-based 값 그룹
    shift = (np.arange(len(b), dtype=np.int64) - groupStart[valueIndex]) * 7
    contrib = (b & 0x7F).astype(np.int64) << shift
    return np.add.reduceat(contrib, groupStart)


def loadShardedSegment(name: str = "main", inDir: Path | None = None, *, includeEvidenceText: bool = False):
    """STORED sidecar(postings/terms/docLengths.bin)에서 CSR 인덱스를 무손실 복원 — npz 없이 로드.

    ``saveShardedSegment`` 의 역연산. ``postings.bin`` 전체를 ``_decodeVarintStream`` 으로 한 번에 디코드한
    뒤 term 별로 [gap×df][tf×df] 로 분리하고, term 경계마다 절대 docId 로 reset 되는 gap 을 세그먼트
    cumsum 으로 docIds 복원한다. 반환 idx 는 ``loadSegment`` 와 동일 키라 ``_scoreBM25`` 가
    그대로 소비(랭킹 불변·byte-parity). meta/info 는 ``loadSegment`` 와 동일하게 parquet/json 에서 읽는다.

    Sig:
        loadShardedSegment(name="main", inDir=None, *, includeEvidenceText=False) -> tuple[dict, pl.DataFrame] | None

    Args:
        name: 세그먼트 이름("main").
        inDir: 인덱스 디렉터리. None 이면 ``_contentIndexDir()``.
        includeEvidenceText: True 면 evidenceText 컬럼까지 meta 로드.

    Returns:
        tuple[dict, pl.DataFrame] 또는 None — sidecar(postings.bin) 부재 시 None.

    Raises:
        ValueError: postings 디코드 값 개수가 terms.bin df 합과 불일치할 때.

    Example:
        >>> loadShardedSegment("main")  # doctest: +SKIP
    """
    inDir = inDir or _contentIndexDir()
    postingsPath = inDir / f"{name}.postings.bin"
    if not postingsPath.exists():
        return None
    stemDict = json.loads((inDir / f"{name}_stems.json").read_text(encoding="utf-8"))
    info = json.loads((inDir / f"{name}_info.json").read_text(encoding="utf-8"))
    terms = np.frombuffer((inDir / f"{name}.terms.bin").read_bytes(), dtype=np.uint32).reshape(-1, 4)
    df = terms[:, 3].astype(np.int64)  # term 별 posting 수
    nTerms = len(df)
    offsets = np.zeros(nTerms + 1, dtype=np.int64)
    np.cumsum(df, out=offsets[1:])
    nPost = int(offsets[-1])
    docLengths = np.frombuffer((inDir / f"{name}.docLengths.bin").read_bytes(), dtype=np.uint32).astype(np.int32)

    if nPost == 0:
        docIds = np.zeros(0, dtype=np.int32)
        termFreqs = np.zeros(0, dtype=np.int32)
    else:
        # postings.bin = term0[gap×df0 | tf×df0] term1[...] ... (stemId 순 연접). 전체를 한 번에 디코드.
        values = _decodeVarintStream(postingsPath.read_bytes(), 2 * nPost)
        perTerm = 2 * df
        termOfValue = np.repeat(np.arange(nTerms, dtype=np.int64), perTerm)
        cumStart = np.zeros(nTerms, dtype=np.int64)
        np.cumsum(perTerm[:-1], out=cumStart[1:])
        within = np.arange(2 * nPost, dtype=np.int64) - cumStart[termOfValue]
        isGap = within < df[termOfValue]  # term 내 앞 df 개=gap, 뒤 df 개=tf
        gaps = values[isGap]
        termFreqs = values[~isGap].astype(np.int32)
        # term 경계마다 첫 gap=절대 docId(reset) → 세그먼트 cumsum 으로 docIds 복원.
        full = np.cumsum(gaps)
        startIdx = offsets[:-1]
        prevIdx = np.where(startIdx > 0, startIdx - 1, 0)
        baseVals = np.where(startIdx > 0, full[prevIdx], 0)
        docIds = (full - np.repeat(baseVals, df)).astype(np.int32)

    metaPath = inDir / f"{name}_meta.parquet"
    meta = pl.read_parquet(metaPath, columns=_segmentMetaColumns(metaPath, includeEvidenceText=includeEvidenceText))
    idx = {
        "stemDict": stemDict,
        "offsets": offsets,
        "docIds": docIds,
        "termFreqs": termFreqs,
        "docLengths": docLengths,
        "avgDocLength": float(info["avgDocLength"]),
        "nDocs": int(info["nDocs"]),
    }
    return idx, meta


# meta.bin doc-카드에 담는 필드 (top-k snippet/회사점프용 — main_meta 의 부분집합, bounded).
_SHARD_META_FIELDS = (
    "docKey",
    "rcept_no",
    "section_order",
    "corp_name",
    "stock_code",
    "report_nm",
    "rcept_dt",
    "source",
    "sourceRef",
    "url",
    "deleted",
)
_SHARD_SNIPPET_LIMIT = 400


def saveShardedSegment(idx: dict, meta: pl.DataFrame, name: str = "main", outDir: Path | None = None) -> dict:
    """range-friendly sidecar(postings/terms/docLengths/meta).bin = postings SSOT (compact-only, npz 폐기).

    DEFLATE npz 는 임의 위치 디코딩 불가(브라우저 range fetch 불능)라, CSR 을 STORED(비압축 컨테이너)
    sidecar 로 재배치한다. 엔진(loadShardedSegment)도 이 sidecar 에서 CSR 을 무손실 복원해 읽는다(단일 SSOT).
    각 산출물은 "offset 표 + STORED blob" 패턴 — 클라이언트가 질의어 term 의 postings 범위와 top-k
    doc 의 meta 범위만 HTTP range 로 받아 full BM25 와 동일한 결과를 낸다(검증: byte-range=full overlap 1.0).

    Sig:
        saveShardedSegment(idx: dict, meta: pl.DataFrame, name: str = "main", outDir: Path | None = None) -> dict

    Args:
        idx: ``loadSegment``/빌더의 인덱스 dict (offsets/docIds/termFreqs/docLengths/stemDict/nDocs/avgDocLength).
        meta: doc_id 순(row i = doc i) 메타 DataFrame. ``_SHARD_META_FIELDS`` + snippet(evidenceText/text) 컬럼 사용.
        name: 세그먼트 이름 ("main" 또는 "delta").
        outDir: 출력 디렉터리. None 이면 ``_contentIndexDir()``.

    Returns:
        dict — 생성 파일명→바이트크기 + nDocs/nTerms (search_meta.json 에도 기록).

    Raises:
        KeyError: idx 에 필수 키(offsets/docIds/termFreqs/docLengths)가 없을 때.

    Example:
        >>> seg = loadSegment("main")
        >>> saveShardedSegment(seg[0], seg[1], "main")["postings.bin"] > 0  # doctest: +SKIP
        True
    """
    outDir = outDir or _contentIndexDir()
    outDir.mkdir(parents=True, exist_ok=True)
    offsets = np.asarray(idx["offsets"], dtype=np.int64)
    docIds = np.asarray(idx["docIds"])
    termFreqs = np.asarray(idx["termFreqs"])
    docLengths = np.asarray(idx["docLengths"], dtype=np.int64)
    nTerms = len(offsets) - 1

    # postings.bin: term 별 [docId delta-gap varint][termFreq varint] 블록 연접.
    gaps = np.empty(len(docIds), dtype=np.int64)
    if len(docIds):
        gaps[1:] = np.diff(docIds.astype(np.int64))
        gaps[0] = int(docIds[0])
        gaps[offsets[1:-1]] = docIds[offsets[1:-1]]  # term 경계 = 절대 docId 로 reset
    gapBytes, gapNb = _encodeVarintArray(gaps)
    tfBytes, tfNb = _encodeVarintArray(termFreqs)
    gapCum = np.zeros(len(docIds) + 1, dtype=np.int64)
    tfCum = np.zeros(len(docIds) + 1, dtype=np.int64)
    np.cumsum(gapNb, out=gapCum[1:])
    np.cumsum(tfNb, out=tfCum[1:])
    postings = bytearray()
    termRecs = np.zeros((nTerms, 4), dtype=np.uint32)  # byteStart, gapLen, tfLen, df
    for t in range(nTerms):
        s, e = int(offsets[t]), int(offsets[t + 1])
        g0, g1, f0, f1 = int(gapCum[s]), int(gapCum[e]), int(tfCum[s]), int(tfCum[e])
        start = len(postings)
        postings += gapBytes[g0:g1]
        postings += tfBytes[f0:f1]
        termRecs[t] = (start, g1 - g0, f1 - f0, e - s)
    (outDir / f"{name}.postings.bin").write_bytes(bytes(postings))
    (outDir / f"{name}.terms.bin").write_bytes(termRecs.tobytes())  # stemId 순 uint32×4
    (outDir / f"{name}.docLengths.bin").write_bytes(np.minimum(docLengths, 0xFFFFFFFF).astype(np.uint32).tobytes())

    # meta.bin: doc 별 카드(JSON) + metaOffsets.bin(uint64×(nDocs+1)) — top-k 만 range fetch.
    metaCols = [c for c in _SHARD_META_FIELDS if c in meta.columns]
    snippetCol = "evidenceText" if "evidenceText" in meta.columns else ("text" if "text" in meta.columns else None)
    metaBlob = bytearray()
    metaOff = [0]
    sel = meta.select(metaCols + ([snippetCol] if snippetCol else []))
    for row in sel.iter_rows(named=True):
        card = {k: row.get(k) for k in metaCols}
        if snippetCol:
            sn = row.get(snippetCol) or ""
            card["snippet"] = str(sn)[:_SHARD_SNIPPET_LIMIT]
        metaBlob += json.dumps(card, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        metaOff.append(len(metaBlob))
    (outDir / f"{name}.meta.bin").write_bytes(bytes(metaBlob))
    (outDir / f"{name}.metaOffsets.bin").write_bytes(np.asarray(metaOff, dtype=np.uint64).tobytes())

    files = {
        f"{name}.postings.bin": len(postings),
        f"{name}.terms.bin": int(termRecs.nbytes),
        f"{name}.docLengths.bin": len(docLengths) * 4,
        f"{name}.meta.bin": len(metaBlob),
        f"{name}.metaOffsets.bin": len(metaOff) * 8,
    }
    (outDir / f"{name}.search_meta.json").write_text(
        json.dumps(
            {
                "nDocs": int(idx["nDocs"]),
                "nTerms": nTerms,
                "avgDocLength": float(idx["avgDocLength"]),
                "schemaVersion": INDEX_SCHEMA_VERSION,
                "snippetField": snippetCol,
                "metaFields": metaCols,
                "files": files,
                "builtAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if name == "delta":
        overrideCols = [
            column
            for column in ("docKey", "sourceRef", "rcept_no", "section_order", "deleted")
            if column in meta.columns
        ]
        overrides = meta.select(overrideCols).to_dicts() if overrideCols else []
        (outDir / "delta_overrides.json").write_text(
            json.dumps(overrides, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    return {**files, "nDocs": int(idx["nDocs"]), "nTerms": nTerms}


def loadSegment(
    name: str,
    inDir: Path | None = None,
    *,
    includeEvidenceText: bool = False,
) -> tuple[dict, pl.DataFrame] | None:
    """세그먼트를 디스크에서 로드. 파일이 없으면 None.

    Args:
        name: 인자.
        inDir: 인자.
        includeEvidenceText: True 면 긴 evidenceText 컬럼까지 로드. 기본 검색 경로는
            slim meta 만 로드해 full index RSS 를 낮춘다.

    Raises:
        없음.

    Example:
        >>> loadSegment(...)

    Returns:
        tuple[dict, pl.DataFrame] 또는 None — (인덱스, meta).
    """
    inDir = inDir or _contentIndexDir()
    # compact-only(P2): postings SSOT = STORED sidecar 단독(npz 폐기). postings.bin 부재면 None.
    if (inDir / f"{name}.postings.bin").exists():
        return loadShardedSegment(name, inDir, includeEvidenceText=includeEvidenceText)
    return None


def _segmentMetaColumns(metaPath: Path, *, includeEvidenceText: bool) -> list[str] | None:
    """Return bounded metadata columns for runtime segment loading."""
    try:
        schema = pl.read_parquet_schema(metaPath)
    except Exception:  # noqa: BLE001 - corrupt schema should fail through normal full read path.
        return None
    wanted = list(_RUNTIME_META_COLUMNS)
    if includeEvidenceText:
        wanted.extend(_EVIDENCE_META_COLUMNS)
    columns = [column for column in wanted if column in schema]
    return columns or None


# ── 검색 ──


def _scoreBM25(
    idx: dict,
    queryTokens: list[str],
    k1: float = 1.5,
    b: float = 0.75,
    weights: dict[str, float] | None = None,
) -> np.ndarray:
    """BM25 벡터화 스코어링 — 토큰 dedup + (선택) 확장어 가중.

    bigram 질의는 토큰 중복이 흔해 dedup 필수(중복 가산 차단). ``weights`` 는 확장
    lane 용 — 질의 원토큰 1.0, 동의어/canon 확장토큰 0.5 식 가중(R* 레시피 parity).
    """
    scores = np.zeros(idx["nDocs"], dtype=np.float32)
    N = idx["nDocs"]
    if N == 0:
        return scores
    avgDl = max(idx["avgDocLength"], 1.0)
    seen: set[str] = set()
    for t in queryTokens:
        if t in seen:
            continue
        seen.add(t)
        sid = idx["stemDict"].get(t)
        if sid is None:
            continue
        qw = 1.0 if weights is None else float(weights.get(t, 1.0))
        s, e = idx["offsets"][sid], idx["offsets"][sid + 1]
        ids = idx["docIds"][s:e]
        tfs = idx["termFreqs"][s:e].astype(np.float32)
        df_t = len(ids)
        idf = math.log((N - df_t + 0.5) / (df_t + 0.5) + 1.0)
        dl = idx["docLengths"][ids].astype(np.float32)
        normTf = tfs * (k1 + 1) / (tfs + k1 * (1 - b + b * dl / avgDl))
        np.add.at(scores, ids, qw * idf * normTf)
    return scores


# 세션 캐시
_segments: dict[str, tuple[dict, pl.DataFrame]] | None = None


def _getSegments() -> dict[str, tuple[dict, pl.DataFrame]]:
    """main과 선택적 누적 delta 세그먼트를 로드한다."""
    global _segments
    if _segments is not None:
        return _segments
    # pip 사용자 진입: 로컬 인덱스 부재 시 HF lazy pull (1회, graceful). 로컬 있으면 no-op.
    from dartlab.providers.dart.search.fieldIndexRebuild import ensureContentIndex, indexInfo

    ensureContentIndex()
    # 버전 계약 — 받은 인덱스가 코드보다 신버전이면 best-effort 로 읽되 1회 경고(라이브러리 업그레이드 안내).
    _info = indexInfo()
    if _info.get("available") and not _info.get("compatible", True):
        _log.warning(
            "검색 인덱스 schemaVersion=%s 가 라이브러리(%s)보다 신버전 — best-effort 로드. "
            "`pip install -U dartlab` 권장.",
            _info.get("schemaVersion"),
            INDEX_SCHEMA_VERSION,
        )
    inDir = _activeIndexDir()  # flat(legacy/full) 우선, 없으면 tier(기본 lite)
    out = {}
    for name in ("main", "delta"):
        seg = loadSegment(name, inDir)
        if seg is not None:
            out[name] = seg
    _segments = out
    return out


def clearCache() -> None:
    """세션 캐시 해제 (인덱스 재빌드 후 호출).

    Raises:
        없음.

    Example:
        >>> clearCache(...)
    """
    global _segments
    _segments = None


def _scopeMask(
    meta: pl.DataFrame,
    corpCode: str | None,
    stockCode: str | None,
    sourceKind: str | None = None,
) -> np.ndarray | None:
    """corp/stock 필터를 랭킹 *전* 스코프 마스크로 변환 — "회사 안에서 검색" 의미론.

    사후(top-N 수집 후) 필터는 흔한 질의에서 해당 회사가 전역 상위에 못 들면 0건이 되는
    결함이 있다 (예: "배당" + 005930). 마스크를 lane 점수에 곱해 랭킹 자체를 스코프한다.

    Args:
        meta: 세그먼트 meta (corp_code/stock_code 컬럼, 점수 배열과 행 정렬 동일).
        corpCode: 회사 식별자 corp_code. None 이면 무제한.
        stockCode: 종목코드 (6 자리). None 이면 무제한.

    Raises:
        없음.

    Example:
        >>> _scopeMask(meta, None, "005930")  # doctest: +SKIP

    Returns:
        np.ndarray(bool) — 스코프 내 행 True. 필터가 없으면 None.
    """
    if not corpCode and not stockCode and not sourceKind:
        return None
    mask = np.ones(meta.height, dtype=bool)
    if corpCode:
        mask &= (meta["corp_code"] == corpCode).to_numpy()
    if stockCode:
        mask &= (meta["stock_code"] == stockCode).to_numpy()
    if sourceKind:
        mask &= _sourceMask(meta, sourceKind)
    return mask


def _sourceMask(meta: pl.DataFrame, sourceKind: str) -> np.ndarray:
    """source family 필터를 랭킹 전 마스크로 변환."""
    from dartlab.providers.dart.search.sourceIntent import sourceFamily

    if "source" not in meta.columns:
        return np.ones(meta.height, dtype=bool)
    return np.array([sourceFamily(value) == sourceKind for value in meta["source"].to_list()], dtype=bool)


def _resolveResultUrl(df: pl.DataFrame) -> pl.DataFrame:
    """결과 DataFrame 에 dartUrl 컬럼 부여 — source 분기.

    뉴스(source="news")는 기사 url 그대로, 그 외(공시)는 DART 뷰어 URL(rcpNo) 조합.

    Args:
        df: 검색 결과 DataFrame (rcept_no/source/url 컬럼 보유).

    Returns:
        pl.DataFrame — dartUrl 컬럼 추가본. 빈 df 면 그대로.

    Raises:
        없음.

    Example:
        >>> _resolveResultUrl(pl.DataFrame())  # doctest: +SKIP
    """
    from dartlab.providers.dart.search.resultSchema import normalizeSearchResult

    if df.height == 0:
        return df
    hasUrl = "url" in df.columns
    dartBase = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + pl.col("rcept_no")
    out = df
    if "source" in df.columns:
        # EDGAR rcept_no = SEC accession — DART 뷰어 URL 조합이 성립하지 않으므로 빈값(정직).
        dartBase = pl.when(pl.col("source") == "edgar-panel").then(pl.lit("")).otherwise(dartBase)
        if hasUrl:
            out = df.with_columns(
                pl.when(pl.col("source") == "news").then(pl.col("url")).otherwise(dartBase).alias("dartUrl")
            )
            return normalizeSearchResult(out)
    out = df.with_columns(dartBase.alias("dartUrl"))
    return normalizeSearchResult(out)


def _segmentRowKey(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("sourceRef") or row.get("source") or ""),
        str(row.get("rcept_no") or ""),
        str(row.get("section_order") or ""),
    )


def searchContent(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    sourceKind: str | None = None,
    limit: int = 10,
) -> pl.DataFrame:
    """content 전용 BM25 검색. delta가 있으면 main보다 우선한다.

    Parameters
    ----------
    query : 자연어 쿼리. 공백으로 단어 분리.
    corpCode, stockCode : 필터.
    limit : 반환 건수.

    Raises:
        없음.

    Example:
        >>> searchContent(...)

    Args:
        query: 검색어 (자연어).
        corpCode: 회사 식별자 corp_code. None 이면 전체.
        stockCode: 종목코드 (6 자리). None 이면 전체.
        limit: 최대 결과 행 수.

    Returns:
        pl.DataFrame — 검색 결과 (rcept_no/score/snippet 등).
    """
    tokens = tokenizeContent(query)
    if not tokens:
        return pl.DataFrame()

    segments = _getSegments()
    if "main" not in segments:
        return pl.DataFrame(
            {
                "info": [
                    "content 인덱스가 없습니다. dartlab.providers.dart.search.fieldIndex.rebuildContent() 실행 필요."
                ]
            }
        )

    allHits: list[dict] = []
    deltaKeys = {
        _segmentRowKey(row) for row in (segments["delta"][1].iter_rows(named=True) if "delta" in segments else [])
    }
    for name in ("delta", "main"):
        if name not in segments:
            continue
        idx, meta = segments[name]
        scores = _scoreBM25(idx, tokens)
        mask = _scopeMask(meta, corpCode, stockCode, sourceKind)
        if mask is not None:
            scores = np.where(mask, scores, 0.0)
        for i in np.argsort(-scores)[: limit * 3]:
            if scores[i] <= 0:
                break
            row = meta.row(int(i), named=True)
            key = _segmentRowKey(row)
            if bool(row.get("deleted")) or (name == "main" and key in deltaKeys):
                continue
            allHits.append({**row, "score": float(scores[i]), "segment": name})

    if not allHits:
        return pl.DataFrame()

    # corp/stock 스코프는 _scopeMask 로 랭킹 전 적용 완료 — 사후 필터 불필요.
    df = pl.DataFrame(allHits).sort("score", descending=True)
    df = _resolveResultUrl(df)
    return df.head(limit)


# ── 풀리빌드 + 증분 ──


# ── rebuildMain / push/pull 등 빌드 helper 는 fieldIndexRebuild.py 로 분리 (룰 3 LoC).
from dartlab.providers.dart.search.fieldIndexRebuild import (  # noqa: E402, F401
    contentStats,
    iterContent,
    pullContentIndex,
    pushContentIndex,
    rebuildMain,
    saveSegmentWithSidecar,
)
