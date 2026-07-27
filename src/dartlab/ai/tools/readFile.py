"""Read tool — 안전 경로 안의 텍스트 파일을 읽어 docRef 를 만든다.

사용자 artifact / project 내 보고서 / skill body / blog md 같은 파일을 LLM 이
직접 읽고 인용할 때 사용한다. dartlab repo 와 사용자 홈의 artifacts 디렉토리만 허용.
"""

from __future__ import annotations

from pathlib import Path

from dartlab.ai.contracts import Ref

from .types import ToolResult

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HOME = Path.home()
_SAFE_ROOTS: tuple[Path, ...] = (
    _REPO_ROOT,
    _HOME / "dartlab-artifacts",
    _HOME / ".dartlab",
)
_MAX_BYTES = 200_000  # 200 KB
_MAX_LINES = 4000

# 안전 경로 안에 있어도 절대 읽지 않는 것들. repo 루트와 `~/.dartlab` 이 허용 경로라
# 예전에는 `.env` 와 `secrets.json` 이 그대로 읽혔다. 열일곱 개 서비스 자격증명이 한 번의
# 도구 호출로 나왔다. 도구가 코드 실행을 이미 준다는 것은 이 구멍을 정당화하지 않는다.
# 외부 본문으로 도구 선택을 흔들 수 있는 통로가 같은 도구 묶음 안에 있기 때문이다.
_DENIED_NAMES = frozenset({"secrets.json", "credentials.json", "id_rsa", "id_ed25519", ".npmrc", ".netrc"})
_DENIED_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
_DENIED_PARTS = frozenset({".git", ".ssh", ".aws", "node_modules"})


def _isDeniedPath(path: Path) -> bool:
    """자격증명 계열 파일인지 판정한다. 안전 경로 판정과 별개로 항상 먼저 본다."""
    name = path.name
    if name in _DENIED_NAMES or name == ".env" or name.startswith(".env."):
        return True
    if name.lower().endswith(_DENIED_SUFFIXES):
        return True
    return bool(_DENIED_PARTS.intersection(path.parts))


def readFile(target: str, *, startLine: int | None = None, endLine: int | None = None) -> ToolResult:
    """안전 경로의 텍스트 파일을 읽는다.

    Args:
        target: 절대 경로 또는 _REPO_ROOT 기준 상대 경로 (예: "blog/foo.md").
        startLine: 1-based 시작 라인 (선택).
        endLine: 1-based 끝 라인 (포함, 선택).
    """
    if not target or not isinstance(target, str):
        return ToolResult(False, "target 이 비어 있습니다", error="invalid_target")

    raw = Path(target.strip())
    candidate = raw if raw.is_absolute() else _REPO_ROOT / raw
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        return ToolResult(False, f"경로 해석 실패: {exc}", error="resolve_failed")

    if _isDeniedPath(resolved):
        return ToolResult(
            False,
            f"자격증명 계열 파일은 읽지 않는다: {resolved.name}",
            error="denied_credential_path",
        )

    if not _isUnderSafeRoot(resolved):
        return ToolResult(
            False,
            f"안전 경로 외 접근 차단: {resolved}",
            error="path_outside_safe_root",
        )

    if not resolved.exists():
        return ToolResult(False, f"파일 없음: {resolved}", error="not_found")
    if not resolved.is_file():
        return ToolResult(False, f"파일이 아님: {resolved}", error="not_a_file")

    size = resolved.stat().st_size
    if size > _MAX_BYTES * 5:
        return ToolResult(
            False,
            f"파일이 너무 큼 ({size:,} bytes). 1 MB 미만만 읽음.",
            error="file_too_large",
        )

    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ToolResult(False, f"읽기 실패: {exc}", error="read_failed")

    lines = text.splitlines()
    total_lines = len(lines)

    if startLine is not None or endLine is not None:
        s = max(1, int(startLine or 1)) - 1
        e = int(endLine) if endLine is not None else total_lines
        e = min(total_lines, max(s + 1, e))
        sliced = lines[s:e]
        slice_label = f" L{s + 1}-L{e}"
    else:
        sliced = lines[:_MAX_LINES]
        slice_label = f" (head {_MAX_LINES})" if total_lines > _MAX_LINES else ""

    body = "\n".join(sliced)
    if len(body) > _MAX_BYTES:
        body = body[:_MAX_BYTES]
        slice_label += " [truncated by bytes]"

    rel = _tryRelative(resolved)
    refId = f"doc:{rel}"
    ref = Ref(
        id=refId,
        kind="docRef",
        title=resolved.name,
        source=str(resolved),
        payload={
            "path": str(resolved),
            "relativePath": rel,
            "totalLines": total_lines,
            "body": body,
            "startLine": (startLine or 1) if (startLine or endLine) else 1,
            "endLine": (endLine if endLine is not None else min(_MAX_LINES, total_lines)),
        },
    )
    summary = f"{rel}{slice_label} ({total_lines} lines)"
    return ToolResult(True, summary, refs=[ref], data={"path": str(resolved), "body": body})


def _isUnderSafeRoot(path: Path) -> bool:
    for root in _SAFE_ROOTS:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _tryRelative(path: Path) -> str:
    for root in _SAFE_ROOTS:
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)
