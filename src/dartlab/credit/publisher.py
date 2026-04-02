"""신용평가 보고서 생성 + 블로그 발간.

narrative.py의 서사 + audit.py의 대조 결과를 조합하여
신평사 수준의 마크다운 보고서를 생성하고 blog/04-credit-reports/에 저장한다.
블로그 카테고리로 GitHub Pages 공개.
"""

from __future__ import annotations

import gc
import json
from datetime import datetime
from pathlib import Path

_BLOG_DIR = Path("blog/04-credit-reports")
_REGISTRY_PATH = _BLOG_DIR / "_registry.json"


def publishReport(stockCode: str, *, basePeriod: str | None = None) -> Path:
    """보고서 생성 + 저장. 반환: 저장된 파일 경로."""
    from dartlab import Company

    company = Company(stockCode)
    path = publishReportFromCompany(company, basePeriod=basePeriod)
    del company
    gc.collect()
    return path


def publishReportFromCompany(company, *, basePeriod: str | None = None) -> Path:
    """Company 객체로 보고서 생성 + 블로그 포스트 저장."""
    from dartlab.credit.engine import evaluateCompany

    result = evaluateCompany(company, detail=True, basePeriod=basePeriod)
    if result is None:
        raise ValueError("등급 산출 실패: 데이터 부족")

    corpName = getattr(company, "corpName", "") or ""
    stockCode = getattr(company, "stockCode", "") or ""

    md = generateReportMarkdown(corpName, stockCode, result)

    # 블로그 포스트로 저장
    order, slug = _resolveSlug(stockCode, corpName)
    postDir = _BLOG_DIR / f"{order:02d}-{slug}"
    postDir.mkdir(parents=True, exist_ok=True)
    path = postDir / "index.md"
    path.write_text(md, encoding="utf-8")

    # 등급 이력 기록
    from dartlab.credit.history import recordGrade

    recordGrade(stockCode, result)

    return path


def publishBatch(stockCodes: list[str], *, basePeriod: str | None = None) -> list[Path]:
    """복수 기업 보고서 순차 발간 (메모리 안전)."""
    paths = []
    for i, code in enumerate(stockCodes):
        try:
            path = publishReport(code, basePeriod=basePeriod)
            paths.append(path)
            if (i + 1) % 10 == 0:
                print(f"[credit] {i + 1}/{len(stockCodes)} 발간 완료")
        except (ValueError, KeyError, TypeError, FileNotFoundError) as e:
            print(f"[credit] {code} 발간 실패: {e}")
        gc.collect()
    print(f"[credit] 배치 완료: {len(paths)}/{len(stockCodes)} 성공")
    return paths


def publishAll(*, basePeriod: str | None = None) -> list[Path]:
    """한국 전 상장사 신용평가 보고서 배치 발간.

    blog/04-credit-reports/에 종목별 블로그 포스트 저장.
    메모리 안전: 기업별 순차 처리 + gc.collect().
    finance 데이터가 있는 종목만 발간.

    주의: 2700+ 포스트는 SvelteKit 빌드 시간에 영향.
    당분간 수동 선택 발간(publishBatch) 권장.
    """
    try:
        from dartlab.gather.listing import listing

        df = listing()
        if df is not None and hasattr(df, "to_series"):
            codes = df["종목코드"].to_list() if "종목코드" in df.columns else []
        elif df is not None and hasattr(df, "to_list"):
            codes = df.to_list()
        else:
            codes = []
    except (ImportError, AttributeError, ValueError):
        codes = []

    if not codes:
        print("[credit] 종목 목록을 가져올 수 없습니다.")
        return []

    print(f"[credit] 전종목 발간 시작: {len(codes)}개사")
    return publishBatch(codes, basePeriod=basePeriod)


def _loadRegistry() -> dict:
    """블로그 레지스트리 로드."""
    if _REGISTRY_PATH.exists():
        return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


