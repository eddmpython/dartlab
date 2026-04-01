"""신용평가 보고서 생성 + GitHub 발간.

narrative.py의 서사 + audit.py의 대조 결과를 조합하여
신평사 수준의 마크다운 보고서를 생성하고 docs/credit/reports/에 저장한다.
docs/credit/은 GitHub Pages 공개 대상.
"""

from __future__ import annotations

import gc
from datetime import datetime
from pathlib import Path

_REPORTS_DIR = Path("docs/credit/reports")


def publishReport(stockCode: str, *, basePeriod: str | None = None) -> Path:
    """보고서 생성 + 저장. 반환: 저장된 파일 경로."""
    from dartlab import Company

    company = Company(stockCode)
    path = publishReportFromCompany(company, basePeriod=basePeriod)
    del company
    gc.collect()
    return path


def publishReportFromCompany(company, *, basePeriod: str | None = None) -> Path:
    """Company 객체로 보고서 생성 + 저장."""
    from dartlab.credit.engine import evaluateCompany

    result = evaluateCompany(company, detail=True, basePeriod=basePeriod)
    if result is None:
        raise ValueError("등급 산출 실패: 데이터 부족")

    corpName = getattr(company, "corpName", "") or ""
    stockCode = getattr(company, "stockCode", "") or ""

    md = generateReportMarkdown(corpName, stockCode, result)

    # 저장
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safeName = corpName.replace("/", "_").replace("\\", "_")
    path = _REPORTS_DIR / f"{stockCode}_{safeName}.md"
    path.write_text(md, encoding="utf-8")

    # 등급 이력 기록
    from dartlab.credit.history import recordGrade

    recordGrade(stockCode, result)

    return path


def publishBatch(stockCodes: list[str], *, basePeriod: str | None = None) -> list[Path]:
    """복수 기업 보고서 순차 발간 (메모리 안전)."""
    paths = []
    for code in stockCodes:
        try:
            path = publishReport(code, basePeriod=basePeriod)
            paths.append(path)
        except (ValueError, KeyError, TypeError) as e:
            print(f"[credit] {code} 발간 실패: {e}")
        gc.collect()
    return paths


