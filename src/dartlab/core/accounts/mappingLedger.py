"""미매핑 계정 관측 ledger.

본 모듈은 `providers/dart/finance/pivot.py` 의 `_pivotToSeries` 가
미매핑 계정 (account_id 표준 X 또는 한글명 사전 미커버) 을 fallback
처리할 때 옵트인으로 호출. ndjson append 만 수행하며 prod 동작 0 영향.

ENV gate:
    `DARTLAB_MAPPING_LEDGER` ∈ {"1", "true", "yes", "on"} 일 때만 활성.
    경로는 `DARTLAB_MAPPING_LEDGER_PATH` 또는 기본 `data/mapping_candidates_raw.ndjson`.

산출물:
    ndjson 1 줄 = 1 관측 단위 (Company 1 회 호출당 unmapped 계정 1 종).
    schema:
        observedAt: ISO8601
        stockCode:  종목코드 (호출자 주입, 없으면 빈 문자열)
        accountId:  DART account_id (보통 "-표준계정코드 미사용-")
        accountNm:  한글 계정명
        sjDiv:      "BS" / "IS" / "CF" / "CIS"
        occurrenceCount: 본 Company 호출 단위 내 동일 키 등장 행 수

후속:
    `reference/mapping/mappingLedgerCompact.py`가 strict하게 읽고 5 신호를 평가한다.

AIContext:
    - 자동화 안전장치: 본 모듈은 *관측* 만. accountMappings.json
      patch 는 별도 promote CLI 의 단독 권한 (관측·후보·승인·반영 4 단계 분리).
    - ENV OFF 가 기본. 사용자 영향 0.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_ENV_FLAG = "DARTLAB_MAPPING_LEDGER"
_ENV_PATH = "DARTLAB_MAPPING_LEDGER_PATH"
_DEFAULT_REL_PATH = Path("data") / "mapping_candidates_raw.ndjson"
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LOCK_TIMEOUT_SECONDS = 10.0


class MappingLedgerLockError(OSError):
    """ledger process lock을 제한 시간 안에 얻지 못한 경우."""


def isEnabled() -> bool:
    """Args: 없음.

    Returns:
        ENV `DARTLAB_MAPPING_LEDGER` 가 truthy 집합 ("1"/"true"/"yes"/"on",
        대소문자 무시) 이면 True. 기본 False.

    Example:
        >>> os.environ.pop("DARTLAB_MAPPING_LEDGER", None)
        >>> isEnabled()
        False
        >>> os.environ["DARTLAB_MAPPING_LEDGER"] = "1"
        >>> isEnabled()
        True

    Raises:
        없음.
    """
    raw = os.environ.get(_ENV_FLAG, "")
    return raw.strip().lower() in _TRUTHY


def ledgerPath() -> Path:
    """Args: 없음.

    Returns:
        ENV `DARTLAB_MAPPING_LEDGER_PATH` 가 있으면 그 경로, 없으면 cwd 기준
        ``data/mapping_candidates_raw.ndjson``. 경로 생성은 하지 않는다.

    Example:
        >>> os.environ.pop("DARTLAB_MAPPING_LEDGER_PATH", None)
        >>> ledgerPath().name
        'mapping_candidates_raw.ndjson'

    Raises:
        없음.
    """
    override = os.environ.get(_ENV_PATH, "").strip()
    if override:
        return Path(override)
    return _DEFAULT_REL_PATH


@contextmanager
def locked(path: Path, *, timeoutSeconds: float | None = None) -> Iterator[None]:
    """ledger 파일의 writer와 compactor가 공유하는 process lock.

    Args:
        path: 보호할 ledger 경로.
        timeoutSeconds: lock 대기 상한. None이면 기본 10초.

    Yields:
        lock을 보유한 임계 구역.

    Example:
        >>> with locked(Path("data/mapping_candidates_raw.ndjson")):  # doctest: +SKIP
        ...     pass

    Raises:
        MappingLedgerLockError: filelock이 없는 런타임이거나 대기 시간이 초과된 경우.
        OSError: lock 획득 또는 해제 중 운영체제 오류가 발생한 경우.
    """
    try:
        from filelock import FileLock
        from filelock import Timeout as FileLockTimeout
    except ModuleNotFoundError as exc:  # pragma: no cover - native dependency 계약 위반
        raise MappingLedgerLockError("mapping ledger lock requires the filelock package") from exc

    timeout = _LOCK_TIMEOUT_SECONDS if timeoutSeconds is None else timeoutSeconds
    lock = FileLock(str(path.with_name(f"{path.name}.lock")))
    try:
        lock.acquire(timeout=timeout)
    except FileLockTimeout as exc:
        raise MappingLedgerLockError(f"mapping ledger lock timeout: {path}") from exc
    try:
        yield
    finally:
        lock.release()


def _serializeRecords(
    records: Iterable[Mapping[str, object]],
    *,
    observedAt: str,
    stockCode: str,
) -> list[str]:
    """전체 batch를 검증하고 NDJSON line으로 직렬화한다.

    파일을 열기 전에 모든 record를 검증하므로 중간 record 오류가 앞선 line만
    기록하는 부분 commit을 만들지 않는다.
    """
    lines: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError(f"records[{index}] must be a mapping")

        textFields: dict[str, str] = {}
        for field in ("accountId", "accountNm", "sjDiv"):
            value = record.get(field, "")
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise TypeError(f"records[{index}].{field} must be str")
            textFields[field] = value
        if not textFields["accountNm"].strip():
            raise ValueError(f"records[{index}].accountNm must not be empty")
        if not textFields["sjDiv"].strip():
            raise ValueError(f"records[{index}].sjDiv must not be empty")

        rawCount = record.get("occurrenceCount", 0)
        if isinstance(rawCount, bool) or not isinstance(rawCount, int):
            raise TypeError(f"records[{index}].occurrenceCount must be a positive integer")
        occurrenceCount = rawCount
        if occurrenceCount <= 0:
            raise ValueError(f"records[{index}].occurrenceCount must be greater than zero")

        line = {
            "observedAt": observedAt,
            "stockCode": stockCode,
            **textFields,
            "occurrenceCount": occurrenceCount,
        }
        extras = {key: value for key, value in record.items() if key not in line}
        line.update(extras)
        lines.append(json.dumps(line, ensure_ascii=False) + "\n")
    return lines


def append(records: Iterable[Mapping[str, object]], stockCode: str | None = None) -> int:
    """ledger 에 nonstd 관측을 ndjson 으로 누적.

    Args:
        records: 각 dict 는 최소 ``accountId``·``accountNm``·``sjDiv``·
            ``occurrenceCount`` 키 보유. 추가 키는 그대로 보존.
        stockCode: 호출자가 알면 주입. None 이면 빈 문자열로 기록.

    Returns:
        실제 기록된 라인 수. ENV OFF 면 0.

    Example:
        >>> os.environ["DARTLAB_MAPPING_LEDGER"] = "1"
        >>> n = append([{"accountId": "", "accountNm": "기타의금융자산",
        ...              "sjDiv": "BS", "occurrenceCount": 14}], "005930")
        >>> n
        1

    Raises:
        OSError: ledger 디렉토리 생성·파일 append 실패 시.
        TypeError: record field 또는 extra가 직렬화 불가능한 타입일 때.
        ValueError: occurrenceCount가 양수가 아닐 때.
    """
    if not isEnabled():
        return 0

    if stockCode is not None and not isinstance(stockCode, str):
        raise TypeError("stockCode must be str or None")
    observedAt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    code = (stockCode or "").strip()
    lines = _serializeRecords(records, observedAt=observedAt, stockCode=code)
    if not lines:
        return 0

    path = ledgerPath()
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path):
        with path.open("a", encoding="utf-8") as f:
            f.write("".join(lines))
            f.flush()
            os.fsync(f.fileno())
    return len(lines)
