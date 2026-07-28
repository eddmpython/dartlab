"""`dartlab report` command. 기본은 Markdown 보고서, `--model` 은 전문 리포트 계약(ReportModel) JSON.

`--model` 은 공개 계약 `Company.reportModel(perspective)` 를 그대로 직렬화한다(self-calc 0).
기존 Markdown 경로는 불변 (추가형).
"""

from __future__ import annotations

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configureDartlab
from dartlab.core.logger import getLogger

_log = getLogger(__name__)
# 조회 실패는 절 하나를 비우되 프로세스를 죽이지 않는다. 다만 이유는 로그에 남긴다.
_FETCH_ERRORS = (AttributeError, KeyError, TypeError, ValueError)


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


def _overviewText(company, limit: int = 2000) -> str:
    """회사 개요 절의 본문을 평문으로 뽑는다. 없으면 빈 문자열."""
    import re

    try:
        df = company.panel("회사의 개요")
    except _FETCH_ERRORS as exc:
        _log.debug("기업 개요 조회 실패: %s", exc)
        return ""
    if df is None or getattr(df, "height", 0) == 0:
        return ""
    periodCols = [c for c in df.columns if re.fullmatch(r"\d{4}(Q[1-4])?", c)]
    if not periodCols:
        return ""
    latest = sorted(periodCols, reverse=True)[0]
    for value in df[latest].drop_nulls().to_list():
        plain = re.sub(r"<[^>]+>", " ", str(value))
        plain = re.sub(r"\s+", " ", plain).strip()
        if len(plain) > 50:
            return plain[:limit]
    return ""


def _gradeRows(company) -> list[tuple[str, str]]:
    """종합평가 축의 영역별 등급. 없으면 빈 목록."""
    try:
        verdict = company.analysis("financial", "종합평가")
    except _FETCH_ERRORS as exc:
        _log.debug("종합평가 조회 실패: %s", exc)
        return []
    if not isinstance(verdict, dict):
        return []
    items = (verdict.get("scorecard") or {}).get("items") or []
    return [(str(i.get("area")), str(i.get("grade"))) for i in items if i.get("area") and i.get("grade")]


def _buildReport(company, name: str, code: str, include: set | None) -> str:
    """Company 데이터를 수집하여 Markdown 보고서를 조립한다.

    호출은 전부 공개 계약(`panel` · `analysis`)으로만 한다. 예전에는 `company.BS` ·
    `company.ratios` · `company.insights` 처럼 계약에서 빠진 이름을 불렀고, 그 실패를
    `getattr(..., None)` 과 넓은 except 가 삼켜서 절 제목만 남고 본문이 통째로 비었다.
    보고서 네 절이 전부 빈 채로 출력되고 있었는데 아무 데서도 안 잡혔다.
    """
    parts: list[str] = [f"# {name} ({code}) 분석 보고서\n"]

    if include is None or "overview" in include:
        parts.append("## 기업 개요\n")
        parts.append(_overviewText(company) or "기업 개요 데이터가 없습니다.")

    if include is None or "finance" in include:
        parts.append("\n## 재무제표\n")
        wrote = False
        for axis, label in (("BS", "재무상태표"), ("IS", "손익계산서"), ("CF", "현금흐름표")):
            try:
                df = company.panel(axis)
            except _FETCH_ERRORS as exc:
                _log.debug("재무제표 %s 조회 실패: %s", axis, exc)
                continue
            if df is None or getattr(df, "height", 0) == 0:
                continue
            parts.append(f"### {label}\n")
            parts.append(_dfToMd(df.select(df.columns[:5]).head(15)))
            wrote = True
        if not wrote:
            parts.append("재무제표 데이터가 없습니다.")

    if include is None or "ratios" in include:
        parts.append("\n## 재무비율\n")
        wrote = False
        for axis in ("수익성", "안정성", "효율성"):
            try:
                result = company.analysis("financial", axis)
            except _FETCH_ERRORS as exc:
                _log.debug("재무비율 %s 조회 실패: %s", axis, exc)
                continue
            if not isinstance(result, dict) or not result:
                continue
            parts.append(f"### {axis}\n")
            parts.append(_ratioLines(result))
            wrote = True
        if not wrote:
            parts.append("재무비율 데이터가 없습니다.")

    if include is None or "insights" in include:
        parts.append("\n## 인사이트 등급\n")
        rows = _gradeRows(company)
        if rows:
            parts.append("| 영역 | 등급 |")
            parts.append("| --- | --- |")
            parts.extend(f"| {area} | {grade} |" for area, grade in rows)
        else:
            parts.append("인사이트 데이터가 없습니다.")

    parts.append("")
    return "\n".join(parts)


def _ratioLines(result: dict, limit: int = 6) -> str:
    """분석 축 결과 dict 에서 최근 시점 지표를 한 줄씩 뽑는다."""
    lines: list[str] = []
    for block, payload in result.items():
        if not isinstance(payload, dict):
            continue
        history = payload.get("history")
        if not isinstance(history, list) or not history:
            continue
        # 마지막 항목이 곧 최신은 아니다. 블록마다 정렬이 달라 2018 과 2025 가 섞여 나온다.
        entries = [h for h in history if isinstance(h, dict)]
        if not entries:
            continue
        latest = max(entries, key=lambda h: str(h.get("period") or ""))
        shown = []
        for key, value in latest.items():
            if key == "period" or value is None or isinstance(value, (dict, list)):
                continue
            shown.append(f"{key} {value:,.1f}" if isinstance(value, (int, float)) else f"{key} {value}")
            if len(shown) >= limit:
                break
        if shown:
            lines.append(f"- **{block}** ({latest.get('period', '')}): " + ", ".join(shown))
    return "\n".join(lines) + "\n" if lines else ""


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
