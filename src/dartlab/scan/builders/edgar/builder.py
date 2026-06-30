"""EDGAR scan 프리빌드 — 전종목 재무 지표를 단일 parquet로 합산.

DART scan/builder.py 패턴을 EDGAR에 이식.
200개 단위 배치 + 중간 파일 병합 + 메모리 안전.

사용법::

    from dartlab.scan.builders.edgar.builder import buildEdgarScan
    path = buildEdgarScan(sinceYear=2021, verbose=True)
"""

from __future__ import annotations

import gc
from pathlib import Path

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import polars as pl

_BATCH_SIZE = 200


def buildEdgarFinance(*, sinceYear: int = 2021, verbose: bool = False) -> Path:
    """전종목 EDGAR finance → scan/finance.parquet.

    각 CIK parquet에서 전 사업연도(sinceYear~)별 BS/IS/CF 주요 계정을 추출하여
    회사-연도 1행씩 다년 패널 wide DataFrame으로 합산한다 (KR buildFinance 대칭).
    옛 latestFy-only 는 단년 횡단면이라 finance.json 5Y 시계열을 못 줬다.

    Parameters
    ----------
    sinceYear : int
        시작 연도.
    verbose : bool
        진행 로그 출력 여부.

    Returns
    -------
    Path
        생성된 scan/finance.parquet 경로.

    Raises
    ------
    FileNotFoundError
        EDGAR finance 디렉토리 또는 parquet 없을 때.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.builder import buildEdgarFinance
    >>> path = buildEdgarFinance(sinceYear=2021, verbose=True)
    >>> path.exists()
    True

    Capabilities:
        - EDGAR raw CIK parquet 컬렉션 → 종목별 전 사업연도 BS/IS/CF 주요 계정을 회사-연도 1행씩
          다년 패널 wide DataFrame 으로 합산. DART scan ``buildFinance`` 와 같은 정공법 (다년 패널 +
          200 단위 배치 + 중간 파일 병합).
        - SnakeId → XBRL primary tag 변환은 ``EdgarMapper.getTagsForSnakeIds()`` 가 자동.

    AIContext:
        EDGAR scan 11 axis 의 source. AI agent 가 미국 종목 분석 시 본 빌드 산출 parquet 을
        ``scan_account``/``scan_*`` 함수들이 lazy scan. DART 와 같은 schema 라 cross-market union.

    Guide:
        - REIT (Funds From Operations / Rental Income) · 은행 특례 (interest_income/expense)
          계정도 포함 → 업종 특례 axis 처리 가능.
        - ebitda 같은 파생 계산 대상 계정은 raw 빌드에 없음. scan axis 가 계산.

    When:
        EDGAR Data Sync 직후 (별도 cron). DART prebuild 와 같은 일일 사이클.

    How:
        edgar finance 디렉토리 종목별 parquet glob → 200 단위 배치 → 종목당 전 fy 루프(회사-연도
        1행) + standalone 연간 값 select + wide → 임시 청크 file write → 종료 시 single 파일 merge.
        gc 명시 호출로 RSS 가드.

    Requires:
        - ``data/edgar/finance/{ticker}.parquet`` (EDGAR Data Sync 결과)
        - ``data/edgar/scan/`` 출력 디렉토리 쓰기 권한
        - ``dartlab.reference.mappers.EdgarMapper`` (snakeId → XBRL tag 해석)

    SeeAlso:
        - :func:`buildEdgarScan` — 본 함수의 alias-free public facade
        - :func:`dartlab.scan.builders.kr.core.buildFinance` — DART 대칭
        - :func:`dartlab.scan.builders.edgar.scan.edgarScan` — 본 빌드 산출 소비자
    """
    from dartlab import config as _cfg

    edgarDir = Path(_cfg.dataDir) / "edgar" / "finance"
    outDir = Path(_cfg.dataDir) / "edgar" / "scan"
    outDir.mkdir(parents=True, exist_ok=True)

    if not edgarDir.exists():
        raise FileNotFoundError(f"EDGAR finance 디렉토리 없음: {edgarDir}")

    parquets = sorted(edgarDir.glob("*.parquet"))
    if not parquets:
        raise FileNotFoundError("EDGAR finance parquet 없음")

    if verbose:
        _log.info(f"[edgarBuilder] {len(parquets)} CIK parquets → scan/finance.parquet")

    # 주요 계정
    # DART 호환 snakeId 기준 — scan 소비자(_edgar_scan.py) 가 total_assets/total_liabilities 사용.
    # EDGAR primary tag 해결은 EdgarMapper.getTagsForSnakeIds() 가 SNAKEID_ALIASES 역방향으로 자동 처리.
    # ebitda 는 XBRL 원본 태그 없음 — 파생 계산 대상이라 제외.
    targetAccounts = [
        # IS
        "sales",
        "cost_of_goods_sold",
        "gross_profit",
        "operating_profit",
        "net_profit",
        "research_and_development",
        "selling_general_and_administrative",
        "interest_expense",
        "depreciation_amortization",
        # IS — 업종 특례 (REIT/은행)
        "funds_from_operations",
        "rental_income",
        "net_interest_income",
        "noninterest_income",
        "provision_for_loan_losses",
        # BS
        "total_assets",
        "current_assets",
        "total_liabilities",
        "current_liabilities",
        "total_stockholders_equity",
        "cash_and_cash_equivalents",
        "inventories",
        "trade_and_other_receivables",
        "trade_and_other_payables",
        "property_plant_and_equipment",
        "goodwill",
        "intangible_assets",
        "treasury_stock",
        "retained_earnings",
        "shortterm_borrowings",
        "longterm_borrowings",
        # CF
        "operating_cashflow",
        "investing_cashflow",
        "financing_cash_flow",
        "capex",
        "dividends_paid",
        "share_repurchase",
    ]

    # snakeId → XBRL 태그 역조회 테이블 (사전 빌드, map_elements 회피)
    snakeIdToTags = _buildReverseTagMap(targetAccounts)

    # CIK → SIC 매핑 (meta/sub/*.parquet 전분기 병합, 최신 filed 우선)
    sicMap = _buildCikToSicMap()

    # CIK → ticker 매핑 (universe 기준) — stockCode 컬럼을 user-facing ticker 로 저장하기 위함.
    # 다운스트림 소비자(quant/AI)는 ticker 만 사용한다. CIK 는 내부 SEC 식별자.
    # edgarCikToTicker = 대표(보통주) 티커 우선 SSOT — finance·valuation·report 공유(키 드리프트 0).
    try:
        from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

        cikToTicker = edgarCikToTicker()
    except (OSError, ValueError, KeyError):
        cikToTicker = {}

    batchFiles: list[Path] = []
    records: list[dict] = []

    for idx, fp in enumerate(parquets):
        cik = fp.stem
        try:
            df = pl.read_parquet(fp)
            if df.is_empty():
                continue

            # 10-K만, sinceYear 이후 + 상한 (달력 연도+1, 비12월결산 커버)
            # 일부 companyfacts.zip 엔트리에 fy=29953000 / 43465 (Excel 날짜코드) 같은
            # 잘못된 값이 섞여 있음 → 미래 연도 필터로 제거.
            from datetime import datetime as _dt

            maxFy = _dt.utcnow().year + 1
            annual = df.filter((pl.col("form") == "10-K") & (pl.col("fy") >= sinceYear) & (pl.col("fy") <= maxFy))
            if annual.is_empty():
                continue

            # 다년 패널 — 회사별 전 fy 1행씩 (KR buildFinance 대칭). 옛 latestFy-only 는 단년
            # 횡단면이라 finance.json 5Y 를 못 줬다. 스크리너(횡단면 소비자)는 read 시 latest 슬라이스,
            # corporate macro 는 전 연도(cycle) — KR dart/scan/finance 다년 패턴과 동형.
            # stockCode 는 ticker 우선 (AI/quant user-facing), universe 에 없으면 CIK fallback.
            ticker = cikToTicker.get(cik, cik)
            sicCode = sicMap.get(cik)
            sector = _sicToSector(sicCode)
            annual = annual.with_columns((pl.col("end") - pl.col("start")).dt.total_days().alias("_dur"))
            for fyVal in sorted(annual["fy"].unique().to_list()):
                fyRows = annual.filter(pl.col("fy") == fyVal)
                entityName = fyRows["entityName"][0] if fyRows.height > 0 else ""
                # 10-K 는 비교재무제표로 과거 2~3년 데이터를 같은 fy 라벨로 포함한다. 해당 fy 의
                # **standalone 연간 값만** 선택 — end 가 fy 연도의 +/- 1 년 범위 + 연간(duration ≥ 300일)
                # 또는 frame=CY{fyVal}. end DESC 로 그 fy 결산일 값 우선.
                fyAnnual = fyRows.filter(
                    (pl.col("_dur").is_null() | (pl.col("_dur") > 300))
                    & (
                        pl.col("end").dt.year().is_between(fyVal - 1, fyVal)
                        | pl.col("frame").str.starts_with(f"CY{fyVal}")
                    )
                )
                if fyAnnual.is_empty():
                    continue
                record: dict = {
                    "stockCode": ticker,
                    "cik": cik,
                    "corpName": entityName,
                    "fy": int(fyVal),
                    "sic": sicCode,
                    "sector": sector,
                }
                usdRows = fyAnnual.filter(pl.col("unit").str.contains("(?i)USD"))
                for snakeId in targetAccounts:
                    candidateTags = snakeIdToTags.get(snakeId, [])
                    if not candidateTags:
                        continue
                    tagRows = usdRows.filter(pl.col("tag").is_in(candidateTags))
                    if tagRows.height > 0:
                        val = tagRows.sort(["end", "filed"], descending=[True, True])["val"][0]
                        record[snakeId] = val
                records.append(record)

        except (pl.exceptions.ComputeError, OSError):
            continue

        # 배치 저장
        if len(records) >= _BATCH_SIZE:
            batchPath = outDir / f"_batch_{len(batchFiles):04d}.parquet"
            pl.DataFrame(records).write_parquet(batchPath)
            batchFiles.append(batchPath)
            records.clear()
            gc.collect()
            if verbose:
                _log.info(f"  batch {len(batchFiles)}: {idx + 1}/{len(parquets)}")

    # 나머지
    if records:
        batchPath = outDir / f"_batch_{len(batchFiles):04d}.parquet"
        pl.DataFrame(records).write_parquet(batchPath)
        batchFiles.append(batchPath)

    # 병합
    if not batchFiles:
        raise ValueError("프리빌드할 데이터 없음")

    frames = [pl.read_parquet(p) for p in batchFiles]
    merged = pl.concat(frames, how="diagonal_relaxed")

    outPath = outDir / "finance.parquet"
    merged.write_parquet(outPath, compression="zstd")

    # 임시 파일 정리
    for bp in batchFiles:
        bp.unlink(missing_ok=True)

    if verbose:
        _log.info(f"[edgarBuilder] 완료: {outPath} ({merged.height}행, {merged.width}열)")

    return outPath