def _saveRegistry(registry: dict) -> None:
    """블로그 레지스트리 저장."""
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# 주요 종목 영문 slug 매핑 (URL 인코딩 방지)
_SLUG_MAP: dict[str, str] = {
    "005930": "005930-samsung",
    "000660": "000660-sk-hynix",
    "035420": "035420-naver",
    "003550": "003550-lg",
    "005380": "005380-hyundai-motor",
    "010950": "010950-s-oil",
    "105560": "105560-kb-financial",
    "000720": "000720-hyundai-engineering",
    "003230": "003230-samyang-foods",
    "068270": "068270-celltrion",
    "015760": "015760-kepco",
    "000270": "000270-kia",
    "055550": "055550-shinhan",
    "051910": "051910-lg-chem",
    "006400": "006400-samsung-sdi",
    "066570": "066570-lg-electronics",
    "028260": "028260-samsung-c-and-t",
    "034730": "034730-sk",
    "036570": "036570-ncsoft",
    "017670": "017670-sk-telecom",
}


def _resolveSlug(stockCode: str, corpName: str) -> tuple[int, str]:
    """종목코드에 대한 블로그 순서번호와 slug 반환."""
    registry = _loadRegistry()

    if stockCode in registry:
        entry = registry[stockCode]
        return entry["order"], entry["slug"]

    # 새 종목: slug 결정
    slug = _SLUG_MAP.get(stockCode, f"{stockCode}-credit")
    order = max((v["order"] for v in registry.values()), default=0) + 1

    registry[stockCode] = {"order": order, "slug": slug}
    _saveRegistry(registry)
    return order, slug


def _generateFrontmatter(corpName: str, stockCode: str, result: dict) -> str:
    """블로그 포스트 frontmatter 생성."""
    today = datetime.now().strftime("%Y-%m-%d")
    grade = result.get("grade", "?")
    desc = result.get("gradeDescription", "")

    # description에 따옴표 이스케이프
    descText = (
        f"{corpName} 독립 신용등급 {grade} ({desc}). 공시 데이터 기반 정량 분석 등급 근거, 재무 하이라이트, 등급 전망."
    )

    return "\n".join(
        [
            "---",
            f'title: "{corpName} ({stockCode}) 신용평가 보고서"',
            f"date: {today}",
            f'description: "{descText}"',
            "category: credit-reports",
            "thumbnail: /avatar-chart.png",
            "---",
            "",
        ]
    )


