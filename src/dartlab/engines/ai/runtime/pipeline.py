"""분석 파이프라인 — LLM 호출 전 자동 pre-computation.

질문을 분류하고, 결정론적으로 분석 도구를 실행하여
pre-computed 결과를 LLM context에 추가한다.

Tier 1 아키텍처:
  - 기존: docs/finance 기반 ratio_table, anomaly 등
  - 추가: L2 엔진(sector, insight, rank) 결과를 분석 패키지로 주입
  - 모든 provider에서 동작 (tool calling 불필요)
"""

from __future__ import annotations

import logging
from typing import Any

import polars as pl

from dartlab.engines.ai.conversation.prompts import _classify_question

_log = logging.getLogger(__name__)
_PIPELINE_ERRORS = (
    AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError,
    pl.exceptions.PolarsError,
)


def classify_question(question: str) -> str:
    """질문을 유형별로 분류.

    Returns:
            "건전성" | "수익성" | "성장성" | "배당" | "지배구조" | "리스크" | "종합"
    """
    result = _classify_question(question)
    return result or "종합"


def run_pipeline(company: Any, question: str, included_tables: list[str]) -> str:
    """질문 유형에 따라 pre-computation 실행.

    Returns:
            추가 context 문자열 (마크다운). 빈 문자열이면 추가 context 없음.
    """
    q_type = classify_question(question)

    runners = _PIPELINE_MAP.get(q_type, [])
    sections: list[str] = []
    for runner in runners:
        try:
            result = runner(company, included_tables)
            if result:
                sections.append(result)
        except _PIPELINE_ERRORS:
            continue

    try:
        l2 = _run_l2_engines(company, q_type)
    except _PIPELINE_ERRORS:
        l2 = None
    if l2:
        sections.append(l2)

    if not sections:
        return ""
    return "\n\n## 자동 분석 결과\n\n" + "\n\n".join(sections)


# ══════════════════════════════════════
# 유형별 파이프라인
# ══════════════════════════════════════


def _df_to_simple_md(df: pl.DataFrame, max_rows: int = 10) -> str:
    """간단한 DataFrame → 마크다운 변환."""
    if df is None or df.height == 0:
        return ""

    display = df.head(max_rows)
    cols = display.columns
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for row in display.iter_rows():
        cells = []
        for val in row:
            if val is None:
                cells.append("-")
            elif isinstance(val, float):
                cells.append(f"{val:,.1f}" if abs(val) >= 1 else f"{val:.4f}")
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, sep] + rows)


def _run_health_analysis(company: Any, tables: list[str]) -> str | None:
    """재무건전성: ratio_table + anomaly detection."""
    from dartlab.engines.ai.aiParser import detect_anomalies
    from dartlab.tools.table import ratio_table

    bs = getattr(company, "BS", None)
    is_ = getattr(company, "IS", None)
    if not isinstance(bs, pl.DataFrame) or not isinstance(is_, pl.DataFrame):
        return None

    parts: list[str] = []

    # 재무비율 계산
    ratios = ratio_table(bs, is_)
    if ratios.height > 0:
        parts.append("### 핵심 재무비율")
        parts.append(_df_to_simple_md(ratios))

    # 이상치 탐지 (BS)
    anomalies = detect_anomalies(bs, use_llm=False, threshold_pct=50.0)
    if anomalies:
        parts.append("### BS 이상치")
        for a in anomalies[:5]:
            parts.append(f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)")

    return "\n".join(parts) if parts else None


def _run_profitability_analysis(company: Any, tables: list[str]) -> str | None:
    """수익성: IS 피벗 + YoY + 요약통계."""
    from dartlab.tools.table import pivot_accounts, summary_stats, yoy_change

    is_ = getattr(company, "IS", None)
    if not isinstance(is_, pl.DataFrame):
        return None

    parts: list[str] = []

    # IS 피벗 → year | 매출액 | 영업이익 | ...
    pivoted = pivot_accounts(is_)
    if "year" not in pivoted.columns:
        return None

    # 핵심 수익성 지표 YoY
    target_cols = [c for c in pivoted.columns if c in ("매출액", "영업이익", "당기순이익")]
    if target_cols:
        yoy = yoy_change(pivoted, value_cols=target_cols)
        if yoy.height > 0:
            parts.append("### 수익성 YoY 변동")
            parts.append(_df_to_simple_md(yoy))

    # 요약통계
    stats = summary_stats(pivoted)
    if stats.height > 0:
        parts.append("### 수익성 요약")
        parts.append(_df_to_simple_md(stats))

    return "\n".join(parts) if parts else None