def generateReportMarkdown(corpName: str, stockCode: str, result: dict) -> str:
    """마크다운 보고서 문자열 생성."""
    from dartlab.credit.audit import auditCredit, auditToMarkdown
    from dartlab.credit.narrative import buildNarratives, buildOverallNarrative

    # 서사 생성
    narratives = buildNarratives(result)
    overallNarrative = buildOverallNarrative(result, narratives)

    # audit 생성
    auditResult = auditCredit(stockCode, corpName, result)

    grade = result.get("grade", "?")
    desc = result.get("gradeDescription", "")
    score = result.get("score", 0)
    pd = result.get("pdEstimate", 0)
    ecr = result.get("eCR", "?")
    outlook = result.get("outlook", "N/A")
    sector = result.get("sector", "")
    version = result.get("methodologyVersion", "v1.0")
    period = result.get("latestPeriod", "")
    category = result.get("gradeCategory", "")
    inv = "투자적격" if result.get("investmentGrade") else "투기등급"
    captive = result.get("captiveFinance", False)
    holding = result.get("holding", False)
    today = datetime.now().strftime("%Y-%m-%d")

    lines = []

    # ── 1. 제목 + 등급 요약 ──
    lines.append(f"# {corpName} ({stockCode}) 신용등급 보고서")
    lines.append(f"> **{grade}** | {desc} | {today} | 방법론 {version}")
    lines.append("")

    lines.append("## 1. 등급 요약")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|------|------|")
    lines.append(f"| **신용등급** | **{grade}** ({desc}) |")
    lines.append(f"| 카테고리 | {category} ({inv}) |")
    lines.append(f"| 종합 점수 | {score:.1f} / 100 |")
    lines.append(f"| 부도확률(1Y) | {pd:.2f}% |")
    lines.append(f"| 현금흐름등급 | {ecr} |")
    lines.append(f"| 등급 전망 | {outlook} |")
    lines.append(f"| 업종 | {sector} |")
    lines.append(f"| 기준 기간 | {period} |")
    if captive:
        lines.append("| 구조 | 캡티브금융 복합기업 (유틸리티 기준 적용) |")
    if holding:
        lines.append("| 구조 | 지주사 |")
    lines.append("")

    # ── 2. 등급 근거 ──
    lines.append("## 2. 등급 근거")
    lines.append("")
    lines.append(overallNarrative)
    lines.append("")

    strengths = [n for n in narratives if n.severity == "strong"]
    weaknesses = [n for n in narratives if n.severity in ("weak", "critical")]
    adequates = [n for n in narratives if n.severity == "adequate"]

    if strengths:
        lines.append("### 강점")
        for n in strengths:
            lines.append(f"- **{n.axisName}**: {n.summary}")
        lines.append("")

    if weaknesses:
        lines.append("### 약점")
        for n in weaknesses:
            lines.append(f"- **{n.axisName}**: {n.summary}")
        lines.append("")

    if adequates:
        lines.append("### 양호")
        for n in adequates:
            lines.append(f"- **{n.axisName}**: {n.summary}")
        lines.append("")

    # ── 3. 7축 상세 분석 ──
    lines.append("## 3. 7축 상세 분석")
    lines.append("")

    # 요약 테이블
    lines.append("| 축 | 점수 | 비중 | 판정 |")
    lines.append("|------|------|------|------|")
    axes = result.get("axes", [])
    for a in axes:
        s = a.get("score")
        sStr = f"{s:.0f}" if s is not None else "-"
        w = a.get("weight", 0)
        if s is None:
            j = "데이터 없음"
        elif s < 10:
            j = "우수"
        elif s < 25:
            j = "양호"
        elif s < 40:
            j = "보통"
        elif s < 60:
            j = "주의"
        else:
            j = "위험"
        lines.append(f"| {a['name']} | {sStr} | {w}% | {j} |")
    lines.append("")

    # 축별 서사 + 지표
    for i, n in enumerate(narratives):
        axData = axes[i] if i < len(axes) else {}
        w = axData.get("weight", 0)
        lines.append(f"### 3.{i + 1} {n.axisName} ({w}%) — {n.severity}")
        lines.append("")
        lines.append(n.summary)
        lines.append("")
        for d in n.details:
            lines.append(f"- {d}")
        lines.append("")

        # 지표 테이블
        metrics = axData.get("metrics", [])
        if metrics:
            lines.append("| 지표 | 점수 |")
            lines.append("|------|------|")
            for m in metrics:
                ms = m.get("score")
                msStr = f"{ms:.0f}" if ms is not None else "-"
                lines.append(f"| {m['name']} | {msStr} |")
            lines.append("")

    # ── 4. 재무 요약 5개년 ──
    history = result.get("metricsHistory", [])
    if history:
        lines.append("## 4. 재무 요약 (5개년)")
        lines.append("")
        cols = ["기간", "EBITDA/이자", "Debt/EBITDA", "부채비율", "유동비율", "OCF/매출"]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["------"] * len(cols)) + "|")
        for h in history[:5]:
            row = [
                h.get("period", ""),
                f"{h['ebitdaInterestCoverage']:.1f}x" if h.get("ebitdaInterestCoverage") is not None else "-",
                f"{h['debtToEbitda']:.1f}x" if h.get("debtToEbitda") is not None else "-",
                f"{h['debtRatio']:.0f}%" if h.get("debtRatio") is not None else "-",
                f"{h['currentRatio']:.0f}%" if h.get("currentRatio") is not None else "-",
                f"{h['ocfToSales']:.1f}%" if h.get("ocfToSales") is not None else "-",
            ]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # ── 5. 등급 전망 + 변경 트리거 ──
    lines.append("## 5. 등급 전망")
    lines.append("")
    lines.append(f"현재 전망: **{outlook}**")
    lines.append("")

    # 상향/하향 트리거 자동 생성
    upTriggers = []
    downTriggers = []
    if history:
        latest = history[0]
        icr = latest.get("ebitdaInterestCoverage")
        if icr is not None and icr < 5:
            upTriggers.append("이자보상배율이 5배 이상으로 개선")
        dr = latest.get("debtRatio")
        if dr is not None and dr > 150:
            upTriggers.append(f"부채비율이 {dr:.0f}%에서 120% 이하로 축소")
        if icr is not None and icr > 3:
            downTriggers.append(f"이자보상배율이 {icr:.1f}배에서 2배 이하로 악화")
        if dr is not None and dr < 250:
            downTriggers.append(f"부채비율이 {dr:.0f}%에서 300% 이상으로 증가")

    if upTriggers:
        lines.append("### 상향 트리거")
        for t in upTriggers:
            lines.append(f"- {t}")
        lines.append("")

    if downTriggers:
        lines.append("### 하향 트리거")
        for t in downTriggers:
            lines.append(f"- {t}")
        lines.append("")

    # ── 6. 신평사 등급 대조 ──
    lines.append(auditToMarkdown(auditResult))
    lines.append("")

    # ── 7. 면책 + 방법론 ──
    lines.append("## 7. 면책 + 방법론")
    lines.append("")
    lines.append(f"- dartlab 독립 신용평가(dCR) {version}")
    lines.append("- 공시 데이터 기반 정량 분석. 비공개 면담/정성 판단 미포함.")
    lines.append("- dCR 등급은 제도권 신용등급과 다를 수 있으며, 투자 권유가 아닙니다.")
    lines.append("- 방법론 상세: [ops/credit.md](../../ops/credit.md)")
    lines.append(f"- 발행일: {today}")
    lines.append("")

    return "\n".join(lines)
