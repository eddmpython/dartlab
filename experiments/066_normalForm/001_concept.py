"""실험 ID: 066-001
실험명: Universal Table Normalizer — Normal Form 개념 검증

목적:
- 마크다운 테이블을 구조 무관하게 (row_key, col_key, value) 정규형으로 변환
- 정규형끼리 기간별 수평화하여 기존 규칙 기반 대비 성능 검증
- 이력형 테이블도 정규형으로 통합 처리 가능한지 확인

가설:
1. 모든 마크다운 테이블은 (row_key, col_key, value) 트리플로 분해 가능
2. 정규형 기반 수평화는 구조 분류(multi_year/key_value/matrix) 없이 통합 처리 가능
3. 이력형 테이블도 정규형으로 변환 후 같은 파이프라인으로 수평화 가능
4. 항목 매칭이 (row_key, col_key) 복합키로 더 정확해짐

방법:
1. 마크다운 테이블 → 정규형 변환 함수 구현
2. 기간별 정규형 merge → 수평화
3. 10종목 × 5 topic 검증 (기존 파이프라인과 비교)
4. 이력형/목록형에서의 동작 확인
5. 기존 대비 성공률/품질 비교

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
# 1. Normal Form: (row_key, col_key, value) 트리플
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class Triple:
    """정규형 트리플: 하나의 데이터 포인트."""
    row_key: str
    col_key: str
    value: str


@dataclass
class NormalizedTable:
    """정규형으로 분해된 테이블."""
    triples: list[Triple] = field(default_factory=list)
    unit: str | None = None
    source_header: str = ""
    row_keys_ordered: list[str] = field(default_factory=list)
    col_keys_ordered: list[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 마크다운 파싱 유틸
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _parseMdTable(md_lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """마크다운 테이블 → (헤더 셀 리스트, 데이터 행 리스트).

    separator 행을 자동 감지하여 분리.
    """
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
            # separator 전 = 헤더
            if not headers:
                headers = [c for c in cells]
            else:
                # 다중행 헤더: 기존 헤더에 append
                for i, c in enumerate(cells):
                    if i < len(headers) and c.strip():
                        headers[i] = f"{headers[i]} {c.strip()}"
        else:
            rows.append(cells)

    return headers, rows


def _splitSubtables(md: str) -> list[list[str]]:
    """기존 splitSubtables와 동일한 로직."""
    from dartlab.engines.dart.docs.sections.tableParser import splitSubtables
    return splitSubtables(md)


def _extractUnit(lines: list[str]) -> str | None:
    full = "\n".join(lines)
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    return m.group(1).strip() if m else None


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


def _isUnitOrDateHeader(cells: list[str]) -> bool:
    """첫 행이 단위/기준일만 있는 행인지."""
    h = " ".join(c.strip() for c in cells).strip()
    if not h:
        return False
    return bool(_UNIT_RE.match(h)) or bool(_DATE_RE.match(h))


_KISU_RE = re.compile(
    r"제\s*\d+\s*기\s*(?:\d*분기|반기|말)?\s*"
    r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
)

_SUFFIX_RE = re.compile(r"(사업)?부문$")
_NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")


def _normalizeItem(name: str) -> str:
    """항목명 정규화."""
    name = re.sub(r"\s+", "", name)
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("ㆍ", "·")
    name = _SUFFIX_RE.sub("", name).strip()
    name = _NOTE_REF_RE.sub("", name).strip()
    m = _KISU_RE.search(name)
    if m:
        return m.group(1)
    return name


def _isJunkItem(name: str) -> bool:
    stripped = re.sub(r"[,.\-\s]", "", name)
    return stripped.isdigit() or not stripped


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 핵심: 마크다운 테이블 → 정규형 변환
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def toNormalForm(md_lines: list[str]) -> NormalizedTable:
    """마크다운 서브테이블(라인 리스트) → 정규형 트리플 변환.

    구조 분류 없이 통합 처리:
    - 헤더가 N개면, 각 데이터 행의 첫 셀 = row_key, 나머지 = (col_key=헤더[i], value)
    - 2컬럼이면 자동으로 key_value
    - 3+컬럼이면 자동으로 matrix
    - multi_year(당기/전기 헤더)도 동일하게 처리 — col_key에 기수가 들어감
    """
    headers, rows = _parseMdTable(md_lines)
    unit = _extractUnit(md_lines)

    if not headers or not rows:
        return NormalizedTable(unit=unit, source_header=" | ".join(headers))

    # 단위/기준일 헤더 스킵
    if _isUnitOrDateHeader(headers):
        # separator 이후 첫 데이터행을 헤더로 사용
        if rows:
            headers = rows[0]
            rows = rows[1:]
        else:
            return NormalizedTable(unit=unit)

    triples: list[Triple] = []
    row_keys: list[str] = []
    seen_row_keys: set[str] = set()
    col_keys: list[str] = []

    # col_keys = 헤더의 2번째~마지막 (첫 컬럼은 row_key 축)
    for h in headers[1:]:
        ck = _normalizeItem(h) if h.strip() else f"col_{len(col_keys)}"
        col_keys.append(ck)

    group_prefix = ""

    for row in rows:
        if not row or not row[0].strip():
            continue

        raw_row_key = row[0].strip()
        if raw_row_key.startswith("※") or raw_row_key.startswith("☞"):
            continue

        row_key = _normalizeItem(raw_row_key)
        if _isJunkItem(row_key):
            continue

        values = row[1:]

        # 그룹 헤더 감지: 모든 값이 비어있으면 접두사로 사용
        all_empty = all(not v.strip() or v.strip() == "-" for v in values)
        if all_empty and len(values) >= 2:
            group_prefix = row_key
            continue

        if group_prefix:
            row_key = f"{group_prefix}_{row_key}"

        if row_key not in seen_row_keys:
            row_keys.append(row_key)
            seen_row_keys.add(row_key)

        for i, ck in enumerate(col_keys):
            val = values[i].strip() if i < len(values) else ""
            if val and val != "-":
                triples.append(Triple(row_key=row_key, col_key=ck, value=val))

    return NormalizedTable(
        triples=triples,
        unit=unit,
        source_header=" | ".join(headers),
        row_keys_ordered=row_keys,
        col_keys_ordered=col_keys,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 정규형 수평화: 기간별 NormalizedTable → DataFrame
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def horizontalizeNormal(
    period_tables: dict[str, list[NormalizedTable]],
    period_cols: list[str],
) -> pl.DataFrame | None:
    """기간별 NormalizedTable 리스트 → 수평화된 DataFrame.

    핵심 아이디어:
    - 각 기간의 트리플을 모두 모음
    - (row_key, col_key) 복합키 기준으로 기간별 값을 정렬
    - 결과: 항목(row_key_col_key) × period 매트릭스
    """
    # 모든 트리플 수집: (row_key, col_key) → {period → value}
    data: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    row_key_order: list[str] = []
    seen_row_keys: set[str] = set()

    for period, tables in period_tables.items():
        for table in tables:
            for rk in table.row_keys_ordered:
                if rk not in seen_row_keys:
                    row_key_order.append(rk)
                    seen_row_keys.add(rk)
            for t in table.triples:
                data[(t.row_key, t.col_key)][period] = t.value

    if not data:
        return None

    # col_key 집합 수집 (모든 기간 통합)
    all_col_keys: list[str] = []
    seen_ck: set[str] = set()
    for period, tables in period_tables.items():
        for table in tables:
            for ck in table.col_keys_ordered:
                if ck not in seen_ck:
                    all_col_keys.append(ck)
                    seen_ck.add(ck)

    # 사용된 기간만 필터
    used_periods = [p for p in period_cols if any(p in vals for vals in data.values())]
    if not used_periods:
        return None

    # DataFrame 구성
    rows: list[dict[str, str | None]] = []
    for rk in row_key_order:
        for ck in all_col_keys:
            key = (rk, ck)
            if key not in data:
                continue
            row: dict[str, str | None] = {"항목": rk, "지표": ck}
            has_any = False
            for p in used_periods:
                val = data[key].get(p)
                row[p] = val
                if val:
                    has_any = True
            if has_any:
                rows.append(row)

    if not rows:
        return None

    return pl.DataFrame(rows)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 테스트 & 비교
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _testWithSample():
    """예제 테이블로 개념 검증."""

    print("=" * 60)
    print("테스트 1: 현황형 (key_value)")
    print("=" * 60)

    md1_2024 = """| 구분 | 인원수 | 승인금액 |
