"""환경변수 저장/조회 — .env 파일 기반."""

from __future__ import annotations

import os
from pathlib import Path

_ENV_FILE: Path | None = None


def _findEnvFile() -> Path:
    """프로젝트 루트 또는 CWD에서 .env 파일 경로 반환."""
    global _ENV_FILE
    if _ENV_FILE is not None:
        return _ENV_FILE

    # pyproject.toml 기준 프로젝트 루트 탐색
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists():
            _ENV_FILE = parent / ".env"
            return _ENV_FILE

    # fallback: CWD
    _ENV_FILE = cwd / ".env"
    return _ENV_FILE


def loadEnv() -> None:
    """프로젝트 .env 파일을 os.environ에 로드 (기존 값 덮어쓰지 않음)."""
    path = _findEnvFile()
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def saveEnvKey(key: str, value: str) -> Path:
    """키를 .env 파일에 저장 (기존 키면 갱신, 없으면 추가)."""
    path = _findEnvFile()
    lines: list[str] = []
    found = False

    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _, _ = stripped.partition("=")
                if k.strip() == key:
                    lines.append(f"{key}={value}")
                    found = True
                    continue
            lines.append(line)

    if not found:
        lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value
    return path


def promptAndSave(envKey: str, *, label: str, guide: str) -> str | None:
    """터미널/노트북에서 API 키를 입력받아 .env에 저장.

    Returns:
        입력된 키 문자열. 건너뛰면 None.
    """
    existing = os.environ.get(envKey)
    if existing:
        masked = existing[:4] + "..." + existing[-4:] if len(existing) > 8 else "***"
        print(f"\n  ✓ {envKey} 이미 설정됨 ({masked})\n")
        return existing

    print(f"\n  {label}")
    print(f"  {guide}")
    print("  입력하면 프로젝트 .env 파일에 안전하게 저장됩니다. (공유되지 않음)\n")

    try:
        key = input(f"  {envKey}: ").strip()
        if key:
            path = saveEnvKey(envKey, key)
            print(f"\n  ✓ {path} 에 저장 완료.\n")
            return key
        print("\n  건너뛰었습니다.\n")
        return None
    except (EOFError, KeyboardInterrupt):
        print("\n  건너뛰었습니다.\n")
        return None
