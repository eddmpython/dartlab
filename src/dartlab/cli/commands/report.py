"""`dartlab report` command. 기본은 Markdown 보고서, `--model` 은 전문 리포트 계약(ReportModel) JSON.

`--model` 은 공개 계약 `Company.reportModel(perspective)` 를 그대로 직렬화한다(self-calc 0).
기존 Markdown 경로는 불변 (추가형).
"""

from __future__ import annotations

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configureDartlab


def configureParser(subparsers) -> None:
    """report 서브커맨드 등록 — Markdown 보고서 자동 생성."""
    parser = subparsers.add_parser("report", help="기업 분석 보고서 자동 생성 (Markdown)")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("-o", "--output", default=None, help="출력 파일 경로 (기본: stdout)")
    parser.add_argument(
        "--sections",
        nargs="+",
        default=None,
        help="포함할 섹션 (overview finance ratios insights). 기본: 전부",
    )
    parser.add_argument(
        "--model",
        action="store_true",
        help="전문 리포트 계약(ReportModel) JSON 출력. Markdown 대신 c.reportModel() 결과를 낸다",
    )
    parser.add_argument(
        "--perspective",
        default="full",
        help="--model 관점 (full/valuation/credit/earnings/growth 등). 기본: full",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    """기업 분석 보고서를 stdout 또는 파일로 출력한다 (기본 Markdown, `--model` 은 계약 JSON)."""
    dartlab = configureDartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
        from dartlab.cli.services.errors import wrapError

        raise CLIError(wrapError(exc, stockCode=args.company)) from exc

    name = getattr(company, "corpName", args.company) or args.company
    code = getattr(company, "stockCode", "") or ""

    if getattr(args, "model", False):
        import json

        model = company.reportModel(getattr(args, "perspective", "full"))
        report = json.dumps(model, ensure_ascii=False, indent=2, default=str)
    else:
        include = set(args.sections) if args.sections else None
        report = _buildReport(company, name, code, include)

    if args.output:
        from pathlib import Path

        from dartlab.cli.services.output import getConsole

        out = Path(args.output)
        out.write_text(report, encoding="utf-8")
        getConsole().print(f"  [bold green]완료[/] {name} ({code}) → {out}")
    else:
        print(report)
    return 0


def _buildReport(company, name: str, code: str, include: set | None) -> str:
    """Company 데이터를 수집하여 Markdown 보고서를 조립한다."""
    import polars as pl

    parts: list[str] = [f"# {name} ({code}) 분석 보고서\n"]

    # ── 기업 개요 ──
    if include is None or "overview" in include:
        parts.append("## 기업 개요\n")
        try:
            overview = company.panel("companyOverview")
            if isinstance(overview, pl.DataFrame) and overview.height > 0:
                for row in overview.iter_rows(named=True):
                    text = row.get("text") or row.get("content") or ""
                    if text:
                        parts.append(str(text)[:2000])
                        break
            elif isinstance(overview, str):
                parts.append(overview[:2000])
        except (AttributeError, KeyError, ValueError):
            parts.append("기업 개요 데이터가 없습니다.\n")

    # ── 재무제표 ──
    if include is None or "finance" in include:
        parts.append("\n## 재무제표\n")
        for stmt_name, label in [("BS", "재무상태표"), ("IS", "손익계산서"), ("CF", "현금흐름표")]:
            try:
                df = getattr(company, stmt_name, None)
                if isinstance(df, pl.DataFrame) and df.height > 0:
                    parts.append(f"### {label}\n")
                    # 최근 4개 기간만
                    cols = df.columns[:1] + [c for c in df.columns[1:5]]
                    preview = df.select(cols).head(15)
                    parts.append(_dfToMd(preview))
            except (AttributeError, KeyError, ValueError):
                pass

    # ── 재무비율 ──
    if include is None or "ratios" in include:
        parts.append("\n## 재무비율\n")
        try:
            ratios = getattr(company, "ratios", None)
            if isinstance(ratios, pl.DataFrame) and ratios.height > 0:
                parts.append(_dfToMd(ratios.head(20)))
        except (AttributeError, KeyError, ValueError):
            parts.append("재무비율 데이터가 없습니다.\n")

    # ── 인사이트 ──
    if include is None or "insights" in include:
        parts.append("\n## 인사이트 등급\n")
        try:
            insights = getattr(company, "insights", None)
            if insights is not None:
                grades = insights.grades() if callable(getattr(insights, "grades", None)) else {}
                if grades:
                    parts.append("| 영역 | 등급 |")
                    parts.append("| --- | --- |")
                    for area, grade in grades.items():
                        parts.append(f"| {area} | {grade} |")
        except (AttributeError, KeyError, ValueError):
            parts.append("인사이트 데이터가 없습니다.\n")

    parts.append("")
    return "\n".join(parts)


def _dfToMd(df) -> str:
    """Polars DataFrame을 Markdown 테이블로 변환."""
    import polars as pl

    if not isinstance(df, pl.DataFrame) or df.height == 0:
        return ""
    cols = df.columns
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for row in df.iter_rows():
        cells = []
        for v in row:
            if v is None:
                cells.append("-")
            elif isinstance(v, float):
                cells.append(f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}")
            else:
                cells.append(str(v)[:80])
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows) + "\n"
