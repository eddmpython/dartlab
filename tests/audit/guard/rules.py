"""Guard Index rule 평가."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from guard.indexer import LAYER_OF, ROOT_FACADE, ModuleRecord

SINK_HELPERS = {"viz", "cli", "server", "channel"}
STRICT_L0_L15 = {"core", "gather", "providers", "scan", "frame", "synth", "reference"}
L1_PEERS = {"gather", "providers"}
L15_PEERS = {"scan", "frame", "synth", "reference"}
L2_PEERS = {"analysis", "macro", "quant", "industry", "credit"}
PROVIDER_COMPANY_FILES = {
    "src/dartlab/providers/dart/company.py": "dart",
    "src/dartlab/providers/edgar/company.py": "edgar",
}
FROZEN_PROVIDER_COMPANY_SURFACE = {
    "dart": {
        "analysis",
        "ask",
        "audit",
        "calendar",
        "canHandle",
        "capital",
        "causalWeights",
        "cleanupCache",
        "codeName",
        "credit",
        "currency",
        "debt",
        "diff",
        "disclosure",
        "executivePay",
        "facts",
        "filings",
        "fiscalYearEnd",
        "flow",
        "gather",
        "governance",
        "industry",
        "index",
        "keywordTrend",
        "listing",
        "liveFilings",
        "macro",
        "market",
        "memorySnapshot",
        "narrativeDiff",
        "network",
        "news",
        "notesDetail",
        "panel",
        "priority",
        "quant",
        "rank",
        "rawFinance",
        "rawReport",
        "readFiling",
        "relatedPartyTx",
        "report",
        "reportModel",
        "resolve",
        "search",
        "sector",
        "sectorParams",
        "select",
        "simulate",
        "sources",
        "status",
        "story",
        "storyTree",
        "table",
        "topicSummaries",
        "topics",
        "trace",
        "update",
        "validateStory",
        "valuationImpact",
        "view",
        "watch",
        "workforce",
    },
    "edgar": {
        "analysis",
        "ask",
        "audit",
        "calendar",
        "canHandle",
        "capital",
        "causalWeights",
        "cleanupCache",
        "contextSlices",
        "credit",
        "currency",
        "debt",
        "diff",
        "disclosure",
        "facts",
        "filings",
        "fiscalYearEnd",
        "gather",
        "governance",
        "index",
        "keywordTrend",
        "listing",
        "liveFilings",
        "macro",
        "market",
        "memorySnapshot",
        "narrativeDiff",
        "network",
        "news",
        "notes",
        "panel",
        "priority",
        "quant",
        "rank",
        "readFiling",
        "refreshFromApi",
        "report",
        "reportModel",
        "retrievalBlocks",
        "search",
        "select",
        "sources",
        "stockCode",
        "story",
        "storyTree",
        "table",
        "topicSummaries",
        "topics",
        "trace",
        "update",
        "validateStory",
        "valuationImpact",
        "view",
        "watch",
        "workforce",
    },
}


@dataclass(frozen=True)
class Violation:
    """Guard 위반 1건."""

    rule: str
    path: str
    line: int
    message: str
    severity: str
    baselineKey: str

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict."""
        return asdict(self)


def evaluateL0L15(records: list[ModuleRecord]) -> list[Violation]:
    """L0~L1.5 architecture rule 전수 평가."""
    violations: list[Violation] = []
    violations.extend(checkImportDirection(records))
    violations.extend(checkL1CrossImport(records))
    violations.extend(checkL15SiblingImport(records))
    violations.extend(checkLazyBoundaryDebt(records))
    violations.extend(checkProviderCompanyFrozenSurface(records))
    return sorted(violations, key=lambda item: (item.rule, item.path, item.line, item.message))


def checkImportDirection(records: list[ModuleRecord]) -> list[Violation]:
    """L0~L1.5 상위 계층 직접 import 금지."""
    violations: list[Violation] = []
    for record in records:
        if record.topPackage not in STRICT_L0_L15:
            continue
        if record.path.endswith("/di.py") or record.path.endswith("\\di.py"):
            continue
        ownerLayer = LAYER_OF.get(record.topPackage)
        if ownerLayer is None:
            continue
        for importRecord in record.imports:
            if not importRecord.isTopLevel:
                continue
            target = importRecord.topPackage
            if target is None or target in SINK_HELPERS or target not in LAYER_OF:
                continue
            targetLayer = LAYER_OF[target]
            if targetLayer > ownerLayer:
                violations.append(
                    makeViolation(
                        "architecture.importDirection",
                        record.path,
                        importRecord.line,
                        f"L{ownerLayer} {record.topPackage} imports L{targetLayer} {target}",
                    )
                )
    return violations


def checkL1CrossImport(records: list[ModuleRecord]) -> list[Violation]:
    """gather/providers module-level cross import 금지."""
    violations: list[Violation] = []
    for record in records:
        if record.topPackage not in L1_PEERS:
            continue
        for importRecord in record.imports:
            if not importRecord.isTopLevel:
                continue
            target = importRecord.topPackage
            if target in L1_PEERS and target != record.topPackage:
                violations.append(
                    makeViolation(
                        "architecture.l1CrossImport",
                        record.path,
                        importRecord.line,
                        f"{record.topPackage} imports {target}",
                    )
                )
    return violations


def checkL15SiblingImport(records: list[ModuleRecord]) -> list[Violation]:
    """scan/frame/synth/reference sibling import 금지. lazy import도 포함한다."""
    violations: list[Violation] = []
    for record in records:
        if record.topPackage not in L15_PEERS:
            continue
        for importRecord in record.imports:
            target = importRecord.topPackage
            if target in L15_PEERS and target != record.topPackage:
                violations.append(
                    makeViolation(
                        "architecture.l15SiblingImport",
                        record.path,
                        importRecord.line,
                        f"{record.topPackage} imports {target}",
                    )
                )
    return violations


