"""DART OpenAPI 키 상태/저장/검증 공용 헬퍼."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DartKeyStatus:
    configured: bool
    source: str
    keyCount: int
    envPath: str
    writable: bool

    def toDict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "source": self.source,
            "keyCount": self.keyCount,
            "envPath": self.envPath,
            "writable": self.writable,
        }


def findProjectEnvPath(startPath: Path | None = None) -> Path:
    """프로젝트 루트 .env 경로를 추정한다."""
    start = startPath or Path.cwd()
    for current in (start, *start.parents):
        candidate = current / ".env"
        if candidate.exists():
            return candidate
    return start / ".env"


def loadDotenvDartKeys(startPath: Path | None = None) -> list[str]:
    """프로젝트 .env의 DART_API_KEY(S)를 읽는다."""
    envPath = findProjectEnvPath(startPath)
    if not envPath.exists():
        return []

    try:
        text = envPath.read_text(encoding="utf-8")
    except OSError:
        return []

    multiKeys: list[str] = []
    singleKey = ""
    for rawLine in text.splitlines():
        line = rawLine.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        normalizedKey = key.strip()
        normalizedValue = value.strip().strip("'\"")
        if normalizedKey == "DART_API_KEYS" and normalizedValue:
            multiKeys = [item.strip() for item in normalizedValue.split(",") if item.strip()]
        elif normalizedKey == "DART_API_KEY" and normalizedValue and not singleKey:
            singleKey = normalizedValue
    # 복수키 우선
    return multiKeys if multiKeys else ([singleKey] if singleKey else [])


def resolveDartKeys(
    apiKey: str | None = None,
    apiKeys: list[str] | None = None,
    *,
    startPath: Path | None = None,
) -> list[str]:
    """DART 키 우선순위: 인자 -> OS env -> 프로젝트 .env."""
    if apiKeys:
        return [item.strip() for item in apiKeys if item and item.strip()]
    if apiKey and apiKey.strip():
        return [apiKey.strip()]

    # OS env + .env 모두 확인해서 키가 더 많은 쪽 채택
    envKeys = os.environ.get("DART_API_KEYS", "")
    osKeysList = [item.strip() for item in envKeys.split(",") if item.strip()] if envKeys else []

    envKey = os.environ.get("DART_API_KEY", "")
    osSingleKey = [envKey.strip()] if envKey and envKey.strip() else []

    dotenvKeys = loadDotenvDartKeys(startPath)

    # 가장 많은 키를 가진 소스 반환
    candidates = [osKeysList, dotenvKeys, osSingleKey]
    best = max(candidates, key=len)
    return best if best else []


def hasDartApiKey(startPath: Path | None = None) -> bool:
    return bool(resolveDartKeys(startPath=startPath))


def getDartKeyStatus(startPath: Path | None = None) -> DartKeyStatus:
    envPath = findProjectEnvPath(startPath)
    envKeys = os.environ.get("DART_API_KEYS", "")
    envKey = os.environ.get("DART_API_KEY", "")
    dotenvKeys = loadDotenvDartKeys(startPath)

    if envKeys:
        keyCount = len([item for item in envKeys.split(",") if item.strip()])
        source = "env"
    elif envKey:
        keyCount = 1
        source = "env"
    elif dotenvKeys:
        keyCount = len(dotenvKeys)
        source = "dotenv"
    else:
        keyCount = 0
        source = "none"

    writableTarget = envPath if envPath.exists() else envPath.parent
    return DartKeyStatus(
        configured=keyCount > 0,
        source=source,
        keyCount=keyCount,
        envPath=str(envPath),
        writable=os.access(writableTarget, os.W_OK),
    )


def saveDartKeyToDotenv(key: str, startPath: Path | None = None) -> Path:
    """프로젝트 .env의 DART_API_KEY를 추가 또는 갱신한다."""
    envPath = findProjectEnvPath(startPath)
    lines: list[str] = []
    replaced = False

    if envPath.exists():
        text = envPath.read_text(encoding="utf-8")
        for rawLine in text.splitlines():
            stripped = rawLine.strip()
            if stripped.startswith("DART_API_KEY=") or stripped.startswith("DART_API_KEYS="):
                if not replaced:
                    lines.append(f"DART_API_KEY={key}")
                    replaced = True
                continue
            lines.append(rawLine)

    if not replaced:
        lines.append(f"DART_API_KEY={key}")

    envPath.parent.mkdir(parents=True, exist_ok=True)
    envPath.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return envPath


def clearDartKeyFromDotenv(startPath: Path | None = None) -> Path:
    """프로젝트 .env에서 DART_API_KEY(S)를 제거한다."""
    envPath = findProjectEnvPath(startPath)
    if not envPath.exists():
        return envPath

    text = envPath.read_text(encoding="utf-8")
    keptLines = [
        rawLine
        for rawLine in text.splitlines()
        if not rawLine.strip().startswith("DART_API_KEY=") and not rawLine.strip().startswith("DART_API_KEYS=")
    ]
    newText = "\n".join(keptLines).rstrip()
    envPath.write_text((newText + "\n") if newText else "", encoding="utf-8")
    return envPath


def validateDartApiKey(key: str) -> dict[str, Any]:
    """키 유효성만 빠르게 점검한다."""
    from dartlab.providers.dart.openapi.client import DartClient

    today = datetime.now().strftime("%Y%m%d")
    client = DartClient(apiKey=key)
    client.getJson(
        "list.json",
        {
            "bgn_de": today,
            "end_de": today,
            "page_no": "1",
            "page_count": "1",
        },
        emptyOn013=True,
    )
    return {"ok": True}
