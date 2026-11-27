"""zip 풀어서 XML 추출 + aclassExtractor 호출 → ref entry 누적.

5 baseline (scanRefBaseline) 및 전종목 (scanAllZips) 의 entry point.
multiprocessing 은 전종목 스캔에서만 활성화 (baseline 은 단일 process — debug 용이).

LLM Specifications:
    AntiPatterns:
        - zip 안 여러 XML 가정 금지 — DART zip 1 개당 XML 1 개 (실측 확인).
        - period 추출 시 zip filename 만 의존 금지 — rcept_no.xml 양식이 변경
          가능. ``rcept_no`` 별도 보유 + period 는 caller (builder) 메타로 매핑.
        - rcept_no → period 매핑은 본 모듈에서 안 함. 본 모듈은 zip path +
          rcept_no 만 carry.
    OutputSchema:
        - ``scanZipFiles(paths) -> pl.DataFrame`` 11 col Layer 1 schema.
        - ``scanRefBaseline(codes) -> pl.DataFrame`` 5 baseline + 전 기간.
    Prerequisites:
        - ``data/original/dart/docs/{code}/*.zip`` 로컬.
        - polars, lxml.
    Freshness:
        - 분기 cron — mtime > sinceDate 만 처리하는 increment 변형.
    Dataflow:
        - zip path list → 각 zip 열기 → XML 추출 → extractAclassEntries
          → corp / rcept_no / aggregator 누적 → (rawId, rawTitleCanonical)
          기준 group → corpCount/periodCount/occurrenceCount 산출.
    TargetMarkets:
        - KR (DART). EDGAR 는 별도 worker.
"""

from __future__ import annotations

import logging
import multiprocessing as mp
import re
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import polars as pl

import dartlab.config as _cfg

from ..xmlRepair import repairDartXml
from .aclassExtractor import extractAclassEntries

_log = logging.getLogger(__name__)

# zip filename 양식: "{rcept_no}.zip" (rcept_no 14 자리).
_RCEPT_RE = re.compile(r"^(\d{14})\.zip$", re.IGNORECASE)


def _rceptFromZip(path: Path) -> str | None:
    """zip 파일명 → rcept_no (14 자리). 양식 불일치는 None.

    Examples:
        >>> _rceptFromZip(Path("20260515002181.zip"))
        '20260515002181'
        >>> _rceptFromZip(Path("invalid.zip")) is None
        True
    """
    m = _RCEPT_RE.match(path.name)
    return m.group(1) if m else None


