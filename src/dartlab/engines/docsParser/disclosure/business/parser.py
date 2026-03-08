"""사업의 내용 섹션 파싱 로직."""

from __future__ import annotations

import difflib
import re

import polars as pl

SECTION_KEYS = {
    "overview": ["사업의 개요"],
    "products": ["주요 제품"],
    "materials": ["원재료", "생산 및 설비"],
    "sales": ["매출", "수주"],
    "risk": ["위험관리", "파생거래"],
    "rnd": ["주요계약", "연구개발", "경영상"],
    "etc": ["기타 참고"],
    "financial": ["재무건전성"],
}


def classifySection(title: str) -> str | None:
    """섹션 타이틀을 키로 분류."""
    for key, keywords in SECTION_KEYS.items():
        for kw in keywords:
            if kw in title:
                return key
    return None


def extractFromSubSections(report: pl.DataFrame) -> dict[str, dict]:
    """하위 섹션이 분리된 경우 직접 매칭."""
    subSections = report.filter(
        pl.col("section_title").str.contains("사업의 개요")
        | pl.col("section_title").str.contains("주요 제품")
        | pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산 및 설비")
        | pl.col("section_title").str.contains("매출")
        | pl.col("section_title").str.contains("수주")
        | pl.col("section_title").str.contains("위험관리")
        | pl.col("section_title").str.contains("기타 참고")
        | pl.col("section_title").str.contains("연구개발")
        | pl.col("section_title").str.contains("주요계약")
        | pl.col("section_title").str.contains("경영상")
        | pl.col("section_title").str.contains("재무건전성")
    )

    if subSections.height == 0:
        return {}

    sections: dict[str, dict] = {}
    for row in subSections.iter_rows(named=True):
        title = row["section_title"]
        key = classifySection(title)
        if not key:
            continue
        content = row["section_content"]
        if key not in sections:
            sections[key] = {"title": title, "chars": len(content), "text": content}
        else:
            sections[key]["title"] += f" + {title}"
            sections[key]["chars"] += len(content)
            sections[key]["text"] += "\n\n" + content

    return sections


def extractFromUnified(report: pl.DataFrame) -> dict[str, dict]:
    """통합 텍스트에서 번호 패턴으로 분리."""
    mainSection = report.filter(
        pl.col("section_title").str.contains("사업의 내용")
    )
    if mainSection.height == 0:
        return {}

    fullText = mainSection.row(0, named=True)["section_content"]
    chunks = splitByNumber(fullText)

    sections: dict[str, dict] = {}
    for num, title, text in chunks:
        key = classifySection(title)
        if key:
            sections[key] = {
                "title": f"{num}. {title}",
                "chars": len(text),
                "text": text,
            }

    return sections


def splitByNumber(text: str) -> list[tuple[str, str, str]]:
    """텍스트를 순차 번호 패턴으로 분리."""
    pattern = re.compile(r"^(\d+)\.\s+(.+?)$", re.MULTILINE)
    allMatches = list(pattern.finditer(text))

    topMatches = []
    expectedNum = 1
    for m in allMatches:
        num = int(m.group(1))
        if num == expectedNum:
            topMatches.append(m)
            expectedNum = num + 1
        elif num == 1 and expectedNum > 2:
            break

    chunks = []
    for i, m in enumerate(topMatches):
        num = m.group(1)
        title = m.group(2).strip()
        start = m.end()
        end = topMatches[i + 1].start() if i + 1 < len(topMatches) else len(text)
        body = text[start:end].strip()
        chunks.append((num, title, body))

    return chunks


def getBusinessText(report: pl.DataFrame) -> str | None:
    """보고서에서 사업 개요 텍스트 추출 (변경 탐지용)."""
    overview = report.filter(
        pl.col("section_title").str.starts_with("1.")
        & pl.col("section_title").str.contains("사업의 개요")
    )
    if overview.height > 0:
        return overview.row(0, named=True)["section_content"]

    main = report.filter(
        pl.col("section_title").str.contains("사업의 내용")
    )
    if main.height > 0:
        return main.row(0, named=True)["section_content"]

    return None


def computeChanges(
    df: pl.DataFrame, years: list[str]
) -> list[dict]:
    """연도별 사업 내용 변경률 계산."""
    changes = []
    prevText = None

    for year in years:
        annual = df.filter(
            (pl.col("year") == year)
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
        if annual.height == 0:
            continue

        overview = annual.filter(
            pl.col("section_title").str.starts_with("1.")
            & pl.col("section_title").str.contains("사업의 개요")
        )
        if overview.height > 0:
            text = overview.row(0, named=True)["section_content"]
        else:
            main = annual.filter(
                pl.col("section_title").str.contains("사업의 내용")
            )
            if main.height > 0:
                text = main.row(0, named=True)["section_content"]
            else:
                continue

        if prevText is not None:
            ratio = difflib.SequenceMatcher(None, prevText, text).ratio()
            changedPct = round((1 - ratio) * 100, 1)

            diffLines = list(difflib.unified_diff(
                prevText.splitlines(), text.splitlines(),
                lineterm="", n=0
            ))
            added = sum(1 for l in diffLines if l.startswith("+") and not l.startswith("+++"))
            removed = sum(1 for l in diffLines if l.startswith("-") and not l.startswith("---"))

            changes.append({
                "year": int(year),
                "changedPct": changedPct,
                "added": added,
                "removed": removed,
                "totalChars": len(text),
            })

        prevText = text

    return changes
