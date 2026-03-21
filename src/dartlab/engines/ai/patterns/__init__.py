"""분석 패턴(Pattern) — 사전 정의된 분석 프레임워크.

fabric 스타일 패턴 시스템.
`dartlab.ask("삼성전자 분석", pattern="financial")` → 전문적 분석 프레임워크 자동 적용.
"""

from __future__ import annotations

from pathlib import Path

_PATTERN_DIR = Path(__file__).parent

# ── 내장 패턴 ──
PATTERNS: dict[str, str] = {}


def _load_patterns() -> None:
    """*.md 패턴 파일을 한번만 로드."""
    if PATTERNS:
        return
    for md_file in _PATTERN_DIR.glob("*.md"):
        PATTERNS[md_file.stem] = md_file.read_text(encoding="utf-8")


def get_pattern(name: str) -> str | None:
    """패턴 이름으로 시스템 프롬프트 조각 반환."""
    _load_patterns()
    return PATTERNS.get(name)


def list_patterns() -> list[str]:
    """사용 가능한 패턴 목록."""
    _load_patterns()
    return sorted(PATTERNS.keys())