def _decodeXmlBytes(raw: bytes) -> str:
    """raw bytes → utf-8 string. trial decode (utf-8 strict → cp949 fallback) 뒤 깨짐 수리.

    DART 옛 분기 zip 은 XML declaration 에 ``encoding="utf-8"`` 박지만 *실제*
    byte stream 은 cp949/EUC-KR. declaration 무시하고 utf-8 strict decode
    시도 → UnicodeDecodeError 시 cp949 fallback.

    실측 (005930 2015Q4 / 2016Q1~Q3): declaration utf-8 + 실제 cp949 → 한국어
    깨짐 회귀.

    decode 한 문자열은 ``repairDartXml`` 로 글자 꺾쇠(``<신 설>``), 겹친 따옴표
    (``ENG=""Other ..."``), 알몸 ``&`` 를 고친다. 고치지 않으면 lxml recover 가
    태그 짝을 잃어 II~XII 장이 앞 장 표 한 칸 안으로 들어간다 (실측 005380
    2025 사업보고서: 표 안 장 12 개 → 0 개).
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp949")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
    return repairDartXml(text)


def _readXml(zipPath: Path) -> str:
    """zip 안 첫 .xml 파일 → utf-8 string.

    declaration encoding 거짓말 (옛 양식 utf-8 선언이나 실제 cp949) 회피 —
    trial decode (utf-8 strict → cp949 fallback).
    """
    try:
        with zipfile.ZipFile(zipPath) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
            if not names:
                return ""
            with zf.open(names[0]) as f:
                raw = f.read()
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        _log.warning("zip read 실패 %s: %s", zipPath, exc)
        return ""
    return _decodeXmlBytes(raw)


def scanZipFiles(
    zipPaths: Iterable[Path],
    *,
    minCorpCount: int = 3,
    verbose: bool = False,
) -> pl.DataFrame:
    """zip path iterable → Layer 1 ``panelXbrlRef.parquet`` DataFrame.

    Capabilities:
        zip 본문 XML 의 ``<TABLE-GROUP ACLASS>`` ref 추출 → (rawId, rawTitleCanonical)
        집계 → corpCount/periodCount/occurrenceCount 계산 → Layer 1 SSOT 11-col table.

    AIContext:
        panelXbrlRef SSOT 빌드 1단계 (zip path → ref). scanAllZips 가 전종목 병렬 호출.

    Guide:
        baseline (5 종목) 검증 시 minCorpCount=1 로 모든 entry 확인. 전종목은 기본 3.

    When:
        panelXbrlRef.parquet 재빌드 시 (build-time 잡, runtime 아님).

    How:
        zip 본문 read → extractAclassEntries → (rawId, title) bag 집계 → minCorpCount 필터 → DataFrame.

    Args:
        zipPaths: 처리할 zip 파일 path iterable.
        minCorpCount: SSOT 입성 최소 회사 수 (기본 3).
            baseline (5 종목) 검증 시 1 로 낮춰 모든 entry 확인 가능.
        verbose: 진행 로그.

    Returns:
        Layer 1 schema 11 col DataFrame:
            rawId / rawTitleCanonical / rawTitleVariants / parentRawId /
            taxonomyVersion / firstSeenPeriod / lastSeenPeriod / corpCount /
            periodCount / occurrenceCount / marketNs.

        marketNs 는 항상 ``"kr"``. taxonomyVersion 은 [추정] — baseline 단계
        에선 NULL, 전종목 스캔에서 IFRS taxonomy 매핑 추가 layer 로.

    Requires:
        zip 양식 ``{code}/{rcept_no}.zip`` + 읽기 가능. polars.

    Raises:
        없음 — 개별 zip read/parse 실패는 worker 가 흡수해 빈 결과로 skip.

    Example:
        >>> df = scanZipFiles(zipPaths, minCorpCount=1)  # doctest: +SKIP
        >>> df.columns[:2]  # doctest: +SKIP
        ['rawId', 'rawTitleCanonical']

    SeeAlso:
        ``scanAllZips`` — 전종목 병렬 호출 래퍼.
        ``extractAclassEntries`` — zip 본문 ACLASS 추출기.

    LLM Specifications:
        AntiPatterns:
            - corp 추출 시 zipPath.parent.name 가정 — 호출자가 표준 구조
              유지 책임 (data/original/dart/docs/{code}/{rcept_no}.zip).
            - period 추출은 baseline 에서 NULL — rcept_no → period 매핑은 caller 메타가 담당.
        OutputSchema:
            - polars DataFrame, 11 col.
        Prerequisites:
            - zip 양식: ``{code}/{rcept_no}.zip``.
        Freshness:
            - minCorpCount 기본값 3 — baseline 5 종목 검증 시 1 로 낮춰 검증.
    """
    # (rawId, rawTitleCanonical) → 집계 bag
    bag: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "titles": Counter(),
            "corps": set(),
            "rcepts": set(),
            "parent": None,
        }
    )

    processed = 0
    failed = 0
    for zp in zipPaths:
        zp = Path(zp)
        corp = zp.parent.name  # data/original/dart/docs/{code}/...
        rcept = _rceptFromZip(zp) or zp.stem
        xml = _readXml(zp)
        if not xml:
            failed += 1
            continue
        entries = extractAclassEntries(xml)
        if not entries:
            failed += 1
            continue
        for entry in entries:
            k = (entry["rawId"], entry["rawTitleCanonical"])
            v = bag[k]
            v["titles"][entry["rawTitleRaw"]] += 1
            v["corps"].add(corp)
            v["rcepts"].add(rcept)
            # parent 일관성 — 첫 발견 우선 (보통 stable)
            if v["parent"] is None and entry["parentRawId"]:
                v["parent"] = entry["parentRawId"]
        processed += 1
        if verbose and processed % 200 == 0:
            _log.info("scanned %d zip, %d entries", processed, len(bag))

    if verbose:
        _log.info(
            "총 processed=%d failed=%d unique=(rawId,title)=%d",
            processed,
            failed,
            len(bag),
        )

    rows = []
    for (rawId, titleCanonical), v in bag.items():
        if len(v["corps"]) < minCorpCount:
            continue
        variants = [t for t, _ in v["titles"].most_common()]
        rows.append(
            {
                "rawId": rawId,
                "rawTitleCanonical": titleCanonical,
                "rawTitleVariants": variants,
                "parentRawId": v["parent"],
                "taxonomyVersion": None,
                "firstSeenPeriod": None,
                "lastSeenPeriod": None,
                "corpCount": len(v["corps"]),
                "periodCount": len(v["rcepts"]),  # baseline 단계: rcept 수 = period proxy
                "occurrenceCount": int(sum(v["titles"].values())),
                "marketNs": "kr",
            }
        )

    if not rows:
        return pl.DataFrame(
            schema={
                "rawId": pl.Utf8,
                "rawTitleCanonical": pl.Utf8,
                "rawTitleVariants": pl.List(pl.Utf8),
                "parentRawId": pl.Utf8,
                "taxonomyVersion": pl.Utf8,
                "firstSeenPeriod": pl.Utf8,
                "lastSeenPeriod": pl.Utf8,
                "corpCount": pl.UInt32,
                "periodCount": pl.UInt32,
                "occurrenceCount": pl.UInt32,
                "marketNs": pl.Utf8,
            }
        )

    return pl.DataFrame(
        rows,
        schema_overrides={
            "corpCount": pl.UInt32,
            "periodCount": pl.UInt32,
            "occurrenceCount": pl.UInt32,
        },
    ).sort(["corpCount", "occurrenceCount"], descending=[True, True])


def _zipToEntries(zipPath: Path) -> tuple[str, str, list[dict]]:
    """multiprocessing worker — 단일 zip → (corp, rcept, entries).

    pickleable function. Pool.imap 으로 사용.
    """
    zp = Path(zipPath)
    corp = zp.parent.name
    rcept = _rceptFromZip(zp) or zp.stem
    xml = _readXml(zp)
    if not xml:
        return (corp, rcept, [])
    return (corp, rcept, extractAclassEntries(xml))


def scanAllZips(
    *,
    baseDir: Path | str | None = None,
    minCorpCount: int = 3,
    numWorkers: int = 8,
    progressEvery: int = 2000,
    verbose: bool = True,
) -> pl.DataFrame:
    """전종목 zip → Layer 1 ref table (multiprocessing).

    Capabilities:
        ``data/original/dart/docs/`` 전 zip 을 multiprocessing 으로 scanZipFiles 병렬 처리 →
        Layer 1 panelXbrlRef table (corpCount desc 정렬).

    AIContext:
        panelXbrlRef SSOT 전종목 빌드 entry. scanZipFiles 의 병렬 래퍼.

    Guide:
        numWorkers 는 IO-heavy 라 코어 수보다 크게(8) 잡아도 무방. minCorpCount=3 권장.

    When:
        panelXbrlRef.parquet 전체 재빌드 시 (build-time 잡, ~시간).

    How:
        baseDir glob → multiprocessing.Pool.imap → scanZipFiles → 집계 → DataFrame.

    Args:
        baseDir: ``data/original/dart/docs/`` 경로. None = config default.
        minCorpCount: SSOT 입성 minimum corpCount. 기본 3.
        numWorkers: multiprocessing.Pool workers. 기본 8.
        progressEvery: 진행 로그 빈도.
        verbose: 진행 로그.

    Returns:
        Layer 1 schema DataFrame (11 col).

    Raises:
        없음 — 개별 zip read/parse 실패는 worker 가 흡수해 빈 entry 로 skip,
        전체 스캔은 계속된다.

    Examples:
        >>> df = scanAllZips(numWorkers=8)  # doctest: +SKIP
        >>> df.height >= 200  # doctest: +SKIP
        True

    Requires:
        ``data/original/dart/docs/{code}/*.zip`` 전종목 + multiprocessing 가용.

    SeeAlso:
        ``scanZipFiles`` — 단일 batch 스캔 로직. ``scanRefBaseline`` — 5 종목 검증 버전.

    LLM Specifications:
        AntiPatterns:
            - Pool.map 사용 금지 — large input 시 memory 폭발. imap 사용.
            - chunk size 1 fix 금지 — IO heavy 라 chunk 큰 게 더 빠름.
        OutputSchema:
            - polars DataFrame, 11 col, corpCount desc 정렬.
        Prerequisites:
            - data/original/dart/docs/{code}/*.zip 로컬 (~30 GB).
        Freshness:
            - 분기 incremental rebuild — mtime > sinceDate 만 필터링.
    """
    if baseDir is None:
        baseDir = Path(_cfg.dataDir) / "original" / "dart" / "docs"
    baseDir = Path(baseDir)
    if not baseDir.exists():
        _log.error("baseDir 없음: %s", baseDir)
        return pl.DataFrame()
    allZips = sorted(baseDir.glob("*/*.zip"))
    if verbose:
        _log.info("전종목 zip: %d", len(allZips))

    bag: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "titles": Counter(),
            "corps": set(),
            "rcepts": set(),
            "parent": None,
        }
    )
    processed = 0
    failed = 0
    t0 = time.perf_counter()

    with mp.Pool(processes=numWorkers) as pool:
        # imap chunk = 32: IO 병목 + worker context switching 균형
        for corp, rcept, entries in pool.imap_unordered(_zipToEntries, allZips, chunksize=32):
            if not entries:
                failed += 1
            else:
                for entry in entries:
                    k = (entry["rawId"], entry["rawTitleCanonical"])
                    v = bag[k]
                    v["titles"][entry["rawTitleRaw"]] += 1
                    v["corps"].add(corp)
                    v["rcepts"].add(rcept)
                    if v["parent"] is None and entry["parentRawId"]:
                        v["parent"] = entry["parentRawId"]
            processed += 1
            if verbose and processed % progressEvery == 0:
                elapsed = time.perf_counter() - t0
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (len(allZips) - processed) / rate if rate > 0 else 0
                _log.info(
                    "[%d/%d] %.1f zip/s, ETA %.1f min, unique entries=%d, failed=%d",
                    processed,
                    len(allZips),
                    rate,
                    eta / 60,
                    len(bag),
                    failed,
                )

    if verbose:
        elapsed = time.perf_counter() - t0
        _log.info(
            "완료: processed=%d failed=%d unique=%d wall=%.1f min",
            processed,
            failed,
            len(bag),
            elapsed / 60,
        )

    rows = []
    for (rawId, titleCanonical), v in bag.items():
        if len(v["corps"]) < minCorpCount:
            continue
        variants = [t for t, _ in v["titles"].most_common()]
        rows.append(
            {
                "rawId": rawId,
                "rawTitleCanonical": titleCanonical,
                "rawTitleVariants": variants,
                "parentRawId": v["parent"],
                "taxonomyVersion": None,
                "firstSeenPeriod": None,
                "lastSeenPeriod": None,
                "corpCount": len(v["corps"]),
                "periodCount": len(v["rcepts"]),
                "occurrenceCount": int(sum(v["titles"].values())),
                "marketNs": "kr",
            }
        )

    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(
        rows,
        schema_overrides={
            "corpCount": pl.UInt32,
            "periodCount": pl.UInt32,
            "occurrenceCount": pl.UInt32,
        },
    ).sort(["corpCount", "occurrenceCount"], descending=[True, True])


