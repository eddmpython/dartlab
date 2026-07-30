"""DART corpProfile의 결산월과 법인 identity SSOT를 발행한다.

OpenDART ``companyInfo()`` 의 ``acc_mt``와 ``jurir_no``를 상장 corp_code 전종목에
대해 prefetch하여 ``data/dart/scan/corpProfile.parquet`` 으로 저장한다. 결산월은
calendarization 기준이고 법인등록번호는 network affiliate identity의 exact 기준이다.

책임 위치: **sync (meta) 단계** — 외부 API 호출이므로 prebuild 안에 박으면 안 된다.
``kindlist.yml`` 의 corp_profile step 으로 매일 cron 갱신, HF dataset ``dart/scan/`` 에
upload. prebuild 는 HF 에서 다운로드한 parquet 만 읽는다.

사용법::

    uv run python -X utf8 .github/scripts/meta/buildCorpProfile.py
    uv run python -X utf8 .github/scripts/meta/buildCorpProfile.py --limit 100   # 테스트
    uv run python -X utf8 .github/scripts/meta/buildCorpProfile.py --workers 5   # 동시 호출 수

환경변수: ``OPEN_DART_KEY`` 또는 ``DART_API_KEY`` 필수.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.core.dartClient import DartClient, resolveDartKeys
from dartlab.core.dataLoader import _dataDir
from dartlab.gather.dart.corpCode import loadCorpCodes
from dartlab.gather.dart.disclosure import companyInfo
from dartlab.scan.builders.kr.corpProfile import (
    CORP_PROFILE_SCHEMA,
    CORP_PROFILE_SCHEMA_VERSION,
    normalizeCorpProfileRow,
    normalizeJurirNo,
)


def _resolveApiKeys() -> list[str]:
    """DART OpenAPI 키를 공통 credential provider에서 추출한다."""

    keys = resolveDartKeys()
    if keys:
        return keys
    legacyKey = os.environ.get("OPEN_DART_KEY", "")
    if legacyKey:
        return [legacyKey]
    raise RuntimeError("DART_API_KEY(S) 또는 OPEN_DART_KEY 환경변수 필요")


def _atomicWriteParquet(combined: dict[str, dict], outPath: Path) -> None:
    """corp_code 매핑 dict → parquet 으로 atomic 저장 (temp → rename).

    중간 저장과 최종 저장 모두 호출. 도중 실패해도 기존 파일 보존 (PolarsError 가
    write 중 났을 때 partial file 이 ``corpProfile.parquet`` 을 덮어쓰지 않게).
    """
    normalizedRows = sorted(
        (normalizeCorpProfileRow(row) for row in combined.values()),
        key=lambda row: str(row["corp_code"]),
    )
    df = pl.DataFrame(normalizedRows, schema=CORP_PROFILE_SCHEMA)
    outPath.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporaryName = tempfile.mkstemp(
        prefix=f".{outPath.stem}-",
        suffix=".tmp.parquet",
        dir=outPath.parent,
    )
    os.close(descriptor)
    temporary = Path(temporaryName)
    try:
        df.write_parquet(temporary, compression="zstd")
        written = pl.read_parquet(temporary)
        if written.schema != CORP_PROFILE_SCHEMA or written.height != df.height:
            raise RuntimeError(
                "corpProfile 임시 artifact 검증 실패: "
                f"schema={written.schema == CORP_PROFILE_SCHEMA}, "
                f"rows={written.height}/{df.height}"
            )
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, outPath)
    except BaseException as primaryError:
        try:
            temporary.unlink(missing_ok=True)
        except BaseException as cleanupError:
            raise BaseExceptionGroup(
                "corpProfile write와 temp cleanup이 함께 실패했습니다",
                [primaryError, cleanupError],
            ) from primaryError
        raise


def _fetchOne(client: Any, row: dict, *, retry: int = 5, delay: float = 0.5) -> dict | None:
    """단일 corp_code 의 companyInfo() 호출 → dict 반환. 실패 시 None.

    DART OpenAPI 가 일시적 "Server disconnected" 다발 시 exponential backoff 로 재시도.
    """
    corpCode = row["corp_code"]
    stockCode = row.get("stock_code", "") or ""
    corpName = row.get("corp_name", "") or ""

    for attempt in range(retry + 1):
        try:
            info = companyInfo(client, corpCode)
            rawJurirNo = info.get("jurir_no", "")
            jurirNo = normalizeJurirNo(rawJurirNo)
            if rawJurirNo and jurirNo is None:
                raise ValueError(f"invalid jurir_no: {rawJurirNo!r}")
            return {
                "corp_code": corpCode,
                "stockCode": stockCode,
                "corp_name": corpName,
                "jurir_no": jurirNo or "",
                "bizr_no": info.get("bizr_no", ""),
                "acc_mt": info.get("acc_mt", ""),
                "induty_code": info.get("induty_code", ""),
                "est_dt": info.get("est_dt", ""),
                "corp_cls": info.get("corp_cls", ""),
                "profileSchemaVersion": CORP_PROFILE_SCHEMA_VERSION,
            }
        except Exception as e:
            if attempt >= retry:
                print(f"  ⚠ {corpCode} ({corpName}) 실패: {e}", file=sys.stderr)
                return None
            # exponential backoff: 0.5s → 1s → 2s → 4s → 8s
            time.sleep(delay * (2**attempt))
    return None


def buildCorpProfile(
    *,
    stockOnly: bool = True,
    workers: int = 5,
    limit: int = 0,
    output: Path | None = None,
    resume: bool = True,
) -> Path | None:
    """전 corp_code 대상 companyInfo() prefetch + parquet 저장.

    매 prebuild 사이클 (Data Sync 직후) 호출되어 신규 상장 / 상장폐지 / 결산월
    변경을 즉시 반영하는 corp_profile dataset 갱신. 기존 결과가 있으면 누락된
    corp_code 만 incremental 호출 (resume=True) 하여 DART OpenAPI rate limit 으로
    부분 실패한 호출도 누적 완성.

    Parameters
    ----------
    stockOnly : bool
        True 면 ``stock_code`` 있는 종목 (상장사 ~3964) 만. False 면 전종목 (~117K).
    workers : int
        ThreadPool 동시 호출 수. DART OpenAPI rate limit 고려 (기본 5 보수).
    limit : int
        0 = 무제한, > 0 = 첫 N 종목 (테스트용).
    output : Path | None
        결과 parquet 저장 경로. None 이면 ``data/dart/scan/corpProfile.parquet``.
    resume : bool
        True (기본) 면 기존 parquet 의 corp_code 는 skip, missing 만 호출. False
        면 전종목 재호출.

    Returns
    -------
    Path | None
        저장된 parquet 경로. API 키 없거나 결과 0 이면 None.
    """
    try:
        apiKeys = _resolveApiKeys()
    except RuntimeError as e:
        print(f"[corpProfile] {e} — 스킵")
        return None

    client = DartClient(apiKeys=apiKeys)

    print("[corpProfile] corp_code master 로드 ...")
    master = loadCorpCodes(client)
    print(f"[corpProfile] master rows: {master.height}")

    if stockOnly:
        master = master.filter(
            pl.col("stock_code").is_not_null() & (pl.col("stock_code") != "") & (pl.col("stock_code") != " ")
        )
        print(f"[corpProfile] stock_code 있는 종목만: {master.height}")

    if limit > 0:
        master = master.head(limit)
        print(f"[corpProfile] limit 적용: {master.height}")

    outPath = output if output else Path(_dataDir("scan")) / "corpProfile.parquet"

    # resume: 기존 결과 있으면 corp_code 매핑 미리 로드, missing 만 호출
    existing: dict[str, dict] = {}
    if resume and outPath.exists():
        try:
            existDf = pl.read_parquet(str(outPath))
            existing = {
                str(row.get("corp_code", "")): normalizeCorpProfileRow(row)
                for row in existDf.to_dicts()
                if row.get("corp_code")
            }
            print(f"[corpProfile] resume: 기존 {len(existing)}개 skip, missing 만 호출")
        except (pl.exceptions.PolarsError, OSError) as e:
            print(f"[corpProfile] resume 실패 (재시작): {e}")
            existing = {}

    allRows = master.to_dicts()
    masterCodes = {row["corp_code"] for row in allRows}
    if limit == 0:
        existing = {corpCode: row for corpCode, row in existing.items() if corpCode in masterCodes}
    for masterRow in allRows:
        prior = existing.get(masterRow["corp_code"])
        if prior is not None:
            prior["stockCode"] = str(masterRow.get("stock_code", "") or "")
            prior["corp_name"] = str(masterRow.get("corp_name", "") or "")
    rows = [
        row
        for row in allRows
        if row["corp_code"] not in existing
        or int(existing[row["corp_code"]].get("profileSchemaVersion", 1)) < CORP_PROFILE_SCHEMA_VERSION
    ]
    print(f"[corpProfile] 호출 대상: {len(rows)} (skip {len(existing)})")
    results: list[dict] = []
    failed = 0
    t0 = time.perf_counter()

    outPath.parent.mkdir(parents=True, exist_ok=True)

    # 중간 저장 빈도 — 인터럽트/quota 소진 시점까지 누적된 결과 보존.
    FLUSH_EVERY = 500
    combined: dict[str, dict] = dict(existing)

    print(f"[corpProfile] companyInfo 병렬 prefetch (workers={workers}) ...")
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_fetchOne, client, row) for row in rows]
            for i, fut in enumerate(as_completed(futures), 1):
                result = fut.result()
                if result is None:
                    failed += 1
                else:
                    results.append(result)
                    combined[result["corp_code"]] = result
                if i % 200 == 0:
                    elapsed = time.perf_counter() - t0
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"  [{i}/{len(rows)}] {len(results)}ok {failed}fail {rate:.1f}/s")
                if i % FLUSH_EVERY == 0 and combined:
                    _atomicWriteParquet(combined, outPath)
                    print(f"  → 중간 저장: {len(combined)} rows")
    except KeyboardInterrupt:
        print("[corpProfile] 인터럽트 — 누적 결과 저장 후 종료")
        if combined:
            _atomicWriteParquet(combined, outPath)
        raise

    elapsed = time.perf_counter() - t0
    print(f"[corpProfile] 완료: {len(results)}ok {failed}fail {elapsed:.0f}초")

    if not combined:
        print("[corpProfile] 결과 없음 — 종료")
        return None

    _atomicWriteParquet(combined, outPath)
    df = pl.read_parquet(str(outPath))
    diskKb = outPath.stat().st_size / 1024
    print(f"[corpProfile] saved: {outPath} ({df.height} rows, {diskKb:.0f}KB)")

    # 결산월 분포 요약
    accDist = (
        df.filter((pl.col("stockCode") != "") & (pl.col("acc_mt") != ""))
        .group_by("acc_mt")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )
    print("[corpProfile] 상장사 결산월 분포:")
    print(accDist)
    completed = df.filter(pl.col("profileSchemaVersion") >= CORP_PROFILE_SCHEMA_VERSION).height
    legalIds = df.filter(pl.col("jurir_no").str.len_chars() == 13).height
    print(
        f"[corpProfile] profile v2 완료 {completed:,}/{df.height:,}, "
        f"valid jurir_no {legalIds:,}, retry {df.height - completed:,}"
    )

    return outPath


def main() -> int:
    """CLI wrapper — argparse + buildCorpProfile()."""
    parser = argparse.ArgumentParser(description="DART corp_profile prefetch 빌드")
    parser.add_argument("--limit", type=int, default=0, help="처리할 최대 종목 수 (0=무제한, 테스트용)")
    parser.add_argument("--workers", type=int, default=5, help="동시 호출 수 (rate limit, 기본 5)")
    parser.add_argument(
        "--allCorps",
        action="store_true",
        help="비상장 포함 전종목 (~117K, 기본은 상장사 ~3964만)",
    )
    parser.add_argument("--output", type=str, default="", help="출력 path (기본 data/dart/scan/corpProfile.parquet)")
    parser.add_argument("--noResume", action="store_true", help="기존 결과 무시하고 전종목 재호출")
    args = parser.parse_args()

    result = buildCorpProfile(
        stockOnly=not args.allCorps,
        workers=args.workers,
        limit=args.limit,
        output=Path(args.output) if args.output else None,
        resume=not args.noResume,
    )
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
