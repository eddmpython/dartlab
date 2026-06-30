"""EDGAR scan report 빌더 — 정기보고서 파생 3관점을 companyfacts 에서 직접 산출.

KR ``builders/kr/report`` 대칭이되 *XBRL facts 가 깨끗한 관점만* 미러한다(덕지덕지 가드). 런타임
reportSource 가 market 분기로 KR(dart/scan/report)과 분리 소비. DART 한국식 필드코드(se·thstrm 등)에 US 를
강제로 끼우지 않고 US-native 컬럼으로 직접 생산한다.

산출 3종(한 번의 finance 순회로 동시 emit):
    - ``shareholderReturn.parquet`` — 주주환원: 배당(dps·총액·payout) + **자사주매입(금액·소각주식수·총환원율)**.
      미국 자본환원의 핵심인 buyback 을 ``PaymentsForRepurchaseOfCommonStock``($)·
      ``StockRepurchasedAndRetiredDuringPeriodShares``(소각 주식수)로 채운다.
    - ``debtMaturity.parquet`` — 부채 만기 사다리: ``LongTermDebtMaturitiesRepaymentsOfPrincipalIn{Year}`` y1~y5 +
      after5 + 총 장기부채. KR ``corporateBond`` 잔존만기 버킷 대칭(신용 분석 source).
    - ``execComp.parquet`` — 임원보수: ecd(Pay-vs-Performance) PEO(CEO) 총보수·실현보수 + 비-PEO NEO 평균 +
      TSR. 2023 회계연도+ proxy(DEF 14A) 인라인 XBRL 보유사만(부분 — fy 없음, 기간 end 로 연도 도출).

⛔ 정직 갭(본 빌드 제외 — companyfacts·companyconcept 양쪽 404 실측): 직원수(10-K 표지 텍스트)·감사인
(dei:AuditorName 텍스트)·소유구조(13D/G·proxy 표)·사외이사·타법인출자(EX-21 텍스트). 모두 XBRL 집계 API 부재
→ 문서 파싱(별도 gather) 필요. 무배당·무자사주·proxy 미제출 기업은 해당 행이 비어 패널 자연 미표시.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# ── us-gaap 연간(fp='FY') 태그 — 배당/자사주/부채만기. totalDividend·buyback 은 회사·연도별 태그 전환 폴백 체인 ──
_DPS_TAGS = ("CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid")
_TOTAL_DIV_TAGS = ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends", "DividendsCommonStock", "Dividends")
_EPS_TAGS = ("EarningsPerShareDiluted",)
_NETINCOME_TAGS = ("NetIncomeLoss",)
_TREASURY_END_TAGS = ("TreasuryStockShares", "TreasuryStockCommonShares")
# 미국은 자사주를 *소각*(retire)하는 회사가 많아 treasury 주식수가 비므로 소각 주식수를 우선 폴백.
_BUYBACK_QTY_TAGS = (
    "StockRepurchasedAndRetiredDuringPeriodShares",
    "TreasuryStockSharesAcquired",
    "StockRepurchasedDuringPeriodShares",
)
_BUYBACK_AMT_TAGS = ("PaymentsForRepurchaseOfCommonStock", "PaymentsForRepurchaseOfEquity")
_DISPOSAL_QTY_TAGS = ("TreasuryStockSharesReissued",)

# 부채 만기 사다리 — 10-K 연간 공시(잔존만기 원금 상환 스케줄).
_DEBT_MAT_TAGS = {
    "y1": ("LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",),
    "y2": ("LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo",),
    "y3": ("LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree",),
    "y4": ("LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour",),
    "y5": ("LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive",),
    "after5": ("LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive",),
}
_LONG_TERM_DEBT_TAGS = ("LongTermDebt", "LongTermDebtNoncurrent")

# ── ecd(Executive Comp Disclosure, Pay-vs-Performance) 태그 — proxy 인라인 XBRL. fy 없음(end 로 연도) ──
_ECD_TAGS = {
    "ceoTotalComp": ("PeoTotalCompAmt",),
    "ceoActuallyPaid": ("PeoActuallyPaidCompAmt",),
    "neoAvgTotalComp": ("NonPeoNeoAvgTotalCompAmt",),
    "neoAvgActuallyPaid": ("NonPeoNeoAvgCompActuallyPaidAmt",),
    "companyTsr": ("TotalShareholderRtnAmt",),
    "peerTsr": ("PeerGroupTotalShareholderRtnAmt",),
}

SHAREHOLDER_RETURN_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "dps": pl.Float64,
    "eps": pl.Float64,
    "totalDividend": pl.Float64,
    "payoutPct": pl.Float64,
    "yieldPct": pl.Float64,
    "buybackAmount": pl.Float64,
    "buybackQty": pl.Float64,
    "totalPayoutPct": pl.Float64,
    "disposalQty": pl.Float64,
    "buybackCancel": pl.Float64,
    "treasuryEnd": pl.Float64,
}

DEBT_MATURITY_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "y1": pl.Float64,
    "y2": pl.Float64,
    "y3": pl.Float64,
    "y4": pl.Float64,
    "y5": pl.Float64,
    "after5": pl.Float64,
    "longTermDebt": pl.Float64,
}

EXEC_COMP_COLS = {
    "stockCode": pl.Utf8,
    "year": pl.Utf8,
    "ceoTotalComp": pl.Float64,
    "ceoActuallyPaid": pl.Float64,
    "neoAvgTotalComp": pl.Float64,
    "neoAvgActuallyPaid": pl.Float64,
    "companyTsr": pl.Float64,
    "peerTsr": pl.Float64,
}

# buildEdgarReport 가 finance parquet 에서 읽는 최소 컬럼(메모리 — end 는 ecd 연도 도출용).
_READ_COLS = ["namespace", "tag", "val", "fp", "fy", "filed", "end"]


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


def _ecdByYear(facts: pl.DataFrame, tags: tuple[str, ...]) -> dict[int, float]:
    """ecd(Pay-vs-Performance) 값을 {year: value} 로 — fy 가 null 이라 기간 end 의 연도로 키.

    ecd 사실은 proxy(DEF 14A) 인라인 XBRL 이라 ``fy``/``fp`` 가 비어 있고 기간 ``start``/``end`` 만 있다.
    회계연도 종료일(``end``)의 달력연도를 연도 키로 쓴다(SEC fy 관례 = FYE 가 속한 연도). 같은 연도
    정정은 최신 filed 채택.

    Args:
        facts: 회사 edgar/finance parquet (namespace·tag·val·end·filed 컬럼).
        tags: ecd 후보 태그(앞 우선).

    Returns:
        dict[int, float] — {year: val}. 매칭 없으면 빈 dict.
    """
    out: dict[int, float] = {}
    for tag in tags:
        sub = facts.filter(
            (pl.col("namespace") == "ecd")
            & (pl.col("tag") == tag)
            & pl.col("val").is_not_null()
            & pl.col("end").is_not_null()
        )
        if sub.is_empty():
            continue
        byYear: dict[int, float] = {}
        bestFiled: dict[int, str] = {}
        for end, val, filed in zip(sub["end"].to_list(), sub["val"].to_list(), sub["filed"].cast(pl.Utf8).to_list()):
            if end is None:
                continue
            yr = int(end.year)
            f = str(filed or "")
            if yr not in byYear or f >= bestFiled[yr]:
                byYear[yr] = float(val)
                bestFiled[yr] = f
        for yr, val in byYear.items():
            out.setdefault(yr, val)
    return out


def shareholderReturnRows(facts: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 facts → 연도별 주주환원 행(ShareholderReturnYear 동형). 배당 + 자사주매입.

    배당(dps·총액·payout)에 더해 미국 자본환원의 핵심인 자사주매입을 금액(buybackAmount)·소각/취득
    주식수(buybackQty)로 채우고, 총환원율(totalPayoutPct=(배당+매입)/순이익)을 계산한다.

    Args:
        facts: 회사 edgar/finance parquet.
        ticker: stockCode.

    Returns:
        list[dict] — 연도별 행. 배당·자사주 신호 전무 연도는 제외.
    """
    dps = _annualByYear(facts, _DPS_TAGS)
    eps = _annualByYear(facts, _EPS_TAGS)
    totalDiv = _annualByYear(facts, _TOTAL_DIV_TAGS)
    netIncome = _annualByYear(facts, _NETINCOME_TAGS)
    treasuryEnd = _annualByYear(facts, _TREASURY_END_TAGS)
    buybackQty = _annualByYear(facts, _BUYBACK_QTY_TAGS)
    buybackAmt = _annualByYear(facts, _BUYBACK_AMT_TAGS)
    disposalQty = _annualByYear(facts, _DISPOSAL_QTY_TAGS)

    years = set(dps) | set(totalDiv) | set(treasuryEnd) | set(buybackQty) | set(buybackAmt)  # 주주환원 신호 연도만
    rows: list[dict] = []
    for y in sorted(years):
        td = totalDiv.get(y)
        bb = buybackAmt.get(y)
        ni = netIncome.get(y)
        payout = round(td / ni * 100, 2) if td is not None and ni and ni > 0 else None
        totalReturn = (td or 0) + (bb or 0)
        totalPayout = round(totalReturn / ni * 100, 2) if totalReturn and ni and ni > 0 else None
        rows.append(
            {
                "stockCode": ticker,
                "year": str(y),
                "dps": dps.get(y),
                "eps": eps.get(y),
                "totalDividend": td,
                "payoutPct": payout,
                "yieldPct": None,  # 시점가 필요 — facts 부재(정직 null)
                "buybackAmount": bb,
                "buybackQty": buybackQty.get(y),
                "totalPayoutPct": totalPayout,
                "disposalQty": disposalQty.get(y),
                "buybackCancel": None,  # 별 태그 — 후속
                "treasuryEnd": treasuryEnd.get(y),
            }
        )
    return rows


