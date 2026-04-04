"""신용분석 보고서 생성 + 블로그 발간.

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
    """한국 전 상장사 신용분석 보고서 배치 발간.

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
            f'title: "{corpName} ({stockCode}) 신용분석 보고서"',
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


def _generateAIAnalysis(corpName: str, stockCode: str, result: dict, narratives, overallNarrative: str) -> str | None:
    """AI로 신용분석 종합 해석 생성. 실패 시 None."""
    try:
        from dartlab.ai.runtime.standalone import ask
    except ImportError:
        return None

    grade = result.get("grade", "?")
    healthScore = 100 - result.get("score", 50)
    history = result.get("metricsHistory", [])
    sector = result.get("sector", "")

    axesSummary = "\n".join(f"- [{n.severity}] {n.axisName}: {n.summary}" for n in narratives)
    histLines = []
    for h in history[:3]:
        icr = h.get("ebitdaInterestCoverage")
        icrStr = "무차입" if icr is not None and icr >= 100 else (f"{icr:.1f}" if icr is not None else "-")
        de = h.get("debtToEbitda")
        dr = h.get("debtRatio")
        histLines.append(
            f"{h.get('period', '')}: ICR={icrStr}, "
            f"D/EBITDA={f'{de:.1f}' if de is not None else '-'}, "
            f"부채비율={f'{dr:.0f}%' if dr is not None else '-'}"
        )
    histSummary = "\n".join(histLines)

    prompt = (
        f"{corpName}({stockCode}, {sector}) 신용등급 {grade}, 건전도 {healthScore}/100.\n\n"
        f"기계 생성 요약:\n{overallNarrative}\n\n"
        f"7축 분석:\n{axesSummary}\n\n"
        f"최근 지표:\n{histSummary}\n\n"
        "위 분석을 바탕으로 이 기업의 신용건전성을 3~4문단으로 전문적으로 해석해줘.\n"
        "- 기존 서사를 복사하지 말고 네 판단으로 다시 써라\n"
        "- 산업 맥락과 경쟁 위치를 반영\n"
        "- 인과 체인: 매출→이익→현금→안정성→등급 흐름으로\n"
        "- 핵심 강점 2개, 핵심 리스크 1~2개 부각\n"
        "- 마크다운 헤딩(#, ##) 사용하지 마라. 본문 문단만 써라\n"
        "- 코드(python, print 등) 절대 쓰지 마라. 순수 텍스트만\n"
        "- 불릿(-) 사용 가능하지만 본문 문단 위주로\n"
    )

    try:
        raw = ask(prompt, stream=False)
        if not isinstance(raw, str):
            return None
        # AI 출력에서 코드블록 제거 (```...``` 사이)
        import re

        cleaned = re.sub(r"```[\s\S]*?```", "", raw).strip()
        # print() 등 코드 라인 제거
        lines_out = [
            ln for ln in cleaned.split("\n") if not ln.strip().startswith(("print(", "import ", "from ", ">>>"))
        ]
        return "\n".join(lines_out).strip() or None
    except (ImportError, ValueError, KeyError, TypeError, RuntimeError, OSError):
        return None


def _fmtTril(value: float | None) -> str:
    """금액을 조/억 단위로 포맷."""
    if value is None:
        return "N/A"
    absV = abs(value)
    sign = "-" if value < 0 else ""
    if absV >= 1e12:
        return f"{sign}{absV / 1e12:.1f}조"
    if absV >= 1e8:
        return f"{sign}{absV / 1e8:,.0f}억"
    return f"{sign}{absV:,.0f}"


def _renderHealthBar(healthScore: float) -> str:
    """건전도 ASCII 바."""
    barLen = 20
    filled = int(max(0.0, min(100.0, healthScore)) / 100 * barLen)
    return f"건전도: [{'█' * filled}{'░' * (barLen - filled)}] {healthScore:.0f}/100"


def _renderExecutiveSummary(narrativesDict: dict, result: dict) -> list[str]:
    """2~3문단 핵심 요약. narratives["overall"] + causalChain."""
    lines: list[str] = []
    overall = narrativesDict.get("overall", "")
    causal = narrativesDict.get("causalChain", "")
    if not overall and not causal:
        return lines

    lines.append("## 2. Executive Summary")
    lines.append("")
    if overall:
        lines.append(overall)
        lines.append("")
    if causal:
        lines.append(f"**인과 연결**: {causal}")
        lines.append("")
    return lines


