"""Guard Index rule 평가."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from guard.indexer import (
    CALLER_OWNED_IMPORT,
    DYNAMIC_UNKNOWN,
    EAGER_PHASE,
    LAYER_OF,
    LAZY_PHASE,
    ROOT_FACADE,
    STATIC_IMPORT,
    ModuleRecord,
)

L1_PEERS = {"gather", "providers"}
L15_PEERS = {"scan", "frame", "synth", "reference"}
L2_PEERS = {"analysis", "macro", "quant", "industry", "credit"}
CORE_CALLER_OWNED_DYNAMIC_FILES = {
    "src/dartlab/core/pluginDiscovery.py",
    "src/dartlab/core/plugins.py",
}
PROVIDER_COMPANY_FILES = {
    "src/dartlab/providers/dart/company.py": "dart",
    "src/dartlab/providers/edgar/company.py": "edgar",
}
# simulate 공개 계약 폐쇄 frozen manifest. `simulate/__init__.py` import 에서 자동 도출하지
# 않는다: 자동이면 import 한 줄 추가로 폐쇄가 넓어져 가드 목적이 무효가 된다. 이 목록의
# 변경 = 의도적 계약 검토다(FROZEN_PROVIDER_COMPANY_SURFACE 선례). 실측(2026-08-04):
# 공개 표면 전이 폐쇄는 86모듈 중 이 6개뿐이고, 나머지는 scenario-simulator initiative
# 자산이라 import 한 줄로 39k LoC 가 조용히 공개 표면이 되는 사고를 오늘은 아무 테스트도
# 못 잡았다.
SIMULATE_CONTRACT_CLOSURE = {
    "dartlab.simulate",
    "dartlab.simulate.entry",
    "dartlab.simulate.registry",
    "dartlab.simulate.run",
    "dartlab.simulate.sheet",
    "dartlab.simulate.transfer",
}
# 계약 밖 승인된 운영 표면: `.github/scripts/sync/buildExpectations.py` 월간 cron 이
# 소비하는 기대격자 체인(handbook architecture/analysisProducts.md 가 제품 구조로 기술).
# src 안 소비자는 없어야 하며, 이 목록은 cron 스크립트 쪽 import 와 함께 갱신한다.
SIMULATE_OPERATIONAL_SURFACE = {
    "dartlab.simulate.dataStore",
    "dartlab.simulate.estimateStatements",
    "dartlab.simulate.expectationCycle",
    "dartlab.simulate.expectationLedger",
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
    violations.extend(checkCoreImportBoundary(records))
    violations.extend(checkImportDirection(records))
    violations.extend(checkL1CrossImport(records))
    violations.extend(checkL15SiblingImport(records))
    violations.extend(checkLazyBoundaryDebt(records))
    violations.extend(checkProviderCompanyFrozenSurface(records))
    return sorted(violations, key=lambda item: (item.rule, item.path, item.line, item.message))


def checkCoreImportBoundary(records: list[ModuleRecord]) -> list[Violation]:
    """core의 정적·동적 상향 import와 미해결 동적 호출을 함께 차단한다."""
    violations: list[Violation] = []
    for record in records:
        if record.topPackage != "core":
            continue
        for importRecord in record.imports:
            if importRecord.module == DYNAMIC_UNKNOWN:
                if importRecord.kind != CALLER_OWNED_IMPORT or record.path not in CORE_CALLER_OWNED_DYNAMIC_FILES:
                    violations.append(
                        makeViolation(
                            "architecture.coreUnresolvedDynamicImport",
                            record.path,
                            importRecord.line,
                            "core has unresolved dynamic import target",
                            importKind=importRecord.kind,
                        )
                    )
                continue
            target = importRecord.topPackage
            targetLayer = LAYER_OF.get(target) if target is not None else None
            if targetLayer is None or targetLayer <= LAYER_OF["core"]:
                continue
            violations.append(
                makeViolation(
                    "architecture.coreUpperImport",
                    record.path,
                    importRecord.line,
                    f"L0 core imports L{targetLayer} {target}",
                    importKind=importRecord.kind,
                    subject=f"{target}:{importRecord.module}",
                )
            )
    return violations


def checkImportDirection(records: list[ModuleRecord]) -> list[Violation]:
    """모든 선언 계층의 module-eager 상향 import를 차단한다."""
    violations: list[Violation] = []
    for record in records:
        if record.topPackage == "core":
            continue
        ownerLayer = LAYER_OF.get(record.topPackage)
        if ownerLayer is None:
            continue
        for importRecord in record.imports:
            if importRecord.kind != STATIC_IMPORT:
                continue
            if importRecord.phase != EAGER_PHASE:
                continue
            target = importRecord.topPackage
            if target is None or target not in LAYER_OF:
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
            if importRecord.kind != STATIC_IMPORT:
                continue
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
            if importRecord.kind != STATIC_IMPORT:
                continue
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
            if importRecord.phase != LAZY_PHASE:
                continue
            target = importRecord.topPackage
            if target is None:
                continue
            if target == ROOT_FACADE:
                violations.append(
                    makeViolation(
                        "architecture.lazyRootFacadeImport",
                        record.path,
                        importRecord.line,
                        f"lazy root-facade import: {record.topPackage} imports dartlab",
                        importKind="root-facade",
                        subject=target if target is not None else "root",
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
                        subject=target if target is not None else "root",
                    )
                )
                continue
            # 예전에는 L1.5 와 L2 만 상위로 셌다. 그래서 L1 이 L2.5(data, simulate)나
            # L3 이상(story, ai, mcp)을 lazy 로 끌어와도 원장에 남지 않았다. 계층
            # 숫자로 비교하면 어느 층이 새로 생겨도 규칙이 따라온다.
            ownerLayer = LAYER_OF.get(record.topPackage)
            targetLayer = LAYER_OF.get(target)
            if ownerLayer is not None and targetLayer is not None and targetLayer > ownerLayer:
                violations.append(
                    makeViolation(
                        "architecture.lazyUpperImport",
                        record.path,
                        importRecord.line,
                        f"lazy upper import: {record.topPackage} imports {target}",
                        importKind="lazy",
                        subject=target if target is not None else "root",
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
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        raise ValueError(f"provider Company surface 검사 실패: {path}: {type(exc).__name__}: {exc}") from exc
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


def checkSimulateContractClosure(records: list[ModuleRecord]) -> list[Violation]:
    """simulate 공개 계약 폐쇄를 frozen manifest 로 고정한다.

    검사 1(외부 유출): simulate 밖 src 모듈이 폐쇄·운영 manifest 밖의
    ``dartlab.simulate.*`` 하위 모듈을 import 하면 위반. kind·phase 무관(lazy·동적 포함).
    검사 2(폐쇄 고정점): 폐쇄 6모듈 자신이 manifest 밖 simulate 모듈을 import 해도 위반.
    ``run.py`` 에 import 한 줄이 추가되는 순간 39k LoC 가 공개 전이 표면으로 소리 없이
    승격되는 사고를 막는다. 승격·삭제는 manifest 수정(=의도적 계약 검토)으로만 가능하다.
    """
    allowed = SIMULATE_CONTRACT_CLOSURE | SIMULATE_OPERATIONAL_SURFACE
    violations: list[Violation] = []
    for record in records:
        insideClosure = record.module in SIMULATE_CONTRACT_CLOSURE
        outsideSimulate = record.topPackage != "simulate"
        if not (insideClosure or outsideSimulate):
            continue
        for importRecord in record.imports:
            module = importRecord.module
            if not module.startswith("dartlab.simulate.") or module in allowed:
                continue
            kind = "closure-fixed-point" if insideClosure else "outside-leak"
            violations.append(
                makeViolation(
                    "api.simulateContractClosure",
                    record.path,
                    importRecord.line,
                    f"{record.module} imports non-contract {module}",
                    importKind=kind,
                    subject=module,
                )
            )
    return violations


def makeViolation(
    rule: str,
    path: str,
    line: int,
    message: str,
    *,
    importKind: str = "direct",
    subject: str | None = None,
) -> Violation:
    """표준 baseline key를 가진 Violation 생성.

    `subject` 를 주면 줄번호 대신 그것으로 키를 만든다. 줄번호 키는 5,660 줄과 4,681 줄
    짜리 최다 편집 파일 두 개를 가리키고 있어서, 위쪽에 한 줄만 끼워 넣어도 같은 위반이
    신규로 잡히고 baseline 항목은 죽은 채 남았다. 그러면 원장을 읽는 대신 다시 뜨는
    습관이 든다. 대상 패키지로 잡으면 파일이 커져도 키가 유지된다.
    """

    anchor = subject if subject is not None else str(line)
    baselineKey = f"{rule}:{importKind}:{path}:{anchor}"
    return Violation(
        rule=rule,
        path=path,
        line=line,
        message=f"[{importKind}] {message}",
        severity="error",
        baselineKey=baselineKey,
    )
