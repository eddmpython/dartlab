"""EDGAR proxy(DEF 14A) 거버넌스 4표 scan 빌더. 감사보수·개별임원보수·실질지분·이사회구성 parquet.

DART 정기보고서 API 가 주는 감사보수(auditContract)·개별임원보수(executivePayIndividual)·최대주주
(majorHolder)의 US 대칭. SEC 는 XBRL 집계로 안 주므로 proxy HTML 표를 파싱한다. 수집은 gather
(``allFilingsContent.getFilingBody``), 파싱은 providers(``proxyParse``), 본 모듈은 오케스트레이션
(메타 선정·순회·emit)만. 메타 SSOT = ``edgar/allFilings/recent.parquet`` (form='DEF 14A').

산출 4종 (``edgar/scan/report/``):
    - ``auditFees.parquet``: stockCode·year·auditFee·auditRelatedFee·taxFee·otherFee (USD)
    - ``execPayIndividual.parquet``: stockCode·year·name·title·totalPay (USD)
    - ``ownership.parquet``: stockCode·year(proxy 제출연도)·holder·pct (%)
    - ``board.parquet``: stockCode·year(proxy 제출연도)·directors·independentDirectors (서술 수치)

리줌: 직전 HF 발행본의 stockCode 는 skip(체크포인트 발행과 함께 죽어도 재실행이 이어감). 파서 미스
(표 없는 특별총회 proxy·펀드)는 그 회사만 빈 결과로 남고 패널 자연 미표시(정직 null).
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

AUDIT_FEES_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "auditFee": pl.Float64,
    "auditRelatedFee": pl.Float64,
    "taxFee": pl.Float64,
    "otherFee": pl.Float64,
}
EXEC_PAY_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "name": pl.Utf8,
    "title": pl.Utf8,
    "totalPay": pl.Float64,
}
OWNERSHIP_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "holder": pl.Utf8,
    "pct": pl.Float64,
}
BOARD_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "directors": pl.Int64,
    "independentDirectors": pl.Int64,
}

_PACE_SECONDS = 0.12  # SEC fair-access(~8req/s)


def proxyRowsFromHtml(html: str, ticker: str, filingYear: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """단일 proxy HTML → (auditFees, execPay, ownership, board) 행 4종 (순수 파싱, 네트워크 0).

    Args:
        html: DEF 14A 전체 HTML.
        ticker: stockCode.
        filingYear: proxy 제출연도(YYYY). ownership·board 의 기준연도.

    Returns:
        tuple[list[dict], list[dict], list[dict], list[dict]]: 스키마별 행. 표/서술 부재는 빈 list.

    Raises:
        없음.

    Example:
        >>> af, ep, ow, bd = proxyRowsFromHtml(html, "AAPL", "2026")  # doctest: +SKIP
    """
    from bs4 import BeautifulSoup

    from dartlab.providers.edgar.report.proxyParse import (
        parseAuditFees,
        parseBeneficialOwnership,
        parseBoardComposition,
        parseSummaryComp,
    )

    soup = BeautifulSoup(html, "lxml")  # 1회 파싱해 4파서 공유 (대형 proxy 재파싱 제거)
    af = [{"stockCode": ticker, **r} for r in parseAuditFees(soup)]
    ep = [{"stockCode": ticker, **r} for r in parseSummaryComp(soup)]
    ow = [{"stockCode": ticker, "year": filingYear, **r} for r in parseBeneficialOwnership(soup)]
    board = parseBoardComposition(soup)
    bd = [{"stockCode": ticker, "year": filingYear, **board}] if board else []
    return af, ep, ow, bd


def _latestProxyMeta(meta: pl.DataFrame) -> pl.DataFrame:
    """allFilings 메타에서 회사별 최신 DEF 14A 1건 (stockCode·filingDate·url)."""
    p = meta.filter(pl.col("form") == "DEF 14A")
    return p.sort("filingDate", descending=True).group_by("stockCode").head(1)


def buildEdgarProxyReport(
    *,
    metaPath: str | Path | None = None,
    doneTickers: set[str] | None = None,
    maxCompanies: int | None = None,
    verbose: bool = False,
) -> dict[str, list[dict]]:
    """DEF 14A 순회 → 거버넌스 4표 행 dict (오케스트레이션. fetch=gather 위임·파싱=providers 위임).

    발행/체크포인트는 호출측(.github/scripts 백필 runner 또는 edgarSync)이 담당한다. 본 함수는
    회사별 최신 proxy 를 fetch·파싱해 행을 누적 반환만 한다(순수 오케스트레이션, 상태 없음).

    Parameters
    ----------
    metaPath : str | Path | None
        allFilings recent.parquet 경로. None 이면 로컬 dataDir 표준 위치.
    doneTickers : set[str] | None
        skip 할 stockCode (리줌 시드). None=전체.
    maxCompanies : int | None
        처리 상한(부분 실행·스모크). None=전체.
    verbose : bool
        진행 로그.

    Returns
    -------
    dict[str, list[dict]]
        ``{"auditFees": [...], "execPayIndividual": [...], "ownership": [...], "board": [...],
        "processedTickers": [...]}``. processedTickers 는 이번 호출이 fetch 한 stockCode 전부
        (파서 0행 포함). 리줌 done 마킹용(0행 회사 무한 재fetch 방지).

    Raises
    ------
    FileNotFoundError
        메타 parquet 부재.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report.proxyBuild import buildEdgarProxyReport
    >>> rows = buildEdgarProxyReport(maxCompanies=5, verbose=True)  # doctest: +SKIP

    Capabilities:
        - 회사별 최신 DEF 14A 를 fair-access 페이싱으로 받아 3표(감사보수·SCT·실질지분) 행 생성.
          적중률 실측 85/75/80%(tests/_attempts/proxyGovernance). 미스는 표 없는 문서, 정직 빈 행.

    AIContext:
        US 거버넌스 패널(auditFees·topExecPay·shareholders)의 scan source. 런타임 reportSource
        US 분기가 edgar/scan/report/{auditFees,execPayIndividual,ownership}.parquet 을 직독.

    Guide:
        - 백필/발행은 .github/scripts/sync 러너가 체크포인트와 함께 수행(HF 시드 리줌).
        - 메타가 깊어지면(2015 백필) 과거 proxy 도 자연 포함 가능(현재 최신 1건).

    Requires:
        - edgar/allFilings/recent.parquet (DEF 14A 메타·url)
        - gather.edgar.allFilingsContent.getFilingBody (수집 위임)
        - providers.edgar.report.proxyParse (파싱 위임)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.report.build.buildEdgarReport` (facts 기반 3관점)
        - :func:`dartlab.scan.builders.edgar.report.employeeBuild.buildEdgarEmployee` (panel 텍스트 기반)
    """
    import httpx

    from dartlab import config as _cfg
    from dartlab.gather.edgar.allFilingsContent import getFilingBody

    mp = Path(metaPath) if metaPath else Path(_cfg.dataDir) / "edgar" / "allFilings" / "recent.parquet"
    if not mp.exists():
        raise FileNotFoundError(f"allFilings 메타 없음: {mp}")
    meta = pl.read_parquet(mp, columns=["stockCode", "form", "filingDate", "url"])
    targets = _latestProxyMeta(meta).sort("stockCode")
    done = doneTickers or set()

    out: dict[str, list[dict]] = {
        "auditFees": [],
        "execPayIndividual": [],
        "ownership": [],
        "board": [],
        "processedTickers": [],
    }
    n = 0
    with httpx.Client(headers={"User-Agent": "dartlab research (contact: research@dartlab.io)"}) as client:
        for r in targets.iter_rows(named=True):
            tk = str(r["stockCode"])
            if tk in done:
                continue
            if maxCompanies is not None and n >= maxCompanies:
                break
            n += 1
            out["processedTickers"].append(tk)
            body, status = getFilingBody(str(r["url"] or ""), client=client)
            if status == "ok" and body:
                try:
                    af, ep, ow, bd = proxyRowsFromHtml(body, tk, str(r["filingDate"])[:4])
                    out["auditFees"].extend(af)
                    out["execPayIndividual"].extend(ep)
                    out["ownership"].extend(ow)
                    out["board"].extend(bd)
                except Exception as exc:  # noqa: BLE001 (개별 proxy 파싱 실패 격리)
                    if verbose:
                        _log.warning(f"[proxyBuild] {tk} 파싱 실패: {exc!r}")
            if verbose and n % 200 == 0:
                _log.info(f"[proxyBuild] {n}사 처리, af={len(out['auditFees'])} ep={len(out['execPayIndividual'])}")
            time.sleep(_PACE_SECONDS)
    if verbose:
        _log.info(
            f"[proxyBuild] 완료 {n}사: auditFees {len(out['auditFees'])}행 · "
            f"execPay {len(out['execPayIndividual'])}행 · ownership {len(out['ownership'])}행"
        )
    return out


__all__ = [
    "AUDIT_FEES_COLS",
    "BOARD_COLS",
    "EXEC_PAY_COLS",
    "OWNERSHIP_COLS",
    "buildEdgarProxyReport",
    "proxyRowsFromHtml",
]
