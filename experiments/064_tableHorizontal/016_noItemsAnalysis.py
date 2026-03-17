"""
실험 ID: 064-016
실험명: no_items / all_junk 케이스 원본 분석

목적:
- executivePay, boardOfDirectors, companyOverview에서 no_items/all_junk 패턴의 원본 확인
- 수정 가능한 패턴 식별

실험일: 2026-03-17
"""

import sys
import re
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _dataRows,
    _classifyStructure,
    _parseMultiYear,
    _parseKeyValueOrMatrix,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


_UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
_DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")


def _stripUnitHeader(sub: list[str]) -> list[str] | None:
    firstRow = None
    for line in sub:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        firstRow = [c for c in cells if c.strip()]
        break
    if firstRow is None or len(firstRow) != 1:
        return None
    h = firstRow[0].strip()
    if not (_UNIT_ONLY_RE.match(h) or _DATE_ONLY_RE.match(h)):
        return None
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break
    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return None
    remainder = sub[sepIdx + 1:]
    if not remainder:
        return None
    hasSep = any(
        all(set(c.strip()) <= {"-", ":"} for c in line.strip("|").split("|") if c.strip())
        for line in remainder
    )
    if hasSep:
        return remainder
    if len(remainder) >= 2:
        headerLine = remainder[0]
        colCount = len(headerLine.strip("|").split("|"))
        sepLine = "| " + " | ".join(["---"] * colCount) + " |"
        return [headerLine, sepLine] + remainder[1:]
    return None


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    # no_items / all_junk 샘플 수집
    samples = defaultdict(list)  # (topic, reason) -> [(code, bo, md_sample)]

    target_topics = ["executivePay", "boardOfDirectors", "companyOverview",
                     "businessOverview", "dividend", "audit"]

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
        except (FileNotFoundError, ValueError):
            continue
        if sec is None:
            continue
        periodCols = [c for c in sec.columns if _isPeriodCol(c)]

        for topic in target_topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            if tTableRows.is_empty():
                continue

            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())
            for bo in blockOrders:
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
                    continue

                # 분류 로직 재현
                allItems = []
                seenItems = set()
                had_sub = False

                for p in periodCols:
                    md = boRow[p][0] if p in boRow.columns else None
                    if md is None:
                        continue
                    m = re.match(r"\d{4}", p)
                    if m is None:
                        continue
                    pYear = int(m.group())

                    for sub in splitSubtables(str(md)):
                        hc = _headerCells(sub)
                        if _isJunk(hc):
                            continue
                        dr = _dataRows(sub)
                        if not dr:
                            continue
                        had_sub = True

                        structType = _classifyStructure(hc)
                        if structType == "skip":
                            fixed = _stripUnitHeader(sub)
                            if fixed is not None:
                                fixedHc = _headerCells(fixed)
                                fixedDr = _dataRows(fixed)
                                if fixedHc and not _isJunk(fixedHc) and fixedDr:
                                    structType = _classifyStructure(fixedHc)
                                    sub = fixed

                        if structType == "multi_year":
                            triples, _ = _parseMultiYear(sub, pYear)
                            for rawItem, year, val in triples:
                                if year == str(pYear) and rawItem not in seenItems:
                                    allItems.append(rawItem)
                                    seenItems.add(rawItem)
                            if not triples and len(hc) >= 2:
                                rows, _, _ = _parseKeyValueOrMatrix(sub)
                                for rawItem, vals in rows:
                                    if rawItem not in seenItems:
                                        allItems.append(rawItem)
                                        seenItems.add(rawItem)
                        elif structType in ("key_value", "matrix"):
                            rows, _, _ = _parseKeyValueOrMatrix(sub)
                            for rawItem, vals in rows:
                                val = " | ".join(v for v in vals if v).strip()
                                if val and rawItem not in seenItems:
                                    allItems.append(rawItem)
                                    seenItems.add(rawItem)
                    break  # 첫 기간만

                if not had_sub:
                    reason = "no_sub"
                elif not allItems:
                    reason = "no_items"
                else:
                    # _isJunkItem 체크
                    valid = [it for it in allItems if not (re.sub(r"[,.\-\s]", "", it).isdigit() or not re.sub(r"[,.\-\s]", "", it))]
                    if not valid:
                        reason = "all_junk"
                    else:
                        continue  # 성공 케이스

                key = (topic, reason)
                if len(samples[key]) < 3:
                    # 첫 기간의 마크다운 수집
                    sample_md = None
                    for p in periodCols:
                        md = boRow[p][0] if p in boRow.columns else None
                        if md is not None:
                            sample_md = str(md)[:400]
                            break
                    # 서브테이블 분류 정보
                    sub_info = []
                    if sample_md:
                        for sub in splitSubtables(sample_md):
                            hc = _headerCells(sub)
                            st = _classifyStructure(hc) if not _isJunk(hc) else "junk"
                            sub_info.append((st, hc[:5]))

                    samples[key].append({
                        "code": code, "bo": bo,
                        "items": allItems[:10],
                        "md": sample_md,
                        "sub_info": sub_info,
                    })

    # 출력
    for (topic, reason), smpls in sorted(samples.items()):
        print(f"\n{'='*70}")
        print(f"{topic} — {reason} ({len(smpls)}건)")
        print(f"{'='*70}")
        for s in smpls:
            print(f"\n  {s['code']} bo={s['bo']}")
            if s['items']:
                print(f"  items(raw): {s['items'][:8]}")
            for st, hc in s['sub_info']:
                print(f"  sub: {st} header={hc}")
            if s['md']:
                lines = s['md'].split("\n")
                for i, line in enumerate(lines[:8]):
                    print(f"    [{i}] {line[:100]}")
