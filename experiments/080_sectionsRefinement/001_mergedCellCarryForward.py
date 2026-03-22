"""
실험 ID: 080-001
실험명: tableParser merged cell carry-forward 검증

목적:
- tableParser에서 빈 첫컬럼 행(HTML merged cell의 markdown 표현)이 통째로 drop되는 문제 검증
- carry-forward 적용 시 복구되는 행 수와 regression 여부 확인

가설:
1. _parseMultiYear와 _parseKeyValueOrMatrix에서 빈 첫컬럼 행을 prevItem으로 carry-forward하면 유의미한 데이터 행이 복구된다
2. carry-forward가 기존 파싱 결과에 regression을 일으키지 않는다

방법:
1. 10종목의 sections에서 table block을 추출
2. 원본 파서로 파싱한 결과(baseline) 수집
3. carry-forward 패치 파서로 파싱한 결과(patched) 수집
4. before/after 비교: 복구된 행 수, regression 여부

결과:
- multi_year: 3,156→3,156 (변화 없음) — multi_year는 빈 첫컬럼 행이 거의 없음
- kv/matrix: 2,342,639→2,352,855 (+10,216행 복구, +0.44%)
- regression: 0건
- 종목별 복구량: 신한지주 +4,822 (금융업 테이블 구조), SK하이닉스 +1,959, POSCO +1,273
- multi_year는 기수 기반이라 merged cell 패턴 자체가 드물지만 방어적으로 적용

결론:
- 채택. kv/matrix에서 10,216개 행 복구, regression 0건
- carry-forward는 금융업(KB금융, 신한지주)처럼 복잡한 테이블 구조에서 특히 효과적
- multi_year에도 방어적으로 적용하되 실측 효과는 0

실험일: 2026-03-20
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.engines.dart.docs.sections.tableParser import (
    _STOCK_TYPES,
    _classifyStructure,
    _dataRows,
    _extractUnit,
    _headerCells,
    _normalizeItemName,
    splitSubtables,
)
from dartlab.engines.dart.docs.sections.pipeline import iterPeriodSubsets


# ── 원본 함수 (baseline) ──


def _parseMultiYear_original(sub: list[str], periodYear: int):
    """원본 _parseMultiYear — 빈 첫컬럼 skip."""
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break
    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return [], None

    kisuCells = [c.strip() for c in sub[sepIdx + 1].strip("|").split("|")]
    kisuNums = []
    for cell in kisuCells:
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))
    if not kisuNums:
        return [], None

    maxKisu = max(kisuNums)
    sortedKisu = sorted(kisuNums, reverse=True)
    kisuToYear = {kn: str(periodYear - maxKisu + kn) for kn in kisuNums}
    unit = _extractUnit(sub)
    triples = []
    prevItem = ""

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        if not cells or not cells[0].strip():
            continue  # ← 빈 첫컬럼 DROP

        first = cells[0].strip()
        if first.startswith("※"):
            continue
        if first in _STOCK_TYPES and prevItem:
            itemName = _normalizeItemName(f"{prevItem}-{first}")
            valCells = cells[1:]
        elif len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
            stockType = cells[1].strip()
            itemName = _normalizeItemName(f"{first}-{stockType}")
            valCells = cells[2:]
            prevItem = first
        else:
            itemName = _normalizeItemName(first)
            valCells = cells[1:]
            prevItem = first

        for i, kn in enumerate(sortedKisu):
            if i < len(valCells):
                val = valCells[i].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    triples.append((itemName, kisuToYear[kn], val))

    return triples, unit


def _parseKvMatrix_original(sub: list[str]):
    """원본 _parseKeyValueOrMatrix — 빈 첫컬럼 skip."""
    headerCells = _headerCells(sub)
    headerNames = [_normalizeItemName(h) for h in headerCells[1:]] if len(headerCells) > 1 else []
    rows = _dataRows(sub)
    unit = _extractUnit(sub)
    result = []

    isSubHeader = (
        rows
        and rows[0]
        and all(not any(ch.isdigit() for ch in c) for c in rows[0])
        and len(rows[0]) <= len(headerCells)
    )
    dataStart = 1 if isSubHeader else 0

    prevGroupItem = ""
    for row in rows[dataStart:]:
        if not row or not row[0].strip():
            continue  # ← 빈 첫컬럼 DROP
        first = row[0].strip()
        if first.startswith("※") or first.startswith("☞"):
            continue
        item = _normalizeItemName(first)
        values = [c.strip() for c in row[1:]]
        allEmpty = all(not v or v == "-" for v in values)
        if allEmpty and len(values) >= 2:
            prevGroupItem = item
            continue
        if prevGroupItem and not allEmpty:
            item = f"{prevGroupItem}_{item}"
        if item:
            result.append((item, values))

    return result, headerNames, unit


# ── 패치 함수 (carry-forward) ──


def _parseMultiYear_patched(sub: list[str], periodYear: int):
    """패치 _parseMultiYear — 빈 첫컬럼 carry-forward."""
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break
    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return [], None

    kisuCells = [c.strip() for c in sub[sepIdx + 1].strip("|").split("|")]
    kisuNums = []
    for cell in kisuCells:
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))
    if not kisuNums:
        return [], None

    maxKisu = max(kisuNums)
    sortedKisu = sorted(kisuNums, reverse=True)
    kisuToYear = {kn: str(periodYear - maxKisu + kn) for kn in kisuNums}
    unit = _extractUnit(sub)
    triples = []
    prevItem = ""

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        if not cells:
            continue
        # ── carry-forward ──
        if not cells[0].strip():
            if not prevItem:
                continue
            first = prevItem
        else:
            first = cells[0].strip()

        if first.startswith("※"):
            continue
        if first in _STOCK_TYPES and prevItem:
            itemName = _normalizeItemName(f"{prevItem}-{first}")
            valCells = cells[1:]
        elif len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
            stockType = cells[1].strip()
            itemName = _normalizeItemName(f"{first}-{stockType}")
            valCells = cells[2:]
            prevItem = first
        else:
            itemName = _normalizeItemName(first)
            valCells = cells[1:]
            prevItem = first

        for i, kn in enumerate(sortedKisu):
            if i < len(valCells):
                val = valCells[i].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    triples.append((itemName, kisuToYear[kn], val))

    return triples, unit


def _parseKvMatrix_patched(sub: list[str]):
    """패치 _parseKeyValueOrMatrix — 빈 첫컬럼 carry-forward."""
    headerCells = _headerCells(sub)
    headerNames = [_normalizeItemName(h) for h in headerCells[1:]] if len(headerCells) > 1 else []
    rows = _dataRows(sub)
    unit = _extractUnit(sub)
    result = []

    isSubHeader = (
        rows
        and rows[0]
        and all(not any(ch.isdigit() for ch in c) for c in rows[0])
        and len(rows[0]) <= len(headerCells)
    )
    dataStart = 1 if isSubHeader else 0

    prevGroupItem = ""
    prevCarryItem = ""
    for row in rows[dataStart:]:
        if not row:
            continue
        # ── carry-forward ──
        if not row[0].strip():
            if not prevCarryItem:
                continue
            first = prevCarryItem
        else:
            first = row[0].strip()

        if first.startswith("※") or first.startswith("☞"):
            continue
        item = _normalizeItemName(first)
        values = [c.strip() for c in row[1:]]
        allEmpty = all(not v or v == "-" for v in values)
        if allEmpty and len(values) >= 2:
            prevGroupItem = item
            continue
        if prevGroupItem and not allEmpty:
            item = f"{prevGroupItem}_{item}"
        if item:
            result.append((item, values))
            prevCarryItem = first  # 일반 item에서만 업데이트

    return result, headerNames, unit


# ── 실험 본체 ──


def run_experiment():
    """10종목 before/after 비교."""
    test_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005490",  # POSCO홀딩스
        "105560",  # KB금융
        "035720",  # 카카오
        "051910",  # LG화학
        "006400",  # 삼성SDI
        "068270",  # 셀트리온
        "055550",  # 신한지주
        "000270",  # 기아
    ]

    total_baseline_triples = 0
    total_patched_triples = 0
    total_baseline_kv_items = 0
    total_patched_kv_items = 0
    total_recovered_triples = 0
    total_recovered_kv_items = 0
    regression_cases = []

    for code in test_codes:
        try:
            periods = list(iterPeriodSubsets(code))
        except FileNotFoundError:
            print(f"  {code}: 데이터 없음, skip")
            continue

        code_baseline_t = 0
        code_patched_t = 0
        code_baseline_kv = 0
        code_patched_kv = 0

        for _period, _kind, _ccol, df in periods:
            if df is None or df.is_empty():
                continue
            period_str = str(_period)
            # period에서 연도 추출
            try:
                pYear = int(period_str[:4])
            except (ValueError, IndexError):
                continue

            content_col = "section_content" if "section_content" in df.columns else "content"
            if content_col not in df.columns:
                continue

            for content in df[content_col].to_list():
                if not content or "|" not in str(content):
                    continue
                # table block 추출
                lines = str(content).split("\n")
                table_blocks = []
                current_table = []
                for line in lines:
                    if line.strip().startswith("|"):
                        current_table.append(line)
                    else:
                        if current_table:
                            table_blocks.append("\n".join(current_table))
                            current_table = []
                if current_table:
                    table_blocks.append("\n".join(current_table))

                for tb in table_blocks:
                    subs = splitSubtables(tb)
                    for sub_lines in subs:
                        hdr = _headerCells(sub_lines)
                        structType = _classifyStructure(hdr)

                        if structType == "multi_year" and "Q" not in period_str:
                            base_t, _ = _parseMultiYear_original(sub_lines, pYear)
                            patch_t, _ = _parseMultiYear_patched(sub_lines, pYear)
                            code_baseline_t += len(base_t)
                            code_patched_t += len(patch_t)
                            if len(patch_t) < len(base_t):
                                regression_cases.append((code, period_str, "multi_year", len(base_t), len(patch_t)))

                        elif structType in ("key_value", "matrix"):
                            base_kv, _, _ = _parseKvMatrix_original(sub_lines)
                            patch_kv, _, _ = _parseKvMatrix_patched(sub_lines)
                            code_baseline_kv += len(base_kv)
                            code_patched_kv += len(patch_kv)
                            if len(patch_kv) < len(base_kv):
                                regression_cases.append((code, period_str, structType, len(base_kv), len(patch_kv)))

        recovered_t = code_patched_t - code_baseline_t
        recovered_kv = code_patched_kv - code_baseline_kv
        total_baseline_triples += code_baseline_t
        total_patched_triples += code_patched_t
        total_baseline_kv_items += code_baseline_kv
        total_patched_kv_items += code_patched_kv
        total_recovered_triples += max(0, recovered_t)
        total_recovered_kv_items += max(0, recovered_kv)

        print(f"  {code}: multi_year {code_baseline_t}→{code_patched_t} (+{recovered_t}), "
              f"kv/matrix {code_baseline_kv}→{code_patched_kv} (+{recovered_kv})")

    print(f"\n총합:")
    print(f"  multi_year: {total_baseline_triples}→{total_patched_triples} (+{total_recovered_triples})")
    print(f"  kv/matrix:  {total_baseline_kv_items}→{total_patched_kv_items} (+{total_recovered_kv_items})")
    print(f"  regression: {len(regression_cases)}건")
    if regression_cases:
        for rc in regression_cases[:10]:
            print(f"    {rc}")

    return {
        "baseline_triples": total_baseline_triples,
        "patched_triples": total_patched_triples,
        "baseline_kv": total_baseline_kv_items,
        "patched_kv": total_patched_kv_items,
        "recovered_triples": total_recovered_triples,
        "recovered_kv": total_recovered_kv_items,
        "regressions": len(regression_cases),
    }


if __name__ == "__main__":
    print("=== 080-001: Merged Cell Carry-Forward ===\n")
    results = run_experiment()
    print(f"\n판정: {'PASS' if results['regressions'] == 0 else 'FAIL (regression 발생)'}")
