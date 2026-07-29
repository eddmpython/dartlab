"""mapping ledger NDJSON을 엄격히 검증해 운영자 검토용 parquet으로 압축한다.

`DARTLAB_MAPPING_LEDGER`가 켜진 동안 DART finance pivot이 기록한 관측을
``(accountId, accountNm)`` 단위로 그룹화하고 `mappingSignals.evaluate`의
5개 신호를 적용한다. 손상 행은 경로와 줄 번호를 포함한 예외로 중단하며
`accountMappings.json`은 읽기만 한다.

호출:
    uv run python -X utf8 src/dartlab/reference/mapping/mappingLedgerCompact.py \
        --raw data/mapping_candidates_raw.ndjson \
        --out data/mapping_candidates.parquet
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.core.accounts import mappingLedger
from dartlab.reference.mapping import mappingSignals

_DEFAULT_RAW = Path("data") / "mapping_candidates_raw.ndjson"
_DEFAULT_OUT = Path("data") / "mapping_candidates.parquet"
_DEFAULT_MAPPINGS = Path("src/dartlab/reference/data/accountMappings.json")
_TEXT_FIELDS = ("observedAt", "stockCode", "accountId", "accountNm", "sjDiv")


def _loadMappings(path: Path) -> tuple[dict[str, dict[str, object]], dict[str, str]]:
    """accountMappings.json의 두 필수 mapping을 schema 검증 후 반환한다."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"accountMappings.json 부재: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"accountMappings.json 손상: {path}:{exc.lineno}:{exc.colno}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"accountMappings.json root must be an object: {path}")
    standardAccounts = data.get("standardAccounts")
    mappings = data.get("mappings")
    if not isinstance(standardAccounts, dict):
        raise ValueError(f"accountMappings.json standardAccounts must be an object: {path}")
    if not isinstance(mappings, dict):
        raise ValueError(f"accountMappings.json mappings must be an object: {path}")

    for snakeId, meta in standardAccounts.items():
        if not isinstance(snakeId, str) or not snakeId:
            raise ValueError(f"accountMappings.json standardAccounts has invalid snakeId: {path}")
        if not isinstance(meta, dict):
            raise ValueError(f"accountMappings.json standardAccounts[{snakeId!r}] must be an object: {path}")
        korName = meta.get("korName")
        if not isinstance(korName, str) or not korName.strip():
            raise ValueError(
                f"accountMappings.json standardAccounts[{snakeId!r}].korName must be a non-empty string: {path}"
            )
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in mappings.items()):
        raise ValueError(f"accountMappings.json mappings keys and values must be strings: {path}")
    return standardAccounts, mappings


def _rowError(path: Path, lineNumber: int, message: str) -> ValueError:
    return ValueError(f"{path}:{lineNumber}: {message}")