def buildEdgarScan(*, sinceYear: int = 2021, verbose: bool = False) -> Path:
    """전체 EDGAR scan 프리빌드.

    Parameters
    ----------
    sinceYear : int, default 2021
        시작 연도.
    verbose : bool, default False
        진행 로그 출력 여부.

    Returns
    -------
    Path
        생성된 scan/finance.parquet 경로.

    Raises
    ------
    FileNotFoundError
        buildEdgarFinance 가 EDGAR finance 디렉토리/parquet 누락 시 전파.

    Examples
    --------
    >>> from dartlab.scan.builders.edgar.builder import buildEdgarScan
    >>> path = buildEdgarScan(sinceYear=2020, verbose=True)

    Requires:
        - :func:`buildEdgarFinance` (위임 대상) 와 동일 — EDGAR Data Sync 결과 + 출력 디렉토리.
    """
    return buildEdgarFinance(sinceYear=sinceYear, verbose=verbose)


def _buildCikToSicMap() -> dict[str, str]:
    """meta/sub/*.parquet 전 분기 병합 → CIK → SIC 매핑 (최신 filed 우선).

    SIC(Standard Industrial Classification) 는 SEC submission 메타 (sub.txt) 의
    sic 필드에 기업별로 기록됨.

    Returns
    -------
    dict[str, str]
        {CIK: SIC코드} — 최신 filing 기준. 데이터 없으면 빈 dict.
    """
    from dartlab import config as _cfg

    metaSubDir = Path(_cfg.dataDir) / "edgar" / "meta" / "sub"
    if not metaSubDir.exists():
        return {}
    parquets = sorted(metaSubDir.glob("*.parquet"))
    if not parquets:
        return {}

    frames: list[pl.DataFrame] = []
    for p in parquets:
        try:
            df = pl.read_parquet(p, columns=["cik", "sic", "filed"])
            frames.append(df)
        except (pl.exceptions.ComputeError, OSError):
            continue
    if not frames:
        return {}

    merged = pl.concat(frames, how="vertical_relaxed").filter(pl.col("sic").is_not_null())
    if merged.is_empty():
        return {}

    # CIK 별 최신 filed 행 (filed 가 동일할 때 첫 번째)
    latest = merged.sort("filed", descending=True).group_by("cik").head(1)
    return dict(zip(latest["cik"].to_list(), latest["sic"].to_list()))