def _gauge(score: float | None, width: int = 10) -> str:
    """점수를 시각적 게이지 바로 변환."""
    if score is None:
        return "░" * width
    filled = max(0, min(width, int((100 - score) / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def _trend(cur, prev) -> str:
    """전기 대비 변화 방향 화살표."""
    if cur is None or prev is None:
        return ""
    if cur < prev * 0.95:
        return " ↓"
    if cur > prev * 1.05:
        return " ↑"
    return " →"


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

    # ── frontmatter (블로그 포스트) ──
    lines.append(_generateFrontmatter(corpName, stockCode, result))

    # ── 1. 등급 요약 ──
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

    # ── 2. 기업 개요 ──
    narrativesDict = result.get("narratives", {})
    profileNarr = narrativesDict.get("profile", "")
    if profileNarr:
        lines.append("## 2. 기업 개요")
        lines.append("")
        lines.append(profileNarr)
        lines.append("")

    # ── 3. 재무 하이라이트 ──
    history = result.get("metricsHistory", [])
    if history:
        from dartlab.credit.narrative import _fmtTril

        h0 = history[0]
        h1 = history[1] if len(history) > 1 else {}

        lines.append("## 3. 재무 하이라이트")
        lines.append("")

        rev0 = h0.get("revenue")
        oi0 = h0.get("operatingIncome")
        ebitda0 = h0.get("ebitda")
        ocf0 = h0.get("ocf")
        netDebt0 = h0.get("netDebt")

        if rev0 is not None:
            revPrev = h1.get("revenue")
            yoy = ""
            if revPrev and revPrev > 0:
                chg = (rev0 - revPrev) / abs(revPrev) * 100
                yoy = f" (전년비 {'+' if chg > 0 else ''}{chg:.0f}%)"
            lines.append(f"- **매출**: {_fmtTril(rev0)}{yoy}")

        if oi0 is not None:
            oiPrev = h1.get("operatingIncome")
            yoy = ""
            if oiPrev and oiPrev != 0:
                chg = (oi0 - oiPrev) / abs(oiPrev) * 100
                yoy = f" (전년비 {'+' if chg > 0 else ''}{chg:.0f}%)"
            lines.append(f"- **영업이익**: {_fmtTril(oi0)}{yoy}")

        if ebitda0 is not None:
            lines.append(f"- **EBITDA**: {_fmtTril(ebitda0)}")

        if ocf0 is not None:
            lines.append(f"- **영업현금흐름**: {_fmtTril(ocf0)}")

        if netDebt0 is not None:
            if netDebt0 <= 0:
                lines.append("- **순차입금**: 순현금 포지션 (현금이 차입금 초과)")
            else:
                lines.append(f"- **순차입금**: {_fmtTril(netDebt0)}")

        # 추세 해석
        trendNarr = narrativesDict.get("trend", "")
        if trendNarr:
            lines.append(f"- **추세**: {trendNarr}")

        # 차입금 구성
        borrowNarr = narrativesDict.get("borrowings", "")
        if borrowNarr:
            lines.append(f"- **차입금 구성**: {borrowNarr}")

        lines.append("")

    # ── 4. 등급 근거 ──
    lines.append("## 4. 등급 근거")
    lines.append("")
    lines.append(overallNarrative)
    lines.append("")

    # 6막 인과 연결
    causalChain = narrativesDict.get("causalChain", "")
    if causalChain:
        lines.append(f"**{causalChain}**")
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
    lines.append("## 5. 7축 상세 분석")
    lines.append("")

    # 요약 테이블 (게이지 바 포함)
    axes = result.get("axes", [])
    lines.append("| 축 | 비중 | 판정 | 점수 |")
    lines.append("|------|:---:|:---:|------|")
    for a in axes:
        s = a.get("score")
        w = a.get("weight", 0)
        if s is None:
            j, gauge = "-", _gauge(None)
        elif s < 10:
            j, gauge = "**우수**", _gauge(s)
        elif s < 25:
            j, gauge = "양호", _gauge(s)
        elif s < 40:
            j, gauge = "보통", _gauge(s)
        elif s < 60:
            j, gauge = "⚠ 주의", _gauge(s)
        else:
            j, gauge = "🔴 위험", _gauge(s)
        sStr = f"{s:.0f}/100" if s is not None else "평가 불가"
        lines.append(f"| {a['name']} | {w}% | {j} | {gauge} {sStr} |")
    lines.append("")

    # 축별 서사 (문단 + 지표 테이블)
    for i, n in enumerate(narratives):
        axData = axes[i] if i < len(axes) else {}
        w = axData.get("weight", 0)
        s = axData.get("score")
        lines.append(f"### 5.{i + 1} {n.axisName} ({w}%)")
        lines.append("")
        if s is not None:
            lines.append(f"**판정: {n.severityKr}** ({s:.0f}점/100)")
        else:
            lines.append(f"**판정: {n.severityKr}** (평가 불가)")
        lines.append("")
        # 문단 서사 (bullet이 아닌 연결된 텍스트)
        lines.append(n.toParagraph())
        lines.append("")

        # 지표 테이블 (값 + 점수 + 판정)
        metricsList = axData.get("metrics", [])
        if metricsList:
            lines.append("| 지표 | 점수 | 판정 |")
            lines.append("|------|:---:|:---:|")
            for m in metricsList:
                ms = m.get("score")
                msStr = f"{ms:.0f}" if ms is not None else "-"
                if ms is None:
                    mj = "-"
                elif ms < 10:
                    mj = "우수"
                elif ms < 30:
                    mj = "양호"
                elif ms < 50:
                    mj = "보통"
                else:
                    mj = "주의"
                lines.append(f"| {m['name']} | {msStr} | {mj} |")
            lines.append("")

    # ── 5. 재무 요약 5개년 ──
    if history:
        lines.append("## 6. 재무 요약 (5개년)")
        lines.append("")
        cols = ["기간", "EBITDA/이자", "Debt/EBITDA", "부채비율", "유동비율", "OCF/매출"]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["------"] * len(cols)) + "|")
        histSlice = history[:5]
        for idx, h in enumerate(histSlice):
            prevH = histSlice[idx + 1] if idx + 1 < len(histSlice) else None

            icr = h.get("ebitdaInterestCoverage")
            de = h.get("debtToEbitda")
            dr = h.get("debtRatio")
            cr_v = h.get("currentRatio")
            ocfS = h.get("ocfToSales")

            icrStr = "무차입" if icr is not None and icr >= 100 else (f"{icr:.1f}x" if icr is not None else "-")
            deStr = f"{de:.1f}x" if de is not None else "-"
            drStr = f"{dr:.0f}%" if dr is not None else "-"
            crStr = f"{cr_v:.0f}%" if cr_v is not None else "-"
            ocfStr = f"{ocfS:.1f}%" if ocfS is not None else "-"

            # 변화 방향 화살표
            if prevH:
                deStr += _trend(de, prevH.get("debtToEbitda"))
                drStr += _trend(dr, prevH.get("debtRatio"))
                crStr += _trend(cr_v, prevH.get("currentRatio"))

            row = [h.get("period", ""), icrStr, deStr, drStr, crStr, ocfStr]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # ── 5. 등급 전망 + 변경 트리거 ──
    lines.append("## 7. 등급 전망")
    lines.append("")
    lines.append(f"현재 전망: **{outlook}**")
    lines.append("")

    # 상향/하향 트리거 자동 생성 — 현실적 조건만
    upTriggers = []
    downTriggers = []
    if history:
        latestH = history[0]
        icr = latestH.get("ebitdaInterestCoverage")
        dr = latestH.get("debtRatio")
        de = latestH.get("debtToEbitda")
        oi = latestH.get("operatingIncome")

        # 상향 트리거
        if icr is not None and icr < 5:
            upTriggers.append("이자보상배율이 5배 이상으로 개선")
        if dr is not None and dr > 100:
            upTriggers.append(f"부채비율이 현 {dr:.0f}%에서 80% 이하로 축소")
        if de is not None and de > 3:
            upTriggers.append(f"Debt/EBITDA가 현 {de:.1f}배에서 2배 이하로 개선")
        if oi is not None and oi < 0:
            upTriggers.append("영업이익 흑자 전환")

        # 하향 트리거 — 현 수준의 1.5~2배 악화를 기준으로
        if icr is not None and 3 < icr < 100:
            downTriggers.append(f"이자보상배율이 현 {icr:.1f}배에서 2배 이하로 악화")
        elif icr is not None and icr >= 100:
            downTriggers.append("대규모 차입으로 이자보상배율이 5배 이하로 하락")

        if dr is not None:
            # 현 수준의 2배 또는 +50%p 중 현실적인 것
            threshold = min(dr * 2, dr + 50) if dr > 30 else 100
            downTriggers.append(f"부채비율이 현 {dr:.0f}%에서 {threshold:.0f}% 이상으로 증가")

        if de is not None and de < 3:
            downTriggers.append(f"Debt/EBITDA가 현 {de:.1f}배에서 5배 이상으로 악화")

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
    lines.append("## 9. 면책 + 방법론")
    lines.append("")
    lines.append(f"- dartlab 독립 신용평가(dCR) {version}")
    lines.append("- 공시 데이터 기반 정량 분석. 비공개 면담/정성 판단 미포함.")
    lines.append("- dCR 등급은 제도권 신용등급과 다를 수 있으며, 투자 권유가 아닙니다.")
    lines.append("- 방법론 상세: [ops/credit.md](https://github.com/eddmpython/dartlab/blob/master/ops/credit.md)")
    lines.append(f"- 발행일: {today}")
    lines.append("")

    return "\n".join(lines)