def _renderCompanyOverview(
    profile: dict | None,
    rank: dict | None,
    segComp: dict | None,
    sector: str,
) -> list[str]:
    """기업 개요 multi-line."""
    lines: list[str] = []
    parts: list[str] = []

    # 업종/섹터
    if profile:
        sectorText = profile.get("sector", "")
        if sectorText:
            parts.append(sectorText)
        products = profile.get("products", "")
        if products:
            parts.append(products)
    if not parts and sector:
        parts.append(f"업종: {sector}")

    # 매출 규모 + 업종 내 순위
    if rank:
        revRankSector = rank.get("revenueRankInSector")
        revSectorTotal = rank.get("revenueSectorTotal")
        sizeClass = rank.get("sizeClass", "")
        indGroup = rank.get("industryGroup", "")

        rankParts: list[str] = []
        if sizeClass:
            rankParts.append(f"규모: {sizeClass}")
        if indGroup:
            rankParts.append(f"업종그룹: {indGroup}")
        if revRankSector is not None and revSectorTotal is not None:
            rankParts.append(f"업종 내 매출 순위: {revRankSector}/{revSectorTotal}위")
        elif revRankSector is not None:
            rankParts.append(f"업종 내 매출 순위: {revRankSector}위")
        if rankParts:
            parts.append(", ".join(rankParts))

    # 최신 매출 규모
    if segComp:
        totalRev = segComp.get("totalRevenue")
        if totalRev is not None:
            parts.append(f"총 매출: {_fmtTril(totalRev)}")

    if not parts:
        return lines

    lines.append("### 3.1 기업 개요")
    lines.append("")
    for p in parts:
        lines.append(f"- {p}")
    lines.append("")
    return lines


def _renderSegmentTable(segComp: dict | None) -> list[str]:
    """부문별 매출 비중 GFM 테이블. 중복 부문명 제거."""
    if segComp is None:
        return []
    segments = segComp.get("segments", [])
    totalRev = segComp.get("totalRevenue")
    if not segments or not totalRev:
        return []

    # 중복 부문명 제거 (최신 값 우선)
    seen: dict[str, float] = {}
    for seg in segments:
        name = seg.get("name", "").replace(" 부문", "").strip()
        rev = seg.get("revenue", 0)
        if name and rev > 0 and name not in seen:
            seen[name] = rev

    if not seen:
        return []

    # 비중 기준 내림차순
    total = sum(seen.values())
    items = sorted(seen.items(), key=lambda x: -x[1])

    lines: list[str] = []
    lines.append("### 3.2 부문별 매출 구성")
    lines.append("")
    lines.append("| 부문 | 비중 |")
    lines.append("|------|-----:|")
    for name, rev in items:
        pct = rev / total * 100
        lines.append(f"| {name} | {pct:.1f}% |")
    lines.append("")
    return lines


def _renderHHI(businessStability: dict | None) -> list[str]:
    """매출 집중도 HHI + 해석."""
    if businessStability is None:
        return []
    hhi = businessStability.get("segmentHHI")
    if hhi is None:
        return []

    lines: list[str] = []
    lines.append("### 3.3 매출 집중도")
    lines.append("")
    lines.append(f"- HHI (허핀달-허쉬만 지수): **{hhi:,.0f}**")

    if hhi >= 8000:
        lines.append("- 해석: 매출이 단일 부문에 극도로 집중. 해당 부문의 업황 변동이 실적을 직접 좌우한다.")
    elif hhi >= 5000:
        lines.append("- 해석: 높은 집중도. 주력 부문 의존도가 크며 사업 다각화가 제한적이다.")
    elif hhi >= 2500:
        lines.append("- 해석: 중간 집중도. 복수 사업부가 존재하나 특정 부문 비중이 높다.")
    else:
        lines.append("- 해석: 낮은 집중도. 사업 다각화가 잘 되어 있어 부문별 리스크가 분산된다.")
    lines.append("")
    return lines


