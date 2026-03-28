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
    """.env 파일을 os.environ에 로드 (기존 값 덮어쓰지 않음).

    Capabilities:
        - pyproject.toml 기준 프로젝트 루트에서 .env 자동 탐색
        - KEY=VALUE 형식 파싱 (주석, 빈 줄 무시)
        - 이미 설정된 환경변수는 덮어쓰지 않음 (시스템 우선)
        - 따옴표 자동 제거 (single/double)

    AIContext:
        API 키 로드 실패 시 이 함수 호출 여부를 먼저 확인.

    Args:
        없음.

    Returns:
        None. os.environ에 직접 반영.

    Requires:
        없음.

    Example::

        from dartlab.core.env import loadEnv
        loadEnv()  # .env 파일의 키가 os.environ에 반영
    """
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
    """.env 파일에 키-값 저장 (기존 키면 갱신, 없으면 추가).

    Capabilities:
        - 기존 키 in-place 갱신 (주석/순서 보존)
        - 새 키는 파일 끝에 추가
        - os.environ에도 즉시 반영
        - .env 파일이 없으면 자동 생성

    AIContext:
        setup 명령에서 API 키 저장 시 사용.

    Args:
        key: 환경변수 이름 (예: "GEMINI_API_KEY").
        value: 환경변수 값.

    Returns:
        Path — 저장된 .env 파일 경로.

    Requires:
        없음.

    Example::

        from dartlab.core.env import saveEnvKey
        path = saveEnvKey("GEMINI_API_KEY", "AIza...")
        # .env에 GEMINI_API_KEY=AIza... 저장 + os.environ 반영
    """
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
    """터미널/노트북에서 API 키를 대화형 입력받아 .env에 저장.

    Capabilities:
        - 이미 설정된 키는 마스킹 표시 후 스킵
        - 사용자 입력 → saveEnvKey로 .env 영구 저장
        - EOFError/KeyboardInterrupt 안전 처리
        - 노트북(input) 및 터미널 양쪽 호환

    AIContext:
        dartlab.setup() 내부에서 provider별 키 입력에 사용.

    Args:
        envKey: 환경변수 이름 (예: "GEMINI_API_KEY").
        label: 사용자에게 표시할 서비스명 (예: "Google Gemini").
        guide: 키 발급 안내 URL 또는 설명.

    Returns:
        str — 입력된 키 문자열. 건너뛰거나 중단 시 None.

    Requires:
        없음 (대화형 입력 환경 필요).

    Example::

        from dartlab.core.env import promptAndSave
        key = promptAndSave(
            "GEMINI_API_KEY",
            label="Google Gemini (무료)",
            guide="https://aistudio.google.com/apikey",
        )
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
