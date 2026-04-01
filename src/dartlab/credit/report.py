"""신용등급 보고서 생성.

등급 결과를 마크다운 보고서로 변환한다.
유튜브 정례 보고서의 원본 소스.
"""

from __future__ import annotations

from datetime import datetime


def toMarkdown(result: dict, companyName: str = "") -> str:
    """등급 결과 → 마크다운 보고서."""
    if result is None:
        return "데이터 부족으로 등급 산출 불가."

    grade = result.get("grade", "?")
    rawGrade = result.get("gradeRaw", "?")
    desc = result.get("gradeDescription", "")
    score = result.get("score", 0)
    currentScore = result.get("currentScore", 0)
    pd = result.get("pdEstimate", 0)
    ecr = result.get("eCR", "?")
    outlook = result.get("outlook", "N/A")
    sector = result.get("sector", "")
    period = result.get("latestPeriod", "")
    category = result.get("gradeCategory", "")
    inv = "투자적격" if result.get("investmentGrade") else "투기등급"
    version = result.get("methodologyVersion", "v1.0")
    captive = result.get("captiveFinance", False)
    holding = result.get("holding", False)

    lines = []

    # ── 헤더 ──
    lines.append(f"# {companyName} 신용평가 보고서")
    lines.append("")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|------|")
    lines.append(f"| **등급** | **{grade}** ({desc}) |")
    lines.append(f"| 카테고리 | {category} ({inv}) |")
    lines.append(f"| 종합 점수 | {score:.1f} / 100 |")
    lines.append(f"| 부도확률(1Y) | {pd:.2f}% |")
    lines.append(f"| 현금흐름등급 | {ecr} |")
    lines.append(f"| 등급 전망 | {outlook} |")
    lines.append(f"| 업종 | {sector} |")
    lines.append(f"| 기준 기간 | {period} |")
    lines.append(f"| 방법론 | {version} |")
    if captive:
        lines.append(f"| 구조 | 캡티브금융 복합기업 (유틸리티 기준 적용) |")
    if holding:
        lines.append(f"| 구조 | 지주사 |")
    lines.append("")

    # ── 7축 상세 ──
    lines.append("## 7축 평가 상세")
    lines.append("")
    lines.append("| 축 | 점수 | 비중 | 판정 |")
    lines.append("|------|------|------|------|")

    for a in result.get("axes", []):
        axScore = a.get("score")
        weight = a.get("weight", 0)
        if axScore is None:
            judgment = "데이터 없음"
        elif axScore < 10:
            judgment = "우수"
        elif axScore < 25:
            judgment = "양호"
        elif axScore < 40:
            judgment = "보통"
        elif axScore < 60:
            judgment = "주의"
        else:
            judgment = "위험"

        scoreStr = f"{axScore:.0f}" if axScore is not None else "-"
        lines.append(f"| {a['name']} | {scoreStr} | {weight}% | {judgment} |")

    lines.append("")

    # ── 축별 지표 상세 ──
    lines.append("## 축별 지표")
    lines.append("")

    for a in result.get("axes", []):
        metricsList = a.get("metrics", [])
        if not metricsList:
            continue
        lines.append(f"### {a['name']}")
        lines.append("")
        for m in metricsList:
            s = m.get("score")
            sStr = f"{s:.0f}" if s is not None else "-"
            lines.append(f"- {m['name']}: {sStr}점")
        lines.append("")

    # ── 등급 근거 ──
    lines.append("## 등급 근거")
    lines.append("")

    # 강점
    strengths = [a for a in result.get("axes", []) if a.get("score") is not None and a["score"] < 15]
    if strengths:
        lines.append("**강점:**")
        for a in strengths:
            lines.append(f"- {a['name']}: {a['score']:.0f}점 (우수)")
        lines.append("")

    # 약점
    weaknesses = [a for a in result.get("axes", []) if a.get("score") is not None and a["score"] > 35]
    if weaknesses:
        lines.append("**약점:**")
        for a in weaknesses:
            lines.append(f"- {a['name']}: {a['score']:.0f}점 (주의/위험)")
        lines.append("")

    # ── 면책 ──
    lines.append("---")
    lines.append("")
    lines.append(f"*dartlab 독립 신용평가 ({version}). 공시 데이터 기반 정량 분석.*")
    lines.append(f"*dCR 등급은 제도권 신용등급과 다를 수 있으며, 투자 권유가 아닙니다.*")
    lines.append(f"*생성일: {datetime.now().strftime('%Y-%m-%d')}*")

    return "\n".join(lines)


def toDict(result: dict) -> dict:
    """등급 결과를 JSON-safe dict로 변환."""
    if result is None:
        return {}
    # result 자체가 이미 dict이므로 그대로 반환
    # datetime 등 직렬화 불가 타입이 있으면 여기서 처리
    return result
