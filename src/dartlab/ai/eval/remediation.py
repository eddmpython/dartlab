"""failure taxonomy → 구체적 코드 수정 위치 매핑."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RemediationPlan:
    """개별 개선 계획."""

    failureType: str
    targetFile: str
    description: str
    priority: int  # 1=최우선 ~ 5=낮음
    estimatedImpact: str  # "high", "medium", "low"


# ── failure → 코드 수정 매핑 ─────────────────────────────

_FAILURE_REMEDIATION: dict[str, dict[str, str]] = {
    "routing_failure": {
        "targetFile": "engines/ai/context/builder.py",
        "description": "_ROUTE_*_KEYWORDS에 누락 키워드 추가",
        "estimatedImpact": "high",
    },
    "retrieval_failure": {
        "targetFile": "engines/ai/context/finance_context.py",
        "description": "_QUESTION_MODULES 매핑에 모듈 추가",
        "estimatedImpact": "high",
    },
    "false_unavailable": {
        "targetFile": "engines/ai/context/builder.py",
        "description": "build_context_tiered에서 context 포함 경로 확장",
        "estimatedImpact": "high",
    },
    "generation_failure": {
        "targetFile": "engines/ai/conversation/templates/analysis_rules.py",
        "description": "분석 규칙에 few-shot 예시 추가",
        "estimatedImpact": "medium",
    },
    "ui_wording_failure": {
        "targetFile": "engines/ai/conversation/system_base.py",
        "description": "시스템 프롬프트에서 내부 명칭 금지 강화",
        "estimatedImpact": "low",
    },
    "hallucination": {
        "targetFile": "engines/ai/conversation/templates/analysis_rules.py",
        "description": "숫자 인용 시 출처 명시 규칙 강화",
        "estimatedImpact": "high",
    },
    "data_gap": {
        "targetFile": "engines/company/dart/",
        "description": "데이터 파서 구현 또는 매핑 확장 필요",
        "estimatedImpact": "medium",
    },
    "module_underuse": {
        "targetFile": "engines/ai/runtime/pipeline.py",
        "description": "파이프라인 frozenset에 모듈 포함 확장",
        "estimatedImpact": "medium",
    },
    "clarification_failure": {
        "targetFile": "engines/ai/conversation/system_base.py",
        "description": "clarification 정책 조건 수정",
        "estimatedImpact": "low",
    },
    "context_shallow": {
        "targetFile": "engines/ai/context/finance_context.py",
        "description": "context 레이어에 더 많은 데이터 소스 포함",
        "estimatedImpact": "medium",
    },
    "citation_imprecise": {
        "targetFile": "engines/ai/conversation/templates/analysis_rules.py",
        "description": "인용 형식 규칙(연도+출처+수치 트리플) 강화",
        "estimatedImpact": "medium",
    },
}


def generateRemediations(
    failureCounts: dict[str, int],
    threshold: int = 1,
) -> list[RemediationPlan]:
    """failure 빈도에서 개선 계획 생성.

    Args:
        failureCounts: {failureType: count}
        threshold: 최소 발생 횟수

    Returns:
        우선순위순 RemediationPlan 목록.
    """
    plans: list[RemediationPlan] = []

    for failureType, count in failureCounts.items():
        if count < threshold:
            continue

        remediation = _FAILURE_REMEDIATION.get(failureType)
        if remediation is None:
            plans.append(
                RemediationPlan(
                    failureType=failureType,
                    targetFile="(매핑 없음)",
                    description=f"새 failure 유형 — 매핑 추가 필요 (발생 {count}회)",
                    priority=5,
                    estimatedImpact="unknown",
                )
            )
            continue

        # 빈도 기반 우선순위 (1=최우선)
        if count >= 5:
            priority = 1
        elif count >= 3:
            priority = 2
        elif count >= 2:
            priority = 3
        else:
            priority = 4

        # impact에 따른 보정
        impact = remediation["estimatedImpact"]
        if impact == "high":
            priority = max(1, priority - 1)

        plans.append(
            RemediationPlan(
                failureType=failureType,
                targetFile=remediation["targetFile"],
                description=f"{remediation['description']} (발생 {count}회)",
                priority=priority,
                estimatedImpact=impact,
            )
        )

    plans.sort(key=lambda p: p.priority)
    return plans


def formatAsMarkdown(plans: list[RemediationPlan]) -> str:
    """개선 계획을 마크다운으로."""
    if not plans:
        return "개선 필요 사항 없음."

    lines = ["# 개선 계획 (Remediation)", ""]
    lines.append("| 우선순위 | Failure | 대상 파일 | 설명 | 영향도 |")
    lines.append("|---------|---------|----------|------|-------|")

    for p in plans:
        lines.append(f"| P{p.priority} | {p.failureType} | `{p.targetFile}` | {p.description} | {p.estimatedImpact} |")

    lines.append("")
    highPriority = [p for p in plans if p.priority <= 2]
    if highPriority:
        lines.append(f"**즉시 조치 필요**: {len(highPriority)}건")
        for p in highPriority:
            lines.append(f"- [{p.failureType}] → `{p.targetFile}`")

    return "\n".join(lines)


def generateGitHubIssueBody(plans: list[RemediationPlan]) -> str:
    """gh issue create용 본문 생성."""
    if not plans:
        return ""

    lines = ["## Eval 자동 진단 — 개선 필요", ""]
    lines.append("배치 결과 분석에서 다음 개선 사항이 발견되었습니다:")
    lines.append("")

    for p in plans:
        lines.append(f"### P{p.priority}: {p.failureType}")
        lines.append(f"- **대상**: `{p.targetFile}`")
        lines.append(f"- **설명**: {p.description}")
        lines.append(f"- **영향도**: {p.estimatedImpact}")
        lines.append("")

    lines.append("---")
    lines.append("*자동 생성 by evalDiagnose.py*")
    return "\n".join(lines)


def extractFailureCounts(results: list[dict[str, Any]]) -> dict[str, int]:
    """배치 결과에서 failure 유형별 빈도 추출."""
    counts: dict[str, int] = {}
    for r in results:
        for ftype in r.get("failureTypes", []):
            counts[ftype] = counts.get(ftype, 0) + 1
    return counts
