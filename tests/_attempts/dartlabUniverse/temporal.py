"""Universe U1 bitemporal point-in-time filtering."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .contracts import UniverseStatement


def parseInstant(value: str) -> datetime:
    """UTC offset이 있는 ISO 8601 instant만 허용한다."""
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timezone 없는 instant: {value}")
    return parsed.astimezone(timezone.utc)


def _insideHalfOpen(instant: datetime, start: str | None, end: str | None) -> bool:
    if start is not None and instant < parseInstant(start):
        return False
    return end is None or instant < parseInstant(end)


def asOfFilter(statement: UniverseStatement, validAt: str, knownAt: str) -> bool:
    """Statement가 validAt에 유효하고 knownAt에 알려졌으며 아직 철회되지 않았는지 판정한다."""
    validInstant = parseInstant(validAt)
    knownInstant = parseInstant(knownAt)
    if not _insideHalfOpen(validInstant, statement.validTime.start, statement.validTime.end):
        return False
    if parseInstant(statement.systemTime.knownAt) > knownInstant:
        return False
    if statement.systemTime.retractedAt is not None and parseInstant(statement.systemTime.retractedAt) <= knownInstant:
        return False
    return True


def pointInTimeStatements(
    statements: Iterable[UniverseStatement],
    validAt: str,
    knownAt: str,
) -> tuple[UniverseStatement, ...]:
    """Bitemporal 조건을 통과한 statement를 stable ID 순서로 반환한다."""
    return tuple(
        sorted((item for item in statements if asOfFilter(item, validAt, knownAt)), key=lambda x: x.statementId)
    )
