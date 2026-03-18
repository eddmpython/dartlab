"""실험 ID: 066-002
실험명: Normal Form 개선 — multi_year 당기 추출 + 이력형 처리 + 실제 비교

목적:
- 001에서 발견된 3가지 문제 해결:
  1. multi_year에서 당기/전기/전전기 col_key → 당기 값만 추출하여 기간 축 일원화
  2. 이력형 테이블에서 날짜 row_key 허용
  3. 이력형 vs 현황형 자동 판별 + 각각 다른 수평화 전략
- 283종목 전수 비교로 기존 대비 성공률 측정

가설:
1. multi_year 당기 추출을 정규형 파이프라인 안에서 처리 가능
2. 정규형 기반 수평화가 기존 규칙 기반과 동등 이상의 성공률 달성
3. (row_key, col_key) 복합키로 항목 매칭 정확도 향상

방법:
1. toNormalForm에 multi_year 인식 + 당기 값 추출 로직 추가
2. 이력형 판별: row_key 간 기간 겹침률 (Jaccard) 검사
3. 283종목 전수: 기존 _horizontalizeTableBlock vs 정규형 성공률 비교

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Normal Form 데이터 구조
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class Triple:
    row_key: str
    col_key: str
    value: str


@dataclass
class NormalizedTable:
    triples: list[Triple] = field(default_factory=list)
    unit: str | None = None
    table_type: str = "flat"  # flat | multi_year | history
    row_keys_ordered: list[str] = field(default_factory=list)
    col_keys_ordered: list[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 정규화 유틸
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기", "당분기", "전분기"}

_KISU_RE = re.compile(
    r"제\s*(\d+)\s*기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)

_SUFFIX_RE = re.compile(r"(사업)?부문$")
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")

_UNIT_RE = re.compile(
    r"^[\[\(（<]?\s*"
    r"(?:단위|원화단위|외화단위|금액단위)"
    r"\s*[:：/]?\s*"
    r"[^\]）)>]*"
    r"[\]）)>]?\s*$"
)

_DATE_RE = re.compile(
    r"^[\[\(（<]?\s*"
    r"(?:기준일|기준|현재|기준시점)"
    r"\s*[:：/]?\s*"
    r"[^\]）)>]*"
    r"[\]）)>]?\s*$"
)

_STOCK_TYPES = {"보통주", "우선주", "기타주식"}


def _normalizeItem(name: str) -> str:
    name = re.sub(r"\s+", "", name)
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("ㆍ", "·")
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(2)  # 상대기명 반환
    return name


def _isJunkItem(name: str) -> bool:
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


def _extractUnit(lines: list[str]) -> str | None:
    full = "\n".join(lines)
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    return m.group(1).strip() if m else None


def _isUnitOrDateHeader(cells: list[str]) -> bool:
    h = " ".join(c.strip() for c in cells).strip()
    if not h:
        return False
    return bool(_UNIT_RE.match(h)) or bool(_DATE_RE.match(h))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 마크다운 파싱
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _parseMdTable(md_lines: list[str]) -> tuple[list[str], list[list[str]], int]:
    """마크다운 → (헤더, 데이터행, separator_index).

    separator_index는 원본 라인에서의 위치.
    """
    headers: list[str] = []
    rows: list[list[str]] = []
    sep_idx = -1

    for i, line in enumerate(md_lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        is_sep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())

        if is_sep:
            sep_idx = i
            continue

        if sep_idx < 0:
            if not headers:
                headers = list(cells)
        else:
            rows.append(cells)

    return headers, rows, sep_idx


def _splitSubtables(md: str) -> list[list[str]]:
    from dartlab.engines.dart.docs.sections.tableParser import splitSubtables
    return splitSubtables(md)


def _isMultiYear(headers: list[str]) -> bool:
    joined = " ".join(headers)
    return any(kw in joined for kw in _MULTI_YEAR_KW)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 핵심: 마크다운 → 정규형
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def toNormalForm(
    md_lines: list[str],
    period_year: int | None = None,
) -> NormalizedTable:
    """마크다운 서브테이블 → 정규형 트리플.

    multi_year 감지 시 당기 값만 추출 (기존 tableParser._parseMultiYear 로직 통합).
    """
    headers, rows, sep_idx = _parseMdTable(md_lines)
    unit = _extractUnit(md_lines)

    if not headers or not rows:
        return NormalizedTable(unit=unit)

    # 단위/기준일 헤더 → 다음 행을 실제 헤더로
    if _isUnitOrDateHeader(headers):
        if rows:
            headers = rows[0]
            rows = rows[1:]
        else:
            return NormalizedTable(unit=unit)

    # ── multi_year 감지 ──
    if _isMultiYear(headers):
        return _toNormalFormMultiYear(md_lines, headers, rows, period_year, unit)

    # ── flat (key_value / matrix) ──
    return _toNormalFormFlat(headers, rows, unit)


def _toNormalFormMultiYear(
    md_lines: list[str],
    headers: list[str],
    rows: list[list[str]],
    period_year: int | None,
    unit: str | None,
) -> NormalizedTable:
    """multi_year 테이블 → 당기 값만 추출하여 정규형.

    col_key는 헤더의 컬럼 이름 (단, 당기/전기 같은 상대기 이름은 무시).
    row_key = 항목명, col_key = "value" (단일 값), value = 당기 값.
    """
    # 기수 행 찾기: separator 직후 첫 행에서 제N기 패턴
    kisu_row_idx = -1
    kisu_nums = []
    for i, row in enumerate(rows):
        for cell in row:
            m = re.search(r"제\s*(\d+)\s*기", cell)
            if m:
                kisu_nums.append(int(m.group(1)))
        if kisu_nums:
            kisu_row_idx = i
            break

    if not kisu_nums or period_year is None:
        # 기수 없으면 당기 컬럼 위치로 추출
        return _extractCurrentPeriod(headers, rows, unit)

    max_kisu = max(kisu_nums)
    sorted_kisu = sorted(kisu_nums, reverse=True)
    kisu_to_year = {kn: period_year - max_kisu + kn for kn in kisu_nums}
    current_year = period_year

    triples: list[Triple] = []
    row_keys: list[str] = []
    seen: set[str] = set()
    prev_item = ""

    for row in rows[kisu_row_idx + 1:]:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first.startswith("※"):
            continue

        # 보통주/우선주 처리
        if first in _STOCK_TYPES and prev_item:
            item = _normalizeItem(f"{prev_item}-{first}")
            vals = row[1:]
        elif len(row) > 1 and row[1].strip() in _STOCK_TYPES:
            stock = row[1].strip()
            item = _normalizeItem(f"{first}-{stock}")
            vals = row[2:]
            prev_item = first
        else:
            item = _normalizeItem(first)
            vals = row[1:]
            prev_item = first

        if _isJunkItem(item):
            continue

        # 뒤에서부터 기수 개수만큼 역순 추출
        non_empty = [(i, v.strip()) for i, v in enumerate(vals) if v.strip() and v.strip() != "-" and v.strip() not in _STOCK_TYPES]
        if len(non_empty) >= len(sorted_kisu):
            # 뒤에서 기수 수만큼
            tail = non_empty[-len(sorted_kisu):]
            for idx, (_, val) in enumerate(tail):
                year = kisu_to_year[sorted_kisu[idx]]
                if year == current_year:
                    if item not in seen:
                        row_keys.append(item)
                        seen.add(item)
                    triples.append(Triple(row_key=item, col_key="value", value=val))
        elif len(non_empty) > 0:
            # 값이 기수 수보다 적으면 첫 번째를 당기로
            for pos, (_, val) in enumerate(non_empty):
                year = kisu_to_year[sorted_kisu[pos]] if pos < len(sorted_kisu) else None
                if year == current_year:
                    if item not in seen:
                        row_keys.append(item)
                        seen.add(item)
                    triples.append(Triple(row_key=item, col_key="value", value=val))

    return NormalizedTable(
        triples=triples,
        unit=unit,
        table_type="multi_year",
        row_keys_ordered=row_keys,
        col_keys_ordered=["value"],
    )


def _extractCurrentPeriod(
    headers: list[str],
    rows: list[list[str]],
    unit: str | None,
) -> NormalizedTable:
    """당기 컬럼 위치를 헤더에서 직접 찾아 추출."""
    # 당기 컬럼 인덱스
    current_idx = -1
    for i, h in enumerate(headers):
        if "당기" in h and "전" not in h:
            current_idx = i
            break
    if current_idx < 0:
        current_idx = 1  # fallback: 첫 값 컬럼

    triples: list[Triple] = []
    row_keys: list[str] = []
    seen: set[str] = set()

    for row in rows:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first.startswith("※"):
            continue
        item = _normalizeItem(first)
        if _isJunkItem(item):
            continue

        val = row[current_idx].strip() if current_idx < len(row) else ""
        if val and val != "-":
            if item not in seen:
                row_keys.append(item)
                seen.add(item)
            triples.append(Triple(row_key=item, col_key="value", value=val))

    return NormalizedTable(
        triples=triples,
        unit=unit,
        table_type="multi_year",
        row_keys_ordered=row_keys,
        col_keys_ordered=["value"],
    )


def _toNormalFormFlat(
    headers: list[str],
    rows: list[list[str]],
    unit: str | None,
) -> NormalizedTable:
    """flat(key_value/matrix) 테이블 → 정규형."""
    triples: list[Triple] = []
    row_keys: list[str] = []
    seen_rk: set[str] = set()
    col_keys: list[str] = []

    for h in headers[1:]:
        ck = _normalizeItem(h) if h.strip() else f"col_{len(col_keys)}"
        col_keys.append(ck)

    group_prefix = ""

    for row in rows:
        if not row or not row[0].strip():
            continue
        raw = row[0].strip()
        if raw.startswith("※") or raw.startswith("☞"):
            continue

        item = _normalizeItem(raw)
        if _isJunkItem(item):
            continue

        values = row[1:]
        all_empty = all(not v.strip() or v.strip() == "-" for v in values)
        if all_empty and len(values) >= 2:
            group_prefix = item
            continue

        if group_prefix:
            item = f"{group_prefix}_{item}"

        if item not in seen_rk:
            row_keys.append(item)
            seen_rk.add(item)

        for i, ck in enumerate(col_keys):
            val = values[i].strip() if i < len(values) else ""
            if val and val != "-":
                triples.append(Triple(row_key=item, col_key=ck, value=val))

    return NormalizedTable(
        triples=triples,
        unit=unit,
        table_type="flat",
        row_keys_ordered=row_keys,
        col_keys_ordered=col_keys,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 수평화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def horizontalize(
    period_tables: dict[str, list[NormalizedTable]],
    period_cols: list[str],
) -> pl.DataFrame | None:
    """기간별 NormalizedTable → 수평화 DataFrame.

    multi_year: row_key만으로 수평화 (col_key="value" 단일)
    flat: (row_key, col_key) 복합키로 수평화
    """
    # 타입 판별: multi_year가 하나라도 있으면 multi_year 모드
    has_multi_year = any(
        t.table_type == "multi_year"
        for tables in period_tables.values()
        for t in tables
    )

    if has_multi_year:
        return _horizontalizeMultiYear(period_tables, period_cols)
    else:
        return _horizontalizeFlat(period_tables, period_cols)


def _horizontalizeMultiYear(
    period_tables: dict[str, list[NormalizedTable]],
    period_cols: list[str],
) -> pl.DataFrame | None:
    """multi_year → 항목 × 기간."""
    item_period_val: dict[str, dict[str, str]] = {}
    all_items: list[str] = []
    seen: set[str] = set()

    for period, tables in period_tables.items():
        for t in tables:
            if t.table_type != "multi_year":
                continue
            for rk in t.row_keys_ordered:
                if rk not in seen:
                    all_items.append(rk)
                    seen.add(rk)
            for tr in t.triples:
                if tr.row_key not in item_period_val:
                    item_period_val[tr.row_key] = {}
                if period not in item_period_val[tr.row_key]:
                    item_period_val[tr.row_key][period] = tr.value

    if not all_items:
        return None

    # 이력형/목록형 필터 적용
    all_items = [i for i in all_items if not _isJunkItem(i)]
    if len(all_items) > 50:
        return None

    result = _checkOverlapAndBuild(all_items, item_period_val, period_cols, use_col_key=False)
    return result


def _horizontalizeFlat(
    period_tables: dict[str, list[NormalizedTable]],
    period_cols: list[str],
) -> pl.DataFrame | None:
    """flat → (항목, 지표) × 기간, 또는 지표 1개면 항목 × 기간."""
    # (row_key, col_key) → {period → value}
    data: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    all_items: list[str] = []
    seen: set[str] = set()
    all_col_keys: list[str] = []
    seen_ck: set[str] = set()

    for period, tables in period_tables.items():
        for t in tables:
            if t.table_type == "multi_year":
                continue
            for rk in t.row_keys_ordered:
                if rk not in seen:
                    all_items.append(rk)
                    seen.add(rk)
            for ck in t.col_keys_ordered:
                if ck not in seen_ck:
                    all_col_keys.append(ck)
                    seen_ck.add(ck)
            for tr in t.triples:
                data[(tr.row_key, tr.col_key)][period] = tr.value

    if not data:
        return None

    all_items = [i for i in all_items if not _isJunkItem(i)]

    # col_key가 1개면 단순 항목 × 기간
    if len(all_col_keys) == 1:
        item_period_val = {}
        for (rk, ck), pv in data.items():
            item_period_val[rk] = pv
        if len(all_items) > 50:
            return None
        return _checkOverlapAndBuild(all_items, item_period_val, period_cols, use_col_key=False)

    # col_key가 여러 개: (항목_지표) 복합키 또는 항목+지표 컬럼
    # 여기서는 항목_지표 복합키로 통합
    compound_items: list[str] = []
    compound_seen: set[str] = set()
    compound_period_val: dict[str, dict[str, str]] = {}

    for rk in all_items:
        for ck in all_col_keys:
            key = (rk, ck)
            if key not in data:
                continue
            compound = f"{rk}_{ck}" if len(all_col_keys) > 1 else rk
            if compound not in compound_seen:
                compound_items.append(compound)
                compound_seen.add(compound)
            compound_period_val[compound] = data[key]

    if len(compound_items) > 50:
        return None
    return _checkOverlapAndBuild(compound_items, compound_period_val, period_cols, use_col_key=False)


def _checkOverlapAndBuild(
    items: list[str],
    item_period_val: dict[str, dict[str, str]],
    period_cols: list[str],
    use_col_key: bool = False,
) -> pl.DataFrame | None:
    """이력형 감지 + DataFrame 구성."""
    if not items:
        return None

    # 이력형 감지: Jaccard 겹침률
    period_item_sets: dict[str, set[str]] = {}
    for item in items:
        for p in item_period_val.get(item, {}):
            if p not in period_item_sets:
                period_item_sets[p] = set()
            period_item_sets[p].add(item)

    if len(period_item_sets) >= 2:
        sets = list(period_item_sets.values())
        total_overlap = 0
        total_pairs = 0
        for i in range(len(sets)):
            for j in range(i + 1, min(i + 4, len(sets))):
                union = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if union > 0:
                    total_overlap += inter / union
                    total_pairs += 1
        avg_overlap = total_overlap / total_pairs if total_pairs else 0
        if avg_overlap < 0.3 and len(items) > 5:
            return None  # 이력형

    # sparse 감지
    used_periods = [p for p in period_cols if any(p in item_period_val.get(item, {}) for item in items)]
    if not used_periods:
        return None

    if len(used_periods) >= 3 and len(items) > 15:
        total = len(items) * len(used_periods)
        filled = sum(1 for item in items for p in used_periods if item_period_val.get(item, {}).get(p))
        if filled / total < 0.5:
            return None

    # DataFrame
    rows = []
    for item in items:
        if not any(item_period_val.get(item, {}).get(p) for p in used_periods):
            continue
        row: dict[str, str | None] = {"항목": item}
        for p in used_periods:
            row[p] = item_period_val.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None

    schema = {"항목": pl.Utf8}
    for p in used_periods:
        schema[p] = pl.Utf8
    return pl.DataFrame(rows, schema=schema)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 통합 함수: sections topic → 수평화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def horizontalizeTopic(
    topic_frame: pl.DataFrame,
    period_cols: list[str],
) -> pl.DataFrame | None:
    """sections의 table 행들 → 정규형 → 수평화.

    topic_frame: blockType=="table"인 행만 (같은 topic).
    """
    if topic_frame.is_empty():
        return None

    period_tables: dict[str, list[NormalizedTable]] = {}

    for p in period_cols:
        if p not in topic_frame.columns:
            continue
        tables = []
        for row_idx in range(topic_frame.height):
            md = topic_frame[p][row_idx]
            if md is None:
                continue

            p_year = None
            m = re.match(r"(\d{4})", p)
            if m:
                p_year = int(m.group(1))

            for sub in _splitSubtables(str(md)):
                nf = toNormalForm(sub, period_year=p_year)
                if nf.triples:
                    tables.append(nf)

        if tables:
            period_tables[p] = tables

    if not period_tables:
        return None

    return horizontalize(period_tables, period_cols)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 비교 검증
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _compare10Stocks():
    """10종목 × 주요 topic: 기존 vs 정규형 비교."""
    from dartlab import Company

    test_stocks = [
        "삼성전자", "SK하이닉스", "네이버", "현대차", "셀트리온",
        "KB금융", "LG화학", "LG", "삼성물산", "SK",
    ]
    test_topics = ["dividend", "audit", "salesOrder", "employee", "companyOverview"]

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}

    results = []

    for stock in test_stocks:
        try:
            c = Company(stock)
            sections = c.sections
        except Exception as e:
            print(f"  {stock}: 로드 실패 — {e}")
            continue

        for topic in test_topics:
            topic_rows = sections.filter(
                (pl.col("topic") == topic) & (pl.col("blockType") == "table")
            )
            if topic_rows.is_empty():
                continue

            period_cols = sorted([
                col for col in topic_rows.columns
                if col not in meta_cols and re.match(r"\d{4}", col)
            ])

            # 기존 방식
            try:
                existing = c.show(topic)
                existing_ok = existing is not None and not (isinstance(existing, pl.DataFrame) and existing.is_empty())
                # show()가 목차 반환 시 table 블록 존재 여부 확인
                if isinstance(existing, pl.DataFrame) and "block" in existing.columns:
                    # 목차 → 각 table block 시도
                    table_blocks = existing.filter(pl.col("type") == "table")
                    existing_ok = table_blocks.height > 0
                    # 실제 수평화 시도
                    block_ok = False
                    for b in table_blocks["block"].to_list():
                        try:
                            bdf = c.show(topic, b)
                            if bdf is not None and isinstance(bdf, pl.DataFrame) and not bdf.is_empty():
                                block_ok = True
                                break
                        except Exception:
                            pass
                    existing_ok = block_ok
            except Exception:
                existing_ok = False

            # 정규형 방식
            try:
                nf_result = horizontalizeTopic(topic_rows, period_cols)
                nf_ok = nf_result is not None and not nf_result.is_empty()
            except Exception:
                nf_ok = False

            results.append({
                "stock": stock,
                "topic": topic,
                "existing": existing_ok,
                "normal_form": nf_ok,
            })

    # 결과 요약
    df = pl.DataFrame(results)
    print(f"\n{'='*60}")
    print("10종목 비교 결과")
    print(f"{'='*60}")
    print(f"총 {df.height}개 (stock × topic)")
    print(f"기존 성공: {df.filter(pl.col('existing')).height}")
    print(f"정규형 성공: {df.filter(pl.col('normal_form')).height}")
    print(f"정규형만 성공: {df.filter(~pl.col('existing') & pl.col('normal_form')).height}")
    print(f"기존만 성공: {df.filter(pl.col('existing') & ~pl.col('normal_form')).height}")
    print(f"둘 다 실패: {df.filter(~pl.col('existing') & ~pl.col('normal_form')).height}")

    # topic별 상세
    print(f"\ntopic별 성공률:")
    for topic in test_topics:
        tf = df.filter(pl.col("topic") == topic)
        e = tf.filter(pl.col("existing")).height
        n = tf.filter(pl.col("normal_form")).height
        print(f"  {topic}: 기존 {e}/{tf.height} ({100*e/tf.height:.0f}%), 정규형 {n}/{tf.height} ({100*n/tf.height:.0f}%)")

    # 차이 상세
    diff_rows = df.filter(pl.col("existing") != pl.col("normal_form"))
    if diff_rows.height > 0:
        print(f"\n차이 ({diff_rows.height}건):")
        print(diff_rows)


def _compare283Stocks():
    """283종목 전수: 기존 vs 정규형 블록 단위 비교."""
    from dartlab import Company
    from dartlab.core.dataLoader import listStocks

    stocks = listStocks("docs")
    print(f"\n{'='*60}")
    print(f"283종목 전수 비교 ({len(stocks)}종목)")
    print(f"{'='*60}")

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
    total_blocks = 0
    existing_success = 0
    nf_success = 0
    both_success = 0
    nf_only = 0
    existing_only = 0
    both_fail = 0
    errors = 0

    for i, stock_code in enumerate(stocks):
        if (i + 1) % 50 == 0:
            print(f"  진행: {i+1}/{len(stocks)} (nf={nf_success}, existing={existing_success})")

        try:
            c = Company(stock_code)
            sections = c.sections
        except Exception:
            errors += 1
            continue

        # 모든 table 블록 topic 수집
        table_rows = sections.filter(pl.col("blockType") == "table")
        if table_rows.is_empty():
            continue

        topics = table_rows["topic"].unique().to_list()
        period_cols = sorted([
            col for col in table_rows.columns
            if col not in meta_cols and re.match(r"\d{4}", col)
        ])

        for topic in topics:
            topic_table = table_rows.filter(pl.col("topic") == topic)
            total_blocks += 1

            # 정규형
            try:
                nf_result = horizontalizeTopic(topic_table, period_cols)
                nf_ok = nf_result is not None and not nf_result.is_empty()
            except Exception:
                nf_ok = False

            # 기존 (show에서 table block 수평화)
            try:
                show_result = c.show(topic)
                existing_ok = False
                if isinstance(show_result, pl.DataFrame) and "block" in show_result.columns:
                    table_blocks = show_result.filter(pl.col("type") == "table")
                    for b in table_blocks["block"].to_list():
                        try:
                            bdf = c.show(topic, b)
                            if bdf is not None and isinstance(bdf, pl.DataFrame) and not bdf.is_empty():
                                existing_ok = True
                                break
                        except Exception:
                            pass
            except Exception:
                existing_ok = False

            if existing_ok:
                existing_success += 1
            if nf_ok:
                nf_success += 1
            if existing_ok and nf_ok:
                both_success += 1
            elif nf_ok and not existing_ok:
                nf_only += 1
            elif existing_ok and not nf_ok:
                existing_only += 1
            else:
                both_fail += 1

    print(f"\n{'='*60}")
    print(f"전수 비교 결과")
    print(f"{'='*60}")
    print(f"총 블록: {total_blocks}, 에러 종목: {errors}")
    print(f"기존 성공: {existing_success} ({100*existing_success/total_blocks:.1f}%)")
    print(f"정규형 성공: {nf_success} ({100*nf_success/total_blocks:.1f}%)")
    print(f"둘 다 성공: {both_success}")
    print(f"정규형만 성공: {nf_only}")
    print(f"기존만 성공: {existing_only}")
    print(f"둘 다 실패: {both_fail}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="283종목 전수 비교")
    args = parser.parse_args()

    if args.full:
        _compare283Stocks()
    else:
        _compare10Stocks()
