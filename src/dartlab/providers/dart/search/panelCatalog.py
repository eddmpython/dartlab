"""Build search catalog rows from DART and EDGAR panel parquet files.

The search index reads only the leading part of each document. A periodic report is
reduced to its company and report name, the opening of the business sections and the
note headings so that topic words reach that leading part instead of the cover and
table of contents.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import polars as pl

from dartlab.providers.dart.search.catalog import normalizeCatalogRows
from dartlab.providers.dart.search.freshness import DEFAULT_DATE_COLUMNS, normalizeSearchDate, periodToDataAsOf

DATE_COLUMNS: tuple[str, ...] = DEFAULT_DATE_COLUMNS
PANEL_CATALOG_SOURCES = {"dartPanel", "edgarPanel"}
# 패널 문서를 만드는 방식의 판. 바뀌면 원격 대조가 모든 패널 파일을 다시 카탈로그에 넣는다.
PANEL_SOURCE_VERSION = "v2"
PANEL_TEXT_LIMIT = 4000
PANEL_SECTION_LIMIT = 2000


# 검색 색인은 본문 앞부분만 읽는다. 보고서 하나를 표지·목차 대신 회사명, 보고서명, 사업 본문 첫머리,
# 주석 제목 순으로 줄여 그 앞부분에 주제 단서가 들어가게 한다.
_PANEL_PATH_SEP = chr(0x241F)
_NOTE_DASHES = chr(0x2013) + chr(0x2014)
_PANEL_NOTE_SHARE = 480
_PANEL_MIN_SHARE = 160
_PANEL_MAX_SHARE = 600
_PANEL_NOTE_SCAN = 200_000
_PANEL_NOTE_MAX = 80
_PERIODIC_KINDS = ("사업보고서", "반기보고서", "분기보고서")
_QUARTER_KIND = {1: "분기보고서", 2: "반기보고서", 3: "분기보고서", 4: "사업보고서"}
_PERIOD_RE = re.compile(r"^(\d{4})Q([1-4])$")
_VERSION_RE = re.compile(r"^\d+(?:\.\d+)+$")
_LEGAL_FORM_RE = re.compile(r"주식회사|\(주\)|㈜")
_NAME_CHAR_RE = re.compile(r"[A-Za-z가-힣]")
_DART_NOTE_RE = re.compile(r"(?<![\d.,])\d{1,2}\.\s{0,2}([가-힣][가-힣·]{1,14}(?:\s[가-힣·]{1,10}){0,3})")
_EDGAR_NOTE_RE = re.compile(r"\bNOTE\s+\d{1,2}\s*[" + _NOTE_DASHES + r":.\-]\s*", re.IGNORECASE)
_EDGAR_TITLE_JOINERS = {"and", "of", "for", "in", "on", "to", "the"}
_EDGAR_ITEM_RE = re.compile(r"\bitem\s+(\d{1,2}[a-c]?)\b", re.IGNORECASE)
_PANEL_SKIP_CHAPTERS = ("대표이사 등의 확인", "전문가의 확인", "상세표")
_EDGAR_TABLE_LEAVES = {"IS", "BS", "CF", "CIS", "SCE", "EF"}
_DART_SECTION_RANK = (("사업의 내용", 0), ("경영진단", 1), ("재무에 관한", 2), ("회사의 개요", 3))
_EDGAR_SECTION_RANK = (
    ("item 1a", 0),
    ("risk factors", 0),
    ("item 7.", 1),
    ("management", 1),
    ("business", 2),
    ("legal proceedings", 3),
    ("financial statements", 4),
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)


def iterPanelCatalogFrames(
    source: str,
    files: Iterable[str | Path],
    *,
    sourceDataAsOf: str,
    sourceAdapterVersion: str,
) -> Iterator[pl.DataFrame]:
    """Turn panel parquet files into one search catalog row per filing.

    Args:
        source: ``dartPanel`` or ``edgarPanel``.
        files: Panel parquet files, one company or ticker per file.
        sourceDataAsOf: Fallback freshness for rows without a filing date.
        sourceAdapterVersion: Adapter version copied into catalog rows.

    Returns:
        Iterator[pl.DataFrame]: Normalized catalog frames, one per non-empty file.
        Files with ``sectionPath`` produce a bounded digest that leads with the
        company, report name, business sections and note headings. Older files
        without it keep the joined leading text.

    Raises:
        ValueError: When a file is unreadable or lacks ``rceptNo``/``contentRaw``.

    Example:
        >>> list(iterPanelCatalogFrames("dartPanel", [], sourceDataAsOf="", sourceAdapterVersion="v2"))
        []
    """
    for rawPath in files:
        path = Path(rawPath)
        try:
            schema = set(pl.scan_parquet(path).collect_schema().names())
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ValueError(f"panel catalog source unreadable: {path}") from exc
        if not {"rceptNo", "contentRaw"}.issubset(schema):
            raise ValueError(f"panel catalog source schema invalid: {path}")
        readCols = [
            col
            for col in (
                "rceptNo",
                "period",
                "contentRaw",
                "sectionLeaf",
                "corp",
                "chapter",
                "sectionPath",
                "leafType",
                "blockOrder",
                *DATE_COLUMNS,
            )
            if col in schema
        ]
        try:
            df = pl.read_parquet(path, columns=readCols)
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ValueError(f"panel catalog source unreadable: {path}") from exc
        if df.height == 0:
            continue
        for col in ("period", "sectionLeaf", "corp"):
            if col not in df.columns:
                df = df.with_columns(pl.lit("").alias(col))
        if "sectionPath" in df.columns:
            frame = normalizeCatalogRows(
                _panelDocumentRows(
                    source, df, code=path.stem, sourceDataAsOf=sourceDataAsOf, sourceAdapterVersion=sourceAdapterVersion
                )
            )
            if frame.height:
                yield frame
            continue
        try:
            rolled = (
                df.with_columns(pl.col("contentRaw").cast(pl.Utf8).str.slice(0, PANEL_SECTION_LIMIT))
                .group_by("rceptNo", maintain_order=True)
                .agg(
                    pl.col("contentRaw").alias("parts"),
                    pl.col("sectionLeaf").first().alias("sectionLeaf"),
                    pl.col("period").first().alias("period"),
                    pl.col("corp").first().alias("corp"),
                    *[pl.col(col).first().alias(col) for col in DATE_COLUMNS if col in df.columns],
                )
            )
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ValueError(f"panel catalog source aggregation failed: {path}") from exc
        rows: list[dict[str, Any]] = []
        code = path.stem
        for row in rolled.iter_rows(named=True):
            rceptNo = str(row.get("rceptNo") or "")
            if not rceptNo:
                continue
            parts = row.get("parts") or []
            text = _stripPanelText(" ".join(part for part in parts if part))
            if not text:
                continue
            dataAsOf = _sourceDataAsOfFromPanelRow(row, source=source, rceptNo=rceptNo)
            out: dict[str, Any] = {
                "source": source,
                "rceptNo": rceptNo,
                "sectionOrder": 0,
                "period": str(row.get("period") or ""),
                "sectionLeaf": str(row.get("sectionLeaf") or ""),
                "contentRaw": text,
                "date": dataAsOf,
                "sourceDataAsOf": dataAsOf or sourceDataAsOf,
                "sourceAdapterVersion": sourceAdapterVersion,
            }
            if source == "edgarPanel":
                out["ticker"] = code
                out["accession"] = rceptNo
                out["companyName"] = str(row.get("corp") or code)
            else:
                out["stockCode"] = code
                out["companyName"] = str(row.get("corp") or code)
            rows.append(out)
        frame = normalizeCatalogRows(rows)
        if frame.height:
            yield frame


def _panelDocumentRows(
    source: str,
    df: pl.DataFrame,
    *,
    code: str,
    sourceDataAsOf: str,
    sourceAdapterVersion: str,
) -> list[dict[str, Any]]:
    """섹션 경로가 있는 패널 파일을 보고서마다 문서 한 건으로 바꾼다."""
    for col in ("chapter", "leafType"):
        if col not in df.columns:
            df = df.with_columns(pl.lit("").alias(col))
    # 주석 제목을 찾는 블록만 길게, 나머지는 쓰는 만큼만 잘라 파이썬으로 넘긴다.
    path = pl.col("sectionPath").cast(pl.Utf8).fill_null("")
    noteBlock = (
        path.str.to_lowercase().str.contains("financial statements|item 8")
        if source == "edgarPanel"
        else pl.col("sectionLeaf").cast(pl.Utf8).fill_null("").str.contains("주석")
    )
    isText = pl.col("leafType").cast(pl.Utf8).fill_null("").is_in(["", "text"])
    raw = pl.col("contentRaw").cast(pl.Utf8).fill_null("")
    sliced = (
        pl.when(isText & noteBlock)
        .then(raw.str.slice(0, _PANEL_NOTE_SCAN * 4))
        .otherwise(raw.str.slice(0, PANEL_SECTION_LIMIT * 4))
    )
    df = df.with_columns(
        sliced.str.replace_all(r"(?is)<(?:style|script)\b[^>]*>.*?</(?:style|script)\s*>", " ")
        .str.replace_all(r"<[^>]+>", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
        .alias("contentRaw")
    )
    rows: list[dict[str, Any]] = []
    for group in df.partition_by("rceptNo", maintain_order=True):
        rceptNo = str(group.item(0, "rceptNo") or "")
        if not rceptNo:
            continue
        if "blockOrder" in group.columns:
            group = group.sort("blockOrder", maintain_order=True)
        first = group.row(0, named=True)
        doc = _panelDocument(
            source,
            group.select("chapter", "sectionPath", "sectionLeaf", "leafType", "contentRaw").iter_rows(),
            code=code,
            corp=str(first.get("corp") or ""),
            period=str(first.get("period") or ""),
        )
        if not doc["text"]:
            continue
        dataAsOf = _sourceDataAsOfFromPanelRow(first, source=source, rceptNo=rceptNo)
        out: dict[str, Any] = {
            "source": source,
            "rceptNo": rceptNo,
            "sectionOrder": 0,
            "period": str(first.get("period") or ""),
            "sectionLeaf": str(first.get("sectionLeaf") or ""),
            "companyName": doc["companyName"],
            "reportName": doc["reportName"],
            "title": doc["reportName"],
            "contentRaw": doc["text"],
            "date": dataAsOf,
            "sourceDataAsOf": dataAsOf or sourceDataAsOf,
            "sourceAdapterVersion": sourceAdapterVersion,
        }
        if source == "edgarPanel":
            out["ticker"] = code
            out["accession"] = rceptNo
        else:
            out["stockCode"] = code
        rows.append(out)
    return rows


def _panelDocument(
    source: str,
    blocks: Iterable[tuple[Any, ...]],
    *,
    code: str,
    corp: str,
    period: str,
) -> dict[str, str]:
    """태그를 걷어낸 보고서 블록(chapter, sectionPath, sectionLeaf, leafType, text)을 검색 문서로 줄인다."""
    edgar = source == "edgarPanel"
    texts: list[tuple[str, str, str, str, bool]] = []
    tables: list[str] = []
    for chapter, path, leaf, leafType, text in blocks:
        if leafType not in (None, "", "text"):
            tables.append(_unescapePanelText(str(text or ""))[:PANEL_SECTION_LIMIT])
            continue
        path, leaf = str(path or ""), str(leaf or "")
        lowered = path.lower()
        noteBlock = ("financial statements" in lowered or "item 8" in lowered) if edgar else "주석" in leaf
        body = _unescapePanelText(str(text or ""))[: _PANEL_NOTE_SCAN if noteBlock else PANEL_SECTION_LIMIT]
        if body:
            texts.append((str(chapter or ""), path, leaf, body, noteBlock))
    kind, name = ("", "") if edgar else _panelCover(texts)
    form = next((text[0] for text in texts if text[0]), "")
    companyName = name or corp or code
    reportName = _panelReportName(source, kind=kind, form=form, period=period)
    header = " ".join(part for part in (companyName, reportName) if part)

    # EDGAR는 위험 요인 같은 항목이 하위 제목마다 갈라져 있어 항목 번호로 묶어야 한 항목이 앞부분을 독차지하지 않는다.
    sections: dict[str, list[str]] = {}
    titles: dict[str, str] = {}
    ranks: dict[str, int] = {}
    notes: list[str] = []
    for chapter, path, leaf, body, noteBlock in texts:
        if not path or any(skip in chapter for skip in _PANEL_SKIP_CHAPTERS) or leaf in _EDGAR_TABLE_LEAVES:
            continue
        if noteBlock and edgar:
            notes.extend(_edgarNoteHeads(body))
        elif noteBlock:
            notes.extend(head.strip() for head in _DART_NOTE_RE.findall(body))
            continue
        title = path.rsplit(_PANEL_PATH_SEP, 1)[-1].strip()
        item = _EDGAR_ITEM_RE.search(title) if edgar else None
        key = f"Item {item.group(1).upper()}" if item else path
        rank = _panelSectionRank(path, edgar=edgar)
        if key not in sections:
            sections[key], titles[key], ranks[key] = [], title, rank
        elif len(title) < len(titles[key]):
            titles[key] = title
        ranks[key] = min(ranks[key], rank)
        sections[key].append(body[: PANEL_SECTION_LIMIT * 2])
    notes = list(dict.fromkeys(note for note in notes if note))[:_PANEL_NOTE_MAX]

    pieces: list[str] = []
    seen: set[str] = set()
    order = {key: index for index, key in enumerate(sections)}
    for key in sorted(sections, key=lambda item: (ranks[item], order[item])):
        title = titles[key]
        body = " ".join(sections[key])
        if title and body.startswith(title):
            body = body[len(title) :].strip()
        if not body or body[:120] in seen:
            continue
        seen.add(body[:120])
        pieces.append(f"[{title}] {body}" if title else body)
    noteText = (("Notes: " if edgar else "주석: ") + ", ".join(notes))[:_PANEL_NOTE_SHARE] if notes else ""
    if not pieces and not noteText:
        # 정정공시처럼 확인서만 담긴 보고서는 남은 블록을 그대로 이어 문서 수를 유지한다.
        joined = " ".join(part for part in [text[3] for text in texts] + tables if part)[:PANEL_TEXT_LIMIT]
        return {"companyName": companyName, "reportName": reportName, "text": _joinPanelText(header, joined)}

    parts = [header] if header else []
    budget = PANEL_TEXT_LIMIT - len(header)
    slots = pieces[:1] + ([noteText] if noteText else []) + pieces[1:]
    noteIndex = min(1, len(pieces)) if noteText else -1
    for index, piece in enumerate(slots):
        share = (
            len(piece)
            if index == noteIndex
            else min(_PANEL_MAX_SHARE, max(_PANEL_MIN_SHARE, budget // (len(slots) - index)))
        )
        parts.append(piece[:share])
        budget -= len(parts[-1]) + 1
        if budget <= 0:
            break
    return {"companyName": companyName, "reportName": reportName, "text": " ".join(parts)[:PANEL_TEXT_LIMIT]}


def _unescapePanelText(text: str) -> str:
    """polars에서 태그와 공백을 정리한 블록에 남은 HTML 엔티티만 푼다."""
    if "&" not in text:
        return text
    return _WS_RE.sub(" ", html.unescape(text)).strip()


def _joinPanelText(header: str, text: str) -> str:
    if not text:
        return ""
    return f"{header} {text}"[:PANEL_TEXT_LIMIT] if header else text


def _panelCover(texts: list[tuple[str, str, str, str, bool]]) -> tuple[str, str]:
    """DART 표지 첫 블록에서 보고서 종류와 법인 형태를 뗀 회사명을 읽는다."""
    words = texts[0][3].split() if texts else []
    if not words or words[0] not in _PERIODIC_KINDS:
        return "", ""
    index = 0
    while index < len(words) and (words[index].endswith("보고서") or _VERSION_RE.match(words[index])):
        index += 1
    name = words[index] if index < len(words) else ""
    if _LEGAL_FORM_RE.fullmatch(name) and index + 1 < len(words):
        name += words[index + 1]
    name = _LEGAL_FORM_RE.sub("", name).strip()
    if len(name) < 2 or name.endswith("보고서") or not _NAME_CHAR_RE.search(name):
        name = ""
    return words[0], name


def _panelReportName(source: str, *, kind: str, form: str, period: str) -> str:
    if source == "edgarPanel":
        return f"{form} ({period})" if form and period else form or period
    match = _PERIOD_RE.match(period)
    if not match:
        return kind
    quarter = int(match.group(2))
    return f"{kind or _QUARTER_KIND[quarter]} ({match.group(1)}.{quarter * 3:02d})"


def _panelSectionRank(path: str, *, edgar: bool) -> int:
    key = path.lower() if edgar else path
    for word, rank in _EDGAR_SECTION_RANK if edgar else _DART_SECTION_RANK:
        if word in key:
            return rank
    return 9


def _edgarNoteHeads(body: str) -> list[str]:
    """EDGAR 재무제표 주석의 "Note N" 제목을 대문자 구간이나 제목형 낱말 6개까지 읽는다.

    제목형에서는 소문자 낱말이 바로 뒤따르는 대문자 낱말을 다음 문장의 첫 낱말로 보고 멈춘다.
    """
    heads: list[str] = []
    for match in _EDGAR_NOTE_RE.finditer(body):
        words = body[match.end() : match.end() + 120].split()[:7]
        caps = bool(words) and words[0].isupper()
        picked: list[str] = []
        for index, word in enumerate(words[:6]):
            plain = not any(ch.isalpha() for ch in word)
            if caps:
                if not (word.isupper() or plain):
                    break
            elif not (plain or word.lower() in _EDGAR_TITLE_JOINERS):
                if not word[:1].isupper():
                    break
                following = words[index + 1] if index + 1 < len(words) else ""
                if index and following[:1].islower() and following.lower() not in _EDGAR_TITLE_JOINERS:
                    break
            picked.append(word)
        while picked and (picked[-1].lower() in _EDGAR_TITLE_JOINERS or not any(ch.isalpha() for ch in picked[-1])):
            picked.pop()
        if picked:
            heads.append(" ".join(picked).strip(" ,.;:").title() if caps else " ".join(picked).strip(" ,.;:"))
    return heads


def _sourceDataAsOfFromPanelRow(row: Mapping[str, Any], *, source: str, rceptNo: str) -> str:
    explicit = normalizeSearchDate(next((row.get(col) for col in DATE_COLUMNS if row.get(col)), ""))
    if explicit:
        return explicit
    if source == "edgarPanel":
        return periodToDataAsOf(row.get("period"))
    return rceptNo[:8] if len(rceptNo) >= 8 else periodToDataAsOf(row.get("period"))


def _stripPanelText(raw: str, *, limit: int | None = PANEL_TEXT_LIMIT) -> str:
    if not raw:
        return ""
    text = html.unescape(raw[: limit * 4] if limit is not None else raw)
    cleaned = _WS_RE.sub(" ", _TAG_RE.sub(" ", _BLOCK_RE.sub(" ", text))).strip()
    return cleaned[:limit] if limit is not None else cleaned
