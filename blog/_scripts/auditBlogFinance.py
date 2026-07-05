"""블로그 finance 표 전수 검증.

각 글에서 markdown finance 표를 파싱하고 dartlab `c.select(..., freq="Y")`
실측값과 1:1 비교한다. 코드/표/실측 3자 정합 확인.

실행:
    uv run python -X utf8 blog/_scripts/auditBlogFinance.py
    uv run python -X utf8 blog/_scripts/auditBlogFinance.py --post 090430:blog/05-company-reports/92-090430-amorepacific/index.md
"""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

import dartlab

POSTS = [
    ("000660", "blog/05-company-reports/01-000660-skhynix/index.md"),
    ("003230", "blog/05-company-reports/02-003230-samyang-foods/index.md"),
    ("034020", "blog/05-company-reports/03-034020-doosan-enerbility/index.md"),
    ("196170", "blog/05-company-reports/04-196170-alteogen/index.md"),
    ("011200", "blog/05-company-reports/05-011200-hmm/index.md"),
    ("068270", "blog/05-company-reports/06-068270-celltrion/index.md"),
]


# (raw markdown text → numeric value in 원). value can be None on parse fail.
def parseCell(raw: str) -> float | None:
    s = raw.strip().replace("**", "").replace("*", "")
    if s in ("", "—", "-", "???", "?"):
        return None
    s = s.replace(",", "").replace("원", "").replace("조", "").replace("억", "")
    s = s.replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None


def normalize(actual: float | None, unit: str) -> float | None:
    """실측값(원) → 표시 단위로 정규화."""
    if actual is None:
        return None
    if unit == "$B":
        return actual / 1e9
    if unit == "$M":
        return actual / 1e6
    if unit == "조":
        return actual / 1e12
    if unit == "억":
        return actual / 1e8
    if unit == "백만":
        return actual / 1e6
    return actual


def detectUnit(text: str) -> str:
    """표 단위 텍스트에서 추출. 우선순위: 가장 가까운 단위 키워드."""
    if "$B" in text or "USD B" in text or "billion" in text.lower():
        return "$B"
    if "$M" in text or "USD M" in text or "million" in text.lower():
        return "$M"
    # 가장 가까운 단위 (text 끝쪽 = 표에 가까움)
    last_eok = max(text.rfind("억원"), text.rfind("(억"))
    last_jo = max(text.rfind("조원"), text.rfind("(조"))
    last_mil = text.rfind("백만원")
    if last_mil > max(last_eok, last_jo):
        return "백만"
    if last_eok > last_jo:
        return "억"
    return "조"


