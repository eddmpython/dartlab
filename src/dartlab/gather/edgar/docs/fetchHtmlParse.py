"""edgar/docs/fetch HTML 다운로드/파싱 — fetch.py 분할 (규칙 3 LoC).

EDGAR 원문 HTML 다운로드 + iXBRL 정제 + Item splitter (10-K/10-Q/20-F/40-F).
"""

from __future__ import annotations

import re
import time
import warnings

import httpx
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from bs4.element import NavigableString

from dartlab.core.htmlMarkdown import tableToMarkdown as _tableToMarkdown
from dartlab.gather.edgar.docs._const import HEADERS, REQUEST_INTERVAL

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def _downloadHtml(url: str, *, maxRetries: int = 3) -> str:
    """HTML 다운로드 (재시도 포함)."""
    lastErr: Exception | None = None
    for attempt in range(maxRetries):
        time.sleep(REQUEST_INTERVAL if attempt == 0 else REQUEST_INTERVAL * (2**attempt))
        try:
            resp = httpx.get(url, headers=HEADERS, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            return resp.text
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            lastErr = e
            continue
    raise lastErr or httpx.HTTPError(f"failed after {maxRetries} retries: {url}")


def _submissionTextUrl(filing: dict) -> str:
    filingUrl = str(filing["filingUrl"])
    baseDir = filingUrl.rsplit("/", 1)[0]
    accession = str(filing["accessionNumber"])
    return f"{baseDir}/{accession}.txt"


def _filingDirectoryUrl(filing: dict) -> str:
    return str(filing["filingUrl"]).rsplit("/", 1)[0]


def _filingIndexJsonUrl(filing: dict) -> str:
    return f"{_filingDirectoryUrl(filing)}/index.json"


def _listFilingHtmlDocuments(filing: dict) -> list[str]:
    time.sleep(REQUEST_INTERVAL)
    resp = httpx.get(_filingIndexJsonUrl(filing), headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    items = resp.json().get("directory", {}).get("item", [])
    names: list[str] = []
    for item in items:
        name = str(item.get("name") or "")
        lower = name.lower()
        if not lower.endswith((".htm", ".html")):
            continue
        if lower.endswith("-index.html") or lower.endswith("-index-headers.html"):
            continue
        if re.fullmatch(r"r\d+\.htm", lower):
            continue
        names.append(name)
    return names


def _classify40FDocumentName(name: str) -> str | None:
    lower = name.lower()
    if "annualinformation" in lower or "annual-information" in lower or "annualinformationfo" in lower:
        return "Annual Information Form"
    if lower.startswith("mda") or "managementdiscussion" in lower or "management-discussion" in lower:
        return "MD&A"
    if "financialstatement" in lower or "financial-statements" in lower or lower.endswith("_d2.htm"):
        return "Financial Statements"
    return None


def _isLowQualityText(text: str) -> bool:
    sample = text[:8000].strip()
    if len(sample) < 200:
        return True
    letters = sum(ch.isalpha() for ch in sample)
    spaces = sample.count(" ")
    if letters > 0 and spaces / max(len(sample), 1) < 0.02:
        return True
    return False


def _downloadFilingSource(filing: dict) -> str:
    html = _downloadHtml(str(filing["filingUrl"]))
    if html.strip():
        return html
    return _downloadHtml(_submissionTextUrl(filing))


def _split40FSections(filing: dict, primaryText: str) -> list[dict]:
    sections: list[dict] = []
    seenTitles: set[str] = set()

    try:
        for name in _listFilingHtmlDocuments(filing):
            title = _classify40FDocumentName(name)
            if title is None or title in seenTitles:
                continue
            url = f"{_filingDirectoryUrl(filing)}/{name}"
            text = _htmlToText(_downloadHtml(url))
            if _isLowQualityText(text):
                continue
            sections.append({"title": title, "content": text})
            seenTitles.add(title)
    except httpx.HTTPError:
        pass

    if sections:
        return sections
    headingSections = _split40FPrimaryText(primaryText)
    if headingSections:
        return headingSections
    return [{"title": "Full Document", "content": primaryText}]


def _split40FPrimaryText(text: str) -> list[dict]:
    starts: list[dict[str, int | str]] = []
    offset = 0
    seen: set[str] = set()
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        upper = stripped.upper()
        if upper in FORTY_F_HEADINGS and upper not in seen:
            starts.append({"title": stripped, "start": offset})
            seen.add(upper)
        offset += len(line)

    if len(starts) < 2:
        return []

    sections: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        sections.append(
            {
                "title": str(startInfo["title"]).title(),
                "content": content,
            }
        )
    return sections


def _extractItemHeaders(soup) -> None:
    for tag in soup.find_all(["font", "span", "b", "strong", "p", "div"]):
        text = tag.get_text(strip=True)
        if not _ITEM_HEADER_RE.match(text) and not _ITEM_HEADER_EXACT_RE.match(text):
            continue
        if tag.find_parent("a", href=True) or tag.find("a", href=True):
            continue
        parentTable = tag.find_parent("table")
        if not parentTable:
            continue
        if tag.name in ("p", "div") and len(text) > 120:
            continue
        headerP = soup.new_tag("p")
        headerP.string = text
        parentTable.insert_before(headerP)


def _htmlToText(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()
    for tag in soup.find_all(style=True):
        # bs4 edge case: find_all이 attrs=None인 노드를 반환할 수 있음
        attrs = getattr(tag, "attrs", None)
        if not attrs:
            continue
        style = str(attrs.get("style") or "").lower()
        if "display:none" in style or "visibility:hidden" in style:
            tag.decompose()
    for tag in soup.find_all(_IX_DECOMPOSE_RE):
        tag.decompose()
    for ix_tag in soup.find_all(_IX_UNWRAP_RE):
        ix_tag.unwrap()
    _extractItemHeaders(soup)
    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(NavigableString(f"\n\n{md}\n\n"))
        else:
            table.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4"]):
        p.insert_after("\n")
    text = (soup.body or soup).get_text("\n")
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return _MULTI_NEWLINE_RE.sub("\n\n", text).strip()


def _splitItems(text: str, formType: str) -> list[dict]:
    if formType == "40-F":
        return [{"title": "Full Document", "content": text}]
    if formType == "10-Q":
        return _splitQuarterlyItems(text)

    itemNames = ITEM_NAMES_20F if formType == "20-F" else ITEM_NAMES_10K
    matches = list(ITEM_PATTERN.finditer(text))
    if not matches:
        tableItems = _splitTableStructuredItems(text, itemNames)
        if tableItems:
            return tableItems
        return [{"title": "Full Document", "content": text}]

    startsByItem: dict[str, dict[str, int | str]] = {}
    for match in matches:
        itemNum = match.group(1).upper()
        canonTitle = itemNames.get(itemNum, match.group(2).strip().rstrip("."))
        startsByItem[itemNum] = {
            "item_num": itemNum,
            "start": match.start(),
            "title": f"Item {itemNum}. {canonTitle}",
        }

    starts = sorted(startsByItem.values(), key=lambda row: int(row["start"]))
    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )
    return items


def _splitTableStructuredItems(text: str, itemNames: dict[str, str]) -> list[dict]:
    startsByItem: dict[str, dict[str, int | str]] = {}
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        match = ITEM_TABLE_LINE_PATTERN.match(stripped)
        if match:
            itemNum = match.group(1).upper()
            title = itemNames.get(itemNum) or re.sub(r"\s+", " ", match.group(2).strip(" |"))
            if title:
                startsByItem[itemNum] = {
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Item {itemNum}. {title}",
                }
        offset += len(line)

    starts = sorted(startsByItem.values(), key=lambda row: int(row["start"]))
    if len(starts) < 2:
        return []

    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )
    return items


def _splitQuarterlyItems(text: str) -> list[dict]:
    body = _quarterlyBodyText(text)
    if not body:
        return [{"title": "Full Document", "content": text}]

    bodyLines = body.splitlines()
    startsByKey: dict[tuple[str, str], dict[str, int | str]] = {}
    currentPart: str | None = None
    offset = 0

    for idx, rawLine in enumerate(bodyLines):
        line = rawLine + "\n"
        stripped = rawLine.strip()
        if not stripped:
            offset += len(line)
            continue
        partMatch = PART_PATTERN.match(stripped)
        if partMatch:
            currentPart = partMatch.group(1).upper()
            offset += len(line)
            continue

        if stripped.upper() == "PART" and idx + 1 < len(bodyLines):
            nextLine = bodyLines[idx + 1].strip()
            nextMatch = re.match(r"^(I|II)\b", nextLine, re.IGNORECASE)
            if nextMatch:
                currentPart = nextMatch.group(1).upper()
                offset += len(line)
                continue

        partTableMatch = PART_TABLE_LINE_PATTERN.match(stripped)
        if partTableMatch:
            currentPart = partTableMatch.group(1).upper()
            offset += len(line)
            continue

        itemMatch = ITEM_LINE_PATTERN.match(stripped)
        if itemMatch and currentPart is not None:
            itemNum = itemMatch.group(1).upper()
            key = (currentPart, itemNum)
            canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}")
            if idx + 1 < len(bodyLines):
                nextTitle = bodyLines[idx + 1].strip()
                if nextTitle and not PART_PATTERN.match(nextTitle) and not ITEM_LINE_PATTERN.match(nextTitle):
                    if not itemMatch.group(2).strip():
                        canonicalTitle = canonicalTitle or nextTitle
            if canonicalTitle:
                startsByKey[key] = {
                    "part": currentPart,
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                }
            offset += len(line)
            continue

        if stripped.upper() == "ITEM" and idx + 1 < len(bodyLines) and currentPart is not None:
            nextLine = bodyLines[idx + 1].strip()
            nextItemMatch = ITEM_NUMBER_TITLE_PATTERN.match(nextLine)
            if nextItemMatch:
                itemNum = nextItemMatch.group(1).upper()
                key = (currentPart, itemNum)
                canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}") or nextItemMatch.group(2).strip()
                if canonicalTitle:
                    startsByKey[key] = {
                        "part": currentPart,
                        "item_num": itemNum,
                        "start": offset,
                        "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                    }
                offset += len(line)
                continue

        itemTableMatch = ITEM_TABLE_LINE_PATTERN.match(stripped)
        if itemTableMatch and currentPart is not None:
            itemNum = itemTableMatch.group(1).upper()
            key = (currentPart, itemNum)
            titleText = itemTableMatch.group(2).strip()
            canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}") or titleText
            if canonicalTitle:
                startsByKey[key] = {
                    "part": currentPart,
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                }
        offset += len(line)

    starts = sorted(startsByKey.values(), key=lambda row: int(row["start"]))
    if len(starts) < 2:
        return [{"title": "Full Document", "content": body}]

    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(body)
        content = _cleanQuarterlySectionText(body[start:end].strip())
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )

    if len(items) < 2:
        return [{"title": "Full Document", "content": body}]
    return items


