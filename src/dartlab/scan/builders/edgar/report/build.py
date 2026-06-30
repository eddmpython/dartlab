"""EDGAR scan report 빌더 — 주주환원(배당) 연도 시계열 → edgar/scan/report/shareholderReturn.parquet.

KR ``builders/kr/report`` 대칭이되 *깨끗한 부분만* 미러한다(덕지덕지 가드). 런타임
``reportSource.buildShareholderReturn`` 의 출력 타입 ``ShareholderReturnYear`` 와 동형 컬럼을 US-native 로
직접 생산 — DART 한국식 필드코드(se·thstrm·change_qy_*)에 US 를 강제로 끼우지 않는다.

채우는 것(facts 청결): dps·eps·totalDividend·payoutPct + (있으면) treasury 주식수. US 배당 지표는 XBRL
태그가 일관(``CommonStockDividendsPerShareDeclared`` 등)이라 깨끗.

⛔ 정직 갭: 미국 기업은 자사주를 *소각*(retire)해 treasury 주식(``TreasuryStockShares``)을 안 들고, 자사주
매입은 *금액*(``PaymentsForRepurchaseOfCommonStock``)으로 공시한다. KR ``ShareholderReturnYear`` 는 자사주를
*주식수*(buybackQty)로 모델링하므로 US 매입금액은 매핑 대상이 없다 → buyback 은 본 빌드 제외(buybackAmount
필드 신설 + 패널은 후속). 무배당 기업(성장주)은 배당 행이 비어 패널 자연 미표시.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# XBRL 태그 — 배당/자사주. totalDividend 는 태그 전환(회사·연도별) 대비 폴백 체인.
_DPS_TAGS = ("CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid")
_TOTAL_DIV_TAGS = ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends", "DividendsCommonStock", "Dividends")
_EPS_TAGS = ("EarningsPerShareDiluted",)
_NETINCOME_TAGS = ("NetIncomeLoss",)
_TREASURY_END_TAGS = ("TreasuryStockShares", "TreasuryStockCommonShares")
_BUYBACK_QTY_TAGS = ("TreasuryStockSharesAcquired",)
_DISPOSAL_QTY_TAGS = ("TreasuryStockSharesReissued",)

_OUT_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "dps": pl.Float64,
    "eps": pl.Float64,
    "totalDividend": pl.Float64,
    "payoutPct": pl.Float64,
    "yieldPct": pl.Float64,
    "buybackQty": pl.Float64,
    "disposalQty": pl.Float64,
    "buybackCancel": pl.Float64,
    "treasuryEnd": pl.Float64,
}


def _annualByYear(facts: pl.DataFrame, tags: tuple[str, ...]) -> dict[int, float]:
    """us-gaap 연간(fp='FY') 값을 {fiscalYear: value} 로 — 태그 폴백 머지(이른 태그 우선).

    태그 체인을 *머지*한다: 이른 태그가 연도 우선권, 빈 연도는 다음 태그가 채운다(회사·연도별 태그 전환
    대비 — 예 AAPL totalDividend 가 PaymentsOfDividendsCommonStock→PaymentsOfDividends 로 바뀜). 같은
    태그 안에선 최신 filed(정정) 채택.

    Args:
        facts: 회사 edgar/finance parquet (namespace·tag·val·fp·fy·filed 컬럼).
        tags: 후보 태그(앞 우선).

    Returns:
        dict[int, float] — {fy: val}. 매칭 없으면 빈 dict.
    """
    out: dict[int, float] = {}
    for tag in tags:
        sub = facts.filter(
            (pl.col("namespace") == "us-gaap")
            & (pl.col("tag") == tag)
            & (pl.col("fp") == "FY")
            & pl.col("val").is_not_null()
        )
        if sub.is_empty():
            continue
        byFy: dict[int, float] = {}
        bestFiled: dict[int, str] = {}
        for fy, val, filed in zip(sub["fy"].to_list(), sub["val"].to_list(), sub["filed"].cast(pl.Utf8).to_list()):
            if fy is None:
                continue
            fyInt = int(fy)
            f = str(filed or "")
            if fyInt not in byFy or f >= bestFiled[fyInt]:  # 최신 filed(정정) 채택
                byFy[fyInt] = float(val)
                bestFiled[fyInt] = f
        for fyInt, val in byFy.items():
            out.setdefault(fyInt, val)  # 이른 태그 우선 — 빈 연도만 다음 태그가 채움
    return out


def shareholderReturnRows(facts: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 facts → 연도별 주주환원 행(ShareholderReturnYear 동형). 배당/자사주주식 메타.

    Args:
        facts: 회사 edgar/finance parquet.
        ticker: stockCode.

    Returns:
        list[dict] — 연도별 행. 배당·자사주 전무 연도는 제외.
    """
    dps = _annualByYear(facts, _DPS_TAGS)
    eps = _annualByYear(facts, _EPS_TAGS)
    totalDiv = _annualByYear(facts, _TOTAL_DIV_TAGS)
    netIncome = _annualByYear(facts, _NETINCOME_TAGS)
    treasuryEnd = _annualByYear(facts, _TREASURY_END_TAGS)
    buybackQty = _annualByYear(facts, _BUYBACK_QTY_TAGS)
    disposalQty = _annualByYear(facts, _DISPOSAL_QTY_TAGS)

    years = set(dps) | set(totalDiv) | set(treasuryEnd) | set(buybackQty)  # 주주환원 신호 있는 연도만
    rows: list[dict] = []
    for y in sorted(years):
        td = totalDiv.get(y)
        ni = netIncome.get(y)
        payout = round(td / ni * 100, 2) if td is not None and ni and ni > 0 else None
        rows.append(
            {
                "stockCode": ticker,
                "year": str(y),
                "dps": dps.get(y),
                "eps": eps.get(y),
                "totalDividend": td,
                "payoutPct": payout,
                "yieldPct": None,  # 시점가 필요 — facts 부재(정직 null)
                "buybackQty": buybackQty.get(y),
                "disposalQty": disposalQty.get(y),
                "buybackCancel": None,  # US 소각은 별 태그 — 후속
                "treasuryEnd": treasuryEnd.get(y),
            }
        )
    return rows


