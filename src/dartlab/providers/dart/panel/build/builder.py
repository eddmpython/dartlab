"""종목별 DART zip을 16-col flat panel artifact로 변환한다.

한 회사의 zip만 읽어 XML, walker, horizontalize, disclosureKey, leaf split을 거친 뒤
공시별 bounded stage를 원자 조립한다. 기간은 접수번호가 아니라 표지 사업연도 종료일에서
계산하고, contentRaw와 receipt 경계를 보존한다. 최종 경로는
``data/dart/panel/{code}.parquet`` 단일 파일이다.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import lxml.etree as etree
import polars as pl

import dartlab.config as _cfg

from ..mapper import resolveBatch
from ..period import periodFromEnd
from ..schema import PANEL_SCHEMA
from .artifactWriter import PanelArtifactAssembler, writePanelStage
from .dechunkNotes import dechunkNotes
from .documentProcess import (
    DocumentInput,
    DocumentProcessRequest,
    DocumentStage,
    runDocumentProcess,
)
from .documentSource import (
    PanelBuildError,
    _expandedZipBytes,
    _readZip,
    _readZipBytes,
)
from .horizontalize import horizontalize
from .leafSplit import splitLeafTypes
from .refScan import scanRefBaseline
from .walker import detectSchemaEra, walkSections

_log = logging.getLogger(__name__)

_DOCUMENTS_PER_PROCESS = 12
_EXPANDED_BYTES_PER_PROCESS = 48 * 1024 * 1024
_ZIP_BYTES_PER_PROCESS = 64 * 1024 * 1024


def panelXbrlRefPath() -> "Path":
    """panelXbrlRef ref table 경로 — refScan 산출 + build(v1 fuzzy) 입력 SSOT.

    Args:
        없음.

    Returns:
        ``data/dart/panelXbrlRef.parquet`` Path.

    Raises:
        없음.

    Example:
        >>> panelXbrlRefPath().name
        'panelXbrlRef.parquet'

    SeeAlso:
        - ``refScan.scanAllZips`` — 본 경로 생산.
        - ``buildPanelAll`` — 본 ref 로 옛 양식(v1) fuzzy 매칭.

    Requires:
        - dartlab.config.

    Capabilities:
        - ref truth 단일 경로 — refScan write·build read 공유 (build 가 ref 경로 SSOT 소유).

    Guide:
        - refScan 후 build(v1 fuzzy)·online sync entry 가 본 경로 참조.

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
            - config.dataDir → data/dart/panelXbrlRef.parquet.
        TargetMarkets:
            - KR (DART).
    """
    # 패키지 동봉(git 추적·wheel) — data/ 가 아님. 뼈대는 코드와 함께 버전·공유 (data/ 는 gitignore).
    return Path(__file__).resolve().parent / "refScan" / "panelXbrlRef.parquet"


# 표지 "사업연도 YYYY년 MM월 DD일 부터 YYYY년 MM월 DD일 까지" — 종료(year, month) 추출.
_FISCAL_PERIOD_RE = re.compile(
    r"사업연도\s+\d{4}\s*년\s+\d{1,2}\s*월\s+\d{1,2}\s*일\s+부터\s+(\d{4})\s*년\s+(\d{1,2})\s*월\s+\d{1,2}\s*일"
)


def _periodFromXml(root, rceptNo: str) -> str:
    """XML 표지의 "사업연도" 종료일 → calendar quarter (..period.periodFromEnd).

    1순위 = 표지 "사업연도 ... 부터 YYYY년 MM월" 종료(year, month) → periodFromEnd.
    fallback = DOCUMENT-NAME ACODE + rcept_no 접수월 추정 (표지 패턴 미발견 시).

    Args:
        root: lxml etree root.
        rceptNo: 접수번호 (fallback 연·월 추정).

    Returns:
        "YYYYQn" period 키.

    Raises:
        없음.

    Example:
        >>> _periodFromXml(root, "20240514000001")  # doctest: +SKIP
    """
    try:
        bodyText = "".join(root.itertext())[:5000]
    except (TypeError, AttributeError):
        bodyText = ""

    m = _FISCAL_PERIOD_RE.search(bodyText)
    if m:
        return periodFromEnd(int(m.group(1)), int(m.group(2)))

    # fallback — ACODE + 접수월
    docName = root.find(".//DOCUMENT-NAME")
    acode = (docName.get("ACODE", "") if docName is not None else "") or ""
    year = rceptNo[:4]
    month = int(rceptNo[4:6]) if rceptNo[4:6].isdigit() else 1
    if acode == "11011":
        suffix = "Q4"
        if month <= 4:
            year = _prevYear(year)
    elif acode == "11012":
        suffix = "Q2"
    elif acode == "11013":
        suffix = "Q1" if month <= 6 else "Q3"
    elif acode == "11014":
        suffix = "Q3"
    elif acode in ("00760", "00761"):
        suffix = "Q4"
        if month <= 4:
            year = _prevYear(year)
    else:
        suffix = "Q4"
    return f"{year}{suffix}"


def _prevYear(year: str) -> str:
    """연도 문자열 → 직전 연도 문자열 (변환 실패 시 원본).

    Args:
        year: "YYYY" 문자열.

    Returns:
        직전 연도 "YYYY". int 변환 실패 시 원본 그대로.

    Raises:
        없음.

    Example:
        >>> _prevYear("2024")
        '2023'
    """
    try:
        return str(int(year) - 1)
    except ValueError:
        return year


def _resolvePeriod(roots: list, rceptNo: str) -> str:
    """zip 의 전 XML root 중 **명시 사업연도 표지를 가진 본문 우선**으로 period 1회 결정.

    sorted XML 의 첫 XML 은 첨부(감사보고서·내부회계 등, 표지 없음)일 수 있어 ACODE 휴리스틱으로
    분기 오귀속 위험. 따라서 전 root 를 훑어 ``_FISCAL_PERIOD_RE`` 명시 매치(보통 본문 표지)를 1순위로,
    없을 때만 첫 root 의 ACODE+접수월 fallback(``_periodFromXml``).

    Args:
        roots: 파싱 성공 lxml root list (≥1).
        rceptNo: 접수번호 (fallback 연·월).

    Returns:
        "YYYYQn" period 키.

    Raises:
        없음.

    Example:
        >>> _resolvePeriod([bodyRoot, attachRoot], "20240514000001")  # doctest: +SKIP
    """
    for root in roots:
        explicitPeriod = _explicitPeriod(root)
        if explicitPeriod is not None:
            return explicitPeriod
    return _periodFromXml(roots[0], rceptNo)  # 표지 없음 → 첫 root ACODE fallback


def _explicitPeriod(root: Any) -> str | None:
    """XML root의 명시 사업연도 종료일을 period로 바꾼다."""

    try:
        bodyText = "".join(root.itertext())[:5000]
    except (TypeError, AttributeError):
        return None
    match = _FISCAL_PERIOD_RE.search(bodyText)
    if match is None:
        return None
    return periodFromEnd(int(match.group(1)), int(match.group(2)))


def _parseXmlRoot(
    xml: str,
    parser: etree.XMLParser,
    *,
    code: str,
    receiptNumber: str,
    memberIndex: int,
) -> Any:
    try:
        root = etree.fromstring(xml.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        source = f"{code}/{receiptNumber}#xml[{memberIndex}]"
        raise PanelBuildError("xml_parse", source, exc, receiptNumber=receiptNumber) from exc
    if root is None:
        cause = ValueError("XML root가 없습니다")
        source = f"{code}/{receiptNumber}#xml[{memberIndex}]"
        raise PanelBuildError("xml_schema", source, cause, receiptNumber=receiptNumber) from cause
    return root


def _resolvePeriodFromXmls(xmls: list[str], receiptNumber: str, code: str) -> str:
    """XML member를 하나씩 열어 명시 period를 찾고 DOM을 즉시 해제한다."""

    if not xmls:
        cause = ValueError("XML member가 없습니다")
        raise PanelBuildError("xml_schema", f"{code}/{receiptNumber}", cause, receiptNumber=receiptNumber) from cause
    parser = etree.XMLParser(recover=True, huge_tree=True)
    fallbackPeriod: str | None = None
    for memberIndex, xml in enumerate(xmls):
        root = _parseXmlRoot(
            xml,
            parser,
            code=code,
            receiptNumber=receiptNumber,
            memberIndex=memberIndex,
        )
        if fallbackPeriod is None:
            fallbackPeriod = _periodFromXml(root, receiptNumber)
        explicitPeriod = _explicitPeriod(root)
        del root
        if explicitPeriod is not None:
            return explicitPeriod
    if fallbackPeriod is None:
        cause = ValueError("period를 판정할 XML root가 없습니다")
        raise PanelBuildError("period", f"{code}/{receiptNumber}", cause, receiptNumber=receiptNumber) from cause
    return fallbackPeriod


def _xmlsToPeriodRows(
    xmls: list[str],
    rcept: str,
    code: str,
    refDf: pl.DataFrame | None,
    matchThreshold: float,
) -> dict[str, list[dict]]:
    """한 zip(rcept)의 XML 문자열 list → {period: [row]} (zip/bytes/online 공통 walker 코어).

    period 는 전 XML 중 명시 사업연도 표지를 가진 본문 우선(``_resolvePeriod``)으로 1회 결정 → 같은 zip
    의 모든 XML row 에 동일 부착(1 zip = 1 rcept = 1 report = 1 period). walker(손실0/dup0) row 에
    period/corp/rceptNo/disclosureKey(None) 부착. buildPanel(disk)·buildPanelFromStream(online) 둘 다 호출.

    Args:
        xmls: 한 zip 의 decoded XML 문자열 list.
        rcept: 접수번호.
        code: 종목코드.
        refDf: 옛 양식(v1) fuzzy 매칭 ref table.
        matchThreshold: fuzzy Jaccard threshold.

    Returns:
        ``{period: [row dict]}``.

    Raises:
        없음 — XML 파싱 실패 XML 은 skip.

    Example:
        >>> _xmlsToPeriodRows(xmls, "20240514000001", "005930", ref, 0.70)  # doctest: +SKIP
    """
    period = _resolvePeriodFromXmls(xmls, rcept, code)
    parser = etree.XMLParser(recover=True, huge_tree=True)
    periodRows: dict[str, list[dict]] = {}
    for memberIndex in range(len(xmls)):
        root = _parseXmlRoot(
            xmls[memberIndex],
            parser,
            code=code,
            receiptNumber=rcept,
            memberIndex=memberIndex,
        )
        xmls[memberIndex] = ""
        era = detectSchemaEra(root)
        for row in walkSections(root, era, refDf, matchThreshold=matchThreshold):
            row["period"] = period
            row["corp"] = code
            row["rceptNo"] = rcept
            row["disclosureKey"] = None
            periodRows.setdefault(period, []).append(row)
        del root
    return periodRows


def _finalizePeriodRows(rows: list[dict]) -> pl.DataFrame:
    """한 공시의 walker 행을 최종 16-col panel frame으로 바꾼다."""

    frame = pl.DataFrame(rows, schema={key: value for key, value in PANEL_SCHEMA.items() if key != "leafType"})
    frame = horizontalize(frame)
    frame = resolveBatch(frame, marketNs="kr")
    frame = dechunkNotes(frame)
    frame = splitLeafTypes(frame).select(PANEL_SCHEMA.keys())
    return frame.with_columns(pl.int_range(pl.len(), dtype=pl.UInt32).alias("blockOrder"))


def _documentChunks(documents: Iterable[DocumentInput]) -> Iterable[tuple[DocumentInput, ...]]:
    """공시 입력을 중복 receipt 없이 개수와 해제 크기 제한 묶음으로 자른다.

    Args:
        documents: 회사 하나의 순서 있는 공시 입력.

    Returns:
        최대 12개, XML 해제 크기 최대 48MiB와 online ZIP 운반 크기 최대 64MiB인 tuple iterable.

    Raises:
        ValueError: receipt 중복 또는 해제 크기가 0 이하일 때.
        PanelBuildError: 단일 공시가 process byte 상한을 넘을 때.

    Example:
        >>> [len(chunk) for chunk in _documentChunks(documents)]  # doctest: +SKIP
        [12, 5]
    """

    chunk: list[DocumentInput] = []
    chunkBytes = 0
    chunkTransportBytes = 0
    seenReceipts: set[str] = set()
    for document in documents:
        if document.receiptNumber in seenReceipts:
            raise ValueError(f"panel document receipt가 중복되었습니다: {document.receiptNumber}")
        if document.expandedBytes <= 0:
            raise ValueError(f"panel document 해제 크기가 잘못됐습니다: {document.receiptNumber}")
        if document.transportBytes < 0:
            raise ValueError(f"panel document 운반 크기가 잘못됐습니다: {document.receiptNumber}")
        if document.expandedBytes > _EXPANDED_BYTES_PER_PROCESS:
            cause = MemoryError(
                "단일 panel document가 process 입력 상한을 초과했습니다: "
                f"expandedBytes={document.expandedBytes}, max={_EXPANDED_BYTES_PER_PROCESS}"
            )
            raise PanelBuildError(
                "document_memory",
                document.zipPath or "memory",
                cause,
                receiptNumber=document.receiptNumber,
            ) from cause
        if document.transportBytes > _ZIP_BYTES_PER_PROCESS:
            cause = MemoryError(
                "단일 online panel ZIP이 process 운반 상한을 초과했습니다: "
                f"transportBytes={document.transportBytes}, max={_ZIP_BYTES_PER_PROCESS}"
            )
            raise PanelBuildError(
                "document_memory",
                document.zipPath or "memory",
                cause,
                receiptNumber=document.receiptNumber,
            ) from cause
        seenReceipts.add(document.receiptNumber)
        if chunk and (
            len(chunk) == _DOCUMENTS_PER_PROCESS
            or chunkBytes + document.expandedBytes > _EXPANDED_BYTES_PER_PROCESS
            or chunkTransportBytes + document.transportBytes > _ZIP_BYTES_PER_PROCESS
        ):
            yield tuple(chunk)
            chunk = []
            chunkBytes = 0
            chunkTransportBytes = 0
        chunk.append(document)
        chunkBytes += document.expandedBytes
        chunkTransportBytes += document.transportBytes
    if chunk:
        yield tuple(chunk)


def _processDocumentInput(
    document: DocumentInput,
    request: DocumentProcessRequest,
    refDf: pl.DataFrame,
) -> tuple[DocumentStage, ...]:
    """단일 공시 입력을 변환해 자식 프로세스 전용 stage로 기록한다.

    Args:
        document: 경로 또는 bytes 하나를 가진 공시 입력.
        request: 회사, ref, stage 경로와 매칭 기준.
        refDf: 자식 프로세스가 읽은 제목 매칭 기준표.

    Returns:
        공시에서 생성된 period별 stage metadata.

    Raises:
        PanelBuildError: zip, XML 또는 변환 실패.
        ValueError: 입력원이 없거나 둘 다 있거나 receipt가 파일명과 다를 때.

    Example:
        >>> _processDocumentInput(document, request, refDf)  # doctest: +SKIP
    """

    hasPath = document.zipPath is not None
    hasBytes = document.zipBytes is not None
    if hasPath == hasBytes:
        raise ValueError("panel document input은 zipPath와 zipBytes 중 정확히 하나가 필요합니다")
    if document.zipPath is not None:
        if document.transportBytes != 0:
            raise ValueError("disk panel document의 transportBytes는 0이어야 합니다")
        receiptNumber, xmls = _readZip(Path(document.zipPath))
        if receiptNumber != document.receiptNumber:
            raise ValueError(
                f"panel document receipt가 파일명과 다릅니다: expected={document.receiptNumber}, actual={receiptNumber}"
            )
    else:
        assert document.zipBytes is not None
        if document.transportBytes != len(document.zipBytes):
            raise ValueError(
                "online panel document의 transportBytes가 실제 ZIP 크기와 다릅니다: "
                f"expected={len(document.zipBytes)}, actual={document.transportBytes}"
            )
        receiptNumber, xmls = _readZipBytes(document.zipBytes, document.receiptNumber)

    periodRows = _xmlsToPeriodRows(
        xmls,
        receiptNumber,
        request.code,
        refDf,
        request.matchThreshold,
    )
    stages: list[DocumentStage] = []
    stageRoot = Path(request.stageRoot)
    for periodIndex, (period, rows) in enumerate(periodRows.items()):
        if not rows:
            continue
        frame = _finalizePeriodRows(rows)
        stagePath = stageRoot / f"document-{document.sequence:08d}-{periodIndex:02d}.parquet"
        writePanelStage(frame, stagePath)
        stages.append(
            DocumentStage(
                path=str(stagePath),
                period=period,
                receiptNumber=receiptNumber,
                sequence=document.sequence,
            )
        )
        del frame
    return tuple(stages)


def _writeCompanyInputs(
    documents: Iterable[DocumentInput],
    *,
    code: str,
    refDf: pl.DataFrame,
    matchThreshold: float,
    outBaseDir: Path,
    overwrite: bool,
    merge: bool,
    verbose: bool,
) -> dict[str, int]:
    """공시를 bounded 자식 프로세스에서 변환하고 회사 artifact를 원자 조립한다.

    Args:
        documents: 디스크 경로 또는 메모리 bytes를 가진 공시 입력 iterable.
        code: 단일 회사 종목코드.
        refDf: 옛 양식 제목 매칭 기준표.
        matchThreshold: fuzzy Jaccard 하한.
        outBaseDir: 회사 panel artifact 출력 폴더.
        overwrite: 기존 artifact 교체 허용 여부.
        merge: 같은 receipt만 교체하는 증분 여부.
        verbose: 완료 로그 출력 여부.

    Returns:
        변경된 ``{period: rowCount}``.

    Raises:
        PanelBuildError: 자식 변환, stage 검증 또는 원자 발행 실패.

    Example:
        >>> _writeCompanyInputs(inputs, code="005930", refDf=ref, outBaseDir=out)  # doctest: +SKIP
    """

    destination = outBaseDir / f"{code}.parquet"
    result: dict[str, int] = {}
    totalRows = 0
    with PanelArtifactAssembler(destination) as assembler:
        refPath = assembler.stageRoot / "reference.parquet"
        refDf.write_parquet(refPath, compression="zstd", statistics=True)
        try:
            for chunk in _documentChunks(documents):
                request = DocumentProcessRequest(
                    code=code,
                    refPath=str(refPath),
                    stageRoot=str(assembler.stageRoot),
                    documents=chunk,
                    matchThreshold=matchThreshold,
                )
                outcome = runDocumentProcess(
                    request,
                    _processDocumentInput,
                )
                if outcome.failure is not None:
                    failure = outcome.failure
                    cause = RuntimeError(f"{failure.errorType}: {failure.message}\n{failure.tracebackText}")
                    source = f"{code}/{failure.receiptNumber or 'document-chunk'}"
                    raise PanelBuildError(
                        "worker_transform",
                        source,
                        cause,
                        receiptNumber=failure.receiptNumber,
                    ) from cause
                expectedReceipts = tuple(document.receiptNumber for document in chunk)
                if outcome.processedReceipts != expectedReceipts:
                    cause = RuntimeError(
                        "panel worker가 입력 receipt 전부를 처리하지 않았습니다: "
                        f"expected={expectedReceipts}, actual={outcome.processedReceipts}"
                    )
                    raise PanelBuildError("worker_protocol", code, cause) from cause
                for receiptNumber in outcome.processedReceipts:
                    assembler.markChangedReceipt(receiptNumber)
                for stage in outcome.stages:
                    rowCount = assembler.registerStage(
                        Path(stage.path),
                        period=stage.period,
                        receiptNumber=stage.receiptNumber,
                        sequence=stage.sequence,
                    )
                    result[stage.period] = result.get(stage.period, 0) + rowCount
        except PanelBuildError:
            raise
        except Exception as exc:
            raise PanelBuildError("worker", code, exc) from exc
        try:
            totalRows = assembler.commit(merge=merge, overwrite=overwrite)
        except Exception as exc:
            raise PanelBuildError("publish", str(destination), exc) from exc

    if verbose and result:
        _log.info(
            "  %s: %d period, %d changed row, %d total row → %s",
            code,
            len(result),
            sum(result.values()),
            totalRows,
            destination.name,
        )
    return result


def buildPanel(
    code: str,
    *,
    refDf: pl.DataFrame | None = None,
    matchThreshold: float = 0.70,
    outBaseDir: Path | str | None = None,
    overwrite: bool = True,
    verbose: bool = False,
) -> dict[str, int]:
    """종목별 panel artifact 빌드. zip을 회사당 flat 16-col parquet로 full rebuild한다.

    Args:
        code: 종목코드 (예: "005930").
        refDf: panelXbrlRef ref table. None = 5 baseline scan.
        matchThreshold: 옛 양식 fuzzy match Jaccard threshold (검증 0.70).
        outBaseDir: 출력 base dir. None = ``data/dart/panel``.
        overwrite: 기존 period parquet overwrite 여부.
        verbose: 진행 로그.

    Returns:
        ``{period: rowCount}`` dict.

    Raises:
        FileNotFoundError: 회사 source zip directory 또는 zip 파일이 없을 때.
        PanelBuildError: zip read, XML parse, transform, stage 또는 publish 실패.

    Example:
        >>> buildPanel("005930", verbose=True)  # doctest: +SKIP
        {'2025Q4': 142, '2025Q3': 98, ...}

    SeeAlso:
        - ``buildPanelAll`` — 전종목 multiprocessing 빌드.
        - ``horizontalize`` — element→section 수평화.
        - ``..mapper.resolveBatch`` — disclosureKey(=native canonicalKey) 부착.

    Requires:
        - data/original/dart/docs/{code}/*.zip. polars. lxml.

    Capabilities:
        - 한 종목의 전 기간 공시를 16-col flat panel artifact로 보존.

    Guide:
        - 운영자/CI build-time 호출. runtime read 는 providers/dart/panel.

    AIContext:
        - strict per-corp 빌드 — 다른 종목 zip 미접근.

    When:
        - 운영자/CI 가 한 종목의 panel artifact 를 (재)생산할 때.

    How:
        - 로컬 zip → walker → horizontalize → resolveBatch → period 별 parquet write.

    LLM Specifications:
        AntiPatterns:
            - 회사당 폴더/{period}.parquet 분할 금지 — flat 단일 {code}.parquet.
            - contentRaw 태그 strip 금지 (R4).
        OutputSchema:
            - ``dict[str, int]`` + data/dart/panel/{code}.parquet (16-col flat).
        Prerequisites:
            - 로컬 zip + refDf (또는 baseline scan).
        Freshness:
            - ref/zip 갱신 시 재빌드.
        Dataflow:
            - zip → walker → horizontalize → resolveBatch → splitLeafTypes → concat → write.
        TargetMarkets:
            - KR (DART).
    """
    if outBaseDir is None:
        outBaseDir = Path(_cfg.dataDir) / "dart" / "panel"
    outBaseDir = Path(outBaseDir)  # flat: data/dart/panel/{code}.parquet (per-company 폴더 없음)

    if refDf is None:
        refDf = scanRefBaseline(minCorpCount=1)

    zipDir = Path(_cfg.dataDir) / "original" / "dart" / "docs" / code
    if not zipDir.exists():
        raise FileNotFoundError(f"panel source zip directory가 없습니다: {zipDir}")
    zipPaths = sorted(zipDir.glob("*.zip"))
    if not zipPaths:
        raise FileNotFoundError(f"panel source zip 파일이 없습니다: {zipDir}")

    documents = (
        DocumentInput(
            receiptNumber=zipPath.stem,
            sequence=sequence,
            expandedBytes=_expandedZipBytes(zipPath, zipPath.stem),
            zipPath=str(zipPath),
        )
        for sequence, zipPath in enumerate(zipPaths)
    )
    return _writeCompanyInputs(
        documents,
        code=code,
        refDf=refDf,
        matchThreshold=matchThreshold,
        outBaseDir=outBaseDir,
        overwrite=overwrite,
        merge=False,
        verbose=verbose,
    )


def buildPanelFromStream(
    code: str,
    docStream: Iterable[tuple[str, bytes]],
    *,
    refDf: pl.DataFrame | None = None,
    matchThreshold: float = 0.70,
    outBaseDir: Path | str | None = None,
    overwrite: bool = True,
    verbose: bool = False,
) -> dict[str, int]:
    """online 1패스 입력을 공시별 stage로 변환해 flat 16-col parquet에 rceptNo upsert한다.

    ``buildPanel``과 같은 ``_writeCompanyInputs`` 코어를 사용한다. 로컬 zip 대신 DART API가
    제공한 bytes를 읽고 같은 receipt만 교체하며 같은 period의 다른 receipt는 보존한다.
    ``data/original/dart/docs``에 zip을 만들지 않으므로 refDf는 반드시 caller가 주입한다.

    Args:
        code: 종목코드 (예 "005930").
        docStream: ``(rceptNo, zipBytes)`` iterable — providers ``streamZipBytes`` 산출(메모리).
        refDf: panelXbrlRef ref table. **None 이면 ValueError** (online 엔 zip 없어 자동 scan 불가).
        matchThreshold: 옛 양식 fuzzy Jaccard threshold (검증 0.70).
        outBaseDir: 출력 base dir. None = ``data/dart/panel``.
        overwrite: 기존 period parquet overwrite 여부.
        verbose: 진행 로그.

    Returns:
        ``{period: changedRowCount}`` dict. 빈 stream이면 빈 dict.

    Raises:
        ValueError: ``refDf is None`` (online 1패스는 ref 자동 scan 금지 — HF seed 필수).

    Example:
        >>> from dartlab.providers.dart.openapi import DartClient, streamZipBytes  # doctest: +SKIP
        >>> stream = ((r, b) for _, r, b in streamZipBytes(DartClient(), [("005930", rcept)]))  # doctest: +SKIP
        >>> buildPanelFromStream("005930", stream, refDf=ref)  # doctest: +SKIP
        {'2025Q1': 142}

    SeeAlso:
        - ``buildPanel`` — 로컬 zip(A) 디스크 트랙 쌍둥이.
        - ``_readZipBytes`` / ``_xmlsToPeriodRows`` / ``_writeCompanyInputs``.
        - ``providers.dart.openapi.streamZipBytes`` — (rcept, bytes) 스트림 생산.

    Requires:
        - polars. lxml. refDf (HF seed panelXbrlRef). providers streamZipBytes (호출측).

    Capabilities:
        - 신규 분기를 zip 디스크 저장 없이 즉시 panel artifact 화 (증분 online sync 트랙).

    Guide:
        - layer-밖 sync entry(`.github/scripts/sync/onlinePanel.py`)가 providers fetch 와 조합 호출.
          gather↛providers(R1) 라 gather 내부에서 fetch 금지 — bytes 만 받음.

    AIContext:
        - strict per-corp (한 종목 stream 만). bytes 는 즉시 소비 후 폐기 (메모리 bounded).

    When:
        - CI online sync 가 신규/변경 분기를 zip 없이 panel 화할 때.

    How:
        - docStream 각 (rcept,bytes) → decode → transform → 즉시 stage → atomic publish.

    LLM Specifications:
        AntiPatterns:
            - refDf None 시 scanRefBaseline 자동 호출 금지 — online 엔 zip 없음(ValueError).
            - 전 종목 stream 한 번에 모으기 금지 — 종목 단위 호출(bytes 메모리 폭주 가드).
            - zip 디스크 저장 금지 — 메모리 1패스 (data/original/dart/docs 안 만듦).
            - 증분 시 같은 period 전체 삭제 금지. 동일 rceptNo만 교체.
        OutputSchema:
            - ``dict[str, int]`` + data/dart/panel/{code}.parquet (16-col flat, rceptNo upsert).
        Prerequisites:
            - refDf (HF seed). docStream (providers streamZipBytes).
        Freshness:
            - 분기 incremental — 신규 rcept 만.
        Dataflow:
            - docStream → _readZipBytes → _writeCompanyInputs(merge) → parquet.
        TargetMarkets:
            - KR (DART).
    """
    if refDf is None:
        raise ValueError(
            "buildPanelFromStream: refDf 필수 — online 1패스는 zip 부재로 자동 scanRefBaseline 금지 (HF seed panelXbrlRef 주입)."
        )

    if outBaseDir is None:
        outBaseDir = Path(_cfg.dataDir) / "dart" / "panel"
    outBaseDir = Path(outBaseDir)  # flat: {code}.parquet

    documents = (
        DocumentInput(
            receiptNumber=receiptNumber,
            sequence=sequence,
            expandedBytes=_expandedZipBytes(raw, receiptNumber),
            transportBytes=len(raw),
            zipBytes=raw,
        )
        for sequence, (receiptNumber, raw) in enumerate(docStream)
    )
    return _writeCompanyInputs(
        documents,
        code=code,
        refDf=refDf,
        matchThreshold=matchThreshold,
        outBaseDir=outBaseDir,
        overwrite=overwrite,
        merge=True,
        verbose=verbose,
    )
