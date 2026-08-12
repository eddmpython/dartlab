"""AST 기반 DartLab Guard Index 생성."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

LAYER_OF: dict[str, float] = {
    "core": 0.0,
    "config": 0.0,
    "gather": 1.0,
    "providers": 1.0,
    "scan": 1.5,
    "frame": 1.5,
    "synth": 1.5,
    "reference": 1.5,
    "analysis": 2.0,
    "macro": 2.0,
    "quant": 2.0,
    "industry": 2.0,
    "credit": 2.0,
    "data": 2.5,
    "dataHub": 2.5,
    "story": 3.0,
    "simulate": 3.0,
    "ai": 4.0,
    "mcp": 4.0,
    "company": 4.0,
    "composition": 4.0,
    "viz": 4.0,
    "cli": 4.0,
    "server": 4.0,
    "channel": 4.0,
    "pipeline": 4.0,
    "__main__": 4.0,
    "_aiEntries": 4.0,
    "_listingDispatch": 4.0,
    "api": 4.0,
    "help": 4.0,
    "plugins": 4.0,
    "productOutcome": 4.0,
    "skills": 4.0,
    "webapi": 4.0,
}

ROOT_FACADE = "__root__"
DYNAMIC_UNKNOWN = "<dynamic-unresolved>"
STATIC_IMPORT = "static"
DYNAMIC_IMPORT = "dynamic"
DISCOVERY_IMPORT = "discovery"
CALLER_OWNED_IMPORT = "caller-owned"
EAGER_PHASE = "eager"
LAZY_PHASE = "lazy"
TYPE_ONLY_PHASE = "type-only"


class GuardIndexError(ValueError):
    """source를 읽거나 parse하지 못해 import graph를 신뢰할 수 없음."""


@dataclass(frozen=True)
class ImportRecord:
    """AST import 1건."""

    module: str
    topPackage: str | None
    line: int
    isTopLevel: bool
    kind: str
    phase: str

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict."""
        return asdict(self)


@dataclass(frozen=True)
class ModuleRecord:
    """파일 1개의 Guard Index record."""

    path: str
    module: str
    topPackage: str
    layer: float | None
    imports: tuple[ImportRecord, ...]

    @property
    def importModules(self) -> list[str]:
        """전체 dartlab import module 목록."""
        return sorted({item.module for item in self.imports if item.topPackage is not None})

    @property
    def topLevelImports(self) -> list[str]:
        """전체 top-level package import 목록."""
        return sorted({item.topPackage for item in self.imports if item.topPackage})

    def toDict(self) -> dict[str, Any]:
        """Guard Index schema module dict."""
        return {
            "path": self.path,
            "module": self.module,
            "topPackage": self.topPackage,
            "layer": self.layer,
            "imports": self.importModules,
            "topLevelImports": self.topLevelImports,
            "dynamicImports": [item.toDict() for item in self.imports if item.kind != STATIC_IMPORT],
        }


def buildIndex(repoRoot: Path) -> list[ModuleRecord]:
    """src/dartlab 전수 AST index의 호출자별 list 사본을 반환한다."""
    return list(_buildIndex(repoRoot.resolve()))


@lru_cache(maxsize=4)
def _buildIndex(repoRoot: Path) -> tuple[ModuleRecord, ...]:
    """같은 process의 중복 architecture gate가 전수 parse를 반복하지 않게 한다."""
    srcRoot = repoRoot / "src" / "dartlab"
    if not srcRoot.exists():
        raise FileNotFoundError(f"dartlab source root not found: {srcRoot}")
    pyFiles = sorted(p for p in srcRoot.rglob("*.py") if "__pycache__" not in p.parts)
    if not pyFiles:
        raise FileNotFoundError(f"dartlab source root has no Python files: {srcRoot}")
    records: list[ModuleRecord] = []
    for pyFile in pyFiles:
        record = indexFile(repoRoot, srcRoot, pyFile)
        if record is not None:
            records.append(record)
    return tuple(records)


