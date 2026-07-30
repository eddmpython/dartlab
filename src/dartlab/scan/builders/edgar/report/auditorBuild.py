"""EDGAR scan 감사인 빌더. 10-K 본문(edgar/panel contentRaw)에서 edgar/scan/report/auditor.parquet 생성.

감사인(auditTrail)은 SEC XBRL 집계(companyfacts)에 없어(dei:AuditorName 은 문서 인라인 전용, 실측 404)
annual filing 감사보고서 텍스트에서 얻는다. ``employeeBuild`` 동형 트랙으로 panel metadata를 먼저
선별하고 bounded content reader로 canonical 법인명과 재임시작연도(auditor since)를 추출한다.

파싱 단일 SSOT 는 providers(L1) ``auditorText.extractAuditorFromText``, 본 scan(L1.5)이 downward import.
실측(auditorProbe): 대형 10사 firm 10/10 · since 9/10, 전부 공지 실제값(KO EY 1921·CAT PwC 1925).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.scan.builders.edgar.helpers import _writeParquetAtomic
from dartlab.scan.builders.edgar.report.employeeBuild import _iterAnnualPanelTexts

_log = getLogger(__name__)

AUDITOR_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "auditor": pl.Utf8,
    "sinceYear": pl.Int64,
}

_HF_REPO = "eddmpython/dartlab-data"
_HF_AUDITOR_PATH = "edgar/scan/report/auditor.parquet"
_BLOB_CAP = 400_000  # 기당 감사 블록 연결 상한(대형 10-K 방어)


def _loadPriorAuditor() -> pl.DataFrame:
    """기존 발행본 auditor.parquet(HF) exact-schema 시드를 로드한다."""
    import os

    from huggingface_hub import hf_hub_download

    from dartlab.core.hfRetry import retryHfCall

    fp = retryHfCall(hf_hub_download, _HF_REPO, _HF_AUDITOR_PATH, repo_type="dataset", token=os.environ.get("HF_TOKEN"))
    prior = pl.read_parquet(fp)
    if prior.schema != pl.Schema(AUDITOR_COLS):
        raise ValueError(f"직전 감사인 스냅샷 schema 불일치: {prior.schema}")
    return prior


def auditorRowsFromPanel(panel: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 panel(10-K 감사 블록)에서 연도별 감사인 행 추출.

    ``period`` 앞 4자리를 회계연도로 보고, 기(period)별 감사 블록을 연결해 법인명·since 를 뽑는다.
    법인명 미검출 연도는 제외(정직 null 미표시).

    Args:
        panel: ``period``·``contentRaw`` 컬럼(10-K 감사 블록 필터 후) DataFrame.
        ticker: stockCode.

    Returns:
        list[dict]. 연도별 감사인 행(stockCode·year·auditor·sinceYear).
    """
    return _auditorRowsFromTexts(
        zip(panel["period"].to_list(), panel["contentRaw"].to_list()),
        ticker,
    )


def _auditorRowsFromTexts(texts: Iterable[tuple[object, object]], ticker: str) -> list[dict]:
    """Python text pair stream에서 연도별 감사인 행을 추출한다."""

    from dartlab.providers.edgar.report.auditorText import extractAuditorFromText

    byYear: dict[str, tuple[str, int | None]] = {}
    grouped: dict[str, list[str]] = {}
    for period, text in texts:
        year = str(period or "")[:4]
        if not year.isdigit():
            continue
        grouped.setdefault(year, []).append(str(text or ""))
    for year, blocks in grouped.items():
        firm, since = extractAuditorFromText(" ".join(blocks)[:_BLOB_CAP])
        if firm:
            byYear[year] = (firm, since)
    return [{"stockCode": ticker, "year": y, "auditor": f, "sinceYear": s} for y, (f, s) in sorted(byYear.items())]