# SIC 대분류 → 섹터 매핑 (SEC 4-digit SIC 앞 2자리 기준, Fama-French 풍)
# https://www.sec.gov/info/edgar/siccodes.htm
_SIC_SECTOR_RANGES: list[tuple[int, int, str]] = [
    (100, 999, "agriculture"),
    (1000, 1499, "mining"),
    (1500, 1799, "construction"),
    (2000, 3999, "manufacturing"),
    (4000, 4899, "transportation_utilities"),
    (4900, 4999, "utilities"),
    (5000, 5199, "wholesale"),
    (5200, 5999, "retail"),
    (6000, 6099, "banks"),
    (6100, 6199, "credit"),
    (6200, 6299, "securities"),
    (6300, 6499, "insurance"),
    (6500, 6599, "real_estate"),
    (6700, 6770, "holding_other"),
    (6798, 6798, "reit"),  # Real Estate Investment Trusts
    (6770, 6799, "fund"),
    (7000, 8999, "services"),
    (9100, 9729, "public_admin"),
]


def _sicToSector(sic: str | None) -> str | None:
    """SIC 코드 → 섹터 분류.

    Parameters
    ----------
    sic : str | None
        4자리 SIC 코드 (예: "3674").

    Returns
    -------
    str | None
        섹터명 (예: "manufacturing"). 매칭 실패 시 None.
    """
    if not sic:
        return None
    try:
        code = int(sic)
    except (ValueError, TypeError):
        return None
    for lo, hi, sector in _SIC_SECTOR_RANGES:
        if lo <= code <= hi:
            return sector
    return None


def _buildReverseTagMap(snakeIds: list[str]) -> dict[str, list[str]]:
    """snakeId → XBRL 태그 목록 역조회 테이블.

    Parameters
    ----------
    snakeIds : list[str]
        조회할 snakeId 목록 (예: ["sales", "total_assets"]).

    Returns
    -------
    dict[str, list[str]]
        {snakeId: [태그1, 태그2, ...]} — 정렬된 XBRL 태그 목록.
    """
    from dartlab.providers.edgar.finance.mapper import EdgarMapper

    result: dict[str, list[str]] = {}
    for sid in snakeIds:
        tags = EdgarMapper.getTagsForSnakeIds([sid])
        result[sid] = sorted(tags)
    return result


def _guessStmt(snakeId: str) -> str:
    """snakeId로 재무제표 유형 추정.

    Returns
    -------
    str
        재무제표 구분 ("IS" | "CF" | "BS").
    """
    if snakeId in ("sales", "operating_profit", "net_profit", "interest_expense", "depreciation_amortization"):
        return "IS"
    if snakeId in ("operating_cashflow", "investing_cashflow", "financing_cash_flow", "capex", "dividends_paid"):
        return "CF"
    return "BS"
