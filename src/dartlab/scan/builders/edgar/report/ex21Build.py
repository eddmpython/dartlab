"""EDGAR 자회사(EX-21) scan 빌더. 10-K exhibit 에서 edgar/scan/report/subsidiaries.parquet 생성.

DART 타법인출자(investedCompany: 피출자사·장부가·지분율)의 US 대칭. US 는 EX-21 exhibit 에
자회사명·설립관할만 공시한다(장부가·지분율 무공시 = 정직 null). 수집은 submissions bulk(10-K
accession) + SEC Archives index.json 경유 exhibit fetch, 파싱은 providers ``ex21Parse``, 본 모듈은
오케스트레이션. 백필/발행은 runner(.github/scripts/sync/backfillEdgarSubsidiaries.py)가 체크포인트 수행.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

SUBSIDIARIES_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "name": pl.Utf8,
    "jurisdiction": pl.Utf8,
}

_PACE_SECONDS = 0.12  # SEC fair-access
_EX21_RE = re.compile(r"(?i)ex(hibit)?[._-]?21")


def latestTenKAccessions(zipPath: Path | None = None) -> dict[str, tuple[str, str]]:
    """submissions bulk 에서 CIK 별 최신 10-K (accessionNo, filingDate). 수집은 gather 위임.

    Args:
        zipPath: submissions.zip 경로. None 이면 자동 다운로드(TTL 가드).

    Returns:
        dict[str, tuple[str, str]]: {cik10: (accessionNumber, filingDate)}. 10-K 없으면 항목 없음.

    Raises:
        zipfile.BadZipFile: zip 손상.

    Example:
        >>> accs = latestTenKAccessions()  # doctest: +SKIP
        >>> accs["0000320193"][0]  # AAPL 최신 10-K accession
        '0000320193-25-000079'
    """
    from dartlab.gather.edgar.bulkSubmissions import downloadSubmissionsBulk, iterSubmissionsBulk

    zp = zipPath if zipPath is not None else downloadSubmissionsBulk()
    out: dict[str, tuple[str, str]] = {}
    for cik, payload in iterSubmissionsBulk(zp, recentOnly=True):
        rec = payload.get("filings", {}).get("recent", {})
        forms = rec.get("form") or []
        for i, f in enumerate(forms):
            if f == "10-K":
                accs = rec.get("accessionNumber", [])
                dates = rec.get("filingDate", [])
                if i < len(accs):
                    out[cik] = (str(accs[i]), str(dates[i] if i < len(dates) else ""))
                break  # recent 은 최신순 → 첫 10-K 가 최신
    return out


def fetchSubsidiaryRows(cik: str, ticker: str, accession: str, filingDate: str, *, client) -> list[dict]:
    """단일 회사 최신 10-K 의 EX-21 exhibit 을 받아 자회사 행 생성 (index.json 경유 2 fetch).

    Args:
        cik: 0-padded 10자리 CIK.
        ticker: stockCode.
        accession: 10-K accessionNumber (dash 포함).
        filingDate: 10-K 제출일(YYYY-MM-DD). 기준연도.
        client: 재사용 httpx.Client (SEC User-Agent 세팅).

    Returns:
        list[dict]: SUBSIDIARIES_COLS 행. EX-21 부재/파싱 실패는 [].

    Raises:
        없음. 개별 실패는 빈 list 로 격리.
    """
    from dartlab.providers.edgar.report.ex21Parse import parseSubsidiaries

    try:
        accNo = accession.replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0') or '0'}/{accNo}"
        index = client.get(f"{base}/index.json", timeout=30).json()
        names = [f["name"] for f in index.get("directory", {}).get("item", [])]
        ex21 = next((n for n in names if _EX21_RE.search(n) and n.endswith((".htm", ".html", ".txt"))), None)
        if not ex21:
            return []
        html = client.get(f"{base}/{ex21}", timeout=30).text
        year = str(filingDate)[:4]
        return [{"stockCode": ticker, "year": year, **r} for r in parseSubsidiaries(html)]
    except Exception:  # noqa: BLE001 (개별 회사 실패 격리)
        return []


def buildEdgarSubsidiaries(
    *,
    doneTickers: set[str] | None = None,
    maxCompanies: int | None = None,
    verbose: bool = False,
) -> dict[str, list]:
    """전종목 최신 10-K EX-21 순회 → 자회사 행 dict (오케스트레이션).

    Parameters
    ----------
    doneTickers : set[str] | None
        skip 할 stockCode (리줌 시드).
    maxCompanies : int | None
        처리 상한(청크). None=전체.
    verbose : bool
        진행 로그.

    Returns
    -------
    dict[str, list]
        ``{"subsidiaries": [...], "processedTickers": [...]}``. processedTickers 는 0행 포함
        (리줌 done 마킹용).

    Raises
    ------
    없음. submissions/네트워크 개별 실패는 격리.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report.ex21Build import buildEdgarSubsidiaries
    >>> rows = buildEdgarSubsidiaries(maxCompanies=5, verbose=True)  # doctest: +SKIP

    Capabilities:
        - 회사별 최신 10-K EX-21 에서 자회사명·설립관할 추출(실측 AAPL 19개). 장부가·지분율은
          US 무공시라 정직 null(스키마에 없음). EX-21 미첨부사는 빈 행(패널 자연 미표시).

    AIContext:
        ``scan`` US 타법인출자(investments 패널)의 source. 런타임 reportSource US 분기가
        edgar/scan/report/subsidiaries.parquet 직독.

    Guide:
        - 백필/발행은 backfillEdgarSubsidiaries runner(체크포인트·리줌). 연 1회 10-K 갱신이라
          주간 CI(edgarProxySync 동형)면 충분.

    Requires:
        - submissions.zip (gather bulkSubmissions, 10-K accession)
        - providers.edgar.report.ex21Parse (파싱 SSOT)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.report.proxyBuild.buildEdgarProxyReport` (동형 오케스트레이션)
    """
    import httpx

    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    cikToTicker = edgarCikToTicker()
    accs = latestTenKAccessions()
    done = doneTickers or set()

    out: dict[str, list] = {"subsidiaries": [], "processedTickers": []}
    n = 0
    with httpx.Client(headers={"User-Agent": "dartlab research (contact: research@dartlab.io)"}) as client:
        for cik, (acc, fd) in sorted(accs.items()):
            ticker = cikToTicker.get(cik)
            if not ticker or ticker in done:
                continue
            if maxCompanies is not None and n >= maxCompanies:
                break
            n += 1
            out["processedTickers"].append(ticker)
            out["subsidiaries"].extend(fetchSubsidiaryRows(cik, ticker, acc, fd, client=client))
            if verbose and n % 200 == 0:
                _log.info(f"[ex21Build] {n}사 처리, rows={len(out['subsidiaries'])}")
            time.sleep(_PACE_SECONDS)
    if verbose:
        _log.info(f"[ex21Build] 완료 {n}사: subsidiaries {len(out['subsidiaries'])}행")
    return out


__all__ = ["SUBSIDIARIES_COLS", "buildEdgarSubsidiaries", "fetchSubsidiaryRows", "latestTenKAccessions"]