def _renderPeerComparison(result: dict) -> list[str]:
    """동종업계 정보 (rank 데이터 기반). scan 호출 없이 result["rank"]만 사용."""
    rank = result.get("rank")
    if rank is None:
        return []

    lines: list[str] = []
    lines.append("## 7. 피어 비교")
    lines.append("")

    revRank = rank.get("revenueRank")
    revTotal = rank.get("revenueTotal")
    revRankSector = rank.get("revenueRankInSector")
    revSectorTotal = rank.get("revenueSectorTotal")
    sizeClass = rank.get("sizeClass", "")
    indGroup = rank.get("industryGroup", "")
    sector = rank.get("sector", "")

    lines.append("| 항목 | 값 |")
    lines.append("|------|------|")
    if sector:
        lines.append(f"| 섹터 | {sector} |")
    if indGroup:
        lines.append(f"| 업종그룹 | {indGroup} |")
    if sizeClass:
        lines.append(f"| 규모 분류 | {sizeClass} |")
    if revRank is not None and revTotal is not None:
        lines.append(f"| 전체 매출 순위 | {revRank} / {revTotal} |")
    if revRankSector is not None and revSectorTotal is not None:
        lines.append(f"| 업종 내 매출 순위 | {revRankSector} / {revSectorTotal} |")
    lines.append("")

    # 순위 해석
    if revRankSector is not None and revSectorTotal is not None and revSectorTotal > 0:
        percentile = revRankSector / revSectorTotal * 100
        if percentile <= 10:
            lines.append(f"업종 내 상위 {percentile:.0f}%에 위치하며, 시장 지배적 지위를 보유한다.")
        elif percentile <= 25:
            lines.append(f"업종 내 상위 {percentile:.0f}%로, 주요 플레이어에 해당한다.")
        elif percentile <= 50:
            lines.append(f"업종 내 상위 {percentile:.0f}%로, 중위권에 위치한다.")
        else:
            lines.append(f"업종 내 상위 {percentile:.0f}%로, 소형/후발 기업에 해당한다.")
        lines.append("")

    return lines