def _quarterlyBodyText(text: str) -> str:
    lines = text.splitlines()
    partStarts: list[int] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^PART\s+I\b", stripped, re.IGNORECASE):
            partStarts.append(idx)
            continue
        if stripped.upper() == "PART" and idx + 1 < len(lines):
            if re.match(r"^I\b", lines[idx + 1].strip(), re.IGNORECASE):
                partStarts.append(idx)
                continue
        if PART_TABLE_LINE_PATTERN.match(stripped):
            partStarts.append(idx)
    if len(partStarts) >= 2:
        return "\n".join(lines[partStarts[1] :]).strip()
    if partStarts:
        return "\n".join(lines[partStarts[0] :]).strip()
    return text


def _cleanQuarterlySectionText(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    headerSeen = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not headerSeen and ITEM_LINE_PATTERN.match(stripped):
            headerSeen = True
            cleaned.append(stripped)
            continue
        if stripped.startswith("| Item ") or stripped.startswith("| PART "):
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()


# ── fetch 상수/헬퍼 (순환 회피: fetch 가 본 모듈을 bottom re-export 하므로 본 import 를 끝으로) ──
from dartlab.gather.edgar.docs.fetch import (
    _ITEM_HEADER_EXACT_RE,
    _ITEM_HEADER_RE,
    _IX_DECOMPOSE_RE,
    _IX_UNWRAP_RE,
    _MULTI_NEWLINE_RE,
    _WHITESPACE_RE,
    FALLBACK_FULL_DOCUMENT_FORMS,
    FORTY_F_HEADINGS,
    ITEM_LINE_PATTERN,
    ITEM_NAMES_10K,
    ITEM_NAMES_10Q,
    ITEM_NAMES_20F,
    ITEM_NUMBER_TITLE_PATTERN,
    ITEM_PATTERN,
    ITEM_TABLE_LINE_PATTERN,
    PART_PATTERN,
    PART_TABLE_LINE_PATTERN,
)