def _validateLedgerRow(row: object, path: Path, lineNumber: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise _rowError(path, lineNumber, "ledger row must be a JSON object")
    for field in _TEXT_FIELDS:
        value = row.get(field)
        if not isinstance(value, str):
            raise _rowError(path, lineNumber, f"{field} must be a string")
    if not row["accountNm"].strip():
        raise _rowError(path, lineNumber, "accountNm must not be empty")
    if not row["sjDiv"].strip():
        raise _rowError(path, lineNumber, "sjDiv must not be empty")
    try:
        observedAt = datetime.fromisoformat(row["observedAt"])
    except ValueError as exc:
        raise _rowError(path, lineNumber, "observedAt must be ISO8601") from exc
    if observedAt.utcoffset() is None:
        raise _rowError(path, lineNumber, "observedAt must include a timezone")

    occurrenceCount = row.get("occurrenceCount")
    if isinstance(occurrenceCount, bool) or not isinstance(occurrenceCount, int):
        raise _rowError(path, lineNumber, "occurrenceCount must be a positive integer")
    if occurrenceCount <= 0:
        raise _rowError(path, lineNumber, "occurrenceCount must be greater than zero")
    return row


def _iterLedgerRows(path: Path) -> Iterator[dict[str, Any]]:
    """NDJSON을 한 줄씩 읽고 손상 위치를 보존한 strict row iterator를 반환한다."""
    try:
        stream = path.open("r", encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"mapping ledger 부재: {path}") from exc

    with stream:
        for lineNumber, rawLine in enumerate(stream, 1):
            if not rawLine.strip():
                continue
            try:
                row = json.loads(rawLine)
            except json.JSONDecodeError as exc:
                raise _rowError(
                    path,
                    lineNumber,
                    f"invalid JSON at column {exc.colno}",
                ) from exc
            yield _validateLedgerRow(row, path, lineNumber)


def _groupRows(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """strict ledger iterator를 ``(accountId, accountNm)`` 단위로 집계한다."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["accountId"], row["accountNm"])
        observedAt = row["observedAt"]
        aggregate = grouped.setdefault(
            key,
            {
                "firstSeenAt": observedAt,
                "lastSeenAt": observedAt,
                "occurrenceCount": 0,
                "stockCodes": set(),
                "sjDivs": set(),
            },
        )
        aggregate["firstSeenAt"] = min(aggregate["firstSeenAt"], observedAt)
        aggregate["lastSeenAt"] = max(aggregate["lastSeenAt"], observedAt)
        aggregate["occurrenceCount"] += row["occurrenceCount"]
        if row["stockCode"]:
            aggregate["stockCodes"].add(row["stockCode"])
        aggregate["sjDivs"].add(row["sjDiv"])
    return grouped


def compact(rawPath: Path, outPath: Path, mappingsPath: Path) -> int:
    """raw ledger를 평가해 staging parquet을 쓰고 그룹 수를 반환한다.

    Args:
        rawPath: strict하게 읽을 ledger NDJSON 경로.
        outPath: 운영자 검토용 staging parquet 경로.
        mappingsPath: 읽기 전용 accountMappings.json 경로.

    Returns:
        평가해 기록한 그룹 수.

    Example:
        >>> compact(Path("raw.ndjson"), Path("out.parquet"), _DEFAULT_MAPPINGS)  # doctest: +SKIP
        1

    Raises:
        FileNotFoundError: raw ledger 또는 accountMappings.json이 없는 경우.
        ValueError: NDJSON 행이나 accountMappings.json schema가 손상된 경우.
        MappingLedgerLockError: writer와 공유한 process lock 획득이 실패한 경우.
        OSError: 입력 또는 출력 파일 I/O가 실패한 경우.
    """
    standardAccounts, mappings = _loadMappings(mappingsPath)
    if not rawPath.is_file():
        raise FileNotFoundError(f"mapping ledger 부재: {rawPath}")
    with mappingLedger.locked(rawPath):
        grouped = _groupRows(_iterLedgerRows(rawPath))

    signalIndex = mappingSignals.buildSignalIndex(standardAccounts, mappings)
    nowIso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records: list[dict[str, object]] = []
    for (accountId, accountNm), aggregate in grouped.items():
        result = mappingSignals.evaluate(
            accountId=accountId,
            accountNm=accountNm,
            occurrenceCount=aggregate["occurrenceCount"],
            stockCodes=aggregate["stockCodes"],
            standardAccounts=standardAccounts,
            mappings=mappings,
            signalIndex=signalIndex,
        )
        records.append(
            {
                "firstSeenAt": aggregate["firstSeenAt"],
                "lastSeenAt": aggregate["lastSeenAt"] or nowIso,
                "accountId": accountId,
                "accountNm": accountNm,
                "occurrenceCount": aggregate["occurrenceCount"],
                "stockCodes": sorted(set(aggregate["stockCodes"])),
                "sjDivs": sorted(set(aggregate["sjDivs"])),
                "corporateDispersion": result.corporateDispersion,
                "suggestedSnakeId": result.suggestedSnakeId,
                "confidence": result.confidence,
                "signalBreakdown": json.dumps(result.breakdown(), ensure_ascii=False),
                "autoEligible": result.autoEligible,
                "status": "auto_proposed" if result.autoEligible else "human_review",
                "operatorNote": None,
                "decidedAt": None,
            }
        )

    schema = {
        "firstSeenAt": pl.String,
        "lastSeenAt": pl.String,
        "accountId": pl.String,
        "accountNm": pl.String,
        "occurrenceCount": pl.Int64,
        "stockCodes": pl.List(pl.String),
        "sjDivs": pl.List(pl.String),
        "corporateDispersion": pl.Int64,
        "suggestedSnakeId": pl.String,
        "confidence": pl.Float64,
        "signalBreakdown": pl.String,
        "autoEligible": pl.Boolean,
        "status": pl.String,
        "operatorNote": pl.String,
        "decidedAt": pl.String,
    }
    frame = pl.DataFrame(records, schema=schema)
    outPath.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(outPath)
    return frame.height


def _parseArgs(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--raw", type=Path, default=_DEFAULT_RAW)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--mappings", type=Path, default=_DEFAULT_MAPPINGS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI 인자를 처리해 compaction을 실행하고 성공 시 0을 반환한다.

    Args:
        argv: argparse 인자. None이면 현재 process 인자를 사용.

    Returns:
        성공 시 0.

    Example:
        >>> main(["--raw", "raw.ndjson", "--out", "out.parquet"])  # doctest: +SKIP
        0

    Raises:
        FileNotFoundError: 입력 ledger 또는 mappings 파일이 없는 경우.
        ValueError: 입력 schema가 손상된 경우.
        OSError: lock 또는 파일 I/O가 실패한 경우.
    """
    args = _parseArgs(list(sys.argv[1:] if argv is None else argv))
    count = compact(args.raw, args.out, args.mappings)
    print(f"[mappingLedgerCompact] {count} 그룹 평가 -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