| --- | --- | --- |
| 등기이사 | 5 | 46,500 |
| 사외이사 | 4 | 22,000 |
| 감사위원 | 3 | - |"""

    md1_2023 = """| 구분 | 인원수 | 승인금액 |
| --- | --- | --- |
| 등기이사 | 5 | 43,000 |
| 사외이사 | 4 | 20,000 |"""

    subs_2024 = _splitSubtables(md1_2024)
    subs_2023 = _splitSubtables(md1_2023)

    nf_2024 = [toNormalForm(sub) for sub in subs_2024]
    nf_2023 = [toNormalForm(sub) for sub in subs_2023]

    for nf in nf_2024:
        print(f"\n2024 정규형 ({len(nf.triples)} triples):")
        for t in nf.triples:
            print(f"  ({t.row_key}, {t.col_key}, {t.value})")

    result = horizontalizeNormal(
        {"2024": nf_2024, "2023": nf_2023},
        ["2023", "2024"],
    )
    print(f"\n수평화 결과:")
    if result is not None:
        print(result)
    else:
        print("  None")

    print("\n" + "=" * 60)
    print("테스트 2: 이력형")
    print("=" * 60)

    md2_2024 = """| 변동일자 | 주총종류 | 선임 | 퇴임 |
| --- | --- | --- | --- |
| 2024.03.15 | 정기주총 | 사내이사 김철수 | 사내이사 박영희 |
| 2024.06.01 | 임시주총 | 사외이사 이민수 | - |"""

    md2_2023 = """| 변동일자 | 주총종류 | 선임 | 퇴임 |
