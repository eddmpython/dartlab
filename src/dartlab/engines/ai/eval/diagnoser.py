"""자동 진단 엔진 — 배치 결과에서 약점/갭/회귀를 자동 발견."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class WeakTypeReport:
    """질문 유형별 약점 보고."""

    questionType: str
    avgOverall: float
    caseCount: int
    topFailures: list[str]


@dataclass
class CoverageGap:
    """eval 케이스가 커버하지 않는 영역."""

    kind: str  # "route", "module", "persona", "severity", "stockCode"
    detail: str
    suggestion: str


@dataclass
class Regression:
    """이전 배치 대비 점수 하락."""

    caseId: str
    prevOverall: float
    currOverall: float
    delta: float
    likelyFailures: list[str]


@dataclass
class DiagnosisReport:
    """전체 진단 결과."""

    weakTypes: list[WeakTypeReport] = field(default_factory=list)
    coverageGaps: list[CoverageGap] = field(default_factory=list)
    regressions: list[Regression] = field(default_factory=list)
    timestamp: str = ""

    def toMarkdown(self) -> str:
        """마크다운 형식으로 변환."""
        lines = [f"# Eval 진단 리포트 — {self.timestamp}", ""]

        if self.weakTypes:
            lines.append("## 약점 유형 (하위 점수)")
            lines.append("")
            lines.append("| 유형 | 평균 점수 | 케이스 수 | 주요 실패 |")
            lines.append("|------|---------|---------|---------|")
            for w in self.weakTypes:
                failures = ", ".join(w.topFailures[:3]) or "-"
                lines.append(f"| {w.questionType} | {w.avgOverall:.2f} | {w.caseCount} | {failures} |")
            lines.append("")

        if self.coverageGaps:
            lines.append("## 커버리지 갭")
            lines.append("")
            for g in self.coverageGaps:
                lines.append(f"- **[{g.kind}]** {g.detail} → {g.suggestion}")
            lines.append("")

        if self.regressions:
            lines.append("## 회귀 감지")
            lines.append("")
            lines.append("| 케이스 | 이전 | 현재 | 변화 | 실패 유형 |")
            lines.append("|--------|------|------|------|---------|")
            for r in self.regressions:
                failures = ", ".join(r.likelyFailures[:3]) or "-"
                lines.append(
                    f"| {r.caseId} | {r.prevOverall:.2f} | {r.currOverall:.2f} | {r.delta:+.2f} | {failures} |"
                )
            lines.append("")

        if not self.weakTypes and not self.coverageGaps and not self.regressions:
            lines.append("모든 항목 양호.")

        return "\n".join(lines)


def findWeakTypes(results: list[dict[str, Any]], bottomN: int = 3) -> list[WeakTypeReport]:
    """질문 유형별 평균 점수 계산, 하위 N개 반환."""
    typeScores: dict[str, list[float]] = {}
    typeFailures: dict[str, list[str]] = {}

    for r in results:
        qType = r.get("questionType") or r.get("userIntent") or "unknown"
        overall = r.get("overall", 0.0)
        failures = r.get("failureTypes", [])

        typeScores.setdefault(qType, []).append(overall)
        typeFailures.setdefault(qType, []).extend(failures)

    reports = []
    for qType, scores in typeScores.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        # 실패 유형 빈도순
        failureCounts: dict[str, int] = {}
        for f in typeFailures.get(qType, []):
            failureCounts[f] = failureCounts.get(f, 0) + 1
        topFailures = sorted(failureCounts, key=failureCounts.get, reverse=True)  # type: ignore[arg-type]
        reports.append(WeakTypeReport(qType, avg, len(scores), topFailures[:3]))

    reports.sort(key=lambda r: r.avgOverall)
    return reports[:bottomN]


def findCoverageGaps(cases: list[dict[str, Any]]) -> list[CoverageGap]:
    """케이스 집합의 커버리지 부족 영역 탐지."""
    gaps: list[CoverageGap] = []

    # 1. persona 균형 (최소 3개)
    personaCounts: dict[str, int] = {}
    for c in cases:
        p = c.get("persona", "unknown")
        personaCounts[p] = personaCounts.get(p, 0) + 1
    for persona, count in personaCounts.items():
        if count < 3:
            gaps.append(
                CoverageGap(
                    "persona",
                    f"{persona}: {count}개 케이스",
                    f"{persona} persona에 케이스 {3 - count}개 추가 필요",
                )
            )

    # 2. route 커버리지
    routes = {c.get("expectedRoute") for c in cases if c.get("expectedRoute")}
    requiredRoutes = {"finance", "sections", "hybrid", "report"}
    for r in requiredRoutes - routes:
        gaps.append(CoverageGap("route", f"route '{r}' 미커버", f"expectedRoute='{r}'인 케이스 추가"))

    # 3. severity 분포
    severityCounts: dict[str, int] = {}
    for c in cases:
        s = c.get("severity", "medium")
        severityCounts[s] = severityCounts.get(s, 0) + 1
    total = len(cases) or 1
    criticalHigh = severityCounts.get("critical", 0) + severityCounts.get("high", 0)
    if criticalHigh / total < 0.4:
        gaps.append(
            CoverageGap(
                "severity",
                f"critical+high = {criticalHigh}/{total} ({criticalHigh / total:.0%})",
                "critical/high severity 케이스 비율 40% 이상으로",
            )
        )

    # 4. 종목코드 편중
    stockCounts: dict[str, int] = {}
    stockCases = [c for c in cases if c.get("stockCode")]
    for c in stockCases:
        sc = c["stockCode"]
        stockCounts[sc] = stockCounts.get(sc, 0) + 1
    if stockCases:
        for sc, count in stockCounts.items():
            if count / len(stockCases) > 0.6:
                gaps.append(
                    CoverageGap(
                        "stockCode",
                        f"{sc}: {count}/{len(stockCases)} ({count / len(stockCases):.0%})",
                        "다른 종목코드 케이스 추가로 편중 해소",
                    )
                )

    # 5. module 커버리지
    coveredModules: set[str] = set()
    for c in cases:
        coveredModules.update(c.get("expectedModules", []))

    # 핵심 모듈 목록
    coreModules = {"IS", "BS", "CF", "ratios", "costByNature", "segments", "businessOverview", "governanceOverview"}
    missing = coreModules - coveredModules
    for m in missing:
        gaps.append(CoverageGap("module", f"모듈 '{m}' 미커버", f"expectedModules에 '{m}' 포함하는 케이스 추가"))

    return gaps


def findRegressions(
    currentResults: list[dict[str, Any]],
    previousResults: list[dict[str, Any]],
    threshold: float = -0.1,
) -> list[Regression]:
    """이전 배치 대비 점수 하락 케이스 탐지."""
    prevMap: dict[str, dict[str, Any]] = {r["caseId"]: r for r in previousResults if "caseId" in r}
    regressions: list[Regression] = []

    for curr in currentResults:
        caseId = curr.get("caseId", "")
        if caseId not in prevMap:
            continue
        prev = prevMap[caseId]
        delta = curr.get("overall", 0) - prev.get("overall", 0)
        if delta < threshold:
            regressions.append(
                Regression(
                    caseId=caseId,
                    prevOverall=prev.get("overall", 0),
                    currOverall=curr.get("overall", 0),
                    delta=delta,
                    likelyFailures=curr.get("failureTypes", []),
                )
            )

    regressions.sort(key=lambda r: r.delta)
    return regressions


# ── 코드 변경 → 케이스 영향 매핑 ─────────────────────────

_FILE_CASE_IMPACT: dict[str, list[str]] = {
    "context/builder.py": ["*"],
    "context/finance_context.py": ["analyst.*", "investor.*", "accountant.*"],
    "conversation/templates/analysis_rules.py": ["*"],
    "conversation/prompts.py": ["*"],
    "runtime/pipeline.py": ["analyst.*", "investor.*", "accountant.*"],
    "tools/recipes.py": ["analyst.*", "investor.*"],
    "tools/defaults/analysis.py": ["analyst.*", "investor.*"],
    "tools/defaults/market.py": ["investor.*", "analyst.*"],
}


def mapCodeImpact(changedFiles: list[str], cases: list[dict[str, Any]]) -> list[str]:
    """변경된 파일 → 영향받는 케이스 ID 반환."""
    impactPatterns: set[str] = set()
    for f in changedFiles:
        for key, patterns in _FILE_CASE_IMPACT.items():
            if key in f.replace("\\", "/"):
                impactPatterns.update(patterns)

    if "*" in impactPatterns:
        return [c.get("id", "") for c in cases]

    import fnmatch

    impacted: list[str] = []
    for c in cases:
        caseId = c.get("id", "")
        for pat in impactPatterns:
            if fnmatch.fnmatch(caseId, pat):
                impacted.append(caseId)
                break
    return impacted


def diagnoseBatchResults(batchPath: Path) -> DiagnosisReport:
    """배치 결과 JSONL 파일을 분석해서 진단 리포트 생성."""
    results: list[dict[str, Any]] = []
    with open(batchPath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    report = DiagnosisReport(
        weakTypes=findWeakTypes(results),
        coverageGaps=[],  # 배치 결과만으로는 케이스 갭 불가 — cases 필요
        regressions=[],
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    return report


def diagnoseFull(
    batchPath: Path | None = None,
    previousBatchPath: Path | None = None,
    casesPath: Path | None = None,
) -> DiagnosisReport:
    """전체 진단 (약점 + 갭 + 회귀)."""
    report = DiagnosisReport(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))

    # 배치 결과 분석
    if batchPath and batchPath.exists():
        results: list[dict[str, Any]] = []
        with open(batchPath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        report.weakTypes = findWeakTypes(results)

        # 회귀 탐지
        if previousBatchPath and previousBatchPath.exists():
            prevResults: list[dict[str, Any]] = []
            with open(previousBatchPath, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        prevResults.append(json.loads(line))
            report.regressions = findRegressions(results, prevResults)

    # 커버리지 갭
    if casesPath and casesPath.exists():
        with open(casesPath, encoding="utf-8") as f:
            data = json.load(f)
        cases = data.get("cases", data) if isinstance(data, dict) else data
        report.coverageGaps = findCoverageGaps(cases)

    return report
