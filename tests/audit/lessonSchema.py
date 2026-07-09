"""브라우저 노트북 레슨(YAML SSOT)의 스키마·그래프·규모 계약.

레슨 한 편 = ``landing/src/lib/notebook/lessons/content/{track}/{NN}-{slug}.yaml`` 하나.
그 파일이 브라우저 노트북(pyodide 실행)과 파이썬 도구(계약 게이트) 양쪽의 단일 진실이다.

이 검사기가 막는 것.
  * 필수 필드 누락, level/runtime 오타, 트랙 미등록
  * id 중복, 트랙 안 order 중복
  * prerequisites 가 실존하지 않는 레슨을 가리키거나 사이클을 만드는 것
  * 코드 셀 문법 오류
  * 브라우저에서 못 도는 호출을 ``runtime: pyodide`` 로 태깅해 배포하는 것
  * eager 번들 규모 폭주 (임계를 넘으면 색인/본문 분리를 강제한다)

공개 계약(미등재 메서드 노출)은 ``notebookContract.py`` 가 같은 파일들을 따로 훑는다.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]
_LESSONS = _REPO / "landing" / "src" / "lib" / "notebook" / "lessons"
_CONTENT = _LESSONS / "content"
_REGISTRY = _LESSONS / "registry.ts"

_LEVELS = {"기초", "중급", "심화"}
_RUNTIMES = {"pyodide", "local"}

# eager raw glob 로 번들에 실리는 레슨 원본 총량 상한. 넘으면 registry 가 색인(경량 메타)과
# 본문(지연 청크)을 분리해야 한다. 미리 나누지 않고, 실제로 커졌을 때 기계가 알려 준다.
_MAX_EAGER_BYTES = 250 * 1024

# 브라우저(pyodide)에서 실행이 불가능한 호출. 실측 근거는 skill `runtime.pyodide`.
# gather 수집은 스레드를 못 만들고, 아래 scan 축들은 KRX 목록·직원수 프리빌드·total_assets 가 없다.
_LOCAL_ONLY_SCAN_AXES = {"screen", "workforce", "quality", "note"}


def _lessonFiles() -> list[Path]:
    return sorted(_CONTENT.rglob("*.yaml")) if _CONTENT.is_dir() else []


def _tracksFromRegistry() -> set[str]:
    """registry.ts 의 TRACKS 에 등재된 트랙 id 집합 (폴더가 거기 없으면 렌더되지 않는다)."""
    if not _REGISTRY.is_file():
        return set()
    text = _REGISTRY.read_text(encoding="utf-8")
    return set(re.findall(r"\{\s*id:\s*'([a-zA-Z]+)'", text))


def _gatherCallsLocalOnly(tree: ast.AST) -> bool:
    """``c.gather("price")`` 처럼 인자가 있는 수집 호출인가 (인자 없는 카탈로그는 브라우저 OK)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "gather" and node.args:
            return True
        if isinstance(fn, ast.Attribute) and fn.attr == "quant" and node.args:
            return True
    return False


