"""gather 데이터 공급자 자격증명 진입점 — env·토큰 관리·안내 단일 facade.

SSOT 본체는 `core/providers/dataCredentials.py` (L0, cross-cutting). 본 모듈은
gather 사용자가 한 곳에서 키를 해석·설정·점검하도록 thin re-export + doctor CLI.

세팅 (둘 중 하나):
    1. .env 에 `DATA_GO_KR_KEY=...` (템플릿: `dartlab.gather.writeEnvExample()`).
    2. `dartlab.gather.setCredential("dataGoKr", "<키>")` — 암호화 저장, .env 불필요.

점검:
    >>> from dartlab import gather
    >>> print(gather.formatStatus())          # 사람용 상태표
    >>> gather.credentialStatus()             # 구조화 상태 리스트

소스 구현 측:
    >>> from dartlab.gather.credentials import resolveKey
    >>> key = resolveKey("dataGoKr", apiKey)  # 명시 → env → SecretStore → 안내에러
"""

from __future__ import annotations

from pathlib import Path

from dartlab.core.providers.dataCredentials import (
    CredentialError,
    CredentialStatus,
    CredentialWriteError,
    DataProviderSpec,
    allSpecs,
    credentialStatus,
    envTemplate,
    formatStatus,
    getKey,
    getSpec,
    isConfigured,
    missingKeyMessage,
    resolveKey,
    setCredential,
)


def writeEnvExample(path: str | Path = ".env.example") -> Path:
    """레지스트리 기반 `.env.example` 파일 생성/갱신.

    Capabilities: dataCredentials.envTemplate() 산출을 파일로 기록 — 공급자별
        용도·발급 URL·활용신청 주석 + ``KEY=`` 빈 줄.
    AIContext: 운영자/외부 사용자의 첫 세팅 진입 — 복사 후 값 채우기.
    Guide: 레지스트리 SSOT 파생이라 공급자 추가 시 자동 반영. 덮어쓰기.
    When: 새 공급자 등록 후 .env.example 동기화 / 온보딩 문서 갱신 시.
    How: envTemplate() → Path.write_text(utf-8).

    Args:
        path: 출력 경로. 기본 repo 루트 ``.env.example``.

    Returns:
        Path — 작성된 파일 경로.

    Raises:
        OSError: 파일 쓰기 실패.

    Requires:
        출력 경로 디렉토리 쓰기 권한.

    Example:
        >>> writeEnvExample("/tmp/.env.example")  # doctest: +SKIP

    SeeAlso:
        dataCredentials.envTemplate : 본문 생성 SSOT.
        formatStatus : 현재 설정 상태 doctor.
    """
    out = Path(path)
    out.write_text(envTemplate(), encoding="utf-8")
    return out


def _main() -> int:
    """`python -m dartlab.gather.credentials` — 자격증명 상태 doctor."""
    print(formatStatus())
    return 0


__all__ = [
    "CredentialError",
    "CredentialStatus",
    "CredentialWriteError",
    "DataProviderSpec",
    "allSpecs",
    "credentialStatus",
    "envTemplate",
    "formatStatus",
    "getKey",
    "getSpec",
    "isConfigured",
    "missingKeyMessage",
    "resolveKey",
    "setCredential",
    "writeEnvExample",
]


if __name__ == "__main__":
    raise SystemExit(_main())
