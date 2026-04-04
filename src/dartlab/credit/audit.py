"""신평사 등급 대조 + 동의/비동의 자동 생성.

dCR 등급을 제도권 신평사(KIS/KR/NICE) 등급과 비교하여
동의/비동의 근거를 자동 생성한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_CREDIT_DATA_DIR = Path("data/credit")
_AUDIT_DIR = _CREDIT_DATA_DIR / "audit"
_EXTERNAL_GRADES_PATH = _CREDIT_DATA_DIR / "external_grades.json"

_GRADE_ORDER = [
    "AAA",
    "AA+",
    "AA",
    "AA-",
    "A+",
    "A",
    "A-",
    "BBB+",
    "BBB",
    "BBB-",
    "BB+",
    "BB",
    "BB-",
    "B+",
    "B",
    "B-",
    "CCC",
    "CC",
    "C",
    "D",
]
_GRADE_IDX = {g: i for i, g in enumerate(_GRADE_ORDER)}


@dataclass
class CreditAuditResult:
    """신용평가 audit 결과."""

    stockCode: str
    corpName: str
    dcrGrade: str
    dcrGradeRaw: str
    dcrScore: float
    externalGrades: dict = field(default_factory=dict)
    notchDifferences: dict = field(default_factory=dict)
    avgNotchDiff: float = 0.0
    agreements: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    structuralNotes: list[str] = field(default_factory=list)
    auditDate: str = ""


def _notchDiff(a: str, b: str) -> int:
    """두 등급 간 notch 차이."""
    ia = _GRADE_IDX.get(a)
    ib = _GRADE_IDX.get(b)
    if ia is None or ib is None:
        return 99
    return abs(ia - ib)


def _loadExternalGrades() -> dict:
    """외부 등급 JSON 로드."""
    if not _EXTERNAL_GRADES_PATH.exists():
        return {}
    try:
        return json.loads(_EXTERNAL_GRADES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def auditCredit(
    stockCode: str,
    corpName: str = "",
    result: dict | None = None,
) -> CreditAuditResult:
    """신평사 대조 + 동의/비동의 자동 생성."""
    if result is None:
        from dartlab.credit.engine import evaluate

        result = evaluate(stockCode, detail=True)

    if result is None:
        return CreditAuditResult(
            stockCode=stockCode,
            corpName=corpName,
            dcrGrade="N/A",
            dcrGradeRaw="N/A",
            dcrScore=0,
            auditDate=datetime.now().strftime("%Y-%m-%d"),
        )

    dcrGrade = result.get("grade", "N/A")
    dcrRaw = result.get("gradeRaw", "N/A")
    dcrScore = result.get("score", 0)

    # 외부 등급 조회
    allExternal = _loadExternalGrades()
    extGrades = allExternal.get(stockCode, {})

    # notch 차이 계산
    diffs = {}
    for agency, grade in extGrades.items():
        diffs[agency] = _notchDiff(dcrRaw, grade)

    avgDiff = sum(diffs.values()) / len(diffs) if diffs else 0.0

    # 동의/비동의 생성
    agreements = []
    disagreements = []
    structuralNotes = []

    captive = result.get("captiveFinance", False)
    holding = result.get("holding", False)

    for agency, grade in extGrades.items():
        diff = diffs.get(agency, 99)

        if diff <= 2:
            # 동의
            agreements.append(
                f"{agency} {grade}등급은 dartlab 정량 분석 결과({dcrGrade}, 점수 {dcrScore:.1f})와 "
                f"±{diff} notch 범위로 합리적이다."
            )
        elif diff <= 4:
            # 부분 동의 — 원인 분석
            if _GRADE_IDX.get(dcrRaw, 0) > _GRADE_IDX.get(grade, 0):
                # dartlab이 더 낮음
                reasons = _findDisagreementReasons(result, "lower")
                disagreements.append(
                    f"{agency} {grade}등급 대비 dartlab {dcrGrade}는 {diff} notch 낮다. 정량 기준 {reasons}."
                )
            else:
                disagreements.append(
                    f"{agency} {grade}등급 대비 dartlab {dcrGrade}는 {diff} notch 높다. "
                    f"정량 기준으로는 더 우수하나, 정성적 리스크가 미반영되었을 수 있다."
                )
        else:
            # 큰 괴리
            reasons = _findDisagreementReasons(
                result, "lower" if _GRADE_IDX.get(dcrRaw, 0) > _GRADE_IDX.get(grade, 0) else "higher"
            )
            disagreements.append(
                f"{agency} {grade}등급과 dartlab {dcrGrade}는 {diff} notch 차이로 큰 괴리가 있다. {reasons}."
            )

    # 구조적 참고사항
    if captive:
        structuralNotes.append(
            "캡티브 금융 복합기업 — 연결 재무제표에 금융자회사 차입금이 포함되어 "
            "정량 등급이 실제보다 낮을 수 있다. 제도권 등급은 제조/금융 부문을 분리하여 평가한다."
        )
    if holding:
        structuralNotes.append(
            "지주사 구조 — 지분법손익 비중이 크고 자체 매출이 제한적이어서 영업 지표의 해석에 주의가 필요하다."
        )

    if not extGrades:
        structuralNotes.append("외부 신용등급 데이터 없음 — data/credit/external_grades.json에 등록 필요.")

    return CreditAuditResult(
        stockCode=stockCode,
        corpName=corpName,
        dcrGrade=dcrGrade,
        dcrGradeRaw=dcrRaw,
        dcrScore=dcrScore,
        externalGrades=extGrades,
        notchDifferences=diffs,
        avgNotchDiff=round(avgDiff, 1),
        agreements=agreements,
        disagreements=disagreements,
        structuralNotes=structuralNotes,
        auditDate=datetime.now().strftime("%Y-%m-%d"),
    )


def _findDisagreementReasons(result: dict, direction: str) -> str:
    """괴리 원인 분석 — 가장 큰 점수 축을 찾아 이유를 설명."""
    axes = result.get("axes", [])
    if not axes:
        return "상세 원인 분석 불가"

    if direction == "lower":
        # dartlab이 더 낮음 — 가장 높은 점수(위험) 축이 원인
        worst = max(axes, key=lambda a: a.get("score") or 0)
        return f"{worst['name']} 축 점수 {worst.get('score', 0):.0f}점이 등급 하방 요인"
    else:
        best = min(axes, key=lambda a: a.get("score") or 100)
        return f"{best['name']} 축 점수 {best.get('score', 0):.0f}점이 정량 강점"


def auditToMarkdown(audit: CreditAuditResult, *, sectionNum: int = 8) -> str:
    """audit 결과를 마크다운으로 변환.

    Args:
        audit: 신용평가 audit 결과.
        sectionNum: 보고서 내 섹션 번호 (기본 8).
    """
    lines = []
    lines.append(f"## {sectionNum}. 신평사 등급 대조")
    lines.append("")

    if audit.externalGrades:
        lines.append("| 기관 | 등급 | dartlab | 차이 |")
        lines.append("|------|------|---------|------|")
        for agency, grade in audit.externalGrades.items():
            diff = audit.notchDifferences.get(agency, "?")
            lines.append(f"| {agency} | {grade} | {audit.dcrGrade} | {diff}n |")
        lines.append("")
        lines.append(f"평균 괴리: {audit.avgNotchDiff:.1f} notch")
        lines.append("")

    if audit.agreements:
        lines.append("### 동의")
        for a in audit.agreements:
            lines.append(f"- {a}")
        lines.append("")

    if audit.disagreements:
        lines.append("### 비동의")
        for d in audit.disagreements:
            lines.append(f"- {d}")
        lines.append("")

    if audit.structuralNotes:
        lines.append("### 구조적 참고")
        for n in audit.structuralNotes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


def saveAudit(audit: CreditAuditResult) -> Path:
    """audit 결과를 파일로 저장."""
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    name = audit.corpName or audit.stockCode
    path = _AUDIT_DIR / f"{audit.stockCode}_{name}.md"

    content = f"# {name} ({audit.stockCode}) 신용평가 Audit\n\n"
    content += f"- dartlab 등급: {audit.dcrGrade} (점수 {audit.dcrScore:.1f})\n"
    content += f"- audit 일자: {audit.auditDate}\n\n"
    content += auditToMarkdown(audit)

    path.write_text(content, encoding="utf-8")
    return path