def indexFile(repoRoot: Path, srcRoot: Path, pyFile: Path) -> ModuleRecord | None:
    """단일 파일 AST import record 생성."""
    module = moduleNameFor(srcRoot, pyFile)
    if module is None:
        return None
    topPackage = ROOT_FACADE if module == "dartlab" else module.split(".")[1]
    try:
        source = pyFile.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(pyFile))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        raise GuardIndexError(f"source index 실패: {pyFile}: {type(exc).__name__}: {exc}") from exc
    imports = tuple(extractImports(tree))
    relPath = pyFile.relative_to(repoRoot).as_posix()
    return ModuleRecord(
        path=relPath,
        module=module,
        topPackage=topPackage,
        layer=4.0 if topPackage == ROOT_FACADE else LAYER_OF.get(topPackage),
        imports=imports,
    )


def moduleNameFor(srcRoot: Path, pyFile: Path) -> str | None:
    """src/dartlab/x/y.py -> dartlab.x.y."""
    try:
        relPath = pyFile.relative_to(srcRoot).with_suffix("")
    except ValueError:
        return None
    parts = list(relPath.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["dartlab", *parts])


def extractImports(tree: ast.Module) -> list[ImportRecord]:
    """AST에서 정적·동적 ``dartlab.*`` import를 한 번에 추출한다.

    ``importlib.import_module``/``__import__`` 리터럴과
    과거 ``discoverOnce(__name__, _KNOWN_*_MODULES)`` 상수 목록을 같은 record로 만든다.
    해석할 수 없는 동적 대상도 버리지 않고 ``DYNAMIC_UNKNOWN``으로 남긴다.
    """
    records: list[ImportRecord] = []
    topLevelIds = topLevelNodeIds(tree)
    typeOnlyIds = typeCheckingNodeIds(tree)
    for node in ast.walk(tree):
        for module in importNames(node):
            topPackage = topPackageFor(module)
            if topPackage is None:
                continue
            records.append(
                ImportRecord(
                    module=module,
                    topPackage=topPackage,
                    line=getattr(node, "lineno", 0),
                    isTopLevel=id(node) in topLevelIds,
                    kind=STATIC_IMPORT,
                    phase=importPhase(node, topLevelIds, typeOnlyIds),
                )
            )
    records.extend(
        extractDynamicImports(
            tree,
            topLevelIds=topLevelIds,
            typeOnlyIds=typeOnlyIds,
        )
    )
    return records


