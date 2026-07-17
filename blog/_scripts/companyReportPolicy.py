"""기업이야기 전용 편집 금지 규칙."""

from __future__ import annotations

import re
from pathlib import Path

COMPANY_REPORT_CATEGORY_RE = re.compile(r"^\s*category:\s*[\"']?company-reports\b", re.M)
DEBT_RATIO_TERM_RE = re.compile(
    r"부채\s*비율|"
    r"부채\s*(?:자본|(?:대|/)\s*자본)\s*비율|"
    r"debt(?:[-\s]+ratio|[-\s/]*to[-\s/]*equity(?:[-\s]+ratio)?|\s*/\s*equity)|"
    r"liabilit(?:y|ies)[-\s/]*to[-\s/]*(?:shareholders?[-\s]*)?equity|"
    r"gearing\s+ratio|"
    r"\bD\s*/\s*E(?:\s+ratio)?\b",
    re.I,
)
DEBT_RATIO_PROXY_RE = re.compile(
    r"(?:총)?부채(?:총계)?\s*(?:/|÷|대)\s*(?:자기|총)?자본(?:총계)?|"
    r"(?:자기|총)?자본(?:총계)?\s*대비\s*(?:총)?부채(?:총계)?|"
    r"(?:총)?부채(?:총계)?[^.!?\n|]{0,60}(?:자기|총)?자본(?:총계)?[^.!?\n|]{0,30}(?:나누|%|퍼센트|배)|"
    r"(?:자기|총)?자본(?:총계)?[^.!?\n|]{0,60}(?:총)?부채(?:총계)?[^.!?\n|]{0,30}(?:나누|%|퍼센트|배)",
    re.I,
)


def validateCompanyReportDebtRatioBan(postDir: Path) -> list[str]:
    """기업이야기 공개물과 기획물에서 금지 지표 및 우회 계산을 찾는다."""
    indexPath = postDir / "index.md"
    if not indexPath.is_file():
        return []
    indexText = indexPath.read_text(encoding="utf-8")
    if not COMPANY_REPORT_CATEGORY_RE.search(indexText):
        return []

    sources = [("index.md", indexText)]
    for planName in ("brief.json", "plan.json", "cards.plan.json"):
        planPath = postDir / planName
        if planPath.is_file():
            sources.append((planName, planPath.read_text(encoding="utf-8")))

    assetsDir = postDir / "assets"
    if assetsDir.is_dir():
        for svgPath in sorted(assetsDir.glob("*.svg")):
            sources.append((f"assets/{svgPath.name}", svgPath.read_text(encoding="utf-8")))

    errors: list[str] = []
    for sourceName, text in sources:
        match = DEBT_RATIO_TERM_RE.search(text) or DEBT_RATIO_PROXY_RE.search(text)
        if match:
            found = re.sub(r"\s+", " ", match.group(0)).strip()
            errors.append(
                f"기업이야기 금지 지표 발견({sourceName}): {found!r}. "
                "절대 차입금, 순차입금, 만기, 이자비용, 현금흐름으로 다시 설명해야 함"
            )
    return errors