| --- | --- | --- | --- |
| 2023.03.17 | 정기주총 | 사내이사 박영희 | 사내이사 최동우 |"""

    nf2_2024 = [toNormalForm(sub) for sub in _splitSubtables(md2_2024)]
    nf2_2023 = [toNormalForm(sub) for sub in _splitSubtables(md2_2023)]

    print(f"\n2024 정규형 ({len(nf2_2024[0].triples)} triples):")
    for t in nf2_2024[0].triples:
        print(f"  ({t.row_key}, {t.col_key}, {t.value})")

    result2 = horizontalizeNormal(
        {"2024": nf2_2024, "2023": nf2_2023},
        ["2023", "2024"],
    )
    print(f"\n수평화 결과:")
    if result2 is not None:
        print(result2)
    else:
        print("  None")

    print("\n" + "=" * 60)
    print("테스트 3: multi_year (당기/전기 헤더)")
    print("=" * 60)

    md3_2024 = """| 구분 | 당기 | 전기 | 전전기 |
| --- | --- | --- | --- |
| (단위:백만원) |  |  |  |
| 제56기 | 제55기 | 제54기 |  |
| 매출액 | 300,870,226 | 258,935,542 | 302,231,360 |
| 영업이익 | 32,726,954 | 6,566,828 | 43,376,617 |"""

    md3_2023 = """| 구분 | 당기 | 전기 | 전전기 |
| --- | --- | --- | --- |
| (단위:백만원) |  |  |  |
| 제55기 | 제54기 | 제53기 |  |
| 매출액 | 258,935,542 | 302,231,360 | 279,604,588 |
| 영업이익 | 6,566,828 | 43,376,617 | 51,633,816 |"""

    nf3_2024 = [toNormalForm(sub) for sub in _splitSubtables(md3_2024)]
    nf3_2023 = [toNormalForm(sub) for sub in _splitSubtables(md3_2023)]

    print(f"\n2024 정규형:")
    for t in nf3_2024[0].triples:
        print(f"  ({t.row_key}, {t.col_key}, {t.value})")

    result3 = horizontalizeNormal(
        {"2024": nf3_2024, "2023": nf3_2023},
        ["2023", "2024"],
    )
    print(f"\n수평화 결과:")
    if result3 is not None:
        print(result3)
    else:
        print("  None")


def _testWithRealData():
    """실제 데이터로 검증."""
    from dartlab import Company

    print("\n" + "=" * 60)
    print("실제 데이터 검증: 삼성전자")
    print("=" * 60)

    c = Company("삼성전자")
    sections = c.sections

    # dividend topic의 table 블록 가져오기
    topic = "dividend"
    topic_rows = sections.filter(
        (pl.col("topic") == topic) & (pl.col("blockType") == "table")
    )

    if topic_rows.is_empty():
        print(f"  {topic}: table 블록 없음")
        return

    # 기간 컬럼 추출
    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "label"}
    period_cols = [c for c in topic_rows.columns if c not in meta_cols]
    period_cols = sorted([p for p in period_cols if re.match(r"\d{4}", p)])

    print(f"\n{topic}: {topic_rows.height}개 table 행, {len(period_cols)}개 기간")

    # 각 기간별로 정규형 변환
    period_tables: dict[str, list[NormalizedTable]] = {}

    for p in period_cols:
        tables = []
        for row_idx in range(topic_rows.height):
            md = topic_rows[p][row_idx]
            if md is None:
                continue
            for sub in _splitSubtables(str(md)):
                hc_cells = [c.strip() for c in sub[0].strip("|").split("|")] if sub else []
                if not hc_cells or all(not c.strip() for c in hc_cells):
                    continue
                nf = toNormalForm(sub)
                if nf.triples:
                    tables.append(nf)
        if tables:
            period_tables[p] = tables

    print(f"  정규형 변환: {sum(len(t) for t in period_tables.values())} tables across {len(period_tables)} periods")

    # 수평화
    result = horizontalizeNormal(period_tables, period_cols)
    if result is not None:
        print(f"  수평화 결과: {result.shape}")
        # 최근 3기간 + 처음 5행만 표시
        display_periods = period_cols[-3:]
        display_cols = ["항목", "지표"] + [p for p in display_periods if p in result.columns]
        display = result.select([c for c in display_cols if c in result.columns]).head(10)
        print(display)
    else:
        print("  수평화 실패: None")

    # 기존 show()와 비교
    print(f"\n기존 show() 결과:")
    existing = c.show(topic)
    if existing is not None:
        if isinstance(existing, list):
            for i, block in enumerate(existing):
                if isinstance(block, pl.DataFrame):
                    print(f"  block[{i}]: {block.shape}")
                    if block.height > 0 and block.height <= 20:
                        print(block.head(5))
        elif isinstance(existing, pl.DataFrame):
            print(f"  shape: {existing.shape}")
            print(existing.head(5))


if __name__ == "__main__":
    print("━━━ Normal Form 개념 검증 ━━━\n")
    _testWithSample()
    print("\n━━━ 실제 데이터 검증 ━━━\n")
    _testWithRealData()
