"""포맷팅·유틸리티 함수 — builder.py에서 분리.

원 단위 변환, DataFrame→마크다운, 파생 지표 자동계산 등
builder / finance_context 양쪽에서 재사용하는 순수 함수 모음.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.engines.ai.metadata import ModuleMeta

_CONTEXT_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

# ── 핵심 계정 필터용 상수 ──

_KEY_ACCOUNTS_BS = {
    "자산총계",
    "유동자산",
    "비유동자산",
    "부채총계",
    "유동부채",
    "비유동부채",
    "자본총계",
    "지배기업소유주지분",
    "현금및현금성자산",
    "매출채권",
    "재고자산",
    "유형자산",
    "무형자산",
    "투자부동산",
    "단기차입금",
    "장기차입금",
    "사채",
}

_KEY_ACCOUNTS_IS = {
    "매출액",
    "매출원가",
    "매출총이익",
    "판매비와관리비",
    "영업이익",
    "영업손실",
    "금융수익",
    "금융비용",
    "이자비용",
    "이자수익",
    "법인세비용차감전순이익",
    "법인세비용",
    "당기순이익",
    "당기순손실",
    "지배기업소유주지분순이익",
}

_KEY_ACCOUNTS_CF = {
    "영업활동현금흐름",
    "영업활동으로인한현금흐름",
    "투자활동현금흐름",
    "투자활동으로인한현금흐름",
    "재무활동현금흐름",
    "재무활동으로인한현금흐름",
    "현금및현금성자산의순증가",
    "현금및현금성자산의증감",
    "기초현금및현금성자산",
    "기말현금및현금성자산",
}

_KEY_ACCOUNTS_MAP = {
    "BS": _KEY_ACCOUNTS_BS,
    "IS": _KEY_ACCOUNTS_IS,
    "CF": _KEY_ACCOUNTS_CF,
}


# ══════════════════════════════════════
# 숫자 포맷팅
# ══════════════════════════════════════


def _format_won(val: float) -> str:
    """원 단위 숫자를 읽기 좋은 한국어 단위로 변환."""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{abs_val / 1e12:,.1f}조"
    if abs_val >= 1e8:
        return f"{sign}{abs_val / 1e8:,.0f}억"
    if abs_val >= 1e4:
        return f"{sign}{abs_val / 1e4:,.0f}만"
    if abs_val >= 1:
        return f"{sign}{abs_val:,.0f}"
    return "0"


def _format_krw(val: float) -> str:
    """백만원 단위 숫자를 읽기 좋은 한국어 단위로 변환."""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:,.1f}조"
    if abs_val >= 10_000:
        return f"{sign}{abs_val / 10_000:,.0f}억"
    if abs_val >= 1:
        return f"{sign}{abs_val:,.0f}"
    if abs_val > 0:
        return f"{sign}{abs_val:.4f}"
    return "0"


def _format_usd(val: float) -> str:
    """USD 숫자를 읽기 좋은 영문 단위로 변환."""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}${abs_val / 1e12:,.1f}T"
    if abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:,.1f}B"
    if abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:,.0f}M"
    if abs_val >= 1e3:
        return f"{sign}${abs_val / 1e3:,.0f}K"
    if abs_val >= 1:
        return f"{sign}${abs_val:,.0f}"
    return "$0"


# ══════════════════════════════════════
# 계정 필터
# ══════════════════════════════════════


def _filter_key_accounts(df: pl.DataFrame, module_name: str) -> pl.DataFrame:
    """재무제표에서 핵심 계정만 필터링."""
    if "계정명" not in df.columns or module_name not in _KEY_ACCOUNTS_MAP:
        return df

    key_set = _KEY_ACCOUNTS_MAP[module_name]
    mask = pl.lit(False)
    for keyword in key_set:
        mask = mask | pl.col("계정명").str.contains(keyword)

    filtered = df.filter(mask)
    if filtered.height < 5:
        return df
    return filtered


# ══════════════════════════════════════
# 업종명 추출
# ══════════════════════════════════════


def _get_sector(company: Any) -> str | None:
    """Company에서 업종명 추출."""
    try:
        overview = getattr(company, "companyOverview", None)
        if isinstance(overview, dict):
            sector = overview.get("indutyName") or overview.get("sector")
            if sector:
                return sector

        detail = getattr(company, "companyOverviewDetail", None)
        if isinstance(detail, dict):
            sector = detail.get("sector") or detail.get("indutyName")
            if sector:
                return sector
    except _CONTEXT_ERRORS:
        pass

    return None


# ══════════════════════════════════════
# DataFrame → 마크다운 변환
# ══════════════════════════════════════


def df_to_markdown(
    df: pl.DataFrame,
    max_rows: int = 30,
    meta: ModuleMeta | None = None,
    compact: bool = False,
    market: str = "KR",
) -> str:
    """Polars DataFrame → 메타데이터 주석 포함 Markdown 테이블.

    Args:
            compact: True면 숫자를 억/조 단위로 변환 (LLM 컨텍스트용).
            market: "KR"이면 한글 라벨, "US"면 영문 라벨.
    """
    if df is None or df.height == 0:
        return "(데이터 없음)"

    # account 컬럼의 snakeId → 한글/영문 라벨 자동 변환
    if "account" in df.columns:
        try:
            from dartlab.engines.common.finance.labels import get_account_labels

            locale = "kr" if market == "KR" else "en"
            _labels = get_account_labels(locale)
            df = df.with_columns(pl.col("account").replace(_labels).alias("account"))
        except ImportError:
            pass

    effective_max = meta.maxRows if meta else max_rows
    if compact:
        effective_max = min(effective_max, 20)

    if "year" in df.columns:
        df = df.sort("year", descending=True)

    if df.height > effective_max:
        display_df = df.head(effective_max)
        truncated = True
    else:
        display_df = df
        truncated = False

    parts = []

    is_krw = not meta or meta.unit in ("백만원", "")
    if meta and meta.unit and meta.unit != "백만원":
        parts.append(f"(단위: {meta.unit})")
    elif compact and is_krw:
        parts.append("(단위: 억/조원, 원본 백만원)")

    if not compact and meta and meta.columns:
        col_map = {c.name: c for c in meta.columns}
        described = []
        for col in display_df.columns:
            if col in col_map:
                c = col_map[col]
                desc = f"`{col}`: {c.description}"
                if c.unit:
                    desc += f" ({c.unit})"
                described.append(desc)
        if described:
            parts.append(" | ".join(described))

    cols = display_df.columns
    if not compact and meta and meta.columns:
        col_map = {c.name: c for c in meta.columns}
        header_cells = []
        for col in cols:
            if col in col_map:
                header_cells.append(f"{col} ({col_map[col].description})")
            else:
                header_cells.append(col)
        header = "| " + " | ".join(header_cells) + " |"
    else:
        header = "| " + " | ".join(cols) + " |"

    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for row in display_df.iter_rows():
        cells = []
        for i, val in enumerate(row):
            if val is None:
                cells.append("-")
            elif isinstance(val, (int, float)):
                col_name = cols[i]
                if compact and is_krw and col_name.isdigit() and len(col_name) == 4:
                    cells.append(_format_krw(float(val)))
                elif isinstance(val, float):
                    if abs(val) >= 1:
                        cells.append(f"{val:,.0f}")
                    else:
                        cells.append(f"{val:.4f}")
                elif col_name == "year" or (isinstance(val, int) and 1900 <= val <= 2100):
                    cells.append(str(val))
                else:
                    cells.append(f"{val:,}")
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")

    parts.append("\n".join([header, sep] + rows))

    if truncated:
        parts.append(f"(상위 {effective_max}행 표시, 전체 {df.height}행)")

    return "\n".join(parts)


# ══════════════════════════════════════
# 파생 지표 자동계산
# ══════════════════════════════════════


def _find_account_value(df: pl.DataFrame, keyword: str, year_col: str) -> float | None:
    """계정명에서 키워드를 포함하는 행의 값 추출."""
    if "계정명" not in df.columns or year_col not in df.columns:
        return None
    matched = df.filter(pl.col("계정명").str.contains(keyword))
    if matched.height == 0:
        return None
    val = matched.row(0, named=True).get(year_col)
    return val if isinstance(val, (int, float)) else None


def _compute_derived_metrics(name: str, df: pl.DataFrame, company: Any = None) -> str | None:
    """핵심 재무제표에서 YoY 성장률/비율 자동계산.

    개선: ROE, 이자보상배율, FCF, EBITDA 등 추가.
    """
    if name not in ("BS", "IS", "CF") or df is None or df.height == 0:
        return None

    year_cols = sorted(
        [c for c in df.columns if c.isdigit() and len(c) == 4],
        reverse=True,
    )
    if len(year_cols) < 2:
        return None

    lines = []

    if name == "IS":
        targets = {
            "매출액": "매출 성장률",
            "영업이익": "영업이익 성장률",
            "당기순이익": "순이익 성장률",
        }
        for acct, label in targets.items():
            metrics = []
            for i in range(min(len(year_cols) - 1, 3)):
                cur = _find_account_value(df, acct, year_cols[i])
                prev = _find_account_value(df, acct, year_cols[i + 1])
                if cur is not None and prev is not None and prev != 0:
                    yoy = (cur - prev) / abs(prev) * 100
                    metrics.append(f"{year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")
            if metrics:
                lines.append(f"- {label}: {', '.join(metrics)}")

        # 영업이익률, 순이익률
        latest = year_cols[0]
        rev = _find_account_value(df, "매출액", latest)
        oi = _find_account_value(df, "영업이익", latest)
        ni = _find_account_value(df, "당기순이익", latest)
        if rev and rev != 0:
            if oi is not None:
                lines.append(f"- {latest} 영업이익률: {oi / rev * 100:.1f}%")
            if ni is not None:
                lines.append(f"- {latest} 순이익률: {ni / rev * 100:.1f}%")

        # 이자보상배율 (영업이익 / 이자비용)
        interest = _find_account_value(df, "이자비용", latest)
        if interest is None:
            interest = _find_account_value(df, "금융비용", latest)
        if oi is not None and interest is not None and interest != 0:
            icr = oi / abs(interest)
            lines.append(f"- {latest} 이자보상배율: {icr:.1f}x")

        # ROE (순이익 / 자본총계) — BS가 있을 때
        if company and ni is not None:
            try:
                bs = getattr(company, "BS", None)
                if isinstance(bs, pl.DataFrame) and latest in bs.columns:
                    equity = _find_account_value(bs, "자본총계", latest)
                    if equity and equity != 0:
                        roe = ni / equity * 100
                        lines.append(f"- {latest} ROE: {roe:.1f}%")
                    total_asset = _find_account_value(bs, "자산총계", latest)
                    if total_asset and total_asset != 0:
                        roa = ni / total_asset * 100
                        lines.append(f"- {latest} ROA: {roa:.1f}%")
            except _CONTEXT_ERRORS:
                pass

    elif name == "BS":
        latest = year_cols[0]
        debt = _find_account_value(df, "부채총계", latest)
        equity = _find_account_value(df, "자본총계", latest)
        ca = _find_account_value(df, "유동자산", latest)
        cl = _find_account_value(df, "유동부채", latest)
        ta = _find_account_value(df, "자산총계", latest)

        if debt is not None and equity is not None and equity != 0:
            lines.append(f"- {latest} 부채비율: {debt / equity * 100:.1f}%")
        if ca is not None and cl is not None and cl != 0:
            lines.append(f"- {latest} 유동비율: {ca / cl * 100:.1f}%")
        if debt is not None and ta is not None and ta != 0:
            lines.append(f"- {latest} 부채총계/자산총계: {debt / ta * 100:.1f}%")

        # 총자산 증가율
        for i in range(min(len(year_cols) - 1, 2)):
            cur = _find_account_value(df, "자산총계", year_cols[i])
            prev = _find_account_value(df, "자산총계", year_cols[i + 1])
            if cur is not None and prev is not None and prev != 0:
                yoy = (cur - prev) / abs(prev) * 100
                lines.append(f"- 총자산 증가율 {year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")

    elif name == "CF":
        latest = year_cols[0]
        op_cf = _find_account_value(df, "영업활동", latest)
        inv_cf = _find_account_value(df, "투자활동", latest)
        fin_cf = _find_account_value(df, "재무활동", latest)

        if op_cf is not None and inv_cf is not None:
            fcf = op_cf + inv_cf
            lines.append(f"- {latest} FCF(영업CF+투자CF): {_format_krw(fcf)}")

        # CF 패턴 해석
        if op_cf is not None and inv_cf is not None and fin_cf is not None:
            pattern = f"{'+' if op_cf >= 0 else '-'}/{'+' if inv_cf >= 0 else '-'}/{'+' if fin_cf >= 0 else '-'}"
            pattern_desc = _interpret_cf_pattern(op_cf >= 0, inv_cf >= 0, fin_cf >= 0)
            lines.append(f"- {latest} CF 패턴(영업/투자/재무): {pattern} → {pattern_desc}")

        for i in range(min(len(year_cols) - 1, 2)):
            cur = _find_account_value(df, "영업활동", year_cols[i])
            prev = _find_account_value(df, "영업활동", year_cols[i + 1])
            if cur is not None and prev is not None and prev != 0:
                yoy = (cur - prev) / abs(prev) * 100
                lines.append(f"- 영업활동CF 변동 {year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")

    if not lines:
        return None

    return "### 주요 지표 (자동계산)\n" + "\n".join(lines)


def _interpret_cf_pattern(op_pos: bool, inv_pos: bool, fin_pos: bool) -> str:
    """현금흐름 패턴 해석."""
    if op_pos and not inv_pos and not fin_pos:
        return "우량 기업형 (영업이익으로 투자+상환)"
    if op_pos and not inv_pos and fin_pos:
        return "성장 투자형 (영업+차입으로 적극 투자)"
    if op_pos and inv_pos and not fin_pos:
        return "구조조정형 (자산 매각+부채 상환)"
    if not op_pos and not inv_pos and fin_pos:
        return "위험 신호 (영업적자인데 차입으로 투자)"
    if not op_pos and inv_pos and fin_pos:
        return "위기 관리형 (자산 매각+차입으로 영업 보전)"
    if not op_pos and inv_pos and not fin_pos:
        return "축소형 (자산 매각으로 부채 상환)"
    return "기타 패턴"
