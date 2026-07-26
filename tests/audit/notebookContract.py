"""노트북·블로그·Skill OS 코드 셀이 공개 호출 계약만 쓰는지 검사한다.

**호출계약은 엔진명뿐이다.** 엔진 = ``src/dartlab/<엔진>/`` 폴더가 실재하는 것.
폴더 없는 spec (dashboard · data · edgar · mappers · panel · search) 은 설명 문서일 뿐이다.

  1. ``dartlab.{engine}("{axis}", ...)`` (톱레벨 공개 표면 = ``__all__``)
  2. ``Company`` 파사드. providers(dart · edgar) 계열은 ``panel`` · ``select`` · ``filings`` 셋뿐이고,
     거기에 ``trace`` 와 엔진명 메서드(analysis · credit · gather · quant · macro · story · industry)가 붙는다.

**세부 호출계약은 만들지 않는다.** ``c.show()`` · ``c.audit()`` · ``c.governance()`` · ``c.disclosure()`` ·
``c.liveFilings()`` · ``c.view()`` 같은 것은 계약이 아니다. 하위 spec 페이지가 자기 ``capabilityRefs``
에 그것을 등재해도 계약이 아니다. 사용자가 그대로 따라 치면 AttributeError 를 만나거나(``show`` 는
런타임에 아예 없다) 우리가 계약하지 않은 표면을 지게 된다.

계약 정본은 문서가 아니라 코드와 spec 이다. 목록을 여기 하드코딩하지 않고 매번 읽는다.

  * ``Company.{method}`` = ``engines/company/SKILL.md`` 의 ``capabilityRefs`` + 엔진이 자기
    SKILL.md 에 등재한 ``Company.{엔진명}``.
  * 톱레벨 ``dartlab.X`` = ``src/dartlab/__init__.py`` 의 ``__all__``. ``getDefault*`` · 밑줄 접두
    같은 계약 우회 진입점은 ``__all__`` 여부와 무관하게 금지다.

기존 위반은 부채 원장(``_baselines/notebookContract.json``)에 담아 두고, **신규 위반 또는 증가만**
차단한다. 2026-07-10 잔재를 전부 걷어내 원장은 현재 비어 있다.

사용법::

    python tests/audit/notebookContract.py              # 검사 (신규 위반 시 exit 1)
    python tests/audit/notebookContract.py --update     # 부채 원장 재기록
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]
_ENGINE_SPECS = _REPO / "src" / "dartlab" / "skills" / "specs" / "engines"
_ROOT_INIT = _REPO / "src" / "dartlab" / "__init__.py"
_BASELINE = Path(__file__).resolve().parent / "_baselines" / "notebookContract.json"

# Company 인스턴스가 관례적으로 담기는 변수명. Skill OS recipe 는 `comp` 도 쓴다.
_COMPANY_VARS = {"c", "co", "comp", "company"}

# 계약이 아니지만 사실상 값 접근(속성)이라 호출 계약과 별개로 허용하는 최소 집합.
# 메서드 호출(``c.filings()``)은 여기 없으면 위반이다.
_ALLOWED_ATTRS = {"corpName", "market", "code", "name", "stockCode"}

# 절대 금지 패턴. 계약 우회 진입점.
_BANNED_PREFIXES = ("getDefault", "_")


def _engineFolders() -> set[str]:
    """엔진 = ``src/dartlab/<엔진>/`` 폴더가 실재하는 것 (CLAUDE.md 강행규칙).

    폴더 없는 spec (dashboard · data · edgar · mappers · panel · search) 은 설명 문서일 뿐
    엔진이 아니다. 그 spec 의 capabilityRefs 는 계약이 아니다.
    """
    pkg = _REPO / "src" / "dartlab"
    # SKILL.md 실재까지 조건에 넣는다. 예전에는 폴더 존재만 봐서, 엔진 이름이 바뀌며
    # 남은 빈 spec 폴더 하나가 바로 뒤의 읽기에서 FileNotFoundError 로 게이트를 통째로
    # 죽였다. git 이 빈 폴더를 추적하지 않아 CI 에서는 보이지도 않는 로컬 전용 사고였다.
    # spec 이 없는 폴더는 spec 이 아니다.
    return {
        d.name for d in _ENGINE_SPECS.iterdir() if d.is_dir() and (pkg / d.name).is_dir() and (d / "SKILL.md").is_file()
    }


def _loadContract() -> tuple[set[str], set[str]]:
    """계약 집합을 정본에서 읽는다 (dartlab import 없이 정적으로).

    Company 파사드의 계약 메서드 = ``engines/company/SKILL.md`` 의 capabilityRefs + 엔진명 메서드.
    하위 spec 페이지가 자기 capabilityRefs 에 ``Company.audit`` 같은 내부 메서드를 등재해도
    계약이 아니다 (세부 호출계약 금지). ``Company.view`` (dashboard) 처럼 폴더 없는 spec 이
    올린 것도 계약이 아니다.

    Returns
    -------
    tuple[set[str], set[str]]
        (``Company.{method}`` 허용 집합, 톱레벨 ``dartlab.X`` 허용 집합)
    """

    def _companyRefs(spec: Path) -> set[str]:
        parts = spec.read_text(encoding="utf-8").split("---")
        frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
        refs = (frontmatter or {}).get("capabilityRefs") or []
        return {r.split(".", 1)[1] for r in refs if r.startswith("Company.")}

    # 파사드 정본 = engines/company/SKILL.md.
    companyMethods: set[str] = _companyRefs(_ENGINE_SPECS / "company" / "SKILL.md")
    # 엔진이 자기 SKILL.md 에 `Company.{엔진명}` 을 등재했으면 그 하나만 더 인정한다.
    # 폴더명을 통째로 인정하면 `c.scan()` · `c.viz()` 처럼 Company 에 없는 메서드가 새어 나간다.
    for engine in _engineFolders():
        if engine in _companyRefs(_ENGINE_SPECS / engine / "SKILL.md"):
            companyMethods.add(engine)

    # 톱레벨 공개 표면 = `__all__`. dartlab 을 import 하면 회사 한 곳당 수백 MB 라
    # (CLAUDE.md 메모리 가드) 게이트는 소스를 ast 로만 읽는다.
    tree = ast.parse(_ROOT_INIT.read_text(encoding="utf-8"))
    rootPublic: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "__all__" in targets and isinstance(node.value, ast.List):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        rootPublic.add(elt.value)
    if not rootPublic:
        raise RuntimeError("dartlab.__all__ 을 파싱하지 못했다. 게이트가 무의미해진다.")
    return companyMethods, rootPublic


class _Visitor(ast.NodeVisitor):
    """코드 셀 AST 를 훑어 계약 밖 심볼 사용을 모은다."""

    def __init__(self, companyMethods: set[str], rootPublic: set[str]) -> None:
        self.companyMethods = companyMethods
        self.rootPublic = rootPublic
        self.found: list[str] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802 (ast API)
        base = node.value
        if isinstance(base, ast.Name):
            if base.id in _COMPANY_VARS:
                if node.attr not in self.companyMethods and node.attr not in _ALLOWED_ATTRS:
                    self.found.append(f"Company.{node.attr}")
            elif base.id == "dartlab":
                if node.attr.startswith(_BANNED_PREFIXES) or node.attr not in self.rootPublic:
                    self.found.append(f"dartlab.{node.attr}")
        self.generic_visit(node)


def _stripMagics(src: str) -> str:
    """Jupyter 매직(`%pip`, `!cmd`)은 파이썬 문법이 아니라 빈 줄로 지운다."""
    out = []
    for line in src.splitlines():
        stripped = line.lstrip()
        out.append("" if stripped.startswith(("%", "!")) else line)
    return "\n".join(out)


def scanSource(src: str, companyMethods: set[str], rootPublic: set[str]) -> list[str]:
    """코드 문자열 하나에서 계약 위반 심볼 목록을 돌려준다 (문법 오류는 무시)."""
    try:
        tree = ast.parse(_stripMagics(src))
    except SyntaxError:
        return []
    visitor = _Visitor(companyMethods, rootPublic)
    visitor.visit(tree)
    return visitor.found


def _codeCellsOfIpynb(path: Path) -> list[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    cells = []
    for cell in doc.get("cells", []):
        if cell.get("cell_type") == "code":
            cells.append("".join(cell.get("source", [])))
    return cells


_PY_FENCE = re.compile(r"^```(?:python|py)\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def _codeBlocksOfMarkdown(path: Path) -> list[str]:
    """마크다운의 python 코드펜스. dartlab 이야기 본문 셀은 독자가 그대로 실행한다."""
    return [m.group(1) for m in _PY_FENCE.finditer(path.read_text(encoding="utf-8"))]


def _targets() -> list[tuple[Path, list[str]]]:
    """검사 대상 = 사용자가 그대로 실행하는 모든 코드 표면."""
    out: list[tuple[Path, list[str]]] = []
    for p in sorted((_REPO / "notebooks" / "colab").glob("*.ipynb")):
        out.append((p, _codeCellsOfIpynb(p)))
    for p in sorted((_REPO / "notebooks" / "marimo").rglob("*.py")):
        out.append((p, [p.read_text(encoding="utf-8")]))
    for p in sorted((_REPO / "notebooks" / "_scripts").glob("*.py")):
        out.append((p, [p.read_text(encoding="utf-8")]))
    # 블로그 전 카테고리. dartlab 이야기 본문은 브라우저 노트북 셀로 그대로 투영되고,
    # 다른 카테고리의 코드도 독자가 그대로 따라 친다. 발행된 8 편이 실체 없는 메서드
    # (`c.insights` · `c.mdna` · `c.majorHolder` 등)를 싣고 있었다(2026-07-10 실측).
    for p in sorted((_REPO / "blog").rglob("index.md")):
        out.append((p, _codeBlocksOfMarkdown(p)))
    # Skill OS spec 의 python 코드펜스. 외부 도구와 기여자가 이 코드를 그대로 실행한다.
    # 은퇴한 `c.show(...)` 와 실체 없는 `dartlab.flow(...)` 가 여기서 오래 살아 있었다.
    # `.archive/` 도 검사한다. 사용자에게 노출되진 않지만, 죽은 API 를 남겨 두면 다음 사람이
    # 그걸 보고 되살린다. 실제로 그렇게 번졌다.
    specs = _REPO / "src" / "dartlab" / "skills" / "specs"
    for p in sorted(specs.rglob("*.md")):
        out.append((p, _codeBlocksOfMarkdown(p)))
    return out


def collect() -> dict[str, list[str]]:
    """{repo 상대경로: 정렬된 위반 심볼 목록} 전수."""
    companyMethods, rootPublic = _loadContract()
    result: dict[str, list[str]] = {}
    for path, cells in _targets():
        found: set[str] = set()
        for cell in cells:
            found.update(scanSource(cell, companyMethods, rootPublic))
        if found:
            result[path.relative_to(_REPO).as_posix()] = sorted(found)
    return result


def _loadBaseline() -> dict[str, list[str]]:
    if not _BASELINE.is_file():
        return {}
    return json.loads(_BASELINE.read_text(encoding="utf-8"))


def staleCatalogRefs() -> list[str]:
    """``runtime.notebooks`` spec 이 존재하지 않는 노트북을 가리키면 그 이름을 돌려준다.

    공개 문서의 Colab/Molab 링크가 실제 파일과 어긋나면 사용자는 404 를 만난다. 실제로
    ``02_scan`` · ``04_gather`` · ``06_ask`` 를 가리키고 있었고(실파일은 02_gather·03_scan·09_ai)
    아무도 못 잡았다. 부채 원장 없이 즉시 차단한다(문서와 파일은 늘 일치해야 한다).
    """
    spec = _REPO / "src" / "dartlab" / "skills" / "specs" / "runtime" / "notebooks.md"
    if not spec.is_file():
        return []
    named = set(re.findall(r"`(\d{2}_[a-z]+)`", spec.read_text(encoding="utf-8")))
    colab = {p.stem for p in (_REPO / "notebooks" / "colab").glob("*.ipynb")}
    marimo = {p.stem for p in (_REPO / "notebooks" / "marimo").glob("*.py")}
    missing = sorted((named - colab) | (named - marimo))
    unlisted = sorted(colab - named)
    return [f"문서가 가리키는 파일 없음: {n}" for n in missing] + [f"실재하는데 문서 미등재: {n}" for n in unlisted]


def main() -> int:
    parser = argparse.ArgumentParser(description="노트북 공개 계약 게이트")
    parser.add_argument("--update", action="store_true", help="부채 원장 재기록")
    args = parser.parse_args()

    current = collect()

    if args.update:
        _BASELINE.parent.mkdir(parents=True, exist_ok=True)
        _BASELINE.write_text(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        total = sum(len(v) for v in current.values())
        print(f"[notebookContract] 부채 원장 기록: {len(current)} 파일 / {total} 위반")
        return 0

    stale = staleCatalogRefs()
    if stale:
        print("[notebookContract] FAIL. runtime.notebooks 카탈로그가 실제 파일과 어긋난다.", file=sys.stderr)
        for line in stale:
            print(f"  {line}", file=sys.stderr)
        return 1

    baseline = _loadBaseline()
    newViolations: dict[str, list[str]] = {}
    for path, symbols in current.items():
        known = set(baseline.get(path, []))
        fresh = [s for s in symbols if s not in known]
        if fresh:
            newViolations[path] = fresh

    if newViolations:
        print("[notebookContract] FAIL. 공개 계약 밖 심볼이 노트북에 새로 노출됐다.", file=sys.stderr)
        print("계약 정본 = engines/*/SKILL.md 의 capabilityRefs 합집합.", file=sys.stderr)
        for path, symbols in sorted(newViolations.items()):
            print(f"  {path}: {', '.join(symbols)}", file=sys.stderr)
        print("\n계약에 넣을 능력이면 해당 engine SKILL.md capabilityRefs 에 등재하라.", file=sys.stderr)
        print("내부 메서드면 노트북에서 빼라. 새 축 임의 신설은 계약이 아니다.", file=sys.stderr)
        return 1

    known = sum(len(v) for v in baseline.values())
    live = sum(len(v) for v in current.values())
    print(f"[notebookContract] PASS. 신규 위반 0 (부채 원장 {known}, 현재 {live}).")
    if live < known:
        print("부채가 줄었다. `--update` 로 원장을 조여라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