def importNames(node: ast.AST) -> list[str]:
    """Import/ImportFrom 노드에서 import module name을 반환한다."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        if node.module is None or node.level != 0:
            return []
        return [node.module]
    return []


def extractDynamicImports(
    tree: ast.Module,
    *,
    topLevelIds: set[int] | None = None,
    typeOnlyIds: set[int] | None = None,
) -> list[ImportRecord]:
    """상수로 확정 가능한 동적 import와 미해결 호출을 추출한다."""
    if topLevelIds is None:
        topLevelIds = topLevelNodeIds(tree)
    if typeOnlyIds is None:
        typeOnlyIds = typeCheckingNodeIds(tree)
    importlibAliases, importModuleAliases, discoverAliases, callerImportAliases = importAliases(tree)
    constants = moduleStringConstants(tree)
    callerOwnedIds = callerOwnedNodeIds(tree)
    records = declarativeBootstrapRecords(tree, constants)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callName = dottedName(node.func)
        if callName in discoverAliases:
            values = expressionStrings(node.args[1], constants) if len(node.args) >= 2 else ()
            records.extend(
                dynamicRecords(
                    values or (DYNAMIC_UNKNOWN,),
                    node=node,
                    kind=DISCOVERY_IMPORT,
                    topLevelIds=topLevelIds,
                    typeOnlyIds=typeOnlyIds,
                )
            )
            continue
        if callName in callerImportAliases:
            values = expressionStrings(node.args[0], constants) if node.args else ()
            records.extend(
                dynamicRecords(
                    values or (DYNAMIC_UNKNOWN,),
                    node=node,
                    kind=CALLER_OWNED_IMPORT,
                    topLevelIds=topLevelIds,
                    typeOnlyIds=typeOnlyIds,
                )
            )
            continue
        if not isDynamicImportCall(callName, importlibAliases, importModuleAliases):
            continue
        values = expressionStrings(node.args[0], constants) if node.args else ()
        records.extend(
            dynamicRecords(
                values or (DYNAMIC_UNKNOWN,),
                node=node,
                kind=CALLER_OWNED_IMPORT if id(node) in callerOwnedIds else DYNAMIC_IMPORT,
                topLevelIds=topLevelIds,
                typeOnlyIds=typeOnlyIds,
            )
        )
    return records


def declarativeBootstrapRecords(
    tree: ast.Module,
    constants: dict[str, tuple[str, ...]],
) -> list[ImportRecord]:
    """composition의 ``_MODULE_BOOTSTRAPS`` 선언 표를 concrete edge로 만든다."""
    records: list[ImportRecord] = []
    for node in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        if not (isinstance(target, ast.Name) and target.id == "_MODULE_BOOTSTRAPS" and isinstance(value, ast.Dict)):
            continue
        for item in value.values:
            for module in expressionStrings(item, constants):
                topPackage = topPackageFor(module)
                if topPackage is None:
                    continue
                records.append(
                    ImportRecord(
                        module=module,
                        topPackage=topPackage,
                        line=getattr(item, "lineno", getattr(node, "lineno", 0)),
                        isTopLevel=False,
                        kind=DISCOVERY_IMPORT,
                        phase=LAZY_PHASE,
                    )
                )
    return records


def importAliases(tree: ast.Module) -> tuple[set[str], set[str], set[str], set[str]]:
    """현재 모듈에서 실제 importlib/discoverOnce 호출 alias를 수집한다."""
    importlibAliases: set[str] = set()
    importModuleAliases: set[str] = set()
    discoverAliases: set[str] = set()
    callerImportAliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlibAliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        importModuleAliases.add(alias.asname or alias.name)
            elif node.module == "dartlab.core.pluginDiscovery":
                for alias in node.names:
                    if alias.name == "discoverOnce":
                        discoverAliases.add(alias.asname or alias.name)
                    elif alias.name == "importCallerModule":
                        callerImportAliases.add(alias.asname or alias.name)
    return importlibAliases, importModuleAliases, discoverAliases, callerImportAliases


def callerOwnedNodeIds(tree: ast.Module) -> set[int]:
    """``@callerOwnedDynamicImport`` 함수 안 노드를 명시적 generic 경계로 표시한다."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        decorators = {dottedName(item) for item in node.decorator_list}
        if "callerOwnedDynamicImport" in decorators:
            found.update(id(item) for item in ast.walk(node))
    return found


