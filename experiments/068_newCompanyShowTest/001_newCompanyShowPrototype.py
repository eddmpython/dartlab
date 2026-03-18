"""
실험 ID: 068-001
실험명: new Company show prototype - block multi-schema renderer

목적:
- 현재 Company.show(topic, block)에서 raw markdown fallback으로 남는 docs table block을
  실험용 multi-schema renderer로 다시 구조화한다
- block 하나 안에 섞인 여러 logical subtable을 분리해 각각 wide/long DataFrame으로 반환한다
- 흡수 전 단계에서 "새 show 레이어가 어떤 API shape를 가져야 하는가"를 코드로 검증한다

가설:
1. block 단위로 전 기간을 동시에 스캔하면 canonical schema를 여러 개 잡을 수 있다
2. schema별로 분리 렌더링하면 현재 raw fallback 블록 일부를 wide DataFrame으로 복구할 수 있다
3. show(topic, block) 단일 DataFrame 강제보다 "block -> logical tables" 구조가 더 현실적이다

방법:
1. docs table block의 전 기간 markdown을 splitSubtables()로 분리한다
2. 각 서브테이블에서 header/group/item/unit 프로파일을 추출한다
3. header group별 canonical schema를 만든다
4. schema마다 wide/long DataFrame을 렌더링하고 fillRate/periodCount/itemCount를 계산한다
5. 삼성전자 등 실제 종목에서 block별 결과를 직접 출력해 확인한다

결과 (실험 후 작성):
- 삼성전자(005930) `audit` block 1:
  - 현재 show(): raw fallback `(1, 40)`
  - prototype: schema 10개 탐지, 그중 wide 6개
  - 대표 schema: `(56, 25)`, `(48, 25)`, `(27, 17)`, `(28, 5)`, `(20, 5)`
- 삼성전자(005930) `salesOrder` block 1:
  - 현재 show(): raw fallback `(1, 18)`
  - prototype: schema 1개 탐지, wide `(123, 19)`
- block 하나에 logical table이 여러 개 섞이는 케이스에서 `block -> schema list` 구조가 실제로 동작함을 확인

결론:
- 가설 1~3 채택
- 흡수 전 실험용 prototype으로 채택
- 향후 Company.show() 흡수 시 block -> schema list 구조를 우선 고려

실험일: 2026-03-18
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab import Company
from dartlab.engines.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _extractUnit,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    _normalizeItemName,
    _parseKeyValueOrMatrix,
    _parseMultiYear,
    splitSubtables,
)


_SUFFIX_RE = re.compile(r"(사업)?부문$")
_KISU_RE = re.compile(
    r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")
_PERIOD_KW_RE = re.compile(
    r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말"
)


@dataclass
class SubtableProfile:
    period: str
    blockOrder: int
    normHeader: str
    rawHeader: list[str]
    structType: str
    items: list[str]
    unit: str | None


@dataclass
class CanonicalSchema:
    schemaId: str
    canonicalHeader: str
    rawHeaderExample: list[str]
    structType: str
    canonicalItems: list[str]
    synonymMap: dict[str, str]
    tableCategory: str
    unit: str | None
    periodCount: int
    itemFrequency: dict[str, int]


@dataclass
class RenderedSchema:
    schema: CanonicalSchema
    wide: pl.DataFrame | None
    long: pl.DataFrame | None
    fillRate: float
    usedPeriods: list[str]


def period_columns(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]


def docs_topic_frame(company: Company, topic: str) -> pl.DataFrame:
    sec = company.sections
    if sec is None:
        return pl.DataFrame()
    frame = sec.filter(pl.col("topic") == topic)
    if "source" in frame.columns:
        frame = frame.filter(pl.col("source") == "docs")
    return frame


def table_blocks(topicFrame: pl.DataFrame) -> list[int]:
    if topicFrame.is_empty():
        return []
    blocks = (
        topicFrame.filter(pl.col("blockType") == "table")
        .select("blockOrder")
        .unique()
        .sort("blockOrder")
    )
    return [int(v) for v in blocks["blockOrder"].to_list()]


def normalize_item(name: str) -> str:
    name = _normalizeItemName(name)
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    match = _KISU_RE.search(name)
    if match:
        return match.group(1)
    return name


def group_header(headerCells: list[str]) -> str:
    header = _normalizeHeader(headerCells)
    header = _PERIOD_KW_RE.sub("", header)
    header = re.sub(r"\| *\|", "|", header)
    header = re.sub(r"\s+", " ", header).strip()
    return header


def scan_block_profiles(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> list[SubtableProfile]:
    blockRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if blockRow.is_empty():
        return []

    profiles: list[SubtableProfile] = []
    for period in periodCols:
        md = blockRow[period][0] if period in blockRow.columns else None
        if md is None:
            continue

        periodYear = int(re.match(r"\d{4}", period).group()) if re.match(r"\d{4}", period) else None
        for sub in splitSubtables(str(md)):
            headerCells = _headerCells(sub)
            if _isJunk(headerCells):
                continue
            dataRows = _dataRows(sub)
            if not dataRows:
                continue

            structType = _classifyStructure(headerCells)
            normHeader = group_header(headerCells)
            unit = _extractUnit(sub)
            items: list[str] = []

            if structType == "multi_year" and periodYear and "Q" not in period:
                triples, parsedUnit = _parseMultiYear(sub, periodYear)
                if parsedUnit:
                    unit = parsedUnit
                for rawItem, _, _ in triples:
                    item = normalize_item(rawItem)
                    if item and item not in items:
                        items.append(item)
            elif structType in {"key_value", "matrix"}:
                rows, _, parsedUnit = _parseKeyValueOrMatrix(sub)
                if parsedUnit:
                    unit = parsedUnit
                for rawItem, _ in rows:
                    item = normalize_item(rawItem)
                    if item and item not in items:
                        items.append(item)
            else:
                for row in dataRows:
                    if row and row[0].strip():
                        item = normalize_item(row[0].strip())
                        if item and item not in items:
                            items.append(item)

            profiles.append(
                SubtableProfile(
                    period=period,
                    blockOrder=blockOrder,
                    normHeader=normHeader,
                    rawHeader=headerCells,
                    structType=structType,
                    items=items,
                    unit=unit,
                )
            )

    return profiles


def _levenshtein_ratio(left: str, right: str) -> float:
    if left == right:
        return 1.0
    maxLen = max(len(left), len(right))
    if maxLen == 0:
        return 1.0

    prev = list(range(len(right) + 1))
    for i in range(1, len(left) + 1):
        curr = [i] + [0] * len(right)
        for j in range(1, len(right) + 1):
            cost = 0 if left[i - 1] == right[j - 1] else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    distance = prev[len(right)]
    return 1.0 - distance / maxLen


def build_synonym_map(group: list[SubtableProfile], canonicalItems: list[str]) -> dict[str, str]:
    synonymMap: dict[str, str] = {}
    maxLen = max((len(profile.items) for profile in group), default=0)

    for pos in range(maxLen):
        namesAtPos = [profile.items[pos] for profile in group if pos < len(profile.items)]
        if not namesAtPos:
            continue
        representative = Counter(namesAtPos).most_common(1)[0][0]
        for name in set(namesAtPos):
            if name == representative:
                continue
            left = re.sub(r"[\s\-_·.]", "", name)
            right = re.sub(r"[\s\-_·.]", "", representative)
            if left == right or _levenshtein_ratio(left, right) >= 0.75:
                synonymMap[name] = representative

    items = list(canonicalItems)
    if len(items) <= 80:
        for i, leftItem in enumerate(items):
            if leftItem in synonymMap:
                continue
            for rightItem in items[i + 1 :]:
                if rightItem in synonymMap:
                    continue
                left = re.sub(r"[\s\-_·.]", "", leftItem)
                right = re.sub(r"[\s\-_·.]", "", rightItem)
                if left == right:
                    synonymMap[rightItem] = leftItem
                elif len(left) > 3 and len(right) > 3 and _levenshtein_ratio(left, right) >= 0.85:
                    synonymMap[rightItem] = leftItem

    return synonymMap


def classify_table_category(
    group: list[SubtableProfile],
    canonicalItems: list[str],
    periodCount: int,
) -> str:
    if len(canonicalItems) > 50:
        return "list_type"
    if periodCount < 2:
        return "normal"

    periodItemSets: dict[str, set[str]] = defaultdict(set)
    for profile in group:
        periodItemSets[profile.period].update(profile.items)

    sets = list(periodItemSets.values())
    if len(sets) < 2:
        return "normal"

    totalOverlap = 0.0
    totalPairs = 0
    for i in range(len(sets)):
        for j in range(i + 1, min(i + 4, len(sets))):
            union = len(sets[i] | sets[j])
            inter = len(sets[i] & sets[j])
            if union > 0:
                totalOverlap += inter / union
                totalPairs += 1
    avgOverlap = totalOverlap / totalPairs if totalPairs else 0.0
    if avgOverlap < 0.3 and len(canonicalItems) > 5:
        return "historical"
    return "normal"


def build_block_schemas(profiles: list[SubtableProfile]) -> list[CanonicalSchema]:
    if not profiles:
        return []

    groups: dict[str, list[SubtableProfile]] = defaultdict(list)
    for profile in profiles:
        groups[profile.normHeader].append(profile)

    schemas: list[CanonicalSchema] = []
    orderedGroups = sorted(groups.items(), key=lambda item: (-len({p.period for p in item[1]}), item[0]))
    for idx, (normHeader, group) in enumerate(orderedGroups):
        typeCounts = Counter(profile.structType for profile in group)
        dominantType = typeCounts.most_common(1)[0][0]
        periods = sorted({profile.period for profile in group})
        periodCount = len(periods)

        canonicalItems: list[str] = []
        seenItems: set[str] = set()
        itemFrequency: Counter[str] = Counter()
        for profile in group:
            periodSeen: set[str] = set()
            for item in profile.items:
                if item not in seenItems:
                    canonicalItems.append(item)
                    seenItems.add(item)
                if item not in periodSeen:
                    itemFrequency[item] += 1
                    periodSeen.add(item)

        synonymMap = build_synonym_map(group, canonicalItems)
        category = classify_table_category(group, canonicalItems, periodCount)
        unitCounts = Counter(profile.unit for profile in group if profile.unit)
        unit = unitCounts.most_common(1)[0][0] if unitCounts else None

        schemas.append(
            CanonicalSchema(
                schemaId=f"s{idx:02d}",
                canonicalHeader=normHeader,
                rawHeaderExample=group[0].rawHeader,
                structType=dominantType,
                canonicalItems=canonicalItems,
                synonymMap=synonymMap,
                tableCategory=category,
                unit=unit,
                periodCount=periodCount,
                itemFrequency=dict(itemFrequency),
            )
        )

    return schemas


def render_schema_wide(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
    schema: CanonicalSchema,
) -> pl.DataFrame | None:
    if schema.tableCategory != "normal":
        return None

    blockRow = topicFrame.filter(
        (pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table")
    )
    if blockRow.is_empty():
        return None

    def resolve(item: str) -> str:
        return schema.synonymMap.get(item, item)

    seenItems: set[str] = set()
    allItems: list[str] = []
    periodItemVal: dict[str, dict[str, str]] = defaultdict(dict)

    for period in periodCols:
        md = blockRow[period][0] if period in blockRow.columns else None
        if md is None:
            continue
        periodYear = int(re.match(r"\d{4}", period).group()) if re.match(r"\d{4}", period) else None

        for sub in splitSubtables(str(md)):
            headerCells = _headerCells(sub)
            if _isJunk(headerCells):
                continue
            if not _dataRows(sub):
                continue
            if group_header(headerCells) != schema.canonicalHeader:
                continue

            if schema.structType == "multi_year" and periodYear and "Q" not in period:
                triples, _ = _parseMultiYear(sub, periodYear)
                for rawItem, year, value in triples:
                    item = resolve(normalize_item(rawItem))
                    if year != str(periodYear) or not value:
                        continue
                    if item not in seenItems:
                        allItems.append(item)
                        seenItems.add(item)
                    periodItemVal[item][period] = value
                continue

            rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
            for rawItem, values in rows:
                item = resolve(normalize_item(rawItem))
                nonEmptyVals = [value for value in values if value.strip()]
                if schema.structType == "matrix" and len(headerNames) >= 2 and len(nonEmptyVals) >= 2 and len(nonEmptyVals) <= len(headerNames):
                    for idx, headerName in enumerate(headerNames):
                        value = values[idx].strip() if idx < len(values) else ""
                        if not value or value == "-":
                            continue
                        compoundItem = resolve(f"{item}_{normalize_item(headerName)}")
                        if compoundItem not in seenItems:
                            allItems.append(compoundItem)
                            seenItems.add(compoundItem)
                        periodItemVal[compoundItem][period] = value
                    continue

                value = " | ".join(value for value in values if value.strip()).strip()
                if not value:
                    continue
                if item not in seenItems:
                    allItems.append(item)
                    seenItems.add(item)
                periodItemVal[item][period] = value

    if not allItems:
        return None

    resolvedCanonical: list[str] = []
    for item in schema.canonicalItems:
        resolved = resolve(item)
        if resolved not in resolvedCanonical:
            resolvedCanonical.append(resolved)
    canonicalOrder = {item: idx for idx, item in enumerate(resolvedCanonical)}
    allItems.sort(key=lambda item: canonicalOrder.get(item, 9999))

    usedPeriods = [period for period in periodCols if any(period in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

    schemaMap = {"항목": pl.Utf8}
    for period in usedPeriods:
        schemaMap[period] = pl.Utf8

    rows: list[dict[str, str | None]] = []
    for item in allItems:
        row = {"항목": item}
        for period in usedPeriods:
            row[period] = periodItemVal.get(item, {}).get(period)
        rows.append(row)

    return pl.DataFrame(rows, schema=schemaMap)


def wide_to_long(wide: pl.DataFrame | None) -> pl.DataFrame | None:
    if wide is None or wide.is_empty() or "항목" not in wide.columns:
        return None
    periodCols = [c for c in wide.columns if c != "항목"]
    if not periodCols:
        return None
    long = wide.unpivot(index="항목", variable_name="period", value_name="value")
    return long.filter(pl.col("value").is_not_null())


def compute_fill_rate(wide: pl.DataFrame | None) -> float:
    if wide is None or wide.is_empty():
        return 0.0
    periodCols = [c for c in wide.columns if c != "항목"]
    if not periodCols:
        return 0.0
    total = wide.height * len(periodCols)
    if total == 0:
        return 0.0
    filled = 0
    for col in periodCols:
        filled += wide[col].drop_nulls().len()
    return filled / total


def render_block(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
) -> list[RenderedSchema]:
    profiles = scan_block_profiles(topicFrame, blockOrder, periodCols)
    schemas = build_block_schemas(profiles)

    rendered: list[RenderedSchema] = []
    for schema in schemas:
        wide = render_schema_wide(topicFrame, blockOrder, periodCols, schema)
        long = wide_to_long(wide)
        usedPeriods = [c for c in wide.columns if c != "항목"] if wide is not None else []
        rendered.append(
            RenderedSchema(
                schema=schema,
                wide=wide,
                long=long,
                fillRate=compute_fill_rate(wide),
                usedPeriods=usedPeriods,
            )
        )

    rendered.sort(
        key=lambda item: (
            item.wide is None,
            item.schema.tableCategory != "normal",
            -item.schema.periodCount,
            -(item.wide.height if item.wide is not None else 0),
            -item.fillRate,
        )
    )
    return rendered


def print_block_summary(company: Company, topic: str) -> None:
    blockIndex = company.show(topic)
    print(f"topic={topic}")
    print(blockIndex)


def print_rendered_block(
    company: Company,
    topic: str,
    blockOrder: int,
    head: int,
    showLong: bool,
) -> None:
    topicFrame = docs_topic_frame(company, topic)
    periodCols = period_columns(topicFrame)
    rendered = render_block(topicFrame, blockOrder, periodCols)
    current = company.show(topic, blockOrder)

    print(f"topic={topic} block={blockOrder}")
    print(f"current_show_shape={None if current is None else current.shape}")
    if isinstance(current, pl.DataFrame):
        print(current.head(head))
    print()

    if not rendered:
        print("rendered schemas: 0")
        return

    print(f"rendered schemas: {len(rendered)}")
    for item in rendered:
        schema = item.schema
        wideShape = None if item.wide is None else item.wide.shape
        print(
            f"- {schema.schemaId} "
            f"type={schema.structType} "
            f"category={schema.tableCategory} "
            f"periods={schema.periodCount} "
            f"items={len(schema.canonicalItems)} "
            f"fill={item.fillRate:.2f} "
            f"shape={wideShape} "
            f"header={schema.canonicalHeader[:80]}"
        )
        if item.wide is not None:
            print(item.wide.head(head))
        if showLong and item.long is not None:
            print(item.long.head(head))
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="new Company show experimental prototype")
    parser.add_argument("stockCode", nargs="?", default="005930")
    parser.add_argument("topic", nargs="?", default="audit")
    parser.add_argument("--block", type=int, default=None)
    parser.add_argument("--head", type=int, default=8)
    parser.add_argument("--long", action="store_true", dest="showLong")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pl.Config.set_tbl_rows(20)
    pl.Config.set_tbl_cols(12)
    pl.Config.set_fmt_str_lengths(60)

    company = Company(args.stockCode)
    if args.block is None:
        print_block_summary(company, args.topic)
    else:
        print_rendered_block(company, args.topic, args.block, args.head, args.showLong)
