"""기능별 준비 상태 점검 — Readiness Protocol.

각 축/기능이 guide.checkReady("feature")로 호출하면,
해당 기능에 필요한 모든 조건을 점검하고 부족한 것 + 해결 방법을 안내한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ReadyStatus(Enum):
    READY = "ready"
    PARTIAL = "partial"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReadinessIssue:
    """하나의 미충족 조건."""

    kind: str
    message: str
    fixAction: str
    severity: str = "error"


@dataclass
class ReadinessResult:
    """기능 준비 상태 점검 결과."""

    feature: str
    status: ReadyStatus
    issues: list[ReadinessIssue] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in (ReadyStatus.READY, ReadyStatus.PARTIAL)

    def guideText(self) -> str:
        """사용자에게 보여줄 안내 텍스트 생성."""
        if self.ok:
            return f"[{self.feature}] 사용 가능"
        lines = [f"[{self.feature}] 사용 불가:"]
        for issue in self.issues:
            lines.append(f"  - {issue.message}")
            lines.append(f"    해결: {issue.fixAction}")
        return "\n".join(lines)


# ── Checker Registry ──

_CHECKERS: dict[str, Callable[..., ReadinessResult]] = {}


def registerChecker(feature: str) -> Callable:
    """기능별 readiness checker 등록 데코레이터.

    L1/L2 모듈이 자기 점검 로직을 등록할 수 있다::

        @registerChecker("analysis.governance")
        def _checkGovernance(*, stockCode=None, **kw):
            ...
    """
    def decorator(fn: Callable[..., ReadinessResult]) -> Callable:
        _CHECKERS[feature] = fn
        return fn
    return decorator


def getChecker(feature: str) -> Callable[..., ReadinessResult] | None:
    return _CHECKERS.get(feature)


def listFeatures() -> list[str]:
    return list(_CHECKERS.keys())


# ── Helper ──

def _lazyHasDartKey() -> bool:
    try:
        from dartlab.providers.dart.openapi.dartKey import hasDartApiKey
        return hasDartApiKey()
    except ImportError:
        return False


# ── Built-in Checkers ──


@registerChecker("data")
def _checkData(*, stockCode: str | None = None, category: str = "docs", **_kw: Any) -> ReadinessResult:
    """데이터 존재 여부 점검."""
    if stockCode is None:
        return ReadinessResult(feature="data", status=ReadyStatus.READY)

    issues: list[ReadinessIssue] = []
    try:
        from dartlab.core.dataLoader import _dataDir
        path = _dataDir(category) / f"{stockCode}.parquet"
        if not path.exists():
            hasKey = _lazyHasDartKey()
            fix = f"dartlab collect {stockCode}" if hasKey else "dartlab setup dart-key"
            issues.append(ReadinessIssue(
                kind="missing_data",
                message=f"{stockCode} {category} 데이터 없음",
                fixAction=fix,
            ))
    except (ImportError, KeyError, TypeError):
        issues.append(ReadinessIssue(
            kind="missing_data",
            message=f"{stockCode} {category} 데이터 경로 확인 불가",
            fixAction=f"dartlab collect {stockCode}",
        ))

    return ReadinessResult(
        feature="data",
        status=ReadyStatus.NOT_READY if issues else ReadyStatus.READY,
        issues=issues,
    )


@registerChecker("ai")
def _checkAi(*, provider: str | None = None, **_kw: Any) -> ReadinessResult:
    """AI provider 사용 가능 여부 점검."""
    issues: list[ReadinessIssue] = []
    context: dict[str, Any] = {}

    try:
        from dartlab.guide.detect import auto_detect_provider
        detected = auto_detect_provider()
        context["detected_provider"] = detected
        if detected is None:
            from dartlab.guide.hints import onKeyRequired

            issues.append(ReadinessIssue(
                kind="no_provider",
                message="사용 가능한 AI provider가 없습니다",
                fixAction=onKeyRequired("gemini").strip(),
            ))
    except ImportError:
        issues.append(ReadinessIssue(
            kind="no_provider",
            message="AI 모듈을 로드할 수 없습니다",
            fixAction="pip install dartlab[ai]",
        ))

    return ReadinessResult(
        feature="ai",
        status=ReadyStatus.NOT_READY if issues else ReadyStatus.READY,
        issues=issues,
        context=context,
    )


@registerChecker("dart_key")
def _checkDartKey(**_kw: Any) -> ReadinessResult:
    """DART API 키 점검."""
    hasKey = _lazyHasDartKey()
    if hasKey:
        return ReadinessResult(feature="dart_key", status=ReadyStatus.READY)
    from dartlab.guide.hints import onKeyRequired

    return ReadinessResult(
        feature="dart_key",
        status=ReadyStatus.PARTIAL,
        issues=[ReadinessIssue(
            kind="missing_key",
            message="DART API 키 미설정 (직접 수집 불가, 사전 데이터만 가능)",
            fixAction=onKeyRequired("dart").strip(),
            severity="warning",
        )],
    )


@registerChecker("finance")
def _checkFinance(*, stockCode: str | None = None, **_kw: Any) -> ReadinessResult:
    """재무분석 기능 점검."""
    dataResult = _checkData(stockCode=stockCode, category="finance")
    return ReadinessResult(
        feature="finance",
        status=dataResult.status,
        issues=list(dataResult.issues),
    )


@registerChecker("valuation")
def _checkValuation(*, stockCode: str | None = None, **_kw: Any) -> ReadinessResult:
    """밸류에이션 기능 점검 — finance + AI 필요."""
    financeResult = _checkFinance(stockCode=stockCode)
    aiResult = _checkAi()
    issues = financeResult.issues + aiResult.issues
    status = ReadyStatus.NOT_READY if issues else ReadyStatus.READY
    return ReadinessResult(feature="valuation", status=status, issues=issues)


@registerChecker("analysis")
def _checkAnalysis(*, stockCode: str | None = None, **_kw: Any) -> ReadinessResult:
    """분석 엔진 점검 — finance 데이터 필요."""
    financeResult = _checkFinance(stockCode=stockCode)
    return ReadinessResult(
        feature="analysis",
        status=financeResult.status,
        issues=list(financeResult.issues),
    )


@registerChecker("scan")
def _checkScan(**_kw: Any) -> ReadinessResult:
    """시장 횡단분석 점검 — finance 전체 데이터 필요."""
    issues: list[ReadinessIssue] = []
    try:
        from dartlab.core.dataLoader import _dataDir
        financeDir = _dataDir("finance")
        count = len(list(financeDir.glob("*.parquet"))) if financeDir.exists() else 0
        if count < 100:
            issues.append(ReadinessIssue(
                kind="insufficient_data",
                message=f"scan은 전체 시장 데이터가 필요합니다 (현재 {count}종목)",
                fixAction="dartlab.downloadAll('finance')",
            ))
    except (ImportError, KeyError):
        issues.append(ReadinessIssue(
            kind="missing_data",
            message="finance 데이터 디렉토리 확인 불가",
            fixAction="dartlab.downloadAll('finance')",
        ))
    return ReadinessResult(
        feature="scan",
        status=ReadyStatus.NOT_READY if issues else ReadyStatus.READY,
        issues=issues,
    )


@registerChecker("review")
def _checkReview(*, stockCode: str | None = None, **_kw: Any) -> ReadinessResult:
    """리뷰 보고서 점검 — finance + docs 데이터 필요."""
    issues: list[ReadinessIssue] = []
    financeResult = _checkFinance(stockCode=stockCode)
    issues.extend(financeResult.issues)
    docsResult = _checkData(stockCode=stockCode, category="docs")
    issues.extend(docsResult.issues)
    status = ReadyStatus.NOT_READY if issues else ReadyStatus.READY
    return ReadinessResult(feature="review", status=status, issues=issues)


@registerChecker("ask")
def _checkAsk(*, stockCode: str | None = None, **_kw: Any) -> ReadinessResult:
    """ask/chat 점검 — AI provider + 데이터(선택)."""
    aiResult = _checkAi()
    issues = list(aiResult.issues)
    if stockCode:
        dataResult = _checkData(stockCode=stockCode, category="docs")
        issues.extend(dataResult.issues)
    status = ReadyStatus.NOT_READY if issues else ReadyStatus.READY
    return ReadinessResult(feature="ask", status=status, issues=issues)
