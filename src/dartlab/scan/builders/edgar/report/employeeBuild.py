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

from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

EMPLOYEE_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "employeeCount": pl.Int64,
    "source": pl.Utf8,
}

# buildEdgarEmployee 가 panel 에서 읽는 최소 컬럼(메모리. contentRaw 가 전 10-K 텍스트라 무겁다).
_READ_COLS = ["chapter", "period", "contentRaw"]

_HF_REPO = "eddmpython/dartlab-data"
_HF_EMPLOYEE_PATH = "edgar/scan/report/employee.parquet"


def _loadPriorEmployee() -> pl.DataFrame | None:
    """기존 발행본 employee.parquet(HF)을 시드로 로드. 누적 병합용. 실패 시 None.

    panel 텍스트는 30GB(7,300+)라 CI 로컬 캐시는 일부만 보유한다. 매 run 이 로컬 추출분만 쓰면 직원수
    커버리지가 줄어든다. 기존 발행본을 시드로 병합해 한 번 채운 종목이 유지되게 한다(panel backfill 동형 누적).

    Returns:
        pl.DataFrame | None. 기존 발행본(없거나 로드 실패면 None).
    """
    try:
        import os

        from huggingface_hub import hf_hub_download

        from dartlab.core.hfRetry import retryHfCall

        fp = retryHfCall(
            hf_hub_download, _HF_REPO, _HF_EMPLOYEE_PATH, repo_type="dataset", token=os.environ.get("HF_TOKEN")
        )
        return pl.read_parquet(fp)
    except Exception:  # noqa: BLE001 (네트워크/부재 모두 graceful None)
        return None


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
    # 파싱 SSOT 는 providers(L1) employee.parseEmployeeCount. scan(L1.5)이 downward lazy import 로 공유.
    from dartlab.providers.edgar.report.employee import parseEmployeeCount

    byYear: dict[str, int] = {}
    for period, text in zip(panel["period"].to_list(), panel["contentRaw"].to_list()):
        year = str(period or "")[:4]
        if not year.isdigit() or year in byYear:
            continue
        count = parseEmployeeCount(str(text or ""))
        if count is not None:
            byYear[year] = count
    return [{"stockCode": ticker, "year": y, "employeeCount": c, "source": "10-K"} for y, c in sorted(byYear.items())]


def buildEdgarEmployee(*, verbose: bool = False) -> Path:
    """전종목 edgar/panel 에서 edgar/scan/report/employee.parquet 생성. 10-K 직원수 순수 텍스트 추출.

    edgar/panel/{ticker}.parquet 만 순회하며 10-K 본문에서 직원수를 regex 추출한다. 별도 수집 0. lazy
    pushdown(chapter='10-K' + 'employ' 포함)으로 직원 무관 텍스트는 안 읽어 메모리를 절약한다. edgarSync 의
    edgarPanel 갱신 직후 호출(로컬 panel 재사용).

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
    없음. panel 부재/공백이면 빈 parquet 을 쓴다(보조 소스, scan 빌드 무중단).

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
        panel 마다 lazy scan + chapter='10-K' & contentRaw~'employ' 푸시다운 후 employeeRowsFromPanel
        (연도별 첫 유효 regex 매칭)로 누적해 단일 parquet 으로 쓴다.

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
    for fp in parquets:
        ticker = fp.stem.upper()
        try:
            sub = (
                pl.scan_parquet(fp)
                .filter((pl.col("chapter") == "10-K") & pl.col("contentRaw").str.contains("(?i)employ"))
                .select(["period", "contentRaw"])
                .collect()
            )
        except (OSError, pl.exceptions.PolarsError):
            continue
        if sub.is_empty():
            continue
        rows.extend(employeeRowsFromPanel(sub, ticker))

    out = pl.DataFrame(rows, schema=EMPLOYEE_COLS) if rows else pl.DataFrame(schema=EMPLOYEE_COLS)
    # 누적 병합: 기존 발행본을 시드로 합치고 (stockCode, year) 충돌은 로컬 신규 우선(keep=first).
    # CI panel 캐시가 일부라 매 run 로컬분만 쓰면 커버리지가 줄어든다. 시드 병합으로 한 번 채운 종목 유지.
    prior = _loadPriorEmployee()
    if prior is not None and not prior.is_empty():
        prior = prior.select(list(EMPLOYEE_COLS.keys())).cast(EMPLOYEE_COLS)  # 스키마 정합
        out = pl.concat([out, prior], how="vertical_relaxed").unique(subset=["stockCode", "year"], keep="first")
    out = out.sort(["stockCode", "year"])
    outPath = outDir / "employee.parquet"
    out.write_parquet(str(outPath), compression="zstd")
    if verbose:
        _log.info(f"[edgarReport] employee: {out.height}행 ({out['stockCode'].n_unique()}종목) 생성 {outPath}")
    return outPath