def parseTable(block: str):
    """markdown table → list of (label, {year: cellValue}) + headers."""
    lines = [l.strip() for l in block.strip().split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return None, None
    header = [h.strip() for h in lines[0].strip("|").split("|")]
    # year columns: skip first label col, parse rest
    year_cols = []
    for h in header[1:]:
        m = re.search(r"(20\d{2})", h)
        if m:
            year_cols.append(m.group(1))
        else:
            year_cols.append(None)
    rows = []
    for line in lines[2:]:  # skip header + separator
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = cells[0].strip().replace("**", "").strip()
        values = {}
        for i, col in enumerate(year_cols, start=1):
            if col is None or i >= len(cells):
                continue
            values[col] = parseCell(cells[i])
        rows.append((label, values))
    return rows, year_cols


def findFinanceTables(text: str):
    """마크다운에서 c.select(...) 코드 블록 + 그 직후 표를 추출."""
    pattern = re.compile(
        r'```python\n([^`]*?c\.select\("(IS|BS|CF|CIS)",\s*\[([^\]]+)\][^)]*\)[^`]*?)\n```\s*\n+(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)',
        re.DOTALL,
    )
    out = []
    for m in pattern.finditer(text):
        code = m.group(1)
        topic = m.group(2)
        keys_raw = m.group(3)
        keys = [k.strip().strip('"').strip("'") for k in keys_raw.split(",")]
        keys = [k for k in keys if k]
        table = m.group(4)
        # 단위 컨텍스트: 표 첫 컬럼 헤더 + 표 직전 400자 (섹션 타이틀 포함)
        first_col_header = ""
        first_line = table.split("\n")[0]
        if "|" in first_line:
            cells = first_line.strip("|").split("|")
            if cells:
                first_col_header = cells[0]
        before_ctx = text[max(0, m.start() - 400) : m.start()]
        out.append(
            {
                "code": code.strip(),
                "topic": topic,
                "keys": keys,
                "table": table,
                "unitHint": first_col_header + " " + before_ctx,
                "lineApprox": text[: m.start()].count("\n") + 1,
            }
        )
    return out


def annualValues(row: dict) -> dict[str, float]:
    annual = {k: v for k, v in row.items() if k.isdigit() and len(k) == 4}
    if annual:
        return annual

    grouped: dict[str, float] = {}
    for key, value in row.items():
        m = re.fullmatch(r"(20\d{2})Q[1-4]", str(key))
        if not m or value is None:
            continue
        year = m.group(1)
        grouped[year] = grouped.get(year, 0.0) + float(value)
    return grouped


def extractBlockCode(codeBlock: str) -> str | None:
    """코드 블록에서 단일 회사 코드를 뽑는다. tech-story 는 표마다 회사가 다르므로
    `Company("454910")` 처럼 블록 안에 박힌 코드를 표별로 바인딩한다.
    코드가 2개 이상(예: for code in [...]) 이면 표-회사 1:1 매칭이 모호해 None."""
    codes = re.findall(r'Company\(["\'](\d{6})["\']\)', codeBlock)
    unique = list(dict.fromkeys(codes))
    return unique[0] if len(unique) == 1 else None


def revenueUnit(rowLabel: str) -> float | None:
    """표 행 라벨(예 '매출 (억원)')에서 매출 표시 단위를 뽑는다."""
    if "조" in rowLabel:
        return 1e12
    if "억" in rowLabel:
        return 1e8
    return None


def auditTechStoryPost(path: str):
    """tech-story(다회사) 글의 회사별 매출 행을 표-회사 바인딩으로 실측 대조.

    매출은 raw 값이라 drift 가 바로 잡힌다. 이익률(%) 행은 파생이라 audit_seo 깊이
    게이트와 사람 검증에 맡기고 여기서는 건너뛴다. 회사보고서용 auditPost 와 달리
    표마다 Company 코드를 다시 바인딩하는 것이 핵심."""
    text = Path(path).read_text(encoding="utf-8")
    tables = findFinanceTables(text)
    if not tables:
        return [{"path": path, "warn": "no finance tables found"}]

    companies: dict[str, object] = {}
    issues = []
    for t in tables:
        code = extractBlockCode(t["code"])
        if not code:
            continue  # 다회사 for-loop 블록은 표-회사 매칭 모호 → 건너뜀
        if code not in companies:
            try:
                companies[code] = dartlab.Company(code)
            except Exception as e:  # noqa: BLE001
                issues.append({"path": path, "code": code, "error": f"load failed: {e}"})
                companies[code] = None
        c = companies[code]
        if c is None:
            continue
        try:
            df = c.select("IS", ["매출액"], freq="Y")
        except Exception as e:  # noqa: BLE001
            issues.append({"path": path, "code": code, "error": f"select failed: {e}"})
            continue
        actual = {}
        for r in df.to_dicts():
            if r.get("항목") == "매출액":
                actual = {k: v for k, v in r.items() if isinstance(k, str) and k.isdigit() and len(k) == 4}
        rows, _ = parseTable(t["table"])
        if not rows:
            continue
        for label, yearValues in rows:
            if "매출" not in label:
                continue
            unit = revenueUnit(label)
            if unit is None:
                continue
            for year, tableV in yearValues.items():
                if tableV is None or not (year.isdigit() and len(year) == 4):
                    continue
                actV = actual.get(year)
                if actV is None:
                    continue
                norm = actV / unit
                tol = max(0.6, abs(norm) * 0.02)
                if abs(norm - tableV) > tol:
                    issues.append(
                        {
                            "path": Path(path).parent.name,
                            "code": code,
                            "line": t["lineApprox"],
                            "label": label,
                            "year": year,
                            "table": tableV,
                            "actual": round(norm, 1),
                        }
                    )
    return issues


def auditPost(code: str, path: str):
    text = Path(path).read_text(encoding="utf-8")
    tables = findFinanceTables(text)
    if not tables:
        return [{"path": path, "warn": "no finance tables found"}]

    c = dartlab.Company(code)
    issues = []
    for t in tables:
        try:
            df = c.select(t["topic"], t["keys"], freq="Y")
        except Exception as e:
            issues.append(
                {
                    "path": path,
                    "line": t["lineApprox"],
                    "topic": t["topic"],
                    "keys": t["keys"],
                    "error": f"select failed: {e}",
                }
            )
            continue

        rows, year_cols = parseTable(t["table"])
        if rows is None:
            continue
        unit = detectUnit(t.get("unitHint", "") + " " + t["table"])

        # build actual lookup: {label: {year: value}}
        labelCol = "항목" if "항목" in df.columns else df.columns[0]
        actual = {}
        for r in df.to_dicts():
            lbl = r.get(labelCol)
            actual[lbl] = annualValues(r)

        for label, year_values in rows:
            if label not in actual:
                # try fuzzy label match (label 변형)
                continue
            for year, table_v in year_values.items():
                if table_v is None:
                    continue
                act_raw = actual[label].get(year)
                act_norm = normalize(act_raw, unit)
                if act_norm is None:
                    # 표가 0이고 실측이 None이면 "데이터 없음 = 0" 으로 본문에서 의미 동일
                    if table_v == 0:
                        continue
                    issues.append(
                        {
                            "path": path,
                            "line": t["lineApprox"],
                            "topic": t["topic"],
                            "label": label,
                            "year": year,
                            "table": table_v,
                            "actual": None,
                            "msg": "actual missing",
                        }
                    )
                    continue
                # tolerance: 0.5단위 반올림 + 1% 상대 (둘 중 큰 값)
                tol = max(0.55, abs(act_norm) * 0.012)
                if abs(act_norm - table_v) > tol:
                    issues.append(
                        {
                            "path": path,
                            "line": t["lineApprox"],
                            "topic": t["topic"],
                            "label": label,
                            "year": year,
                            "table": table_v,
                            "actual": round(act_norm, 3),
                            "diff": round(act_norm - table_v, 3),
                            "unit": unit,
                        }
                    )
    return issues


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit markdown finance tables against dartlab c.select outputs.")
    parser.add_argument(
        "--post",
        action="append",
        default=[],
        metavar="CODE:PATH",
        help="Audit one post. Can be repeated. Defaults to the legacy first-post batch.",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional report path. Defaults to the OS temp directory; use 'none' to skip writing.",
    )
    return parser.parse_args()


def parsePostArg(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise ValueError(f"--post must be CODE:PATH, got {raw!r}")
    code, path = raw.split(":", 1)
    code = code.strip()
    path = path.strip()
    if not code or not path:
        raise ValueError(f"--post must include both CODE and PATH, got {raw!r}")
    return code, path


def main():
    args = parseArgs()
    posts = [parsePostArg(raw) for raw in args.post] if args.post else POSTS
    all_issues = []
    for code, path in posts:
        print(f"\n=== {code} {Path(path).parent.name} ===")
        # tech-story(다회사) 글은 표-회사 바인딩 auditor 로 라우팅. code 인자는 무시(표별로 재바인딩).
        if "08-tech-story" in path.replace("\\", "/"):
            issues = auditTechStoryPost(path)
        else:
            issues = auditPost(code, path)
        if not issues:
            print("  OK — all values match")
            continue
        for it in issues:
            print(f"  {it}")
        all_issues.extend(issues)

    print(f"\n=== TOTAL: {len(all_issues)} issues ===")
    if args.out.lower() == "none":
        return
    reportPath = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "dartlab_audit_blog_finance_report.md"
    reportPath.parent.mkdir(parents=True, exist_ok=True)
    reportPath.write_text(
        "# Blog Finance Audit\n\n" + f"{len(all_issues)} mismatches\n\n" + "\n".join(f"- {it}" for it in all_issues),
        encoding="utf-8",
    )
    print(f"report: {reportPath}")


if __name__ == "__main__":
    main()
