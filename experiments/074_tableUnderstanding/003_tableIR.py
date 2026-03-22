"""
실험 ID: 074-003
실험명: markdown table -> TableIR 변환

목적:
- sections의 markdown table을 사람이 읽을 수 있는 중간표현(TableIR)로 만든다.
- 이후 bundle, scorer, alignment 평가가 같은 입력 구조를 공유하게 한다.

가설:
1. latest markdown 하나만 봐도 header band, row label, unit/kisu/period token을 안정적으로 뽑을 수 있다.
2. row label을 core/qualifier/annotation으로 분해하면 raw label보다 alignment에 유리하다.
3. TableIR만으로도 multi_year / matrix / key_value 분포를 요약할 수 있다.

방법:
1. 002의 seed gold set을 불러온다.
2. 각 bundle의 latest markdown에서 대표 subtable을 고른다.
3. header, row label, unit, kisu, period token, numeric/empty ratio를 계산해 TableIR로 변환한다.

결과 (실험 후 작성):
- TableIR `60개`를 생성했다.
- structure 분포: `matrix 37`, `multi_year 10`, `key_value 7`, `skip 6`
- median cell shape: `12행 x 5열`
- multiHeaderShare `1.0`으로, seed set 최신 markdown은 사실상 전부 header band가 2행 이상이었다.
- unit token 빈도: `원 38`, `주 38`, `명 18`, `% 16`, `천원 15`, `백만원 11`
- sample audit row에서 `제103기(당기)` -> core=`제103기`, qualifier=`당기`, annotation=`(당기)`로 분해됨
- 실행 시간: 약 `135.7초`

결론:
- latest markdown 기준 TableIR 추출은 안정적으로 동작한다.
- row label core/qualifier/annotation 분리는 실제 audit/dividend 계열에서 바로 의미가 있다.
- seed set의 대표 문제는 "표를 못 읽는다"보다 "matrix + multi-header를 어떻게 해석하느냐" 쪽에 가깝다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _normalizeHeader,
    splitSubtables,
)

ROOT = Path(__file__).resolve().parent


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_seed = load_script("002_seedGoldSet")

KISU_RE = re.compile(r"(당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말)")
PERIOD_RE = re.compile(r"(\d{4}Q\d|\d{4}년|\d{4})")
ANNOTATION_RE = re.compile(r"(\([^)]*\)|\[[^\]]*\])")


@dataclass
class TableIR:
    stockCode: str
    topic: str
    blockOrder: int
    period: str
    structureType: str
    headerBands: list[str]
    rowLabels: list[str]
    rowCore: list[str]
    rowQualifier: list[str]
    rowAnnotation: list[str]
    unitTokens: list[str]
    kisuTokens: list[str]
    periodTokens: list[str]
    numericRatio: float
    emptyRatio: float
    cellShape: tuple[int, int]
    headerSignature: str


def choose_representative_subtable(md: str) -> list[str]:
    subtables = splitSubtables(md)
    if not subtables:
        return []
    ranked = sorted(subtables, key=lambda sub: (len(_dataRows(sub)), len(sub)), reverse=True)
    return ranked[0]


def split_row_label(label: str) -> tuple[str, str, str]:
    raw = re.sub(r"\s+", " ", label).strip()
    annotations = " ".join(match.group(0) for match in ANNOTATION_RE.finditer(raw))
    no_annotation = ANNOTATION_RE.sub("", raw).strip()
    qualifier = ""
    if "-" in no_annotation:
        head, tail = no_annotation.split("-", 1)
        no_annotation = head.strip()
        qualifier = tail.strip()
    kisu = " ".join(KISU_RE.findall(raw))
    if kisu:
        qualifier = (qualifier + " " + kisu).strip()
        no_annotation = KISU_RE.sub("", no_annotation).strip()
    core = re.sub(r"\s+", "", no_annotation)
    return core or re.sub(r"\s+", "", raw), qualifier, annotations


def tokens_from_text(pattern: re.Pattern[str], text: str) -> list[str]:
    found = pattern.findall(text)
    tokens = sorted({token if isinstance(token, str) else token[0] for token in found if token})
    return tokens


def build_table_ir(entry: dict[str, object]) -> TableIR:
    sub = choose_representative_subtable(str(entry["latestMarkdown"]))
    header_cells = _headerCells(sub)
    data_rows = _dataRows(sub)
    row_labels = [row[0].strip() for row in data_rows if row and row[0].strip()]
    split_rows = [split_row_label(label) for label in row_labels]
    non_empty_cells = [cell.strip() for row in data_rows for cell in row if cell.strip()]
    numeric_cells = sum(1 for cell in non_empty_cells if re.search(r"-?[\d,]+(?:\.\d+)?", cell))
    total_cells = sum(len(row) for row in data_rows) if data_rows else 0
    empty_cells = sum(1 for row in data_rows for cell in row if not cell.strip())
    header_text = " | ".join(header_cells)
    full_text = str(entry["latestMarkdown"])
    unit_tokens = sorted({token for token in ["원", "주", "%", "백만원", "천원", "명"] if token in full_text})
    return TableIR(
        stockCode=str(entry["stockCode"]),
        topic=str(entry["topic"]),
        blockOrder=int(entry["blockOrder"]),
        period=str(entry["latestPeriod"]),
        structureType=_classifyStructure(header_cells) if header_cells else "skip",
        headerBands=[line.strip() for line in sub[:2]],
        rowLabels=row_labels,
        rowCore=[value[0] for value in split_rows],
        rowQualifier=[value[1] for value in split_rows],
        rowAnnotation=[value[2] for value in split_rows],
        unitTokens=unit_tokens,
        kisuTokens=tokens_from_text(KISU_RE, full_text),
        periodTokens=tokens_from_text(PERIOD_RE, header_text),
        numericRatio=round(numeric_cells / len(non_empty_cells), 4) if non_empty_cells else 0.0,
        emptyRatio=round(empty_cells / total_cells, 4) if total_cells else 0.0,
        cellShape=(len(data_rows), max((len(row) for row in data_rows), default=0)),
        headerSignature=_normalizeHeader(header_cells),
    )


def build_ir_samples() -> list[TableIR]:
    return [build_table_ir(entry) for entry in _seed.build_seed_gold_set()]


def summarize_ir() -> dict[str, object]:
    irs = build_ir_samples()
    return {
        "count": len(irs),
        "structures": Counter(ir.structureType for ir in irs).most_common(),
        "topics": Counter(ir.topic for ir in irs).most_common(10),
        "medianRows": float(pl.Series([ir.cellShape[0] for ir in irs]).median()) if irs else 0.0,
        "medianCols": float(pl.Series([ir.cellShape[1] for ir in irs]).median()) if irs else 0.0,
        "multiHeaderShare": round(sum(1 for ir in irs if len(ir.headerBands) > 1) / len(irs), 4) if irs else 0.0,
        "unitTokens": Counter(token for ir in irs for token in ir.unitTokens).most_common(),
        "sample": asdict(irs[0]) if irs else {},
    }


def main() -> None:
    print(summarize_ir())


if __name__ == "__main__":
    main()
