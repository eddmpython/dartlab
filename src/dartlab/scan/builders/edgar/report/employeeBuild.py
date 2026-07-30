"""EDGAR scan 직원수 빌더. 10-K 본문(edgar/panel contentRaw) regex 로 edgar/scan/report/employee.parquet 생성.

직원수(workforce)는 SEC XBRL 집계(companyfacts·companyconcept)에 ``EntityNumberOfEmployees`` 가 없어서
(실측 404) 10-K 본문에서만 얻는다. edgar/panel 의 ``contentRaw``(10-K 텍스트 SSOT. 7,300+ 종목 발행)에
직원수 정규식을 적용해 연도별 직원수를 추출한다. companyfacts 직독인 다른 report 관점(buildEdgarReport)과
달리 panel 텍스트가 소스라 별 빌더로 분리한다.

파싱 단일 SSOT. ``parseEmployeeCount`` 는 providers(L1) ``edgar/report/employee`` 가 보유하고 본 scan(L1.5)이
downward import 로 공유한다(중복 0). KR 정기보고서 직원현황(성별·정규/계약 분해)과 달리 US 10-K 는 총원
단일값이라 employeeCount 단일 컬럼이다(정직한 충실도 차이).
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from dartlab.core.logger import getLogger
from dartlab.scan.builders.edgar.helpers import _writeParquetAtomic

_log = getLogger(__name__)

EMPLOYEE_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "employeeCount": pl.Int64,
    "source": pl.Utf8,
}

_HF_REPO = "eddmpython/dartlab-data"
_HF_EMPLOYEE_PATH = "edgar/scan/report/employee.parquet"
_ANNUAL_PANEL_CHAPTERS = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A")
_PANEL_METADATA_BATCH_ROWS = 4096
_PANEL_READ_WORKERS = 2


def _loadPriorEmployee() -> pl.DataFrame:
    """기존 발행본 employee.parquet(HF)을 누적 병합 시드로 로드한다.

    panel 텍스트는 30GB(7,300+)라 CI 로컬 캐시는 일부만 보유한다. 매 run 이 로컬 추출분만 쓰면 직원수
    커버리지가 줄어든다. 기존 발행본을 시드로 병합해 한 번 채운 종목이 유지되게 한다(panel backfill 동형 누적).

    Returns:
        pl.DataFrame. exact schema 기존 발행본.
    """
    import os

    from huggingface_hub import hf_hub_download

    from dartlab.core.hfRetry import retryHfCall

    fp = retryHfCall(
        hf_hub_download, _HF_REPO, _HF_EMPLOYEE_PATH, repo_type="dataset", token=os.environ.get("HF_TOKEN")
    )
    prior = pl.read_parquet(fp)
    if prior.schema != pl.Schema(EMPLOYEE_COLS):
        raise ValueError(f"직전 임직원 스냅샷 schema 불일치: {prior.schema}")
    return prior


def employeeRowsFromPanel(panel: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 panel(10-K contentRaw) 에서 연도별 직원수 행 추출. 연도당 첫 유효 매칭.

    ``period`` 앞 4자리를 회계연도로 보고, 연도마다 첫 직원수 매칭을 채택한다(10-K 본문 한정 입력 가정.
    빌더가 chapter='10-K' 푸시다운). 무매칭 연도는 제외.

    Args:
        panel: ``period``·``contentRaw`` 컬럼(10-K 필터 후) DataFrame.
        ticker: stockCode.

    Returns:
        list[dict]. 연도별 직원수 행(stockCode·year·employeeCount·source).
    """
    return _employeeRowsFromTexts(
        zip(panel["period"].to_list(), panel["contentRaw"].to_list()),
        ticker,
    )


def _employeeRowsFromTexts(texts: Iterable[tuple[object, object]], ticker: str) -> list[dict]:
    """Python text pair stream에서 연도별 직원수를 추출한다."""

    from dartlab.providers.edgar.report.employee import parseEmployeeCount

    byYear: dict[str, int] = {}
    for period, text in texts:
        year = str(period or "")[:4]
        if not year.isdigit() or year in byYear:
            continue
        count = parseEmployeeCount(str(text or ""))
        if count is not None:
            byYear[year] = count
    return [{"stockCode": ticker, "year": y, "employeeCount": c, "source": "10-K"} for y, c in sorted(byYear.items())]


