"""EDGAR scan 프리빌드 — 전종목 재무 지표를 단일 parquet로 합산.

DART scan/builder.py 패턴을 EDGAR에 이식.
200개 단위 배치 + 중간 파일 병합 + 메모리 안전.

사용법::

    from dartlab.scan.edgarBuilder import buildEdgarScan
    path = buildEdgarScan(sinceYear=2021, verbose=True)
"""

from __future__ import annotations

import gc
from pathlib import Path

import polars as pl

_BATCH_SIZE = 200


def buildEdgarFinance(*, sinceYear: int = 2021, verbose: bool = False) -> Path:
    """전종목 EDGAR finance → scan/finance.parquet.

    각 CIK parquet에서 최신 연간 BS/IS/CF 주요 계정을 추출하여
    하나의 wide DataFrame으로 합산한다.
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
        print(f"[edgarBuilder] {len(parquets)} CIK parquets → scan/finance.parquet")

    # snakeId → XBRL 태그 역조회 테이블 (사전 빌드, map_elements 회피)
    snakeIdToTags = _buildReverseTagMap(targetAccounts)

    # 주요 계정
    targetAccounts = [
        "sales",
        "operating_profit",
        "net_profit",
        "total_assets",
        "current_assets",
        "total_liabilities",
        "current_liabilities",
        "total_stockholders_equity",
        "operating_cashflow",
        "investing_cashflow",
        "financing_cash_flow",
        "capex",
        "dividends_paid",
        "cash_and_cash_equivalents",
        "inventories",
        "trade_and_other_receivables",
        "trade_and_other_payables",
        "interest_expense",
        "treasury_stock",
        "shortterm_borrowings",
        "longterm_borrowings",
        "depreciation_amortization",
    ]

    batchFiles: list[Path] = []
    records: list[dict] = []

    for idx, fp in enumerate(parquets):
        cik = fp.stem
        try:
            df = pl.read_parquet(fp)
            if df.is_empty():
                continue

            # 10-K만, sinceYear 이후
            annual = df.filter((pl.col("form") == "10-K") & (pl.col("fy") >= sinceYear))
            if annual.is_empty():
                continue

            latestFy = annual["fy"].max()
            latest = annual.filter(pl.col("fy") == latestFy)
            entityName = latest["entityName"][0] if latest.height > 0 else ""

            # snakeId 매핑 → 최신값 추출 (is_in 필터, map_elements 회피)
            record: dict = {"stockCode": cik, "corpName": entityName, "fy": int(latestFy)}
            usdRows = latest.filter(pl.col("unit").str.contains("(?i)USD"))
            for snakeId in targetAccounts:
                candidateTags = snakeIdToTags.get(snakeId, [])
                if not candidateTags:
                    continue
                tagRows = usdRows.filter(pl.col("tag").is_in(candidateTags))
                if tagRows.height > 0:
                    val = tagRows.sort("filed", descending=True)["val"][0]
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
                print(f"  batch {len(batchFiles)}: {idx + 1}/{len(parquets)}")

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
        print(f"[edgarBuilder] 완료: {outPath} ({merged.height}행, {merged.width}열)")

    return outPath


def buildEdgarScan(*, sinceYear: int = 2021, verbose: bool = False) -> Path:
    """전체 EDGAR scan 프리빌드."""
    return buildEdgarFinance(sinceYear=sinceYear, verbose=verbose)


def _buildReverseTagMap(snakeIds: list[str]) -> dict[str, list[str]]:
    """snakeId → XBRL 태그 목록 역조회 테이블.

    EdgarMapper.getTagsForSnakeIds()를 개별 snakeId씩 호출하여
    snakeId별 후보 태그 목록을 구축. map_elements 회피.
    """
    from dartlab.providers.edgar.finance.mapper import EdgarMapper

    result: dict[str, list[str]] = {}
    for sid in snakeIds:
        tags = EdgarMapper.getTagsForSnakeIds([sid])
        result[sid] = sorted(tags)
    return result


def _guessStmt(snakeId: str) -> str:
    """snakeId로 재무제표 유형 추정."""
    if snakeId in ("sales", "operating_profit", "net_profit", "interest_expense", "depreciation_amortization"):
        return "IS"
    if snakeId in ("operating_cashflow", "investing_cashflow", "financing_cash_flow", "capex", "dividends_paid"):
        return "CF"
    return "BS"