def generateReportMarkdown(
    corpName: str,
    stockCode: str,
    result: dict,
    *,
    auditResult=None,
    aiAnalysis: str | None = None,
) -> str:
    """마크다운 보고서 문자열 생성.

    13섹션 구조:
    1. 등급 요약 + 건전도 바
    2. Executive Summary
    3. 사업 분석 (개요, 부문별 매출, 집중도)
    4. 등급 근거 상세
    5. 재무 분석 (7축/5축 상세)
    6. 5개년 재무 시계열
    7. 피어 비교
    8. 등급 전망 + 트리거
    9. 신평사 등급 대조
    10. 등급 괴리 분석
    11. Notch Adjustment 상세
    12. 별도재무제표 비교
    13. 면책 + 방법론
    """
    from dartlab.credit.audit import auditCredit, auditToMarkdown
    from dartlab.credit.narrative import buildNarratives, buildOverallNarrative

    # 서사 생성
    narratives = buildNarratives(result)
    overallNarrative = buildOverallNarrative(result, narratives)

    # audit 생성 (외부 전달 우선)
    if auditResult is None:
        auditResult = auditCredit(stockCode, corpName, result)

    grade = result.get("grade", "?")
    desc = result.get("gradeDescription", "")
    score = result.get("score", 0)
    healthScore = max(0.0, 100.0 - score)
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
    narrativesDict = result.get("narratives", {})
    history = result.get("metricsHistory", [])

    lines: list[str] = []

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

    # 건전도 바
    lines.append(f"```\n{_renderHealthBar(healthScore)}\n```")
    lines.append("")

    # ── 2. Executive Summary ──
    lines.extend(_renderExecutiveSummary(narrativesDict, result))

    # ── 3. 사업 분석 ──
    profile = result.get("profile")
    rank = result.get("rank")
    segComp = result.get("segmentComposition")
    bizStab = result.get("businessStability")

    overviewLines = _renderCompanyOverview(profile, rank, segComp, sector)
    segmentLines = _renderSegmentTable(segComp)
    hhiLines = _renderHHI(bizStab)

    if overviewLines or segmentLines or hhiLines:
        lines.append("## 3. 사업 분석")
        lines.append("")
        lines.extend(overviewLines)
        lines.extend(segmentLines)
        lines.extend(hhiLines)

    # ── 4. 등급 근거 상세 ──
    lines.append("## 4. 등급 근거 상세")
    lines.append("")

    # AI 분석 (외부 전달 우선 → 자체 생성 시도 → 기계 서사 fallback)
    if aiAnalysis:
        lines.append(aiAnalysis)
    else:
        generatedAi = _generateAIAnalysis(corpName, stockCode, result, narratives, overallNarrative)
        if generatedAi:
            lines.append(generatedAi)
        else:
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

    # ── 5. 재무 분석 (7축/5축 상세) ──
    lines.append("## 5. 재무 분석")
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
            j, gauge = "주의", _gauge(s)
        else:
            j, gauge = "위험", _gauge(s)
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

    # ── 6. 5개년 재무 시계열 ──
    if history:
        lines.append("## 6. 5개년 재무 시계열")
        lines.append("")
        cols = ["기간", "매출", "영업이익", "EBITDA/이자", "Debt/EBITDA", "부채비율", "유동비율", "OCF/매출"]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["------"] * len(cols)) + "|")
        histSlice = history[:5]
        for idx, h in enumerate(histSlice):
            prevH = histSlice[idx + 1] if idx + 1 < len(histSlice) else None

            rev = h.get("revenue")
            oi = h.get("operatingIncome")
            icr = h.get("ebitdaInterestCoverage")
            de = h.get("debtToEbitda")
            dr = h.get("debtRatio")
            cr_v = h.get("currentRatio")
            ocfS = h.get("ocfToSales")

            revStr = _fmtTril(rev) if rev is not None else "-"
            oiStr = _fmtTril(oi) if oi is not None else "-"
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

            row = [h.get("period", ""), revStr, oiStr, icrStr, deStr, drStr, crStr, ocfStr]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # ── 7. 피어 비교 ──
    lines.extend(_renderPeerComparison(result))

    # ── 8. 등급 전망 + 트리거 ──
    lines.append("## 8. 등급 전망")
    lines.append("")
    lines.append(f"현재 전망: **{outlook}**")
    lines.append("")

    # 상향/하향 트리거 자동 생성 — 현실적 조건만
    upTriggers: list[str] = []
    downTriggers: list[str] = []
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

    # ── 9. 신평사 등급 대조 ──
    lines.append(auditToMarkdown(auditResult, sectionNum=9))
    lines.append("")

    # ── 10. 등급 괴리 분석 ──
    divExpl = result.get("divergenceExplanation", [])
    matchExpl = result.get("matchExplanation", [])
    if divExpl or matchExpl:
        lines.append("## 10. 등급 괴리 분석")
        lines.append("")
        if divExpl:
            lines.append("dartlab dCR 등급이 외부 신평사 등급과 다를 수 있는 이유:")
            lines.append("")
            for d in divExpl:
                lines.append(f"- {d}")
            lines.append("")
        if matchExpl:
            lines.append("dCR 등급과 외부 등급이 일치하는 이유:")
            lines.append("")
            for m in matchExpl:
                lines.append(f"- {m}")
            lines.append("")
    elif divExpl:
        lines.append("## 10. 등급 괴리 분석")
        lines.append("")
        lines.append("dartlab dCR 등급이 외부 신평사 등급과 다를 수 있는 이유:")
        lines.append("")
        for d in divExpl:
            lines.append(f"- {d}")
        lines.append("")

    # ── 11. Notch Adjustment 상세 ──
    notchAdj = result.get("notchAdjustment")
    if notchAdj and notchAdj.get("totalNotch", 0) > 0:
        lines.append("## 11. Notch Adjustment 상세")
        lines.append("")
        lines.append(f"총 조정: **-{notchAdj['totalNotch']} notch (상향)**")
        lines.append("")
        lines.append("적용 규칙:")
        for r in notchAdj.get("reasons", []):
            lines.append(f"- {r}")
        lines.append("")

    # ── 12. 별도재무제표 비교 ──
    sepMetrics = result.get("separateMetrics")
    if sepMetrics:
        lines.append("## 12. 별도재무제표 비교")
        lines.append("")
        lines.append("연결 재무제표에 자회사 부채가 포함되어 왜곡될 수 있으므로, 별도(모회사) 재무를 함께 확인합니다.")
        lines.append("")
        latest = history[0] if history else {}
        lines.append("| 지표 | 연결 | 별도 |")
        lines.append("| --- | ---: | ---: |")
        conDE = latest.get("debtToEbitda")
        sepDE = sepMetrics.get("separateDebtToEbitda")
        conDR = latest.get("debtRatio")
        sepDR = sepMetrics.get("separateDebtRatio")
        lines.append(f"| D/EBITDA | {conDE:.1f}x | {sepDE:.1f}x |" if conDE and sepDE else "| D/EBITDA | - | - |")
        lines.append(f"| 부채비율 | {conDR:.0f}% | {sepDR:.0f}% |" if conDR and sepDR else "| 부채비율 | - | - |")
        conBorrow = latest.get("totalBorrowing")
        sepBorrow = sepMetrics.get("totalBorrowing")
        if conBorrow and sepBorrow:
            lines.append(f"| 총차입금 | {_fmtTril(conBorrow)} | {_fmtTril(sepBorrow)} |")
        lines.append("")

    # ── 13. 면책 + 방법론 ──
    lines.append("## 13. 면책 + 방법론")
    lines.append("")
    lines.append(f"- dartlab 독립 신용분석(dCR) {version}")
    lines.append("- 공시 데이터 기반 정량 분석. 비공개 면담/정성 판단 미포함.")
    lines.append("- dCR 등급은 제도권 신용등급과 다를 수 있으며, 투자 권유가 아닙니다.")
    lines.append("- 방법론 상세: [ops/credit.md](https://github.com/eddmpython/dartlab/blob/master/ops/credit.md)")
    lines.append(f"- 발행일: {today}")
    lines.append("")

    return "\n".join(lines)