def _run_growth_analysis(company: Any, tables: list[str]) -> str | None:
    """성장성: growth_matrix."""
    from dartlab.tools.table import growth_matrix, pivot_accounts

    is_ = getattr(company, "IS", None)
    if not isinstance(is_, pl.DataFrame):
        return None

    parts: list[str] = []

    pivoted = pivot_accounts(is_)
    if "year" not in pivoted.columns:
        return None

    target_cols = [c for c in pivoted.columns if c in ("매출액", "영업이익", "당기순이익")]
    if target_cols:
        gm = growth_matrix(pivoted, value_cols=target_cols)
        if gm.height > 0:
            parts.append("### 성장률 매트릭스 (CAGR)")
            parts.append(_df_to_simple_md(gm))

    return "\n".join(parts) if parts else None


def _run_dividend_analysis(company: Any, tables: list[str]) -> str | None:
    """배당: dividend 데이터 YoY + 요약통계."""
    from dartlab.tools.table import summary_stats, yoy_change

    div = getattr(company, "dividend", None)
    if not isinstance(div, pl.DataFrame) or div.height == 0:
        return None

    parts: list[str] = []

    # DPS 등 배당 지표 YoY
    numeric_cols = [
        c for c in div.columns if c != "year" and div[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]
    if numeric_cols:
        yoy = yoy_change(div, value_cols=numeric_cols)
        if yoy.height > 0:
            parts.append("### 배당 지표 YoY 변동")
            parts.append(_df_to_simple_md(yoy))

        stats = summary_stats(div)
        if stats.height > 0:
            parts.append("### 배당 요약")
            parts.append(_df_to_simple_md(stats))

    return "\n".join(parts) if parts else None


def _run_risk_analysis(company: Any, tables: list[str]) -> str | None:
    """리스크: 주요 테이블 이상치 탐지."""
    from dartlab.engines.ai.aiParser import detect_anomalies

    parts: list[str] = []
    checked_modules = ["BS", "IS", "CF"]

    for mod_name in checked_modules:
        data = getattr(company, mod_name, None)
        if not isinstance(data, pl.DataFrame):
            continue

        anomalies = detect_anomalies(data, use_llm=False, threshold_pct=40.0)
        if anomalies:
            parts.append(f"### {mod_name} 이상치")
            for a in anomalies[:5]:
                parts.append(f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)")

    return "\n".join(parts) if parts else None


def _run_quality_of_earnings(company: Any, tables: list[str]) -> str | None:
    """이익의 질: 영업CF/순이익, CCC 분석."""
    from dartlab.engines.ai.context.company_adapter import get_headline_ratios

    ratios = get_headline_ratios(company)
    if ratios is None:
        return None

    parts: list[str] = []
    cfni = getattr(ratios, "operatingCfToNetIncome", None)
    ccc = getattr(ratios, "ccc", None)
    dso = getattr(ratios, "dso", None)
    dio = getattr(ratios, "dio", None)
    dpo = getattr(ratios, "dpo", None)
    capex_ratio = getattr(ratios, "capexRatio", None)

    if cfni is not None or ccc is not None:
        parts.append("### 이익의 질 분석")
        rows = ["| 지표 | 값 | 판단 |", "| --- | --- | --- |"]
        if cfni is not None:
            q = "양호" if cfni >= 100 else ("보통" if cfni >= 50 else "주의")
            rows.append(f"| 영업CF/순이익 | {cfni:.0f}% | {q} |")
        if ccc is not None:
            rows.append(f"| CCC(현금전환주기) | {ccc:.0f}일 | - |")
        if dso is not None:
            rows.append(f"| DSO(매출채권회수) | {dso:.0f}일 | - |")
        if dio is not None:
            rows.append(f"| DIO(재고보유) | {dio:.0f}일 | - |")
        if dpo is not None:
            rows.append(f"| DPO(매입채무지급) | {dpo:.0f}일 | - |")
        if capex_ratio is not None:
            rows.append(f"| CAPEX비율 | {capex_ratio:.1f}% | - |")
        parts.append("\n".join(rows))

    return "\n".join(parts) if parts else None


def _run_dupont_analysis(company: Any, tables: list[str]) -> str | None:
    """DuPont 분해: ROE = 순이익률 × 자산회전율 × 레버리지."""
    from dartlab.engines.ai.context.company_adapter import get_headline_ratios

    ratios = get_headline_ratios(company)
    if ratios is None:
        return None

    dm = getattr(ratios, "dupontMargin", None)
    dt = getattr(ratios, "dupontTurnover", None)
    dl = getattr(ratios, "dupontLeverage", None)
    roe = getattr(ratios, "roe", None)
    if dm is None or dt is None or dl is None or roe is None:
        return None

    # 주요 동인 판별
    factors = {"수익성(순이익률)": dm, "효율성(자산회전율)": dt, "레버리지": dl}
    driver = max(factors, key=lambda k: factors[k])

    parts = [
        "### DuPont 분해 분석",
        f"ROE **{roe:.1f}%** = 순이익률({dm:.1f}%) × 자산회전율({dt:.2f}x) × 레버리지({dl:.2f}x)",
        f"→ **{driver} 주도형**",
    ]

    return "\n".join(parts)


def _run_composite_scoring(company: Any, tables: list[str]) -> str | None:
    """복합 스코어링: Piotroski F-Score, Altman Z-Score, ROIC."""
    from dartlab.engines.ai.context.company_adapter import get_headline_ratios

    ratios = get_headline_ratios(company)
    if ratios is None:
        return None

    pf = getattr(ratios, "piotroskiFScore", None)
    az = getattr(ratios, "altmanZScore", None)
    roic = getattr(ratios, "roic", None)
    ic = getattr(ratios, "interestCoverage", None)

    if pf is None and az is None and roic is None:
        return None

    parts = ["### 복합 재무 지표"]
    rows = ["| 지표 | 값 | 판단 | 기준 |", "| --- | --- | --- | --- |"]
    has_rows = False

    if pf is not None:
        label = "우수" if pf >= 7 else ("보통" if pf >= 4 else "취약")
        rows.append(f"| Piotroski F-Score | {pf}/9 | {label} | ≥7 우수, 4-6 보통, <4 취약 |")
        has_rows = True
    if az is not None:
        label = "안전" if az > 2.99 else ("회색" if az >= 1.81 else "부실위험")
        rows.append(f"| Altman Z-Score | {az:.2f} | {label} | >2.99 안전, 1.81-2.99 회색, <1.81 부실 |")
        has_rows = True
    if roic is not None:
        label = "우수" if roic >= 15 else ("적정" if roic >= 8 else "미흡")
        rows.append(f"| ROIC | {roic:.1f}% | {label} | ≥15% 우수, 8-15% 적정, <8% 미흡 |")
        has_rows = True
    if ic is not None:
        label = "양호" if ic >= 5 else ("주의" if ic >= 1 else "위험")
        rows.append(f"| 이자보상배율 | {ic:.1f}x | {label} | ≥5x 양호, 1-5x 주의, <1x 위험 |")
        has_rows = True

    if not has_rows:
        return None

    parts.append("\n".join(rows))
    return "\n".join(parts)


def _run_governance_analysis(company: Any, tables: list[str]) -> str | None:
    """지배구조: majorHolder 지분율 + audit 의견 + executive 규모."""
    parts: list[str] = []

    report = getattr(company, "report", None)
    if report is None:
        return None

    mh = getattr(report, "majorHolder", None)
    if mh is not None and mh.years and mh.totalShareRatio:
        latest_ratio = mh.totalShareRatio[-1]
        if latest_ratio is not None:
            parts.append(f"- 최대주주 합산 지분율: {latest_ratio:.1f}% ({mh.years[-1]}년)")
            if len(mh.totalShareRatio) >= 2:
                prev = mh.totalShareRatio[-2]
                if prev is not None:
                    diff = latest_ratio - prev
                    parts.append(f"  전년 대비: {diff:+.1f}%p")

    aud = getattr(report, "audit", None)
    if aud is not None and aud.years and aud.opinions:
        latest_opinion = aud.opinions[-1]
        parts.append(f"- 최근 감사의견: {latest_opinion or '-'} ({aud.years[-1]}년)")

    exe = getattr(report, "executive", None)
    if exe is not None and exe.totalCount > 0:
        outside_pct = exe.outsideCount / max(exe.registeredCount + exe.outsideCount, 1) * 100
        parts.append(f"- 임원 {exe.totalCount}명 (사외이사 비율 {outside_pct:.0f}%)")

    if not parts:
        return None
    return "### 지배구조 분석\n" + "\n".join(parts)


def _run_business_analysis(company: Any, tables: list[str]) -> str | None:
    """사업: segments 매출 구성 + productService 주요제품."""
    parts: list[str] = []

    try:
        segments = getattr(company, "segments", None)
        if isinstance(segments, pl.DataFrame) and not segments.is_empty():
            parts.append("### 사업 부문 (segments)")
            parts.append(_df_to_simple_md(segments, max_rows=8))
    except _PIPELINE_ERRORS:
        pass

    try:
        ps = getattr(company, "productService", None)
        if isinstance(ps, pl.DataFrame) and not ps.is_empty():
            parts.append("### 주요 제품/서비스")
            parts.append(_df_to_simple_md(ps, max_rows=8))
    except _PIPELINE_ERRORS:
        pass

    return "\n\n".join(parts) if parts else None


def _run_investment_analysis(company: Any, tables: list[str]) -> str | None:
    """투자: R&D/매출 비율 + CAPEX + 자회사 현황."""
    from dartlab.engines.ai.context.company_adapter import get_headline_ratios

    parts: list[str] = []

    ratios = get_headline_ratios(company)
    if ratios is not None:
        capex = getattr(ratios, "capexRatio", None)
        if capex is not None:
            parts.append(f"- CAPEX/매출: {capex:.1f}%")

    try:
        rnd = getattr(company, "rnd", None)
        if isinstance(rnd, pl.DataFrame) and not rnd.is_empty():
            parts.append("### R&D 현황")
            parts.append(_df_to_simple_md(rnd, max_rows=5))
    except _PIPELINE_ERRORS:
        pass

    try:
        sub = getattr(company, "subsidiary", None)
        if isinstance(sub, pl.DataFrame) and not sub.is_empty():
            parts.append(f"### 종속기업 ({sub.height}개)")
            parts.append(_df_to_simple_md(sub, max_rows=5))
    except _PIPELINE_ERRORS:
        pass

    return "\n\n".join(parts) if parts else None


_PIPELINE_MAP: dict[str, list] = {
    "건전성": [_run_health_analysis, _run_quality_of_earnings, _run_composite_scoring],
    "수익성": [_run_profitability_analysis, _run_quality_of_earnings, _run_dupont_analysis],
    "성장성": [_run_growth_analysis],
    "배당": [_run_dividend_analysis],
    "리스크": [_run_risk_analysis, _run_composite_scoring],
    "투자": [_run_investment_analysis, _run_growth_analysis],
    "지배구조": [_run_governance_analysis],
    "종합": [
        _run_health_analysis,
        _run_profitability_analysis,
        _run_growth_analysis,
        _run_quality_of_earnings,
        _run_dupont_analysis,
        _run_composite_scoring,
    ],
    "공시": [],  # show_topic 도구 사용 안내 — insight만 주입
    "사업": [_run_business_analysis],
}


# ══════════════════════════════════════
# L2 엔진 통합 — Tier 1 분석 패키지
# ══════════════════════════════════════

_Q_TYPES_NEED_INSIGHT = frozenset(
    {
        "건전성",
        "수익성",
        "성장성",
        "리스크",
        "종합",
        "배당",
        "지배구조",
        "투자",
        "공시",
        "사업",
    }
)

_Q_TYPES_NEED_RANK = frozenset(
    {
        "종합",
        "성장성",
    }
)


_Q_TYPES_NEED_SCAN = frozenset(
    {
        "지배구조",
        "리스크",
        "종합",
        "투자",
    }
)


def _run_l2_engines(company: Any, q_type: str) -> str | None:
    """L2 엔진(sector, insight, rank, scan) 결과를 분석 패키지로 조립."""
    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    parts: list[str] = []

    sector_md = _run_sector(company)
    if sector_md:
        parts.append(sector_md)

    if q_type in _Q_TYPES_NEED_INSIGHT:
        insight_md = _run_insight(stockCode, company)
        if insight_md:
            parts.append(insight_md)

    if q_type in _Q_TYPES_NEED_RANK:
        rank_md = _run_rank(stockCode)
        if rank_md:
            parts.append(rank_md)

    if q_type in _Q_TYPES_NEED_SCAN:
        scan_md = _run_scan(company, q_type)
        if scan_md:
            parts.append(scan_md)

    if not parts:
        return None
    return "\n\n".join(parts)


def _run_sector(company: Any) -> str | None:
    """sector 엔진: 업종 분류 + 섹터 파라미터."""
    try:
        from dartlab.engines.sector import classify, getParams

        corpName = getattr(company, "corpName", "")
        overview = getattr(company, "companyOverview", None)
        kindIndustry = None
        mainProducts = None
        if isinstance(overview, dict):
            kindIndustry = overview.get("indutyName")
        detail = getattr(company, "companyOverviewDetail", None)
        if isinstance(detail, dict):
            mainProducts = detail.get("mainBusiness")

        info = classify(corpName, kindIndustry=kindIndustry, mainProducts=mainProducts)
        if info.source == "unknown":
            return None

        params = getParams(info)

        lines = [
            "### 섹터 분류 (자동)",
            f"- **대분류**: {info.sector.value}",
            f"- **중분류**: {info.industryGroup.value}",
            f"- **분류근거**: {info.source} (신뢰도 {info.confidence:.0%})",
        ]
        if params:
            lines.append(f"- **섹터 기준 PER**: {params.perMultiple}배")
            lines.append(f"- **섹터 기준 PBR**: {params.pbrMultiple}배")
            lines.append(f"- **적정 할인율**: {params.discountRate}%")
        return "\n".join(lines)
    except (ImportError, AttributeError):
        _log.debug("sector engine not available")
        return None
    except _PIPELINE_ERRORS as e:
        _log.debug("sector engine error: %s", e)
        return None


def _run_insight(stockCode: str, company: Any) -> str | None:
    """insight 엔진: 7영역 등급 + 이상치 + 프로파일."""
    try:
        from dartlab.engines.insight import analyze

        result = analyze(stockCode, company=company)
        if result is None:
            return None

        grades = result.grades()
        lines = [
            "### 인사이트 등급 (자동분석)",
            f"- **프로파일**: {result.profile}",
            "",
            "| 영역 | 등급 | 요약 |",
            "| --- | --- | --- |",
        ]
        areaMap = {
            "performance": ("실적", result.performance),
            "profitability": ("수익성", result.profitability),
            "health": ("건전성", result.health),
            "cashflow": ("현금흐름", result.cashflow),
            "governance": ("지배구조", result.governance),
            "risk": ("리스크", result.risk),
            "opportunity": ("기회", result.opportunity),
        }
        for key, (label, ir) in areaMap.items():
            grade = grades.get(key, "N")
            summary = ir.summary if ir else "-"
            lines.append(f"| {label} | **{grade}** | {summary} |")

        if result.anomalies:
            lines.append("")
            lines.append("### 이상치 탐지")
            for a in result.anomalies[:5]:
                severity = {"danger": "⚠️", "warning": "🔸", "info": "ℹ️"}.get(a.severity, "•")
                lines.append(f"- {severity} [{a.category}] {a.text}")

        if result.summary:
            lines.append("")
            lines.append(f"**종합**: {result.summary}")

        return "\n".join(lines)
    except (ImportError, AttributeError):
        _log.debug("insight engine not available")
        return None
    except _PIPELINE_ERRORS as e:
        _log.debug("insight engine error: %s", e)
        return None


def _run_rank(stockCode: str) -> str | None:
    """rank 엔진: 시장 내 규모 순위."""
    try:
        from dartlab.engines.rank import getRank

        rank = getRank(stockCode)
        if rank is None:
            return None

        lines = ["### 시장 순위 (캐시)"]

        def _fmtRank(r, total, label):
            if r is None:
                return None
            pct = r / total * 100 if total > 0 else 0
            return f"- **{label}**: {r:,}위 / {total:,}개 (상위 {pct:.1f}%)"

        row = _fmtRank(rank.revenueRank, rank.revenueTotal, "매출 순위(전체)")
        if row:
            lines.append(row)
        row = _fmtRank(rank.assetRank, rank.assetTotal, "자산 순위(전체)")
        if row:
            lines.append(row)
        row = _fmtRank(rank.growthRank, rank.growthTotal, "성장률 순위(전체)")
        if row:
            lines.append(row)

        if rank.revenueRankInSector is not None:
            lines.append(
                f"- **섹터({rank.sector}) 매출 순위**: {rank.revenueRankInSector}위 / {rank.revenueSectorTotal}개"
            )

        if rank.sizeClass:
            sizeLabels = {"large": "대형", "mid": "중형", "small": "소형"}
            lines.append(f"- **규모 분류**: {sizeLabels.get(rank.sizeClass, rank.sizeClass)}")

        if len(lines) <= 1:
            return None
        return "\n".join(lines)
    except (ImportError, AttributeError):
        _log.debug("rank engine not available")
        return None
    except _PIPELINE_ERRORS as e:
        _log.debug("rank engine error: %s", e)
        return None


# ══════════════════════════════════════
# scan 엔진 통합
# ══════════════════════════════════════

_SCAN_AXES_BY_QTYPE: dict[str, list[str]] = {
    "지배구조": ["governance", "capital"],
    "리스크": ["debt", "governance"],
    "종합": ["governance", "debt", "capital", "workforce"],
    "투자": ["capital", "debt"],
}

_SCAN_SUPPLEMENTARY: dict[str, list[str]] = {
    "governance": ["boardOfDirectors", "auditSystem", "internalControl"],
    "debt": ["bond", "contingentLiability"],
    "capital": ["capitalChange", "fundraising"],
    "workforce": ["executivePay"],
}


def _run_scan(company: Any, q_type: str) -> str | None:
    """scan 엔진: 질문 유형에 맞는 축만 조회 + 보충 모듈 핵심 수치 주입."""
    axes = _SCAN_AXES_BY_QTYPE.get(q_type, [])
    if not axes:
        return None

    parts: list[str] = []
    _LABELS = {
        "governance": "지배구조 스캔",
        "workforce": "인력/급여 스캔",
        "capital": "주주환원 스캔",
        "debt": "부채구조 스캔",
    }

    for axis in axes:
        method = getattr(company, axis, None)
        if method is None:
            continue
        try:
            result = method()
            if result is None or not isinstance(result, pl.DataFrame) or result.is_empty():
                continue
            label = _LABELS.get(axis, axis)
            lines = [f"### {label}"]
            for col in result.columns:
                val = result[col][0]
                if val is not None:
                    lines.append(f"- **{col}**: {val}")

            # 보충 모듈 핵심 수치
            for mod_name in _SCAN_SUPPLEMENTARY.get(axis, []):
                try:
                    mod_data = getattr(company, mod_name, None)
                    if isinstance(mod_data, pl.DataFrame) and not mod_data.is_empty():
                        lines.append(f"- [{mod_name}] {mod_data.height}건 데이터 존재")
                    elif mod_data is not None:
                        lines.append(f"- [{mod_name}] 데이터 있음")
                except _PIPELINE_ERRORS:
                    pass

            if len(lines) > 1:
                parts.append("\n".join(lines))
        except _PIPELINE_ERRORS:
            continue

    if not parts:
        return None
    return "\n\n".join(parts)