def buildEdgarAuditor(*, verbose: bool = False) -> Path:
    """전종목 edgar/panel 에서 edgar/scan/report/auditor.parquet 생성. 10-K 감사인 순수 텍스트 추출.

    edgar/panel/{ticker}.parquet 만 순회한다(별도 수집 0). metadata 선필터와 bounded content reader로
    annual form 선택 본문만 읽는다. 기존 HF 발행본 시드 병합으로 부분 캐시에서도 커버리지를 유지한다.

    Parameters
    ----------
    verbose : bool
        진행 로그.

    Returns
    -------
    Path
        edgar/scan/report/auditor.parquet 경로.

    Raises
    ------
    기존 발행본 또는 listed panel 로드와 검증이 실패하면 원인을 포함해 전파한다.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report.auditorBuild import buildEdgarAuditor
    >>> p = buildEdgarAuditor(verbose=True)  # doctest: +SKIP
    >>> p.name
    'auditor.parquet'

    Capabilities:
        - 연도별 감사법인(canonical)·재임시작연도 추출. 실측 대형 10사 firm 10/10·since 9/10.
          미검출 기업/연도는 빈 행(패널 자연 미표시).

    AIContext:
        ``scan`` US auditTrail 의 source. 런타임 reportSource 가 market 분기로 KR
        (dart/scan/report/auditOpinion 파생)과 분리 소비.

    Guide:
        - edgarSync edgarPanel 갱신 직후 호출(buildEdgarEmployee 와 함께). 발행은 deployEdgarToHF 자동.
        - 전 유니버스 1회 백필은 HF panel 스트리밍 runner(scratchpad, backfillEmployee 동형)로 수행.

    When:
        edgarSync scan 프리빌드 단계. 직접 호출은 드물다.

    How:
        panel metadata에서 annual form 행 번호를 고르고 bounded content reader로 선택 본문만 읽은 뒤
        기별 블록 연결과 canonical 매칭을 수행한다. 마지막에 기존 시드와 병합한다.

    Requires:
        - edgar/panel/{ticker}.parquet (edgarPanel stage 산출)
        - providers.edgar.report.auditorText (파싱 SSOT)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.report.employeeBuild.buildEdgarEmployee` (동형 panel 텍스트 트랙)
        - :func:`dartlab.providers.edgar.report.auditorText.extractAuditorFromText` (파싱 SSOT)
    """
    from dartlab import config as _cfg

    panelDir = Path(_cfg.dataDir) / "edgar" / "panel"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan" / "report"
    outDir.mkdir(parents=True, exist_ok=True)
    parquets = sorted(panelDir.glob("*.parquet")) if panelDir.exists() else []
    if not parquets and verbose:
        _log.info("[edgarReport] auditor: edgar/panel 부재. 빈 parquet 생성")

    rows: list[dict] = []
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    listedTickers = set(edgarCikToTicker().values())
    listedPanels = [path for path in parquets if path.stem.upper() in listedTickers]

    matchedTickers = 0
    keywords = ("accounting firm", "auditor", "audit report")
    for index, (path, texts) in enumerate(_iterAnnualPanelTexts(listedPanels, keywords), start=1):
        ticker = path.stem.upper()
        if texts:
            matchedTickers += 1
        rows.extend(_auditorRowsFromTexts(texts, ticker))
        if verbose and (index % 100 == 0 or index == len(listedPanels)):
            _log.info("[edgarReport] auditor panel: %s/%s", index, len(listedPanels))
    if verbose:
        _log.info(
            "[edgarReport] auditor panel filter: files=%s, matchedTickers=%s",
            len(listedPanels),
            matchedTickers,
        )

    out = _auditorFrame(rows, listedTickers)
    return _writeAuditorFrame(out, outDir, verbose=verbose)


def _auditorFrame(rows: list[dict], listedTickers: set[str]) -> pl.DataFrame:
    """로컬 감사인 행과 exact-schema prior를 listed identity로 병합한다."""

    out = pl.DataFrame(rows, schema=AUDITOR_COLS) if rows else pl.DataFrame(schema=AUDITOR_COLS)
    prior = _loadPriorAuditor()
    if not prior.is_empty():
        prior = prior.filter(pl.col("stockCode").is_in(listedTickers))
        out = pl.concat([out, prior], how="vertical_relaxed").unique(subset=["stockCode", "year"], keep="first")
    return out.sort(["stockCode", "year"])


def _writeAuditorFrame(out: pl.DataFrame, outDir: Path, *, verbose: bool) -> Path:
    """검증된 auditor frame을 원자 교체한다."""

    outPath = outDir / "auditor.parquet"
    _writeParquetAtomic(out, outPath)
    if verbose:
        _log.info(f"[edgarReport] auditor: {out.height}행 ({out['stockCode'].n_unique()}종목) 생성 {outPath}")
    return outPath


def buildEdgarPanelReports(*, verbose: bool = False) -> list[Path]:
    """employee와 auditor를 같은 bounded panel pass에서 만들고 prior와 병합한다."""

    from dartlab import config as _cfg
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker
    from dartlab.scan.builders.edgar.report import employeeBuild

    panelDir = Path(_cfg.dataDir) / "edgar" / "panel"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan" / "report"
    outDir.mkdir(parents=True, exist_ok=True)
    listedTickers = set(edgarCikToTicker().values())
    listedPanels = [path for path in sorted(panelDir.glob("*.parquet")) if path.stem.upper() in listedTickers]

    keywords = ("employ", "accounting firm", "auditor", "audit report")
    employeeRows: list[dict] = []
    auditorRows: list[dict] = []
    for index, (path, texts) in enumerate(employeeBuild._iterAnnualPanelTexts(listedPanels, keywords), start=1):
        ticker = path.stem.upper()
        employeeTexts: list[tuple[str, str]] = []
        auditorTexts: list[tuple[str, str]] = []
        for period, content in texts:
            lowered = content.casefold()
            pair = (period, content)
            if "employ" in lowered:
                employeeTexts.append(pair)
            if any(keyword in lowered for keyword in keywords[1:]):
                auditorTexts.append(pair)
        employeeRows.extend(employeeBuild._employeeRowsFromTexts(employeeTexts, ticker))
        auditorRows.extend(_auditorRowsFromTexts(auditorTexts, ticker))
        if verbose and (index % 100 == 0 or index == len(listedPanels)):
            _log.info("[edgarReport] employee+auditor panel: %s/%s", index, len(listedPanels))

    employeeFrame = employeeBuild._employeeFrame(employeeRows, listedTickers)
    auditorFrame = _auditorFrame(auditorRows, listedTickers)
    return [
        employeeBuild._writeEmployeeFrame(employeeFrame, outDir, verbose=verbose),
        _writeAuditorFrame(auditorFrame, outDir, verbose=verbose),
    ]


__all__ = [
    "AUDITOR_COLS",
    "auditorRowsFromPanel",
    "buildEdgarAuditor",
    "buildEdgarPanelReports",
]