def checkLazyBoundaryDebt(records: list[ModuleRecord]) -> list[Violation]:
    """L1 function-local 상위 import debt를 수집한다.

    module-level import 는 기존 architecture rule 이 직접 차단한다. 이 rule 은
    Company facade / legacy accessor 가 function body 안에서 상위 계층을 당겨 쓰는
    경로를 baseline ledger 에 올려 신규 증가를 막는다.
    """
    violations: list[Violation] = []
    for record in records:
        if record.topPackage not in L1_PEERS:
            continue
        for importRecord in record.imports:
            if importRecord.isTopLevel:
                continue
            target = importRecord.topPackage
            if target is None or target in SINK_HELPERS:
                continue
            if target == ROOT_FACADE:
                violations.append(
                    makeViolation(
                        "architecture.lazyRootFacadeImport",
                        record.path,
                        importRecord.line,
                        f"lazy root-facade import: {record.topPackage} imports dartlab",
                        importKind="root-facade",
                    )
                )
                continue
            if target in L1_PEERS and target != record.topPackage:
                violations.append(
                    makeViolation(
                        "architecture.lazyL1CrossImport",
                        record.path,
                        importRecord.line,
                        f"lazy L1 cross import: {record.topPackage} imports {target}",
                        importKind="lazy",
                    )
                )
                continue
            if target in L15_PEERS or target in L2_PEERS:
                violations.append(
                    makeViolation(
                        "architecture.lazyUpperImport",
                        record.path,
                        importRecord.line,
                        f"lazy upper import: {record.topPackage} imports {target}",
                        importKind="lazy",
                    )
                )
    return violations


def checkProviderCompanyFrozenSurface(records: list[ModuleRecord]) -> list[Violation]:
    """provider Company public surface 변경을 frozen manifest로 차단한다.

    Capabilities:
        DART/EDGAR provider `Company` 클래스의 public method 추가와 제거를
        둘 다 Guard 신규 위반으로 보고한다.

    Args:
        records: Guard Index module record 목록.

    Returns:
        `api.companyFacadeFrozenSurface` 위반 목록. 현재 공개 surface는 보존되고,
        신규 추가·삭제는 API Contract 검토 전까지 실패한다.

    Example:
        >>> violations = checkProviderCompanyFrozenSurface(records)
        >>> all(v.rule == "api.companyFacadeFrozenSurface" for v in violations)
        True

    Guide:
        Company facade 공개 호출은 보존한다. 이 rule은 facade를 쪼개거나 rename하지 않고,
        provider class 공개 surface가 조용히 늘거나 줄어드는 일을 막는다.

    SeeAlso:
        `operation.apiContract` 공개 진입점 정책, `core.protocols.PublicCompanyFacadeProtocol`.

    Requires:
        repo root에서 실행되어 `src/dartlab/providers/{dart,edgar}/company.py`를 읽을 수 있어야 한다.

    AIContext:
        신규 surface가 필요하면 먼저 API Contract와 Protocol에 명시한 뒤 의도적으로 검토한다.

    LLM Specifications:
        AntiPatterns: facade method를 자동 이동하거나 삭제하지 않는다.
        OutputSchema: rule/path/line/message/baselineKey를 가진 Violation.
        Prerequisites: AST parse 가능한 Python source.
        Freshness: frozen manifest는 현재 public facade surface snapshot이다.
        Dataflow: provider company AST -> public method inventory -> frozen manifest diff.
        TargetMarkets: KR DART, US EDGAR.
    """
    violations: list[Violation] = []
    indexedPaths = {record.path for record in records}
    for path, providerName in PROVIDER_COMPANY_FILES.items():
        if path not in indexedPaths:
            continue
        violations.extend(checkProviderCompanyFile(Path(path), providerName))
    return violations


def checkProviderCompanyFile(path: Path, providerName: str) -> list[Violation]:
    """provider company.py 1개를 frozen public surface와 비교한다."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    companyClass = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Company"),
        None,
    )
    if companyClass is None:
        return []

    actual = {
        node.name
        for node in companyClass.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("_")
    }
    expected = FROZEN_PROVIDER_COMPANY_SURFACE[providerName]
    violations: list[Violation] = []
    lineByName = {
        node.name: node.lineno
        for node in companyClass.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("_")
    }
    for methodName in sorted(actual - expected):
        violations.append(
            Violation(
                rule="api.companyFacadeFrozenSurface",
                path=path.as_posix(),
                line=lineByName.get(methodName, 0),
                message=(
                    "[public] provider Company public surface added without API Contract review: "
                    f"{providerName}.Company.{methodName}"
                ),
                severity="error",
                baselineKey=f"api.companyFacadeFrozenSurface:added:{path.as_posix()}:{methodName}",
            )
        )
    for methodName in sorted(expected - actual):
        violations.append(
            Violation(
                rule="api.companyFacadeFrozenSurface",
                path=path.as_posix(),
                line=0,
                message=(
                    "[public] provider Company public surface removed without compatibility review: "
                    f"{providerName}.Company.{methodName}"
                ),
                severity="error",
                baselineKey=f"api.companyFacadeFrozenSurface:removed:{path.as_posix()}:{methodName}",
            )
        )
    return violations


def makeViolation(rule: str, path: str, line: int, message: str, *, importKind: str = "direct") -> Violation:
    """표준 baseline key를 가진 Violation 생성."""
    baselineKey = f"{rule}:{importKind}:{path}:{line}"
    return Violation(
        rule=rule,
        path=path,
        line=line,
        message=f"[{importKind}] {message}",
        severity="error",
        baselineKey=baselineKey,
    )