def _scanCallsLocalOnly(tree: ast.AST) -> str | None:
    """브라우저 불가 scan 축을 부르면 그 축 이름을 돌려준다."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "scan" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and first.value in _LOCAL_ONLY_SCAN_AXES:
                return str(first.value)
    return None


def _rel(path: Path) -> str:
    """repo 상대경로. repo 밖(테스트 임시경로 등)이면 파일명만."""
    try:
        return path.relative_to(_REPO).as_posix()
    except ValueError:
        return path.name


def _checkLesson(path: Path, doc: dict, tracks: set[str]) -> list[str]:
    errs: list[str] = []
    rel = _rel(path)

    meta = doc.get("meta") or {}
    for field in ("id", "title", "description", "level", "track", "order", "tags"):
        if field not in meta:
            errs.append(f"{rel}: meta.{field} 누락")
    if meta.get("level") not in _LEVELS and "level" in meta:
        errs.append(f"{rel}: meta.level 은 {sorted(_LEVELS)} 중 하나 (지금 {meta.get('level')!r})")
    if "track" in meta and tracks and meta["track"] not in tracks:
        errs.append(f"{rel}: meta.track {meta['track']!r} 이 registry.ts TRACKS 에 없다")

    intro = doc.get("intro") or {}
    for field in ("goal", "body"):
        if not intro.get(field):
            errs.append(f"{rel}: intro.{field} 누락")

    sections = doc.get("sections") or []
    if not sections:
        errs.append(f"{rel}: sections 가 비었다")
    seenSection: set[str] = set()
    for i, sec in enumerate(sections):
        tag = f"{rel}: sections[{i}]"
        sid = sec.get("id")
        if not sid:
            errs.append(f"{tag}.id 누락")
        elif sid in seenSection:
            errs.append(f"{tag}.id {sid!r} 중복 (진도 오버레이가 셀을 이 id 로 매칭한다)")
        else:
            seenSection.add(sid)
        if not sec.get("code") and not sec.get("body"):
            errs.append(f"{tag}: code 도 body 도 없다")

        runtime = sec.get("runtime", "pyodide")
        if runtime not in _RUNTIMES:
            errs.append(f"{tag}.runtime 은 {sorted(_RUNTIMES)} 중 하나 (지금 {runtime!r})")

        code = sec.get("code")
        if not code:
            continue
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            errs.append(f"{tag}: 코드 문법 오류 {exc}")
            continue

        # 경계 정합: 브라우저에서 못 도는 호출은 local 이거나 expectError 여야 한다.
        tolerated = runtime == "local" or sec.get("expectError")
        if not tolerated:
            if _gatherCallsLocalOnly(tree):
                errs.append(
                    f"{tag}: 수집 호출(gather/quant 인자 있음)은 브라우저에서 못 돈다. runtime: local 또는 expectError: true"
                )
            axis = _scanCallsLocalOnly(tree)
            if axis:
                errs.append(
                    f"{tag}: scan({axis!r}) 는 브라우저 불가(runtime.pyodide 실측). runtime: local 또는 expectError: true"
                )
    return errs


def validate() -> list[str]:
    files = _lessonFiles()
    if not files:
        return ["레슨이 하나도 없다. content/ 경로를 확인하라."]

    tracks = _tracksFromRegistry()
    errs: list[str] = []
    docs: dict[str, dict] = {}
    orders: dict[tuple[str, int], str] = {}
    totalBytes = 0

    for path in files:
        totalBytes += path.stat().st_size
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errs.append(f"{_rel(path)}: YAML 파싱 실패 {exc}")
            continue
        errs.extend(_checkLesson(path, doc, tracks))

        meta = doc.get("meta") or {}
        lid = meta.get("id")
        if lid:
            if lid in docs:
                errs.append(f"레슨 id {lid!r} 중복")
            docs[lid] = doc
            key = (meta.get("track"), meta.get("order"))
            if key in orders:
                errs.append(f"트랙 {key[0]!r} 안에서 order {key[1]} 중복: {lid} vs {orders[key]}")
            orders[key] = lid

    # prerequisites 무결성 + 사이클
    for lid, doc in docs.items():
        for prereq in doc["meta"].get("prerequisites") or []:
            if prereq not in docs:
                errs.append(f"{lid}: prerequisites 가 없는 레슨 {prereq!r} 을 가리킨다")

    cycle = _findCycle(
        {lid: [p for p in (d["meta"].get("prerequisites") or []) if p in docs] for lid, d in docs.items()}
    )
    if cycle:
        errs.append(f"prerequisites 사이클: {' -> '.join(cycle)}")

    if totalBytes > _MAX_EAGER_BYTES:
        errs.append(
            f"레슨 원본 총 {totalBytes / 1024:.0f}KB 가 임계 {_MAX_EAGER_BYTES / 1024:.0f}KB 를 넘었다. "
            "registry.ts 를 색인(경량 메타 eager) + 본문(지연 청크)으로 분리하라."
        )
    return errs


def _findCycle(graph: dict[str, list[str]]) -> list[str] | None:
    """DFS 위상 정렬로 사이클 하나를 찾아 경로로 돌려준다."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(graph, WHITE)
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GRAY
        stack.append(node)
        for nxt in graph.get(node, []):
            if color.get(nxt) == GRAY:
                return stack[stack.index(nxt) :] + [nxt]
            if color.get(nxt) == WHITE:
                found = visit(nxt)
                if found:
                    return found
        color[node] = BLACK
        stack.pop()
        return None

    for node in graph:
        if color[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def main() -> int:
    errs = validate()
    if errs:
        print("[lessonSchema] FAIL", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    files = _lessonFiles()
    size = sum(p.stat().st_size for p in files)
    print(
        f"[lessonSchema] PASS. 레슨 {len(files)} 편 / 원본 {size / 1024:.0f}KB (임계 {_MAX_EAGER_BYTES / 1024:.0f}KB)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