def scanRefBaseline(
    codes: list[str] | None = None,
    *,
    minCorpCount: int = 1,
    verbose: bool = False,
) -> pl.DataFrame:
    """검증용 — 5 baseline 종목의 전 기간 zip scan.

    Capabilities:
        지정 codes (기본 5 baseline) 의 전 기간 zip → scanZipFiles → Layer 1 ref table.

    AIContext:
        panelXbrlRef 검증 게이트 입력. 전종목 scanAllZips 의 소규모 검증 버전.

    Guide:
        codes=None 이면 5 baseline (005930/005380/035720/207940/000660). minCorpCount=1 로 전 entry 노출.

    When:
        panelXbrlRef 빌더 검증 (손실 0 / 정렬 확인) 시.

    How:
        codes → 각 code 디렉터리 zip glob → scanZipFiles 위임.

    Args:
        codes: 종목코드 list. None = 5 baseline default.
        minCorpCount: 기본 1 (5 회사 중 1 이상 발견 entry 모두 보기).
        verbose: 진행 로그.

    Returns:
        Layer 1 schema DataFrame. 5 baseline 의 모든 ACLASS entry.

    Requires:
        ``data/original/dart/docs/{code}/*.zip`` 존재.

    Raises:
        없음 — 종목 디렉터리 부재 시 경고 로그 후 skip.

    Examples:
        >>> df = scanRefBaseline(codes=['005930'], minCorpCount=1)  # doctest: +SKIP
        >>> df.height > 50  # doctest: +SKIP
        True

    SeeAlso:
        ``scanAllZips`` — 전종목 버전. ``scanZipFiles`` — 실제 스캔 로직.

    LLM Specifications:
        AntiPatterns:
            - 5 baseline 외 종목 default 추가 금지 — 검증 게이트 일치.
        OutputSchema:
            - polars DataFrame, 11 col.
    """
    if codes is None:
        codes = ["005930", "005380", "035720", "207940", "000660"]
    baseDir = Path(_cfg.dataDir) / "original" / "dart" / "docs"
    allZips: list[Path] = []
    for code in codes:
        codeDir = baseDir / code
        if not codeDir.exists():
            _log.warning("종목 디렉터리 없음: %s", codeDir)
            continue
        zips = sorted(codeDir.glob("*.zip"))
        allZips.extend(zips)
        if verbose:
            _log.info("%s: %d zip", code, len(zips))
    if verbose:
        _log.info("총 %d zip across %d codes", len(allZips), len(codes))
    return scanZipFiles(allZips, minCorpCount=minCorpCount, verbose=verbose)
