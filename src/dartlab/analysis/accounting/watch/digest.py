"""시장 변화 다이제스트 생성.

scan_market 결과를 마크다운/JSON/DataFrame 형태의 요약 다이제스트로 변환한다.

사용법::

    from dartlab.analysis.accounting.watch.digest import build_digest

    df = scan_market(top_n=30)
    md = build_digest(df, format="markdown")
    print(md)
"""

from __future__ import annotations

from datetime import date

import polars as pl


def build_digest(
    scan_df: pl.DataFrame,
    *,
    title: str | None = None,
    format: str = "markdown",
    top_n: int = 20,
) -> str | pl.DataFrame | dict:
    """스캔 결과에서 다이제스트를 생성한다.

    Args:
        scan_df: scan_market() 결과 DataFrame.
        title: 다이제스트 제목 (None이면 자동 생성).
        format: "markdown", "json", "dataframe" 중 택1.
        top_n: 다이제스트에 포함할 최대 항목 수.

    Returns:
        format에 따라 str(markdown), dict(json), pl.DataFrame.
    """
    if scan_df.height == 0:
        if format == "dataframe":
            return scan_df
        if format == "json":
            return {"title": title or "변화 없음", "date": str(date.today()), "items": []}
        return f"# {title or '시장 변화 다이제스트'}\n\n변화가 감지되지 않았습니다.\n"

    df = scan_df.sort("score", descending=True).head(top_n)

    if format == "dataframe":
        return df

    if format == "json":
        return _to_json(df, title)

    return _to_markdown(df, title)


def _to_markdown(df: pl.DataFrame, title: str | None) -> str:
    """DataFrame → 마크다운 다이제스트."""
    today = date.today().isoformat()
    header = title or f"시장 변화 다이제스트 ({today})"

    lines = [f"# {header}\n"]

    # 기업별 그룹핑
    if "stockCode" in df.columns and "corpName" in df.columns:
        grouped = df.group_by(["stockCode", "corpName"], maintain_order=True)
        for (stock_code, corp_name), group_df in grouped:
            name_label = corp_name if corp_name else stock_code
            lines.append(f"\n## {name_label} ({stock_code})\n")
            for row in group_df.iter_rows(named=True):
                score = row.get("score", 0)
                topic = row.get("topic", "")
                reason = row.get("reason", "")
                change_rate = row.get("changeRate", 0)
                period = row.get("latestPeriod", "")

                badge = _score_badge(score)
                lines.append(f"- {badge} **{topic}** (score: {score:.1f}, 변화율: {change_rate:.1%})")
                if period:
                    lines.append(f"  - 기간: {period}")
                if reason:
                    lines.append(f"  - 근거: {reason}")
    else:
        for row in df.iter_rows(named=True):
            score = row.get("score", 0)
            topic = row.get("topic", "")
            reason = row.get("reason", "")
            badge = _score_badge(score)
            lines.append(f"- {badge} **{topic}** (score: {score:.1f}) — {reason}")

    lines.append(f"\n---\n생성일: {today}\n")
    return "\n".join(lines)


def _to_json(df: pl.DataFrame, title: str | None) -> dict:
    """DataFrame → JSON dict."""
    today = date.today().isoformat()
    items = []
    for row in df.iter_rows(named=True):
        items.append(
            {
                "stockCode": row.get("stockCode", ""),
                "corpName": row.get("corpName", ""),
                "topic": row.get("topic", ""),
                "score": round(row.get("score", 0), 1),
                "changeRate": round(row.get("changeRate", 0), 4),
                "deltaBytes": row.get("deltaBytes", 0),
                "latestPeriod": row.get("latestPeriod", ""),
                "reason": row.get("reason", ""),
            }
        )
    return {
        "title": title or f"시장 변화 다이제스트 ({today})",
        "date": today,
        "count": len(items),
        "items": items,
    }


def _score_badge(score: float) -> str:
    """점수에 따른 텍스트 배지."""
    if score >= 80:
        return "[!!!]"
    if score >= 50:
        return "[!!]"
    if score >= 25:
        return "[!]"
    return "[~]"