def moduleStringConstants(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    """모듈 직속 상수 중 문자열 또는 문자열 컨테이너만 해석한다."""
    constants: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        if isinstance(target, ast.Name) and value is not None:
            resolved = expressionStrings(value, constants)
            if resolved:
                constants[target.id] = resolved
    return constants


def expressionStrings(
    node: ast.AST,
    constants: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """간단한 상수 식을 문자열 tuple로 평가한다."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    if isinstance(node, ast.Name):
        return constants.get(node.id, ())
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        values: list[str] = []
        for item in node.elts:
            resolved = expressionStrings(item, constants)
            if not resolved:
                return ()
            values.extend(resolved)
        return tuple(values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = expressionStrings(node.left, constants)
        right = expressionStrings(node.right, constants)
        if len(left) == 1 and len(right) == 1:
            return (left[0] + right[0],)
    return ()


def dottedName(node: ast.AST) -> str | None:
    """Name/Attribute 호출자를 점 경로로 변환한다."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dottedName(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def isDynamicImportCall(
    callName: str | None,
    importlibAliases: set[str],
    importModuleAliases: set[str],
) -> bool:
    """호출자가 importlib API 또는 builtin ``__import__``인지 판정한다."""
    if callName is None:
        return False
    if callName == "__import__" or callName in importModuleAliases:
        return True
    return any(callName == f"{alias}.import_module" for alias in importlibAliases)


def dynamicRecords(
    modules: tuple[str, ...],
    *,
    node: ast.Call,
    kind: str,
    topLevelIds: set[int],
    typeOnlyIds: set[int],
) -> list[ImportRecord]:
    """동적 대상 문자열을 표준 ImportRecord로 변환한다."""
    records: list[ImportRecord] = []
    for module in modules:
        topPackage = topPackageFor(module)
        if topPackage is None and module != DYNAMIC_UNKNOWN:
            continue
        records.append(
            ImportRecord(
                module=module,
                topPackage=topPackage,
                line=node.lineno,
                isTopLevel=id(node) in topLevelIds,
                kind=kind,
                phase=importPhase(node, topLevelIds, typeOnlyIds),
            )
        )
    return records


def topPackageFor(module: str) -> str | None:
    """dartlab.x.y -> x."""
    parts = module.split(".")
    if not parts or parts[0] != "dartlab":
        return None
    if len(parts) == 1:
        return ROOT_FACADE
    return parts[1]


def isTopLevelNode(tree: ast.Module, target: ast.AST) -> bool:
    """모듈 직속 import인지 확인한다. TYPE_CHECKING 블록은 top-level로 보지 않는다."""
    return id(target) in topLevelNodeIds(tree)


def topLevelNodeIds(tree: ast.Module) -> set[int]:
    """module import 때 실행되는 노드 id.

    함수·lambda 본문은 지연 실행이지만 decorator와 default 식은 즉시 실행된다.
    class 본문도 정의 시점에 실행된다. ``TYPE_CHECKING`` 본문만 별도 type-only
    phase로 분리한다.
    """
    found: set[int] = set()

    def visit(node: ast.AST) -> None:
        found.add(id(node))
        if isinstance(node, ast.If) and isTypeCheckingGuard(node.test):
            visit(node.test)
            for item in node.orelse:
                visit(item)
            return
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                visit(decorator)
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    visit(default)
            return
        if isinstance(node, ast.Lambda):
            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    visit(default)
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for item in tree.body:
        visit(item)
    return found


def typeCheckingNodeIds(tree: ast.Module) -> set[int]:
    """TYPE_CHECKING 분기 안 source-coupling node id."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isTypeCheckingGuard(node.test):
            for statement in node.body:
                found.update(id(item) for item in ast.walk(statement))
    return found


def importPhase(node: ast.AST, topLevelIds: set[int], typeOnlyIds: set[int]) -> str:
    """import record의 eager/lazy/type-only 실행 phase."""
    if id(node) in typeOnlyIds:
        return TYPE_ONLY_PHASE
    if id(node) in topLevelIds:
        return EAGER_PHASE
    return LAZY_PHASE


def isTypeCheckingGuard(test: ast.expr) -> bool:
    """if TYPE_CHECKING / typing.TYPE_CHECKING 분기."""
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def reverseImportClosure(records: list[ModuleRecord], changedModules: set[str]) -> set[str]:
    """변경 module을 import하는 역방향 의존 closure."""
    seen = set(changedModules)
    stack = list(changedModules)
    while stack:
        current = stack.pop()
        for record in records:
            if record.module in seen:
                continue
            if any(_modulePathsOverlap(importName, current) for importName in record.importModules):
                seen.add(record.module)
                stack.append(record.module)
    return seen


def selectImpactedTestTargets(
    repoRoot: Path,
    changedFiles: list[str],
    *,
    records: list[ModuleRecord] | None = None,
) -> dict[str, Any]:
    """변경 파일에서 push용 pytest target을 보수적으로 선택한다.

    Regression for #103. src 변경은 Guard Index 역방향 closure와 테스트의 직접 import를
    함께 사용한다. 공용 fixture, 실행기, 공개 root facade처럼 그래프가 충분히 설명하지
    못하는 변경은 전수 실행으로 올리고, 동적·데이터 결합의 나머지는 nightly 전수가 맡는다.
    """
    normalized = sorted(
        {normalizedPath.removeprefix("./") for item in changedFiles if (normalizedPath := item.replace("\\", "/"))}
    )
    fullTriggers = {
        "pyproject.toml",
        "uv.lock",
        "tests/conftest.py",
        "tests/run.py",
        "src/dartlab/__init__.py",
        "src/dartlab/_aiEntries.py",
        "src/dartlab/_listingDispatch.py",
    }
    if any(path in fullTriggers or path.startswith("tests/fixtures/") for path in normalized):
        return {
            "mode": "full",
            "targets": ["tests/"],
            "changedFiles": normalized,
            "changedModules": [],
            "impactedModules": [],
            "reason": "sharedContractChange",
        }

    targets: set[str] = set()
    changedModules = {_sourceModuleForPath(path) for path in normalized}
    changedModules.discard(None)
    impactedModules: set[str] = set()
    if changedModules:
        indexRecords = records if records is not None else buildIndex(repoRoot)
        impactedModules = reverseImportClosure(indexRecords, set(changedModules))
        topPackages = {
            module.split(".")[1]
            for module in impactedModules
            if module.startswith("dartlab.") and len(module.split(".")) > 1
        }
        for package in sorted(topPackages):
            mirror = repoRoot / "tests" / package
            if mirror.is_dir():
                targets.add(mirror.relative_to(repoRoot).as_posix())
        targets.update(_testFilesImportingModules(repoRoot, impactedModules))

    for path in normalized:
        candidate = repoRoot / path
        if path.startswith("tests/") and path.endswith(".py") and candidate.is_file():
            targets.add(path)
        elif path.startswith(".github/scripts/search/"):
            _addExistingTarget(repoRoot, targets, "tests/search")
        elif path.startswith(".github/scripts/ops/"):
            _addExistingTarget(repoRoot, targets, "tests/pipeline")
        elif path.startswith(".github/scripts/sync/"):
            for testDir in ("tests/sync", "tests/pipeline", "tests/gather"):
                _addExistingTarget(repoRoot, targets, testDir)
        elif path.startswith(".github/workflows/"):
            _addExistingTarget(repoRoot, targets, "tests/pipeline")
            if path.startswith(".github/workflows/ci-"):
                _addExistingTarget(repoRoot, targets, "tests/audit/test_runEntrypoint.py")

    if changedModules and not targets:
        return {
            "mode": "full",
            "targets": ["tests/"],
            "changedFiles": normalized,
            "changedModules": sorted(changedModules),
            "impactedModules": sorted(impactedModules),
            "reason": "unmappedSourceChange",
        }
    return {
        "mode": "selected" if targets else "skip",
        "targets": sorted(targets),
        "changedFiles": normalized,
        "changedModules": sorted(changedModules),
        "impactedModules": sorted(impactedModules),
        "reason": "guardIndexReverseClosure" if targets else "noPythonTestImpact",
    }


def _sourceModuleForPath(path: str) -> str | None:
    prefix = "src/dartlab/"
    if not path.startswith(prefix) or not path.endswith(".py"):
        return None
    rel = path[len("src/") : -3]
    parts = rel.split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _modulePathsOverlap(left: str, right: str) -> bool:
    """package import와 구체 module 변경을 양방향 prefix로 연결한다."""
    if DYNAMIC_UNKNOWN in {left, right}:
        return False
    return left == right or left.startswith(right + ".") or right.startswith(left + ".")


def _testFilesImportingModules(repoRoot: Path, impactedModules: set[str]) -> set[str]:
    targets: set[str] = set()
    testsRoot = repoRoot / "tests"
    for path in testsRoot.rglob("*.py"):
        if any(part in {"__pycache__", "_attempts", "realData"} for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        imports = {item.module for item in extractImports(tree) if item.module != "dartlab"}
        if any(_modulePathsOverlap(importName, impacted) for importName in imports for impacted in impactedModules):
            targets.add(path.relative_to(repoRoot).as_posix())
    return targets


def _addExistingTarget(repoRoot: Path, targets: set[str], relPath: str) -> None:
    if (repoRoot / relPath).exists():
        targets.add(relPath)
