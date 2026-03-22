"""실험 ID: 066-003
실험명: 정규형 실패 원인 진단 — 핵심 3 topic 상세 분석

실험일: 2026-03-18
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

import polars as pl

sys.path.insert(0, "C:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

from dartlab.engines.company.dart.docs.sections.tableParser import splitSubtables

# ── 002에서 복사한 핵심 함수들 (import 문제 회피) ──

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


def _isUnitOrDateHeader(cells: list[str]) -> bool:
    h = " ".join(c.strip() for c in cells).strip()
    if not h:
        return False
    return bool(_UNIT_RE.match(h)) or bool(_DATE_RE.match(h))


def _isMultiYear(headers: list[str]) -> bool:
    joined = " ".join(headers)
    return any(kw in joined for kw in _MULTI_YEAR_KW)


def _normalFormFlat(headers, rows):
    """flat 변환 → (triples, row_keys, col_keys)."""
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
                triples.append((item, ck, val))

    return triples, row_keys, col_keys


def diagnose():
    from dartlab import Company

    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}

    cases = [
        ("삼성전자", "audit"),
        ("삼성전자", "salesOrder"),
        ("삼성전자", "companyOverview"),
    ]

    for stock, topic in cases:
        print(f"\n{'='*70}")
        print(f"{stock} / {topic}")
        print(f"{'='*70}")

        c = Company(stock)
        sections = c.sections
        topic_rows = sections.filter(
            (pl.col("topic") == topic) & (pl.col("blockType") == "table")
        )
        if topic_rows.is_empty():
            print("  table 블록 없음")
            continue

        period_cols = sorted([
            col for col in topic_rows.columns
            if col not in meta_cols and re.match(r"\d{4}", col)
        ])

        # 각 기간별 triples 수집 → 항목 겹침 분석
        period_items = defaultdict(set)  # period → set of item names
        period_triple_count = {}
        total_unique_items = set()
        sub_count_per_period = {}

        for p in period_cols:
            triple_count = 0
            sub_count = 0
            for row_idx in range(topic_rows.height):
                md = topic_rows[p][row_idx]
                if md is None:
                    continue
                subs = splitSubtables(str(md))
                sub_count += len(subs)

                for sub in subs:
                    headers, rows = _parseMdTable(sub)
                    if not headers or not rows:
                        continue
                    if _isUnitOrDateHeader(headers):
                        if rows:
                            headers = rows[0]
                            rows = rows[1:]
                    if _isMultiYear(headers):
                        # multi_year는 별도 처리
                        for row in rows:
                            if row and row[0].strip():
                                item = _normalizeItem(row[0].strip())
                                if not _isJunkItem(item):
                                    period_items[p].add(item)
                                    total_unique_items.add(item)
                                    triple_count += 1
                    else:
                        triples, rks, cks = _normalFormFlat(headers, rows)
                        for rk, ck, val in triples:
                            period_items[p].add(rk)
                            total_unique_items.add(rk)
                            triple_count += 1

            period_triple_count[p] = triple_count
            sub_count_per_period[p] = sub_count

        # 기간별 항목 수 + 겹침률
        print(f"\n  고유 항목 총합: {len(total_unique_items)}")
        print(f"  기간 수: {len(period_cols)}")

        # 최근 5기간 항목 수
        recent5 = period_cols[-5:]
        print(f"\n  최근 5기간:")
        for p in recent5:
            print(f"    {p}: 항목 {len(period_items[p])}, triples {period_triple_count.get(p,0)}, subs {sub_count_per_period.get(p,0)}")

        # 인접 기간 Jaccard
        if len(period_cols) >= 2:
            sets_list = [period_items[p] for p in period_cols if period_items[p]]
            overlaps = []
            for i in range(len(sets_list)):
                for j in range(i+1, min(i+4, len(sets_list))):
                    u = len(sets_list[i] | sets_list[j])
                    inter = len(sets_list[i] & sets_list[j])
                    if u:
                        overlaps.append(inter/u)
            avg = sum(overlaps)/len(overlaps) if overlaps else 0
            print(f"\n  평균 Jaccard: {avg:.3f}")
            if avg < 0.3 and len(total_unique_items) > 5:
                print(f"  → 이력형 감지됨 (< 0.3, 항목 > 5)")
            elif len(total_unique_items) > 50:
                print(f"  → 목록형 감지됨 (> 50)")
            else:
                print(f"  → 수평화 가능")

        # 핵심: 왜 기존은 성공하는가?
        print(f"\n  기존 show() 결과:")
        try:
            show_r = c.show(topic)
            if isinstance(show_r, pl.DataFrame) and "block" in show_r.columns:
                table_blocks = show_r.filter(pl.col("type") == "table")
                print(f"    table 블록 {table_blocks.height}개")
                for b in table_blocks["block"].to_list()[:3]:
                    try:
                        bdf = c.show(topic, b)
                        if isinstance(bdf, pl.DataFrame) and not bdf.is_empty():
                            print(f"    block[{b}]: {bdf.shape}")
                            print(f"      항목: {bdf['항목'].head(5).to_list()}")
                        else:
                            print(f"    block[{b}]: None")
                    except Exception as e:
                        print(f"    block[{b}]: 에러 — {e}")
        except Exception as e:
            print(f"    에러 — {e}")


if __name__ == "__main__":
    diagnose()
