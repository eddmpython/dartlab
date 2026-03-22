"""실험 ID: 066-004
실험명: Normal Form 패러다임 최종 분석 — 서브테이블 클러스터링 통합

목적:
- 003에서 발견된 근본 원인 (서브테이블 분리 부재) 해결
- 정규형 + 서브테이블 클러스터링 통합 파이프라인 구현
- 10종목 × 5 topic 비교로 기존 대비 성공률 재측정
- 정규형 패러다임의 실용성/한계 최종 판단

가설:
1. 서브테이블별로 독립 정규형 → 독립 수평화하면 기존과 동등 이상
2. 복합키(row_key_col_key)는 col_key가 적을 때만 유효, 많으면 pipe join fallback
3. 정규형이 기존 대비 구조적 장점을 보이는 케이스가 존재

방법:
1. 서브테이블별 독립 정규형 변환 + 독립 수평화
2. 헤더 시그니처 기반 서브테이블 클러스터링 (기존 로직과 동일)
3. 10종목 재비교

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

from dartlab.engines.company.dart.docs.sections.tableParser import (
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    splitSubtables,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Normal Form 데이터 구조 (002에서 가져옴, 최소 수정)
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
    table_type: str = "flat"
    row_keys_ordered: list[str] = field(default_factory=list)
    col_keys_ordered: list[str] = field(default_factory=list)
    header_sig: str = ""  # 서브테이블 클러스터링용


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 정규화 유틸 (002에서 그대로)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기", "당분기", "전분기"}
_STOCK_TYPES = {"보통주", "우선주", "기타주식"}

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

_PERIOD_KW_RE = re.compile(
    r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말"
)


def _normalizeItem(name: str) -> str:
    name = re.sub(r"\s+", "", name)
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("ㆍ", "·")
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(2)
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


def _groupHeaderSig(hc: list[str]) -> str:
    """클러스터링용 헤더 시그니처: 연도/기수/기간 키워드 제거."""
    h = _normalizeHeader(hc)
    h = _PERIOD_KW_RE.sub("", h)
    h = re.sub(r"\| *\|", "|", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 정규형 변환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _parseMdTable(md_lines: list[str]) -> tuple[list[str], list[list[str]]]:
    headers: list[str] = []
    rows: list[list[str]] = []
    sep_found = False
    for line in md_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        is_sep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if is_sep:
            sep_found = True
            continue
        if not sep_found:
            if not headers:
                headers = list(cells)
        else:
            rows.append(cells)
    return headers, rows


def toNormalForm(sub: list[str], period_year: int | None = None) -> NormalizedTable:
    """서브테이블 → 정규형. multi_year 감지 시 당기만 추출."""
    hc = _headerCells(sub)
    if _isJunk(hc):
        return NormalizedTable()

    dr = _dataRows(sub)
    if not dr:
        return NormalizedTable()

    headers, rows = _parseMdTable(sub)
    unit = _extractUnit(sub)
    header_sig = _groupHeaderSig(hc)

    if not headers or not rows:
        return NormalizedTable(unit=unit, header_sig=header_sig)

    # 단위 헤더 → shift
    if _isUnitOrDateHeader(headers):
        if rows:
            headers = rows[0]
            rows = rows[1:]
        else:
            return NormalizedTable(unit=unit, header_sig=header_sig)

    # multi_year
    if any(kw in " ".join(headers) for kw in _MULTI_YEAR_KW):
        return _normalFormMultiYear(sub, headers, rows, period_year, unit, header_sig)

    # flat
    return _normalFormFlat(headers, rows, unit, header_sig)


def _normalFormMultiYear(sub, headers, rows, period_year, unit, header_sig):
    """multi_year → 당기 값만 추출. col_key='value'."""
    # 기수 행 찾기
    kisu_nums = []
    kisu_row_idx = -1
    for i, row in enumerate(rows):
        for cell in row:
            m = re.search(r"제\s*(\d+)\s*기", cell)
            if m:
                kisu_nums.append(int(m.group(1)))
        if kisu_nums:
            kisu_row_idx = i
            break

    if not kisu_nums or period_year is None:
        # 기수 없으면 당기 컬럼 직접 추출
        current_idx = -1
        for i, h in enumerate(headers):
            if "당기" in h and "전" not in h:
                current_idx = i
                break
        if current_idx < 0:
            current_idx = 1

        triples = []
        row_keys = []
        seen = set()
        for row in rows:
            if not row or not row[0].strip():
                continue
            item = _normalizeItem(row[0].strip())
            if _isJunkItem(item):
                continue
            val = row[current_idx].strip() if current_idx < len(row) else ""
            if val and val != "-":
                if item not in seen:
                    row_keys.append(item)
                    seen.add(item)
                triples.append(Triple(item, "value", val))

        return NormalizedTable(triples, unit, "multi_year", row_keys, ["value"], header_sig)

    max_kisu = max(kisu_nums)
    sorted_kisu = sorted(kisu_nums, reverse=True)
    kisu_to_year = {kn: period_year - max_kisu + kn for kn in kisu_nums}

    triples = []
    row_keys = []
    seen = set()
    prev_item = ""

    for row in rows[kisu_row_idx + 1:]:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first.startswith("※"):
            continue

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

        non_empty = [(i, v.strip()) for i, v in enumerate(vals)
                     if v.strip() and v.strip() != "-" and v.strip() not in _STOCK_TYPES]

        if len(non_empty) >= len(sorted_kisu):
            tail = non_empty[-len(sorted_kisu):]
            for idx, (_, val) in enumerate(tail):
                year = kisu_to_year[sorted_kisu[idx]]
                if year == period_year:
                    if item not in seen:
                        row_keys.append(item)
                        seen.add(item)
                    triples.append(Triple(item, "value", val))

    return NormalizedTable(triples, unit, "multi_year", row_keys, ["value"], header_sig)


def _normalFormFlat(headers, rows, unit, header_sig):
    """flat → 정규형. col_key = 헤더 컬럼명."""
    triples = []
    row_keys = []
    seen_rk = set()
    col_keys = []

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
                triples.append(Triple(item, ck, val))

    return NormalizedTable(triples, unit, "flat", row_keys, col_keys, header_sig)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 서브테이블 클러스터링 + 수평화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def horizontalizeTopic(
    topic_frame: pl.DataFrame,
    period_cols: list[str],
) -> list[pl.DataFrame]:
    """sections의 table 행들 → 서브테이블별 독립 수평화.

    핵심 개선: 서브테이블을 header_sig로 클러스터링하여 각각 독립 수평화.
    반환: 수평화 성공한 DataFrame 리스트.
    """
    if topic_frame.is_empty():
        return []

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}

    # 1단계: 기간별 서브테이블 → 정규형 변환 + header_sig 수집
    #   cluster_key = header_sig
    #   cluster_data[cluster_key][period] = list[NormalizedTable]
    cluster_data: dict[str, dict[str, list[NormalizedTable]]] = defaultdict(lambda: defaultdict(list))

    for p in period_cols:
        if p not in topic_frame.columns:
            continue
        p_year = int(re.match(r"(\d{4})", p).group()) if re.match(r"(\d{4})", p) else None

        for row_idx in range(topic_frame.height):
            md = topic_frame[p][row_idx]
            if md is None:
                continue

            for sub in splitSubtables(str(md)):
                nf = toNormalForm(sub, period_year=p_year)
                if not nf.triples:
                    continue
                cluster_data[nf.header_sig][p].append(nf)

    # 2단계: 각 클러스터별 독립 수평화
    results = []
    for sig, period_tables in cluster_data.items():
        df = _horizontalizeCluster(period_tables, period_cols)
        if df is not None:
            results.append(df)

    return results


def _horizontalizeCluster(
    period_tables: dict[str, list[NormalizedTable]],
    period_cols: list[str],
) -> pl.DataFrame | None:
    """한 클러스터(같은 header_sig)의 정규형 → 수평화."""
    # 타입 판별
    has_multi_year = any(
        t.table_type == "multi_year"
        for ts in period_tables.values()
        for t in ts
    )

    if has_multi_year:
        return _hzMultiYear(period_tables, period_cols)
    else:
        return _hzFlat(period_tables, period_cols)


def _hzMultiYear(period_tables, period_cols):
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

    all_items = [i for i in all_items if not _isJunkItem(i)]
    return _buildDataFrame(all_items, item_period_val, period_cols)


def _hzFlat(period_tables, period_cols):
    # (row_key, col_key) → {period → value}
    data: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    all_items: list[str] = []
    seen: set[str] = set()
    all_col_keys: list[str] = []
    seen_ck: set[str] = set()

    for period, tables in period_tables.items():
        for t in tables:
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

    # col_key 1개 → 단순 수평화
    if len(all_col_keys) <= 1:
        item_period_val = {}
        for (rk, ck), pv in data.items():
            if rk in set(all_items):
                item_period_val[rk] = pv
        return _buildDataFrame(all_items, item_period_val, period_cols)

    # col_key 여러 개 → matrix: 헤더별 분리 또는 pipe join
    if len(all_col_keys) <= 5:
        # 헤더별 분리: row_key_col_key 복합 항목
        compound_items = []
        compound_seen = set()
        compound_pv = {}
        for rk in all_items:
            for ck in all_col_keys:
                key = (rk, ck)
                if key not in data:
                    continue
                compound = f"{rk}_{ck}"
                if compound not in compound_seen:
                    compound_items.append(compound)
                    compound_seen.add(compound)
                compound_pv[compound] = data[key]
        return _buildDataFrame(compound_items, compound_pv, period_cols)
    else:
        # col_key 6개 이상: pipe join (기존 방식과 동일)
        item_period_val: dict[str, dict[str, str]] = {}
        for rk in all_items:
            pv: dict[str, str] = {}
            for p in period_cols:
                vals = []
                for ck in all_col_keys:
                    v = data.get((rk, ck), {}).get(p, "")
                    if v:
                        vals.append(v)
                if vals:
                    pv[p] = " | ".join(vals)
            if pv:
                item_period_val[rk] = pv
        return _buildDataFrame(all_items, item_period_val, period_cols)


def _buildDataFrame(items, item_period_val, period_cols) -> pl.DataFrame | None:
    if not items:
        return None

    # 이력형 감지
    period_sets: dict[str, set[str]] = {}
    for item in items:
        for p in item_period_val.get(item, {}):
            if p not in period_sets:
                period_sets[p] = set()
            period_sets[p].add(item)

    if len(period_sets) >= 2:
        sets = list(period_sets.values())
        total = 0
        pairs = 0
        for i in range(len(sets)):
            for j in range(i+1, min(i+4, len(sets))):
                u = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if u:
                    total += inter/u
                    pairs += 1
        avg = total/pairs if pairs else 0
        if avg < 0.3 and len(items) > 5:
            return None  # 이력형

    if len(items) > 50:
        return None  # 목록형

    used = [p for p in period_cols if any(p in item_period_val.get(item, {}) for item in items)]
    if not used:
        return None

    # sparse 감지
    if len(used) >= 3 and len(items) > 15:
        total = len(items) * len(used)
        filled = sum(1 for item in items for p in used if item_period_val.get(item, {}).get(p))
        if filled/total < 0.5:
            return None

    rows = []
    for item in items:
        if not any(item_period_val.get(item, {}).get(p) for p in used):
            continue
        row: dict[str, str | None] = {"항목": item}
        for p in used:
            row[p] = item_period_val.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None

    schema = {"항목": pl.Utf8}
    for p in used:
        schema[p] = pl.Utf8
    return pl.DataFrame(rows, schema=schema)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 비교 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compare10():
    from dartlab import Company

    test_stocks = ["삼성전자", "SK하이닉스", "셀트리온", "KB금융", "LG화학", "삼성물산"]
    test_topics = ["dividend", "audit", "salesOrder", "employee", "companyOverview"]

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
    results = []

    for stock in test_stocks:
        try:
            c = Company(stock)
            sections = c.sections
        except Exception as e:
            print(f"  {stock}: 실패 — {e}")
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

            # 기존
            try:
                show_r = c.show(topic)
                existing_ok = False
                if isinstance(show_r, pl.DataFrame) and "block" in show_r.columns:
                    for b in show_r.filter(pl.col("type") == "table")["block"].to_list():
                        try:
                            bdf = c.show(topic, b)
                            if isinstance(bdf, pl.DataFrame) and not bdf.is_empty():
                                existing_ok = True
                                break
                        except Exception:
                            pass
            except Exception:
                existing_ok = False

            # 정규형 (클러스터링 포함)
            try:
                nf_results = horizontalizeTopic(topic_rows, period_cols)
                nf_ok = len(nf_results) > 0
            except Exception:
                nf_ok = False

            results.append({
                "stock": stock,
                "topic": topic,
                "existing": existing_ok,
                "nf_clustered": nf_ok,
            })

            if nf_ok and not existing_ok:
                print(f"  [NF만 성공] {stock}/{topic}: {len(nf_results)}개 클러스터")
            elif existing_ok and not nf_ok:
                print(f"  [기존만 성공] {stock}/{topic}")

    df = pl.DataFrame(results)
    print(f"\n{'='*60}")
    print("비교 결과")
    print(f"{'='*60}")
    print(f"총 {df.height}개")
    e_total = df.filter(pl.col("existing")).height
    n_total = df.filter(pl.col("nf_clustered")).height
    print(f"기존 성공: {e_total} ({100*e_total/df.height:.0f}%)")
    print(f"정규형 성공: {n_total} ({100*n_total/df.height:.0f}%)")
    print(f"정규형만 성공: {df.filter(~pl.col('existing') & pl.col('nf_clustered')).height}")
    print(f"기존만 성공: {df.filter(pl.col('existing') & ~pl.col('nf_clustered')).height}")

    for topic in test_topics:
        tf = df.filter(pl.col("topic") == topic)
        if tf.is_empty():
            continue
        e = tf.filter(pl.col("existing")).height
        n = tf.filter(pl.col("nf_clustered")).height
        print(f"  {topic}: 기존 {e}/{tf.height}, 정규형 {n}/{tf.height}")

    # 삼성전자 dividend 상세 출력
    print(f"\n{'='*60}")
    print("삼성전자 dividend 정규형 수평화 상세")
    print(f"{'='*60}")
    c = Company("삼성전자")
    sections = c.sections
    topic_rows = sections.filter(
        (pl.col("topic") == "dividend") & (pl.col("blockType") == "table")
    )
    period_cols = sorted([
        col for col in topic_rows.columns
        if col not in meta_cols and re.match(r"\d{4}", col)
    ])
    nf_results = horizontalizeTopic(topic_rows, period_cols)
    for i, df in enumerate(nf_results):
        print(f"\n  클러스터 {i}: {df.shape}")
        # 최근 3기간만
        display_cols = ["항목"] + [p for p in period_cols[-3:] if p in df.columns]
        print(df.select([c for c in display_cols if c in df.columns]).head(8))


if __name__ == "__main__":
    compare10()
