"""루트 Company facade — canHandle() 체인 기반 자동 라우팅."""

from __future__ import annotations

from dartlab.core.protocols import CompanyProtocol

# ── provider 레지스트리 ──
_PROVIDERS: list[type] = []
_DISCOVERED = False


def _discover() -> None:
    """내장 provider를 priority 순으로 등록. 최초 1회만 실행."""
    global _DISCOVERED  # noqa: PLW0603
    if _DISCOVERED:
        return
    _DISCOVERED = True

    # 내장 provider lazy import
    from dartlab.providers.dart.company import Company as DartCompany
    from dartlab.providers.edgar.company import Company as EdgarCompany

    _PROVIDERS.clear()
    _PROVIDERS.extend([DartCompany, EdgarCompany])

    # entry_points 기반 외부 플러그인 (향후)
    from dartlab.core.plugins import discover as _pluginDiscover
    _pluginDiscover()

    # priority 순 정렬 (낮을수록 먼저)
    _PROVIDERS.sort(key=lambda cls: getattr(cls, "priority", lambda: 99)())


def Company(codeOrName: str) -> CompanyProtocol:
    """종목코드/회사명/ticker → 적절한 Company 인스턴스 생성.

    각 provider의 canHandle()을 priority 순으로 시도하여
    첫 번째 매칭되는 provider로 인스턴스를 생성한다.
    새 국가 추가 시 이 파일 수정 불필요 — provider 패키지만 추가하면 됨.
    """
    _discover()

    normalized = codeOrName.strip()
    if not normalized:
        raise ValueError("종목코드 또는 회사명을 입력해 주세요.")

    # canHandle 체인: priority 순으로 시도
    for cls in _PROVIDERS:
        if hasattr(cls, "canHandle") and cls.canHandle(normalized):
            try:
                return cls(normalized)
            except (ValueError, FileNotFoundError, OSError):
                continue  # 이 provider가 실패하면 다음 시도

    # fallback: DART (한글도 아니고 ticker도 아닌 회사명 검색 시도)
    for cls in _PROVIDERS:
        try:
            return cls(normalized)
        except (ValueError, FileNotFoundError, OSError):
            continue

    raise ValueError(
        f"'{codeOrName}'을(를) 찾을 수 없습니다. dartlab.search('{codeOrName}')로 검색해 보세요."
    )