def debtMaturityRows(facts: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 facts → 연도별 부채 만기 사다리 행(y1~y5·after5·총 장기부채).

    Args:
        facts: 회사 edgar/finance parquet.
        ticker: stockCode.

    Returns:
        list[dict] — 만기 버킷 한 개라도 있는 연도만.
    """
    buckets = {k: _annualByYear(facts, tags) for k, tags in _DEBT_MAT_TAGS.items()}
    ltDebt = _annualByYear(facts, _LONG_TERM_DEBT_TAGS)
    years: set[int] = set()
    for d in buckets.values():
        years |= set(d)
    rows: list[dict] = []
    for y in sorted(years):
        rows.append(
            {
                "stockCode": ticker,
                "year": str(y),
                **{k: buckets[k].get(y) for k in _DEBT_MAT_TAGS},
                "longTermDebt": ltDebt.get(y),
            }
        )
    return rows


def execCompRows(facts: pl.DataFrame, ticker: str) -> list[dict]:
    """단일 회사 facts → 연도별 임원보수 행(ecd Pay-vs-Performance: CEO·평균 NEO 보수·TSR).

    Args:
        facts: 회사 edgar/finance parquet(ecd 네임스페이스 포함).
        ticker: stockCode.

    Returns:
        list[dict] — CEO 또는 NEO 보수가 있는 연도만. ecd 미제출사는 빈 list.
    """
    series = {k: _ecdByYear(facts, tags) for k, tags in _ECD_TAGS.items()}
    years: set[int] = set(series["ceoTotalComp"]) | set(series["neoAvgTotalComp"])  # 보수 신호 있는 연도만
    rows: list[dict] = []
    for y in sorted(years):
        rows.append(
            {
                "stockCode": ticker,
                "year": str(y),
                **{k: series[k].get(y) for k in _ECD_TAGS},
            }
        )
    return rows


def buildEdgarReport(*, verbose: bool = False) -> list[Path]:
    """전종목 EDGAR facts → edgar/scan/report/{shareholderReturn,debtMaturity,execComp}.parquet (순수 계산).

    edgar/finance/{cik}.parquet 만 한 번 순회하며 3관점(주주환원·부채만기·임원보수)을 동시 추출 — 별도
    수집 0, 재다운로드 0. edgarSync 의 finance 빌드 직후 호출(로컬 finance parquet 재사용). 런타임
    reportSource 의 US 분기가 stockCode 필터로 직독.

    Parameters
    ----------
    verbose : bool
        진행 로그.

    Returns
    -------
    list[Path]
        생성된 3 parquet 경로(shareholderReturn·debtMaturity·execComp).

    Raises
    ------
    FileNotFoundError
        edgar/finance 디렉토리/parquet 부재.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.report import buildEdgarReport
    >>> paths = buildEdgarReport(verbose=True)  # doctest: +SKIP
    >>> [p.name for p in paths]
    ['shareholderReturn.parquet', 'debtMaturity.parquet', 'execComp.parquet']

    Capabilities:
        - 한 finance 순회로 3 US-native 산출물 emit. 주주환원=배당+자사주매입($·소각주식수·총환원율),
          부채만기=잔존만기 원금 사다리, 임원보수=ecd Pay-vs-Performance. 신호 없는 연도/기업은 빈 행.

    AIContext:
        ``scan`` US 정기보고서 파생의 source. 런타임 reportSource 가 market 분기로 KR(dart/scan/report)과
        분리 소비. 직원수·감사인·소유구조는 XBRL 집계 API 부재라 본 빌드 제외(문서 파싱 별도 gather).

    Guide:
        - edgarSync finance 빌드 직후 호출(로컬 finance parquet 재사용, 재다운로드 0).
        - 발행은 deployEdgarToHF(['scan']) 가 data/edgar/scan/ 통째 업로드(별도 push 0).

    Requires:
        - edgar/finance/{cik}.parquet (companyfacts 빌드)
        - loadEdgarListedUniverse() (cik→ticker)

    SeeAlso:
        - :func:`dartlab.scan.builders.edgar.valuationBuild.buildEdgarValuation` — 같은 facts 소스 패턴
        - :func:`dartlab.scan.builders.kr.report.build.buildReport` — KR 대칭(DART 정기보고서 17 apiType)
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
        from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

        cikToTicker = edgarCikToTicker()  # 대표 보통주 티커 우선(finance·valuation 과 동일 키)
    except (OSError, ValueError, KeyError):
        cikToTicker = {}

    srRows: list[dict] = []
    dmRows: list[dict] = []
    ecRows: list[dict] = []
    for fp in parquets:
        ticker = cikToTicker.get(fp.stem.zfill(10))
        if not ticker:
            continue
        try:
            facts = pl.read_parquet(fp, columns=_READ_COLS)
        except (OSError, pl.exceptions.PolarsError):
            continue
        if facts.is_empty():
            continue
        tk = str(ticker).upper()
        srRows.extend(shareholderReturnRows(facts, tk))
        dmRows.extend(debtMaturityRows(facts, tk))
        ecRows.extend(execCompRows(facts, tk))

    outputs: list[Path] = []
    for rows, schema, name in (
        (srRows, SHAREHOLDER_RETURN_COLS, "shareholderReturn"),
        (dmRows, DEBT_MATURITY_COLS, "debtMaturity"),
        (ecRows, EXEC_COMP_COLS, "execComp"),
    ):
        out = pl.DataFrame(rows, schema=schema) if rows else pl.DataFrame(schema=schema)
        out = out.sort(["stockCode", "year"])
        outPath = outDir / f"{name}.parquet"
        out.write_parquet(str(outPath), compression="zstd")
        outputs.append(outPath)
        if verbose:
            _log.info(f"[edgarReport] {name}: {out.height}행 ({out['stockCode'].n_unique()}종목) → {outPath}")
    return outputs