def _readAnnualPanelTexts(path: Path, keywords: tuple[str, ...]) -> list[tuple[str, str]]:
    """metadata 선필터 뒤 bounded reader로 annual form 선택 content만 읽는다."""

    from dartlab.scan.builders.kr.network import _readSelectedContents

    if not keywords:
        raise ValueError("EDGAR panel content keyword가 비어 있습니다")
    contents: dict[int, str] = {}
    periods: dict[int, str] = {}
    try:
        with pq.ParquetFile(path, memory_map=False, pre_buffer=False) as parquet:
            required = {"chapter", "period", "contentRaw"}
            missing = sorted(required - set(parquet.schema_arrow.names))
            if missing:
                raise ValueError(f"EDGAR panel 필수 컬럼 누락: path={path}, columns={missing}")
            rowOffset = 0
            for batch in parquet.iter_batches(
                batch_size=_PANEL_METADATA_BATCH_ROWS,
                columns=["chapter", "period"],
                use_threads=False,
            ):
                chapters = batch.column("chapter").to_pylist()
                batchPeriods = batch.column("period").to_pylist()
                for localIndex, chapter in enumerate(chapters):
                    if chapter in _ANNUAL_PANEL_CHAPTERS and batchPeriods[localIndex]:
                        periods[rowOffset + localIndex] = str(batchPeriods[localIndex])
                rowOffset += batch.num_rows
            contents = _readSelectedContents(path, parquet, set(periods))
        loweredKeywords = tuple(keyword.casefold() for keyword in keywords)
        return [
            (periods[index], content)
            for index, content in contents.items()
            if any(keyword in content.casefold() for keyword in loweredKeywords)
        ]
    finally:
        contents.clear()
        pa.default_memory_pool().release_unused()


def _iterAnnualPanelTexts(
    paths: list[Path],
    keywords: tuple[str, ...],
) -> Iterable[tuple[Path, list[tuple[str, str]]]]:
    """작은 panel은 2개까지 겹치고 큰 content 파일군은 완전히 직렬화한다."""

    from dartlab.scan.builders.kr.network import panelContentRequiresSerialRead

    parallelPaths: list[Path] = []
    serialPaths: list[Path] = []
    for path in paths:
        try:
            target = serialPaths if panelContentRequiresSerialRead(path) else parallelPaths
        except (OSError, ValueError, RuntimeError) as exc:
            raise RuntimeError(f"EDGAR panel footer 읽기 실패: ticker={path.stem.upper()}, path={path}") from exc
        target.append(path)

    for path in serialPaths:
        try:
            yield path, _readAnnualPanelTexts(path, keywords)
        except (OSError, ValueError, RuntimeError, pl.exceptions.PolarsError) as exc:
            raise RuntimeError(f"EDGAR listed panel 읽기 실패: ticker={path.stem.upper()}, path={path}") from exc

    with ThreadPoolExecutor(max_workers=_PANEL_READ_WORKERS, thread_name_prefix="edgar-panel-report") as executor:
        futureToPath = {executor.submit(_readAnnualPanelTexts, path, keywords): path for path in parallelPaths}
        try:
            for future in as_completed(futureToPath):
                path = futureToPath[future]
                yield path, _panelTextResult(future, path)
        except BaseException:
            for future in futureToPath:
                future.cancel()
            raise