def buildEdgarReport(*, verbose: bool = False) -> Path:
    """전종목 EDGAR facts → edgar/scan/report/shareholderReturn.parquet (배당 주주환원, 순수 계산).

    edgar/finance/{cik}.parquet 만 읽어 연도별 배당/자사주주식 메타를 뽑는다 — 별도 수집 0. edgarSync 의
    finance 빌드 직후 호출(로컬 finance parquet 재사용). 런타임 ``reportSource.buildShareholderReturn`` US 분기가
    stockCode 필터로 직독.

    Parameters
    ----------
    verbose : bool
        진행 로그.

    Returns
    -------
    Path
        edgar/scan/report/shareholderReturn.parquet 경로.

    Raises
    ------
    FileNotFoundError
        edgar/finance 디렉토리/parquet 부재.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report import buildEdgarReport
    >>> p = buildEdgarReport(verbose=True)  # doctest: +SKIP
    >>> p.name
    'shareholderReturn.parquet'

    Capabilities:
        - XBRL 배당 태그(dps·총액)·자사주 주식수에서 연도 시계열 → KR ShareholderReturnYear 동형 행. 무배당
          기업은 빈 행(패널 자연 미표시). buyback 금액은 KR 주식모델 미스매치라 제외(정직 갭).

    AIContext:
        ``scan`` US 주주환원의 source. 런타임 reportSource 가 market 분기로 KR(dart/scan/report)과 분리 소비.

    Guide:
        - edgarSync finance 빌드 직후 호출(로컬 finance parquet 재사용, 재다운로드 0).

    Requires:
        - edgar/finance/{cik}.parquet (companyfacts 빌드)
        - loadEdgarListedUniverse() (cik→ticker)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.valuationBuild.buildEdgarValuation` — 같은 facts 소스 패턴
        - :func:`dartlab.scan.builders.kr.report.build` — KR 대칭(DART 정기보고서 추출)
    """
    from dartlab import config as _cfg

    edgarDir = Path(_cfg.dataDir) / "edgar" / "finance"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan" / "report"
    outDir.mkdir(parents=True, exist_ok=True)
    if not edgarDir.exists():
        raise FileNotFoundError(f"EDGAR finance 디렉토리 없음: {edgarDir}")
    parquets = sorted(edgarDir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError("EDGAR finance parquet 없음")

    try:
        from dartlab.core.dataLoader import loadEdgarListedUniverse

        univ = loadEdgarListedUniverse()
        cikToTicker = {str(c).zfill(10): t for c, t in zip(univ["cik"].to_list(), univ["ticker"].to_list()) if t}
    except (OSError, ValueError, KeyError):
        cikToTicker = {}

    cols = ["namespace", "tag", "val", "fp", "fy", "filed"]
    rows: list[dict] = []
    for fp in parquets:
        ticker = cikToTicker.get(fp.stem.zfill(10))
        if not ticker:
            continue
        try:
            facts = pl.read_parquet(fp, columns=cols)
        except (OSError, pl.exceptions.PolarsError):
            continue
        if facts.is_empty():
            continue
        rows.extend(shareholderReturnRows(facts, str(ticker).upper()))

    out = pl.DataFrame(rows, schema=_OUT_COLS) if rows else pl.DataFrame(schema=_OUT_COLS)
    out = out.sort(["stockCode", "year"])
    outPath = outDir / "shareholderReturn.parquet"
    out.write_parquet(str(outPath), compression="zstd")
    if verbose:
        _log.info(f"[edgarReport] shareholderReturn: {out.height}행 ({out['stockCode'].n_unique()}종목) → {outPath}")
    return outPath
