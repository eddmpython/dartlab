"""EDGAR scan 프리빌드 — 전종목 재무 지표를 단일 parquet로 합산.

DART scan/builder.py 패턴을 EDGAR에 이식한다. 상장 universe의 canonical ticker만
발행하며 완성된 frame을 검증한 뒤 원자 교체한다.

사용법::

    from dartlab.scan.builders.edgar.builder import buildEdgarScan
    path = buildEdgarScan(sinceYear=2021, verbose=True)
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.scan.builders.edgar.helpers import (
    EDGAR_PREBUILD_READ_WORKERS,
    _writeParquetAtomic,
    edgarCikToTicker,
    edgarListedFinanceSources,
)

_log = getLogger(__name__)

_TARGET_ACCOUNTS = (
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
    # IS 업종 특례 (REIT/은행)
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
)
FINANCE_SCHEMA = {
    "stockCode": pl.Utf8,
    "cik": pl.Utf8,
    "corpName": pl.Utf8,
    "fy": pl.Int64,
    "sic": pl.Utf8,
    "sector": pl.Utf8,
    **dict.fromkeys(_TARGET_ACCOUNTS, pl.Float64),
}
_FINANCE_READ_COLS = ["form", "fy", "end", "start", "frame", "entityName", "unit", "tag", "val", "filed"]
_ANNUAL_FORMS = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A")
_PREBUILD_MANIFEST_NAME = "prebuild-manifest.json"


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
          다년 패널 wide DataFrame 으로 합산. DART scan ``buildFinance`` 와 같은 다년 패널이다.
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
        edgar finance 디렉토리 종목별 parquet glob → canonical listed CIK만 필요한 열을 읽음 →
        종목당 전 fy standalone 연간 값 select → exact-schema frame → 검증된 원자 교체.

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

    # snakeId → XBRL 태그 역조회 테이블 (사전 빌드, map_elements 회피)
    snakeIdToTags = _buildReverseTagMap(list(_TARGET_ACCOUNTS))

    # CIK → SIC 매핑 (meta/sub/*.parquet 전분기 병합, 최신 filed 우선)
    sicMap = _buildCikToSicMap()

    # CIK → ticker 매핑 (universe 기준) — stockCode 컬럼을 user-facing ticker 로 저장하기 위함.
    # 다운스트림 소비자(quant/AI)는 ticker 만 사용한다. CIK 는 내부 SEC 식별자.
    # edgarCikToTicker = 대표(보통주) 티커 우선 SSOT — finance·valuation·report 공유(키 드리프트 0).
    cikToTicker = edgarCikToTicker()

    selected = edgarListedFinanceSources(edgarDir, cikToTicker)
    if not selected:
        raise ValueError("상장 universe와 연결된 EDGAR finance 원천이 없습니다")
    maxFy = datetime.now().year + 1

    def readSelected(item: tuple[Path, str, str]) -> list[dict]:
        """한 listed finance source를 exact-schema record로 변환한다."""

        fp, cik, ticker = item
        return _financeRecordsForCompany(
            fp,
            cik=cik,
            ticker=ticker,
            sicCode=sicMap.get(cik),
            snakeIdToTags=snakeIdToTags,
            sinceYear=sinceYear,
            maxFy=maxFy,
        )

    records: list[dict] = []
    # companyfacts shard는 수십 KB 단위라 12개 동시 읽기도 작은 bounded frame만 유지한다.
    # executor.map의 입력 순서 회수로 artifact 결정성은 보존한다.
    with ThreadPoolExecutor(
        max_workers=EDGAR_PREBUILD_READ_WORKERS,
        thread_name_prefix="edgar-finance",
    ) as executor:
        for idx, companyRecords in enumerate(executor.map(readSelected, selected), start=1):
            records.extend(companyRecords)
            if verbose and idx % 500 == 0:
                _log.info(f"  {idx}/{len(selected)} listed CIK, {len(records)} rows")

    if not records:
        raise ValueError("프리빌드할 데이터 없음")

    merged = pl.DataFrame(records, schema=FINANCE_SCHEMA, strict=False).sort(["stockCode", "fy"])
    duplicateCount = merged.height - merged.unique(subset=["stockCode", "fy"]).height
    if duplicateCount:
        raise ValueError(f"EDGAR finance identity 중복: stockCode/fy={duplicateCount}")
    outPath = outDir / "finance.parquet"
    _writeParquetAtomic(merged, outPath)

    if verbose:
        _log.info(f"[edgarBuilder] 완료: {outPath} ({merged.height}행, {merged.width}열)")

    return outPath


def _financeRecordsForCompany(
    path: Path,
    *,
    cik: str,
    ticker: str,
    sicCode: str | None,
    snakeIdToTags: dict[str, list[str]],
    sinceYear: int,
    maxFy: int,
) -> list[dict]:
    """한 listed CIK 원천에서 결정적인 회사-연도 finance 행을 만든다."""

    try:
        frame = pl.read_parquet(path, columns=_FINANCE_READ_COLS)
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise RuntimeError(f"EDGAR listed finance 원천 읽기 실패: cik={cik}, path={path}") from exc
    if frame.is_empty():
        return []

    annual = frame.filter(pl.col("form").is_in(_ANNUAL_FORMS) & (pl.col("fy") >= sinceYear) & (pl.col("fy") <= maxFy))
    if annual.is_empty():
        return []
    annual = annual.with_columns((pl.col("end") - pl.col("start")).dt.total_days().alias("_dur"))
    sector = _sicToSector(sicCode)
    records: list[dict] = []
    for fiscalYear in sorted(annual["fy"].unique().to_list()):
        fiscalRows = annual.filter(pl.col("fy") == fiscalYear)
        standalone = fiscalRows.filter(
            (pl.col("_dur").is_null() | (pl.col("_dur") > 300))
            & (
                pl.col("end").dt.year().is_between(fiscalYear - 1, fiscalYear)
                | pl.col("frame").str.starts_with(f"CY{fiscalYear}")
            )
        )
        if standalone.is_empty():
            continue
        record: dict = {
            "stockCode": ticker,
            "cik": cik,
            "corpName": fiscalRows["entityName"][0],
            "fy": int(fiscalYear),
            "sic": sicCode,
            "sector": sector,
        }
        usdRows = standalone.filter(pl.col("unit").str.contains("(?i)USD"))
        for snakeId in _TARGET_ACCOUNTS:
            candidateTags = snakeIdToTags.get(snakeId, [])
            if not candidateTags:
                continue
            tagRows = usdRows.filter(pl.col("tag").is_in(candidateTags))
            if not tagRows.is_empty():
                record[snakeId] = tagRows.sort(["end", "filed"], descending=[True, True])["val"][0]
        records.append(record)
    return records


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


def validateEdgarPrebuild(*, scanDir: Path | None = None) -> dict[str, int]:
    """EDGAR scan cohort의 schema, identity, coverage와 중복을 fail-closed 검증한다."""

    from dartlab import config as _cfg

    root = scanDir or Path(_cfg.dataDir) / "edgar" / "scan"
    cikToTicker = edgarCikToTicker()
    listedTickers = set(cikToTicker.values())
    counts: dict[str, int] = {}
    for relativePath, schema, keys in _edgarPrebuildContracts():
        path = root / relativePath
        if not path.is_file():
            raise FileNotFoundError(f"EDGAR prebuild artifact 누락: {path}")
        frame = pl.read_parquet(path)
        if frame.schema != pl.Schema(schema):
            raise ValueError(f"EDGAR prebuild schema 불일치: path={path}, actual={frame.schema}")
        if frame.is_empty():
            raise ValueError(f"EDGAR prebuild artifact가 비어 있습니다: {path}")
        stockCodes = frame["stockCode"]
        invalidTickers = sorted(set(stockCodes.drop_nulls().to_list()) - listedTickers)
        if stockCodes.null_count() or invalidTickers:
            raise ValueError(
                f"EDGAR prebuild listed identity 위반: path={path}, "
                f"nulls={stockCodes.null_count()}, invalid={invalidTickers[:10]}"
            )
        duplicateCount = frame.height - frame.unique(subset=keys).height
        if duplicateCount:
            raise ValueError(f"EDGAR prebuild identity 중복: path={path}, keys={keys}, count={duplicateCount}")
        counts[relativePath.as_posix()] = frame.height

    finance = pl.read_parquet(root / "finance.parquet", columns=["stockCode", "cik"])
    expectedIdentity = pl.DataFrame(
        {
            "cik": list(cikToTicker),
            "_expectedStockCode": list(cikToTicker.values()),
        }
    )
    invalidPairs = finance.join(expectedIdentity, on="cik", how="left").filter(
        pl.col("_expectedStockCode").is_null() | (pl.col("stockCode") != pl.col("_expectedStockCode"))
    )
    if not invalidPairs.is_empty():
        raise ValueError(f"EDGAR finance CIK/ticker identity 불일치: {invalidPairs.head(10).to_dicts()}")
    coverage = finance["stockCode"].n_unique() / len(cikToTicker)
    if coverage < 0.75:
        raise ValueError(f"EDGAR finance listed coverage 미달: {coverage:.4%} < 75.0000%")
    return counts


def _edgarPrebuildContracts() -> tuple:
    """EDGAR prebuild 8종의 relative path, exact schema, identity key SSOT를 반환한다."""

    from dartlab.scan.builders.edgar.report.auditorBuild import AUDITOR_COLS
    from dartlab.scan.builders.edgar.report.build import (
        CAPITAL_CHANGES_COLS,
        DEBT_MATURITY_COLS,
        EXEC_COMP_COLS,
        SHAREHOLDER_RETURN_COLS,
    )
    from dartlab.scan.builders.edgar.report.employeeBuild import EMPLOYEE_COLS
    from dartlab.scan.builders.edgar.valuationBuild import VALUATION_SCHEMA

    return (
        (Path("finance.parquet"), FINANCE_SCHEMA, ["stockCode", "fy"]),
        (Path("valuation.parquet"), VALUATION_SCHEMA, ["stockCode"]),
        (Path("report/shareholderReturn.parquet"), SHAREHOLDER_RETURN_COLS, ["stockCode", "year"]),
        (Path("report/debtMaturity.parquet"), DEBT_MATURITY_COLS, ["stockCode", "year"]),
        (Path("report/execComp.parquet"), EXEC_COMP_COLS, ["stockCode", "year"]),
        (Path("report/capitalChanges.parquet"), CAPITAL_CHANGES_COLS, ["stockCode", "year"]),
        (Path("report/employee.parquet"), EMPLOYEE_COLS, ["stockCode", "year"]),
        (Path("report/auditor.parquet"), AUDITOR_COLS, ["stockCode", "year"]),
    )


def _writeEdgarPrebuildManifest(scanDir: Path, counts: dict[str, int]) -> Path:
    """검증된 8종 artifact의 size와 SHA-256을 결정적 manifest로 원자 기록한다."""

    artifactPaths = [relative.as_posix() for relative, _, _ in _edgarPrebuildContracts()]
    if set(counts) != set(artifactPaths):
        raise ValueError(f"EDGAR prebuild manifest count 계약 불일치: {sorted(counts)}")
    artifacts = []
    for relative in artifactPaths:
        path = scanDir / relative
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        artifacts.append(
            {
                "path": relative,
                "rows": counts[relative],
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    payload = {
        "kind": "dartlab.edgar.scan.prebuild",
        "schemaVersion": 1,
        "artifacts": artifacts,
    }
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor, temporaryName = tempfile.mkstemp(
        prefix=".prebuild-manifest-",
        suffix=".tmp.json",
        dir=scanDir,
    )
    os.close(descriptor)
    temporary = Path(temporaryName)
    try:
        with temporary.open("wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        output = scanDir / _PREBUILD_MANIFEST_NAME
        os.replace(temporary, output)
        if os.name != "nt":
            directoryDescriptor = os.open(scanDir, os.O_RDONLY)
            try:
                os.fsync(directoryDescriptor)
            finally:
                os.close(directoryDescriptor)
        return output
    except BaseException as primaryError:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException as cleanupError:
            raise BaseExceptionGroup(
                "EDGAR prebuild manifest write와 temporary cleanup이 함께 실패했습니다",
                [primaryError, cleanupError],
            ) from primaryError
        raise


def buildEdgarPrebuild(*, sinceYear: int = 2021, verbose: bool = False) -> dict[str, int]:
    """EDGAR scan 소유 artifact 전체를 단일 lock 안에서 빌드하고 계약 검증한다."""

    from filelock import FileLock

    from dartlab import config as _cfg
    from dartlab.scan.builders.edgar.report import buildEdgarPanelReports, buildEdgarReport
    from dartlab.scan.builders.edgar.valuationBuild import buildEdgarValuation

    scanDir = Path(_cfg.dataDir) / "edgar" / "scan"
    scanDir.mkdir(parents=True, exist_ok=True)
    with FileLock(scanDir / ".prebuild.lock", timeout=0):
        buildEdgarFinance(sinceYear=sinceYear, verbose=verbose)
        buildEdgarValuation(verbose=verbose)
        buildEdgarReport(verbose=verbose)
        buildEdgarPanelReports(verbose=verbose)
        counts = validateEdgarPrebuild(scanDir=scanDir)
        _writeEdgarPrebuildManifest(scanDir, counts)
        return counts


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
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise RuntimeError(f"EDGAR SIC 원천 읽기 실패: path={p}") from exc
    if not frames:
        return {}

    merged = pl.concat(frames, how="vertical_relaxed").filter(pl.col("sic").is_not_null())
    if merged.is_empty():
        return {}

    # CIK 별 최신 filed 행 (filed 가 동일할 때 첫 번째)
    latest = (
        merged.with_columns(pl.col("cik").cast(pl.Utf8).str.zfill(10))
        .sort("filed", descending=True)
        .group_by("cik")
        .head(1)
    )
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
