"""자격증명 lifecycle 추적 + 만료 임계 알람 (T2-4).

DART API key (90 일 lifecycle, 사용자 갱신 필요) + OAuth token (자동 refresh
가능) 의 *만료 임계 점검*. 임계 도달 시 logEvent 알람 + INCIDENTS 자동 항목
(T1-3 통합 후속).

API:
    recordIssuance(key, issuedAt, lifetimeDays) -> None
    checkLifecycle(thresholdDays=14) -> list[CredentialAlert]
    daysUntilExpiry(key) -> int | None

저장: `data/_credentials/lifecycle.json` (gitignored, 로컬 추적).

SecretStore의 암호화 backend와 독립된 만료 메타데이터이며 비밀 값은 기록하지 않는다.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dartlab.core.logger import logEvent


def _defaultLifecycleFile() -> Path:
    """기본 lifecycle 저장 경로 — DARTLAB_CREDENTIAL_DIR env override 가능."""
    custom = os.getenv("DARTLAB_CREDENTIAL_DIR")
    if custom:
        return Path(custom) / "lifecycle.json"
    return Path.cwd() / "data" / "_credentials" / "lifecycle.json"


@dataclass
class CredentialAlert:
    """단일 자격증명 만료 임계 알람."""

    key: str
    issuedAt: str
    expiresAt: str
    daysRemaining: int
    severity: str  # "ok" / "warning" / "critical" / "expired"


class CredentialLifecycleError(RuntimeError):
    """credential lifecycle 저장소 접근 또는 내용 오류."""


class CredentialLifecycleReadError(CredentialLifecycleError):
    """존재하는 lifecycle 파일을 읽지 못한 경우."""


class CredentialLifecycleCorruptError(CredentialLifecycleError):
    """lifecycle JSON 또는 entry schema가 손상된 경우."""


def _corrupt(path: Path, message: str, *, key: str | None = None) -> CredentialLifecycleCorruptError:
    location = f"{path} [{key}]" if key is not None else str(path)
    return CredentialLifecycleCorruptError(f"credential lifecycle 손상: {location}: {message}")


def _parseStoredExpiry(path: Path, key: str, entry: object) -> dt.datetime:
    if not isinstance(entry, dict):
        raise _corrupt(path, "entry가 object가 아닙니다", key=key)
    expiresAt = entry.get("expiresAt")
    if not isinstance(expiresAt, str) or not expiresAt.strip():
        raise _corrupt(path, "expiresAt이 문자열이 아닙니다", key=key)
    try:
        expires = dt.datetime.fromisoformat(expiresAt.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _corrupt(path, "expiresAt이 ISO datetime이 아닙니다", key=key) from exc
    if expires.tzinfo is None or expires.utcoffset() is None:
        raise _corrupt(path, "expiresAt에 timezone이 없습니다", key=key)
    issuedAt = entry.get("issuedAt")
    if not isinstance(issuedAt, str) or not issuedAt.strip():
        raise _corrupt(path, "issuedAt이 문자열이 아닙니다", key=key)
    try:
        issued = dt.datetime.fromisoformat(issuedAt.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _corrupt(path, "issuedAt이 ISO datetime이 아닙니다", key=key) from exc
    if issued.tzinfo is None or issued.utcoffset() is None:
        raise _corrupt(path, "issuedAt에 timezone이 없습니다", key=key)
    if issued > expires:
        raise _corrupt(path, "issuedAt이 expiresAt보다 늦습니다", key=key)
    return expires


def _loadLifecycle(path: Path | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, dt.datetime]]:
    resolvedPath = path or _defaultLifecycleFile()
    try:
        raw = resolvedPath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}, {}
    except UnicodeDecodeError as exc:
        raise _corrupt(resolvedPath, "UTF-8 decoding 실패") from exc
    except OSError as exc:
        raise CredentialLifecycleReadError(f"credential lifecycle 읽기 실패: {resolvedPath}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _corrupt(resolvedPath, "JSON 파싱 실패") from exc
    if not isinstance(data, dict):
        raise _corrupt(resolvedPath, "root가 object가 아닙니다")
    expiries: dict[str, dt.datetime] = {}
    for key, entry in data.items():
        if not isinstance(key, str):
            raise _corrupt(resolvedPath, "key가 문자열이 아닙니다")
        expiries[key] = _parseStoredExpiry(resolvedPath, key, entry)
    return data, expiries


def _saveLifecycle(data: dict, path: Path | None = None) -> None:
    path = path or _defaultLifecycleFile()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def recordIssuance(
    key: str,
    *,
    issuedAt: str | None = None,
    lifetimeDays: int = 90,
    path: Path | None = None,
) -> None:
    """자격증명 발급 시점 기록 (T10-4).

    Capabilities:
        DART API key / OAuth token 등의 발급 시점 + lifetime 을 lifecycle.json
        에 누적. checkLifecycle / daysUntilExpiry 의 입력.

    Args:
        key: 자격증명 식별자 (예: "DART_API_KEY").
        issuedAt: ISO datetime. None 이면 현재 시각.
        lifetimeDays: 발급 후 만료까지 일 수. DART API 기본 90.
        path: lifecycle 파일 override (테스트용).

    Returns:
        None.

    Example:
        >>> from dartlab.core.credentialLifecycle import recordIssuance
        >>> recordIssuance("DART_API_KEY", lifetimeDays=90)

    Guide:
        setSecret (T2-3) 직후 호출 권장. setup CLI 가 자동 동행하도록 후속.

    SeeAlso:
        checkLifecycle / daysUntilExpiry.

    Requires:
        쓰기 권한.

    AIContext:
        T2-4 보안 트랙.

    Raises:
        OSError: 디스크 쓰기 실패.
        TypeError: lifetimeDays가 정수가 아닌 경우.
        ValueError: issuedAt 형식 또는 lifetimeDays 범위 오류.
        CredentialLifecycleError: 기존 lifecycle 파일이 손상되었거나 읽기 실패한 경우.
    """
    if isinstance(lifetimeDays, bool) or not isinstance(lifetimeDays, int):
        raise TypeError("lifetimeDays must be an integer")
    if lifetimeDays <= 0:
        raise ValueError("lifetimeDays must be greater than zero")
    issued = issuedAt or dt.datetime.now(dt.UTC).isoformat()
    issuedDt = dt.datetime.fromisoformat(issued.replace("Z", "+00:00"))
    if issuedDt.tzinfo is None or issuedDt.utcoffset() is None:
        raise ValueError("issuedAt must include a timezone")
    expires = (issuedDt + dt.timedelta(days=lifetimeDays)).isoformat()

    data, _ = _loadLifecycle(path)
    data[key] = {
        "issuedAt": issued,
        "expiresAt": expires,
        "lifetimeDays": lifetimeDays,
        "recordedAt": dt.datetime.now(dt.UTC).isoformat(),
    }
    _saveLifecycle(data, path)
    logEvent("info", "credential_issuance_recorded", key=key, lifetime_days=lifetimeDays)


def daysUntilExpiry(key: str, *, path: Path | None = None) -> int | None:
    """key 의 만료까지 남은 일 수 (T10-4).

    Capabilities:
        recordIssuance() 로 기록된 key 의 expiresAt 기준 남은 일 수.

    Args:
        key: 자격증명 식별자.
        path: lifecycle 파일 override.

    Returns:
        남은 일수 (int) 또는 None (기록 없음). 음수면 expired.

    Example:
        >>> from dartlab.core.credentialLifecycle import daysUntilExpiry
        >>> days = daysUntilExpiry("DART_API_KEY")
        >>> if days is not None and days < 14:
        ...     print("갱신 임박")

    SeeAlso:
        recordIssuance / checkLifecycle.

    Requires:
        lifecycle.json 안 key 항목.

    AIContext:
        T2-4 보안 트랙. dashboard / setup CLI 에서 갱신 알람.

    Raises:
        CredentialLifecycleError: lifecycle 파일 또는 등록 entry가 손상된 경우.
    """
    data, expiries = _loadLifecycle(path)
    entry = data.get(key)
    if not entry:
        return None
    expires = expiries[key]
    delta = expires - dt.datetime.now(dt.UTC)
    return math.floor(delta.total_seconds() / 86400)


def checkLifecycle(*, thresholdDays: int = 14, path: Path | None = None) -> list[CredentialAlert]:
    """모든 등록 자격증명의 만료 임계 점검 (T10-4).

    Capabilities:
        recordIssuance() 로 등록된 모든 key 의 만료 일자 검사. severity 분류
        (ok / warning / critical / expired). warning 이상만 반환.

    Args:
        thresholdDays: warning 임계 (기본 14 일).
        path: lifecycle 파일 override (테스트용).

    Returns:
        severity 가 ok 아닌 CredentialAlert 리스트.

    Example:
        >>> from dartlab.core.credentialLifecycle import recordIssuance, checkLifecycle
        >>> recordIssuance("DART_API_KEY", lifetimeDays=90)
        >>> alerts = checkLifecycle(thresholdDays=14)

    Guide:
        DART API key 는 사용자 갱신 — alert 발생 시 신규 발급 + setSecret +
        recordIssuance 동행. OAuth token 은 자동 refresh 가능.

    SeeAlso:
        recordIssuance / daysUntilExpiry / SecretStore (T2-3).

    Requires:
        data/_credentials/lifecycle.json 존재 (없으면 빈 리스트 반환).

    AIContext:
        T2-4 보안 트랙. INCIDENTS 자동 알람 통합 후속.

    Raises:
        TypeError: thresholdDays가 정수가 아닌 경우.
        ValueError: thresholdDays가 음수인 경우.
        CredentialLifecycleError: lifecycle 파일 또는 등록 entry가 손상된 경우.
    """
    if isinstance(thresholdDays, bool) or not isinstance(thresholdDays, int):
        raise TypeError("thresholdDays must be an integer")
    if thresholdDays < 0:
        raise ValueError("thresholdDays must be greater than or equal to zero")
    resolvedPath = path or _defaultLifecycleFile()
    data, expiries = _loadLifecycle(resolvedPath)
    alerts: list[CredentialAlert] = []
    for key, entry in data.items():
        expires = expiries[key]
        days = math.floor((expires - dt.datetime.now(dt.UTC)).total_seconds() / 86400)
        if days < 0:
            severity = "expired"
        elif days < 3:
            severity = "critical"
        elif days < thresholdDays:
            severity = "warning"
        else:
            severity = "ok"

        if severity != "ok":
            alerts.append(
                CredentialAlert(
                    key=key,
                    issuedAt=entry.get("issuedAt", ""),
                    expiresAt=entry.get("expiresAt", ""),
                    daysRemaining=days,
                    severity=severity,
                )
            )
    if alerts:
        for alert in alerts:
            logEvent(
                "warning",
                "credential_lifecycle_alert",
                key=alert.key,
                severity=alert.severity,
                days_remaining=alert.daysRemaining,
            )
    return alerts


__all__ = [
    "CredentialAlert",
    "CredentialLifecycleCorruptError",
    "CredentialLifecycleError",
    "CredentialLifecycleReadError",
    "checkLifecycle",
    "daysUntilExpiry",
    "recordIssuance",
]
