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

from dartlab.engines.ai.prompts import _classify_question

_log = logging.getLogger(__name__)


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
        except Exception:
            continue

    l2 = _run_l2_engines(company, q_type)
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


_PIPELINE_MAP: dict[str, list] = {
    "건전성": [_run_health_analysis],
    "수익성": [_run_profitability_analysis],
    "성장성": [_run_growth_analysis],
    "배당": [_run_dividend_analysis],
    "리스크": [_run_risk_analysis],
    "투자": [_run_growth_analysis],
    "종합": [_run_health_analysis, _run_profitability_analysis, _run_growth_analysis],
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
    }
)

_Q_TYPES_NEED_RANK = frozenset(
    {
        "종합",
        "성장성",
    }
)


def _run_l2_engines(company: Any, q_type: str) -> str | None:
    """L2 엔진(sector, insight, rank) 결과를 분석 패키지로 조립."""
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
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        _log.debug("rank engine error: %s", e)
        return None
