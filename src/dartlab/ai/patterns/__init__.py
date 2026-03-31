"""분석 템플릿(Template) — 내장 + 사용자 정의 분석 프레임워크.

내장 템플릿: src/dartlab/ai/patterns/*.md (수정 불가)
사용자 템플릿: ~/.dartlab/templates/*.md (자유 추가/수정)

사용법::

    dartlab.ask("삼성전자 분석", template="가치투자")
    dartlab.templates()          # 전체 목록
    dartlab.saveTemplate("my", content="## 내 기준\\n...")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_BUILTIN_DIR = Path(__file__).parent
_USER_DIR = Path.home() / ".dartlab" / "templates"

# ── 캐시 ──
_BUILTIN: dict[str, str] = {}
_USER: dict[str, str] = {}

# 하위호환: 기존 PATTERNS 참조
PATTERNS: dict[str, str] = _BUILTIN


def _load_builtin() -> None:
    """내장 *.md 패턴을 한번만 로드."""
    if _BUILTIN:
        return
    for md_file in _BUILTIN_DIR.glob("*.md"):
        _BUILTIN[md_file.stem] = md_file.read_text(encoding="utf-8")


def _load_user() -> None:
    """사용자 ~/.dartlab/templates/*.md를 로드."""
    _USER.clear()
    if not _USER_DIR.exists():
        return
    for md_file in _USER_DIR.glob("*.md"):
        _USER[md_file.stem] = md_file.read_text(encoding="utf-8")


def _all_templates() -> dict[str, str]:
    """내장 + 사용자 통합. 사용자가 내장과 같은 이름이면 사용자 우선."""
    _load_builtin()
    _load_user()
    merged = dict(_BUILTIN)
    merged.update(_USER)  # 사용자 우선
    return merged


# ── 공개 API ──


def get_template(name: str) -> str | None:
    """템플릿 이름으로 내용 반환. 내장 + 사용자 통합 검색."""
    all_t = _all_templates()
    # 정확 매칭
    if name in all_t:
        return all_t[name]
    # 한글 name → description 매칭 (frontmatter에서)
    for key, content in all_t.items():
        if f"name: {name}" in content[:200]:
            return content
    return None


def get_modules(names: list[str]) -> str | None:
    """여러 모듈을 합쳐서 반환. 먼저 나온 모듈이 우선.

    최대 3개까지. 모듈 간 충돌 시 앞 모듈 우선 지시를 포함.
    """
    texts: list[str] = []
    for name in names[:3]:
        t = get_template(name)
        if t:
            texts.append(t)
    if not texts:
        return None
    if len(texts) == 1:
        return texts[0]
    preamble = (
        "아래 분석 모듈이 활성화되어 있습니다. "
        "모듈 간 지시가 충돌하면 먼저 나온 모듈을 우선하세요.\n"
    )
    return preamble + "\n\n---\n\n".join(texts)


def list_templates() -> list[dict[str, Any]]:
    """사용 가능한 템플릿 목록 [{name, description, source}]."""
    all_t = _all_templates()
    result = []
    for key, content in sorted(all_t.items()):
        desc = ""
        source = "user" if key in _USER else "builtin"
        # frontmatter에서 description 추출
        if content.startswith("---"):
            lines = content.split("\n")
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                elif line.startswith("name:"):
                    pass  # name은 key로 이미 있음
        result.append({"name": key, "description": desc, "source": source})
    return result


def save_template(name: str, *, content: str | None = None, file: str | None = None) -> Path:
    """사용자 템플릿 저장. ~/.dartlab/templates/{name}.md"""
    _USER_DIR.mkdir(parents=True, exist_ok=True)
    path = _USER_DIR / f"{name}.md"

    if file is not None:
        src = Path(file).expanduser()
        text = src.read_text(encoding="utf-8")
    elif content is not None:
        text = content
    else:
        raise ValueError("content 또는 file 중 하나를 지정하세요.")

    path.write_text(text, encoding="utf-8")
    _USER.clear()  # 캐시 무효화
    return path


# ── 하위호환 ──


def get_pattern(name: str) -> str | None:
    """기존 pattern API 하위호환 → get_template으로 위임."""
    return get_template(name)


def list_patterns() -> list[str]:
    """기존 pattern API 하위호환."""
    _load_builtin()
    return sorted(_BUILTIN.keys())