def _panelTextResult(future: Future[list[tuple[str, str]]], path: Path) -> list[tuple[str, str]]:
    """parallel panel future의 실패에 source identity를 붙인다."""

    try:
        return future.result()
    except (OSError, ValueError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise RuntimeError(f"EDGAR listed panel 읽기 실패: ticker={path.stem.upper()}, path={path}") from exc


def buildEdgarEmployee(*, verbose: bool = False) -> Path:
    """전종목 edgar/panel 에서 edgar/scan/report/employee.parquet 생성. 10-K 직원수 순수 텍스트 추출.

    edgar/panel/{ticker}.parquet 만 순회하며 annual form 본문에서 직원수를 regex 추출한다. 별도 수집 0.
    metadata를 먼저 읽고 bounded content reader로 선택 행만 해독한다. edgarSync의 edgarPanel 갱신 직후
    호출해 로컬 panel을 재사용한다.

    Parameters
    ----------
    verbose : bool
        진행 로그.

    Returns
    -------
    Path
        edgar/scan/report/employee.parquet 경로.

    Raises
    ------
    기존 발행본 또는 listed panel 로드와 검증이 실패하면 원인을 포함해 전파한다.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report.employeeBuild import buildEdgarEmployee
    >>> p = buildEdgarEmployee(verbose=True)  # doctest: +SKIP
    >>> p.name
    'employee.parquet'

    Capabilities:
        - 7,300+ 종목 panel 텍스트에서 연도별 직원수 추출. XBRL 부재라 10-K 본문이 유일 소스. 무매칭
          기업/연도는 빈 행(패널 자연 미표시).

    AIContext:
        ``scan`` US workforce 의 source. companyfacts 직독 report 관점과 별개로 panel 텍스트가 소스다.
        런타임 reportSource 가 market 분기로 KR(dart/scan/report/employee)과 분리 소비할 예정.

    Guide:
        - edgarSync edgarPanel 갱신 직후 호출. 발행은 deployEdgarToHF(['scan']) 가 자동.
        - panel 로컬 커버리지에 비례(panel SSOT 가 채워질수록 직원수도 증가).

    When:
        edgarSync scan 프리빌드 단계(buildEdgarReport 직후). 직접 호출은 드물다.

    How:
        panel metadata에서 annual form 행 번호를 고르고 bounded content reader로 선택 본문만 읽은 뒤
        연도별 첫 유효 regex 매칭을 누적한다.

    Requires:
        - edgar/panel/{ticker}.parquet (edgarPanel stage 산출)

    SeeAlso:
        - :func:`parseEmployeeCount` (파싱 SSOT. L4 employee 공유)
        - :func:`dartlab.scan.builders.edgar.report.build.buildEdgarReport` (companyfacts 직독 3관점)
    """
    from dartlab import config as _cfg

    panelDir = Path(_cfg.dataDir) / "edgar" / "panel"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan" / "report"
    outDir.mkdir(parents=True, exist_ok=True)
    # panel 은 보조 소스(커버리지 가변). 부재/공백이어도 빈 parquet 으로 graceful 처리(scan 빌드 무중단).
    parquets = sorted(panelDir.glob("*.parquet")) if panelDir.exists() else []
    if not parquets and verbose:
        _log.info("[edgarReport] employee: edgar/panel 부재. 빈 parquet 생성")

    rows: list[dict] = []
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    listedTickers = set(edgarCikToTicker().values())
    listedPanels = [path for path in parquets if path.stem.upper() in listedTickers]

    matchedTickers = 0
    for index, (path, texts) in enumerate(_iterAnnualPanelTexts(listedPanels, ("employ",)), start=1):
        ticker = path.stem.upper()
        if texts:
            matchedTickers += 1
        rows.extend(_employeeRowsFromTexts(texts, ticker))
        if verbose and (index % 100 == 0 or index == len(listedPanels)):
            _log.info("[edgarReport] employee panel: %s/%s", index, len(listedPanels))
    if verbose:
        _log.info(
            "[edgarReport] employee panel filter: files=%s, matchedTickers=%s",
            len(listedPanels),
            matchedTickers,
        )

    out = _employeeFrame(rows, listedTickers)
    return _writeEmployeeFrame(out, outDir, verbose=verbose)


def _employeeFrame(rows: list[dict], listedTickers: set[str]) -> pl.DataFrame:
    """로컬 직원수 행과 exact-schema prior를 listed identity로 병합한다."""

    out = pl.DataFrame(rows, schema=EMPLOYEE_COLS) if rows else pl.DataFrame(schema=EMPLOYEE_COLS)
    # 누적 병합: 기존 발행본을 시드로 합치고 (stockCode, year) 충돌은 로컬 신규 우선(keep=first).
    # CI panel 캐시가 일부라 매 run 로컬분만 쓰면 커버리지가 줄어든다. 시드 병합으로 한 번 채운 종목 유지.
    prior = _loadPriorEmployee()
    if not prior.is_empty():
        prior = prior.filter(pl.col("stockCode").is_in(listedTickers))
        out = pl.concat([out, prior], how="vertical_relaxed").unique(subset=["stockCode", "year"], keep="first")
    return out.sort(["stockCode", "year"])


def _writeEmployeeFrame(out: pl.DataFrame, outDir: Path, *, verbose: bool) -> Path:
    """검증된 employee frame을 원자 교체한다."""

    outPath = outDir / "employee.parquet"
    _writeParquetAtomic(out, outPath)
    if verbose:
        _log.info(f"[edgarReport] employee: {out.height}행 ({out['stockCode'].n_unique()}종목) 생성 {outPath}")
    return outPath
